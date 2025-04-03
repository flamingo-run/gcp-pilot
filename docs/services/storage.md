# Cloud Storage

Cloud Storage is a service for storing objects in Google Cloud Platform. The `CloudStorage` class in gcp-pilot provides a high-level interface for interacting with Google Cloud Storage.

## Installation

To use the Cloud Storage functionality, you need to install gcp-pilot with the storage extra:

```bash
pip install gcp-pilot[storage]
```

## Usage

### Initialization

```python
from gcp_pilot.storage import CloudStorage

# Initialize with default credentials
storage = CloudStorage()

# Initialize with specific project
storage = CloudStorage(project_id="my-project")

# Initialize with service account impersonation
storage = CloudStorage(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

### Creating a Bucket

```python
# Create a bucket in the default region
bucket = storage.create_bucket(name="my-bucket")

# Create a bucket in a specific region
bucket = storage.create_bucket(
    name="my-bucket",
    region="us-central1",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    exists_ok=True,  # Optional: if True, returns the existing bucket if it already exists
)
```

### Uploading Files

The `upload` method is versatile and can handle various types of input:

```python
# Upload a local file
blob = storage.upload(
    source_file="/path/to/local/file.txt",
    bucket_name="my-bucket",
    target_file_name="file.txt",  # Optional: defaults to the source file name
    is_public=False,  # Optional: if True, makes the file publicly accessible
    content_type="text/plain",  # Optional: sets the content type
)

# Upload from a URL
blob = storage.upload(
    source_file="https://example.com/file.txt",
    bucket_name="my-bucket",
    target_file_name="file.txt",
)

# Upload from a string
blob = storage.upload(
    source_file="Hello, World!",
    bucket_name="my-bucket",
    target_file_name="hello.txt",
)

# Upload from bytes
blob = storage.upload(
    source_file=b"Hello, World!",
    bucket_name="my-bucket",
    target_file_name="hello.txt",
)

# Upload from a file-like object
with open("/path/to/local/file.txt", "rb") as f:
    blob = storage.upload(
        source_file=f,
        bucket_name="my-bucket",
        target_file_name="file.txt",
    )
```

### Getting a Bucket

```python
# Get a bucket
bucket = storage.get_bucket(name="my-bucket")

# Get a bucket, creating it if it doesn't exist
bucket = storage.get_bucket(
    name="my-bucket",
    auto_create_bucket=True,
    region="us-central1",  # Optional: used only if the bucket is created
    project_id="my-project",  # Optional: used only if the bucket is created
)
```

### Copying Files

```python
# Copy a file from one bucket to another
blob = storage.copy(
    source_file_name="file.txt",
    source_bucket_name="source-bucket",
    target_bucket_name="target-bucket",
    target_file_name="file_copy.txt",  # Optional: defaults to the source file name
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    region="us-central1",  # Optional: used only if a bucket is created
    auto_create_bucket=False,  # Optional: if True, creates the target bucket if it doesn't exist
)
```

### Moving Files

```python
# Move a file from one bucket to another
blob = storage.move(
    source_file_name="file.txt",
    source_bucket_name="source-bucket",
    target_bucket_name="target-bucket",
    target_file_name="file_moved.txt",  # Optional: defaults to the source file name
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    region="us-central1",  # Optional: used only if a bucket is created
)
```

### Deleting Files

```python
# Delete a file
storage.delete(
    file_name="file.txt",
    bucket_name="my-bucket",
)
```

### Listing Files

```python
# List all files in a bucket
for blob in storage.list_files(bucket_name="my-bucket"):
    print(f"File: {blob.name}")

# List files with a specific prefix
for blob in storage.list_files(bucket_name="my-bucket", prefix="folder/"):
    print(f"File: {blob.name}")
```

### Getting a File

```python
# Get a file by its GCS URI
blob = storage.get_file(uri="gs://my-bucket/file.txt")
```

### Getting a Download URL

```python
# Generate a signed URL for downloading a file
url = storage.get_download_url(
    bucket_name="my-bucket",
    blob_name="file.txt",
    expiration=timedelta(minutes=30),  # Optional: defaults to 5 minutes
    version="v4",  # Optional: defaults to "v4"
)
```

### Getting a GCS URI

```python
# Get the GCS URI for a blob
uri = storage.get_uri(blob)
# Returns: "gs://my-bucket/file.txt"
```

## Error Handling

The CloudStorage class handles common errors and converts them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    storage.create_bucket(name="my-bucket", exists_ok=False)
except exceptions.AlreadyExists:
    print("Bucket already exists")

try:
    storage.get_file(uri="invalid-uri")
except exceptions.ValidationError:
    print("Invalid GCS URI")
```