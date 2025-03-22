# Reference: https://developers.google.com/drive/api/reference/rest/v3

from typing import Any

from gcp_pilot.base import DiscoveryMixin, GoogleCloudPilotAPI


class BaseDrive(GoogleCloudPilotAPI):
    _scopes = ["https://www.googleapis.com/auth/drive"]

    def __init__(self, **kwargs):
        super().__init__(serviceName="drive", version="v3", **kwargs)


class GoogleDrivePermissions(DiscoveryMixin, BaseDrive):
    @property
    def _resource(self):
        return self.client.permissions()

    def create_for_domain(
        self,
        file_id: str,
        role: str,
        domain: str,
        extra_permission_body: dict[str, Any] | None = None,
        **kwargs,
    ):
        body = {
            "role": role,
            "type": "domain",
            "domain": domain,
        } | (extra_permission_body or {})

        return self._execute(self._resource.create, fileId=file_id, body=body, **kwargs)

    def create_for_group(
        self,
        file_id: str,
        role: str,
        email: str,
        extra_permission_body: dict | None = None,
        **kwargs,
    ):
        body = {
            "role": role,
            "type": "group",
            "emailAddress": email,
        } | (extra_permission_body or {})
        return self._execute(self._resource.create, fileId=file_id, body=body, **kwargs)

    def create_for_anyone(
        self,
        file_id: str,
        role: str,
        extra_permission_body: dict | None = None,
        **kwargs,
    ):
        body = {
            "role": role,
            "type": "anyone",
        } | (extra_permission_body or {})
        return self._execute(self._resource.create, fileId=file_id, body=body, **kwargs)

    def create_for_user(
        self,
        file_id: str,
        role: str,
        email: str,
        extra_permission_body: dict | None = None,
        **kwargs,
    ):
        body = {
            "role": role,
            "type": "user",
            "emailAddress": email,
        } | (extra_permission_body or {})
        return self._execute(self._resource.create, fileId=file_id, body=body, **kwargs)

    def delete(self, permission_id: str, file_id: str):
        return self._execute(self._resource.delete, fileId=file_id, permissionId=permission_id)

    def list(self, file_id: str, **kwargs):
        return self._paginate(
            self._resource.list,
            result_key="permissions",
            params={"fileId": file_id},
            **kwargs,
        )

    def update(self, permission_id: str, file_id: str, body: dict, **kwargs):
        return self._execute(
            self._resource.update,
            fileId=file_id,
            permissionId=permission_id,
            body=body,
            **kwargs,
        )

    def get(self, permission_id: str, file_id: str, **kwargs):
        return self._execute(self._resource.get, fileId=file_id, permissionId=permission_id, **kwargs)


__all__ = ("GoogleDrivePermissions",)
