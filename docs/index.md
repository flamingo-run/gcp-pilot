# Google Cloud Pilot

![Github CI](https://github.com/flamingo-run/gcp-pilot/workflows/Github%20CI/badge.svg)
[![Coverage Status](https://coveralls.io/repos/github/flamingo-run/gcp-pilot/badge.svg)](https://coveralls.io/github/flamingo-run/gcp-pilot)
[![python](https://img.shields.io/badge/python-3.11-blue.svg)]() [![python](https://img.shields.io/badge/python-3.12-blue.svg)]() [![python](https://img.shields.io/badge/python-3.13-blue.svg)]()

Google Cloud Pilot (gcp-pilot) is a Python library that simplifies interaction with Google Cloud Platform services. It provides a high-level, user-friendly interface to various GCP APIs, handling authentication, error management, and parameter fallback automatically.

## Installation

```bash title="Install gcp-pilot"
pip install gcp-pilot
```

Some APIs need extra packages, thus you must use `extras` to add them:

```bash title="Install with extras"
pip install gcp-pilot[tasks] # (1)!
pip install gcp-pilot[build] # (2)!
pip install gcp-pilot[storage] # (3)!
pip install gcp-pilot[bigquery] # (4)!
pip install gcp-pilot[speech] # (5)!
pip install gcp-pilot[sheets] # (6)!
pip install gcp-pilot[pubsub] # (7)!
pip install gcp-pilot[datastore] # (8)!
pip install gcp-pilot[dns] # (9)!
pip install gcp-pilot[secret] # (10)!
pip install gcp-pilot[healthcare] # (11)!
pip install gcp-pilot[iam] # (12)!
```

1.  Cloud Tasks
2.  Cloud Build
3.  Cloud Storage
4.  Big Query
5.  Speech
6.  Sheets
7.  Pub/Sub
8.  Datastore
9.  Cloud DNS
10. Secret Manager
11. Healthcare Engine
12. IAM

## Basic Usage

```python title="Basic Usage Example"
from gcp_pilot.resource import ResourceManager

grm = ResourceManager()
```

## Why Use gcp-pilot

> _"Since Google already has a [generic API client](https://github.com/googleapis/google-api-python-client) and so many [specific clients](https://github.com/googleapis?q=python&type=&language=), why should I use this library?"_

Google has 2 types of clients:

- **dedicated**: custom-made for the APIs. They are excellent: they implement high level interaction with the API with friendly methods. The `gcp-pilot` adds value by handling authentication, friendly errors and parameter fallback.

- **generic**: a single client that is capable of dynamically calling any REST API. They are a pain to use: very specific calls that must be translated from the documentation. The `gcp-pilot` comes in handy to add high-level interaction with friendly methods such as `Calendar.create_event`, on top of all other advantages cited above.

### Key Features

- **Parameter Fallback**: Automatically detects project_id and location based on your credentials
- **Friendly Errors**: Converts generic HttpExceptions into more specific exceptions like NotFound, AlreadyExists, etc.
- **Auto-Authorization**: Sets up required permissions for services that need specific authorizations
- **Integration**: Seamlessly integrates different GCP services
- **Authentication Handling**: Uses Application Default Credentials with support for impersonation and delegation

## Supported Services

gcp-pilot supports a wide range of Google Cloud Platform services. Each service has its own dedicated documentation page with detailed usage examples:

- [IAM](services/iam.md)
- [Identity Platform](services/identity_platform.md)
- [Resource Manager](services/resource.md)
- [Secret Manager](services/secret_manager.md)
- [Cloud Storage](services/storage.md)
- [Cloud Build](services/build.md)
- [Cloud Functions](services/functions.md)
- [Cloud Scheduler](services/scheduler.md)
- [Cloud Tasks](services/tasks.md)
- [Cloud Run](services/run.md)
- [BigQuery](services/big_query.md)
- [Pub/Sub](services/pubsub.md)
- [Datastore](services/datastore.md)
- [Cloud DNS](services/dns.md)
- [Healthcare](services/healthcare.md)
- [And more...](services/index.md)