# More Information: https://cloud.google.com/api-keys/docs/reference/rest
from collections.abc import Generator
from dataclasses import dataclass
from datetime import UTC, datetime

from gcp_pilot.base import DiscoveryMixin, GoogleCloudPilotAPI
from gcp_pilot.exceptions import NotAllowed


@dataclass
class Key:
    raw: dict
    project_id: str

    @property
    def key_id(self) -> str:
        return self.raw["name"].rsplit("/", 1)[-1]

    @property
    def uid(self) -> str:
        return self.raw["uid"]

    @property
    def etag(self) -> str:
        return self.raw["etag"]

    @property
    def api_targets(self) -> list:
        return self.raw["restrictions"].get("apiTargets", [])

    @property
    def display_name(self) -> str:
        return self.raw["displayName"]

    @property
    def created_at(self) -> datetime:
        return datetime.strptime(self.raw["createTime"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=UTC)

    @property
    def updated_at(self) -> datetime:
        return datetime.strptime(self.raw["updateTime"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=UTC)

    @property
    def value(self) -> str:
        data = APIKey().get_key_string(key_id=self.key_id)
        return data["keyString"]


class APIKey(DiscoveryMixin, GoogleCloudPilotAPI):
    def __init__(self, **kwargs):
        super().__init__(
            serviceName="apikeys",
            version="v2",
            location="global",
            **kwargs,
        )

    def _key_path(self, key_id: str, project_id: str | None = None) -> str:
        location_path = self._location_path(project_id=project_id)
        return f"{location_path}/keys/{key_id}"

    def lookup(self, key: str):
        data = self._execute(
            method=self.client.keys().lookupKey,
            keyString=key,
        )
        project_number = data["name"].split("/", 2)[1]
        key_id = data["name"].rsplit("/", 1)[-1]
        return self.get(key_id=key_id, project_id=project_number)

    def exists(self, key: str) -> bool:
        try:
            self._execute(
                method=self.client.keys().lookupKey,
                keyString=key,
            )
        except NotAllowed:
            return False
        return True

    def get(self, key_id: str, project_id: str | None = None) -> Key:
        data = self._execute(
            method=self.client.projects().locations().keys().get,
            name=self._key_path(key_id=key_id, project_id=project_id),
        )
        return Key(raw=data, project_id=project_id or self.project_id)

    def create(
        self,
        key_id: str,
        display_name: str = "",
        api_targets: list[str] | None = None,
        project_id: str | None = None,
    ) -> dict:
        body = {
            "displayName": display_name,
            "restrictions": {},
        }
        if api_targets:
            body["restrictions"]["apiTargets"] = [{"service": service} for service in api_targets]

        return self._execute(
            method=self.client.projects().locations().keys().create,
            parent=self._location_path(project_id=project_id),
            keyId=key_id,
            body=body,
        )

    def delete(self, key_id: str, project_id: str | None = None):
        return self._execute(
            method=self.client.projects().locations().keys().delete,
            name=self._key_path(key_id=key_id, project_id=project_id),
        )

    def undelete(self, key_id: str, project_id: str | None = None):
        return self._execute(
            method=self.client.projects().locations().keys().undelete,
            name=self._key_path(key_id=key_id, project_id=project_id),
        )

    def list(self, project_id: str | None = None) -> Generator[Key, None, None]:
        params = dict(parent=self._location_path(project_id=project_id))
        data = self._paginate(
            method=self.client.projects().locations().keys().list,
            result_key="keys",
            params=params,
        )
        for item in data:
            yield Key(raw=item, project_id=project_id or self.project_id)

    def get_key_string(self, key_id: str, project_id: str | None = None) -> dict:
        return self._execute(
            method=self.client.projects().locations().keys().getKeyString,
            name=self._key_path(key_id=key_id, project_id=project_id),
        )
