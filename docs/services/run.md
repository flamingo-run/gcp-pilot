# Cloud Run

Cloud Run is a fully managed compute platform that automatically scales your stateless containers. The `CloudRun` class in gcp-pilot provides a high-level interface for interacting with Google Cloud Run.

## Installation

To use the Cloud Run functionality, you need to install gcp-pilot:

```bash
pip install gcp-pilot
```

## Usage

### Initialization

```python
from gcp_pilot.run import CloudRun

# Initialize with default credentials
cloud_run = CloudRun()

# Initialize with specific project
cloud_run = CloudRun(project_id="my-project")

# Initialize with specific location
cloud_run = CloudRun(location="us-central1")

# Initialize with service account impersonation
cloud_run = CloudRun(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

### Managing Services

#### Listing Services

```python
# List all Cloud Run services in a project
services = cloud_run.list_services(
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
for service in services:
    print(f"Service: {service['metadata']['name']}")
    print(f"URL: {service['status']['url']}")
    print(f"Latest Revision: {service['status']['latestCreatedRevisionName']}")
```

#### Getting a Service

```python
# Get information about a specific Cloud Run service
service = cloud_run.get_service(
    service_name="my-service",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
)
print(f"Service: {service['metadata']['name']}")
print(f"URL: {service['status']['url']}")
print(f"Latest Revision: {service['status']['latestCreatedRevisionName']}")
```

#### Creating a Service

```python
# Create a new Cloud Run service
service = cloud_run.create_service(
    service_name="my-service",
    image="gcr.io/my-project/my-image:latest",  # Container image to deploy
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
    service_account="service-account@my-project.iam.gserviceaccount.com",  # Optional: service account to run the service
    trigger_id="my-trigger",  # Optional: Cloud Build trigger ID
    ram=512,  # Optional: memory in MB, defaults to 256
    concurrency=100,  # Optional: maximum concurrent requests per container, defaults to 80
    timeout=600,  # Optional: request timeout in seconds, defaults to 300
    port=8080,  # Optional: container port, defaults to 8080
)
print(f"Service created: {service['metadata']['name']}")
print(f"URL: {service['status']['url']}")
```

### Managing Revisions

```python
# List all revisions of a Cloud Run service
revisions = cloud_run.list_revisions(
    service_name="my-service",  # Optional: if provided, only lists revisions for this service
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
for revision in revisions:
    print(f"Revision: {revision['metadata']['name']}")
    print(f"Created: {revision['metadata']['creationTimestamp']}")
    print(f"Image: {revision['spec']['containers'][0]['image']}")
```

### Managing Domain Mappings

#### Listing Domain Mappings

```python
# List all domain mappings in a project
domain_mappings = cloud_run.list_domain_mappings(
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
for mapping in domain_mappings:
    print(f"Domain: {mapping['metadata']['name']}")
    print(f"Service: {mapping['spec']['routeName']}")
    print(f"Status: {mapping['status']['conditions'][0]['status']}")
```

#### Getting a Domain Mapping

```python
# Get information about a specific domain mapping
domain_mapping = cloud_run.get_domain_mapping(
    domain="example.com",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
)
print(f"Domain: {domain_mapping['metadata']['name']}")
print(f"Service: {domain_mapping['spec']['routeName']}")
print(f"Status: {domain_mapping['status']['conditions'][0]['status']}")
```

#### Creating a Domain Mapping

```python
# Create a new domain mapping for a Cloud Run service
domain_mapping = cloud_run.create_domain_mapping(
    domain="example.com",
    service_name="my-service",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
    exists_ok=True,  # Optional: if True, returns the existing mapping if it already exists
    force=True,  # Optional: if True, forces the mapping even if it conflicts with existing mappings
)
print(f"Domain mapping created: {domain_mapping['metadata']['name']}")
print(f"Service: {domain_mapping['spec']['routeName']}")
print(f"Status: {domain_mapping['status']['conditions'][0]['status']}")
```

#### Deleting a Domain Mapping

```python
# Delete a domain mapping
cloud_run.delete_domain_mapping(
    domain="example.com",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
)
```

### Listing Locations

```python
# List all locations where Cloud Run is available
locations = cloud_run.list_locations(
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
for location in locations:
    print(f"Location: {location['locationId']}")
    print(f"Display Name: {location['displayName']}")
    print(f"Metadata: {location['metadata']}")
```

## Error Handling

The CloudRun class handles common errors and converts them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    cloud_run.get_service(service_name="non-existent-service")
except exceptions.NotFound:
    print("Service not found")

try:
    cloud_run.create_domain_mapping(domain="existing-domain.com", service_name="my-service", exists_ok=False)
except exceptions.AlreadyExists:
    print("Domain mapping already exists")
```

## Working with Service Account Impersonation

Service account impersonation allows you to act as a service account without having its key file. This is a more secure approach than downloading and storing service account keys.

```python
# Initialize with service account impersonation
cloud_run = CloudRun(impersonate_account="service-account@project-id.iam.gserviceaccount.com")

# Now all operations will be performed as the impersonated service account
services = cloud_run.list_services()
```

For more information on service account impersonation, see the [Authentication](../authentication.md) documentation.

## Best Practices

Here are some best practices for working with Cloud Run:

1. **Use container images from trusted sources**: Only deploy container images from trusted sources to minimize security risks.
2. **Optimize container startup time**: Cloud Run scales to zero when not in use, so optimizing container startup time improves user experience.
3. **Handle concurrency properly**: Set an appropriate concurrency value based on your application's requirements.
4. **Use appropriate memory settings**: Allocate enough memory for your application to run efficiently, but not so much that you waste resources.
5. **Implement health checks**: Add health check endpoints to your application to help Cloud Run determine when your service is ready to receive traffic.
6. **Use custom domains with SSL**: Set up custom domains with SSL certificates for production services.
7. **Monitor your services**: Set up monitoring and alerting for your Cloud Run services to detect and respond to issues quickly.