# Resource Manager

Resource Manager is a service that allows you to programmatically manage your Google Cloud resources. The `ResourceManager` and `ServiceAgent` classes in gcp-pilot provide high-level interfaces for interacting with Google Cloud Resource Manager.

## Installation

To use the Resource Manager functionality, you need to install gcp-pilot:

```bash
pip install gcp-pilot
```

## Usage

### ResourceManager

The `ResourceManager` class allows you to manage IAM policies and project information.

#### Initialization

```python
from gcp_pilot.resource import ResourceManager

# Initialize with default credentials
resource_manager = ResourceManager()

# Initialize with specific project
resource_manager = ResourceManager(project_id="my-project")

# Initialize with service account impersonation
resource_manager = ResourceManager(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

#### Managing IAM Policies

```python
# Get the IAM policy for a project
policy = resource_manager.get_policy(
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    version=1,  # Optional: the policy version to request
)
print(f"Policy: {policy}")

# Add a member to a role
policy = resource_manager.add_member(
    email="user@example.com",
    role="roles/viewer",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Updated policy: {policy}")

# Remove a member from a role
policy = resource_manager.remove_member(
    email="user@example.com",
    role="roles/viewer",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Updated policy: {policy}")

# Set a custom policy
policy = resource_manager.set_policy(
    policy=custom_policy,  # A policy object
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Updated policy: {policy}")

# Allow a service account to impersonate another service account
policy = resource_manager.allow_impersonation(
    email="service-account@project-id.iam.gserviceaccount.com",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Updated policy: {policy}")
```

#### Getting Project Information

```python
# Get information about a project
project = resource_manager.get_project(
    project_id="my-project",
)
print(f"Project: {project['name']}")
print(f"Project Number: {project['projectNumber']}")
print(f"Project ID: {project['projectId']}")
print(f"Lifecycle State: {project['lifecycleState']}")
```

### ServiceAgent

The `ServiceAgent` class provides utilities for working with Google Cloud service agents.

#### Getting Service Agent Information

```python
from gcp_pilot.resource import ServiceAgent

# Get a list of available service agents
available_agents = ServiceAgent.get_available_agents()
for agent in available_agents:
    print(f"Service Agent: {agent}")

# Get the email address of a service agent
email = ServiceAgent.get_email(
    service_name="Cloud Run",
    project_id="my-project",
)
print(f"Service Agent Email: {email}")

# Get the role of a service agent
role = ServiceAgent.get_role(
    service_name="Cloud Run",
)
print(f"Service Agent Role: {role}")

# Get the project number
project_number = ServiceAgent.get_project_number(
    project_id="my-project",
)
print(f"Project Number: {project_number}")
```

#### Getting Specific Service Accounts

```python
# Get the Compute Engine service account
compute_sa = ServiceAgent.get_compute_service_account(
    project_id="my-project",
)
print(f"Compute Service Account: {compute_sa}")

# Get the Cloud Build service account
build_sa = ServiceAgent.get_cloud_build_service_account(
    project_id="my-project",
)
print(f"Cloud Build Service Account: {build_sa}")
```

#### Restoring Service Agent Permissions

```python
# Restore permissions for multiple service agents
ServiceAgent.restore(
    services=["Cloud Run", "Cloud Build", "Cloud Functions"],
    project_id="my-project",
)
```

## Error Handling

The Resource Manager classes handle common errors and convert them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    resource_manager = ResourceManager()
    resource_manager.set_policy(policy={"bindings": []})
except exceptions.NotAllowed:
    print("Too dangerous to set policy with empty bindings")

try:
    ServiceAgent.get_email(service_name="Non-existent Service", project_id="my-project")
except exceptions.NotFound:
    print("Service not found")
```

## Working with Service Account Impersonation

Service account impersonation allows you to act as a service account without having its key file. This is a more secure approach than downloading and storing service account keys.

```python
# Initialize with service account impersonation
resource_manager = ResourceManager(impersonate_account="service-account@project-id.iam.gserviceaccount.com")

# Now all operations will be performed as the impersonated service account
policy = resource_manager.get_policy()
```

For more information on service account impersonation, see the [Authentication](../authentication.md) documentation.

## Common IAM Roles

Here are some common IAM roles that you might use with Resource Manager:

- `roles/viewer`: Read-only access to view resources
- `roles/editor`: Read-write access to manage resources
- `roles/owner`: Full access to manage resources and grant permissions
- `roles/resourcemanager.projectCreator`: Create new projects
- `roles/resourcemanager.projectDeleter`: Delete projects
- `roles/resourcemanager.projectIamAdmin`: Manage IAM policies on projects

You can use these roles when adding members to a project:

```python
# Grant the viewer role to a user
policy = resource_manager.add_member(
    email="user@example.com",
    role="roles/viewer",
)
```

## Service Agents

Google Cloud uses service agents to perform operations on your behalf. These are special service accounts that are automatically created and managed by Google. The `ServiceAgent` class provides a comprehensive list of service agents and their roles.

Here are some examples of service agents:

- Cloud Run Service Agent: `service-{project-number}@serverless-robot-prod.iam.gserviceaccount.com`
- Cloud Build Service Agent: `service-{project-number}@gcp-sa-cloudbuild.iam.gserviceaccount.com`
- Cloud Functions Service Agent: `service-{project-number}@gcf-admin-robot.iam.gserviceaccount.com`
- Compute Engine Service Agent: `service-{project-number}@compute-system.iam.gserviceaccount.com`

You can get the email address of a service agent using the `get_email` method:

```python
email = ServiceAgent.get_email(
    service_name="Cloud Run",
    project_id="my-project",
)
print(f"Service Agent Email: {email}")
```

And you can get the role of a service agent using the `get_role` method:

```python
role = ServiceAgent.get_role(
    service_name="Cloud Run",
)
print(f"Service Agent Role: {role}")
```

If a service agent's permissions are removed, you can restore them using the `restore` method:

```python
ServiceAgent.restore(
    services=["Cloud Run"],
    project_id="my-project",
)
```