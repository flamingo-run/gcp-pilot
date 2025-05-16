# Source Repositories

Source Repositories is a service that provides Git version control to support collaborative development of any application or service. The `SourceRepository` class in gcp-pilot provides a high-level interface for interacting with Google Cloud Source Repositories.

## Installation

To use the Source Repositories functionality, you need to install gcp-pilot:

```bash title="Install gcp-pilot"
pip install gcp-pilot
```

## Usage

### Initialization

```python title="Initialize SourceRepository Client"
from gcp_pilot.source import SourceRepository

source_repo = SourceRepository() # (1)!
source_repo = SourceRepository(project_id="my-project") # (2)!
source_repo = SourceRepository(impersonate_account="service-account@project-id.iam.gserviceaccount.com") # (3)!
```

1.  Initialize with default credentials
2.  Initialize with specific project
3.  Initialize with service account impersonation

### Listing Repositories

```python title="List Source Repositories"
repos = source_repo.list_repos( # (1)!
    project_id="my-project",  # (2)!
)
for repo in repos:
    print(f"Repository: {repo['name']}")
    print(f"URL: {repo['url']}")
    print(f"Size: {repo.get('size', 'Unknown')}")
```

1.  List all repositories in a project
2.  Optional: defaults to the project associated with credentials

### Getting a Repository

```python title="Get a Source Repository"
repo = source_repo.get_repo( # (1)!
    name="my-repo",
    project_id="my-project",  # (2)!
)
print(f"Repository: {repo['name']}")
print(f"URL: {repo['url']}")
```

1.  Get information about a specific repository
2.  Optional: defaults to the project associated with credentials

### Creating a Repository

```python title="Create a Source Repository"
repo = source_repo.create_repo( # (1)!
    name="my-new-repo",
    project_id="my-project",  # (2)!
    exists_ok=True,  # (3)!
)
print(f"Repository created: {repo['name']}")
```

1.  Create a new repository
2.  Optional: defaults to the project associated with credentials
3.  Optional: if True, returns the existing repository if it already exists

### Deleting a Repository

```python title="Delete a Source Repository"
source_repo.delete_repo( # (1)!
    name="my-repo-to-delete",
    project_id="my-project",  # (2)!
)
```

1.  Delete a repository
2.  Optional: defaults to the project associated with credentials

## Common Git Commands with Source Repositories

```bash title="Common Git Operations"
# Clone a repository (1)!
git clone https://source.developers.google.com/p/my-project/r/my-repo

# Add a remote for Source Repositories (2)!
git remote add google https://source.developers.google.com/p/my-project/r/my-repo

# Push to Source Repositories (3)!
git push google master

# Pull from Source Repositories (4)!
git pull google master
```

1.  Clone a repository
2.  Add a remote for Source Repositories
3.  Push to Source Repositories
4.  Pull from Source Repositories

## Authenticate for Source Repositories CLI Access

```bash title="Authenticate for CLI Access"
# Authenticate using gcloud (1)!
gcloud auth login
gcloud auth application-default login

# Configure Git to use the gcloud credential helper (2)!
git config --global credential.helper gcloud.sh
```

1.  Authenticate using gcloud
2.  Configure Git to use the gcloud credential helper

## Working with Service Account Impersonation

Service account impersonation allows you to act as a service account without having its key file. This is a more secure approach than downloading and storing service account keys.

```python title="Using Impersonated Credentials for Source Repositories"
source_repo = SourceRepository(impersonate_account="service-account@project-id.iam.gserviceaccount.com") # (1)!
repos = source_repo.list_repos() # (2)!
```

1.  Initialize with service account impersonation
2.  Now all operations will be performed as the impersonated service account

For more information on service account impersonation, see the [Authentication](../authentication.md) documentation.

!!! info "Integration with Cloud Build"
    Source Repositories can be integrated with Cloud Build to automatically build and deploy your code when changes are pushed to the repository. For more information, see the [Cloud Build](build.md) documentation.

!!! tip "Best Practices for Source Repositories"
    Here are some best practices for working with Source Repositories:

    1. **Use descriptive repository names**: Choose repository names that clearly indicate their purpose and content.
    2. **Set up branch protection**: Configure branch protection rules to prevent direct pushes to important branches.
    3. **Use meaningful commit messages**: Write clear and descriptive commit messages to make it easier to understand changes.
    4. **Implement a branching strategy**: Use a consistent branching strategy like Git Flow or GitHub Flow.
    5. **Regularly clean up old branches**: Delete branches that are no longer needed to keep the repository clean.
    6. **Set up code reviews**: Use pull requests and code reviews to maintain code quality.
    7. **Integrate with CI/CD**: Set up continuous integration and continuous deployment pipelines to automate testing and deployment.
