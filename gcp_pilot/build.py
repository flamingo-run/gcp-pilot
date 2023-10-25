# More Information: https://cloud.google.com/cloud-build/docs/api
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

from google.api_core.exceptions import AlreadyExists
from google.cloud.devtools import cloudbuild_v1

from gcp_pilot import exceptions
from gcp_pilot.base import GoogleCloudPilotAPI

TriggerType = cloudbuild_v1.BuildTrigger
AnyEventType = cloudbuild_v1.GitHubEventsConfig | cloudbuild_v1.RepoSource


@dataclass
class _SubstitutionVariable:
    key: str
    value: Any
    escape_delimiter: str | None = None

    def __post_init__(self):
        self.escape_delimiter = "|" if "," in str(self.value) else None

    @property
    def full_key(self) -> str:
        # Custom substitution variables must be prefixed with an underscore
        return f"_{self.key}"

    def __str__(self) -> str:
        # When used in a template, $_NAME should work, but it requires to be isolated by blank spaces
        # Thus, we use ${_NAME} by default, because it allows merging with other text.
        return "${%s}" % self.full_key

    @property
    def _escape(self):
        # <https://cloud.google.com/run/docs/configuring/environment-variables#setting>
        return f"^{self.escape_delimiter}^" if self.escape_delimiter else ""

    def as_env_var(self, key: str | None = None):
        return f"{self._escape}{key or self.key}={self!s}"


@dataclass
class Substitutions:
    _variables: dict[str, _SubstitutionVariable] = field(default_factory=dict)

    def add(self, **kwargs):
        for key, val in kwargs.items():
            variable = _SubstitutionVariable(key=key.upper(), value=val)
            self._variables[variable.key] = variable

    @property
    def as_dict(self) -> dict[str, str]:
        return {
            variable.full_key: str(variable.value)  # all values must be string or bytes
            for variable in self._variables.values()
        }

    def __getattr__(self, item: str):
        # Useful tool to ease the variable access (eg. substitution.MY_VAR_NAME)
        return self._variables[item.upper()]


