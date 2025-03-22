# Reference: https://developers.google.com/drive/api/reference/rest/v3

from gcp_pilot.base import GoogleCloudPilotAPI


class BaseDrive(GoogleCloudPilotAPI):
    _scopes = ["https://www.googleapis.com/auth/drive"]

    def __init__(self, **kwargs):
        super().__init__(
            serviceName="drive",
            version="v3",
            **kwargs
        )

__all__ = ()
