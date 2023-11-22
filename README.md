![Github CI](https://github.com/flamingo-run/gcp-pilot/workflows/Github%20CI/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/flamingo-run/gcp-pilot/badge.svg)](https://coveralls.io/github/flamingo-run/gcp-pilot)
[![python](https://img.shields.io/badge/python-3.11-blue.svg)]() [![python](https://img.shields.io/badge/python-3.12-blue.svg)]()

# Google Cloud Pilot

## Installation

`pip install gcp-pilot`

Some APIs need extra packages, thus you must use `extras` to add them:

- Cloud Tasks: `pip install gcp-pilot[tasks]`
- Cloud Build: `pip install gcp-pilot[build]`
- Cloud Storage: `pip install gcp-pilot[storage]`
- Big Query: `pip install gcp-pilot[bigquery]`
- Speech: `pip install gcp-pilot[speech]`
- Sheets: `pip install gcp-pilot[sheets]`
- Pub/Sub: `pip install gcp-pilot[pubsub]`
- Datastore: `pip install gcp-pilot[datastore]`
- Cloud DNS: `pip install gcp-pilot[dns]`
- Secret Manager: `pip install gcp-pilot[secret]`
- Healthcare Engine: `pip install gcp-pilot[healthcare]`
- IAM: `pip install gcp-pilot[iam]`


## Usage

```
from gcp_pilot.resource import ResourceManager

grm = ResourceManager()
```

## Default Values

### Credentials

`gcp-pilot` uses [ADC](https://cloud.google.com/docs/authentication/production#automatically) to detect credentials. This means that you must have one of the following setups:
- Environment variable `GOOGLE_APPLICATION_CREDENTIALS` pointing to the JSON file with the credentials
- Run inside GCP (Compute Engine, Cloud Run, GKE, AppEngine), so the machine's credentials will be used
- Run locally after authenticating with `gcloud auth application-default login`

You can also globally set a service account using the environment variable `DEFAULT_SERVICE_ACCOUNT`, which will require impersonation.

### Project

When creating a client, a default project is defined by using the project that the credentials belongs to.

Clients that support managing resources from other projects can be overwritten per call.

> Example: you create a `BigQuery` client using credentials from  `project_a`.
All calls will query datasets from `project_a`, unless another project is passed as parameter when performing the call.

You can also globally set a project using the environment variable `DEFAULT_PROJECT`

### Location

Very similar to default project, a default location is defined by using the project's location.
The project's location will exist if you ever enabled AppEngine, so you had to set a location then.
Otherwise, no default location will be set.

You can also globally set a location using the environment variable `DEFAULT_LOCATION` and reduce the amount of API calls 
when creating clients.

## Why Use ``gcp-pilot``

_"Since Google already has a [generic API client](https://github.com/googleapis/google-api-python-client) and so many [specific clients](https://github.com/googleapis?q=python&type=&language=), why should I use this library?"_

Google's has 2 types of clients:
- **dedicated**: custom-made for the APIs. They are excellent: they implement high level interaction with the API with friendly methods. The `gcp-pilot` can adds its value by handling authentication, friendly errors and parameter fallback.
- **generic**: a single client that is capable of dynamically calling any REST API. They are a pain to use: very specific calls that must be translated from the documentation. The `gcp-pilot` comes in handy to add high-level interaction with friendly method such as `Calendar.create_event`, on top of all other vantages cited above.

### Parameter Fallback

Most API endpoints require `project_id` (sometimes even `project_number`) and `location`.

So `gcp-pilot` automatically detects these values for you, based on your credentials (although it'll require extra permissions and API calls).

If you use multiple projects, and your credentials is accessing other projects, you can still customize the parameters on each call to avoid the default fallback.


### Friendly Errors

Most APIs return a generic ``HttpException`` with am embedded payload with error output, and also there's a couple of different structures for these payloads.

So `gcp-pilot` tries its best to convert these exceptions into more friendly ones, such as `NotFound`, `AlreadyExists` and `NotAllowed`.

It'll be much easier to capture these exceptions and handle them by its type.


### Identification Features

- **Authentication**: each client uses [ADC](https://cloud.google.com/docs/authentication/production#automatically),
which consists on trying to detect the service account with fallbacks: SDK > Environment Variable > Metadata
- **Impersonation**: it's possible to create clients with ``impersonate_account`` parameter that [impersonates](https://cloud.google.com/iam/docs/impersonating-service-accounts#allow-impersonation) another account.
- **Delegation**: services _(eg. Google Workspace)_ that requires specific subjects are automatically delegated, sometimes even performing additional credential signatures.
- **Region**: most GCP services requires a location to work on *(some even require specific locations)*. If not provided, the clients use the project's default location, as defined by App Engine.
- **Authorization**: OIDC authorization is automatically generated for services *(eg. CloudRun)* that require authentication to be used.

### Auto-Authorization

Some services require specific authorizations that should be setup prior to its usage, some examples:
- [Pub/Sub] subscribe to a topic with authenticated push;
- [Cloud Scheduler] schedule a job to trigger a Cloud Run service;
- [Cloud Tasks] queue a task to trigger a Cloud Run service;

In these cases, `gcp-pilot` tries its best to assure that the required permissions are properly set up
before the actual request is made.

### Integration

Some services can be integrated, and `gcp-pilot` does just that in a seamless way by adding helper methods.

Example: you can subscribe to Google Cloud Build's events to be notified by every build step.

By using `CloudBuild.subscribe`, the `gcp-pilot` creates a subscription (and the topic, if needed) in the Google Pub/Sub service.

## Supported APIs

- IAM
   - manage service accounts
   - manage permissions
   - encode & decode JWT tokens
- Identity Platform
  - sign in users
  - sign up users
  - reset password flow
  - verify email flow
  - generate authentication magic links (OOB tokens)
  - manage authorized domains
- Credentials
  - manage API Keys
- Resource Manager
   - manage projects
   - manage permissions
- Secret Manager
  - manage secrets
- Identity Aware Proxy
   - generate OIDC token
- Source Repositories
   - manage repositories
- Directory:
  - manage users
  - manage groups
- People:
  - get people
- Cloud SQL
   - manage instances
   - manage databases
   - manage users
- Cloud Storage
   - manage buckets
   - manage files
- Cloud Build
   - manage triggers
- Cloud Functions
  - manager functions
  - manage permissions
- Cloud Scheduler
   - manage schedules
- Cloud Tasks
   - manage tasks & queues
- Cloud Run
   - read services
   - manage domain mappings [[1]](https://cloud.google.com/run/docs/mapping-custom-domains#adding_verified_domain_owners_to_other_users_or_service_accounts)
- API Gateway
  - manage APIs
  - manage API Configs
  - manage Gateways
- Service Usage
  - enable/disable APIs and Services
- BigQuery
   - manage datasets
   - perform queries
- Calendar
   - manage events
- Google Chats
   - build complex messages
   - call webhook
   - interact as bot
- Cloud Directory
   - manage groups
- Cloud DNS
   - manage DNS zones
   - manage zone's registers
- Sheets
   - manage spreadsheets (powered by gspread)
- Speech
   - recognize speech from audio
- Datastore
   - Object Mapping ("ORM-ish" management of documents)
- Monitoring
  - reporting errors
  - logging
  - manage custom services
- Healthcare
  - Manage datasets
  - Manage stores
  - Manage FHIR resources: _powered by [fhir-resources](https://github.com/nazrulworld/fhir.resources)_
- Datastream
  - Read/Delete streams
  - Read Stream's Objects
  - Start/Stop object backfill