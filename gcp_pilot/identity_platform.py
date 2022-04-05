# Reference <https://cloud.google.com/identity-platform/docs/apis>
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional, Union, Iterator
from urllib.parse import urlparse, parse_qs

from google.auth.transport import requests
from google.oauth2 import id_token
from tenacity import Retrying, stop_after_attempt, wait_fixed

from gcp_pilot import exceptions
from gcp_pilot.base import GoogleCloudPilotAPI, DiscoveryMixin, ResourceType


class OOBCodeType(Enum):
    RESET = "PASSWORD_RESET"
    VERIFY = "VERIFY_EMAIL"
    SIGNIN = "EMAIL_SIGNIN"


def parse_timestamp(timestamp: Union[str, int, float]) -> Optional[datetime]:
    if not timestamp:
        return None
    if len(str(timestamp)) >= 10:
        timestamp = float(timestamp) / 1000
    return datetime.fromtimestamp(float(timestamp), tz=timezone.utc)


@dataclass
class User:
    id: str
    email: str
    verified: bool
    disabled: bool
    created_at: Optional[datetime]
    name: str = None
    photo_url: bool = None
    last_login_at: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None
    extra_attributes: Dict[str, str] = None

    @classmethod
    def create(cls, data: ResourceType) -> "User":
        return cls(
            id=data["localId"],
            email=data["email"],
            verified=data.get("emailVerified"),
            disabled=data.get("disabled"),
            photo_url=data.get("photoUrl"),
            created_at=parse_timestamp(timestamp=data["createdAt"]),
            last_login_at=parse_timestamp(timestamp=data.get("lastLoginAt")),
            password_changed_at=parse_timestamp(timestamp=data.get("passwordUpdatedAt")),
            extra_attributes=json.loads(data.get("customAttributes", "{}")),
        )


@dataclass
class FirebaseOAuth:
    id_token: str
    access_token: str
    refresh_token: str = None
    token_secret: str = None


@dataclass
class FirebaseAuthToken:
    jwt_token: str

    def __post_init__(self):
        self._data = id_token.verify_firebase_token(id_token=self.jwt_token, request=requests.Request())

    @property
    def provider_id(self) -> str:
        return self._data["sign_in_method"]

    @property
    def tenant_id(self) -> str:
        return self._data["tenant_id"]  # FIXME

    @property
    def oauth(self) -> FirebaseOAuth:
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
            email=user_data["email"],
            name=user_data["display_name"],
            photo_url=user_data["photo_url"],
            verified=user_data["email_verified"],
            disabled=user_data["disabled"],
            created_at=parse_timestamp(user_data["metadata"]["creation_time"]),
            last_login_at=parse_timestamp(user_data["metadata"]["last_sign_in_time"]),
        )


class IdentityPlatform(DiscoveryMixin, GoogleCloudPilotAPI):
    _scopes = ["https://www.googleapis.com/auth/identitytoolkit"]

    def __init__(self, tenant_id: str = None, **kwargs):
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
        email: str = None,
        phone_number: str = None,
        tenant_id: str = None,
        project_id: str = None,
    ) -> User:
        try:
            return next(self.lookup(email=email, phone_number=phone_number, tenant_id=tenant_id, project_id=project_id))
        except StopIteration as exc:
            raise exceptions.NotFound() from exc

    def lookup(
        self,
        email: str = None,
        phone_number: str = None,
        tenant_id: str = None,
        project_id: str = None,
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

    def sign_in_with_password(self, email: str, password: str, tenant_id: str = None):
        data = {
            "email": email,
            "password": password,
            "tenantId": tenant_id or self.tenant_id,
        }
        response = self._execute(method=self.client.accounts().signInWithPassword, body=data)
        return response

    def sign_in_with_phone_number(self, phone_number: str, code: str, tenant_id: str = None):
        data = {
            "phone_number": phone_number,
            "code": code,
            "tenantId": tenant_id or self.tenant_id,
        }
        response = self._execute(method=self.client.accounts().signInWithPhoneNumber, body=data)
        return response

    def sign_in_with_email_link(self, email: str, code: str, tenant_id: str = None):
        data = {
            "email": email,
            "oobCode": code,
            "tenantId": tenant_id or self.tenant_id,
        }
        response = self._execute(method=self.client.accounts().signInWithEmailLink, body=data)
        return response

    def generate_email_code(
        self,
        type: OOBCodeType,  # pylint: disable=redefined-builtin
        email: str,
        ip_address: str = None,
        project_id: str = None,
        send_email: bool = False,
        redirect_url: str = None,
        tenant_id: str = None,
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
        old_password: str = None,
        oob_code: str = None,
        tenant_id: str = None,
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

    def delete_user(self, user_id: str, tenant_id: str = None):
        data = {
            "localId": user_id,
            "tenantId": tenant_id or self.tenant_id,
        }
        response = self._execute(method=self.client.accounts().delete, body=data)
        return response

    def disable_user(self, user_id: str, project_id: str = None, tenant_id: str = None):
        data = {
            "localId": user_id,
            "disableUser": True,
            "targetProjectId": project_id or self.project_id,
            "tenantId": tenant_id or self.tenant_id,
        }
        response = self._execute(method=self.client.accounts().update, body=data)
        return response

    def enable_user(self, user_id: str, project_id: str = None, tenant_id: str = None):
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
        phone_number: str = None,
        name: str = None,
        photo_url: str = None,
        user_id: str = None,
        project_id: str = None,
        tenant_id: str = None,
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
                return self.find(email=email, project_id=project_id)

    def update(
        self,
        user_id: str,
        email: str = None,
        password: str = None,
        phone_number: str = None,
        name: str = None,
        photo_url: str = None,
        project_id: str = None,
        attributes: Dict[str, str] = None,
        tenant_id: str = None,
    ):
        data = {
            "localId": user_id,
            "targetProjectId": project_id or self.project_id,
            "tenantId": tenant_id or self.tenant_id,
        }
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
