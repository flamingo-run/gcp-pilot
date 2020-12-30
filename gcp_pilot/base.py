import abc
import logging
import os
from typing import Dict, Any, Callable, Tuple

from google import auth
from google.auth.credentials import Credentials
from google.auth.impersonated_credentials import Credentials as ImpersonatedCredentials
from google.protobuf.duration_pb2 import Duration
from googleapiclient.discovery import build

DEFAULT_LOCATION = os.environ.get('GOOGLE_CLOUD_LOCATION', None)

PolicyType = Dict[str, Any]
AuthType = Tuple[Credentials, str]
ImpersonatedAuthType = Tuple[ImpersonatedCredentials, str]

logger = logging.getLogger()


def _get_project_default_location(credentials, project_id: str, default_zone: str = '1') -> str:
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

    def __init__(
            self,
            subject: str = None,
            location: str = None,
            project_id: str = None,
            impersonate_account: str = None,
            **kwargs,
    ):
        self.credentials, credential_project_id = self._set_credentials(
            subject=subject,
            impersonate_account=impersonate_account,
        )
        self.project_id = self._set_project_id(project_id=project_id, credential_project_id=credential_project_id)
        self.location = self._set_location(location=location)

        self.client = (self._client_class or build)(
            credentials=self.credentials,
            **kwargs
        )

    def _set_project_id(self, project_id: str, credential_project_id: str) -> str:
        return project_id or credential_project_id

    def _set_location(self, location: str = None) -> str:
        return location or DEFAULT_LOCATION or _get_project_default_location(
            credentials=self.credentials,
            project_id=self.project_id,
        )

    @classmethod
    def _impersonate_account(cls, credentials, service_account, scopes) -> ImpersonatedAuthType:
        credentials = ImpersonatedCredentials(
            source_credentials=credentials,
            target_principal=service_account,
            target_scopes=scopes,
            delegates=[],
        )

        # Fetch project from service account
        # Since we are impersonating this service account, use it's own project
        # TODO: regex this
        project_id = credentials.service_account_email.split('@')[-1].replace('.iam.gserviceaccount.com', '')

        return credentials, project_id

    @classmethod
    def _set_credentials(cls, subject: str = None, impersonate_account: str = None) -> AuthType:
        # Speed up consecutive authentications
        # TODO: check if this does not break multiple client usage
        if not cls._cached_credentials:
            all_scopes = MINIMAL_SCOPES + cls._scopes
            credentials, project_id = auth.default(scopes=all_scopes)

            if impersonate_account:
                credentials, impersonated_project_id = cls._impersonate_account(
                    credentials=credentials,
                    service_account=impersonate_account,
                    scopes=all_scopes,
                )
                project_id = impersonated_project_id or project_id

            cls._cached_credentials = credentials, project_id

        credentials, project_id = cls._cached_credentials
        if subject:
            credentials = credentials.with_subject(subject=subject)
        return credentials, (project_id or getattr(credentials, 'project_id'))

    @property
    def oidc_token(self) -> Dict[str, Dict[str, str]]:
        return {'oidc_token': {'service_account_email': self.credentials.service_account_email}}

    async def add_permissions(self, email: str, project_id: str = None) -> None:
        from gcp_pilot.resource import GoogleResourceManager  # pylint: disable=import-outside-toplevel

        for role in self._iam_roles:
            await GoogleResourceManager().add_member(
                email=email,
                role=role,
                project_id=project_id or self.project_id,
            )

    def _get_project_number(self, project_id: str) -> int:
        from gcp_pilot.resource import GoogleResourceManager  # pylint: disable=import-outside-toplevel

        project = GoogleResourceManager().get_project(project_id=project_id)
        return project.projectNumber

    def _paginate(self, method: Callable, result_key: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        page_token = None
        params = params or {}

        while True:
            results = method(
                **params,
                pageToken=page_token,
            ).execute()
            for item in results.get(result_key, []):
                yield item

            page_token = results.get('nextPageToken')
            if not page_token:
                break

    def _as_duration(self, seconds):
        return Duration(seconds=seconds)


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
    # This mixin must be used for all clients that uses GCP's resources that are based on App Engine
    # such as Cloud Scheduler.
    # They have a peculiar behaviour because the App Engine, when enabled the first time,
    # is created in a region and this region cannot be changed ever.
    # So these clients cannot just choose a desired region to work on, they must use the App Engine's
    # previously chosen region.
    def _set_location(self, location: str = None):
        project_location = _get_project_default_location(credentials=self.credentials, project_id=self.project_id)

        explicit_location = location
        if explicit_location and explicit_location != project_location:
            logger.warning(
                f"Location {explicit_location} cannot be set in {self.__class__.__name__}. "
                f"It uses App Engine's default location for your project: {project_location}"
            )
        return project_location
