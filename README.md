![Github CI](https://github.com/flamingo-run/gcp-pilot/workflows/Github%20CI/badge.svg)
[![Maintainability](https://api.codeclimate.com/v1/badges/0e03784af54dab4a7ebe/maintainability)](https://codeclimate.com/github/flamingo-run/gcp-pilot/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/0e03784af54dab4a7ebe/test_coverage)](https://codeclimate.com/github/flamingo-run/gcp-pilot/test_coverage)
[![python](https://img.shields.io/badge/python-3.8-blue.svg)]()

# Google Cloud Pilot

## Installation

`pip install gcp-pilot`

## Usage

```
from gcp_pilot.resource import ResourceManager

grm = ResourceManager()
```

## Identification Features

- **Authentication**: each client uses [ADC](https://cloud.google.com/docs/authentication/production#automatically),
which consists on trying to detect the service account with fallbacks: SDK > Environment Variable > Metadata
- **Impersonation**: it's possible to create clients with ``impersonate_account`` parameter that [impersonates](https://cloud.google.com/iam/docs/impersonating-service-accounts#allow-impersonation) another account.
- **Delegation**: services _(eg. Google Workspace)_ that requires specific subjects are automatically delegated, sometimes even performing additional credential signatures.
- **Region**: most GCP services requires a location to work on *(some even require specific locations)*. If not provided, the clients use the project's default location, as defined by App Engine.
- **Authorization**: OIDC authorization is automatically generated for services *(eg. CloudRun)* that require authentication to be used.

## Supported APIs

- IAM
   - manage service accounts
   - manage permissions
- Resource Manager
   - manage projects
   - manage permissions
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
