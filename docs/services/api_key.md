# API Key

API Key is a service that allows you to create and manage API keys for your Google Cloud project. The `APIKey` class in gcp-pilot provides a high-level interface for interacting with Google Cloud API Keys.

## Installation

To use the API Key functionality, you need to install gcp-pilot:

```bash
pip install gcp-pilot
```

## Usage

### Initialization

```python
from gcp_pilot.api_key import APIKey

# Initialize with default credentials
api_key = APIKey()

# Initialize with specific project
api_key = APIKey(project_id="my-project")

# Initialize with service account impersonation
api_key = APIKey(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

### Creating an API Key

```python
# Create a simple API key
key = api_key.create(
    key_id="my-api-key",
    display_name="My API Key",
)

# Create an API key with API targets
key = api_key.create(
    key_id="my-api-key",
    display_name="My API Key",
    api_targets=["maps.googleapis.com", "places.googleapis.com"],
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
```

### Getting an API Key

```python
# Get information about an API key
key = api_key.get(
    key_id="my-api-key",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)

# Access key properties
print(f"Key ID: {key.key_id}")
print(f"Display Name: {key.display_name}")
print(f"Created At: {key.created_at}")
print(f"Updated At: {key.updated_at}")
print(f"API Targets: {key.api_targets}")
print(f"Key Value: {key.value}")
```

### Looking Up an API Key

```python
# Look up an API key by its value
key = api_key.lookup(key="AIza...")

# Check if an API key exists
exists = api_key.exists(key="AIza...")
if exists:
    print("API key exists")
else:
    print("API key does not exist")
```

### Listing API Keys

```python
# List all API keys in a project
for key in api_key.list():
    print(f"Key ID: {key.key_id}, Display Name: {key.display_name}")

# List API keys in a specific project
for key in api_key.list(project_id="my-project"):
    print(f"Key ID: {key.key_id}, Display Name: {key.display_name}")
```

### Getting the API Key String

```python
# Get the actual API key string
key_data = api_key.get_key_string(
    key_id="my-api-key",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"API Key: {key_data['keyString']}")
```

### Deleting and Undeleting API Keys

```python
# Delete an API key
api_key.delete(
    key_id="my-api-key",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)

# Undelete a previously deleted API key
api_key.undelete(
    key_id="my-api-key",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
```

## The Key Class

The `Key` class is a dataclass that represents an API key. It provides convenient properties for accessing the key's attributes:

```python
from gcp_pilot.api_key import APIKey

api_key = APIKey()
key = api_key.get(key_id="my-api-key")

# Access key properties
print(f"Key ID: {key.key_id}")
print(f"UID: {key.uid}")
print(f"ETag: {key.etag}")
print(f"Display Name: {key.display_name}")
print(f"Created At: {key.created_at}")
print(f"Updated At: {key.updated_at}")
print(f"API Targets: {key.api_targets}")
print(f"Key Value: {key.value}")
```

## Error Handling

The APIKey class handles common errors and converts them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    api_key.get(key_id="non-existent-key")
except exceptions.NotFound:
    print("API key not found")

try:
    api_key.lookup(key="invalid-key")
except exceptions.NotAllowed:
    print("Invalid API key")
```