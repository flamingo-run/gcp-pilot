# More Information: https://cloud.google.com/cloud-build/docs/api
from dataclasses import dataclass, field
from typing import List, Dict, Any

from google.api_core.exceptions import AlreadyExists
from google.cloud.devtools import cloudbuild_v1

from gcp_pilot.base import GoogleCloudPilotAPI

TriggerType = cloudbuild_v1.BuildTrigger


class GoogleCloudBuild(GoogleCloudPilotAPI):
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

    def _make_trigger(
            self,
            name: str,
            description: str,
            repo_name: str,
            steps: List[cloudbuild_v1.BuildStep],
            branch_name: str,
            tags: List[str],
            project_id: str,
            images: List[str] = None,
            substitutions: Dict[str, str] = None,
    ) -> cloudbuild_v1.BuildTrigger:
        return cloudbuild_v1.BuildTrigger(
            name=name,
            description=description,
            tags=tags,
            trigger_template=cloudbuild_v1.RepoSource(
                project_id=project_id or self.project_id,
                repo_name=repo_name,
                branch_name=branch_name,
            ),
            build=cloudbuild_v1.Build(
                steps=steps,
                images=images or [],
            ),
            substitutions=substitutions,
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
            repo_name: str,
            steps: List[cloudbuild_v1.BuildStep],
            branch_name: str = 'master',
            tags: List[str] = None,
            project_id: str = None,
            images: List[str] = None,
            substitutions: Dict[str, str] = None,
    ) -> TriggerType:
        trigger = self._make_trigger(
            name=name,
            description=description,
            repo_name=repo_name,
            steps=steps,
            branch_name=branch_name,
            tags=tags,
            project_id=project_id or self.project_id,
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
            repo_name: str,
            steps: List[cloudbuild_v1.BuildStep],
            branch_name: str = 'master',
            tags: List[str] = None,
            project_id: str = None,
            images: List[str] = None,
            substitutions: Dict[str, str] = None,
    ) -> TriggerType:
        trigger = self._make_trigger(
            name=name,
            description=description,
            repo_name=repo_name,
            steps=steps,
            branch_name=branch_name,
            tags=tags,
            project_id=project_id or self.project_id,
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
            repo_name: str,
            steps: List[cloudbuild_v1.BuildStep],
            branch_name: str = 'master',
            tags: List[str] = None,
            project_id: str = None,
            images: List[str] = None,
            substitutions: Dict[str, str] = None,
    ) -> TriggerType:
        create_args = dict(
            name=name,
            description=description,
            repo_name=repo_name,
            steps=steps,
            branch_name=branch_name,
            tags=tags,
            project_id=project_id,
            images=images,
            substitutions=substitutions,
        )

        try:
            return await self.create_trigger(**create_args)
        except AlreadyExists:
            return await self.update_trigger(**create_args)

    def get_builds(self, trigger_id: str = None, project_id: str = None) -> cloudbuild_v1.Build:
        # https://cloud.google.com/cloud-build/docs/view-build-results#filtering_build_results_using_queries
        filters = []
        if trigger_id:
            filters.append(f'trigger_id="{trigger_id}"')

        all_builds = self.client.list_builds(
            filter=' AND '.join(filters),
            project_id=project_id or self.project_id,
        )
        for build in all_builds:
            yield build


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
