# More Information: <https://cloud.google.com/functions/docs/reference/rest>
from typing import Dict, Any, Generator

from gcp_pilot.base import GoogleCloudPilotAPI, DiscoveryMixin, PolicyType, AccountManagerMixin
from gcp_pilot import exceptions

FunctionType = Dict[str, Any]


class CloudFunctions(DiscoveryMixin, AccountManagerMixin, GoogleCloudPilotAPI):
    _scopes = [
        "https://www.googleapis.com/auth/cloudfunctions",
    ]

    def __init__(self, **kwargs):
        super().__init__(
            serviceName="cloudfunctions",
            version="v1",
            cache_discovery=False,
            **kwargs,
        )

    def _parent_path(self, project_id: str = None, location: str = None) -> str:
        return self._location_path(project_id=project_id, location=location)

    def _function_path(self, name: str, project_id: str = None, location: str = None) -> str:
        location_path = self._location_path(project_id=project_id, location=location)
        return f"{location_path}/functions/{name}"

    def get_functions(self, project_id: str = None, location: str = None) -> Generator[FunctionType, None, None]:
        params = dict(
            parent=self._parent_path(project_id=project_id, location=location),
        )
        yield from self._list(
            method=self.client.projects().locations().functions().list,
            result_key="functions",
            params=params,
        )

    def get_function(self, name: str, project_id: str = None, location: str = None) -> FunctionType:
        function_name = self._function_path(name=name, project_id=project_id, location=location)
        return self._execute(
            method=self.client.projects().locations().functions().get,
            name=function_name,
        )

    @classmethod
    def build_repo_source(
        cls,
        name,
        branch: str = None,
        commit: str = None,
        tag: str = None,
        directory: str = None,
        project_id: str = None,
    ) -> Dict[str, Any]:

        valid_references = [ref for ref in [branch, commit, tag] if ref]
        if len(valid_references) > 1:
            raise exceptions.ValidationError("Only one of branch|tag|commit must be provided")

        if branch:
            ref = f"moveable-aliases/{branch}"
        elif commit:
            ref = f"revisions{commit}"
        elif tag:
            ref = f"fixed-aliases/{tag}"
        else:
            ref = f"moveable-aliases/master"

        path = f"/paths/{directory}" if directory else ""

        if "/" in name:
            # Assume it's a repository integrated through Github App
            org, repo = name.split("/")
            repo_name = f"github_{org}_{repo}"
        else:
            repo_name = name

        REPO_SOURCE_URL = "https://source.developers.google.com"
        url = f"{REPO_SOURCE_URL}/projects/{project_id}/repos/{repo_name}/{ref}{path}"
        repo = dict(url=url)

        return repo

    def create_or_update_function(
        self,
        name: str,
        description: str,
        entry_point: str,
        repo_name: str,
        runtime: str = "python39",
        timeout: int = 60,
        ram: int = 128,
        repo_branch: str = None,
        repo_tag: str = None,
        repo_commit: str = None,
        repo_directory: str = None,
        labels: Dict[str, str] = None,
        env_vars: Dict[str, str] = None,
        max_instances: int = None,
        project_id: str = None,
        location: str = None,
        service_account_email: str = None,
        is_public: bool = False,
    ) -> FunctionType:
        repo = self.build_repo_source(
            name=repo_name,
            commit=repo_commit,
            tag=repo_tag,
            branch=repo_branch,
            directory=repo_directory,
            project_id=project_id or self.project_id,
        )
        body = dict(
            name=self._function_path(name=name, project_id=project_id, location=location),
            description=description,
            entry_point=entry_point,
            runtime=runtime,
            labels=labels,
            environment_variables=env_vars,
            timeout=f"{timeout}s",
            available_memory_mb=ram,
            service_account_email=service_account_email,
            max_instances=max_instances,
            source_repository=repo,
            https_trigger=dict(security_level="SECURE_ALWAYS"),
        )

        try:
            fields_to_update = ",".join(body.keys())
            function_name = self._function_path(name=name, project_id=project_id, location=location)
            operation = self._execute(
                method=self.client.projects().locations().functions().patch,
                name=function_name,
                updateMask=fields_to_update,
                body=body,
            )
        except exceptions.NotFound:
            parent = self._parent_path(project_id=project_id, location=location)
            operation = self._execute(
                method=self.client.projects().locations().functions().create,
                location=parent,
                body=body,
            )

        self.set_permissions(name=name, project_id=project_id, location=location, is_public=is_public)

        return {"name": operation["metadata"]["target"]}

    def get_permissions(self, name: str, project_id: str = None, location: str = None) -> PolicyType:
        function_name = self._function_path(name=name, project_id=project_id, location=location)

        return self._execute(
            method=self.client.projects().locations().functions().getIamPolicy,
            resource=function_name,
        )

    def set_permissions(self, name: str, is_public: bool, project_id: str = None, location: str = None) -> PolicyType:
        policy = self.get_permissions(name=name, project_id=project_id, location=location)
        role = "roles/cloudfunctions.invoker"
        if is_public:
            new_policy = self._make_public(role=role, policy=policy)
        else:
            new_policy = self._make_private(role=role, policy=policy)

        function_name = self._function_path(name=name, project_id=project_id, location=location)
        body = dict(
            policy=new_policy,
            updateMask="bindings",
        )

        return self._execute(
            method=self.client.projects().locations().functions().setIamPolicy,
            resource=function_name,
            body=body,
        )

    def delete_function(self, name: str, project_id: str = None, location: str = None) -> FunctionType:
        function_name = self._function_path(name=name, project_id=project_id, location=location)
        operation = self._execute(
            method=self.client.projects().locations().functions().delete,
            name=function_name,
        )
        return {"name": operation["metadata"]["target"]}


__all__ = ("CloudFunctions",)
