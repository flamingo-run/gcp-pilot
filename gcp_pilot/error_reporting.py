# More Information: <https://googleapis.dev/python/clouderrorreporting/latest/usage.html>
from google.cloud import error_reporting
from google.cloud.error_reporting import HTTPContext

from gcp_pilot.base import GoogleCloudPilotAPI


class CloudErrorReporting(GoogleCloudPilotAPI):
    _client_class = error_reporting.Client

    def __init__(self, service_name):
        super().__init__(service=service_name)

    def report(self, message, http_context=None, user=None) -> None:
        self.client.report(message=message, http_context=http_context, user=user)

    def report_with_request(self, request: "WSGIRequest", status_code: int, message: str = None) -> None:
        user = str(request.user) if request.user.is_authenticated else None
        http_context = self._wsgi_to_http_context(request=request, status_code=status_code)

        if not message:
            self.client.report_exception(
                http_context=http_context,
                user=user,
            )
        else:
            self.report(
                message=message,
                http_context=http_context,
                user=user,
            )

    def _wsgi_to_http_context(self, request: "WSGIRequest", status_code: int) -> HTTPContext:
        return HTTPContext(
            url=request.get_raw_uri(),
            method=request.method,
            user_agent=request.headers.get("User-Agent"),
            referrer=request.headers.get("Referer"),
            response_status_code=status_code,
        )


__all__ = (
    'CloudErrorReporting',
)
