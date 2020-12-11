import abc
import os
from typing import Dict, Any

from google import auth
from googleapiclient.discovery import build

DEFAULT_PROJECT_ID = os.environ.get('PROJECT_ID')
DEFAULT_LOCATION = os.environ.get('LOCATION', 'us-east1')

PolicyType = Dict[str, Any]


class GoogleCloudPilotAPI(abc.ABC):
    _client_class = None
    _scopes = ['https://www.googleapis.com/auth/cloud-platform']
    _iam_roles = []

    def __init__(self, subject=None, location=None, **kwargs):
        self.credentials, project_id = self._build_credentials(subject=subject)
        self.project_id = kwargs.get('project') \
            or DEFAULT_PROJECT_ID \
            or getattr(self.credentials, 'project_id', project_id)

        self.location = location or DEFAULT_LOCATION

        self.client = (self._client_class or build)(
            credentials=self.credentials,
            **kwargs
        )

    @classmethod
    def _build_credentials(cls, subject=None):
        credentials, project_id = auth.default()
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
