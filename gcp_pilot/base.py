import abc
import json
import logging
import os
from typing import Dict, Any, Callable, Tuple, List, Generator

from google import auth
from google.auth import iam
from google.auth.credentials import Credentials
from google.auth.impersonated_credentials import Credentials as ImpersonatedCredentials
from google.auth.transport import requests
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.protobuf.duration_pb2 import Duration
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from gcp_pilot import exceptions

DEFAULT_PROJECT = os.environ.get('GOOGLE_CLOUD_PROJECT', None)
DEFAULT_LOCATION = os.environ.get('GOOGLE_CLOUD_LOCATION', None)
TOKEN_URI = 'https://accounts.google.com/o/oauth2/token'

PolicyType = Dict[str, Any]
AuthType = Tuple[Credentials, str]
ImpersonatedAuthType = Tuple[ImpersonatedCredentials, str]
ResourceType = Dict[str, Any]

logger = logging.getLogger()

_CACHED_LOCATIONS = {}  # TODO: Implement a smarter solution for caching project's location


def _get_project_default_location(credentials, project_id: str, default_zone: str = '1') -> str:
    location = _CACHED_LOCATIONS.get(project_id, None)

    if not location:
        service = build(serviceName='appengine', version='v1', credentials=credentials, cache_discovery=False)
        data = service.apps().get(appsId=project_id).execute()
        location = data['locationId'] + default_zone
        _CACHED_LOCATIONS[project_id] = location
    return location


MINIMAL_SCOPES = [
    'https://www.googleapis.com/auth/cloud-platform',
]


class GoogleCloudPilotAPI(abc.ABC):
    _client_class = None
    _scopes: List[str] = []
    _iam_roles: List[str] = []
    _cached_credentials: AuthType = None

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
        return project_id or DEFAULT_PROJECT or credential_project_id

    def _set_location(self, location: str = None) -> str:
        return location or DEFAULT_LOCATION or _get_project_default_location(
            credentials=self.credentials,
            project_id=self.project_id,
        )

    @classmethod
    def _impersonate_account(
            cls,
            credentials: Credentials,
            service_account: str,
            scopes: List[str],
    ) -> ImpersonatedAuthType:
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
    def _delegated_credential(
            cls,
            credentials: Credentials,
            subject: str,
            scopes: List[str],
    ) -> ServiceAccountCredentials:
        try:
            admin_credentials = credentials.with_subject(subject).with_scopes(scopes)
        except AttributeError:
            # When inside GCP, the credentials provided by the metadata service are immutable.
            # https://github.com/GoogleCloudPlatform/professional-services/tree/master/examples/gce-to-adminsdk

            request = requests.Request()
            credentials.refresh(request)

            # Create an IAM signer using the bootstrap credentials.
            signer = iam.Signer(
                request,
                credentials,
                credentials.service_account_email,
            )
            # Create OAuth 2.0 Service Account credentials using the IAM-based
            # signer and the bootstrap_credential's service account email.
            admin_credentials = ServiceAccountCredentials(
                signer,
                credentials.service_account_email,
                TOKEN_URI,
                scopes=scopes,
                subject=subject,
            )

        return admin_credentials

    @classmethod
    def _set_credentials(cls, subject: str = None, impersonate_account: str = None) -> AuthType:
        # Speed up consecutive authentications
        # TODO: check if this does not break multiple client usage
        all_scopes = MINIMAL_SCOPES + cls._scopes
        if not cls._cached_credentials:
            credentials, project_id = auth.default(scopes=all_scopes)
            cls._cached_credentials = credentials, project_id
        else:
            credentials, project_id = cls._cached_credentials

        if impersonate_account:
            credentials, impersonated_project_id = cls._impersonate_account(
                credentials=credentials,
                service_account=impersonate_account,
                scopes=all_scopes,
            )
            project_id = impersonated_project_id or project_id

        if subject:
            credentials = cls._delegated_credential(credentials=credentials, subject=subject, scopes=all_scopes)

        return credentials, (project_id or getattr(credentials, 'project_id'))

    @property
    def oidc_token(self) -> Dict[str, Dict[str, str]]:
        return {'oidc_token': {'service_account_email': self.credentials.service_account_email}}

    async def add_permissions(self, email: str, project_id: str = None) -> None:
        from gcp_pilot.resource import ResourceManager  # pylint: disable=import-outside-toplevel

        for role in self._iam_roles:
            await ResourceManager().add_member(
                email=email,
                role=role,
                project_id=project_id or self.project_id,
            )

    def _get_project_number(self, project_id: str) -> int:
        from gcp_pilot.resource import ResourceManager  # pylint: disable=import-outside-toplevel

        project = ResourceManager().get_project(project_id=project_id)
        return project.projectNumber

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


def friendly_http_error(func):
    _reasons = {
        'notFound': exceptions.NotFound,
        'deleted': exceptions.AlreadyDeleted,
        'forbidden': exceptions.NotAllowed,
    }

    def inner_function(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HttpError as exc:
            error = json.loads(exc.content)['error']['errors'][0]

            exception_klass = _reasons.get(error['reason'], None)
            if exception_klass:
                raise exception_klass() from exc  # TODO: add more details to the exceptions
            raise exc

    return inner_function


class DiscoveryMixin:
    @friendly_http_error
    def _execute(self, method: Callable, **kwargs) -> ResourceType:
        return method(**kwargs).execute()

    def _paginate(
            self,
            method: Callable,
            result_key: str = 'items',
            params: Dict[str, Any] = None,
            order_by: str = None,
            limit: int = 200,
    ) -> Generator[ResourceType, None, None]:
        page_token = None
        params = params or {}

        if order_by:
            if order_by.startswith('-'):
                params['sortOrder'] = 'DESCENDING'
                order_by = order_by[1:]
            params['orderBy'] = order_by

        if limit:
            params['maxResults'] = limit

        while True:
            results = self._execute(
                method=method,
                **params,
                pageToken=page_token,
            )
            for item in results.get(result_key, []):
                yield item

            page_token = results.get('nextPageToken')
            if not page_token:
                break
