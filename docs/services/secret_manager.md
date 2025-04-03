# Secret Manager

Secret Manager is a service that allows you to store, manage, and access secrets as binary blobs or text strings. The `SecretManager` class in gcp-pilot provides a high-level interface for interacting with Google Cloud Secret Manager.

## Installation

To use the Secret Manager functionality, you need to install gcp-pilot with the secret extra:

```bash
pip install gcp-pilot[secret]
```

## Usage

### Initialization

```python
from gcp_pilot.secret_manager import SecretManager

# Initialize with default credentials
secret_manager = SecretManager()

# Initialize with specific project
secret_manager = SecretManager(project_id="my-project")

# Initialize with service account impersonation
secret_manager = SecretManager(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

### Adding Secrets

```python
# Add a new secret
version_name = secret_manager.add_secret(
    key="my-secret",
    value="secret-value",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Secret version created: {version_name}")
```

If the secret doesn't exist, it will be created automatically. If it does exist, a new version will be added.

### Getting Secrets

```python
# Get the latest version of a secret
secret_value = secret_manager.get_secret(
    key="my-secret",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Secret value: {secret_value}")

# Get a specific version of a secret
secret_value = secret_manager.get_secret(
    key="my-secret",
    version=1,  # Optional: defaults to the latest version
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Secret value (version 1): {secret_value}")
```

### Listing Secrets

```python
# List all secrets in a project
secrets = secret_manager.list_secrets(
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
for name, value in secrets:
    print(f"Secret: {name}, Value: {value}")

# List secrets with a specific prefix
secrets = secret_manager.list_secrets(
    prefix="api-",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
for name, value in secrets:
    print(f"Secret: {name}, Value: {value}")

# List secrets with a specific suffix
secrets = secret_manager.list_secrets(
    suffix="-key",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
for name, value in secrets:
    print(f"Secret: {name}, Value: {value}")

# List secrets with both prefix and suffix
secrets = secret_manager.list_secrets(
    prefix="api-",
    suffix="-key",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
for name, value in secrets:
    print(f"Secret: {name}, Value: {value}")
```

### Rolling Back Secrets

```python
# Temporarily disable the latest version of a secret
response = secret_manager.rollback_secret(
    key="my-secret",
    temporarily=True,  # Optional: if True, disables the version; if False, destroys it
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Secret version disabled: {response.name}")

# Permanently destroy the latest version of a secret
response = secret_manager.rollback_secret(
    key="my-secret",
    temporarily=False,  # Optional: if True, disables the version; if False, destroys it
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Secret version destroyed: {response.name}")
```

## Error Handling

The SecretManager class handles common errors and converts them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    secret_value = secret_manager.get_secret(key="non-existent-secret")
except exceptions.NotFound:
    print("Secret not found")
```

## Working with Service Account Impersonation

Service account impersonation allows you to act as a service account without having its key file. This is a more secure approach than downloading and storing service account keys.

```python
# Initialize with service account impersonation
secret_manager = SecretManager(impersonate_account="service-account@project-id.iam.gserviceaccount.com")

# Now all operations will be performed as the impersonated service account
secret_value = secret_manager.get_secret(key="my-secret")
```

For more information on service account impersonation, see the [Authentication](../authentication.md) documentation.

## Best Practices

Here are some best practices for working with Secret Manager:

1. **Use descriptive secret names**: Choose secret names that clearly indicate their purpose and content.
2. **Rotate secrets regularly**: Create new versions of secrets on a regular schedule to minimize the impact of potential leaks.
3. **Limit access to secrets**: Use IAM policies to restrict who can access and manage secrets.
4. **Monitor secret access**: Set up audit logging to track who is accessing your secrets.
5. **Use the latest version**: Unless you have a specific reason to use an older version, always use the latest version of a secret.