# Cloud Build

Cloud Build is a service that executes your builds on Google Cloud Platform infrastructure. The `CloudBuild` class in gcp-pilot provides a high-level interface for interacting with Google Cloud Build, making it easy to create and manage build triggers, run builds, and subscribe to build notifications.

## Installation

To use the Cloud Build functionality, you need to install gcp-pilot with the build extra:

```bash
pip install gcp-pilot[build]
```

## Usage

### Initialization

```python title="Initialize CloudBuild Client"
from gcp_pilot.build import CloudBuild

build = CloudBuild() # (1)!
build = CloudBuild(project_id="my-project") # (2)!
build = CloudBuild(impersonate_account="service-account@project-id.iam.gserviceaccount.com") # (3)!
```

1.  Initialize with default credentials
2.  Initialize with specific project
3.  Initialize with service account impersonation

### Creating Build Steps

Build steps define the actions that Cloud Build will execute during a build. Each step runs a Docker container.

```python title="Create Build Steps"
from gcp_pilot.build import CloudBuild
from google.cloud.devtools import cloudbuild_v1

build = CloudBuild()

step = build.make_build_step( # (1)!
    name="gcr.io/cloud-builders/docker",
    args=["build", "-t", "gcr.io/my-project/my-image", "."],
)

step = build.make_build_step( # (2)!
    name="gcr.io/cloud-builders/docker",
    identifier="build-docker-image",
    args=["build", "-t", "gcr.io/my-project/my-image", "."],
)

step = build.make_build_step( # (3)!
    name="gcr.io/cloud-builders/docker",
    args=["build", "-t", "gcr.io/my-project/my-image", "."],
    env=["ENV_VAR=value"],
)

step = build.make_build_step( # (4)!
    name="gcr.io/cloud-builders/docker",
    args=["build", "-t", "gcr.io/my-project/my-image", "."],
    entrypoint="bash",
)

step = build.make_build_step( # (5)!
    name="gcr.io/cloud-builders/docker",
    args=["build", "-t", "gcr.io/my-project/my-image", "."],
    timeout=300,  # (6)!
)
```

1.  Create a simple build step
2.  Create a build step with an identifier
3.  Create a build step with environment variables
4.  Create a build step with a custom entrypoint
5.  Create a build step with a timeout
6.  5 minutes

### Creating Source Repository Events

Source repository events define when a build trigger should run based on changes to a Cloud Source Repository.

```python title="Create Source Repository Events"
event = build.make_source_repo_event( # (1)!
    repo_name="my-repo",
)

event = build.make_source_repo_event( # (2)!
    repo_name="my-repo",
    branch_name="develop",
)

event = build.make_source_repo_event( # (3)!
    repo_name="my-repo",
    tag_name="v1.0.0",
)

event = build.make_source_repo_event( # (4)!
    repo_name="my-repo",
    branch_name="develop",
    project_id="my-project",
)
```

1.  Create a source repository event for the master branch
2.  Create a source repository event for a specific branch
3.  Create a source repository event for a specific tag
4.  Create a source repository event for a specific project

### Creating GitHub Events

GitHub events define when a build trigger should run based on changes to a GitHub repository.

```python title="Create GitHub Events"
event = build.make_github_event( # (1)!
    url="https://github.com/owner/repo",
)

event = build.make_github_event( # (2)!
    url="https://github.com/owner/repo",
    branch_name="develop",
)

event = build.make_github_event( # (3)!
    url="https://github.com/owner/repo",
    tag_name="v1.0.0",
)
```

1.  Create a GitHub event for the master branch
2.  Create a GitHub event for a specific branch
3.  Create a GitHub event for a specific tag

### Working with Substitutions

Substitutions allow you to parameterize your build configurations.

```python title="Work with Substitutions"
from gcp_pilot.build import CloudBuild, Substitutions

substitutions = Substitutions() # (1)!

substitutions.add( # (2)!
    image_name="my-image",
    tag="latest",
    env="production",
)

print(substitutions.IMAGE_NAME)  # (3)!

build = CloudBuild()
step = build.make_build_step( # (4)!
    name="gcr.io/cloud-builders/docker",
    args=["build", "-t", f"gcr.io/my-project/{substitutions.IMAGE_NAME}:{substitutions.TAG}", "."],
)
```

1.  Create a substitutions object
2.  Add substitution variables
3.  Access substitution variables (Outputs: ${_IMAGE_NAME})
4.  Use substitution variables in a build step

### Creating Build Triggers

Build triggers automatically start a build when changes are pushed to a repository.

```python title="Create Build Triggers"
trigger = build.create_trigger( # (1)!
    name="my-trigger",
    description="Build and deploy on push to master",
    event=build.make_source_repo_event(repo_name="my-repo"),
    steps=[
        build.make_build_step(
            name="gcr.io/cloud-builders/docker",
            args=["build", "-t", "gcr.io/my-project/my-image", "."],
        ),
    ],
    tags=["deploy", "production"],
    images=["gcr.io/my-project/my-image"],
    substitutions=substitutions,
    timeout=600,  # (2)!
    machine_type=cloudbuild_v1.BuildOptions.MachineType.N1_HIGHCPU_8,
)

trigger = build.create_trigger( # (3)!
    name="my-github-trigger",
    description="Build and deploy on push to master",
    event=build.make_github_event(url="https://github.com/owner/repo"),
    steps=[
        build.make_build_step(
            name="gcr.io/cloud-builders/docker",
            args=["build", "-t", "gcr.io/my-project/my-image", "."],
        ),
    ],
    tags=["deploy", "production"],
)
```

