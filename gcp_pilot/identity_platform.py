# Reference <https://cloud.google.com/identity-platform/docs/apis>
import json
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from urllib.parse import parse_qs, urlparse

from google.auth.transport import requests
from google.oauth2 import id_token
from tenacity import Retrying, stop_after_attempt, wait_fixed

from gcp_pilot import exceptions
from gcp_pilot.base import DiscoveryMixin, GoogleCloudPilotAPI, ResourceType


class OOBCodeType(Enum):
    RESET = "PASSWORD_RESET"
    VERIFY = "VERIFY_EMAIL"
    SIGNIN = "EMAIL_SIGNIN"


class FirebaseProviderType(Enum):
    GOOGLE = "google"
    FACEBOOK = "facebook"
    GITHUB = "github"
    MICROSOFT = "microsoft"
    APPLE = "apple"
    PASSWORD = "password"  # TODO: check if this is correct
    PASSWORDLESS = "emailLink"


def parse_timestamp(timestamp: str | int | float) -> datetime | None:
    if not timestamp:
        return None
    if len(str(timestamp)) > 10:
        timestamp = float(timestamp) / 1000
    return datetime.fromtimestamp(float(timestamp), tz=UTC)


@dataclass
class JWTInfo:
    aud: str
    exp: datetime
    iat: datetime
    iss: str
    sub: str

    @property
    def is_expired(self) -> bool:
        return datetime.now(tz=UTC).timestamp() >= self.exp.timestamp()


@dataclass
class User:
    id: str
    email: str
    verified: bool
    disabled: bool
    created_at: datetime | None
    name: str | None = None
    photo_url: bool | None = None
    last_login_at: datetime | None = None
    password_changed_at: datetime | None = None
    extra_attributes: dict[str, str] | None = None
    tenant_id: str | None | None = None

    @classmethod
    def create(cls, data: ResourceType) -> "User":
        return cls(
            id=data["localId"],
            email=data["email"],
            verified=data.get("emailVerified"),
            disabled=data.get("disabled"),
            photo_url=data.get("photoUrl"),
            tenant_id=data.get("tenant_id"),
            created_at=parse_timestamp(timestamp=data["createdAt"]),
            last_login_at=parse_timestamp(timestamp=data.get("lastLoginAt")),
            password_changed_at=parse_timestamp(timestamp=data.get("passwordUpdatedAt")),
            extra_attributes=json.loads(data.get("customAttributes", "{}")),
        )


@dataclass
class FirebaseOAuth:
    id_token: str
    access_token: str
    refresh_token: str | None = None
    token_secret: str | None = None


@dataclass
class FirebaseAuthToken:
    jwt_token: str
    request: requests.Request | None = None
    validate_expiration: bool = True

    def __post_init__(self):
        verification_kwargs = dict(
            id_token=self.jwt_token,
            request=self.request or requests.Request(),
        )
        if not self.validate_expiration:
            verification_kwargs["clock_skew_in_seconds"] = sys.maxsize
        self._data = id_token.verify_firebase_token(**verification_kwargs)

    @property
    def provider_id(self) -> str:
        return self._data["sign_in_method"]

    @property
    def tenant_id(self) -> str | None:
        return self._data.get("tenant_id", None)

    @property
    def oauth(self) -> FirebaseOAuth | None:
        if "oauth_id_token" not in self._data:
            return None

        return FirebaseOAuth(
            id_token=self._data["oauth_id_token"],
            access_token=self._data["oauth_access_token"],
            refresh_token=self._data.get("oauth_refresh_token", None),
            token_secret=self._data.get("oauth_token_secret", None),
        )

    @property
    def event_type(self) -> str:
        return self._data["event_type"]

    @property
    def ip_address(self) -> str:
        return self._data["ip_address"]

    @property
    def user_agent(self) -> str:
        return self._data["user_agent"]

    @property
    def expiration_date(self) -> datetime:
        epoch = self._data["exp"]
        return parse_timestamp(epoch)

    @property
    def user(self) -> User:
        user_data = self._data["user_record"]
        return User(
            id=user_data["uid"],
            email=user_data.get("email"),
            name=user_data.get("display_name"),
            photo_url=user_data.get("photo_url"),
            verified=user_data.get("email_verified"),
            disabled=user_data.get("disabled"),
            tenant_id=user_data.get("tenant_id"),
            created_at=parse_timestamp(user_data["metadata"]["creation_time"]),
            last_login_at=parse_timestamp(user_data["metadata"]["last_sign_in_time"]),
        )

    @property
    def raw_user(self) -> dict:
        return json.loads(self._data["raw_user_info"])

    @property
    def event_id(self) -> dict:
        return self._data["event_id"]

    @property
    def jwt_info(self) -> JWTInfo:
        return JWTInfo(
            aud=self._data["aud"],
            exp=parse_timestamp(timestamp=self._data["exp"]),
            iat=parse_timestamp(timestamp=self._data["iat"]),
            iss=self._data["iss"],
            sub=self._data["sub"],
        )


