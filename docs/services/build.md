# Cloud Build

Cloud Build is a service that executes your builds on Google Cloud Platform infrastructure. The `CloudBuild` class in gcp-pilot provides a high-level interface for interacting with Google Cloud Build, making it easy to create and manage build triggers, run builds, and subscribe to build notifications.

## Installation

To use the Cloud Build functionality, you need to install gcp-pilot with the build extra:

```bash
pip install gcp-pilot[build]
```

## Usage

### Initialization

```python
from gcp_pilot.build import CloudBuild

# Initialize with default credentials
build = CloudBuild()

# Initialize with specific project
build = CloudBuild(project_id="my-project")

# Initialize with service account impersonation
build = CloudBuild(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

### Creating Build Steps

Build steps define the actions that Cloud Build will execute during a build. Each step runs a Docker container.

```python
from gcp_pilot.build import CloudBuild
from google.cloud.devtools import cloudbuild_v1

build = CloudBuild()

# Create a simple build step
step = build.make_build_step(
    name="gcr.io/cloud-builders/docker",
    args=["build", "-t", "gcr.io/my-project/my-image", "."],
)

# Create a build step with an identifier
step = build.make_build_step(
    name="gcr.io/cloud-builders/docker",
    identifier="build-docker-image",
    args=["build", "-t", "gcr.io/my-project/my-image", "."],
)

# Create a build step with environment variables
step = build.make_build_step(
    name="gcr.io/cloud-builders/docker",
    args=["build", "-t", "gcr.io/my-project/my-image", "."],
    env=["ENV_VAR=value"],
)

# Create a build step with a custom entrypoint
step = build.make_build_step(
    name="gcr.io/cloud-builders/docker",
    args=["build", "-t", "gcr.io/my-project/my-image", "."],
    entrypoint="bash",
)

# Create a build step with a timeout
step = build.make_build_step(
    name="gcr.io/cloud-builders/docker",
    args=["build", "-t", "gcr.io/my-project/my-image", "."],
    timeout=300,  # 5 minutes
)
```

### Creating Source Repository Events

Source repository events define when a build trigger should run based on changes to a Cloud Source Repository.

```python
# Create a source repository event for the master branch
event = build.make_source_repo_event(
    repo_name="my-repo",
)

# Create a source repository event for a specific branch
event = build.make_source_repo_event(
    repo_name="my-repo",
    branch_name="develop",
)

# Create a source repository event for a specific tag
event = build.make_source_repo_event(
    repo_name="my-repo",
    tag_name="v1.0.0",
)

# Create a source repository event for a specific project
event = build.make_source_repo_event(
    repo_name="my-repo",
    branch_name="develop",
    project_id="my-project",
)
```

### Creating GitHub Events

GitHub events define when a build trigger should run based on changes to a GitHub repository.

```python
# Create a GitHub event for the master branch
event = build.make_github_event(
    url="https://github.com/owner/repo",
)

# Create a GitHub event for a specific branch
event = build.make_github_event(
    url="https://github.com/owner/repo",
    branch_name="develop",
)

# Create a GitHub event for a specific tag
event = build.make_github_event(
    url="https://github.com/owner/repo",
    tag_name="v1.0.0",
)
```

### Working with Substitutions

Substitutions allow you to parameterize your build configurations.

```python
from gcp_pilot.build import CloudBuild, Substitutions

# Create a substitutions object
substitutions = Substitutions()

# Add substitution variables
substitutions.add(
    image_name="my-image",
    tag="latest",
    env="production",
)

# Access substitution variables
print(substitutions.IMAGE_NAME)  # Outputs: ${_IMAGE_NAME}

# Use substitution variables in a build step
build = CloudBuild()
step = build.make_build_step(
    name="gcr.io/cloud-builders/docker",
    args=["build", "-t", f"gcr.io/my-project/{substitutions.IMAGE_NAME}:{substitutions.TAG}", "."],
)
```

### Creating Build Triggers

Build triggers automatically start a build when changes are pushed to a repository.

```python
# Create a build trigger for a Cloud Source Repository
trigger = build.create_trigger(
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
    timeout=600,  # 10 minutes
    machine_type=cloudbuild_v1.BuildOptions.MachineType.N1_HIGHCPU_8,
)

# Create a build trigger for a GitHub repository
trigger = build.create_trigger(
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

### Updating Build Triggers

```python
# Update an existing build trigger
trigger = build.update_trigger(
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

### Creating or Updating Build Triggers

```python
# Create a trigger if it doesn't exist, or update it if it does
trigger = build.create_or_update_trigger(
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

### Getting and Deleting Build Triggers

```python
# Get a build trigger
trigger = build.get_trigger(
    trigger_id="my-trigger",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)

# Delete a build trigger
build.delete_trigger(
    trigger_id="my-trigger",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
```

### Running Build Triggers

```python
# Run a build trigger for a specific branch
build.run_trigger(
    name="my-trigger",
    branch_name="master",
)

# Run a build trigger for a specific tag
build.run_trigger(
    name="my-trigger",
    tag_name="v1.0.0",
)

# Run a build trigger for a specific commit
build.run_trigger(
    name="my-trigger",
    commit_sha="abc123",
)
```

### Getting Builds

```python
# Get all builds
for build_obj in build.get_builds():
    print(f"Build: {build_obj.id}")

# Get builds for a specific trigger
for build_obj in build.get_builds(trigger_id="my-trigger"):
    print(f"Build: {build_obj.id}")

# Get builds with a specific status
for build_obj in build.get_builds(status="SUCCESS"):
    print(f"Build: {build_obj.id}")
```

### Subscribing to Build Notifications

Cloud Build can publish build status notifications to Pub/Sub. gcp-pilot makes it easy to subscribe to these notifications.

```python
# Subscribe to build notifications
build.subscribe(
    subscription_id="my-build-notifications",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)

# Subscribe to build notifications with a push endpoint
build.subscribe(
    subscription_id="my-build-notifications",
    push_to_url="https://example.com/build-webhook",
    use_oidc_auth=True,  # Use OIDC authentication for the push endpoint
)
```

Note: To use the `subscribe` method, you need to install gcp-pilot with the pubsub extra:

```bash
pip install gcp-pilot[build,pubsub]
```

## Error Handling

The CloudBuild class handles common errors and converts them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    build.create_trigger(name="existing-trigger", ...)
except exceptions.AlreadyExists:
    print("Trigger already exists")
```