# More Information: https://cloud.google.com/healthcare-api/docs/reference/rest
import abc
import json
import logging
import math
from collections.abc import Callable, Generator
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl, urlsplit

from fhir.resources.domainresource import DomainResource
from fhir.resources.identifier import Identifier

from gcp_pilot import exceptions
from gcp_pilot.base import DiscoveryMixin, GoogleCloudPilotAPI, ResourceType, friendly_http_error

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

    def _set_location(self, location: str | None = None) -> str:
        # Only some limited regions are available: https://cloud.google.com/healthcare-api/docs/concepts/regions
        valid_locations = [
            "northamerica-northeast1",
            "us-central1",
            "us-east1",
            "us-east4",
            "us-west1",
            "us-west2",
            "us-west3",
            "southamerica-east1",
            "europe-west2",
            "europe-west3",
            "europe-west4",
            "europe-west6",
            "asia-east1",
            "asia-east2",
            "asia-northeast1",
            "asia-northeast2",
            "asia-northeast3",
            "asia-south1",
            "asia-southeast1",
            "asia-southeast2",
            "australia-southeast1",
        ]
        location = super()._set_location(location=location)
        if location not in valid_locations:
            logger.warning(f"The location {location} is not available for Healthcare API yet. Using multi-region US.")
            location = "us"
        return location

    def _dataset_path(self, name: str, project_id: str | None = None, location: str | None = None) -> str:
        location_path = self._location_path(project_id=project_id, location=location)
        return f"{location_path}/datasets/{name}"

    def list_datasets(
        self,
        project_id: str | None = None,
        location: str | None = None,
    ) -> Generator[ResourceType, None, None]:
        params = dict(
            parent=self._location_path(project_id=project_id, location=location),
        )

        yield from self._list(
            method=self.client.projects().locations().datasets().list,
            result_key="datasets",
            params=params,
        )

    def get_dataset(self, name: str, project_id: str | None = None, location: str | None = None) -> ResourceType:
        name = self._dataset_path(name=name, project_id=project_id, location=location)

        return self._execute(
            method=self.client.projects().locations().datasets().get,
            name=name,
        )

    def delete_dataset(self, name: str, project_id: str | None = None, location: str | None = None) -> ResourceType:
        name = self._dataset_path(name=name, project_id=project_id, location=location)

        return self._execute(
            method=self.client.projects().locations().datasets().delete,
            name=name,
        )

    def create_dataset(
        self,
        name: str,
        project_id: str | None = None,
        location: str | None = None,
    ) -> ResourceType:
        parent = self._location_path(project_id=project_id, location=location)

        body = {}

        return self._execute(
            method=self.client.projects().locations().datasets().create,
            parent=parent,
            datasetId=name,
            body=body,
        )


def as_json(resource: DomainResource) -> dict[str, Any]:
    return json.loads(resource.json())