class IdentityPlatform(DiscoveryMixin, GoogleCloudPilotAPI):
    _scopes = ["https://www.googleapis.com/auth/identitytoolkit"]

    def __init__(self, tenant_id: str | None = None, **kwargs):
        super().__init__(
            serviceName="identitytoolkit",
            version="v1",
            cache_discovery=False,
            static_discovery=False,
            **kwargs,
        )
        self.tenant_id = tenant_id

    def find(
        self,
        email: str | None = None,
        phone_number: str | None = None,
        tenant_id: str | None = None,
        project_id: str | None = None,
    ) -> User:
        try:
            return next(self.lookup(email=email, phone_number=phone_number, tenant_id=tenant_id, project_id=project_id))
        except StopIteration as exc:
            raise exceptions.NotFound() from exc

    def lookup(
        self,
        email: str | None = None,
        phone_number: str | None = None,
        tenant_id: str | None = None,
        project_id: str | None = None,
    ) -> Iterator[User]:
        if not email and not phone_number:
            raise exceptions.ValidationError("Either `email` or `phone_number` must be provided")

        data = {
            "target_project_id": project_id or self.project_id,
            "tenantId": tenant_id or self.tenant_id,
        }
        if email:
            data["email"] = email
        if phone_number:
            if not phone_number.startswith("+"):
                phone_number = f"+{phone_number}"
            data["phone_number"] = phone_number

        response = self._execute(method=self.client.accounts().lookup, body=data)
        for item in response.get("users", []):
            yield User.create(data=item)

    def sign_in_with_password(self, email: str, password: str, tenant_id: str | None = None):
        data = {
            "email": email,
            "password": password,
            "tenantId": tenant_id or self.tenant_id,
        }
        response = self._execute(method=self.client.accounts().signInWithPassword, body=data)
        return response

    def sign_in_with_phone_number(self, phone_number: str, code: str, tenant_id: str | None = None):
        data = {
            "phone_number": phone_number,
            "code": code,
            "tenantId": tenant_id or self.tenant_id,
        }
        response = self._execute(method=self.client.accounts().signInWithPhoneNumber, body=data)
        return response

    def sign_in_with_custom_token(self, token: str, tenant_id: str | None = None):
        data = {
            "token": token,
            "returnSecureToken": True,
            "tenantId": tenant_id or self.tenant_id,
        }
        response = self._execute(method=self.client.accounts().signInWithCustomToken, body=data)
        return response

    def sign_in_with_email_link(self, email: str, code: str, tenant_id: str | None = None):
        data = {
            "email": email,
            "oobCode": code,
            "tenantId": tenant_id or self.tenant_id,
        }
        response = self._execute(method=self.client.accounts().signInWithEmailLink, body=data)
        return response

    def list_users(self, tenant_id: str | None = None, project_id: str | None = None):
        params = {
            "targetProjectId": project_id or self.project_id,
            "tenantId": tenant_id or self.tenant_id,
        }
        method = self.client.projects().accounts().batchGet
        for item in self._paginate(method=method, result_key="users", pagination_key="nextPageToken", params=params):
            yield User.create(data=item)

    def generate_email_code(
        self,
        type: OOBCodeType,
        email: str,
        ip_address: str | None = None,
        project_id: str | None = None,
        send_email: bool = False,
        redirect_url: str | None = None,
        tenant_id: str | None = None,
    ) -> ResourceType:
        data = {
            "requestType": type.value,
            "email": email,
            "user_ip": ip_address,
            "continue_url": redirect_url,
            "target_project_id": project_id or self.project_id,
            "returnOobLink": not send_email,
            "tenantId": tenant_id or self.tenant_id,
        }
        response = self._execute(method=self.client.accounts().sendOobCode, body=data)

        if send_email:
            return {}

        url = response["oobLink"]
        query = parse_qs(urlparse(url).query)
        return {"url": url, "code": query["oobCode"][0]}

    def reset_password(
        self,
        email: str,
        new_password: str,
        old_password: str | None = None,
        oob_code: str | None = None,
        tenant_id: str | None = None,
    ):
        data = {
            "newPassword": new_password,
            "email": email,
            "tenantId": tenant_id or self.tenant_id,
        }

        if oob_code:
            data["oobCode"] = oob_code
        elif old_password:
            data["oldPassword"] = old_password
        else:
            raise exceptions.ValidationError("Either `old_password` or `oob_code` must be provided")

        response = self._execute(method=self.client.accounts().resetPassword, body=data)
        return response

    def delete_user(self, user_id: str, project_id: str | None = None, tenant_id: str | None = None):
        data = {
            "localId": user_id,
            "targetProjectId": project_id or self.project_id,
            "tenantId": tenant_id or self.tenant_id,
        }
        response = self._execute(method=self.client.accounts().delete, body=data)
        return response

    def disable_user(self, user_id: str, project_id: str | None = None, tenant_id: str | None = None):
        data = {
            "localId": user_id,
            "disableUser": True,
            "targetProjectId": project_id or self.project_id,
            "tenantId": tenant_id or self.tenant_id,
        }
        response = self._execute(method=self.client.accounts().update, body=data)
        return response

    def enable_user(self, user_id: str, project_id: str | None = None, tenant_id: str | None = None):
        data = {
            "localId": user_id,
            "disableUser": False,
            "targetProjectId": project_id or self.project_id,
            "tenantId": tenant_id or self.tenant_id,
        }
        response = self._execute(method=self.client.accounts().update, body=data)
        return response

    def sign_up(
        self,
        email: str,
        password: str,
        phone_number: str | None = None,
        name: str | None = None,
        photo_url: str | None = None,
        user_id: str | None = None,
        project_id: str | None = None,
        tenant_id: str | None = None,
    ):
        if phone_number and not phone_number.startswith("+"):
            phone_number = f"+{phone_number}"

        data = {
            "email": email,
            "password": password,
            "displayName": name,
            "photoUrl": photo_url,
            "disabled": False,
            "localId": user_id,
            "phoneNumber": phone_number,
            "targetProjectId": project_id or self.project_id,
            "tenantId": tenant_id or self.tenant_id,
        }
        self._execute(method=self.client.accounts().signUp, body=data)

        for attempt in Retrying(stop=stop_after_attempt(3), wait=wait_fixed(1)):
            with attempt:
                return self.find(email=email, project_id=project_id, tenant_id=tenant_id or self.tenant_id)

    def update(
        self,
        user_id: str,
        email: str | None = None,
        password: str | None = None,
        phone_number: str | None = None,
        name: str | None = None,
        photo_url: str | None = None,
        project_id: str | None = None,
        attributes: dict[str, str] | None = None,
        tenant_id: str | None = None,
        enabled: bool | None = None,
    ):
        data = {
            "localId": user_id,
            "targetProjectId": project_id or self.project_id,
            "tenantId": tenant_id or self.tenant_id,
        }
        if enabled:
            data["disableUser"] = not enabled
        if email:
            data["email"] = email
        if password:
            data["password"] = password
        if phone_number:
            if not phone_number.startswith("+"):
                phone_number = f"+{phone_number}"
            data["phoneNumber"] = phone_number
        if name:
            data["displayName"] = name
        if photo_url:
            data["photoUrl"] = photo_url
        if attributes:
            data["customAttributes"] = json.dumps(attributes)
        response = self._execute(method=self.client.accounts().update, body=data)
        return response


