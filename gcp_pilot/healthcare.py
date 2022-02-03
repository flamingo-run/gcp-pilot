# More Information: https://cloud.google.com/healthcare-api/docs/reference/rest
import abc
from typing import Generator, Dict, Any

from gcp_pilot import exceptions
from gcp_pilot.base import GoogleCloudPilotAPI, DiscoveryMixin, ResourceType


class HealthcareBase(DiscoveryMixin, GoogleCloudPilotAPI, abc.ABC):
    _scopes = ["https://www.googleapis.com/auth/cloud-healthcare"]

    def __init__(self, **kwargs):
        super().__init__(
            serviceName="healthcare",
            version="v1beta1",
            cache_discovery=False,
            **kwargs,
        )

    def _set_location(self, location: str = None) -> str:
        # Only some limited regions are available: https://cloud.google.com/healthcare-api/docs/concepts/region
        return "us"

    def _dataset_path(self, name: str, project_id: str = None, location: str = None) -> str:
        location_path = self._location_path(project_id=project_id, location=location)
        return f"{location_path}/datasets/{name}"

    def list_datasets(self, project_id: str = None, location: str = None) -> Generator[ResourceType, None, None]:
        params = dict(
            parent=self._location_path(project_id=project_id, location=location),
        )

        yield from self._list(
            method=self.client.projects().locations().datasets().list,
            result_key="datasets",
            params=params,
        )

    def get_dataset(self, name: str, project_id: str = None, location: str = None) -> ResourceType:
        name = self._dataset_path(name=name, project_id=project_id, location=location)

        return self._execute(
            method=self.client.projects().locations().datasets().get,
            name=name,
        )

    def delete_dataset(self, name: str, project_id: str = None, location: str = None) -> ResourceType:
        name = self._dataset_path(name=name, project_id=project_id, location=location)

        return self._execute(
            method=self.client.projects().locations().datasets().delete,
            name=name,
        )

    def create_dataset(
        self,
        name: str,
        project_id: str = None,
        location: str = None,
    ) -> ResourceType:
        parent = self._location_path(project_id=project_id, location=location)

        body = {}

        return self._execute(
            method=self.client.projects().locations().datasets().create,
            parent=parent,
            datasetId=name,
            body=body,
        )


