# IAM (Identity and Access Management)

IAM (Identity and Access Management) is a service that allows you to manage access control to your Google Cloud resources. The `IdentityAccessManager` and `IAMCredentials` classes in gcp-pilot provide high-level interfaces for interacting with Google Cloud IAM.

## Installation

To use the IAM functionality, you need to install gcp-pilot with the iam extra:

```bash
pip install gcp-pilot[iam]
```

## Usage

### IdentityAccessManager

The `IdentityAccessManager` class allows you to manage service accounts and their keys, as well as IAM policies.

#### Initialization

```python
from gcp_pilot.iam import IdentityAccessManager

# Initialize with default credentials
iam = IdentityAccessManager()

# Initialize with specific project
iam = IdentityAccessManager(project_id="my-project")

# Initialize with service account impersonation
iam = IdentityAccessManager(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

#### Managing Service Accounts

```python
# Create a service account
service_account = iam.create_service_account(
    name="my-service-account",
    display_name="My Service Account",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    exists_ok=True,  # Optional: if True, returns the existing service account if it already exists
)
print(f"Service Account: {service_account['email']}")

# Get a service account
service_account = iam.get_service_account(
    name="my-service-account",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Service Account: {service_account['email']}")

# List all service accounts in a project
service_accounts = iam.list_service_accounts(
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
for account in service_accounts:
    print(f"Service Account: {account['email']}")
```

#### Managing Service Account Keys

```python
# Create a key for a service account
key = iam.create_key(
    service_account_name="my-service-account",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Key ID: {key['id']}")
print(f"Private Key JSON: {key['json']}")

# List keys for a service account
keys = iam.list_keys(
    service_account_name="my-service-account",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
for key in keys:
    print(f"Key ID: {key['id']}")
    print(f"Valid After: {key['validAfterTime']}")
    print(f"Valid Before: {key['validBeforeTime']}")

# Get a specific key
key = iam.get_key(
    key_id="key-id",
    service_account_name="my-service-account",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Key ID: {key['id']}")
print(f"Valid After: {key['validAfterTime']}")
print(f"Valid Before: {key['validBeforeTime']}")

# Delete a key
iam.delete_key(
    key_id="key-id",
    service_account_name="my-service-account",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
```

#### Managing IAM Policies

```python
# Get the IAM policy for a service account
policy = iam.get_policy(
    email="my-service-account@my-project.iam.gserviceaccount.com",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Policy: {policy}")

# Bind a member to a role for a service account
policy = iam.bind_member(
    target_email="my-service-account@my-project.iam.gserviceaccount.com",
    member_email="user@example.com",
    role="roles/iam.serviceAccountUser",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Updated Policy: {policy}")

# Remove a member from a role for a service account
policy = iam.remove_member(
    target_email="my-service-account@my-project.iam.gserviceaccount.com",
    member_email="user@example.com",
    role="roles/iam.serviceAccountUser",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Updated Policy: {policy}")

# Set a custom policy for a service account
policy = iam.set_policy(
    email="my-service-account@my-project.iam.gserviceaccount.com",
    policy=custom_policy,  # A policy object
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Updated Policy: {policy}")
```

### IAMCredentials

The `IAMCredentials` class allows you to work with IAM credentials, including JWT tokens, ID tokens, and custom tokens.

#### Initialization

```python
from gcp_pilot.iam import IAMCredentials

# Initialize with default credentials
iam_credentials = IAMCredentials()

# Initialize with service account impersonation
iam_credentials = IAMCredentials(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

#### Working with JWT Tokens

```python
# Encode a JWT token
payload = {
    "sub": "user@example.com",
    "aud": "https://example.com",
    "iat": datetime.now(tz=UTC).timestamp(),
    "exp": (datetime.now(tz=UTC) + timedelta(hours=1)).timestamp(),
    "custom_claim": "custom_value",
}
jwt_token = iam_credentials.encode_jwt(
    payload=payload,
    service_account_email="service-account@project-id.iam.gserviceaccount.com",
)
print(f"JWT Token: {jwt_token}")

# Decode a JWT token
decoded_token = IAMCredentials.decode_jwt(
    token=jwt_token,
    issuer_email="service-account@project-id.iam.gserviceaccount.com",
    audience="https://example.com",
    verify=True,  # Optional: if True, verifies the token signature
    cache_certs=True,  # Optional: if True, caches the public certificates
    clock_skew_in_seconds=0,  # Optional: allows for clock skew
)
print(f"Decoded Token: {decoded_token}")
```

#### Working with ID Tokens

```python
# Generate an ID token
id_token = iam_credentials.generate_id_token(
    audience="https://example.com",
    service_account_email="service-account@project-id.iam.gserviceaccount.com",  # Optional: defaults to the impersonated account
)
print(f"ID Token: {id_token}")

# Decode an ID token
decoded_token = IAMCredentials.decode_id_token(
    token=id_token,
    audience="https://example.com",  # Optional: if provided, verifies the audience
)
print(f"Decoded Token: {decoded_token}")
```

#### Working with Custom Tokens

```python
# Generate a custom token for Firebase Authentication
custom_token = iam_credentials.generate_custom_token(
    uid="user123",  # Optional: defaults to a random UUID
    expires_in_seconds=3600,  # Optional: defaults to 12 hours
    tenant_id="tenant123",  # Optional: for multi-tenancy
    auth_email="service-account@project-id.iam.gserviceaccount.com",  # Optional: defaults to the impersonated account
    claims={"premium_account": True},  # Optional: custom claims
)
print(f"Custom Token: {custom_token}")

# Decode a custom token
decoded_token = IAMCredentials.decode_custom_token(
    token=custom_token,
    issuer_email="service-account@project-id.iam.gserviceaccount.com",
    verify=True,  # Optional: if True, verifies the token signature
)
print(f"Decoded Token: {decoded_token}")
```

## Error Handling

The IAM classes handle common errors and convert them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    iam.get_service_account(name="non-existent-account")
except exceptions.NotFound:
    print("Service account not found")

try:
    iam.create_service_account(name="existing-account", display_name="Existing Account", exists_ok=False)
except exceptions.AlreadyExists:
    print("Service account already exists")

try:
    iam_credentials.encode_jwt(payload={"exp": datetime.now(tz=UTC).timestamp() + 13 * 60 * 60}, service_account_email="service-account@project-id.iam.gserviceaccount.com")
except ValueError:
    print("JWT tokens cannot be valid for more than 12 hours")
```

## Working with Service Account Impersonation

Service account impersonation allows you to act as a service account without having its key file. This is a more secure approach than downloading and storing service account keys.

```python
# Initialize with service account impersonation
iam = IdentityAccessManager(impersonate_account="service-account@project-id.iam.gserviceaccount.com")

# Now all operations will be performed as the impersonated service account
service_account = iam.get_service_account(name="another-service-account")
```

For more information on service account impersonation, see the [Authentication](../authentication.md) documentation.

## Common IAM Roles

Here are some common IAM roles that you might use with service accounts:

- `roles/iam.serviceAccountUser`: Allows a user to impersonate a service account
- `roles/iam.serviceAccountTokenCreator`: Allows a user to create tokens for a service account
- `roles/iam.serviceAccountKeyAdmin`: Allows a user to manage keys for a service account
- `roles/iam.serviceAccountAdmin`: Allows a user to create and manage service accounts

You can use these roles when binding members to service accounts:

```python
# Grant the serviceAccountUser role to a user
policy = iam.bind_member(
    target_email="my-service-account@my-project.iam.gserviceaccount.com",
    member_email="user@example.com",
    role="roles/iam.serviceAccountUser",
)
```