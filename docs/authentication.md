# Authentication and Credentials

Authentication is a critical aspect of interacting with Google Cloud Platform services. gcp-pilot simplifies this process by providing several authentication mechanisms and features.

## Application Default Credentials (ADC)

By default, gcp-pilot uses [Application Default Credentials (ADC)](https://cloud.google.com/docs/authentication/production#automatically) to detect credentials. This means that you must have one of the following setups:

1. Environment variable `GOOGLE_APPLICATION_CREDENTIALS` pointing to the JSON file with the credentials
2. Run inside GCP (Compute Engine, Cloud Run, GKE, AppEngine), so the machine's credentials will be used
3. Run locally after authenticating with `gcloud auth application-default login`

This approach allows your application to run seamlessly in different environments without code changes.

## Service Account Impersonation

You can globally set a service account using the environment variable `DEFAULT_SERVICE_ACCOUNT`, which will require impersonation.

Impersonation allows a service account to act on behalf of another service account. This is useful when you want to:
- Use a single service account for authentication but need different permissions for different operations
- Avoid distributing service account keys by using impersonation instead

To use impersonation, you need to:
1. Ensure the original service account has the `roles/iam.serviceAccountTokenCreator` role on the target service account
2. Pass the target service account email to the client using the `impersonate_account` parameter

```python title="Service Account Impersonation Example"
from gcp_pilot.storage import CloudStorage

storage = CloudStorage(impersonate_account="target-sa@project-id.iam.gserviceaccount.com") # (1)!
```

1. Impersonate a service account

## Delegation

Some services (like Google Workspace) require specific subjects to be delegated. gcp-pilot automatically handles delegation, sometimes even performing additional credential signatures.

To use delegation, you can pass the subject to the client:

```python title="Delegation Example"
from gcp_pilot.directory import Directory

directory = Directory(subject="user@example.com") # (1)!
```

1. Use delegation for a specific user

## Default Project

When creating a client, a default project is defined by using the project that the credentials belong to.

Clients that support managing resources from other projects can be overwritten per call.

!!! example "Project Specificity Example"
    You create a `BigQuery` client using credentials from `project_a`.
    All calls will query datasets from `project_a`, unless another project is passed as parameter when performing the call.

You can also globally set a project using the environment variable `DEFAULT_PROJECT`.

## Default Location

Similar to the default project, a default location is defined by using the project's location.
The project's location will exist if you ever enabled AppEngine, so you had to set a location then.
Otherwise, no default location will be set.

You can also globally set a location using the environment variable `DEFAULT_LOCATION` to reduce the number of API calls when creating clients.

## Auto-Authorization

Some services require specific authorizations that should be set up prior to their usage. 

!!! example "Auto-Authorization Scenarios"
    gcp-pilot tries its best to ensure that the required permissions are properly set up before the actual request is made in cases like:
    - [Pub/Sub] subscribe to a topic with authenticated push
    - [Cloud Scheduler] schedule a job to trigger a Cloud Run service
    - [Cloud Tasks] queue a task to trigger a Cloud Run service

## OIDC Authorization

Identity-Aware Proxy (IAP) and other services that require OIDC tokens are automatically handled by gcp-pilot. The library generates the necessary OIDC tokens for services that require authentication.

```python title="OIDC Token Generation Example"
from gcp_pilot.iap import IdentityAwareProxy

iap = IdentityAwareProxy()
token = iap.get_token(url="https://my-service.run.app") # (1)!
```

1. Generate an OIDC token for a Cloud Run service
