# More Information <https://cloud.google.com/scheduler/docs/reference/rest>
import os
from collections.abc import Generator

from google.api_core.exceptions import NotFound
from google.cloud import scheduler

from gcp_pilot.base import AppEngineBasedService, GoogleCloudPilotAPI

DEFAULT_TIMEZONE = os.environ.get("TIMEZONE", None)  # UTC
MAX_TIMEOUT = 30 * 60  # max allowed to HTTP endpoints is 30 minutes


class CloudScheduler(AppEngineBasedService, GoogleCloudPilotAPI):
    _client_class = scheduler.CloudSchedulerClient
    DEFAULT_METHOD = scheduler.HttpMethod.POST

    def __init__(self, **kwargs):
        self.timezone = kwargs.pop("timezone", DEFAULT_TIMEZONE)
        super().__init__(**kwargs)

    def _parent_path(self, project_id: str | None = None) -> str:
        return self._location_path(project_id=project_id, location=self.location)

    def _job_path(self, job, project_id: str | None = None) -> str:
        parent_name = self._parent_path(project_id=project_id)
        return f"{parent_name}/jobs/{job}"

    def create(
        self,
        name: str,
        url: str,
        payload: str,
        cron: str,
        timezone: str | None = None,
        method: int = DEFAULT_METHOD,
        headers: dict[str, str] | None = None,
        project_id: str | None = None,
        use_oidc_auth: bool = True,
        timeout_in_seconds: int = MAX_TIMEOUT,
    ) -> scheduler.Job:
        parent = self._parent_path(project_id=project_id)
        job_name = self._job_path(job=name, project_id=project_id)
        job = scheduler.Job(
            name=job_name,
            schedule=cron,
            time_zone=timezone or self.timezone,
            attempt_deadline=self._as_duration(seconds=timeout_in_seconds),
            http_target=scheduler.HttpTarget(
                uri=url,
                http_method=method,
                body=payload.encode(),
                headers=headers or {},
                **(self.get_oidc_token(audience=url) if use_oidc_auth else {}),
            ),
        )

        response = self.client.create_job(request={"parent": parent, "job": job})
        return response

    def update(
        self,
        name: str,
        url: str,
        payload: str,
        cron: str,
        timezone: str | None = None,
        method: int = DEFAULT_METHOD,
        headers: dict[str, str] | None = None,
        project_id: str | None = None,
        use_oidc_auth: bool = True,
        timeout_in_seconds: int = MAX_TIMEOUT,
    ) -> scheduler.Job:
        job_name = self._job_path(job=name, project_id=project_id)
        job = scheduler.Job(
            name=job_name,
            schedule=cron,
            time_zone=timezone or self.timezone,
            attempt_deadline=self._as_duration(seconds=timeout_in_seconds),
            http_target=scheduler.HttpTarget(
                uri=url,
                http_method=method,
                body=payload.encode(),
                headers=headers or {},
                **(self.get_oidc_token(audience=url) if use_oidc_auth else {}),
            ),
        )

        response = self.client.update_job(
            job=job,
        )
        return response

    def list(self, prefix: str = "", project_id: str | None = None) -> Generator[scheduler.Job, None, None]:
        parent = self._parent_path(project_id=project_id)
        for job in self.client.list_jobs(parent=parent):
            if job.name.split("/jobs/")[-1].startswith(prefix):
                yield job

    def get(self, name: str, project_id: str | None = None) -> scheduler.Job:
        job_name = self._job_path(job=name, project_id=project_id)
        return self.client.get_job(
            name=job_name,
        )

    def delete(self, name: str, project_id: str | None = None) -> None:
        job_name = self._job_path(job=name, project_id=project_id)
        return self.client.delete_job(
            name=job_name,
        )

    def put(
        self,
        name: str,
        url: str,
        payload: str,
        cron: str,
        timezone: str | None = None,
        method: int = DEFAULT_METHOD,
        headers: dict[str, str] | None = None,
        project_id: str | None = None,
        use_oidc_auth: bool = True,
        timeout_in_seconds: int = MAX_TIMEOUT,
    ) -> scheduler.Job:
        try:
            response = self.update(
                name=name,
                url=url,
                payload=payload,
                cron=cron,
                timezone=timezone,
                method=method,
                headers=headers,
                project_id=project_id,
                use_oidc_auth=use_oidc_auth,
                timeout_in_seconds=timeout_in_seconds,
            )
        except NotFound:
            response = self.create(
                name=name,
                url=url,
                payload=payload,
                cron=cron,
                timezone=timezone,
                method=method,
                headers=headers,
                project_id=project_id,
                use_oidc_auth=use_oidc_auth,
                timeout_in_seconds=timeout_in_seconds,
            )
        return response


__all__ = ("CloudScheduler",)
