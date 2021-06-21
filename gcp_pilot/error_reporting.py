# More Information: <https://googleapis.dev/python/clouderrorreporting/latest/usage.html>
from google.cloud import error_reporting
from google.cloud.error_reporting import HTTPContext

from gcp_pilot.base import GoogleCloudPilotAPI, DiscoveryMixin


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


class CloudErrorExplorer(DiscoveryMixin, GoogleCloudPilotAPI):
    def __init__(self):
        super().__init__(
            serviceName="clouderrorreporting",
            version="v1beta1",
            cache_discovery=False,
        )

    def get_events(
        self,
        error_id: str = None,
        service_name: str = None,
        service_version: str = None,
        resource_type: str = None,
        project_id: str = None,
    ):
        params = dict(
            projectName=self._project_path(project_id=project_id),
            groupId=error_id,
        )
        if service_name:
            params["serviceFilter_service"] = service_name
        if service_version:
            params["serviceFilter_version"] = service_version
        if resource_type:
            params["serviceFilter_resourceType"] = resource_type

        yield from self._paginate(
            method=self.client.projects().events().list,
            params=params,
            result_key="errorEvents",
        )

    def get_errors(
        self,
        service_name: str = None,
        service_version: str = None,
        resource_type: str = None,
        project_id: str = None,
    ):
        params = dict(
            projectName=self._project_path(project_id=project_id),
        )
        if service_name:
            params["serviceFilter_service"] = service_name
        if service_version:
            params["serviceFilter_version"] = service_version
        if resource_type:
            params["serviceFilter_resourceType"] = resource_type

        items = self._paginate(
            method=self.client.projects().groupStats().list,
            params=params,
            result_key="errorGroupStats",
        )
        for item in items:
            yield {"id": item["group"]["groupId"], **item}


__all__ = (
    "CloudErrorReporting",
    "CloudErrorExplorer",
)
