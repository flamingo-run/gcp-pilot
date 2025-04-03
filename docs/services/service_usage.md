# Service Usage

Service Usage is a Google Cloud service that allows you to manage which APIs are enabled on your Google Cloud projects. The `ServiceUsage` class in gcp-pilot provides a high-level interface for interacting with Google Cloud Service Usage API.

## Installation

To use the Service Usage functionality, you need to install gcp-pilot:

```bash
pip install gcp-pilot
```

## Usage

### Initialization

```python
from gcp_pilot.service_usage import ServiceUsage

# Initialize with default credentials
service_usage = ServiceUsage()

# Initialize with specific project
service_usage = ServiceUsage(project_id="my-project")

# Initialize with service account impersonation
service_usage = ServiceUsage(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

### Managing Services

#### Listing Services

```python
from gcp_pilot.service_usage import ServiceUsage, ServiceStatus

# List all enabled services in a project
for service in service_usage.list_services():
    print(f"Service: {service['name']}")

# List all services in a specific project
for service in service_usage.list_services(project_id="my-project"):
    print(f"Service: {service['name']}")

# List all disabled services
for service in service_usage.list_services(status=ServiceStatus.DISABLED):
    print(f"Service: {service['name']}")
```

#### Getting a Service

```python
# Get information about a specific service
service = service_usage.get_service(
    service_name="compute.googleapis.com",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
```

#### Enabling a Service

```python
# Enable a service in a project
service_usage.enable_service(
    service_name="compute.googleapis.com",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
```

#### Disabling a Service

```python
# Disable a service in a project
service_usage.disable_service(
    service_name="compute.googleapis.com",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
```

## Error Handling

The ServiceUsage class handles common errors and converts them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    service_usage.get_service(service_name="non-existent-service")
except exceptions.NotFound:
    print("Service not found")
```