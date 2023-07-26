# More Information: https://cloud.google.com/api-gateway/docs/reference/rest
import base64
import time
from collections.abc import Generator
from pathlib import Path

from gcp_pilot.base import DiscoveryMixin, GoogleCloudPilotAPI, ResourceType
from gcp_pilot.service_usage import ServiceUsage


class APIGateway(DiscoveryMixin, GoogleCloudPilotAPI):
    def __init__(self, **kwargs):
        super().__init__(
            serviceName="apigateway",
            version="v1",
            cache_discovery=False,
            **kwargs,
        )

    def _api_path(self, api_name: str, project_id: str | None = None) -> str:
        location_path = self._location_path(project_id=project_id, location="global")
        return f"{location_path}/apis/{api_name}"

    def _gateway_path(self, gateway_name: str, location: str | None = None, project_id: str | None = None) -> str:
        location_path = self._location_path(project_id=project_id, location=location)
        return f"{location_path}/gateways/{gateway_name}"

    def _config_path(self, config_name: str, api_name: str, project_id: str | None = None) -> str:
        api_path = self._api_path(api_name=api_name, project_id=project_id)
        return f"{api_path}/configs/{config_name}"

    def list_apis(
        self,
        project_id: str | None = None,
        location: str | None = "global",
    ) -> Generator[ResourceType, None, None]:
        params = dict(
            parent=self._location_path(project_id=project_id, location=location),
        )
        yield from self._list(
            method=self.client.projects().locations().apis().list,
            result_key="apis",
            params=params,
        )

    def get_api(
        self,
        api_name: str,
        project_id: str | None = None,
    ) -> ResourceType:
        name = self._api_path(api_name=api_name, project_id=project_id)
        return self._execute(
            method=self.client.projects().locations().apis().get,
            name=name,
        )

    def create_api(
        self,
        api_name: str,
        display_name: str = "",
        labels: dict[str, str] | None = None,
        project_id: str | None = None,
        wait: bool = True,
    ) -> ResourceType:
        parent = self._location_path(location="global", project_id=project_id)
        body = {
            "displayName": display_name,
            "labels": labels,
        }
        output = self._execute(
            method=self.client.projects().locations().apis().create,
            parent=parent,
            apiId=api_name,
            body=body,
        )
        if wait:
            while output.get("state", "CREATING") == "CREATING":
                output = self.get_api(api_name=api_name, project_id=project_id)
                time.sleep(5)
        return output

    def delete_api(
        self,
        api_name: str,
        project_id: str | None = None,
    ) -> ResourceType:
        name = self._api_path(api_name=api_name, project_id=project_id)
        return self._execute(
            method=self.client.projects().locations().apis().delete,
            name=name,
        )

    def list_configs(
        self,
        api_name: str,
        project_id: str | None = None,
    ) -> Generator[ResourceType, None, None]:
        params = dict(
            parent=self._api_path(api_name=api_name, project_id=project_id),
        )
        yield from self._paginate(
            method=self.client.projects().locations().apis().configs().list,
            result_key="apiConfigs",
            params=params,
        )

    def get_config(
        self,
        config_name: str,
        api_name: str,
        project_id: str | None = None,
    ) -> ResourceType:
        name = self._config_path(config_name=config_name, api_name=api_name, project_id=project_id)
        return self._execute(
            method=self.client.projects().locations().apis().configs().get,
            name=name,
        )

    def create_config(
        self,
        config_name: str,
        api_name: str,
        service_account: str,
        open_api_file: Path,
        display_name: str = "",
        labels: dict[str, str] | None = None,
        project_id: str | None = None,
        wait: bool = True,
    ) -> ResourceType:
        parent = self._api_path(api_name=api_name, project_id=project_id)
        file_content = {"path": open_api_file.name, "contents": base64.b64encode(open_api_file.read_bytes()).decode()}
        body = {
            "displayName": display_name,
            "gatewayServiceAccount": service_account,
            "openapiDocuments": [{"document": file_content}],
            "labels": labels,
        }
        output = self._execute(
            method=self.client.projects().locations().apis().configs().create,
            parent=parent,
            apiConfigId=config_name,
            body=body,
        )

        if wait:
            while output.get("state", "CREATING") == "CREATING":
                output = self.get_config(config_name=config_name, api_name=api_name, project_id=project_id)
                time.sleep(5)
        return output

    def delete_config(
        self,
        config_name: str,
        api_name: str,
        project_id: str | None = None,
    ) -> ResourceType:
        name = self._config_path(config_name=config_name, api_name=api_name, project_id=project_id)
        return self._execute(
            method=self.client.projects().locations().apis().configs().delete,
            name=name,
        )

    def list_gateways(
        self,
        project_id: str | None = None,
        location: str | None = None,
    ) -> Generator[ResourceType, None, None]:
        params = dict(
            parent=self._location_path(project_id=project_id, location=location),
        )
        yield from self._paginate(
            method=self.client.projects().locations().gateways().list,
            result_key="gateways",
            params=params,
        )

    def get_gateway(
        self,
        gateway_name: str,
        project_id: str | None = None,
        location: str | None = None,
    ) -> ResourceType:
        name = self._gateway_path(gateway_name=gateway_name, location=location, project_id=project_id)
        return self._execute(
            method=self.client.projects().locations().gateways().get,
            name=name,
        )

    def create_gateway(
        self,
        gateway_name: str,
        api_name: str,
        config_name: str,
        labels: dict[str, str] | None = None,
        project_id: str | None = None,
        location: str | None = None,
        wait: bool = True,
    ) -> ResourceType:
        parent = self._location_path(project_id=project_id, location=location)
        config_path = self._config_path(
            api_name=api_name,
            config_name=config_name,
            project_id=project_id,
        )
        body = {
            "apiConfig": config_path,
            "labels": labels,
        }
        output = self._execute(
            method=self.client.projects().locations().gateways().create,
            parent=parent,
            gatewayId=gateway_name,
            body=body,
        )
        if wait:
            while output.get("state", "CREATING") == "CREATING":
                output = self.get_gateway(gateway_name=gateway_name, location=location, project_id=project_id)
                time.sleep(5)
        return output

    def delete_gateway(
        self,
        gateway_name: str,
        project_id: str | None = None,
        location: str | None = None,
    ) -> ResourceType:
        name = self._gateway_path(gateway_name=gateway_name, location=location, project_id=project_id)
        return self._execute(
            method=self.client.projects().locations().gateways().delete,
            name=name,
        )

    def enable_gateway(
        self,
        api_name: str,
        project_id: str | None = None,
    ):
        api_data = self.get_api(api_name=api_name, project_id=project_id)
        service_name = api_data["managedService"]

        service_usage = ServiceUsage()
        return service_usage.enable_service(
            service_name=service_name,
            project_id=project_id,
        )

    def disable_gateway(
        self,
        api_name: str,
        project_id: str | None = None,
    ):
        api_data = self.get_api(api_name=api_name, project_id=project_id)
        service_name = api_data["managedService"]

        service_usage = ServiceUsage()
        return service_usage.disable_service(
            service_name=service_name,
            project_id=project_id,
        )
