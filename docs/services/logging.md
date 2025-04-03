# Cloud Logging

Cloud Logging is a fully managed service that allows you to store, search, analyze, monitor, and alert on log data and events from Google Cloud and Amazon Web Services. The `CloudLogging` class in gcp-pilot provides a high-level interface for interacting with Google Cloud Logging.

## Installation

To use the Cloud Logging functionality, you need to install gcp-pilot:

```bash
pip install gcp-pilot
```

## Usage

### Initialization

```python
from gcp_pilot.logging import CloudLogging

# Initialize with default credentials
logging = CloudLogging()

# Initialize with specific project
logging = CloudLogging(project_id="my-project")

# Initialize with service account impersonation
logging = CloudLogging(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

### Enabling Logging

You can enable Cloud Logging to capture logs from your application:

```python
import logging as python_logging

# Enable Cloud Logging with the default log level (INFO)
cloud_logging = CloudLogging()
cloud_logging.enable()

# Enable Cloud Logging with a specific log level
cloud_logging.enable(log_level=python_logging.DEBUG)

# Now you can use the standard Python logging module, and logs will be sent to Cloud Logging
python_logging.info("This is an info message")
python_logging.error("This is an error message")
```

### Getting the Default Handler

You can get the default handler to add it to your own logger:

```python
import logging as python_logging

# Initialize Cloud Logging
cloud_logging = CloudLogging()

# Get the default handler
handler = cloud_logging.handler

# Create a custom logger
logger = python_logging.getLogger("my-logger")
logger.setLevel(python_logging.INFO)
logger.addHandler(handler)

# Use the custom logger
logger.info("This is an info message")
logger.error("This is an error message")
```

### Logging Structured Data

You can log structured data with additional metadata:

```python
from datetime import datetime, UTC
from google.logging.type.log_severity_pb2 import LogSeverity
from google.logging.type.http_request_pb2 import HttpRequest
from google.cloud.logging_v2 import Resource

# Initialize Cloud Logging
cloud_logging = CloudLogging()

# Log a simple message
cloud_logging.log_struct(
    logger_name="my-logger",
    message="This is a simple message",
    severity=LogSeverity.INFO,
)

# Log a structured message
cloud_logging.log_struct(
    logger_name="my-logger",
    message={
        "message": "This is a structured message",
        "user_id": "123",
        "action": "login",
        "status": "success",
    },
    severity=LogSeverity.INFO,
)

# Log with additional metadata
cloud_logging.log_struct(
    logger_name="my-logger",
    message="This is a message with metadata",
    severity=LogSeverity.ERROR,
    timestamp=datetime.now(tz=UTC),
    labels={"environment": "production", "version": "1.0.0"},
    span_id="span-123",
    trace="projects/my-project/traces/trace-123",
)

# Log an HTTP request
http_request = HttpRequest(
    request_method="GET",
    request_url="https://example.com/api",
    status=200,
    user_agent="Mozilla/5.0",
    remote_ip="192.0.2.1",
)

cloud_logging.log_struct(
    logger_name="my-logger",
    message="HTTP request processed",
    severity=LogSeverity.INFO,
    http_request=http_request,
)

# Log with a specific resource
resource = Resource(
    type="gce_instance",
    labels={
        "instance_id": "instance-123",
        "zone": "us-central1-a",
    },
)

cloud_logging.log_struct(
    logger_name="my-logger",
    message="Instance event",
    severity=LogSeverity.INFO,
    resource=resource,
)
```

## Log Severity Levels

The `LogSeverity` enum from `google.logging.type.log_severity_pb2` provides the following severity levels:

```python
from google.logging.type.log_severity_pb2 import LogSeverity

# Available severity levels
LogSeverity.DEFAULT  # (0) The log entry has no assigned severity level.
LogSeverity.DEBUG    # (100) Debug or trace information.
LogSeverity.INFO     # (200) Routine information, such as ongoing status or performance.
LogSeverity.NOTICE   # (300) Normal but significant events, such as start up, shut down, or a configuration change.
LogSeverity.WARNING  # (400) Warning events might cause problems.
LogSeverity.ERROR    # (500) Error events are likely to cause problems.
LogSeverity.CRITICAL # (600) Critical events cause more severe problems or outages.
LogSeverity.ALERT    # (700) A person must take an action immediately.
LogSeverity.EMERGENCY # (800) One or more systems are unusable.
```

## Integration with Python Logging

Cloud Logging integrates with the standard Python logging module. When you call `enable()`, it sets up a handler that sends logs to Cloud Logging.

```python
import logging as python_logging

# Initialize Cloud Logging
cloud_logging = CloudLogging()
cloud_logging.enable()

# Use the standard Python logging module
python_logging.info("This is an info message")
python_logging.warning("This is a warning message")
python_logging.error("This is an error message")
python_logging.critical("This is a critical message")

# Use a named logger
logger = python_logging.getLogger("my-component")
logger.info("This is an info message from my component")
```

## Viewing Logs

You can view your logs in the Google Cloud Console:

1. Go to the [Cloud Logging](https://console.cloud.google.com/logs) page
2. Select your project
3. Use the query editor to filter logs by:
   - Log name
   - Severity
   - Resource type
   - Labels
   - Text search

## Error Handling

The CloudLogging class handles common errors and converts them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    logging = CloudLogging()
    logging.log_struct(
        logger_name="my-logger",
        message="Test message",
        severity=LogSeverity.INFO,
    )
except exceptions.HttpError as e:
    print(f"HTTP error: {e}")
except Exception as e:
    print(f"Error: {e}")
```

## Working with Service Account Impersonation

Service account impersonation allows you to act as a service account without having its key file. This is a more secure approach than downloading and storing service account keys.

```python
# Initialize with service account impersonation
logging = CloudLogging(impersonate_account="service-account@project-id.iam.gserviceaccount.com")

# Now all operations will be performed as the impersonated service account
logging.log_struct(
    logger_name="my-logger",
    message="Test message",
    severity=LogSeverity.INFO,
)
```

For more information on service account impersonation, see the [Authentication](../authentication.md) documentation.