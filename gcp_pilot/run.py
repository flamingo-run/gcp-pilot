# More Information <https://cloud.google.com/run/docs/reference/rest>
from typing import Generator

from google.api_core.client_options import ClientOptions
from googleapiclient.discovery import Resource

from gcp_pilot.base import (
    GoogleCloudPilotAPI,
    ResourceType,
    DiscoveryMixin,
    _get_project_default_location,
)


class CloudRun(DiscoveryMixin, GoogleCloudPilotAPI):
    def _service_endpoint(self, location: str = None):
        if not location:
            return 'https://run.googleapis.com'
        return f'https://{location}-run.googleapis.com'

    def _namespace_path(self, project_id: str = None):
        return f'namespaces/{project_id or self.project_id}'

    def _project_path(self, project_id: str = None):
        return f'projects/{project_id or self.project_id}'

    def _service_path(self, service_name: str, project_id: str = None):
        parent = self._namespace_path(project_id=project_id)
        return f'{parent}/services/{service_name}'

    def _domain_mapping_path(self, domain: str, project_id: str = None):
        parent = self._namespace_path(project_id=project_id)
        return f'{parent}/domainmappings/{domain}'

    def list_services(self, project_id: str = None) -> Generator[ResourceType, None, None]:
        params = dict(
            parent=self._namespace_path(project_id=project_id),
        )
        yield from self._list(
            method=self.client.namespaces().services().list,
            result_key='items',
            params=params,
        )

    def get_service(self, service_name: str, project_id: str = None, location: str = None) -> ResourceType:
        name = self._service_path(service_name=service_name, project_id=project_id)
        client = self._get_localized_client(project_id=project_id, location=location)
        return self._execute(
            method=client.namespaces().services().get,
            name=name,
        )

    def list_locations(self, project_id: str = None) -> Generator[ResourceType, None, None]:
        params = dict(
            name=self._project_path(project_id=project_id),
        )
        yield from self._paginate(
            method=self.client.projects().locations().list,
            result_key='locations',
            params=params,
        )

    def list_revisions(self, service_name: str = None, project_id: str = None) -> Generator[ResourceType, None, None]:
        params = dict(
            parent=self._namespace_path(project_id=project_id),
        )
        items = self._list(
            method=self.client.namespaces().revisions().list,
            result_key='items',
            params=params,
        )
        for item in items:
            if not service_name or item['metadata']['labels']['serving.knative.dev/service'] == service_name:
                yield item

    def list_domain_mappings(self, project_id: str = None) -> Generator[ResourceType, None, None]:
        params = dict(
            parent=self._namespace_path(project_id=project_id),
        )
        yield from self._list(
            method=self.client.namespaces().domainmappings().list,
            result_key='items',
            params=params,
        )

    def get_domain_mapping(self, domain: str, project_id: str = None, location: str = None) -> ResourceType:
        name = self._domain_mapping_path(domain=domain, project_id=project_id)
        client = self._get_localized_client(project_id=project_id, location=location)
        return self._execute(
            method=client.namespaces().domainmappings().get,
            name=name,
        )

    def delete_domain_mapping(self, domain: str, project_id: str = None, location: str = None) -> ResourceType:
        name = self._domain_mapping_path(domain=domain, project_id=project_id)
        client = self._get_localized_client(project_id=project_id, location=location)
        return self._execute(
            method=client.namespaces().domainmappings().delete,
            name=name,
        )

    def create_domain_mapping(
            self,
            domain: str,
            service_name: str,
            project_id: str = None,
            location: str = None,
    ) -> ResourceType:
        parent = self._namespace_path(project_id=project_id)
        client = self._get_localized_client(project_id=project_id, location=location)

        body = {
            'apiVersion': 'domains.cloudrun.com/v1',
            'kind': 'DomainMapping',
            'metadata': {'name': domain},
            'spec': {'routeName': service_name, 'certificateMode': 'AUTOMATIC'},
        }
        return self._execute(
            method=client.namespaces().domainmappings().create,
            parent=parent,
            body=body,
        )

    def _get_localized_client(self, project_id: str = None, location: str = None) -> Resource:
        # Reminder: List methods do not require a localized client
        if not location:
            if not project_id:
                location = self.location
            else:
                location = _get_project_default_location(credentials=self.credentials, project_id=project_id)
        return self._build_client(location=location)

    def _build_client(self, location: str = None, **kwargs) -> Resource:
        options = ClientOptions(api_endpoint=self._service_endpoint(location=location))
        kwargs.update(dict(
            serviceName='run',
            version='v1',
            cache_discovery=False,
            client_options=options,
        ))
        return super()._build_client(**kwargs)
