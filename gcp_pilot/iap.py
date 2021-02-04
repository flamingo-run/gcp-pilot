from typing import Dict

from google.auth.transport.requests import Request
from google.oauth2 import service_account

from gcp_pilot.base import GoogleCloudPilotAPI


class IdentityAwareProxy(GoogleCloudPilotAPI):
    def __init__(self, audience):
        self.audience = audience
        super().__init__()

    def _build_client(self, **kwargs) -> None:
        return None

    def _get_id_credentials(self):
        credentials = service_account.IDTokenCredentials(
            signer=self.credentials.signer,
            service_account_email=self.credentials.service_account_email,
            token_uri="https://oauth2.googleapis.com/token",  # TODO: fetch from credentials
            target_audience=self.audience,
        )
        if not credentials.valid:
            credentials.refresh(request=Request())
        return credentials

    @property
    def token(self) -> str:
        credentials = self._get_id_credentials()
        return credentials.token

    @property
    def expires_at(self):
        credentials = self._get_id_credentials()
        return credentials.expiry

    @property
    def headers(self) -> Dict[str, str]:
        return {'Authorization': f'Bearer {self.token}'}


__all__ = (
    'IdentityAwareProxy',
)
