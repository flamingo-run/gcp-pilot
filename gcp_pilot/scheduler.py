import os
from typing import Dict

from google.api_core.exceptions import NotFound
from google.cloud import scheduler

from gcp_pilot.base import GoogleCloudPilotAPI


DEFAULT_TIMEZONE = os.environ.get('TIMEZONE', 'UTC')


class CloudScheduler(GoogleCloudPilotAPI):
    _client_class = scheduler.CloudSchedulerClient
    DEFAULT_METHOD = scheduler.HttpMethod.POST

    def __init__(self, **kwargs):
        self.timezone = kwargs.pop('timezone', DEFAULT_TIMEZONE)
        super().__init__(**kwargs)

    def _parent_path(self, project_id=None, location=None):
        return f'projects/{project_id or self.project_id}/locations/{location or self.location}'

    def _job_path(self, job, project_id=None, location=None):
        parent_name = self._parent_path(project_id=project_id, location=location)
        return f'{parent_name}/jobs/{job}'

    async def create(
            self,
            name: str,
            url: str,
            payload: str,
            cron: str,
            timezone: str = None,
            method: int = DEFAULT_METHOD,
            headers: Dict[str, str] = None,
            project_id: str = None,
            location: str = None,
            use_oidc_auth: bool = True,
    ):
        parent = self._parent_path(project_id=project_id, location=location)
        job_name = self._job_path(job=name, project_id=project_id, location=location)
        job = scheduler.Job(
            name=job_name,
            schedule=cron,
            time_zone=timezone or self.timezone,
            http_target=scheduler.HttpTarget(
                uri=url,
                http_method=method,
                body=payload.encode(),
                headers=headers or {},
                **(self.oidc_token if use_oidc_auth else {}),
            )
        )

        response = self.client.create_job(
            request={
                'parent': parent,
                'job': job
            }
        )
        return response

    async def update(
            self,
            name: str,
            url: str,
            payload: str,
            cron: str,
            timezone: str = None,
            method: int = DEFAULT_METHOD,
            headers: Dict[str, str] = None,
            project_id: str = None,
            location: str = None,
            use_oidc_auth: bool = True,
    ):
        job_name = self._job_path(job=name, project_id=project_id, location=location)
        job = scheduler.Job(
            name=job_name,
            schedule=cron,
            time_zone=timezone or self.timezone,
            http_target=scheduler.HttpTarget(
                uri=url,
                http_method=method,
                body=payload.encode(),
                headers=headers or {},
                **(self.oidc_token if use_oidc_auth else {}),
            )
        )

        response = self.client.update_job(
            job=job,
        )
        return response

    async def get(self, name: str, project_id: str = None, location: str = None):
        job_name = self._job_path(job=name, project_id=project_id, location=location)
        response = self.client.get_job(
            name=job_name,
        )
        return response

    async def delete(self, name: str, project_id: str = None, location: str = None):
        job_name = self._job_path(job=name, project_id=project_id, location=location)
        response = self.client.delete_job(
            name=job_name,
        )
        return response

    async def put(
            self,
            name: str,
            url: str,
            payload,
            cron: str,
            timezone: str = None,
            method: int = DEFAULT_METHOD,
            headers: Dict[str, str] = None,
            project_id: str = None,
            location: str = None,
            use_oidc_auth: bool = True,
    ):
        try:
            response = await self.update(
                name=name,
                url=url,
                payload=payload,
                cron=cron,
                timezone=timezone,
                method=method,
                headers=headers,
                location=location,
                project_id=project_id,
                use_oidc_auth=use_oidc_auth,
            )
        except NotFound:
            response = await self.create(
                name=name,
                url=url,
                payload=payload,
                cron=cron,
                timezone=timezone,
                method=method,
                headers=headers,
                location=location,
                project_id=project_id,
                use_oidc_auth=use_oidc_auth,
            )
        return response
