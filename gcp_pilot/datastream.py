from collections.abc import Generator

from gcp_pilot.base import DiscoveryMixin, GoogleCloudPilotAPI, ResourceType


class Datastream(DiscoveryMixin, GoogleCloudPilotAPI):
    def __init__(self, **kwargs):
        super().__init__(
            serviceName="datastream",
            version="v1",
            cache_discovery=False,
            **kwargs,
        )

    def _stream_path(self, stream_name: str, location: str | None = None, project_id: str | None = None) -> str:
        location_path = self._location_path(location=location, project_id=project_id)
        return f"{location_path}/streams/{stream_name}"

    def _object_path(
        self,
        object_id: str,
        stream_name: str,
        location: str | None = None,
        project_id: str | None = None,
    ) -> str:
        stream_path = self._stream_path(stream_name=stream_name, location=location, project_id=project_id)
        return f"{stream_path}/objects/{object_id}"

    def get_streams(
        self,
        location: str | None = None,
        project_id: str | None = None,
    ) -> Generator[ResourceType, None, None]:
        location_path = self._location_path(location=location, project_id=project_id)
        params = {"parent": location_path}
        yield from self._paginate(
            method=self.client.projects().locations().streams().list,
            result_key="streams",
            params=params,
        )

    def get_stream(self, stream_name: str, location: str | None = None, project_id: str | None = None):
        name = self._stream_path(stream_name=stream_name, location=location, project_id=project_id)
        return self._execute(
            method=self.client.projects().locations().streams().get,
            name=name,
        )

    def delete_stream(self, stream_name: str, location: str | None = None, project_id: str | None = None):
        name = self._stream_path(stream_name=stream_name, location=location, project_id=project_id)
        return self._execute(
            method=self.client.projects().locations().streams().delete,
            name=name,
        )

    def get_objects(
        self,
        stream_name: str,
        location: str | None = None,
        project_id: str | None = None,
    ) -> Generator[ResourceType, None, None]:
        stream_path = self._stream_path(stream_name=stream_name, location=location, project_id=project_id)
        params = {"parent": stream_path}
        yield from self._paginate(
            method=self.client.projects().locations().streams().objects().list,
            result_key="streamObjects",
            params=params,
        )

    def get_object(
        self,
        object_id: str,
        stream_name: str,
        location: str | None = None,
        project_id: str | None = None,
    ):
        name = self._object_path(
            object_id=object_id,
            stream_name=stream_name,
            location=location,
            project_id=project_id,
        )
        return self._execute(
            method=self.client.projects().locations().streams().objects().get,
            name=name,
        )

    def find_object(
        self,
        schema: str,
        table: str,
        stream_name: str,
        location: str | None = None,
        project_id: str | None = None,
    ):
        stream_path = self._stream_path(stream_name=stream_name, location=location, project_id=project_id)
        body = {
            "sourceObjectIdentifier": {
                "postgresqlIdentifier": {"schema": schema, "table": table},
            },
        }
        return self._execute(
            method=self.client.projects().locations().streams().objects().lookup,
            parent=stream_path,
            body=body,
        )

    def start_backfill(
        self,
        schema: str,
        table: str,
        stream_name: str,
        location: str | None = None,
        project_id: str | None = None,
    ):
        object_info = self.find_object(
            schema=schema,
            table=table,
            stream_name=stream_name,
            location=location,
            project_id=project_id,
        )
        return self._execute(
            method=self.client.projects().locations().streams().objects().startBackfillJob,
            object=object_info["name"],
        )

    def stop_backfill(
        self,
        schema: str,
        table: str,
        stream_name: str,
        location: str | None = None,
        project_id: str | None = None,
    ):
        object_info = self.find_object(
            schema=schema,
            table=table,
            stream_name=stream_name,
            location=location,
            project_id=project_id,
        )

        return self._execute(
            method=self.client.projects().locations().streams().objects().stopBackfillJob,
            object=object_info["name"],
        )
