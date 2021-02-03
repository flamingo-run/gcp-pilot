![Github CI](https://github.com/flamingo-run/gcp-pilot/workflows/Github%20CI/badge.svg)
[![Maintainability](https://api.codeclimate.com/v1/badges/0e03784af54dab4a7ebe/maintainability)](https://codeclimate.com/github/flamingo-run/gcp-pilot/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/0e03784af54dab4a7ebe/test_coverage)](https://codeclimate.com/github/flamingo-run/gcp-pilot/test_coverage)
[![python](https://img.shields.io/badge/python-3.8-blue.svg)]()

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


## Usage

```
from gcp_pilot.resource import ResourceManager

grm = ResourceManager()
```

## Why Use ``gcp-pilot``

_"Since Google already has a [generic API client](https://github.com/googleapis/google-api-python-client) and so many [specific clients](https://github.com/googleapis?q=python&type=&language=), why should I use this library?"_

Google's has 2 types of clients:
- **dedicated**: custom made for the APIs. They are excellent: they implement high level interaction with the API with friendly methods. The `gcp-pilot` can adds its value by handling authentication, friendly errors and parameter fallback.
- **generic**: a single client that is capable of dynamically calling any REST API. They are a pain to use: very specific calls that must be translated from the documentation. The `gcp-pilot` comes in handy to add high-level interaction with friendly method such as `Calendar.create_event`, on top of all other vantages cited above.

### Parameter Fallback

Most of the API endpoints require `project_id` (sometimes even `project_number`) and `location`.

So `gcp-pilot` automatically detects these values for you, based on your credentials (although it'll require extra permissions and API calls).

If you use multiple projects, and your credentials is accessing other projects, you can still customize the parameters on each call to avoid the default fallback.


### Friendly Errors

Most of APIs return a generic ``HttpException`` with am embedded payload with error output, and also there's a couple of different structures for these payloads.

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
- Resource Manager
   - manage projects
   - manage permissions
- Identity Aware Proxy
   - generate OIDC token
- Source Repositories
   - manage repositories
- Cloud SQL
   - manage instances
   - manage databases
   - manage users
- Cloud Storage
   - manage buckets
   - manage files
- Cloud Build
   - manager triggers
- Cloud Scheduler
   - manage schedules
- Cloud Tasks
   - manage tasks & queues
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
- Sheets
   - manage spreadsheets (powered by gspread)
- Speech
   - recognize speech from audio
- Datastore
   - Object Mapping ("ORM-ish" management of documents)
