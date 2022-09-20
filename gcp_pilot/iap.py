import requests
from google.auth.transport.requests import Request
from google.oauth2 import service_account

from gcp_pilot.base import GoogleCloudPilotAPI


class IdentityAwareProxy(GoogleCloudPilotAPI):
    def __init__(self, audience: str):
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

    def _get_gcp_token(self):
        email = self.credentials.service_account_email
        metadata_server_token_url = f"http://metadata/computeMetadata/v1/instance/service-accounts/{email}/identity"

        token_request_url = f"{metadata_server_token_url}?audience={self.audience}"
        token_request_headers = {"Metadata-Flavor": "Google"}

        token_response = requests.get(url=token_request_url, headers=token_request_headers, timeout=15)
        return token_response.content.decode("utf-8")

    @property
    def token(self) -> str:
        try:
            return self._get_gcp_token()
        except requests.exceptions.ConnectionError:
            credentials = self._get_id_credentials()
            return credentials.token

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}


__all__ = ("IdentityAwareProxy",)
