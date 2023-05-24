# More Information <https://cloud.google.com/monitoring/api/ref_v3/rest>
from collections.abc import Generator

from gcp_pilot.base import DiscoveryMixin, GoogleCloudPilotAPI, ResourceType


class Monitoring(DiscoveryMixin, GoogleCloudPilotAPI):
    _scopes = ["https://www.googleapis.com/auth/monitoring"]

    def __init__(self, **kwargs):
        super().__init__(
            serviceName="monitoring",
            version="v3",
            cache_discovery=False,
            **kwargs,
        )

    def _service_path(self, service_id: str, project_id: str | None = None) -> str:
        parent = self._project_path(project_id=project_id)
        return f"{parent}/services/{service_id}"

    def list_services(self, project_id: str | None = None) -> Generator[ResourceType, None, None]:
        parent = self._project_path(project_id=project_id)

        params = dict(
            parent=parent,
        )

        yield from self._paginate(
            method=self.client.services().list,
            result_key="services",
            params=params,
        )

    def get_service(self, service_id: str, project_id: str | None = None) -> ResourceType:
        service_path = self._service_path(service_id=service_id, project_id=project_id)

        return self._execute(
            method=self.client.services().get,
            name=service_path,
        )

    def create_service(
        self,
        name: str,
        project_id: str | None = None,
    ):
        parent = self._project_path(project_id=project_id)

        data = dict(
            name=name,
            display_name=name,
            custom={},
        )

        return self._execute(
            method=self.client.services().create,
            parent=parent,
            body=data,
        )


__all__ = ("Monitoring",)
