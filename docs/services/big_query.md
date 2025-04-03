# BigQuery

BigQuery is a fully managed, serverless data warehouse that enables scalable analysis over petabytes of data. The `BigQuery` class in gcp-pilot provides a high-level interface for interacting with Google Cloud BigQuery.

## Installation

To use the BigQuery functionality, you need to install gcp-pilot with the bigquery extra:

```bash
pip install gcp-pilot[bigquery]
```

## Usage

### Initialization

```python
from gcp_pilot.big_query import BigQuery

# Initialize with default credentials
bq = BigQuery()

# Initialize with specific project
bq = BigQuery(project_id="my-project")

# Initialize with specific location
bq = BigQuery(location="us-central1")

# Initialize with service account impersonation
bq = BigQuery(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

### Managing Datasets and Tables

#### Listing Datasets

```python
# List all datasets in the project
datasets = bq.list_datasets()
for dataset in datasets:
    print(f"Dataset: {dataset.dataset_id}")
```

#### Listing Tables

```python
# List all tables in a dataset
tables = bq.list_tables(dataset_id="my_dataset")
for table in tables:
    print(f"Table: {table.table_id}")
```

#### Getting a Table

```python
# Get a table
table = bq.get_table(
    table_name="my_table",
    dataset_name="my_dataset",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Table: {table.table_id}")
print(f"Schema: {table.schema}")
print(f"Rows: {table.num_rows}")
```

#### Creating a Table

```python
from google.cloud import bigquery

# Define the schema
schema = [
    bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("age", "INTEGER", mode="REQUIRED"),
    bigquery.SchemaField("email", "STRING", mode="NULLABLE"),
]

# Create a table reference
dataset_ref = bq.client.dataset("my_dataset")
table_ref = dataset_ref.table("my_table")

# Create a table object
table = bigquery.Table(table_ref, schema=schema)

# Create the table
bq.create_table(table)
```

#### Deleting a Table

```python
from google.cloud import bigquery

# Create a table reference
dataset_ref = bq.client.dataset("my_dataset")
table_ref = dataset_ref.table("my_table")

# Create a table object
table = bigquery.Table(table_ref)

# Delete the table
bq.delete_table(table)
```

### Executing Queries

```python
# Execute a simple query
results = bq.execute("SELECT * FROM `my_dataset.my_table` LIMIT 10")
for row in results:
    print(row)

# Execute a query with parameters
results = bq.execute(
    "SELECT * FROM `my_dataset.my_table` WHERE name = @name",
    params={"name": "John"},
)
for row in results:
    print(row)

# Execute a query and write the results to a destination table
bq.execute(
    "SELECT * FROM `my_dataset.my_table`",
    destination_table_name="my_destination_table",
    destination_dataset_name="my_destination_dataset",
    destination_project="my-destination-project",  # Optional: defaults to the project associated with credentials
    truncate=True,  # Optional: if True, truncates the destination table before writing
)
```

### Inserting Data

```python
# Insert rows into a table
rows = [
    {"name": "John", "age": 30, "email": "john@example.com"},
    {"name": "Jane", "age": 25, "email": "jane@example.com"},
]
errors = bq.insert_rows(
    dataset_name="my_dataset",
    table_name="my_table",
    rows=rows,
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
if errors:
    print(f"Errors: {errors}")
```

### Loading Data

```python
# Load data from a local file
bq.load(
    table_name="my_table",
    filename="/path/to/data.csv",
    dataset_name="my_dataset",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    schema=[
        bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("age", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("email", "STRING", mode="NULLABLE"),
    ],
    wait=True,  # Optional: if True, waits for the load job to complete
    truncate=True,  # Optional: if True, truncates the table before loading
)

# Load data from a file in Google Cloud Storage
bq.load(
    table_name="my_table",
    filename="gs://my-bucket/data.csv",
    dataset_name="my_dataset",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    schema=[
        bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("age", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("email", "STRING", mode="NULLABLE"),
    ],
    wait=True,  # Optional: if True, waits for the load job to complete
)

# Load data from a local file, uploading it to Google Cloud Storage first
bq.load(
    table_name="my_table",
    filename="/path/to/data.csv",
    dataset_name="my_dataset",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    schema=[
        bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("age", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("email", "STRING", mode="NULLABLE"),
    ],
    gcs_bucket="my-bucket",  # Uploads the file to this bucket before loading
    wait=True,  # Optional: if True, waits for the load job to complete
)
```

### Copying Tables

```python
# Copy a table
bq.copy(
    source_dataset_name="my_source_dataset",
    source_table_name="my_source_table",
    destination_dataset_name="my_destination_dataset",
    destination_table_name="my_destination_table",
    destination_project="my-destination-project",  # Optional: defaults to the project associated with credentials
    wait=True,  # Optional: if True, waits for the copy job to complete
)
```

### Working with External Data Sources

```python
# Add an external Google Cloud Storage data source
bq.add_external_gcs_source(
    gcs_url="gs://my-bucket/data.csv",
    dataset_name="my_dataset",
    table_name="my_external_table",
    skip_rows=1,  # Optional: number of header rows to skip
    delimiter=",",  # Optional: field delimiter
    quote='"',  # Optional: quote character
    source_format="CSV",  # Optional: source format (CSV, NEWLINE_DELIMITED_JSON, AVRO, etc.)
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
```

### Utility Methods

```python
# Convert a datetime to a string format suitable for BigQuery
from datetime import datetime

dt = datetime.now()
date_str = BigQuery.date_to_str(dt)
print(f"Date string: {date_str}")

# Convert a datetime to a string format suitable for BigQuery table suffixes
date_str = BigQuery.date_to_str(dt, table_suffix=True)
print(f"Table suffix: {date_str}")
```

## Error Handling

The BigQuery class handles common errors and converts them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    bq.get_table(table_name="non_existent_table", dataset_name="my_dataset")
except exceptions.NotFound:
    print("Table not found")

try:
    bq.execute("SELECT * FROM `non_existent_dataset.non_existent_table`")
except exceptions.NotFound:
    print("Table or dataset not found")
```