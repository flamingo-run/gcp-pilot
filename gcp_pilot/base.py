import abc
import logging
import os
from typing import Dict, Any, Callable

from google import auth
from googleapiclient.discovery import build

DEFAULT_PROJECT_ID = os.environ.get('PROJECT_ID')
DEFAULT_LOCATION = os.environ.get('LOCATION', None)

PolicyType = Dict[str, Any]

logger = logging.getLogger()


def _get_project_default_location(credentials, project_id, default_zone='1'):
    service = build(serviceName='appengine', version='v1', credentials=credentials, cache_discovery=False)
    data = service.apps().get(appsId=project_id).execute()
    return data['locationId'] + default_zone


MINIMAL_SCOPES = [
    'https://www.googleapis.com/auth/cloud-platform',
]


class GoogleCloudPilotAPI(abc.ABC):
    _client_class = None
    _scopes = []
    _iam_roles = []
    _cached_credentials = None

    def __init__(self, subject=None, location=None, **kwargs):
        self.credentials, project_id = self._set_credentials(subject=subject)
        self.project_id = self._set_project_id(project_id=project_id)
        self.location = self._set_location(location=location)

        self.client = (self._client_class or build)(
            credentials=self.credentials,
            **kwargs
        )

    def _set_project_id(self, project_id: str = None):
        return DEFAULT_PROJECT_ID or getattr(self.credentials, 'project_id', project_id)

    def _set_location(self, location: str = None):
        return location or DEFAULT_LOCATION or _get_project_default_location(
            credentials=self.credentials,
            project_id=self.project_id,
        )

    @classmethod
    def _set_credentials(cls, subject=None):
        # Speed up consecutive authentications
        if not cls._cached_credentials:
            all_scopes = MINIMAL_SCOPES + cls._scopes
            credentials, project_id = auth.default(scopes=all_scopes)
            cls._cached_credentials = credentials, project_id

        credentials, project_id = cls._cached_credentials
        if subject:
            credentials = credentials.with_subject(subject=subject)
        return credentials, project_id

    @property
    def oidc_token(self):
        return {'oidc_token': {'service_account_email': self.credentials.service_account_email}}

    async def add_permissions(self, email, project_id=None):
        from gcp_pilot.resource import GoogleResourceManager  # pylint: disable=import-outside-toplevel

        for role in self._iam_roles:
            await GoogleResourceManager().add_member(
                email=email,
                role=role,
                project_id=project_id or self.project_id,
            )

    def _get_project_number(self, project_id):
        from gcp_pilot.resource import GoogleResourceManager  # pylint: disable=import-outside-toplevel

        project = GoogleResourceManager().get_project(project_id=project_id)
        return project.projectNumber

    def _paginate(self, method: Callable, result_key: str, params: Dict[str, Any] = None):
        page_token = None
        params = params or {}

        while True:
            results = method(
                **params,
                pageToken=page_token,
            ).execute()
            for space in results.get(result_key, []):
                yield space

            page_token = results.get('nextPageToken')
            if not page_token:
                break


class AccountManagerMixin:
    def as_member(self, email: str) -> str:
        is_service_account = email.endswith('.gserviceaccount.com')
        prefix = 'serviceAccount' if is_service_account else 'member'
        return f'{prefix}:{email}'

    def bind_email_to_policy(self, email: str, role: str, policy: Dict) -> Dict:
        role_id = role if (role.startswith('organizations/') or role.startswith('roles/')) else f'roles/{role}'
        member = self.as_member(email=email)

        try:
            binding = next(b for b in policy['bindings'] if b['role'] == role_id)
            if member in binding['members']:
                return policy
            binding['members'].append(member)
        except (StopIteration, KeyError):
            binding = {'role': role_id, 'members': [member]}
            policy['bindings'] = policy.get('bindings', []).append(binding)
        return policy

    def unbind_email_from_policy(self, email: str, role: str, policy: Dict):
        role_id = f'roles/{role}'
        member = self.as_member(email=email)

        try:
            binding = next(b for b in policy['bindings'] if b['role'] == role_id)
            if member not in binding['members']:
                return policy
            binding['members'].remove(member)
        except (StopIteration, KeyError):
            pass
        return policy


class AppEngineBasedService:
    def _set_location(self, location: str = None):
        project_location = _get_project_default_location(credentials=self.credentials, project_id=self.project_id)

        explicit_location = location
        if explicit_location and explicit_location != project_location:
            logger.warning(
                f"Location {explicit_location} cannot be set in {self.__class__.__name__}. "
                f"It uses App Engine's default location for your project: {project_location}"
            )
        return project_location
