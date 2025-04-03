# Identity-Aware Proxy (IAP)

Identity-Aware Proxy (IAP) is a service that provides a central authorization layer for applications accessed by HTTPS. The `IdentityAwareProxy` class in gcp-pilot provides a high-level interface for interacting with Google Cloud IAP.

## Installation

To use the IAP functionality, you need to install gcp-pilot:

```bash
pip install gcp-pilot
```

## Usage

### Initialization

```python
from gcp_pilot.iap import IdentityAwareProxy

# Initialize with an audience
iap = IdentityAwareProxy(audience="https://example.com")

# Initialize with service account impersonation
iap = IdentityAwareProxy(
    audience="https://example.com",
    impersonate_account="service-account@project-id.iam.gserviceaccount.com"
)
```

The `audience` parameter is required and should be the URL of the IAP-protected resource you want to access.

### Getting an IAP Token

```python
# Get an IAP token
token = iap.token
print(f"IAP Token: {token}")
```

The `token` property automatically handles token generation, either by:
1. Getting a token from the GCP metadata server (when running on GCP)
2. Getting a token using the service account credentials (when running outside GCP)

### Using IAP Headers

```python
# Get headers for IAP-protected requests
headers = iap.headers
print(f"IAP Headers: {headers}")

# Use the headers in a request
import requests

response = requests.get(
    url="https://example.com",
    headers=headers
)
print(f"Response: {response.text}")
```

The `headers` property returns a dictionary with the Authorization header set to "Bearer {token}".

## Example: Accessing an IAP-Protected Cloud Run Service

```python
from gcp_pilot.iap import IdentityAwareProxy
import requests

# Initialize IAP for a Cloud Run service
iap = IdentityAwareProxy(audience="https://my-service-abcdef-uc.a.run.app")

# Make a request to the IAP-protected service
response = requests.get(
    url="https://my-service-abcdef-uc.a.run.app",
    headers=iap.headers
)

# Process the response
if response.status_code == 200:
    print("Successfully accessed IAP-protected service")
    print(f"Response: {response.json()}")
else:
    print(f"Failed to access IAP-protected service: {response.status_code}")
    print(f"Error: {response.text}")
```

## Example: Accessing an IAP-Protected App Engine Service

```python
from gcp_pilot.iap import IdentityAwareProxy
import requests

# Initialize IAP for an App Engine service
iap = IdentityAwareProxy(audience="https://my-service-dot-my-project.appspot.com")

# Make a request to the IAP-protected service
response = requests.get(
    url="https://my-service-dot-my-project.appspot.com",
    headers=iap.headers
)

# Process the response
if response.status_code == 200:
    print("Successfully accessed IAP-protected service")
    print(f"Response: {response.json()}")
else:
    print(f"Failed to access IAP-protected service: {response.status_code}")
    print(f"Error: {response.text}")
```

## Example: Accessing an IAP-Protected Compute Engine Service

```python
from gcp_pilot.iap import IdentityAwareProxy
import requests

# Initialize IAP for a Compute Engine service
iap = IdentityAwareProxy(audience="https://my-vm-ip.region.c.my-project.internal")

# Make a request to the IAP-protected service
response = requests.get(
    url="https://my-vm-ip.region.c.my-project.internal",
    headers=iap.headers
)

# Process the response
if response.status_code == 200:
    print("Successfully accessed IAP-protected service")
    print(f"Response: {response.json()}")
else:
    print(f"Failed to access IAP-protected service: {response.status_code}")
    print(f"Error: {response.text}")
```

## Error Handling

The IAP class handles common errors and automatically falls back to alternative token generation methods:

```python
from gcp_pilot.iap import IdentityAwareProxy
import requests

try:
    # Initialize IAP
    iap = IdentityAwareProxy(audience="https://example.com")
    
    # Get a token
    token = iap.token
    
    # Make a request
    response = requests.get(
        url="https://example.com",
        headers=iap.headers
    )
    
    # Check for HTTP errors
    response.raise_for_status()
    
except requests.exceptions.ConnectionError:
    print("Failed to connect to the metadata server, falling back to service account credentials")
    
except requests.exceptions.HTTPError as e:
    print(f"HTTP error: {e}")
    
except Exception as e:
    print(f"Error: {e}")
```

## Working with Service Account Impersonation

Service account impersonation allows you to act as a service account without having its key file. This is a more secure approach than downloading and storing service account keys.

```python
# Initialize with service account impersonation
iap = IdentityAwareProxy(
    audience="https://example.com",
    impersonate_account="service-account@project-id.iam.gserviceaccount.com"
)

# Now all operations will be performed as the impersonated service account
token = iap.token
```

For more information on service account impersonation, see the [Authentication](../authentication.md) documentation.

## Setting Up IAP

Before you can use IAP, you need to set it up in the Google Cloud Console:

1. Enable the IAP API in your project
2. Configure IAP for your application (App Engine, Cloud Run, Compute Engine, etc.)
3. Set up the appropriate IAM permissions for the service account you're using

For more information on setting up IAP, see the [Google Cloud IAP documentation](https://cloud.google.com/iap/docs).