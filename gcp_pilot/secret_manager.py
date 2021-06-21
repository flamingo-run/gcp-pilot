# More Information: <https://googleapis.dev/python/secretmanager/latest/index.html>
from typing import List, Tuple

from google.api_core.exceptions import NotFound
from google.cloud import secretmanager

from gcp_pilot.base import GoogleCloudPilotAPI


class SecretManager(GoogleCloudPilotAPI):
    _client_class = secretmanager.SecretManagerServiceClient

    def _secret_path(self, key: str, project_id: str = None) -> str:
        parent = self._project_path(project_id=project_id)
        return f"{parent}/secrets/{key}"

    def _secret_version_path(self, key: str, version: int = None, project_id: str = None):
        parent = self._secret_path(key=key, project_id=project_id)
        version_str = str(version) if version else "latest"
        return f"{parent}/versions/{version_str}"

    def _create_secret(self, key: str, project_id: str = None):
        parent = self._project_path(project_id=project_id)

        return self.client.create_secret(
            request={
                "parent": parent,
                "secret_id": key,
                "secret": {"replication": {"automatic": {}}},
            }
        )

    def _create_version(self, key: str, value: str, project_id: str = None):
        parent = self._secret_path(key=key, project_id=project_id)

        return self.client.add_secret_version(request={"parent": parent, "payload": {"data": value.encode()}})

    def list_secrets(self, prefix: str = None, suffix: str = None, project_id: str = None) -> List[Tuple[str, str]]:
        parent = self._project_path(project_id=project_id)
        secrets = self.client.list_secrets(
            request={
                "parent": parent,
            }
        )
        for secret in secrets:
            name = secret.name.rsplit("secrets/", 1)[-1]
            if prefix and not name.startswith(prefix=prefix):
                continue
            if suffix and not name.endswith(suffix=suffix):
                continue
            yield name, self.get_secret(key=name, project_id=project_id)

    def add_secret(self, key: str, value: str, project_id: str = None) -> str:
        try:
            version = self._create_version(
                key=key,
                value=value,
                project_id=project_id,
            )
        except NotFound:
            self._create_secret(
                key=key,
                project_id=project_id,
            )
            version = self._create_version(
                key=key,
                value=value,
                project_id=project_id,
            )
        return version.name

    def get_secret(self, key: str, version: int = None, project_id: str = None) -> str:
        response = self.client.access_secret_version(
            request={"name": self._secret_version_path(key=key, version=version, project_id=project_id)}
        )
        return response.payload.data.decode()

    def rollback_secret(self, key: str, temporarily: bool = False, project_id: str = None):
        secret_path = self._secret_version_path(key=key, project_id=project_id)

        if temporarily:
            response = self.client.disable_secret_version(request={"name": secret_path})
        else:
            response = self.client.destroy_secret_version(request={"name": secret_path})
        return response


__all__ = ("SecretManager",)