class IdentityPlatformAdmin(DiscoveryMixin, GoogleCloudPilotAPI):
    _scopes = ["https://www.googleapis.com/auth/identitytoolkit"]

    def __init__(self, tenant_id: str | None = None, **kwargs):
        super().__init__(
            serviceName="identitytoolkit",
            version="v2",
            cache_discovery=False,
            static_discovery=False,
            **kwargs,
        )
        self.tenant_id = tenant_id

    def _config_path(self, project_id: str | None = None) -> str:
        project_path = self._project_path(project_id=project_id)
        return f"{project_path}/config"

    def get_config(self, project_id: str | None = None) -> dict:
        config_path = self._config_path(project_id=project_id)
        response = self._execute(
            method=self.client.projects().getConfig,
            name=config_path,
        )
        return response

    def add_authorized_domains(self, domains: list[str], project_id: str | None = None) -> dict:
        config = self.get_config(project_id=project_id)
        existing_domains = set(config.get("authorizedDomains", []))
        all_domains = existing_domains.union(set(domains))
        if all_domains != existing_domains:  # only if there's new domains
            return self.set_authorized_domains(domains=list(all_domains), project_id=project_id)
        return config

    def remove_authorized_domains(self, domains: list[str], project_id: str | None = None) -> dict:
        config = self.get_config(project_id=project_id)
        existing_domains = set(config.get("authorizedDomains", []))
        all_domains = existing_domains - set(domains)
        if all_domains != existing_domains:  # only if there's domains to remove
            return self.set_authorized_domains(domains=list(all_domains), project_id=project_id)
        return config

    def set_authorized_domains(self, domains: list[str], project_id: str | None = None) -> dict:
        config_path = self._config_path(project_id=project_id)

        response = self._execute(
            method=self.client.projects().updateConfig,
            name=config_path,
            updateMask="authorizedDomains",
            body={"authorizedDomains": domains},
        )
        return response
