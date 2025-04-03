# Identity Platform

Identity Platform is a customer identity and access management (CIAM) platform that helps organizations add identity and access management functionality to their applications. The `IdentityPlatform` and `IdentityPlatformAdmin` classes in gcp-pilot provide high-level interfaces for interacting with Google Identity Platform (Firebase Auth).

## Installation

To use the Identity Platform functionality, you need to install gcp-pilot:

```bash
pip install gcp-pilot
```

## Usage

### IdentityPlatform

The `IdentityPlatform` class allows you to manage users and authentication in Google Identity Platform.

#### Initialization

```python
from gcp_pilot.identity_platform import IdentityPlatform

# Initialize with default credentials
identity = IdentityPlatform()

# Initialize with specific project
identity = IdentityPlatform(project_id="my-project")

# Initialize with a specific tenant
identity = IdentityPlatform(tenant_id="my-tenant")

# Initialize with service account impersonation
identity = IdentityPlatform(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

#### User Management

##### Finding Users

```python
# Find a user by email
user = identity.find(
    email="user@example.com",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    tenant_id="my-tenant",  # Optional: defaults to the tenant specified during initialization
)
print(f"User ID: {user.id}")
print(f"Email: {user.email}")
print(f"Verified: {user.verified}")
print(f"Created At: {user.created_at}")

# Find a user by phone number
user = identity.find(
    phone_number="+1234567890",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    tenant_id="my-tenant",  # Optional: defaults to the tenant specified during initialization
)
print(f"User ID: {user.id}")
print(f"Email: {user.email}")
print(f"Verified: {user.verified}")
print(f"Created At: {user.created_at}")

# Look up multiple users by email
users = identity.lookup(
    email="user@example.com",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    tenant_id="my-tenant",  # Optional: defaults to the tenant specified during initialization
)
for user in users:
    print(f"User ID: {user.id}")
    print(f"Email: {user.email}")
    print(f"Verified: {user.verified}")
    print(f"Created At: {user.created_at}")
```

##### Listing Users

```python
# List all users
users = identity.list_users(
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    tenant_id="my-tenant",  # Optional: defaults to the tenant specified during initialization
)
for user in users:
    print(f"User ID: {user.id}")
    print(f"Email: {user.email}")
    print(f"Verified: {user.verified}")
    print(f"Created At: {user.created_at}")
```

##### Creating Users

```python
# Sign up a new user with email and password
user = identity.sign_up(
    email="user@example.com",
    password="securepassword",
    name="John Doe",  # Optional: display name
    photo_url="https://example.com/photo.jpg",  # Optional: profile photo URL
    phone_number="+1234567890",  # Optional: phone number
    user_id="custom-user-id",  # Optional: custom user ID
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    tenant_id="my-tenant",  # Optional: defaults to the tenant specified during initialization
)
print(f"User ID: {user.id}")
print(f"Email: {user.email}")
print(f"Verified: {user.verified}")
print(f"Created At: {user.created_at}")
```

##### Updating Users

```python
# Update a user's information
response = identity.update(
    user_id="user-id",
    email="new-email@example.com",  # Optional: new email
    password="newsecurepassword",  # Optional: new password
    phone_number="+1234567890",  # Optional: new phone number
    name="John Smith",  # Optional: new display name
    photo_url="https://example.com/new-photo.jpg",  # Optional: new profile photo URL
    attributes={"role": "admin", "subscription": "premium"},  # Optional: custom attributes
    enabled=True,  # Optional: enable or disable the user
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    tenant_id="my-tenant",  # Optional: defaults to the tenant specified during initialization
)
print(f"Updated user: {response}")
```

##### Deleting and Disabling Users

```python
# Delete a user
response = identity.delete_user(
    user_id="user-id",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    tenant_id="my-tenant",  # Optional: defaults to the tenant specified during initialization
)
print(f"Deleted user: {response}")

# Disable a user
response = identity.disable_user(
    user_id="user-id",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    tenant_id="my-tenant",  # Optional: defaults to the tenant specified during initialization
)
print(f"Disabled user: {response}")

