# More Information: https://developers.google.com/admin-sdk/directory/reference/rest
from collections.abc import Generator
from typing import Any

from gcp_pilot.base import DiscoveryMixin, GoogleCloudPilotAPI

UserType = GroupType = MemberType = dict[str, Any]
USER_FIELDS = [
    "addresses",
    "addresses",
    "ageRanges",
    "biographies",
    "birthdays",
    "calendarUrls",
    "clientData",
    "coverPhotos",
    "emailAddresses",
    "events",
    "externalIds",
    "genders",
    "imClients",
    "interests",
    "locales",
    "locations",
    "memberships",
    "metadata",
    "miscKeywords",
    "names",
    "nicknames",
    "occupations",
    "organizations",
    "phoneNumbers",
    "photos",
    "relations",
    "sipAddresses",
    "skills",
    "urls",
    "userDefined",
]


class People(DiscoveryMixin, GoogleCloudPilotAPI):
    _scopes = [
        "https://www.googleapis.com/auth/contacts",
        "https://www.googleapis.com/auth/directory.readonly",
    ]

    def __init__(self, email: str, **kwargs):
        self.email = email
        super().__init__(
            serviceName="people",
            version="v1",
            cache_discovery=False,
            subject=email,
            **kwargs,
        )

    def _get_project_default_location(self, project_id: str | None = None) -> str | None:
        return None

    def get_people(self, query: str | None = None, fields: list[str] | None = None) -> Generator[UserType, None, None]:
        params = {
            "readMask": ",".join(fields or USER_FIELDS),
            "sources": ["DIRECTORY_SOURCE_TYPE_DOMAIN_PROFILE", "DIRECTORY_SOURCE_TYPE_DOMAIN_CONTACT"],
        }
        if query:
            params["query"] = query
            yield from self._list(
                method=self.client.people().searchDirectoryPeople,
                result_key="people",
                params=params,
            )
        else:
            yield from self._paginate(
                method=self.client.people().listDirectoryPeople,
                result_key="people",
                params=params,
            )


__all__ = ("People",)