class HealthcareFHIR(HealthcareBase):
    def _store_path(self, name: str, dataset_name: str, project_id: str = None, location: str = None) -> str:
        dataset_path = self._dataset_path(name=dataset_name, project_id=project_id, location=location)
        return f"{dataset_path}/fhirStores/{name}"

    def _resource_path(
        self,
        resource_type: str,
        resource_id: str,
        store_name: str,
        dataset_name: str,
        project_id: str = None,
        location: str = None,
    ) -> str:
        store_path = self._store_path(
            name=store_name,
            dataset_name=dataset_name,
            project_id=project_id,
            location=location,
        )
        return f"{store_path}/fhir/{resource_type}/{resource_id}"

    def list_stores(
        self, dataset_name: str, project_id: str = None, location: str = None
    ) -> Generator[ResourceType, None, None]:
        params = dict(
            parent=self._dataset_path(name=dataset_name, project_id=project_id, location=location),
        )

        yield from self._list(
            method=self.client.projects().locations().datasets().fhirStores().list,
            result_key="fhirStores",
            params=params,
        )

    def get_store(self, name: str, dataset_name: str, project_id: str = None, location: str = None) -> ResourceType:
        name = self._store_path(name=name, dataset_name=dataset_name, project_id=project_id, location=location)

        return self._execute(
            method=self.client.projects().locations().datasets().fhirStores().get,
            name=name,
        )

    def delete_store(self, name: str, dataset_name: str, project_id: str = None, location: str = None) -> ResourceType:
        name = self._store_path(name=name, dataset_name=dataset_name, project_id=project_id, location=location)

        return self._execute(
            method=self.client.projects().locations().datasets().fhirStores().delete,
            name=name,
        )

    def list_resources(
        self,
        store_name: str,
        dataset_name: str,
        project_id: str = None,
        location: str = None,
        resource_type: str = None,
        query: Dict[str, Any] = None,
    ) -> Generator[ResourceType, None, None]:
        parent = self._store_path(
            name=store_name,
            dataset_name=dataset_name,
            project_id=project_id,
            location=location,
        )
        url = f"{self._base_url}/{parent}/fhir/{resource_type}/_search"

        params = dict(
            url=url,
            params=query,
            headers={"Content-Type": "application/fhir+json;charset=utf-8"},
        )

        entries = self._list(
            method=self._session.post,
            result_key="entry",
            params=params,
        )
        for entry in entries:
            yield entry["resource"]

    def create_store(
        self,
        name: str,
        dataset_name: str,
        labels: Dict[str, str] = None,
        enable_upsert: bool = True,
        notify_pubsub_topic: str = None,
        export_to_bigquery_dataset: str = None,
        project_id: str = None,
        location: str = None,
        version: str = "R4",
    ) -> ResourceType:
        parent = self._dataset_path(name=dataset_name, project_id=project_id, location=location)

        body = {
            "name": name,
            "enableUpdateCreate": enable_upsert,
            "labels": labels,
            "version": version,
        }

        if notify_pubsub_topic:
            body["notification_config"] = {
                "pubsubTopic": notify_pubsub_topic,
            }

        if export_to_bigquery_dataset:
            body["streamConfigs"] = {
                "resourceTypes": [],  # empty means all
                "bigqueryDestination": {
                    "datasetUri": f"bq://{export_to_bigquery_dataset}",
                    "schemaConfig": {
                        "schemaType": "ANALYTICS",
                        "recursiveStructureDepth": 5,  # max depth
                    },
                    "writeDisposition": "WRITE_TRUNCATE",
                },
            }

        return self._execute(
            method=self.client.projects().locations().datasets().fhirStores().create,
            parent=parent,
            body=body,
            fhirStoreId=name,
        )

    def get_resource(
        self,
        resource_type: str,
        resource_id: str,
        store_name: str,
        dataset_name: str,
        project_id: str = None,
        location: str = None,
    ) -> ResourceType:
        name = self._resource_path(
            resource_type=resource_type,
            resource_id=resource_id,
            store_name=store_name,
            dataset_name=dataset_name,
            project_id=project_id,
            location=location,
        )

        return self._execute(
            method=self.client.projects().locations().datasets().fhirStores().fhir().read,
            name=name,
        )

    def delete_resource(
        self,
        resource_type: str,
        resource_id: str,
        store_name: str,
        dataset_name: str,
        project_id: str = None,
        location: str = None,
    ) -> ResourceType:
        name = self._resource_path(
            resource_type=resource_type,
            resource_id=resource_id,
            store_name=store_name,
            dataset_name=dataset_name,
            project_id=project_id,
            location=location,
        )

        return self._execute(
            method=self.client.projects().locations().datasets().fhirStores().fhir().delete,
            name=name,
        )

    def create_resource(
        self,
        data: Dict[str, Any],
        resource_type: str,
        store_name: str,
        dataset_name: str,
        project_id: str = None,
        location: str = None,
    ) -> ResourceType:
        parent = self._store_path(name=store_name, dataset_name=dataset_name, project_id=project_id, location=location)
        return self._execute(
            method=self.client.projects().locations().datasets().fhirStores().fhir().create,
            parent=parent,
            type=resource_type,
            body=data,
        )

    def update_resource(
        self,
        data: Dict[str, Any],
        resource_type: str,
        resource_id: str,
        store_name: str,
        dataset_name: str,
        project_id: str = None,
        location: str = None,
    ) -> ResourceType:
        name = self._resource_path(
            resource_type=resource_type,
            resource_id=resource_id,
            store_name=store_name,
            dataset_name=dataset_name,
            project_id=project_id,
            location=location,
        )

        return self._execute(
            method=self.client.projects().locations().datasets().fhirStores().fhir().update,
            name=name,
            body=data,
        )

    def create_or_update_resource(
        self,
        data: Dict[str, Any],
        resource_type: str,
        store_name: str,
        dataset_name: str,
        query: Dict[str, Any] = None,
        project_id: str = None,
        location: str = None,
    ) -> ResourceType:
        if not query:
            identifiers = data.get("identifier")
            if not identifiers:
                raise exceptions.ValidationError("Either `query` or identifiers must be provided to create-or-update")

            query_values = []
            for identifier in identifiers:
                query_values.append(identifier["system"])
                query_values.append(identifier["value"])
            query = {"identifier": "|".join(query_values)}

        parent = self._store_path(
            name=store_name,
            dataset_name=dataset_name,
            project_id=project_id,
            location=location,
        )
        url = f"{self._base_url}/{parent}/fhir/{resource_type}"

        params = dict(
            url=url,
            params=query,
            headers={"Content-Type": "application/fhir+json;charset=utf-8"},
            json=data,
        )

        return self._execute(method=self._session.put, **params)

    def export_resources(
        self,
        gcs_path: str,
        store_name: str,
        dataset_name: str,
        project_id: str = None,
        location: str = None,
    ) -> ResourceType:
        parent = self._store_path(name=store_name, dataset_name=dataset_name, project_id=project_id, location=location)
        body = {"gcsDestination": {"uriPrefix": f"gs://{gcs_path}"}}
        return self._execute(
            method=self.client.projects().locations().datasets().fhirStores().export,
            parent=parent,
            body=body,
        )

    def import_resources(
        self,
        gcs_path: str,
        store_name: str,
        dataset_name: str,
        project_id: str = None,
        location: str = None,
    ) -> ResourceType:
        parent = self._store_path(name=store_name, dataset_name=dataset_name, project_id=project_id, location=location)
        body = {
            "contentStructure": "CONTENT_STRUCTURE_UNSPECIFIED",
            "gcsSource": {"uri": f"gs://{gcs_path}"},
        }
        return self._execute(
            method=self.client.projects().locations().datasets().fhirStores().import_,
            name=parent,
            body=body,
        )

    def get_resource_history(
        self,
        resource_type: str,
        resource_id: str,
        store_name: str,
        dataset_name: str,
        project_id: str = None,
        location: str = None,
    ) -> ResourceType:
        name = self._resource_path(
            resource_type=resource_type,
            resource_id=resource_id,
            store_name=store_name,
            dataset_name=dataset_name,
            project_id=project_id,
            location=location,
        )

        entries = self._list(
            method=self.client.projects().locations().datasets().fhirStores().fhir().history,
            params=dict(
                name=name,
            ),
            result_key="entry",
        )

        for entry in entries:
            yield entry["resource"]
