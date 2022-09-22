# More Information: <https://cloud.google.com/iam/docs/reference/rest>
import base64
from typing import Any, Generator

from gcp_pilot import exceptions
from gcp_pilot.base import AccountManagerMixin, DiscoveryMixin, GoogleCloudPilotAPI, PolicyType

AccountType = dict[str, Any]
KeyType = dict[str, Any]


class IdentityAccessManager(AccountManagerMixin, DiscoveryMixin, GoogleCloudPilotAPI):
    def __init__(self, **kwargs):
        super().__init__(
            serviceName="iam",
            version="v1",
            cache_discovery=False,
            **kwargs,
        )

    def _service_account_path(self, email: str, project_id: str | None = None) -> str:
        parent_path = self._project_path(project_id=project_id)
        return f"{parent_path}/serviceAccounts/{email}"

    def _key_path(self, key_id: str, email: str, project_id: str | None = None) -> str:
        parent_path = self._service_account_path(email=email, project_id=project_id)
        return f"{parent_path}/keys/{key_id}"

    def _build_service_account_email(self, name: str, project_id: str | None = None) -> str:
        return f"{name}@{project_id or self.project_id}.iam.gserviceaccount.com"

    def get_service_account(self, name: str, project_id: str | None = None) -> AccountType:
        account_path = self._service_account_path(
            email=self._build_service_account_email(name=name, project_id=project_id),
            project_id=project_id,
        )

        return self._execute(
            method=self.client.projects().serviceAccounts().get,
            name=account_path,
        )

    def create_service_account(
        self,
        name: str,
        display_name: str,
        project_id: str | None = None,
        exists_ok: bool = True,
    ) -> AccountType:
        try:
            body = {"accountId": name, "serviceAccount": {"displayName": display_name}}
            service_account = self._execute(
                method=self.client.projects().serviceAccounts().create,
                name=self._project_path(project_id=project_id),
                body=body,
            )
        except exceptions.AlreadyExists:
            if not exists_ok:
                raise
            service_account = self.get_service_account(name=name, project_id=project_id)
        return service_account

    def list_service_accounts(self, project_id: str | None = None) -> Generator[AccountType, None, None]:
        params = dict(
            name=self._project_path(project_id=project_id),
        )
        pagination = self._paginate(
            method=self.client.projects().serviceAccounts().list,
            result_key="accounts",
            params=params,
        )
        for item in pagination:
            yield item

    def get_policy(self, email: str, project_id: str | None = None) -> PolicyType:
        resource = self._service_account_path(email=email, project_id=project_id)
        return self._execute(
            method=self.client.projects().serviceAccounts().getIamPolicy,
            resource=resource,
        )

    def _as_member(self, email: str) -> str:
        is_service_account = email.endswith(".gserviceaccount.com")
        prefix = "serviceAccount" if is_service_account else "member"
        return f"{prefix}:{email}"

    def bind_member(self, target_email: str, member_email: str, role: str, project_id=None) -> PolicyType:
        policy = self.get_policy(email=target_email, project_id=project_id)
        changed_policy = self._bind_email_to_policy(email=member_email, role=role, policy=policy)
        return self.set_policy(email=target_email, policy=changed_policy, project_id=project_id)

    def remove_member(
        self,
        target_email: str,
        member_email: str,
        role: str,
        project_id: str | None = None,
    ) -> PolicyType:
        policy = self.get_policy(email=target_email, project_id=project_id)
        changed_policy = self._unbind_email_from_policy(email=member_email, role=role, policy=policy)
        return self.set_policy(email=target_email, policy=changed_policy, project_id=project_id)

    def set_policy(self, email: str, policy: PolicyType, project_id: str | None = None) -> PolicyType:
        resource = self._service_account_path(email=email, project_id=project_id)
        return self._execute(
            method=self.client.projects().serviceAccounts().setIamPolicy,
            resource=resource,
            body={"policy": policy, "updateMask": "bindings"},
        )

    def get_key(self, key_id: str, service_account_name: str, project_id: str | None = None) -> KeyType:
        key_path = self._key_path(
            key_id=key_id,
            email=self._build_service_account_email(name=service_account_name, project_id=project_id),
            project_id=project_id,
        )

        return self._execute(
            method=self.client.projects().serviceAccounts().key().get,
            name=key_path,
        )

    def delete_key(self, key_id: str, service_account_name: str, project_id: str | None = None) -> KeyType:
        key_path = self._key_path(
            key_id=key_id,
            email=self._build_service_account_email(name=service_account_name, project_id=project_id),
            project_id=project_id,
        )

        return self._execute(
            method=self.client.projects().serviceAccounts().keys().delete,
            name=key_path,
        )

    def create_key(
        self,
        service_account_name: str,
        project_id: str | None = None,
    ) -> KeyType:
        body = {}
        parent = self._service_account_path(
            email=self._build_service_account_email(name=service_account_name, project_id=project_id),
            project_id=project_id,
        )
        account_key = self._execute(
            method=self.client.projects().serviceAccounts().keys().create,
            name=parent,
            body=body,
        )
        return self._format_key(data=account_key)

    def list_keys(self, service_account_name: str, project_id: str | None = None) -> Generator[KeyType, None, None]:
        parent = self._service_account_path(
            email=self._build_service_account_email(name=service_account_name, project_id=project_id),
            project_id=project_id,
        )
        params = dict(
            name=parent,
        )
        pagination = self._list(
            method=self.client.projects().serviceAccounts().keys().list,
            result_key="keys",
            params=params,
        )
        for item in pagination:
            yield self._format_key(data=item)

    def _format_key(self, data: dict) -> dict:
        prefix, suffix = data["name"].split("/keys/", 1)
        data["id"] = suffix
        data["service_account_email"] = prefix.rsplit("/", 1)[-1]
        data["service_account_name"] = data["service_account_email"].rsplit("@", 1)[0]

        if "privateKeyData" in data:
            data["json"] = base64.b64decode(data["privateKeyData"]).decode()
        return data


__all__ = ("IdentityAccessManager",)
