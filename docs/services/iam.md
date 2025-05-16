# IAM (Identity and Access Management)

IAM (Identity and Access Management) is a service that allows you to manage access control to your Google Cloud resources. The `IdentityAccessManager` and `IAMCredentials` classes in gcp-pilot provide high-level interfaces for interacting with Google Cloud IAM.

## Installation

To use the IAM functionality, you need to install gcp-pilot with the iam extra:

```bash title="Install IAM extra"
pip install gcp-pilot[iam]
```

## Usage

### IdentityAccessManager

The `IdentityAccessManager` class allows you to manage service accounts and their keys, as well as IAM policies.

#### Initialization

```python title="Initialize IdentityAccessManager"
from gcp_pilot.iam import IdentityAccessManager

iam = IdentityAccessManager() # (1)!
iam = IdentityAccessManager(project_id="my-project") # (2)!
iam = IdentityAccessManager(impersonate_account="service-account@project-id.iam.gserviceaccount.com") # (3)!
```

1.  Initialize with default credentials
2.  Initialize with specific project
3.  Initialize with service account impersonation

#### Managing Service Accounts

```python title="Manage Service Accounts"
service_account = iam.create_service_account( # (1)!
    name="my-service-account",
    display_name="My Service Account",
    project_id="my-project",  # (2)!
    exists_ok=True,  # (3)!
)
print(f"Service Account: {service_account['email']}")

service_account = iam.get_service_account( # (4)!
    name="my-service-account",
    project_id="my-project",  # (5)!
)
print(f"Service Account: {service_account['email']}")

service_accounts = iam.list_service_accounts( # (6)!
    project_id="my-project",  # (7)!
)
for account in service_accounts:
    print(f"Service Account: {account['email']}")
```

1.  Create a service account
2.  Optional: defaults to the project associated with credentials
3.  Optional: if True, returns the existing service account if it already exists
4.  Get a service account
5.  Optional: defaults to the project associated with credentials
6.  List all service accounts in a project
7.  Optional: defaults to the project associated with credentials

#### Managing Service Account Keys

```python title="Manage Service Account Keys"
key = iam.create_key( # (1)!
    service_account_name="my-service-account",
    project_id="my-project",  # (2)!
)
print(f"Key ID: {key['id']}")
print(f"Private Key JSON: {key['json']}")

keys = iam.list_keys( # (3)!
    service_account_name="my-service-account",
    project_id="my-project",  # (4)!
)
for key_item in keys: # Renamed key to key_item to avoid conflict with variable 'key' later
    print(f"Key ID: {key_item['id']}")
    print(f"Valid After: {key_item['validAfterTime']}")
    print(f"Valid Before: {key_item['validBeforeTime']}")

key = iam.get_key( # (5)!
    key_id="key-id",
    service_account_name="my-service-account",
    project_id="my-project",  # (6)!
)
print(f"Key ID: {key['id']}")
print(f"Valid After: {key['validAfterTime']}")
print(f"Valid Before: {key['validBeforeTime']}")

iam.delete_key( # (7)!
    key_id="key-id",
    service_account_name="my-service-account",
    project_id="my-project",  # (8)!
)
```

1.  Create a key for a service account
2.  Optional: defaults to the project associated with credentials
3.  List keys for a service account
4.  Optional: defaults to the project associated with credentials
5.  Get a specific key
6.  Optional: defaults to the project associated with credentials
7.  Delete a key
8.  Optional: defaults to the project associated with credentials

#### Managing IAM Policies

```python title="Manage IAM Policies"
policy = iam.get_policy( # (1)!
    email="my-service-account@my-project.iam.gserviceaccount.com",
    project_id="my-project",  # (2)!
)
print(f"Policy: {policy}")

policy = iam.bind_member( # (3)!
    target_email="my-service-account@my-project.iam.gserviceaccount.com",
    member_email="user@example.com",
    role="roles/iam.serviceAccountUser",
    project_id="my-project",  # (4)!
)
print(f"Updated Policy: {policy}")

policy = iam.remove_member( # (5)!
    target_email="my-service-account@my-project.iam.gserviceaccount.com",
    member_email="user@example.com",
    role="roles/iam.serviceAccountUser",
    project_id="my-project",  # (6)!
)
print(f"Updated Policy: {policy}")

policy = iam.set_policy( # (7)!
    email="my-service-account@my-project.iam.gserviceaccount.com",
    policy=custom_policy,  # (8)!
    project_id="my-project",  # (9)!
)
print(f"Updated Policy: {policy}")
```