1.  Create a build trigger for a Cloud Source Repository
2.  10 minutes
3.  Create a build trigger for a GitHub repository

### Updating Build Triggers

```python title="Update a Build Trigger"
trigger = build.update_trigger( # (1)!
    name="my-trigger",
    description="Updated description",
    event=build.make_source_repo_event(repo_name="my-repo"),
    steps=[
        build.make_build_step(
            name="gcr.io/cloud-builders/docker",
            args=["build", "-t", "gcr.io/my-project/my-image:v2", "."],
        ),
    ],
    tags=["deploy", "production"],
)
```

1.  Update an existing build trigger

### Creating or Updating Build Triggers

```python title="Create or Update a Build Trigger"
trigger = build.create_or_update_trigger( # (1)!
    name="my-trigger",
    description="Build and deploy on push to master",
    event=build.make_source_repo_event(repo_name="my-repo"),
    steps=[
        build.make_build_step(
            name="gcr.io/cloud-builders/docker",
            args=["build", "-t", "gcr.io/my-project/my-image", "."],
        ),
    ],
    tags=["deploy", "production"],
)
```

1.  Create a trigger if it doesn't exist, or update it if it does

### Getting and Deleting Build Triggers

```python title="Get and Delete Build Triggers"
trigger = build.get_trigger( # (1)!
    trigger_id="my-trigger",
    project_id="my-project",  # (2)!
)

build.delete_trigger( # (3)!
    trigger_id="my-trigger",
    project_id="my-project",  # (4)!
)
```

1.  Get a build trigger
2.  Optional: defaults to the project associated with credentials
3.  Delete a build trigger
4.  Optional: defaults to the project associated with credentials

### Running Build Triggers

```python title="Run a Build Trigger"
build.run_trigger( # (1)!
    trigger_id="my-trigger",
    branch_name="feature-branch",  # (2)!
    project_id="my-project",  # (3)!
)
```

1.  Run a build trigger for a specific branch
2.  Optional: defaults to the default branch of the trigger
3.  Optional: defaults to the project associated with credentials

### Managing Builds

#### Listing Builds

```python title="List Builds"
builds = build.list_builds( # (1)!
    project_id="my-project",  # (2)!
    limit=10,  # (3)!
    query="status=\"SUCCESS\"",  # (4)!
)
for b in builds:
    print(f"Build ID: {b.id}, Status: {b.status}")
```

1.  List builds in a project
2.  Optional: defaults to the project associated with credentials
3.  Optional: maximum number of builds to return
4.  Optional: filter builds using a query string

#### Getting a Build

```python title="Get a Build"
build_info = build.get_build( # (1)!
    build_id="build-id",
    project_id="my-project",  # (2)!
)
print(f"Build ID: {build_info.id}, Status: {build_info.status}")
```

1.  Get information about a specific build
2.  Optional: defaults to the project associated with credentials

#### Approving a Build

```python title="Approve a Build"
build.approve_build( # (1)!
    build_id="build-id",
    project_id="my-project",  # (2)!
)
```

1.  Approve a pending build
2.  Optional: defaults to the project associated with credentials

#### Canceling a Build

```python title="Cancel a Build"
build.cancel_build( # (1)!
    build_id="build-id",
    project_id="my-project",  # (2)!
)
```

1.  Cancel a running build
2.  Optional: defaults to the project associated with credentials

#### Retrying a Build

```python title="Retry a Build"
build.retry_build( # (1)!
    build_id="build-id",
    project_id="my-project",  # (2)!
)
```

1.  Retry a failed build
2.  Optional: defaults to the project associated with credentials

## Subscribing to Build Notifications

Cloud Build can publish build status notifications to Pub/Sub. gcp-pilot makes it easy to subscribe to these notifications.

```python title="Subscribe to Build Notifications"
from gcp_pilot.build import CloudBuild
from gcp_pilot.pubsub import PubSub

build = CloudBuild()

# Create a Pub/Sub topic for build notifications (1)!
build.enable_build_notifications(topic_name="my-build-notifications")

# Subscribe to the topic and process messages (2)!
subscriber = PubSub()
subscription = subscriber.subscribe(
    topic_name="my-build-notifications",
    subscription_name="my-build-subscription",
    ack_deadline=60,  # (3)!
)

def callback(message):
    print(f"Received build notification: {message.data}")
    message.ack()

subscriber.pull(subscription_name=subscription.name, callback=callback) # (4)!
```

1.  Ensure a Pub/Sub topic exists for build notifications
2.  Subscribe to the topic
3.  Optional: acknowledgement deadline in seconds
4.  Start pulling messages (this is a blocking call)

## Working with Service Account Impersonation

Service account impersonation allows you to act as a service account without having its key file. This is a more secure approach than downloading and storing service account keys.

```python title="Using Impersonated Credentials for Cloud Build"
build = CloudBuild(impersonate_account="service-account@project-id.iam.gserviceaccount.com") # (1)!
builds = build.list_builds() # (2)!
```

1.  Initialize with service account impersonation
2.  Now all operations will be performed as the impersonated service account

For more information on service account impersonation, see the [Authentication](../authentication.md) documentation.

!!! warning "Permissions"

## Error Handling

The CloudBuild class handles common errors and converts them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    build.create_trigger(name="existing-trigger", ...)
except exceptions.AlreadyExists:
    print("Trigger already exists")
```