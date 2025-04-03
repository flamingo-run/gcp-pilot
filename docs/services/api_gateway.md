# API Gateway

API Gateway is a fully managed service that enables you to create, secure, and monitor APIs for your Google Cloud backends. The `APIGateway` class in gcp-pilot provides a high-level interface for interacting with Google Cloud API Gateway.

## Installation

To use the API Gateway functionality, you need to install gcp-pilot:

```bash
pip install gcp-pilot
```

## Usage

### Initialization

```python
from gcp_pilot.api_gateway import APIGateway

# Initialize with default credentials
api_gateway = APIGateway()

# Initialize with specific project
api_gateway = APIGateway(project_id="my-project")

# Initialize with service account impersonation
api_gateway = APIGateway(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

### Managing APIs

#### Listing APIs

```python
# List all APIs in a project
for api in api_gateway.list_apis():
    print(f"API: {api['name']}")

# List APIs in a specific location
for api in api_gateway.list_apis(location="us-central1"):
    print(f"API: {api['name']}")
```

#### Getting an API

```python
# Get information about an API
api = api_gateway.get_api(api_name="my-api")
```

#### Creating an API

```python
# Create a simple API
api = api_gateway.create_api(
    api_name="my-api",
    display_name="My API",
)

# Create an API with labels
api = api_gateway.create_api(
    api_name="my-api",
    display_name="My API",
    labels={"environment": "production"},
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    wait=True,  # Optional: wait for the operation to complete
)
```

#### Deleting an API

```python
# Delete an API
api_gateway.delete_api(
    api_name="my-api",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
```

### Managing API Configurations

#### Listing API Configurations

```python
# List all configurations for an API
for config in api_gateway.list_configs(api_name="my-api"):
    print(f"Config: {config['name']}")
```

#### Getting an API Configuration

```python
# Get information about an API configuration
config = api_gateway.get_config(
    config_name="my-config",
    api_name="my-api",
)
```

#### Creating an API Configuration

```python
from pathlib import Path

# Create an API configuration
config = api_gateway.create_config(
    config_name="my-config",
    api_name="my-api",
    service_account="service-account@project-id.iam.gserviceaccount.com",
    open_api_file=Path("/path/to/openapi.yaml"),
    display_name="My API Configuration",
    labels={"environment": "production"},
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    wait=True,  # Optional: wait for the operation to complete
)
```

#### Deleting an API Configuration

```python
# Delete an API configuration
api_gateway.delete_config(
    config_name="my-config",
    api_name="my-api",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
```

### Managing Gateways

#### Listing Gateways

```python
# List all gateways in a project
for gateway in api_gateway.list_gateways():
    print(f"Gateway: {gateway['name']}")

# List gateways in a specific location
for gateway in api_gateway.list_gateways(location="us-central1"):
    print(f"Gateway: {gateway['name']}")
```

#### Getting a Gateway

```python
# Get information about a gateway
gateway = api_gateway.get_gateway(
    gateway_name="my-gateway",
    location="us-central1",  # Optional: defaults to the default location
)
```

#### Creating a Gateway

```python
# Create a gateway
gateway = api_gateway.create_gateway(
    gateway_name="my-gateway",
    api_name="my-api",
    config_name="my-config",
    labels={"environment": "production"},
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
    wait=True,  # Optional: wait for the operation to complete
)
```

#### Deleting a Gateway

```python
# Delete a gateway
api_gateway.delete_gateway(
    gateway_name="my-gateway",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
)
```

### Enabling and Disabling API Gateway

```python
# Enable API Gateway for an API
api_gateway.enable_gateway(
    api_name="my-api",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)

# Disable API Gateway for an API
api_gateway.disable_gateway(
    api_name="my-api",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
```

## Error Handling

The APIGateway class handles common errors and converts them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    api_gateway.get_api(api_name="non-existent-api")
except exceptions.NotFound:
    print("API not found")
```