# Testing Utilities

The `mocker` module in gcp-pilot provides utilities for mocking Google Cloud Platform services during testing. This is particularly useful for unit testing applications that use gcp-pilot without needing to connect to actual GCP services.

## Installation

To use the mocker functionality, you need to install gcp-pilot:

```bash title="Install gcp-pilot"
pip install gcp-pilot
```

## Usage

### Mocking Authentication

The `patch_auth` class provides a context manager and decorator for mocking Google Cloud authentication:

```python title="Mock Authentication with patch_auth"
from gcp_pilot.mocker import patch_auth

# As a context manager
with patch_auth(project_id="test-project", location="us-central1", email="test@example.com"):
    # Code that uses gcp-pilot services
    # Authentication will be mocked
    
# As a decorator
@patch_auth(project_id="test-project", location="us-central1")
def test_function():
    # Code that uses gcp-pilot services
    # Authentication will be mocked
```

#### Parameters

- `project_id` (str, optional): The project ID to use in the mock. Defaults to "potato-dev".
- `location` (str, optional): The location to use in the mock. Defaults to "moon-dark1".
- `email` (str, optional): The service account email to use in the mock. Defaults to "chuck@norris.com".

### Mocking Firebase Token Verification

The `patch_firebase_token` function provides a way to mock Firebase token verification:

```python title="Mock Firebase Token Verification"
from gcp_pilot.mocker import patch_firebase_token
import unittest.mock

with patch_firebase_token(return_value={"user_id": "test-user"}): # (1)!
    # Code that verifies Firebase tokens
    # Verification will be mocked and return the specified value
```

1.  Mock Firebase token verification

## Example: Unit Testing with Mocks

Here's an example of how to use the mocker utilities in a unit test:

```python title="Unit Test Example with Mocks"
import unittest
from gcp_pilot.mocker import patch_auth
from gcp_pilot.storage import Storage

class TestStorage(unittest.TestCase):
    @patch_auth(project_id="test-project")
    def test_list_buckets(self):
        storage = Storage() # (1)!
        
        with unittest.mock.patch.object(storage.client.buckets, 'list',  # (2)!
                                       return_value=[{'name': 'test-bucket'}]):
            buckets = list(storage.list_buckets())
            self.assertEqual(len(buckets), 1)
            self.assertEqual(buckets[0]['name'], 'test-bucket')
```

1.  This test doesn't actually connect to GCP
2.  Mock the list_buckets method to return test data

## Advanced Usage: Manual Control

If you need more control over when the mocks start and stop:

```python title="Manual Control of Mocks"
from gcp_pilot.mocker import patch_auth

# Create the mock
auth_mock = patch_auth(project_id="test-project")

# Start the mock
auth_mock.start()

try:
    # Code that uses gcp-pilot services
    # Authentication will be mocked
finally:
    # Stop the mock
    auth_mock.stop()
```

!!! warning "Important Notes on Mocking"
    - The mocks provided by this module are designed for testing purposes only and should not be used in production code.
    - While these mocks prevent actual API calls to GCP, they don't provide mock responses for service-specific methods. You'll need to combine them with additional mocks (e.g., using `unittest.mock`) to fully mock GCP service interactions.
    - The authentication mock provides a real `Credentials` object, but with minimal attributes, so it will pass type checks but fail if actually used to make API calls.