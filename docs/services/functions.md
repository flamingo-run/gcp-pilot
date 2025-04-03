# Cloud Functions

Cloud Functions is a serverless execution environment for building and connecting cloud services. The `CloudFunctions` class in gcp-pilot provides a high-level interface for interacting with Google Cloud Functions.

## Installation

To use the Cloud Functions functionality, you need to install gcp-pilot:

```bash
pip install gcp-pilot
```

## Usage

### Initialization

```python
from gcp_pilot.functions import CloudFunctions

# Initialize with default credentials
functions = CloudFunctions()

# Initialize with specific project
functions = CloudFunctions(project_id="my-project")

# Initialize with specific location
functions = CloudFunctions(location="us-central1")

# Initialize with service account impersonation
functions = CloudFunctions(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

### Listing Functions

```python
# List all functions in a project
functions_list = functions.get_functions()
for function in functions_list:
    print(f"Function: {function['name']}")

# List functions in a specific location
functions_list = functions.get_functions(location="us-central1")
for function in functions_list:
    print(f"Function: {function['name']}")

# List functions in a specific project
functions_list = functions.get_functions(project_id="my-project")
for function in functions_list:
    print(f"Function: {function['name']}")
```

### Getting a Function

```python
# Get information about a specific function
function = functions.get_function(
    name="my-function",
    location="us-central1",  # Optional: defaults to the default location
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Function: {function['name']}")
print(f"Description: {function['description']}")
print(f"Entry Point: {function['entryPoint']}")
print(f"Runtime: {function['runtime']}")
```

### Creating or Updating a Function

```python
# Create a new function
function = functions.create_or_update_function(
    name="my-function",
    description="My Cloud Function",
    entry_point="main",  # The name of the function to execute
    repo_name="my-repo",  # The name of the repository containing the function code
    runtime="python39",  # Optional: defaults to "python39"
    timeout=60,  # Optional: timeout in seconds, defaults to 60
    ram=128,  # Optional: memory in MB, defaults to 128
    repo_branch="main",  # Optional: the branch to use, defaults to "master"
    repo_tag=None,  # Optional: the tag to use
    repo_commit=None,  # Optional: the commit to use
    repo_directory=None,  # Optional: the directory containing the function code
    labels={"environment": "production"},  # Optional: labels to apply to the function
    env_vars={"DEBUG": "True"},  # Optional: environment variables for the function
    max_instances=10,  # Optional: maximum number of instances
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
    service_account_email="service-account@project-id.iam.gserviceaccount.com",  # Optional: service account to use
    is_public=False,  # Optional: if True, makes the function publicly accessible
)
print(f"Function created/updated: {function['name']}")

# Update an existing function
function = functions.create_or_update_function(
    name="my-function",
    description="Updated description",
    entry_point="main",
    repo_name="my-repo",
    runtime="python310",  # Updated runtime
    timeout=120,  # Updated timeout
    ram=256,  # Updated memory
    repo_branch="develop",  # Updated branch
    labels={"environment": "staging"},  # Updated labels
    env_vars={"DEBUG": "False"},  # Updated environment variables
    max_instances=5,  # Updated maximum instances
    is_public=True,  # Updated accessibility
)
print(f"Function updated: {function['name']}")
```

### Managing Function Permissions

```python
# Get the current permissions for a function
policy = functions.get_permissions(
    name="my-function",
    location="us-central1",  # Optional: defaults to the default location
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Policy: {policy}")

# Make a function publicly accessible
policy = functions.set_permissions(
    name="my-function",
    is_public=True,
    location="us-central1",  # Optional: defaults to the default location
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Updated policy: {policy}")

# Make a function private
policy = functions.set_permissions(
    name="my-function",
    is_public=False,
    location="us-central1",  # Optional: defaults to the default location
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Updated policy: {policy}")
```

### Deleting a Function

```python
# Delete a function
function = functions.delete_function(
    name="my-function",
    location="us-central1",  # Optional: defaults to the default location
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Function deleted: {function['name']}")
```

### Building Repository Sources

The `build_repo_source` method is a helper method for building the source repository configuration for a function. It's used internally by the `create_or_update_function` method, but you can also use it directly:

```python
# Build a repository source for a function
repo_source = CloudFunctions.build_repo_source(
    name="my-repo",
    branch="main",  # Optional: defaults to "master"
    tag=None,  # Optional: the tag to use
    commit=None,  # Optional: the commit to use
    directory="functions/my-function",  # Optional: the directory containing the function code
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Repository source URL: {repo_source['url']}")

# Build a repository source for a GitHub repository
repo_source = CloudFunctions.build_repo_source(
    name="organization/repo",  # GitHub repository in the format "organization/repo"
    branch="main",
    project_id="my-project",
)
print(f"Repository source URL: {repo_source['url']}")
```

## Error Handling

The CloudFunctions class handles common errors and converts them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    functions.get_function(name="non-existent-function")
except exceptions.NotFound:
    print("Function not found")

try:
    CloudFunctions.build_repo_source(name="my-repo", branch="main", tag="v1.0")
except exceptions.ValidationError:
    print("Only one of branch, tag, or commit can be provided")
```

## Working with GitHub Repositories

The CloudFunctions class supports working with GitHub repositories that are integrated with Google Cloud Source Repositories through the GitHub App:

```python
# Create a function using a GitHub repository
function = functions.create_or_update_function(
    name="my-function",
    description="Function from GitHub",
    entry_point="main",
    repo_name="organization/repo",  # GitHub repository in the format "organization/repo"
    repo_branch="main",
    repo_directory="functions/my-function",  # Optional: the directory containing the function code
)
print(f"Function created/updated: {function['name']}")
```

## Supported Runtimes

The CloudFunctions class supports various runtimes for Cloud Functions:

- `python37`: Python 3.7
- `python38`: Python 3.8
- `python39`: Python 3.9
- `python310`: Python 3.10
- `nodejs10`: Node.js 10
- `nodejs12`: Node.js 12
- `nodejs14`: Node.js 14
- `nodejs16`: Node.js 16
- `go113`: Go 1.13
- `go116`: Go 1.16
- `java11`: Java 11
- `dotnet3`: .NET Core 3.1
- `ruby27`: Ruby 2.7

You can specify the runtime when creating or updating a function:

```python
function = functions.create_or_update_function(
    name="my-function",
    description="My Cloud Function",
    entry_point="main",
    repo_name="my-repo",
    runtime="python310",  # Specify the runtime
)
```