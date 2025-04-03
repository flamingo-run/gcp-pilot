# Cloud Tasks

Cloud Tasks is a fully managed service that allows you to manage the execution, dispatch, and delivery of a large number of distributed tasks. The `CloudTasks` class in gcp-pilot provides a high-level interface for interacting with Google Cloud Tasks.

## Installation

To use the Cloud Tasks functionality, you need to install gcp-pilot with the tasks extra:

```bash
pip install gcp-pilot[tasks]
```

## Usage

### Initialization

```python
from gcp_pilot.tasks import CloudTasks

# Initialize with default credentials
tasks = CloudTasks()

# Initialize with specific project and location
tasks = CloudTasks(project_id="my-project", location="us-central1")

# Initialize with service account impersonation
tasks = CloudTasks(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

### Pushing Tasks to a Queue

The `push` method is the primary way to add tasks to a queue:

```python
# Push a simple task to a queue
task = tasks.push(
    queue_name="my-queue",
    url="https://example.com/task-handler",
    payload="Hello, World!",
)

# Push a task with custom HTTP method
from google.cloud import tasks_v2

task = tasks.push(
    queue_name="my-queue",
    url="https://example.com/task-handler",
    payload="Hello, World!",
    method=tasks_v2.HttpMethod.GET,
)

# Push a task with a delay
task = tasks.push(
    queue_name="my-queue",
    url="https://example.com/task-handler",
    payload="Hello, World!",
    delay_in_seconds=300,  # 5 minutes
)

# Push a task with a custom name
task = tasks.push(
    queue_name="my-queue",
    url="https://example.com/task-handler",
    payload="Hello, World!",
    task_name="my-custom-task",
    unique=True,  # Appends a UUID to the task name to ensure uniqueness
)

# Push a task with custom headers
task = tasks.push(
    queue_name="my-queue",
    url="https://example.com/task-handler",
    payload="Hello, World!",
    headers={"X-Custom-Header": "value"},
    content_type="application/json",
)

# Push a task with a custom timeout
from datetime import timedelta

task = tasks.push(
    queue_name="my-queue",
    url="https://example.com/task-handler",
    payload="Hello, World!",
    task_timeout=timedelta(minutes=10),
)

# Push a task without OIDC authentication
task = tasks.push(
    queue_name="my-queue",
    url="https://example.com/task-handler",
    payload="Hello, World!",
    use_oidc_auth=False,
)
```

If the specified queue doesn't exist, gcp-pilot will automatically create it for you.

### Creating a Queue

```python
# Create a queue
queue = tasks.create_queue(
    queue_name="my-queue",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
```

### Getting a Queue

```python
# Get information about a queue
queue = tasks.get_queue(
    queue_name="my-queue",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
```

### Getting a Task

```python
# Get information about a task
task = tasks.get_task(
    queue_name="my-queue",
    task_name="my-task",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
```

### Deleting a Task

```python
# Delete a task
tasks.delete_task(
    queue_name="my-queue",
    task_name="my-task",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    not_found_ok=True,  # Optional: if True, doesn't raise an error if the task doesn't exist
)
```

### Listing Tasks in a Queue

```python
# List all tasks in a queue
for task in tasks.list_tasks(
    queue_name="my-queue",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
):
    print(f"Task: {task.name}")
```

## Auto-Authorization

One of the key features of gcp-pilot's Cloud Tasks implementation is automatic OIDC authorization. When you push a task to a queue with `use_oidc_auth=True` (the default), gcp-pilot automatically generates an OIDC token for the task. This allows the task to authenticate with the target service, which is especially useful when the target service is a Cloud Run service or another service that requires authentication.

## Error Handling

The CloudTasks class handles common errors and converts them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    tasks.push(queue_name="recently-deleted-queue", url="https://example.com")
except exceptions.DeletedRecently:
    print("Queue was recently deleted and cannot be recreated yet")
```

## Working with App Engine

Since CloudTasks inherits from AppEngineBasedService, it's designed to work seamlessly with App Engine. It automatically detects the App Engine location and uses it as the default location for Cloud Tasks operations.