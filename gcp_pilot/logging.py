# More Information: <https://cloud.google.com/logging/docs/reference/libraries#client-libraries-install-python>
from logging import INFO

from google.cloud import logging

from gcp_pilot.base import GoogleCloudPilotAPI


class CloudLogging(GoogleCloudPilotAPI):
    _client_class = logging.Client

    def _get_client_extra_kwargs(self):
        return {"project": self.project_id}

    def enable(self, log_level=INFO):
        self.client.setup_logging(log_level=log_level)

    @property
    def handler(self):
        return self.client.get_default_handler()


__all__ = ("CloudLogging",)
