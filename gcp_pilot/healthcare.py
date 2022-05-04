# More Information: https://cloud.google.com/healthcare-api/docs/reference/rest
import abc
import logging
import math
import json
from dataclasses import dataclass
from typing import Generator, Dict, Any, Callable, Optional, Type, List
from urllib.parse import urlsplit, parse_qsl

from fhir.resources.domainresource import DomainResource
from fhir.resources.identifier import Identifier

from gcp_pilot import exceptions
from gcp_pilot.base import GoogleCloudPilotAPI, DiscoveryMixin, ResourceType, friendly_http_error

logger = logging.getLogger("gcp-pilot")


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
        # Only some limited regions are available: https://cloud.google.com/healthcare-api/docs/concepts/regions
        valid_locations = [
            "us-central1",
            "us-west2",
            "us-east4",
            "northamerica-northeast1",
            "southamerica-east1",
            "europe-west3",
            "europe-west2",
            "europe-west4",
            "europe-west6",
            "asia-east2",
            "asia-south1",
            "asia-southeast1",
            "asia-northeast1",
            "asia-northeast3",
            "australia-southeast1",
        ]
        location = super()._set_location(location=location)
        if location not in valid_locations:
            logger.warning(f"The location {location} is not available for Healthcare API yet. Using multi-region US.")
            location = "us"
        return location

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


def as_json(resource: DomainResource) -> Dict[str, Any]:
    return json.loads(resource.json())


