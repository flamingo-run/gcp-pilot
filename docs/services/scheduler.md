# Cloud Scheduler

Cloud Scheduler is a fully managed enterprise-grade cron job scheduler. The `CloudScheduler` class in gcp-pilot provides a high-level interface for interacting with Google Cloud Scheduler.

## Installation

To use the Cloud Scheduler functionality, you need to install gcp-pilot:

```bash
pip install gcp-pilot
```

## Usage

### Initialization

```python
from gcp_pilot.scheduler import CloudScheduler

# Initialize with default credentials
scheduler = CloudScheduler()

# Initialize with specific project
scheduler = CloudScheduler(project_id="my-project")

# Initialize with specific location
scheduler = CloudScheduler(location="us-central1")

# Initialize with specific timezone
scheduler = CloudScheduler(timezone="America/New_York")

# Initialize with service account impersonation
scheduler = CloudScheduler(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

### Creating Jobs

```python
from google.cloud import scheduler

# Create a new Cloud Scheduler job
job = scheduler.create(
    name="my-job",  # The name of the job
    url="https://example.com/api/endpoint",  # The URL to call
    payload="Hello, world!",  # The payload to send
    cron="0 * * * *",  # The cron schedule (every hour in this example)
    timezone="America/New_York",  # Optional: the timezone for the schedule, defaults to UTC
    method=scheduler.HttpMethod.POST,  # Optional: the HTTP method, defaults to POST
    headers={"Content-Type": "application/json"},  # Optional: HTTP headers
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    use_oidc_auth=True,  # Optional: if True, uses OIDC authentication for the request
    timeout_in_seconds=600,  # Optional: request timeout in seconds, defaults to 30 minutes
    retry_count=3,  # Optional: number of retry attempts, defaults to 0
)
print(f"Job created: {job.name}")
print(f"Schedule: {job.schedule}")
print(f"Time Zone: {job.time_zone}")
print(f"URL: {job.http_target.uri}")
```

### Updating Jobs

```python
# Update an existing Cloud Scheduler job
job = scheduler.update(
    name="my-job",  # The name of the job
    url="https://example.com/api/new-endpoint",  # The new URL to call
    payload="Updated payload",  # The new payload to send
    cron="0 */2 * * *",  # The new cron schedule (every 2 hours in this example)
    timezone="America/Los_Angeles",  # Optional: the new timezone for the schedule
    method=scheduler.HttpMethod.PUT,  # Optional: the new HTTP method
    headers={"Content-Type": "application/json", "X-Custom-Header": "value"},  # Optional: new HTTP headers
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    use_oidc_auth=True,  # Optional: if True, uses OIDC authentication for the request
    timeout_in_seconds=300,  # Optional: new request timeout in seconds
    retry_count=5,  # Optional: new number of retry attempts
)
print(f"Job updated: {job.name}")
print(f"New Schedule: {job.schedule}")
print(f"New Time Zone: {job.time_zone}")
print(f"New URL: {job.http_target.uri}")
```

### Creating or Updating Jobs

```python
# Create a new job or update an existing one
job = scheduler.put(
    name="my-job",  # The name of the job
    url="https://example.com/api/endpoint",  # The URL to call
    payload="Hello, world!",  # The payload to send
    cron="0 * * * *",  # The cron schedule (every hour in this example)
    timezone="America/New_York",  # Optional: the timezone for the schedule, defaults to UTC
    method=scheduler.HttpMethod.POST,  # Optional: the HTTP method, defaults to POST
    headers={"Content-Type": "application/json"},  # Optional: HTTP headers
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    use_oidc_auth=True,  # Optional: if True, uses OIDC authentication for the request
    timeout_in_seconds=600,  # Optional: request timeout in seconds, defaults to 30 minutes
    retry_count=3,  # Optional: number of retry attempts, defaults to 0
)
print(f"Job created or updated: {job.name}")
```

### Listing Jobs

```python
# List all jobs in a project
jobs = scheduler.list(
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
for job in jobs:
    print(f"Job: {job.name}")
    print(f"Schedule: {job.schedule}")
    print(f"Time Zone: {job.time_zone}")
    print(f"URL: {job.http_target.uri}")

# List jobs with a specific prefix
jobs = scheduler.list(
    prefix="backup-",  # Only list jobs with names starting with "backup-"
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
for job in jobs:
    print(f"Job: {job.name}")
```

### Getting a Job

```python
# Get information about a specific job
job = scheduler.get(
    name="my-job",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Job: {job.name}")
print(f"Schedule: {job.schedule}")
print(f"Time Zone: {job.time_zone}")
print(f"URL: {job.http_target.uri}")
print(f"HTTP Method: {job.http_target.http_method}")
print(f"Payload: {job.http_target.body.decode()}")
print(f"Headers: {job.http_target.headers}")
print(f"Retry Count: {job.retry_config.retry_count}")
```

### Deleting a Job

```python
# Delete a job
scheduler.delete(
    name="my-job",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
```

## Cron Syntax

Cloud Scheduler uses a standard cron syntax with five fields:

```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of the month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of the week (0 - 6) (Sunday to Saturday)
│ │ │ │ │
│ │ │ │ │
* * * * *
```

Here are some examples:

- `0 * * * *`: Run at the beginning of every hour
- `0 0 * * *`: Run at midnight every day
- `0 0 * * 0`: Run at midnight every Sunday
- `0 0 1 * *`: Run at midnight on the first day of every month
- `0 0 1 1 *`: Run at midnight on January 1st
- `*/5 * * * *`: Run every 5 minutes
- `0 9-17 * * 1-5`: Run every hour from 9 AM to 5 PM, Monday to Friday

## Error Handling

The CloudScheduler class handles common errors and converts them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    scheduler.get(name="non-existent-job")
except exceptions.NotFound:
    print("Job not found")

try:
    scheduler.update(
        name="non-existent-job",
        url="https://example.com",
        payload="Hello, world!",
        cron="0 * * * *"
    )
except exceptions.NotFound:
    print("Job not found, creating instead")
    scheduler.create(
        name="non-existent-job",
        url="https://example.com",
        payload="Hello, world!",
        cron="0 * * * *"
    )
```

## Working with Service Account Impersonation

Service account impersonation allows you to act as a service account without having its key file. This is a more secure approach than downloading and storing service account keys.

```python
# Initialize with service account impersonation
scheduler = CloudScheduler(impersonate_account="service-account@project-id.iam.gserviceaccount.com")

# Now all operations will be performed as the impersonated service account
jobs = scheduler.list()
```

For more information on service account impersonation, see the [Authentication](../authentication.md) documentation.

## Best Practices

Here are some best practices for working with Cloud Scheduler:

1. **Use descriptive job names**: Choose job names that clearly indicate their purpose and function.
2. **Set appropriate retry policies**: Configure retry counts based on the criticality of the job and the reliability of the target endpoint.
3. **Use OIDC authentication**: Enable OIDC authentication for secure communication with your endpoints.
4. **Monitor job execution**: Set up monitoring and alerting for job failures.
5. **Choose appropriate schedules**: Avoid scheduling too many jobs at the same time to prevent resource contention.
6. **Set reasonable timeouts**: Configure timeouts based on the expected execution time of your job.
7. **Use appropriate time zones**: Set the time zone to match your business operations to make schedules more intuitive.