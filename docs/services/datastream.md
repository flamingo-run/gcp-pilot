# Datastream

Datastream is a serverless and easy-to-use change data capture (CDC) and replication service. The `Datastream` class in gcp-pilot provides a high-level interface for interacting with Google Cloud Datastream.

## Installation

To use the Datastream functionality, you need to install gcp-pilot:

```bash
pip install gcp-pilot
```

## Usage

### Initialization

```python
from gcp_pilot.datastream import Datastream

# Initialize with default credentials
datastream = Datastream()

# Initialize with specific project
datastream = Datastream(project_id="my-project")

# Initialize with specific location
datastream = Datastream(location="us-central1")

# Initialize with service account impersonation
datastream = Datastream(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

### Managing Streams

#### Listing Streams

```python
# List all streams in a project
streams = datastream.get_streams()
for stream in streams:
    print(f"Stream: {stream['name']}")

# List streams in a specific location
streams = datastream.get_streams(location="us-central1")
for stream in streams:
    print(f"Stream: {stream['name']}")
```

#### Getting a Stream

```python
# Get information about a stream
stream = datastream.get_stream(
    stream_name="my-stream",
    location="us-central1",  # Optional: defaults to the default location
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Stream: {stream['name']}")
print(f"State: {stream['state']}")
print(f"Source: {stream['sourceConfig']['sourceConnectionProfile']}")
print(f"Destination: {stream['destinationConfig']['destinationConnectionProfile']}")
```

#### Deleting a Stream

```python
# Delete a stream
datastream.delete_stream(
    stream_name="my-stream",
    location="us-central1",  # Optional: defaults to the default location
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
```

### Managing Stream Objects

Stream objects represent the database objects (tables, schemas) that are being replicated by a stream.

#### Listing Stream Objects

```python
# List all objects in a stream
objects = datastream.get_objects(
    stream_name="my-stream",
    location="us-central1",  # Optional: defaults to the default location
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
for obj in objects:
    print(f"Object: {obj['displayName']}")
    print(f"Source Type: {obj['sourceObject']['postgresqlTable']['table']}")
    print(f"Backfill Status: {obj['backfillJob']['state']}")
```

#### Getting a Stream Object

```python
# Get information about a specific stream object
obj = datastream.get_object(
    object_id="my-object-id",
    stream_name="my-stream",
    location="us-central1",  # Optional: defaults to the default location
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Object: {obj['displayName']}")
print(f"Source Type: {obj['sourceObject']['postgresqlTable']['table']}")
print(f"Backfill Status: {obj['backfillJob']['state']}")
```

#### Finding a Stream Object

```python
# Find a stream object by schema and table name
obj = datastream.find_object(
    schema="public",
    table="users",
    stream_name="my-stream",
    location="us-central1",  # Optional: defaults to the default location
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Object: {obj['displayName']}")
```

### Managing Backfill Jobs

Backfill jobs are used to replicate existing data from the source to the destination.

#### Starting a Backfill Job

```python
# Start a backfill job for a specific table
response = datastream.start_backfill(
    schema="public",
    table="users",
    stream_name="my-stream",
    location="us-central1",  # Optional: defaults to the default location
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Backfill job started: {response}")
```

#### Stopping a Backfill Job

```python
# Stop a backfill job for a specific table
response = datastream.stop_backfill(
    schema="public",
    table="users",
    stream_name="my-stream",
    location="us-central1",  # Optional: defaults to the default location
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Backfill job stopped: {response}")
```

## Error Handling

The Datastream class handles common errors and converts them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    datastream.get_stream(stream_name="non-existent-stream")
except exceptions.NotFound:
    print("Stream not found")

try:
    datastream.find_object(schema="non-existent", table="non-existent", stream_name="my-stream")
except exceptions.NotFound:
    print("Object not found")
```

## Working with PostgreSQL Sources

The examples above focus on PostgreSQL sources, which is what the current implementation supports. The `find_object` method specifically looks for PostgreSQL identifiers. If you're working with other source types, you may need to modify the code or wait for future updates to the library.