@dataclass
class FHIRResultSet:
    method: Callable
    url: str
    resource_class: Type[DomainResource]
    query: Dict[str, Any] = None
    order_by: str = None
    limit: int = None
    cursor: str = None
    _response: Dict = None

    @property
    def response(self):
        if not self._response:
            self._request()
        return self._response

    @response.setter
    def response(self, value):
        self._response = value

    @friendly_http_error
    def _request(self):
        kwargs = {
            "url": self.url,
            "headers": {"Content-Type": "application/fhir+json;charset=utf-8"},
            "params": self.query or {},
        }
        if self.order_by:
            kwargs["params"]["_sort"] = self.order_by
        if self.limit:
            kwargs["params"]["_count"] = self.limit
        if self.cursor:
            kwargs["params"]["_page_token"] = self.cursor

        request = self.method(**kwargs)
        request.raise_for_status()
        self.response = request.json()

    def __iter__(self) -> Generator[Dict, None, None]:
        while True:
            yield from self.get_page_resources()
            self.cursor = self.next_cursor
            if not self.cursor:
                break
            self._request()

    def first(self) -> Dict:
        try:
            return next(iter(self))
        except StopIteration as exc:
            raise exceptions.NotFound() from exc

    def get_page_resources(self) -> Generator[DomainResource, None, None]:
        if self.total == 0:
            return

        for entry in self.response["entry"]:
            yield self.resource_class(**entry["resource"])

    @property
    def next_cursor(self) -> Optional[str]:
        for link in self.response["link"]:
            if link["relation"] == "next":
                query_params = dict(parse_qsl(urlsplit(link["url"]).query))
                return query_params.get("_page_token")
        return None

    @property
    def previous_cursor(self) -> Optional[str]:
        for link in self.response["link"]:
            if link["relation"] == "previous":
                return link["url"]
        return None

    @property
    def total(self) -> int:
        return self.response["total"]

    def __len__(self) -> int:
        return self.total

    @property
    def num_pages(self) -> int:
        return int(math.ceil(self.total / self.limit))


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
        self,
        dataset_name: str,
        project_id: str = None,
        location: str = None,
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
        resource_class: Type[DomainResource],
        project_id: str = None,
        location: str = None,
        query: Dict[str, Any] = None,
        limit: int = 100,
        cursor: str = None,
    ) -> FHIRResultSet:
        parent = self._store_path(
            name=store_name,
            dataset_name=dataset_name,
            project_id=project_id,
            location=location,
        )
        resource_type = resource_class.get_resource_type()
        url = f"{self._base_url}/{parent}/fhir/{resource_type}/_search"

        return FHIRResultSet(
            method=self._session.post,
            url=url,
            resource_class=resource_class,
            query=query,
            limit=limit,
            cursor=cursor,
        )

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
        resource_class: Type[DomainResource],
        resource_id: str,
        store_name: str,
        dataset_name: str,
        project_id: str = None,
        location: str = None,
    ) -> DomainResource:
        resource_type = resource_class.get_resource_type()
        name = self._resource_path(
            resource_type=resource_type,
            resource_id=resource_id,
            store_name=store_name,
            dataset_name=dataset_name,
            project_id=project_id,
            location=location,
        )

        data = self._execute(
            method=self.client.projects().locations().datasets().fhirStores().fhir().read,
            name=name,
        )
        return resource_class(**data)

    def delete_resource(
        self,
        resource_class: Type[DomainResource],
        resource_id: str,
        store_name: str,
        dataset_name: str,
        project_id: str = None,
        location: str = None,
    ) -> ResourceType:
        resource_type = resource_class.get_resource_type()
        name = self._resource_path(
            resource_type=resource_type,
            resource_id=resource_id,
            store_name=store_name,
            dataset_name=dataset_name,
            project_id=project_id,
            location=location,
        )

        data = self._execute(
            method=self.client.projects().locations().datasets().fhirStores().fhir().delete,
            name=name,
        )
        return data

    def create_resource(
        self,
        resource: DomainResource,
        store_name: str,
        dataset_name: str,
        project_id: str = None,
        location: str = None,
    ) -> ResourceType:
        parent = self._store_path(name=store_name, dataset_name=dataset_name, project_id=project_id, location=location)
        return self._execute(
            method=self.client.projects().locations().datasets().fhirStores().fhir().create,
            parent=parent,
            type=resource.get_resource_type(),
            body=as_json(resource),
        )

    def update_resource(
        self,
        resource: DomainResource,
        store_name: str,
        dataset_name: str,
        project_id: str = None,
        location: str = None,
    ) -> DomainResource:
        name = self._resource_path(
            resource_type=resource.get_resource_type(),
            resource_id=resource.id,
            store_name=store_name,
            dataset_name=dataset_name,
            project_id=project_id,
            location=location,
        )

        data = self._execute(
            method=self.client.projects().locations().datasets().fhirStores().fhir().update,
            name=name,
            body=as_json(resource),
        )
        return resource.__class__(**data)

    def create_or_update_resource(
        self,
        resource: DomainResource,
        store_name: str,
        dataset_name: str,
        query: Dict[str, Any] = None,
        project_id: str = None,
        location: str = None,
    ) -> DomainResource:
        if not query:
            identifiers: List[Identifier] = getattr(resource, "identifier")
            if not identifiers:
                raise exceptions.ValidationError("Either `query` or identifiers must be provided to create-or-update")

            query_values = []
            for identifier in identifiers:
                query_values.append(identifier.system)
                query_values.append(identifier.value)
            query = {"identifier": "|".join(query_values)}

        parent = self._store_path(
            name=store_name,
            dataset_name=dataset_name,
            project_id=project_id,
            location=location,
        )
        url = f"{self._base_url}/{parent}/fhir/{resource.get_resource_type()}"

        params = dict(
            url=url,
            params=query,
            headers={"Content-Type": "application/fhir+json;charset=utf-8"},
            json=as_json(resource),
        )

        try:
            data = self._execute(method=self._session.put, **params)
        except exceptions.OperationError as exc:
            if exc.errors[0]["code"] == "conflict":
                raise exceptions.FailedPrecondition(
                    f"{resource.get_resource_type()} with query {query} matches multiple resources at {parent}"
                )
            raise

        return resource.__class__(**data)

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
        resource: DomainResource,
        store_name: str,
        dataset_name: str,
        project_id: str = None,
        location: str = None,
    ) -> ResourceType:
        name = self._resource_path(
            resource_type=resource.get_resource_type(),
            resource_id=resource.id,
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
            yield resource.__class__(**entry["resource"])
