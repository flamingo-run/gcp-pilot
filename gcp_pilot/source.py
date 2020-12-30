# https://cloud.google.com/source-repositories/docs/reference/rest
from typing import Dict, Any

from googleapiclient.errors import HttpError

from gcp_pilot.base import GoogleCloudPilotAPI

RepoType = Dict[str, Any]


class GoogleCloudSourceRepo(GoogleCloudPilotAPI):
    _iam_roles = ['source.repos.create']

    def __init__(self, **kwargs):
        super().__init__(
            serviceName='sourcerepo',
            version='v1',
            cache_discovery=False,
            **kwargs,
        )

    def _parent_path(self, project_id: str = None) -> str:
        return f'projects/{project_id or self.project_id}'

    def _repo_path(self, repo: str, project_id: str = None) -> str:
        parent_path = self._parent_path(project_id=project_id)
        return f'{parent_path}/repos/{repo}'

    async def get_repo(self, repo_name: str, project_id: str = None) -> RepoType:
        return self.client.projects().repos().get(
            name=self._repo_path(repo=repo_name, project_id=project_id),
        ).execute()

    async def create_repo(self, repo_name: str, project_id: str = None, exists_ok: bool = True) -> RepoType:
        parent = self._parent_path(project_id=project_id)
        repo_path = self._repo_path(repo=repo_name, project_id=project_id)
        try:
            return self.client.projects().repos().create(
                parent=parent,
                body={
                    'name': repo_path,
                },
            ).execute()
        except HttpError as e:
            if e.resp.status == 409 and exists_ok:
                return await self.get_repo(repo_name=repo_name, project_id=project_id)
            raise
