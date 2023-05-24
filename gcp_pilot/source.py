# More Information: <https://cloud.google.com/source-repositories/docs/reference/rest>
from typing import Any

from gcp_pilot import exceptions
from gcp_pilot.base import DiscoveryMixin, GoogleCloudPilotAPI

RepoType = dict[str, Any]


class SourceRepository(DiscoveryMixin, GoogleCloudPilotAPI):
    _iam_roles = ["source.repos.create"]

    def __init__(self, **kwargs):
        super().__init__(
            serviceName="sourcerepo",
            version="v1",
            cache_discovery=False,
            **kwargs,
        )

    def _repo_path(self, repo: str, project_id: str | None = None) -> str:
        parent_path = self._project_path(project_id=project_id)
        return f"{parent_path}/repos/{repo}"

    def list_repos(self, project_id: str | None = None) -> RepoType:
        params = dict(
            name=self._project_path(project_id=project_id),
        )
        items = self._paginate(
            method=self.client.projects().repos().list,
            result_key="repos",
            params=params,
        )
        yield from items

    def get_repo(self, repo_name: str, project_id: str | None = None) -> RepoType:
        return self._execute(
            method=self.client.projects().repos().get,
            name=self._repo_path(repo=repo_name, project_id=project_id),
        )

    def create_repo(self, repo_name: str, project_id: str | None = None, exists_ok: bool = True) -> RepoType:
        parent = self._project_path(project_id=project_id)
        repo_path = self._repo_path(repo=repo_name, project_id=project_id)
        try:
            return self._execute(
                method=self.client.projects().repos().create,
                parent=parent,
                body={
                    "name": repo_path,
                },
            )
        except exceptions.AlreadyExists:
            if not exists_ok:
                raise
            return self.get_repo(repo_name=repo_name, project_id=project_id)


__all__ = ("SourceRepository",)
