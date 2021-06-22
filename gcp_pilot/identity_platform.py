# Reference <https://cloud.google.com/identity-platform/docs/apis>
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional, Union, Iterator
from urllib.parse import urlparse, parse_qs

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
    last_login_at: Optional[datetime] = None
    password_changed_at: Optional[datetime] = None
    extra_attributes: Dict[str, str] = None

    @classmethod
    def create(cls, data: ResourceType) -> "User":
        return cls(
            id=data["localId"],
            email=data["email"],
            verified=data["emailVerified"],
            disabled=data["disabled"],
            created_at=parse_timestamp(timestamp=data["createdAt"]),
            last_login_at=parse_timestamp(timestamp=data.get("lastLoginAt")),
            password_changed_at=parse_timestamp(timestamp=data.get("passwordUpdatedAt")),
            extra_attributes=json.loads(data.get("customAttributes", "{}")),
        )


class IdentityPlatform(DiscoveryMixin, GoogleCloudPilotAPI):
    _scopes = ["https://www.googleapis.com/auth/identitytoolkit"]

    def __init__(self, **kwargs):
        super().__init__(
            serviceName="identitytoolkit",
            version="v1",
            cache_discovery=False,
            **kwargs,
        )

    def find(self, email: str = None, phone_number: str = None, project_id: str = None) -> User:
        try:
            return next(self.lookup(email=email, phone_number=phone_number, project_id=project_id))
        except StopIteration:
            raise exceptions.NotFound()

    def lookup(self, email: str = None, phone_number: str = None, project_id: str = None) -> Iterator[User]:
        if not email and not phone_number:
            raise exceptions.ValidationError("Either `email` or `phone_number` must be provided")

        data = {
            "target_project_id": project_id or self.project_id,
        }
        if email:
            data["email"] = email
        if phone_number:
            data["phone_number"] = phone_number

        response = self._execute(method=self.client.accounts().lookup, body=data)
        for item in response.get("users", []):
            yield User.create(data=item)

    def sign_in_with_password(self, email: str, password: str):
        data = {
            "email": email,
            "password": password,
        }
        response = self._execute(method=self.client.accounts().signInWithPassword, body=data)
        return response

    def sign_in_with_phone_number(self, phone_number: str, code: str):
        data = {
            "phone_number": phone_number,
            "code": code,
        }
        response = self._execute(method=self.client.accounts().signInWithPhoneNumber, body=data)
        return response

    def sign_in_with_email_link(self, email: str, code: str):
        data = {
            "email": email,
            "oobCode": code,
        }
        response = self._execute(method=self.client.accounts().signInWithEmailLink, body=data)
        return response

    def generate_email_code(
        self,
        type: OOBCodeType,
        email: str,
        ip_address: str = None,
        project_id: str = None,
        send_email: bool = False,
        redirect_url: str = None,
    ) -> ResourceType:
        data = {
            "requestType": type.value,
            "email": email,
            "user_ip": ip_address,
            "continue_url": redirect_url,
            "target_project_id": project_id or self.project_id,
            "returnOobLink": not send_email,
        }
        response = self._execute(method=self.client.accounts().sendOobCode, body=data)

        if send_email:
            return {}

        url = response["oobLink"]
        query = parse_qs(urlparse(url).query)
        return {"url": url, "code": query["oobCode"][0]}

    def reset_password(self, email: str, new_password: str, old_password: str = None, oob_code: str = None):
        data = {
            "newPassword": new_password,
            "email": email,
        }

        if oob_code:
            data["oobCode"] = oob_code
        elif old_password:
            data["oldPassword"] = old_password
        else:
            raise exceptions.ValidationError("Either `old_password` or `oob_code` must be provided")

        response = self._execute(method=self.client.accounts().resetPassword, body=data)
        return response

    def delete_user(self, user_id: str):
        data = {
            "localId": user_id,
        }
        response = self._execute(method=self.client.accounts().delete, body=data)
        return response

    def disable_user(self, user_id: str, project_id: str = None):
        data = {
            "localId": user_id,
            "disableUser": True,
            "targetProjectId": project_id or self.project_id,
        }
        response = self._execute(method=self.client.accounts().update, body=data)
        return response

    def enable_user(self, user_id: str, project_id: str = None):
        data = {
            "localId": user_id,
            "disableUser": False,
            "targetProjectId": project_id or self.project_id,
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
    ):
        data = {
            "email": email,
            "password": password,
            "displayName": name,
            "photoUrl": photo_url,
            "disabled": False,
            "localId": user_id,
            "phoneNumber": phone_number,
            "targetProjectId": project_id or self.project_id,
        }
        response = self._execute(method=self.client.accounts().signUp, body=data)
        return User.create(data=response)

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
    ):
        data = {
            "localId": user_id,
            "targetProjectId": project_id or self.project_id,
        }
        if email:
            data["email"] = email
        if password:
            data["password"] = password
        if phone_number:
            data["phoneNumber"] = phone_number
        if name:
            data["displayName"] = name
        if photo_url:
            data["photoUrl"] = photo_url
        if attributes:
            data["customAttributes"] = json.dumps(attributes)

        response = self._execute(method=self.client.accounts().update, body=data)
        return response
