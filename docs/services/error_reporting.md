# Error Reporting

Error Reporting is a service that aggregates and displays errors produced in your running cloud services. The `CloudErrorReporting` and `CloudErrorExplorer` classes in gcp-pilot provide high-level interfaces for interacting with Google Cloud Error Reporting.

## Installation

To use the Error Reporting functionality, you need to install gcp-pilot:

```bash
pip install gcp-pilot
```

## Usage

### CloudErrorReporting

The `CloudErrorReporting` class allows you to report errors to Google Cloud Error Reporting.

#### Initialization

```python
from gcp_pilot.error_reporting import CloudErrorReporting

# Initialize with a service name
error_reporting = CloudErrorReporting(service_name="my-service")

# Initialize with service account impersonation
error_reporting = CloudErrorReporting(
    service_name="my-service",
    impersonate_account="service-account@project-id.iam.gserviceaccount.com"
)
```

The `service_name` parameter is required and identifies the service that is reporting the error.

#### Reporting Errors

```python
# Report a simple error message
error_reporting.report(message="An error occurred")

# Report an error with user information
error_reporting.report(
    message="An error occurred for a specific user",
    user="user@example.com"
)

# Report an error with HTTP context
from google.cloud.error_reporting import HTTPContext

http_context = HTTPContext(
    url="https://example.com/path",
    method="GET",
    user_agent="Mozilla/5.0",
    referrer="https://example.com",
    response_status_code=500
)

error_reporting.report(
    message="An HTTP error occurred",
    http_context=http_context
)
```

#### Reporting Errors with WSGI Requests

If you're using a WSGI-compatible web framework like Django or Flask, you can report errors with the request context:

```python
# Report an exception with a WSGI request
try:
    # Some code that might raise an exception
    raise ValueError("Something went wrong")
except Exception:
    error_reporting.report_with_request(
        request=request,  # A WSGI request object
        status_code=500
    )

# Report a specific message with a WSGI request
error_reporting.report_with_request(
    request=request,  # A WSGI request object
    status_code=400,
    message="Invalid request parameters"
)
```

### CloudErrorExplorer

The `CloudErrorExplorer` class allows you to explore errors that have been reported to Google Cloud Error Reporting.

#### Initialization

```python
from gcp_pilot.error_reporting import CloudErrorExplorer

# Initialize with default credentials
error_explorer = CloudErrorExplorer()

# Initialize with specific project
error_explorer = CloudErrorExplorer(project_id="my-project")

# Initialize with service account impersonation
error_explorer = CloudErrorExplorer(
    impersonate_account="service-account@project-id.iam.gserviceaccount.com"
)
```

#### Getting Error Events

```python
# Get all error events
events = error_explorer.get_events()
for event in events:
    print(f"Error: {event['message']}")
    print(f"Time: {event['eventTime']}")
    print(f"Service: {event['serviceContext']['service']}")

# Get error events for a specific error group
events = error_explorer.get_events(error_id="error-group-id")
for event in events:
    print(f"Error: {event['message']}")

# Get error events for a specific service
events = error_explorer.get_events(service_name="my-service")
for event in events:
    print(f"Error: {event['message']}")

# Get error events with multiple filters
events = error_explorer.get_events(
    service_name="my-service",
    service_version="v1.0",
    resource_type="gae_app",
    project_id="my-project"  # Optional: defaults to the project associated with credentials
)
for event in events:
    print(f"Error: {event['message']}")
```

#### Getting Error Groups

```python
# Get all error groups
errors = error_explorer.get_errors()
for error in errors:
    print(f"Error Group ID: {error['id']}")
    print(f"Count: {error['count']}")
    print(f"First Seen: {error['firstSeenTime']}")
    print(f"Last Seen: {error['lastSeenTime']}")

# Get error groups for a specific service
errors = error_explorer.get_errors(service_name="my-service")
for error in errors:
    print(f"Error Group ID: {error['id']}")

# Get error groups with multiple filters
errors = error_explorer.get_errors(
    service_name="my-service",
    service_version="v1.0",
    resource_type="gae_app",
    project_id="my-project"  # Optional: defaults to the project associated with credentials
)
for error in errors:
    print(f"Error Group ID: {error['id']}")
```

## Error Handling

The Error Reporting classes handle common errors and convert them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    error_explorer.get_events(error_id="non-existent-id")
except exceptions.NotFound:
    print("Error group not found")
```

## Integration with Web Frameworks

### Django Integration

Here's an example of how to integrate Error Reporting with Django:

```python
# In your Django middleware
from gcp_pilot.error_reporting import CloudErrorReporting

class ErrorReportingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.error_reporting = CloudErrorReporting(service_name="my-django-app")

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        except Exception as e:
            self.error_reporting.report_with_request(
                request=request,
                status_code=500
            )
            raise
```

### Flask Integration

Here's an example of how to integrate Error Reporting with Flask:

```python
# In your Flask app
from flask import Flask, request
from gcp_pilot.error_reporting import CloudErrorReporting

app = Flask(__name__)
error_reporting = CloudErrorReporting(service_name="my-flask-app")

@app.errorhandler(Exception)
def handle_exception(e):
    error_reporting.report_with_request(
        request=request,
        status_code=500
    )
    return "An error occurred", 500
```