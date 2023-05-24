# More Information: https://cloud.google.com/service-usage/docs/reference/rest
from collections.abc import Generator
from enum import Enum

from gcp_pilot.base import DiscoveryMixin, GoogleCloudPilotAPI, ResourceType


class ServiceStatus(Enum):
    ENABLED = "ENABLED"
    DISABLED = "Enabled"


class ServiceUsage(DiscoveryMixin, GoogleCloudPilotAPI):
    def __init__(self, **kwargs):
        super().__init__(
            serviceName="serviceusage",
            version="v1",
            cache_discovery=False,
            **kwargs,
        )

    def _service_path(self, service_name: str, project_id: str | None = None) -> str:
        project_path = self._project_path(project_id=project_id)
        return f"{project_path}/services/{service_name}"

    def list_services(
        self,
        project_id: str | None = None,
        status: ServiceStatus = ServiceStatus.ENABLED,
    ) -> Generator[ResourceType, None, None]:
        params = dict(
            parent=self._project_path(project_id=project_id),
        )
        if status:
            params["filter"] = f"state:{status.value}"

        yield from self._paginate(
            method=self.client.services().list,
            result_key="services",
            params=params,
        )

    def get_service(
        self,
        service_name: str,
        project_id: str | None = None,
    ) -> ResourceType:
        name = self._service_path(service_name=service_name, project_id=project_id)
        return self._execute(
            method=self.client.services().get,
            name=name,
        )

    def enable_service(
        self,
        service_name: str,
        project_id: str | None = None,
    ) -> ResourceType:
        name = self._service_path(service_name=service_name, project_id=project_id)
        return self._execute(
            method=self.client.services().enable,
            name=name,
        )

    def disable_service(
        self,
        service_name: str,
        project_id: str | None = None,
    ) -> ResourceType:
        name = self._service_path(service_name=service_name, project_id=project_id)
        return self._execute(
            method=self.client.services().disable,
            name=name,
        )
