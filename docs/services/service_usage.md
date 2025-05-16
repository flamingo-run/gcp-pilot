# Service Usage

Service Usage is a Google Cloud service that allows you to manage which APIs are enabled on your Google Cloud projects. The `ServiceUsage` class in gcp-pilot provides a high-level interface for interacting with Google Cloud Service Usage API.

## Installation

To use the Service Usage functionality, you need to install gcp-pilot:

```bash title="Install gcp-pilot"
pip install gcp-pilot
```

## Usage

### Initialization

```python title="Initialize ServiceUsage Client"
from gcp_pilot.service_usage import ServiceUsage

service_usage = ServiceUsage() # (1)!
service_usage = ServiceUsage(project_id="my-project") # (2)!
service_usage = ServiceUsage(impersonate_account="service-account@project-id.iam.gserviceaccount.com") # (3)!
```

1.  Initialize with default credentials
2.  Initialize with specific project
3.  Initialize with service account impersonation

### Managing Services

#### Listing Services

```python title="List Services"
from gcp_pilot.service_usage import ServiceUsage, ServiceStatus

for service in service_usage.list_services(): # (1)!
    print(f"Service: {service['name']}")

for service in service_usage.list_services(project_id="my-project"): # (2)!
    print(f"Service: {service['name']}")

for service in service_usage.list_services(status=ServiceStatus.DISABLED): # (3)!
    print(f"Service: {service['name']}")
```

1.  List all enabled services in a project
2.  List all services in a specific project
3.  List all disabled services

#### Getting a Service

```python title="Get a Service"
service = service_usage.get_service( # (1)!
    service_name="compute.googleapis.com",
    project_id="my-project",  # (2)!
)
```

1.  Get information about a specific service
2.  Optional: defaults to the project associated with credentials

#### Enabling a Service

```python title="Enable a Service"
service_usage.enable_service( # (1)!
    service_name="compute.googleapis.com",
    project_id="my-project",  # (2)!
)
```

1.  Enable a service in a project
2.  Optional: defaults to the project associated with credentials

#### Disabling a Service

```python title="Disable a Service"
service_usage.disable_service( # (1)!
    service_name="compute.googleapis.com",
    project_id="my-project",  # (2)!
)
```

1.  Disable a service in a project
2.  Optional: defaults to the project associated with credentials

## Error Handling

The ServiceUsage class handles common errors and converts them to more specific exceptions:

```python title="Error Handling for Service Usage"
from gcp_pilot import exceptions

try:
    service_usage.get_service(service_name="non-existent-service")
except exceptions.NotFound:
    print("Service not found")
```