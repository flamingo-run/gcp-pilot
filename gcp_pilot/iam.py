# More Information: <https://cloud.google.com/iam/docs/reference/rest>
import base64
import json
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Any

import requests
from google.auth import jwt
from google.cloud import iam_credentials_v1

from gcp_pilot import exceptions
from gcp_pilot.base import AccountManagerMixin, DiscoveryMixin, GoogleCloudPilotAPI, PolicyType, friendly_http_error

AccountType = dict[str, Any]
KeyType = dict[str, Any]


IDP_JWT_AUDIENCE = "https://identitytoolkit.googleapis.com/google.identity.identitytoolkit.v1.IdentityToolkit"


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
        yield from pagination

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


class IAMCredentials(GoogleCloudPilotAPI):
    _client_class = iam_credentials_v1.IAMCredentialsClient

    @friendly_http_error
    def encode_jwt(self, payload: dict, service_account_email: str | None) -> str:
        max_expiration = 12 * 60 * 60
        if "iat" not in payload:
            payload["iat"] = datetime.now(tz=UTC).timestamp()
        if "exp" not in payload:
            payload["exp"] = datetime.now(tz=UTC).timestamp() + max_expiration
        elif payload["exp"] - datetime.now(tz=UTC).timestamp() > max_expiration:
            raise ValueError("JWT tokens cannot be valid for more than 12 hours")

        payload["iam"] = int(payload["iat"])
        payload["exp"] = int(payload["exp"])

        response = self.client.sign_jwt(
            name=self.client.service_account_path(service_account=service_account_email, project="-"),
            payload=json.dumps(payload),
        )
        return response.signed_jwt

    @friendly_http_error
    def generate_id_token(self, audience: str, service_account_email: str | None = None) -> str:
        response = self.client.generate_id_token(
            name=self.client.service_account_path(
                service_account=service_account_email or self.service_account_email,
                project="-",
            ),
            audience=audience,
        )
        return response.token

    @classmethod
    def decode_jwt(cls, token: str, issuer_email: str, audience: str | None, verify: bool = True) -> dict[str, Any]:
        certs = cls._fetch_public_certs(email=issuer_email)
        return dict(
            jwt.decode(
                token=token,
                certs=certs,
                audience=audience,
                verify=verify,
            ),
        )

    @classmethod
    def decode_id_token(cls, token: str, issuer_email: str, verify: bool = True) -> dict[str, Any]:
        return cls.decode_jwt(
            token=token,
            issuer_email=issuer_email,
            audience=IDP_JWT_AUDIENCE,
            verify=verify,
        )

    def generate_custom_token(
        self,
        uid: str,
        expires_in_seconds: int,
        tenant_id: str | None = None,
        auth_email: str | None = None,
        claims: dict | None = None,
    ) -> str:
        authenticator_email = auth_email or self.service_account_email
        payload = {
            "iat": datetime.now(tz=UTC).timestamp(),
            "exp": (datetime.now(tz=UTC) + timedelta(seconds=expires_in_seconds)).timestamp(),
            "aud": IDP_JWT_AUDIENCE,
            "iss": authenticator_email,
            "sub": authenticator_email,
            "email": authenticator_email,
            "uid": uid,
            "tenant_id": tenant_id,
            "claims": claims or {},
        }

        return self.encode_jwt(
            payload=payload,
            service_account_email=authenticator_email,
        )

    @classmethod
    def _fetch_public_certs(cls, email: str) -> dict:
        url = f"https://www.googleapis.com/robot/v1/metadata/x509/{email}"
        response = requests.get(url=url, timeout=5)
        return response.json()


__all__ = (
    "IdentityAccessManager",
    "IAMCredentials",
)
