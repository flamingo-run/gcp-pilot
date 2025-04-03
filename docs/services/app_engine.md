# App Engine

App Engine is a fully managed, serverless platform for developing and hosting web applications at scale. The `AppEngine` class in gcp-pilot provides a high-level interface for interacting with Google Cloud App Engine.

## Installation

To use the App Engine functionality, you need to install gcp-pilot:

```bash
pip install gcp-pilot
```

## Usage

### Initialization

```python
from gcp_pilot.app_engine import AppEngine

# Initialize with default credentials
app_engine = AppEngine()

# Initialize with specific project
app_engine = AppEngine(project_id="my-project")

# Initialize with specific location
app_engine = AppEngine(location="us-central1")

# Initialize with service account impersonation
app_engine = AppEngine(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

### Getting App Information

```python
# Get information about the current project's App Engine application
app = app_engine.get_app()
print(f"App ID: {app['id']}")
print(f"Location: {app['locationId']}")

# Get information about a specific App Engine application
app = app_engine.get_app(app_id="my-project")
print(f"App ID: {app['id']}")
print(f"Location: {app['locationId']}")
```

## AppEngineBasedService

The `AppEngine` class inherits from `AppEngineBasedService`, which is a base class used by other services that rely on App Engine, such as Cloud Tasks. This base class provides functionality for determining the default location of an App Engine application, which is useful for services that need to be deployed in the same location as the App Engine application.

```python
from gcp_pilot.tasks import CloudTasks

# CloudTasks inherits from AppEngineBasedService
tasks = CloudTasks()

# The location will be automatically set to the App Engine application's location
print(f"Location: {tasks.location}")
```

## Error Handling

The AppEngine class handles common errors and converts them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    app_engine.get_app(app_id="non-existent-project")
except exceptions.NotFound:
    print("App Engine application not found")
```