# Cloud Monitoring

Cloud Monitoring is a service that provides visibility into the performance, uptime, and overall health of cloud-powered applications. The `Monitoring` class in gcp-pilot provides a high-level interface for interacting with Google Cloud Monitoring.

## Installation

To use the Cloud Monitoring functionality, you need to install gcp-pilot:

```bash
pip install gcp-pilot
```

## Usage

### Initialization

```python
from gcp_pilot.monitoring import Monitoring

# Initialize with default credentials
monitoring = Monitoring()

# Initialize with specific project
monitoring = Monitoring(project_id="my-project")

# Initialize with service account impersonation
monitoring = Monitoring(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

### Managing Services

Cloud Monitoring services represent the applications or components that you want to monitor.

#### Listing Services

```python
# List all services in a project
services = monitoring.list_services()
for service in services:
    print(f"Service: {service['name']}")
    print(f"Display Name: {service['displayName']}")

# List services in a specific project
services = monitoring.list_services(project_id="my-project")
for service in services:
    print(f"Service: {service['name']}")
    print(f"Display Name: {service['displayName']}")
```

#### Getting a Service

```python
# Get information about a specific service
service = monitoring.get_service(
    service_id="my-service",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Service: {service['name']}")
print(f"Display Name: {service['displayName']}")
print(f"Type: {service['type']}")
```

#### Creating a Service

```python
# Create a new service
service = monitoring.create_service(
    name="my-service",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Service created: {service['name']}")
print(f"Display Name: {service['displayName']}")
```

## Working with Service Monitoring

Cloud Monitoring services are used to group related resources and metrics. Once you've created a service, you can:

1. Set up Service Level Objectives (SLOs) for the service
2. Create uptime checks for the service
3. Set up alerts based on service performance
4. View service dashboards

While the current implementation of the `Monitoring` class focuses on service management, you can use the Google Cloud Console to perform these additional tasks:

1. Go to the [Cloud Monitoring](https://console.cloud.google.com/monitoring) page
2. Select your project
3. Navigate to the "Services" section
4. Select the service you created
5. Use the UI to set up SLOs, uptime checks, and alerts

## Error Handling

The Monitoring class handles common errors and converts them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    monitoring.get_service(service_id="non-existent-service")
except exceptions.NotFound:
    print("Service not found")

try:
    monitoring.create_service(name="existing-service")
except exceptions.AlreadyExists:
    print("Service already exists")
```

## Working with Service Account Impersonation

Service account impersonation allows you to act as a service account without having its key file. This is a more secure approach than downloading and storing service account keys.

```python
# Initialize with service account impersonation
monitoring = Monitoring(impersonate_account="service-account@project-id.iam.gserviceaccount.com")

# Now all operations will be performed as the impersonated service account
services = monitoring.list_services()
```

For more information on service account impersonation, see the [Authentication](../authentication.md) documentation.

## Additional Resources

For more advanced monitoring capabilities, you can use the full Google Cloud Monitoring API. The `Monitoring` class in gcp-pilot provides a simplified interface for common operations, but the full API offers more features:

- Creating and managing metrics
- Setting up dashboards
- Configuring alerts
- Creating uptime checks
- Setting up Service Level Objectives (SLOs)

For more information, see the [Google Cloud Monitoring documentation](https://cloud.google.com/monitoring/docs).