# Source Repositories

Source Repositories is a service that provides Git version control to support collaborative development of any application or service. The `SourceRepository` class in gcp-pilot provides a high-level interface for interacting with Google Cloud Source Repositories.

## Installation

To use the Source Repositories functionality, you need to install gcp-pilot:

```bash
pip install gcp-pilot
```

## Usage

### Initialization

```python
from gcp_pilot.source import SourceRepository

# Initialize with default credentials
source_repo = SourceRepository()

# Initialize with specific project
source_repo = SourceRepository(project_id="my-project")

# Initialize with service account impersonation
source_repo = SourceRepository(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

### Listing Repositories

```python
# List all repositories in a project
repos = source_repo.list_repos(
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
for repo in repos:
    print(f"Repository: {repo['name']}")
    print(f"URL: {repo['url']}")
    print(f"Size: {repo.get('size', 'Unknown')}")
```

### Getting a Repository

```python
# Get information about a specific repository
repo = source_repo.get_repo(
    repo_name="my-repo",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Repository: {repo['name']}")
print(f"URL: {repo['url']}")
print(f"Size: {repo.get('size', 'Unknown')}")
```

### Creating a Repository

```python
# Create a new repository
repo = source_repo.create_repo(
    repo_name="my-new-repo",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    exists_ok=True,  # Optional: if True, returns the existing repository if it already exists
)
print(f"Repository created: {repo['name']}")
print(f"URL: {repo['url']}")
```

## Working with Repositories

After creating a repository, you can clone it and work with it using standard Git commands:

```bash
# Clone the repository
git clone https://source.developers.google.com/p/my-project/r/my-repo

# Add files
git add .

# Commit changes
git commit -m "Initial commit"

# Push to the repository
git push origin master
```

## Authentication

When working with Source Repositories from the command line, you can authenticate using the Google Cloud SDK:

```bash
# Authenticate with Google Cloud
gcloud auth login

# Configure Git to use gcloud as a credential helper
git config --global credential.https://source.developers.google.com.helper gcloud.sh
```

## Error Handling

The SourceRepository class handles common errors and converts them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    source_repo.get_repo(repo_name="non-existent-repo")
except exceptions.NotFound:
    print("Repository not found")

try:
    source_repo.create_repo(repo_name="existing-repo", exists_ok=False)
except exceptions.AlreadyExists:
    print("Repository already exists")
```

## Working with Service Account Impersonation

Service account impersonation allows you to act as a service account without having its key file. This is a more secure approach than downloading and storing service account keys.

```python
# Initialize with service account impersonation
source_repo = SourceRepository(impersonate_account="service-account@project-id.iam.gserviceaccount.com")

# Now all operations will be performed as the impersonated service account
repos = source_repo.list_repos()
```

For more information on service account impersonation, see the [Authentication](../authentication.md) documentation.

## Integration with Cloud Build

Source Repositories can be integrated with Cloud Build to automatically build and deploy your code when changes are pushed to the repository. For more information, see the [Cloud Build](build.md) documentation.

## Best Practices

Here are some best practices for working with Source Repositories:

1. **Use descriptive repository names**: Choose repository names that clearly indicate their purpose and content.
2. **Set up branch protection**: Configure branch protection rules to prevent direct pushes to important branches.
3. **Use meaningful commit messages**: Write clear and descriptive commit messages to make it easier to understand changes.
4. **Implement a branching strategy**: Use a consistent branching strategy like Git Flow or GitHub Flow.
5. **Regularly clean up old branches**: Delete branches that are no longer needed to keep the repository clean.
6. **Set up code reviews**: Use pull requests and code reviews to maintain code quality.
7. **Integrate with CI/CD**: Set up continuous integration and continuous deployment pipelines to automate testing and deployment.