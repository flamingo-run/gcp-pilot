# More Information: https://cloud.google.com/cloud-build/docs/api
from dataclasses import dataclass, field
from typing import List, Dict, Any, Union, Generator
from urllib.parse import urlparse

from google.api_core.exceptions import AlreadyExists
from google.cloud.devtools import cloudbuild_v1

from gcp_pilot import exceptions
from gcp_pilot.base import GoogleCloudPilotAPI

TriggerType = cloudbuild_v1.BuildTrigger
AnyEventType = Union[cloudbuild_v1.GitHubEventsConfig, cloudbuild_v1.RepoSource]


class CloudBuild(GoogleCloudPilotAPI):
    _client_class = cloudbuild_v1.CloudBuildClient

    def make_build_step(
            self,
            name: str,
            identifier: str = None,
            args: list = None,
            env=None,
            entrypoint: str = None,
    ) -> cloudbuild_v1.BuildStep:
        return cloudbuild_v1.BuildStep(
            id=identifier,
            name=name,
            args=args,
            env=env,
            entrypoint=entrypoint,
        )

    def make_source_repo_event(
            self,
            repo_name: str,
            branch_name: str = None,
            tag_name: str = None,
            project_id: str = None,
    ) -> cloudbuild_v1.RepoSource:
        if not branch_name and not tag_name:
            branch_name = 'master'

        params = {}
        if branch_name:
            params['branch_name'] = branch_name
        if tag_name:
            params['tag_name'] = tag_name
        return cloudbuild_v1.RepoSource(
            project_id=project_id or self.project_id,
            repo_name=repo_name,
            **params,
        )

    def make_github_event(
            self,
            url,
            branch_name: str = None,
            tag_name: str = None,
    ) -> cloudbuild_v1.GitHubEventsConfig:
        if not branch_name and not tag_name:
            branch_name = 'master'

        params = {}
        if branch_name:
            params['branch'] = branch_name
        if tag_name:
            params['tag'] = tag_name

        path = urlparse(url).path
        owner, name = path.split('/')[1:]
        return cloudbuild_v1.GitHubEventsConfig(
            owner=owner,
            name=name,
            push=cloudbuild_v1.PushFilter(
                **params,
            ),
        )

    def _make_trigger(
            self,
            name: str,
            description: str,
            steps: List[cloudbuild_v1.BuildStep],
            event: AnyEventType,
            tags: List[str],
            images: List[str] = None,
            substitutions: Dict[str, str] = None,
    ) -> cloudbuild_v1.BuildTrigger:

        def _get_event_param():
            valid_events = {
                'trigger_template': cloudbuild_v1.RepoSource,
                'github': cloudbuild_v1.GitHubEventsConfig,
            }
            for key, klass in valid_events.items():
                if isinstance(event, klass):
                    return key
            raise exceptions.ValidationError(f"Unsupported event type {event.__class__.__name__,}")

        params = {
            _get_event_param(): event
        }

        return cloudbuild_v1.BuildTrigger(
            name=name,
            description=description,
            tags=tags,
            build=cloudbuild_v1.Build(
                steps=steps,
                images=images or [],
            ),
            substitutions=substitutions,
            **params,
        )

    async def get_trigger(self, trigger_id: str, project_id: str = None) -> TriggerType:
        response = self.client.get_build_trigger(
            trigger_id=trigger_id,
            project_id=project_id or self.project_id,
        )
        return response

    async def delete_trigger(self, trigger_id: str, project_id: str = None):
        response = self.client.delete_build_trigger(
            trigger_id=trigger_id,
            project_id=project_id or self.project_id,
        )
        return response

    async def create_trigger(
            self,
            name: str,
            description: str,
            event: AnyEventType,
            steps: List[cloudbuild_v1.BuildStep],
            tags: List[str] = None,
            project_id: str = None,
            images: List[str] = None,
            substitutions: Dict[str, str] = None,
    ) -> TriggerType:
        trigger = self._make_trigger(
            name=name,
            description=description,
            event=event,
            steps=steps,
            tags=tags,
            images=images,
            substitutions=substitutions,
        )

        response = self.client.create_build_trigger(
            trigger=trigger,
            project_id=project_id or self.project_id,
        )
        return response

    async def update_trigger(
            self,
            name: str,
            description: str,
            event: AnyEventType,
            steps: List[cloudbuild_v1.BuildStep],
            tags: List[str] = None,
            images: List[str] = None,
            substitutions: Dict[str, str] = None,
            project_id: str = None,
    ) -> TriggerType:
        trigger = self._make_trigger(
            name=name,
            description=description,
            event=event,
            steps=steps,
            tags=tags,
            images=images,
            substitutions=substitutions,
        )

        response = self.client.update_build_trigger(
            trigger_id=name,
            trigger=trigger,
            project_id=project_id or self.project_id,
        )
        return response

    async def create_or_update_trigger(
            self,
            name: str,
            description: str,
            event: AnyEventType,
            steps: List[cloudbuild_v1.BuildStep],
            tags: List[str] = None,
            project_id: str = None,
            images: List[str] = None,
            substitutions: Dict[str, str] = None,
    ) -> TriggerType:
        create_args = dict(
            name=name,
            description=description,
            event=event,
            steps=steps,
            tags=tags,
            project_id=project_id,
            images=images,
            substitutions=substitutions,
        )

        try:
            return await self.create_trigger(**create_args)
        except AlreadyExists:
            return await self.update_trigger(**create_args)

    def get_builds(
            self,
            trigger_id: str = None,
            project_id: str = None,
            status: str = None,
    ) -> Generator[cloudbuild_v1.Build, None, None]:
        # https://cloud.google.com/cloud-build/docs/view-build-results#filtering_build_results_using_queries
        filters = []
        if trigger_id:
            filters.append(f'trigger_id="{trigger_id}"')

        if status:
            filters.append(f'status="{status}"')

        all_builds = self.client.list_builds(
            filter=' AND '.join(filters),
            project_id=project_id or self.project_id,
        )
        for build in all_builds:
            yield build

    async def subscribe(
            self,
            subscription_id: str,
            project_id: str = None,
            push_to_url: str = None,
            use_oidc_auth: bool = False,
    ):
        # https://cloud.google.com/cloud-build/docs/subscribe-build-notifications
        try:
            # try to import here to avoid making pubsub a mandatory dependency of CloudBuild
            from gcp_pilot.pubsub import CloudSubscriber  # pylint: disable=import-outside-toplevel
        except ImportError as e:
            raise ImportError("Add `pubsub` extras dependency in order to use CloudBuild notifications") from e
        subscriber = CloudSubscriber()
        await subscriber.create_subscription(
            topic_id='cloud-builds',  # pre-defined by GCP
            subscription_id=subscription_id,
            project_id=project_id,
            exists_ok=True,
            auto_create_topic=True,
            push_to_url=push_to_url,
            use_oidc_auth=use_oidc_auth,
        )


@dataclass
class _SubstitutionVariable:
    key: str
    value: Any

    @property
    def as_kv(self) -> str:
        return '%s=%s' % (self.key, str(self))

    @property
    def custom_key(self) -> str:
        # Custom substitution variables must be prefixed with an underscore
        return f'_{self.key}'

    def __str__(self) -> str:
        # When used in a template, $_NAME should work, but it requires to be isolated by blank spaces
        # Thus, we use ${_NAME} by default, because it allows merging with other text.
        return '${%s}' % self.custom_key


@dataclass
class SubstitutionHelper:
    _variables: Dict[str, _SubstitutionVariable] = field(default_factory=dict)

    def add(self, **kwargs):
        for k, v in kwargs.items():
            variable = _SubstitutionVariable(key=k.upper(), value=v)
            self._variables[variable.key] = variable

    @property
    def as_dict(self) -> Dict[str, str]:
        return {
            variable.custom_key: str(variable.value)  # all values must be string or bytes
            for variable in self._variables.values()
        }

    def __getattr__(self, item: str):
        # Useful tool to ease the variable access (eg. substitution.MY_VAR_NAME)
        return self._variables[item.upper()]