@dataclass
class FHIRResultSet:
    method: Callable
    url: str
    resource_class: type[DomainResource]
    query: dict[str, Any] | None = None
    order_by: str | None = None
    limit: int | None = None
    cursor: str | None = None
    _response: dict | None = None

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

    def __iter__(self) -> Generator[dict, None, None]:
        while True:
            yield from self.get_page_resources()
            self.cursor = self.next_cursor
            if not self.cursor:
                break
            self._request()

    def first(self) -> dict:
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
    def next_cursor(self) -> str | None:
        for link in self.response["link"]:
            if link["relation"] == "next":
                query_params = dict(parse_qsl(urlsplit(link["url"]).query))
                return query_params.get("_page_token")
        return None

    @property
    def previous_cursor(self) -> str | None:
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
    def _store_path(
        self,
        name: str,
        dataset_name: str,
        project_id: str | None = None,
        location: str | None = None,
    ) -> str:
        dataset_path = self._dataset_path(name=dataset_name, project_id=project_id, location=location)
        return f"{dataset_path}/fhirStores/{name}"

    def _resource_path(
        self,
        resource_type: str,
        resource_id: str,
        store_name: str,
        dataset_name: str,
        project_id: str | None = None,
        location: str | None = None,
    ) -> str:
        store_path = self._store_path(
            name=store_name,
            dataset_name=dataset_name,
            project_id=project_id,
            location=location,
        )
        return f"{store_path}/fhir/{resource_type}/{resource_id}"

    def _operation_path(
        self,
        operation_id: str,
        dataset_name: str,
        project_id: str | None = None,
        location: str | None = None,
    ) -> str:
        dataset_path = self._dataset_path(name=dataset_name, project_id=project_id, location=location)
        return f"{dataset_path}/operations/{operation_id}"

    def list_stores(
        self,
        dataset_name: str,
        project_id: str | None = None,
        location: str | None = None,
    ) -> Generator[ResourceType, None, None]:
        params = dict(
            parent=self._dataset_path(name=dataset_name, project_id=project_id, location=location),
        )

        yield from self._list(
            method=self.client.projects().locations().datasets().fhirStores().list,
            result_key="fhirStores",
            params=params,
        )

    def get_store(
        self,
        name: str,
        dataset_name: str,
        project_id: str | None = None,
        location: str | None = None,
    ) -> ResourceType:
        name = self._store_path(name=name, dataset_name=dataset_name, project_id=project_id, location=location)

        return self._execute(
            method=self.client.projects().locations().datasets().fhirStores().get,
            name=name,
        )

    def delete_store(
        self,
        name: str,
        dataset_name: str,
        project_id: str | None = None,
        location: str | None = None,
    ) -> ResourceType:
        name = self._store_path(name=name, dataset_name=dataset_name, project_id=project_id, location=location)

        return self._execute(
            method=self.client.projects().locations().datasets().fhirStores().delete,
            name=name,
        )

    def list_resources(
        self,
        store_name: str,
        dataset_name: str,
        resource_class: type[DomainResource],
        project_id: str | None = None,
        location: str | None = None,
        query: dict[str, Any] | None = None,
        limit: int = 100,
        cursor: str | None = None,
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
        labels: dict[str, str] | None = None,
        enable_upsert: bool = True,
        notify_pubsub_topic: str | None = None,
        notify_pubsub_full_resource: bool = False,
        notify_pubsub_deletion: bool = True,
        export_to_bigquery_dataset: str | None = None,
        project_id: str | None = None,
        location: str | None = None,
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
            if "/" not in notify_pubsub_topic:
                notify_pubsub_topic = f"projects/{(project_id or self.project_id)}/topics/{notify_pubsub_topic}"
            body["notificationConfigs"] = [
                {
                    {
                        "pubsubTopic": notify_pubsub_topic,
                        "sendFullResource": notify_pubsub_full_resource,
                        "sendPreviousResourceOnDelete": notify_pubsub_deletion,
                    },
                },
            ]

        if export_to_bigquery_dataset:
            if "." not in export_to_bigquery_dataset:
                export_to_bigquery_dataset = f"{(project_id or self.project_id)}.{export_to_bigquery_dataset}"

            body["streamConfigs"] = [
                {
                    "resourceTypes": [],  # empty means all
                    "bigqueryDestination": {
                        "datasetUri": f"bq://{export_to_bigquery_dataset}",
                        "schemaConfig": {
                            "schemaType": "ANALYTICS_V2",
                            "recursiveStructureDepth": 5,  # max depth
                        },
                        "writeDisposition": "WRITE_TRUNCATE",
                    },
                },
            ]

        return self._execute(
            method=self.client.projects().locations().datasets().fhirStores().create,
            parent=parent,
            body=body,
            fhirStoreId=name,
        )

    def update_store(
        self,
        name: str,
        dataset_name: str,
        labels: dict[str, str] | None = None,
        notify_pubsub_topic: str | None = None,
        notify_pubsub_full_resource: bool = False,
        notify_pubsub_deletion: bool = True,
        export_to_bigquery_dataset: str | None = None,
        project_id: str | None = None,
        location: str | None = None,
    ) -> ResourceType:
        name = self._store_path(name=name, dataset_name=dataset_name, project_id=project_id, location=location)
        update_fields = []
        body = {}

        if labels:
            update_fields.append("labels")
            body["labels"] = labels

        if notify_pubsub_topic:
            update_fields.append("notificationConfigs")
            if "/" not in notify_pubsub_topic:
                notify_pubsub_topic = f"projects/{(project_id or self.project_id)}/topics/{notify_pubsub_topic}"
            body["notificationConfigs"] = [
                {
                    "pubsubTopic": notify_pubsub_topic,
                    "sendFullResource": notify_pubsub_full_resource,
                    "sendPreviousResourceOnDelete": notify_pubsub_deletion,
                },
            ]

        if export_to_bigquery_dataset:
            update_fields.append("streamConfigs")
            if "." not in export_to_bigquery_dataset:
                export_to_bigquery_dataset = f"{(project_id or self.project_id)}.{export_to_bigquery_dataset}"

            body["streamConfigs"] = [
                {
                    "resourceTypes": [],  # empty means all
                    "bigqueryDestination": {
                        "datasetUri": f"bq://{export_to_bigquery_dataset}",
                        "schemaConfig": {
                            "schemaType": "ANALYTICS_V2",
                            "recursiveStructureDepth": 5,  # max depth
                        },
                        "writeDisposition": "WRITE_TRUNCATE",
                    },
                },
            ]

        return self._execute(
            method=self.client.projects().locations().datasets().fhirStores().patch,
            name=name,
            updateMask=", ".join(update_fields),
            body=body,
        )

    def get_resource(
        self,
        resource_class: type[DomainResource],
        resource_id: str,
        store_name: str,
        dataset_name: str,
        project_id: str | None = None,
        location: str | None = None,
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
        resource_class: type[DomainResource],
        resource_id: str,
        store_name: str,
        dataset_name: str,
        project_id: str | None = None,
        location: str | None = None,
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
        project_id: str | None = None,
        location: str | None = None,
    ) -> DomainResource:
        parent = self._store_path(name=store_name, dataset_name=dataset_name, project_id=project_id, location=location)
        data = self._execute(
            method=self.client.projects().locations().datasets().fhirStores().fhir().create,
            parent=parent,
            type=resource.get_resource_type(),
            body=as_json(resource),
        )
        return resource.__class__(**data)

    def update_resource(
        self,
        resource: DomainResource,
        store_name: str,
        dataset_name: str,
        project_id: str | None = None,
        location: str | None = None,
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

    def patch_update(
        self,
        resource_class: type[DomainResource],
        data: dict,
        resource_id: str,
        store_name: str,
        dataset_name: str,
        project_id: str | None = None,
        location: str | None = None,
    ) -> DomainResource:
        name = self._resource_path(
            resource_type=resource_class.get_resource_type(),
            resource_id=resource_id,
            store_name=store_name,
            dataset_name=dataset_name,
            project_id=project_id,
            location=location,
        )
        body = [{"op": "replace", "path": f"/{key}", "value": value} for key, value in data.items()]
        data = self._execute(
            method=self.client.projects().locations().datasets().fhirStores().fhir().patch,
            method_http_headers={"Content-Type": "application/json-patch+json"},
            name=name,
            body=body,
        )
        return resource_class(**data)

    def create_or_update_resource(
        self,
        resource: DomainResource,
        store_name: str,
        dataset_name: str,
        query: dict[str, Any] | None = None,
        project_id: str | None = None,
        location: str | None = None,
    ) -> DomainResource:
        if not query:
            identifiers: list[Identifier] = getattr(resource, "identifier")
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
                    f"{resource.get_resource_type()} with query {query} matches multiple resources at {parent}",
                ) from exc
            raise

        return resource.__class__(**data)

    def export_resources(
        self,
        gcs_path: str,
        store_name: str,
        dataset_name: str,
        project_id: str | None = None,
        location: str | None = None,
        resource_names: list[str] | None = None,
    ) -> dict[str, str]:
        name = self._store_path(name=store_name, dataset_name=dataset_name, project_id=project_id, location=location)
        body = {"gcsDestination": {"uriPrefix": f"gs://{gcs_path}"}}
        if resource_names:
            body["_type"] = ",".join(resource_names)
        data = self._execute(
            method=self.client.projects().locations().datasets().fhirStores().export,
            name=name,
            body=body,
        )

        _, project_id, _, location, _, dataset_name, _, operation_id = data["name"].split("/")
        return {
            "project_id": project_id,
            "location": location,
            "dataset_name": dataset_name,
            "operation_id": operation_id,
        }

    def get_operation(
        self,
        operation_id: str,
        dataset_name: str,
        project_id: str | None = None,
        location: str | None = None,
    ) -> ResourceType:
        name = self._operation_path(
            operation_id=operation_id,
            dataset_name=dataset_name,
            project_id=project_id,
            location=location,
        )
        return self._execute(
            method=self.client.projects().locations().datasets().operations().get,
            name=name,
        )

    def import_resources(
        self,
        gcs_path: str,
        store_name: str,
        dataset_name: str,
        project_id: str | None = None,
        location: str | None = None,
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
        resource_class: type[DomainResource],
        resource_id: str,
        store_name: str,
        dataset_name: str,
        project_id: str | None = None,
        location: str | None = None,
    ) -> tuple[str, ResourceType | None]:
        name = self._resource_path(
            resource_type=resource_class.get_resource_type(),
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
            method = entry["request"]["method"]
            version = resource_class(**entry["resource"]) if "resource" in entry else None
            yield method, version

    def validate_resource(
        self,
        resource: DomainResource,
        store_name: str,
        dataset_name: str,
        project_id: str | None = None,
        location: str | None = None,
    ):
        parent = self._store_path(
            name=store_name,
            dataset_name=dataset_name,
            project_id=project_id,
            location=location,
        )

        try:
            self._execute(
                method=self.client.projects().locations().datasets().fhirStores().fhir().Resource_validate,
                parent=parent,
                type=resource.get_resource_type(),
                body=as_json(resource),
            )
        except exceptions.OperationError as exc:
            errors = [{"fields": error.get("expression", None), "detail": error["diagnostics"]} for error in exc.errors]
            raise exceptions.ValidationError(errors) from exc
