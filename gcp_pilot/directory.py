# More Information: https://developers.google.com/admin-sdk/directory/reference/rest
from typing import Dict, Any, Generator

from gcp_pilot.base import GoogleCloudPilotAPI, DiscoveryMixin

UserType = GroupType = MemberType = Dict[str, Any]


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

    def _build_context(self, customer: str = None, domain: str = None) -> Dict[str, str]:
        context = {
            "customer": customer or "my_customer",
        }
        if domain:
            context["domain"] = domain
        return context

    def get_users(self, customer: str = None, domain: str = None) -> Generator[UserType, None, None]:
        params = self._build_context(customer=customer, domain=domain)
        yield from self._paginate(
            method=self.client.users().list,
            result_key="users",
            params=params,
            order_by="email",
        )

    def get_groups(self, customer: str = None, domain: str = None) -> Generator[GroupType, None, None]:
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
        name: str = None,
        description: str = None,
        group_id: str = None,
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
        else:
            return self._execute(
                method=self.client.groups().update,
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


__all__ = ("Directory",)