# Enable a user
response = identity.enable_user(
    user_id="user-id",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    tenant_id="my-tenant",  # Optional: defaults to the tenant specified during initialization
)
print(f"Enabled user: {response}")
```

#### Authentication

##### Email and Password Authentication

```python
# Sign in with email and password
response = identity.sign_in_with_password(
    email="user@example.com",
    password="securepassword",
    tenant_id="my-tenant",  # Optional: defaults to the tenant specified during initialization
)
print(f"ID Token: {response['idToken']}")
print(f"Refresh Token: {response['refreshToken']}")
print(f"Expires In: {response['expiresIn']}")
```

##### Phone Number Authentication

```python
# Sign in with phone number and verification code
response = identity.sign_in_with_phone_number(
    phone_number="+1234567890",
    code="123456",  # Verification code sent to the phone
    tenant_id="my-tenant",  # Optional: defaults to the tenant specified during initialization
)
print(f"ID Token: {response['idToken']}")
print(f"Refresh Token: {response['refreshToken']}")
print(f"Expires In: {response['expiresIn']}")
```

##### Custom Token Authentication

```python
# Sign in with a custom token
response = identity.sign_in_with_custom_token(
    token="custom-token",
    tenant_id="my-tenant",  # Optional: defaults to the tenant specified during initialization
)
print(f"ID Token: {response['idToken']}")
print(f"Refresh Token: {response['refreshToken']}")
print(f"Expires In: {response['expiresIn']}")
```

##### Email Link Authentication

```python
# Sign in with an email link
response = identity.sign_in_with_email_link(
    email="user@example.com",
    code="oob-code",  # One-time code from the email link
    tenant_id="my-tenant",  # Optional: defaults to the tenant specified during initialization
)
print(f"ID Token: {response['idToken']}")
print(f"Refresh Token: {response['refreshToken']}")
print(f"Expires In: {response['expiresIn']}")
```

#### Email Verification and Password Reset

```python
from gcp_pilot.identity_platform import OOBCodeType

# Generate an email verification code
response = identity.generate_email_code(
    type=OOBCodeType.VERIFY,
    email="user@example.com",
    ip_address="192.0.2.1",  # Optional: IP address of the user
    send_email=False,  # Optional: if True, sends the email directly; if False, returns the code
    redirect_url="https://example.com/verified",  # Optional: URL to redirect to after verification
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    tenant_id="my-tenant",  # Optional: defaults to the tenant specified during initialization
)
print(f"Verification URL: {response['url']}")
print(f"Verification Code: {response['code']}")

# Generate a password reset code
response = identity.generate_email_code(
    type=OOBCodeType.RESET,
    email="user@example.com",
    ip_address="192.0.2.1",  # Optional: IP address of the user
    send_email=False,  # Optional: if True, sends the email directly; if False, returns the code
    redirect_url="https://example.com/reset-password",  # Optional: URL to redirect to after reset
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    tenant_id="my-tenant",  # Optional: defaults to the tenant specified during initialization
)
print(f"Reset URL: {response['url']}")
print(f"Reset Code: {response['code']}")

# Generate an email sign-in link
response = identity.generate_email_code(
    type=OOBCodeType.SIGNIN,
    email="user@example.com",
    ip_address="192.0.2.1",  # Optional: IP address of the user
    send_email=False,  # Optional: if True, sends the email directly; if False, returns the code
    redirect_url="https://example.com/signin",  # Optional: URL to redirect to after sign-in
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    tenant_id="my-tenant",  # Optional: defaults to the tenant specified during initialization
)
print(f"Sign-in URL: {response['url']}")
print(f"Sign-in Code: {response['code']}")

# Reset a password with a reset code
response = identity.reset_password(
    email="user@example.com",
    new_password="newsecurepassword",
    oob_code="reset-code",  # Code from the password reset email
    tenant_id="my-tenant",  # Optional: defaults to the tenant specified during initialization
)
print(f"Reset password: {response}")

# Reset a password with the old password
response = identity.reset_password(
    email="user@example.com",
    new_password="newsecurepassword",
    old_password="oldsecurepassword",
    tenant_id="my-tenant",  # Optional: defaults to the tenant specified during initialization
)
print(f"Reset password: {response}")
```

### IdentityPlatformAdmin

The `IdentityPlatformAdmin` class allows you to manage the configuration of Google Identity Platform.

#### Initialization

```python
from gcp_pilot.identity_platform import IdentityPlatformAdmin

# Initialize with default credentials
admin = IdentityPlatformAdmin()

# Initialize with specific project
admin = IdentityPlatformAdmin(project_id="my-project")

# Initialize with a specific tenant
admin = IdentityPlatformAdmin(tenant_id="my-tenant")

