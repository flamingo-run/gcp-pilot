![PyPI - Downloads](https://img.shields.io/pypi/dm/gcp-pilot)

![Github CI](https://github.com/flamingo-run/gcp-pilot/workflows/Github%20CI/badge.svg)
[![Maintainability](https://qlty.sh/badges/e65aa986-7aeb-436c-9340-9aa19ef3edaa/maintainability.svg)](https://qlty.sh/gh/flamingo-run/projects/gcp-pilot)
[![Code Coverage](https://qlty.sh/badges/e65aa986-7aeb-436c-9340-9aa19ef3edaa/test_coverage.svg)](https://qlty.sh/gh/flamingo-run/projects/gcp-pilot)

[![python](https://img.shields.io/badge/python-3.11-blue.svg)]() [![python](https://img.shields.io/badge/python-3.12-blue.svg)]() [![python](https://img.shields.io/badge/python-3.13-blue.svg)]()

# Google Cloud Pilot

Google Cloud Pilot (gcp-pilot) is a Python library that simplifies interaction with Google Cloud Platform services. It provides a high-level, user-friendly interface to various GCP APIs, handling authentication, error management, and parameter fallback automatically.

## Documentation

**Full documentation is available at [gcp-pilot.flamingo.codes](https://gcp-pilot.flamingo.codes)**

## Installation

```bash
pip install gcp-pilot
```

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

## Basic Usage

```python
from gcp_pilot.resource import ResourceManager

grm = ResourceManager()
```

## Key Features

- **Parameter Fallback**: Automatically detects project_id and location based on your credentials
- **Friendly Errors**: Converts generic HttpExceptions into more specific exceptions like NotFound, AlreadyExists, etc.
- **Auto-Authorization**: Sets up required permissions for services that need specific authorizations
- **Integration**: Seamlessly integrates different GCP services
- **Authentication Handling**: Uses Application Default Credentials with support for impersonation and delegation

## Supported Services

gcp-pilot supports a wide range of Google Cloud Platform services, including:

- IAM and Identity Management
- Storage and Databases (Cloud Storage, BigQuery, Datastore, etc.)
- Compute and Serverless (Cloud Functions, Cloud Run, App Engine)
- Messaging and Integration (Pub/Sub, Cloud Tasks, Cloud Scheduler)
- DevOps and CI/CD (Cloud Build, Source Repositories)
- Monitoring and Logging
- Google Workspace Integration (Directory, Calendar, Sheets, etc.)

For detailed documentation on each service, please refer to the [documentation site](https://github.com/flamingo-run/gcp-pilot/tree/main/docs).
