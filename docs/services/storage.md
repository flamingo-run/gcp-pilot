# Cloud Storage

Cloud Storage is a service for storing objects in Google Cloud Platform. The `CloudStorage` class in gcp-pilot provides a high-level interface for interacting with Google Cloud Storage.

## Installation

To use the Cloud Storage functionality, you need to install gcp-pilot with the storage extra:

```bash title="Install Storage extra"
pip install gcp-pilot[storage]
```

## Usage

### Initialization

```python title="Initialize CloudStorage"
from gcp_pilot.storage import CloudStorage

storage = CloudStorage() # (1)!
storage = CloudStorage(project_id="my-project") # (2)!
storage = CloudStorage(impersonate_account="service-account@project-id.iam.gserviceaccount.com") # (3)!
```

1.  Initialize with default credentials
2.  Initialize with specific project
3.  Initialize with service account impersonation

### Creating a Bucket

```python title="Create a Cloud Storage Bucket"
bucket = storage.create_bucket(name="my-bucket") # (1)!

bucket = storage.create_bucket( # (2)!
    name="my-bucket",
    region="us-central1",
    project_id="my-project",  # (3)!
    exists_ok=True,  # (4)!
)
```

1.  Create a bucket in the default region
2.  Create a bucket in a specific region
3.  Optional: defaults to the project associated with credentials
4.  Optional: if True, returns the existing bucket if it already exists

### Uploading Files

The `upload` method is versatile and can handle various types of input:

```python title="Upload Files to Cloud Storage"
blob = storage.upload( # (1)!
    source_file="/path/to/local/file.txt",
    bucket_name="my-bucket",
    target_file_name="file.txt",  # (2)!
    is_public=False,  # (3)!
    content_type="text/plain",  # (4)!
)

blob = storage.upload( # (5)!
    source_file="https://example.com/file.txt",
    bucket_name="my-bucket",
    target_file_name="file.txt",
)

blob = storage.upload( # (6)!
    source_file="Hello, World!",
    bucket_name="my-bucket",
    target_file_name="hello.txt",
)

blob = storage.upload( # (7)!
    source_file=b"Hello, World!",
    bucket_name="my-bucket",
    target_file_name="hello.txt",
)

with open("/path/to/local/file.txt", "rb") as f: # (8)!
    blob = storage.upload(
        source_file=f,
        bucket_name="my-bucket",
        target_file_name="file.txt",
    )
```

1.  Upload a local file
2.  Optional: defaults to the source file name
3.  Optional: if True, makes the file publicly accessible
4.  Optional: sets the content type
5.  Upload from a URL
6.  Upload from a string
7.  Upload from bytes
8.  Upload from a file-like object

### Getting a Bucket

```python title="Get a Cloud Storage Bucket"
bucket = storage.get_bucket(name="my-bucket") # (1)!

bucket = storage.get_bucket( # (2)!
    name="my-bucket",
    auto_create_bucket=True,
    region="us-central1",  # (3)!
    project_id="my-project",  # (4)!
)
```

1.  Get a bucket
2.  Get a bucket, creating it if it doesn't exist
3.  Optional: used only if the bucket is created
4.  Optional: used only if the bucket is created

### Copying Files

```python title="Copy Files in Cloud Storage"
blob = storage.copy( # (1)!
    source_file_name="file.txt",
    source_bucket_name="source-bucket",
    target_bucket_name="target-bucket",
    target_file_name="file_copy.txt",  # (2)!
    project_id="my-project",  # (3)!
    region="us-central1",  # (4)!
    auto_create_bucket=False,  # (5)!
)
```

1.  Copy a file from one bucket to another
2.  Optional: defaults to the source file name
3.  Optional: defaults to the project associated with credentials
4.  Optional: used only if a bucket is created
5.  Optional: if True, creates the target bucket if it doesn't exist

### Moving Files

```python title="Move Files in Cloud Storage"
blob = storage.move( # (1)!
    source_file_name="file.txt",
    source_bucket_name="source-bucket",
    target_bucket_name="target-bucket",
    target_file_name="file_moved.txt",  # (2)!
    project_id="my-project",  # (3)!
    region="us-central1",  # (4)!
)
```

1.  Move a file from one bucket to another
2.  Optional: defaults to the source file name
3.  Optional: defaults to the project associated with credentials
4.  Optional: used only if a bucket is created

### Deleting Files

```python title="Delete Files from Cloud Storage"
storage.delete( # (1)!
    file_name="file.txt",
    bucket_name="my-bucket",
)
```

1.  Delete a file

### Listing Files

```python title="List Files in Cloud Storage"
for blob in storage.list_files(bucket_name="my-bucket"): # (1)!
    print(f"File: {blob.name}")

for blob in storage.list_files(bucket_name="my-bucket", prefix="folder/"): # (2)!
    print(f"File: {blob.name}")
```

1.  List all files in a bucket
2.  List files with a specific prefix

### Getting a File

```python title="Get a File from Cloud Storage"
blob = storage.get_file(uri="gs://my-bucket/file.txt") # (1)!
```

1.  Get a file by its GCS URI

### Getting a Download URL

```python title="Get a Download URL for a File"
# Generate a signed URL for downloading a file (1)!
url = storage.get_download_url(
    bucket_name="my-bucket",
    blob_name="file.txt",
    expiration=timedelta(minutes=30),  # (2)!
    version="v4",  # (3)!
)
```

1.  Generate a signed URL for downloading a file
2.  Optional: defaults to 5 minutes
3.  Optional: defaults to "v4"

### Getting a GCS URI

```python title="Get GCS URI for a Blob"
uri = storage.get_uri(blob) # (1)!
```

1.  Get the GCS URI for a blob: "gs://my-bucket/file.txt

## Error Handling

The CloudStorage class handles common errors and converts them to more specific exceptions:

```python title="Error Handling for Cloud Storage"
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