1.  Get the IAM policy for a service account
2.  Optional: defaults to the project associated with credentials
3.  Bind a member to a role for a service account
4.  Optional: defaults to the project associated with credentials
5.  Remove a member from a role for a service account
6.  Optional: defaults to the project associated with credentials
7.  Set a custom policy for a service account
8.  A policy object
9.  Optional: defaults to the project associated with credentials

### IAMCredentials

The `IAMCredentials` class allows you to work with IAM credentials, including JWT tokens, ID tokens, and custom tokens.

#### Initialization

```python title="Initialize IAMCredentials"
from gcp_pilot.iam import IAMCredentials

iam_credentials = IAMCredentials() # (1)!
iam_credentials = IAMCredentials(impersonate_account="service-account@project-id.iam.gserviceaccount.com") # (2)!
```

1.  Initialize with default credentials
2.  Initialize with service account impersonation

#### Working with JWT Tokens

```python title="Work with JWT Tokens"
# Encode a JWT token (1)!
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

decoded_token = IAMCredentials.decode_jwt( # (2)!
    token=jwt_token,
    issuer_email="service-account@project-id.iam.gserviceaccount.com",
    audience="https://example.com",
    verify=True,  # (3)!
    cache_certs=True,  # (4)!
    clock_skew_in_seconds=0,  # (5)!
)
print(f"Decoded Token: {decoded_token}")
```

1.  Encode a JWT token
2.  Decode a JWT token
3.  Optional: if True, verifies the token signature
4.  Optional: if True, caches the public certificates
5.  Optional: allows for clock skew

#### Working with ID Tokens

```python title="Work with ID Tokens"
id_token = iam_credentials.generate_id_token( # (1)!
    audience="https://example.com",
    service_account_email="service-account@project-id.iam.gserviceaccount.com",  # (2)!
)
print(f"ID Token: {id_token}")

decoded_token = IAMCredentials.decode_id_token( # (3)!
    token=id_token,
    audience="https://example.com",  # (4)!
)
print(f"Decoded Token: {decoded_token}")
```

1.  Generate an ID token
2.  Optional: defaults to the impersonated account
3.  Decode an ID token
4.  Optional: if provided, verifies the audience

#### Working with Custom Tokens

```python title="Work with Custom Tokens"
custom_token = iam_credentials.generate_custom_token( # (1)!
    uid="user123",  # (2)!
    expires_in_seconds=3600,  # (3)!
    tenant_id="tenant123",  # (4)!
    auth_email="service-account@project-id.iam.gserviceaccount.com",  # (5)!
    claims={"premium_account": True},  # (6)!
)
print(f"Custom Token: {custom_token}")

decoded_token = IAMCredentials.decode_custom_token( # (7)!
    token=custom_token,
    issuer_email="service-account@project-id.iam.gserviceaccount.com",
    verify=True,  # (8)!
)
print(f"Decoded Token: {decoded_token}")
```

1.  Generate a custom token for Firebase Authentication
2.  Optional: defaults to a random UUID
3.  Optional: defaults to 12 hours
4.  Optional: for multi-tenancy
5.  Optional: defaults to the impersonated account
6.  Optional: custom claims
7.  Decode a custom token
8.  Optional: if True, verifies the token signature

## Error Handling

The IAM classes handle common errors and convert them to more specific exceptions:

```python title="Error Handling Examples"
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

```python title="Using Impersonated Credentials"
iam = IdentityAccessManager(impersonate_account="service-account@project-id.iam.gserviceaccount.com") # (1)!
service_account = iam.get_service_account(name="another-service-account") # (2)!
```

1.  Initialize with service account impersonation
2.  Now all operations will be performed as the impersonated service account

For more information on service account impersonation, see the [Authentication](../authentication.md) documentation.

## Common IAM Roles

Here are some common IAM roles that you might use with service accounts:

- `roles/iam.serviceAccountUser`: Allows a user to impersonate a service account
- `roles/iam.serviceAccountTokenCreator`: Allows a user to create tokens for a service account
- `roles/iam.serviceAccountKeyAdmin`: Allows a user to manage keys for a service account
- `roles/iam.serviceAccountAdmin`: Allows a user to create and manage service accounts

You can use these roles when binding members to service accounts:

```python title="Granting an IAM Role"
policy = iam.bind_member( # (1)!
    target_email="my-service-account@my-project.iam.gserviceaccount.com",
    member_email="user@example.com",
    role="roles/iam.serviceAccountUser",
)
```

1.  Grant the serviceAccountUser role to a user