class CloudBuild(GoogleCloudPilotAPI):
    _client_class = cloudbuild_v1.CloudBuildClient

    def make_build_step(
        self,
        name: str,
        identifier: str | None = None,
        args: list | None = None,
        env=None,
        entrypoint: str | None = None,
        timeout: int | None = None,
    ) -> cloudbuild_v1.BuildStep:
        return cloudbuild_v1.BuildStep(
            id=identifier,
            name=name,
            args=args,
            env=env,
            entrypoint=entrypoint,
            timeout=self._as_duration(timeout),
        )

    def make_source_repo_event(
        self,
        repo_name: str,
        branch_name: str | None = None,
        tag_name: str | None = None,
        project_id: str | None = None,
    ) -> cloudbuild_v1.RepoSource:
        if not branch_name and not tag_name:
            branch_name = "master"

        params = {}
        if branch_name:
            params["branch_name"] = branch_name
        if tag_name:
            params["tag_name"] = tag_name
        return cloudbuild_v1.RepoSource(
            project_id=project_id or self.project_id,
            repo_name=repo_name,
            **params,
        )

    def make_github_event(
        self,
        url,
        branch_name: str | None = None,
        tag_name: str | None = None,
    ) -> cloudbuild_v1.GitHubEventsConfig:
        if not branch_name and not tag_name:
            branch_name = "master"

        params = {}
        if branch_name:
            params["branch"] = branch_name
        if tag_name:
            params["tag"] = tag_name

        path = urlparse(url).path
        owner, name = path.split("/")[1:]
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
        steps: list[cloudbuild_v1.BuildStep],
        event: AnyEventType,
        tags: list[str],
        images: list[str] | None = None,
        substitutions: Substitutions | None = None,
        timeout: int | None = None,
        machine_type: str = cloudbuild_v1.BuildOptions.MachineType.UNSPECIFIED,
    ) -> cloudbuild_v1.BuildTrigger:
        def _get_event_param():
            valid_events = {
                "trigger_template": cloudbuild_v1.RepoSource,
                "github": cloudbuild_v1.GitHubEventsConfig,
            }
            for key, klass in valid_events.items():
                if isinstance(event, klass):
                    return key
            raise exceptions.ValidationError(f"Unsupported event type {event.__class__.__name__}")

        params = {_get_event_param(): event}

        return cloudbuild_v1.BuildTrigger(
            name=name,
            description=description,
            tags=tags,
            build=cloudbuild_v1.Build(
                steps=steps,
                images=images or [],
                timeout=self._as_duration(timeout),
                options=cloudbuild_v1.BuildOptions(
                    machine_type=machine_type,
                ),
            ),
            substitutions=substitutions.as_dict,
            **params,
        )

    def get_trigger(self, trigger_id: str, project_id: str | None = None) -> TriggerType:
        return self.client.get_build_trigger(
            trigger_id=trigger_id,
            project_id=project_id or self.project_id,
        )

    def delete_trigger(self, trigger_id: str, project_id: str | None = None):
        return self.client.delete_build_trigger(
            trigger_id=trigger_id,
            project_id=project_id or self.project_id,
        )

    def create_trigger(
        self,
        name: str,
        description: str,
        event: AnyEventType,
        steps: list[cloudbuild_v1.BuildStep],
        tags: list[str] | None = None,
        project_id: str | None = None,
        images: list[str] | None = None,
        substitutions: Substitutions | None = None,
        timeout: int | None = None,
        machine_type: str | None = None,
    ) -> TriggerType:
        trigger = self._make_trigger(
            name=name,
            description=description,
            event=event,
            steps=steps,
            tags=tags,
            images=images,
            substitutions=substitutions,
            timeout=timeout,
            machine_type=machine_type,
        )

        response = self.client.create_build_trigger(
            trigger=trigger,
            project_id=project_id or self.project_id,
        )
        return response

    def update_trigger(
        self,
        name: str,
        description: str,
        event: AnyEventType,
        steps: list[cloudbuild_v1.BuildStep],
        tags: list[str] | None = None,
        images: list[str] | None = None,
        substitutions: Substitutions | None = None,
        project_id: str | None = None,
        timeout: int | None = None,
        machine_type: str | None = None,
    ) -> TriggerType:
        trigger = self._make_trigger(
            name=name,
            description=description,
            event=event,
            steps=steps,
            tags=tags,
            images=images,
            substitutions=substitutions,
            timeout=timeout,
            machine_type=machine_type,
        )

        response = self.client.update_build_trigger(
            trigger_id=name,
            trigger=trigger,
            project_id=project_id or self.project_id,
        )
        return response

    def create_or_update_trigger(
        self,
        name: str,
        description: str,
        event: AnyEventType,
        steps: list[cloudbuild_v1.BuildStep],
        tags: list[str] | None = None,
        project_id: str | None = None,
        images: list[str] | None = None,
        substitutions: Substitutions | None = None,
        timeout: int | None = None,
        machine_type: str | None = None,
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
            timeout=timeout,
            machine_type=machine_type,
        )

        try:
            return self.create_trigger(**create_args)
        except AlreadyExists:
            return self.update_trigger(**create_args)

    def run_trigger(
        self,
        name: str,
        tag_name: str | None = None,
        branch_name: str | None = None,
        commit_sha: str | None = None,
        project_id: str | None = None,
    ) -> TriggerType:
        params = [tag_name, branch_name, commit_sha]
        if len([x for x in params if x]) != 1:
            raise exceptions.ValidationError("Only one of {tag_name, branch_name, commit_sha} must be provided")

        event = cloudbuild_v1.RepoSource(
            project_id=project_id or self.project_id,
            tag_name=tag_name,
            branch_name=branch_name,
            commit_sha=commit_sha,
        )
        response = self.client.run_build_trigger(
            trigger_id=name,
            source=event,
            project_id=project_id or self.project_id,
        )
        return response

    def get_builds(
        self,
        trigger_id: str | None = None,
        project_id: str | None = None,
        status: str | None = None,
    ) -> Generator[cloudbuild_v1.Build, None, None]:
        # https://cloud.google.com/cloud-build/docs/view-build-results#filtering_build_results_using_queries
        filters = []
        if trigger_id:
            filters.append(f'trigger_id="{trigger_id}"')

        if status:
            filters.append(f'status="{status}"')

        all_builds = self.client.list_builds(
            filter=" AND ".join(filters),
            project_id=project_id or self.project_id,
        )
        yield from all_builds

    def subscribe(
        self,
        subscription_id: str,
        project_id: str | None = None,
        push_to_url: str | None = None,
        use_oidc_auth: bool | None = False,
    ):
        # https://cloud.google.com/cloud-build/docs/subscribe-build-notifications
        try:
            # try to import here to avoid making pubsub a mandatory dependency of CloudBuild
            from gcp_pilot.pubsub import CloudSubscriber
        except ImportError as exc:
            raise ImportError("Add `pubsub` extras dependency in order to use CloudBuild notifications") from exc
        subscriber = CloudSubscriber()
        subscriber.create_subscription(
            topic_id="cloud-builds",  # pre-defined by GCP
            subscription_id=subscription_id,
            project_id=project_id,
            exists_ok=True,
            auto_create_topic=True,
            push_to_url=push_to_url,
            use_oidc_auth=use_oidc_auth,
        )


__all__ = (
    "CloudBuild",
    "Substitutions",
)
