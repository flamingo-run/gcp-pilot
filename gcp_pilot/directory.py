# More Information: https://developers.google.com/admin-sdk/directory/reference/rest
from collections.abc import Generator
from typing import Any

from gcp_pilot.base import DiscoveryMixin, GoogleCloudPilotAPI

UserType = GroupType = MemberType = dict[str, Any]


class Directory(DiscoveryMixin, GoogleCloudPilotAPI):
    _scopes = [
        "https://www.googleapis.com/auth/admin.directory.group",
        "https://www.googleapis.com/auth/admin.directory.user",
    ]

    def __init__(self, email: str, **kwargs):
        self.email = email
        super().__init__(
            serviceName="admin",
            version="directory_v1",
            cache_discovery=False,
            subject=email,
            **kwargs,
        )

    def _get_project_default_location(self, project_id: str | None = None) -> str | None:
        return "us"

    def _build_context(self, customer: str | None = None, domain: str | None = None) -> dict[str, str]:
        context = {
            "customer": customer or "my_customer",
        }
        if domain:
            context["domain"] = domain
        return context

    def get_groups(self, customer: str | None = None, domain: str | None = None) -> Generator[GroupType, None, None]:
        params = self._build_context(customer=customer, domain=domain)
        yield from self._paginate(
            method=self.client.groups().list,
            result_key="groups",
            params=params,
        )

    def get_group(self, group_id: str) -> GroupType:
        return self._execute(
            method=self.client.groups().get,
            groupKey=group_id,
        )

    def create_or_update_group(
        self,
        email: str,
        name: str | None = None,
        description: str | None = None,
        group_id: str | None = None,
    ) -> GroupType:
        body = dict(
            email=email,
            name=name,
            description=description,
        )

        if not group_id:
            return self._execute(
                method=self.client.groups().insert,
                body=body,
            )

        return self._execute(
            method=self.client.groups().patch,
            groupKey=group_id,
            body=body,
        )

    def delete_group(self, group_id: str) -> GroupType:
        return self._execute(
            method=self.client.groups().delete,
            groupKey=group_id,
        )

    def get_group_members(self, group_id: str) -> Generator[MemberType, None, None]:
        params = dict(
            groupKey=group_id,
        )

        yield from self._paginate(
            method=self.client.members().list,
            result_key="members",
            params=params,
        )

    def add_group_member(self, group_id: str, email: str, role: str = "MEMBER") -> MemberType:
        body = {"email": email, "role": role}

        return self._execute(
            method=self.client.members().insert,
            groupKey=group_id,
            body=body,
        )

    def delete_group_member(self, group_id: str, member_id: str) -> MemberType:
        return self._execute(
            method=self.client.members().delete,
            groupKey=group_id,
            memberKey=member_id,
        )

    def get_users(self, customer: str | None = None, domain: str | None = None) -> Generator[UserType, None, None]:
        params = self._build_context(customer=customer, domain=domain)
        yield from self._paginate(
            method=self.client.users().list,
            result_key="users",
            params=params,
            order_by="email",
        )

    def add_user(self, email: str, first_name: str, last_name: str, password: str) -> UserType:
        body = {
            "name": {
                "familyName": last_name,
                "givenName": first_name,
            },
            "password": password,
            "primaryEmail": email,
        }
        # TODO: add support to much more fields from
        # https://developers.google.com/admin-sdk/directory/reference/rest/v1/users#User

        return self._execute(
            method=self.client.users().insert,
            body=body,
        )

    def update_user(
        self,
        user_id: str,
        email: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        password: str | None = None,
        suspended: bool | None = None,
    ) -> UserType:
        body = {}
        if email:
            body["primaryEmail"] = email
        if first_name:
            body["name"]["givenName"] = first_name
        if last_name:
            body["name"]["familyName"] = last_name
        if password:
            body["password"] = password
        if suspended is not None:
            body["suspended"] = suspended

        return self._execute(
            method=self.client.users().patch,
            userKey=user_id,
            body=body,
        )

    def get_user(self, user_id: str) -> UserType:
        return self._execute(
            method=self.client.users().get,
            userKey=user_id,
        )

    def delete_user(self, user_id: str) -> UserType:
        body = {}

        return self._execute(
            method=self.client.users().delete,
            userKey=user_id,
            body=body,
        )

    def undelete_user(self, user_id: str) -> UserType:
        body = {}

        return self._execute(
            method=self.client.users().undelete,
            userKey=user_id,
            body=body,
        )

    def suspend_user(self, user_id: str) -> UserType:
        return self.update_user(user_id=user_id, suspended=True)

    def reestablish_user(self, user_id: str) -> UserType:
        return self.update_user(user_id=user_id, suspended=False)

    def make_admin(self, user_id: str) -> UserType:
        body = {"status": True}
        return self._execute(
            method=self.client.users().makeAdmin,
            userKey=user_id,
            body=body,
        )

    def unmake_admin(self, user_id: str) -> UserType:
        body = {"status": False}
        return self._execute(
            method=self.client.users().makeAdmin,
            userKey=user_id,
            body=body,
        )


__all__ = ("Directory",)