# Initialize with service account impersonation
admin = IdentityPlatformAdmin(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

#### Managing Configuration

```python
# Get the current configuration
config = admin.get_config(
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Authorized Domains: {config.get('authorizedDomains', [])}")

# Add authorized domains
config = admin.add_authorized_domains(
    domains=["example.com", "example.org"],
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Updated Authorized Domains: {config.get('authorizedDomains', [])}")

# Remove authorized domains
config = admin.remove_authorized_domains(
    domains=["example.org"],
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Updated Authorized Domains: {config.get('authorizedDomains', [])}")

# Set authorized domains (replaces all existing domains)
config = admin.set_authorized_domains(
    domains=["example.com", "example.net"],
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Updated Authorized Domains: {config.get('authorizedDomains', [])}")
```

### Working with Firebase Auth Tokens

The `FirebaseAuthToken` class allows you to parse and validate Firebase Auth tokens.

```python
from gcp_pilot.identity_platform import FirebaseAuthToken

# Parse and validate a Firebase Auth token
token = FirebaseAuthToken(
    jwt_token="id-token-from-firebase",
    validate_expiration=True,  # Optional: if False, ignores token expiration
)

# Access token information
print(f"Provider ID: {token.provider_id}")
print(f"Tenant ID: {token.tenant_id}")
print(f"Event Type: {token.event_type}")
print(f"IP Address: {token.ip_address}")
print(f"User Agent: {token.user_agent}")
print(f"Expiration Date: {token.expiration_date}")
print(f"Event ID: {token.event_id}")

# Access user information
print(f"User ID: {token.user.id}")
print(f"Email: {token.user.email}")
print(f"Name: {token.user.name}")
print(f"Verified: {token.user.verified}")
print(f"Disabled: {token.user.disabled}")
print(f"Created At: {token.user.created_at}")
print(f"Last Login At: {token.user.last_login_at}")

# Access OAuth information (if available)
if token.oauth:
    print(f"OAuth ID Token: {token.oauth.id_token}")
    print(f"OAuth Access Token: {token.oauth.access_token}")
    print(f"OAuth Refresh Token: {token.oauth.refresh_token}")
    print(f"OAuth Token Secret: {token.oauth.token_secret}")

# Access JWT information
print(f"Audience: {token.jwt_info.aud}")
print(f"Issuer: {token.jwt_info.iss}")
print(f"Subject: {token.jwt_info.sub}")
print(f"Issued At: {token.jwt_info.iat}")
print(f"Expires At: {token.jwt_info.exp}")
print(f"Is Expired: {token.jwt_info.is_expired}")

# Access raw user information
print(f"Raw User Info: {token.raw_user}")
```

## Error Handling

The Identity Platform classes handle common errors and convert them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    identity.find(email="non-existent@example.com")
except exceptions.NotFound:
    print("User not found")

try:
    identity.lookup(email=None, phone_number=None)
except exceptions.ValidationError:
    print("Either email or phone_number must be provided")

try:
    identity.reset_password(email="user@example.com", new_password="newpassword")
except exceptions.ValidationError:
    print("Either old_password or oob_code must be provided")
```

## Working with Multi-Tenancy

Identity Platform supports multi-tenancy, which allows you to manage separate user pools for different applications or organizations within the same project.

```python
# Initialize with a specific tenant
identity = IdentityPlatform(tenant_id="my-tenant")

# All operations will use this tenant by default
user = identity.find(email="user@example.com")

# You can also specify a different tenant for a specific operation
user = identity.find(email="user@example.com", tenant_id="other-tenant")
```

## Provider Types

The `FirebaseProviderType` enum represents the different authentication providers supported by Identity Platform:

```python
from gcp_pilot.identity_platform import FirebaseProviderType

# Available provider types
FirebaseProviderType.GOOGLE     # Google authentication
FirebaseProviderType.FACEBOOK   # Facebook authentication
FirebaseProviderType.GITHUB     # GitHub authentication
FirebaseProviderType.MICROSOFT  # Microsoft authentication
FirebaseProviderType.APPLE      # Apple authentication
FirebaseProviderType.PASSWORD   # Email/password authentication
FirebaseProviderType.PASSWORDLESS  # Email link authentication
```

You can use these provider types to check the authentication method used by a user:

```python
if token.provider_id == FirebaseProviderType.GOOGLE.value:
    print("User authenticated with Google")
```
