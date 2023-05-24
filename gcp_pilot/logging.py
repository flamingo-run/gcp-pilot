# More Information: <https://cloud.google.com/logging/docs/reference/libraries#client-libraries-install-python>
from datetime import UTC, datetime
from logging import INFO

from google.cloud import logging
from google.cloud.logging_v2 import Resource
from google.logging.type.http_request_pb2 import HttpRequest
from google.logging.type.log_severity_pb2 import LogSeverity

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

    def log_struct(
        self,
        logger_name: str,
        message: str | dict,
        severity: LogSeverity,
        timestamp: datetime | None = None,
        http_request: HttpRequest | None = None,
        labels: dict | None = None,
        span_id: str | None = None,
        trace: str | None = None,
        resource: Resource | None = None,
    ):
        logger = self.client.logger(name=logger_name)
        logger.log_struct(
            message,
            timestamp=timestamp or datetime.now(tz=UTC),
            labels=labels,
            resource=resource,
            severity=severity,
            trace=trace,
            span_id=span_id,
            http_request=http_request,
        )


__all__ = ("CloudLogging",)
