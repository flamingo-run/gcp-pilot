# Healthcare API

The Healthcare API is a service that enables secure storage, processing, and machine learning for healthcare data. The `HealthcareBase` and `HealthcareFHIR` classes in gcp-pilot provide high-level interfaces for interacting with Google Cloud Healthcare API, with a focus on FHIR (Fast Healthcare Interoperability Resources) data.

## Installation

To use the Healthcare API functionality, you need to install gcp-pilot with the healthcare extra:

```bash title="Install Healthcare extra"
pip install gcp-pilot[healthcare]
```

## Usage

### Initialization

```python title="Initialize HealthcareFHIR Client"
from gcp_pilot.healthcare import HealthcareFHIR

healthcare = HealthcareFHIR() # (1)!
healthcare = HealthcareFHIR(project_id="my-project") # (2)!
healthcare = HealthcareFHIR(location="us-central1") # (3)!
healthcare = HealthcareFHIR(impersonate_account="service-account@project-id.iam.gserviceaccount.com") # (4)!
```

1.  Initialize with default credentials
2.  Initialize with specific project
3.  Initialize with specific location
4.  Initialize with service account impersonation

!!! note "Region Availability"
    The Healthcare API is only available in specific regions. If you specify a region that is not supported, the API will default to the multi-region "us".

### Managing Datasets

#### Listing Datasets

```python title="List Healthcare Datasets"
datasets = healthcare.list_datasets( # (1)!
    project_id="my-project",  # (2)!
    location="us-central1",  # (3)!
)
for dataset in datasets:
    print(f"Dataset: {dataset['name']}")
```

1.  List all datasets in a project
2.  Optional: defaults to the project associated with credentials
3.  Optional: defaults to the default location

#### Getting a Dataset

```python title="Get a Healthcare Dataset"
dataset = healthcare.get_dataset( # (1)!
    name="my-dataset",
    project_id="my-project",  # (2)!
    location="us-central1",  # (3)!
)
print(f"Dataset: {dataset['name']}")
```

1.  Get information about a specific dataset
2.  Optional: defaults to the project associated with credentials
3.  Optional: defaults to the default location

#### Creating a Dataset

```python title="Create a Healthcare Dataset"
dataset = healthcare.create_dataset( # (1)!
    name="my-dataset",
    project_id="my-project",  # (2)!
    location="us-central1",  # (3)!
)
print(f"Dataset created: {dataset['name']}")
```

1.  Create a new dataset
2.  Optional: defaults to the project associated with credentials
3.  Optional: defaults to the default location

#### Deleting a Dataset

```python title="Delete a Healthcare Dataset"
healthcare.delete_dataset( # (1)!
    name="my-dataset",
    project_id="my-project",  # (2)!
    location="us-central1",  # (3)!
)
```

1.  Delete a dataset
2.  Optional: defaults to the project associated with credentials
3.  Optional: defaults to the default location

### Managing FHIR Stores

#### Listing FHIR Stores

```python title="List FHIR Stores"
stores = healthcare.list_stores( # (1)!
    dataset_name="my-dataset",
    project_id="my-project",  # (2)!
    location="us-central1",  # (3)!
)
for store in stores:
    print(f"Store: {store['name']}")
```

1.  List all FHIR stores in a dataset
2.  Optional: defaults to the project associated with credentials
3.  Optional: defaults to the default location

#### Getting a FHIR Store

```python title="Get a FHIR Store"
store = healthcare.get_store( # (1)!
    name="my-store",
    dataset_name="my-dataset",
    project_id="my-project",  # (2)!
    location="us-central1",  # (3)!
)
print(f"Store: {store['name']}")
```

1.  Get information about a specific FHIR store
2.  Optional: defaults to the project associated with credentials
3.  Optional: defaults to the default location

#### Creating a FHIR Store

```python title="Create a FHIR Store"
store = healthcare.create_store( # (1)!
    name="my-store",
    dataset_name="my-dataset",
    labels={"environment": "production"},  # (2)!
    enable_upsert=True,  # (3)!
    notify_pubsub_topic="my-topic",  # (4)!
    notify_pubsub_full_resource=False,  # (5)!
    notify_pubsub_deletion=True,  # (6)!
    export_to_bigquery_dataset="my-bq-dataset",  # (7)!
    project_id="my-project",  # (8)!
    location="us-central1",  # (9)!
    version="R4",  # (10)!
)
print(f"Store created: {store['name']}")
```

1.  Create a new FHIR store
2.  Optional: labels to apply to the store
3.  Optional: if True, enables update-as-create semantics
4.  Optional: Pub/Sub topic for notifications
5.  Optional: if True, sends the full resource in notifications
6.  Optional: if True, sends notifications for deletions
7.  Optional: BigQuery dataset for streaming exports
8.  Optional: defaults to the project associated with credentials
9.  Optional: defaults to the default location
10. Optional: FHIR version, defaults to "R4"

#### Updating a FHIR Store

```python title="Update a FHIR Store"
store = healthcare.update_store( # (1)!
    name="my-store",
    dataset_name="my-dataset",
    labels={"environment": "staging"},  # (2)!
    notify_pubsub_topic="my-new-topic",  # (3)!
    notify_pubsub_full_resource=True,  # (4)!
    notify_pubsub_deletion=True,  # (5)!
    export_to_bigquery_dataset="my-new-bq-dataset",  # (6)!
    project_id="my-project",  # (7)!
    location="us-central1",  # (8)!
)
print(f"Store updated: {store['name']}")
```

1.  Update an existing FHIR store
2.  Optional: new labels to apply to the store
3.  Optional: new Pub/Sub topic for notifications
4.  Optional: if True, sends the full resource in notifications
5.  Optional: if True, sends notifications for deletions
6.  Optional: new BigQuery dataset for streaming exports
7.  Optional: defaults to the project associated with credentials
8.  Optional: defaults to the default location

#### Deleting a FHIR Store

```python title="Delete a FHIR Store"
healthcare.delete_store( # (1)!
    name="my-store",
    dataset_name="my-dataset",
    project_id="my-project",  # (2)!
    location="us-central1",  # (3)!
)
```

1.  Delete a FHIR store
2.  Optional: defaults to the project associated with credentials
3.  Optional: defaults to the default location

### Managing FHIR Resources

#### Listing Resources

```python title="List FHIR Resources"
from fhir.resources.patient import Patient

patients = healthcare.list_resources( # (1)!
    resource_type=Patient,
    store_name="my-store",
    dataset_name="my-dataset",
    project_id="my-project",  # (2)!
    location="us-central1",  # (3)!
    query={"name": "John"},  # (4)!
    limit=100,  # (5)!
    cursor=None,  # (6)!
)

if patients:
    for patient in patients: # (7)!
        print(f"Name: {patient.name[0].given[0]} {patient.name[0].family}")
else:
    print("No patients found")
```

1.  List all FHIR resources of a specific type in a store
2.  Optional: defaults to the project associated with credentials
3.  Optional: defaults to the default location
4.  Optional: query parameters to filter resources
5.  Optional: maximum number of resources to return per page
6.  Optional: cursor for pagination
7.  Iterate through all patients

#### Getting a Resource

```python title="Get a FHIR Resource"
from fhir.resources.patient import Patient

patient = healthcare.get_resource( # (1)!
    resource_id="patient-id",
    resource_type=Patient,
    store_name="my-store",
    dataset_name="my-dataset",
    project_id="my-project",  # (2)!
    location="us-central1",  # (3)!
)
print(f"Patient: {patient.id}")

if patient and patient.name and patient.name[0].given and patient.name[0].family: # (4)!
    print(f"Name: {patient.name[0].given[0]} {patient.name[0].family}")
```

1.  Get a specific FHIR resource
2.  Optional: defaults to the project associated with credentials
3.  Optional: defaults to the default location
4.  Get the first patient

#### Creating a Resource

```python title="Create a FHIR Resource"
from fhir.resources.patient import Patient

patient = Patient.construct(
    name=[{"given": ["John"], "family": "Doe"}],
    gender="male",
    birthDate="1990-01-01",
) # (1)!

created_patient = healthcare.create_resource( # (2)!
    resource=patient,
    store_name="my-store",
    dataset_name="my-dataset",
    project_id="my-project",  # (3)!
    location="us-central1",  # (4)!
)
print(f"Patient created: {created_patient.id}")
```

1.  Create a Patient resource using the fhir.resources library
2.  Create a new FHIR resource
3.  Optional: defaults to the project associated with credentials
4.  Optional: defaults to the default location

#### Updating a Resource

```python title="Update a FHIR Resource (Full Update)"
patient.name[0].family = "Smith" # (1)!
updated_patient = healthcare.update_resource( # (2)!
    resource=patient,
    store_name="my-store",
    dataset_name="my-dataset",
    project_id="my-project",  # (3)!
    location="us-central1",  # (4)!
)
print(f"Patient updated: {updated_patient.id}")
```

1.  Modify the Patient resource
2.  Update an existing FHIR resource (full update)
3.  Optional: defaults to the project associated with credentials
4.  Optional: defaults to the default location

#### Patch Updating a Resource

```python title="Patch Update a FHIR Resource"
patch = [
    {"op": "replace", "path": "/birthDate", "value": "1991-01-01"},
    {"op": "add", "path": "/telecom/-", "value": {"system": "phone", "value": "555-555-5555"}}
] # (1)!

updated_patient = healthcare.patch_resource( # (2)!
    resource_id="patient-id",
    resource_type=Patient,
    patch=patch,
    store_name="my-store",
    dataset_name="my-dataset",
    project_id="my-project",  # (3)!
    location="us-central1",  # (4)!
)
print(f"Patient patched: {updated_patient.id}")
```

1.  Create a JSON patch
2.  Patch an existing FHIR resource
3.  Optional: defaults to the project associated with credentials
4.  Optional: defaults to the default location

#### Conditional Patch Updating a Resource

```python title="Conditional Patch Update a FHIR Resource"
patch = [
    {"op": "replace", "path": "/birthDate", "value": "1992-01-01"}
] # (1)!

updated_patient = healthcare.patch_resource_conditional( # (2)!
    resource_type=Patient,
    patch=patch,
    store_name="my-store",
    dataset_name="my-dataset",
    query={"identifier": "http://example.org/fhir/ids|12345"},  # (3)!
    project_id="my-project",  # (4)!
    location="us-central1",  # (5)!
)
print(f"Patient conditionally patched: {updated_patient.id}")
```

1.  Create a JSON patch
2.  Conditionally patch an existing FHIR resource
3.  Optional: query to find existing resource
4.  Optional: defaults to the project associated with credentials
5.  Optional: defaults to the default location

#### Upserting a Resource

```python title="Upsert a FHIR Resource"
patient = Patient.construct(
    id="patient-id",
    name=[{"given": ["John"], "family": "Doe"}],
    gender="male",
    birthDate="1990-01-01",
) # (1)!

patient = healthcare.upsert_resource( # (2)!
    resource=patient,
    store_name="my-store",
    dataset_name="my-dataset",
    query={"identifier": "http://example.org/fhir/ids|12345"},  # (3)!
    project_id="my-project",  # (4)!
    location="us-central1",  # (5)!
)
print(f"Patient created or updated: {patient.id}")
```

1.  Create a Patient resource
2.  Create or update a FHIR resource (upsert)
3.  Optional: query to find existing resource
4.  Optional: defaults to the project associated with credentials
5.  Optional: defaults to the default location

#### Deleting a Resource

```python title="Delete a FHIR Resource"
healthcare.delete_resource( # (1)!
    resource_id="patient-id",
    resource_type=Patient,
    store_name="my-store",
    dataset_name="my-dataset",
    project_id="my-project",  # (2)!
    location="us-central1",  # (3)!
)
```

1.  Delete a FHIR resource
2.  Optional: defaults to the project associated with credentials
3.  Optional: defaults to the default location

### Resource History

```python title="Get FHIR Resource History"
history = healthcare.get_resource_history( # (1)!
    resource_id="patient-id",
    resource_type=Patient,
    store_name="my-store",
    dataset_name="my-dataset",
    project_id="my-project",  # (2)!
    location="us-central1",  # (3)!
    since="2023-01-01T00:00:00Z",  # (4)!
    limit=10,  # (5)!
)

for version in history: # (6)!
    print(f"Version: {version.id}")
    if version.name and version.name[0].given and version.name[0].family:
        print(f"Name: {version.name[0].given[0]} {version.name[0].family}")
```

1.  Get the history of a Patient resource
2.  Optional: defaults to the project associated with credentials
3.  Optional: defaults to the default location
4.  Optional: only return versions since this timestamp
5.  Optional: limit the number of versions returned
6.  Iterate through versions

### Validating Resources

```python title="Validate a FHIR Resource"
try: # (1)!
    healthcare.validate_resource(
        resource=patient, # (2)!
        store_name="my-store",
        dataset_name="my-dataset",
        project_id="my-project",  # (3)!
        location="us-central1",  # (4)!
    )
    print("Resource is valid")
except exceptions.InvalidInput as e:
    print(f"Validation errors: {e}")
```

1.  Validate a Patient resource
2.  The FHIR resource object to validate
3.  Optional: defaults to the project associated with credentials
4.  Optional: defaults to the default location

### Importing and Exporting Resources

#### Exporting Resources

```python title="Export FHIR Resources"
export_info = healthcare.export_resources( # (1)!
    output_gcs_uri="gs://my-bucket/fhir-export/",
    store_name="my-store",
    dataset_name="my-dataset",
    project_id="my-project",  # (2)!
    location="us-central1",  # (3)!
    resource_names=["Patient", "Observation"],  # (4)!
)
print(f"Export operation ID: {export_info['operation_id']}")

operation = healthcare.get_operation(export_info['operation_id']) # (5)!
print(f"Operation status: {operation['metadata']['state']}")
```

1.  Export FHIR resources to Google Cloud Storage
2.  Optional: defaults to the project associated with credentials
3.  Optional: defaults to the default location
4.  Optional: specific resource types to export
5.  Check the status of the export operation

#### Importing Resources

```python title="Import FHIR Resources"
import_operation = healthcare.import_resources( # (1)!
    source_gcs_uri="gs://my-bucket/fhir-import/",
    store_name="my-store",
    dataset_name="my-dataset",
    project_id="my-project",  # (2)!
    location="us-central1",  # (3)!
)
print(f"Import operation: {import_operation['name']}")
```

1.  Import FHIR resources from Google Cloud Storage
2.  Optional: defaults to the project associated with credentials
3.  Optional: defaults to the default location

### Natural Language Processing

```python title="Analyze Healthcare Entities"
entities = healthcare.analyze_entities( # (1)!
    content="Patient has a history of hypertension and type 2 diabetes.",
    use_idc10=True,  # (2)!
    use_snomed=True,  # (3)!
    location="us-central1",  # (4)!
    project_id="my-project",  # (5)!
    fhir_output=True,  # (6)!
)
print(f"Entities: {entities}")
```

1.  Analyze clinical text for entities
2.  Optional: if True, includes ICD-10 codes
3.  Optional: if True, includes SNOMED CT codes
4.  Optional: defaults to the default location
5.  Optional: defaults to the project associated with credentials
6.  Optional: if True, returns results as FHIR resources

### Configuring Search

```python title="Configure FHIR Store Search"
search_config = {
    "searchParameters": [
        {
            "name": "patient-name",
            "definition": "Patient.name",
            "type": "string"
        }
    ]
} # (1)!

search_config = healthcare.configure_search( # (2)!
    config=search_config,
    store_name="my-store",
    dataset_name="my-dataset",
    validate_only=False,  # (3)!
    project_id="my-project",  # (4)!
    location="us-central1",  # (5)!
)
print(f"Search configuration: {search_config}")
```

1.  Define the search configuration
2.  Configure search parameters for a FHIR store
3.  Optional: if True, validates the configuration without applying it
4.  Optional: defaults to the project associated with credentials
5.  Optional: defaults to the default location

## Error Handling

The Healthcare classes handle common errors and convert them to more specific exceptions:

```python title="Error Handling for Healthcare API"
from gcp_pilot import exceptions

try:
    healthcare.get_dataset(name="non-existent-dataset")
except exceptions.NotFound:
    print("Dataset not found")

try:
    healthcare.create_dataset(name="existing-dataset") # This assumes exists_ok=False or not provided
except exceptions.AlreadyExists:
    print("Dataset already exists")

try:
    healthcare.validate_resource(resource=invalid_patient_resource) # (1)!
except exceptions.InvalidInput as e:
    print(f"Validation errors: {e}")
```

1.  Example: an invalid FHIR resource object

## Working with Service Account Impersonation

Service account impersonation allows you to act as a service account without having its key file. This is a more secure approach than downloading and storing service account keys.

```python title="Using Impersonated Credentials for Healthcare API"
healthcare = HealthcareFHIR(impersonate_account="service-account@project-id.iam.gserviceaccount.com") # (1)!
datasets = healthcare.list_datasets() # (2)!
```

1.  Initialize with service account impersonation
2.  Now all operations will be performed as the impersonated service account

For more information on service account impersonation, see the [Authentication](../authentication.md) documentation.

!!! tip "Best Practices for Healthcare API"
    Here are some best practices for working with the Healthcare API:

    1. **Use appropriate regions**: Choose a region that complies with your data residency requirements and is close to your users.
    2. **Implement proper access controls**: Use IAM to restrict access to healthcare datasets and FHIR stores.
    3. **Enable audit logging**: Set up audit logging to track access to sensitive healthcare data.
    4. **Use FHIR validation**: Validate resources before storing them to ensure data quality.
    5. **Configure notifications**: Set up Pub/Sub notifications for important events like resource creation and deletion.
    6. **Stream to BigQuery**: Enable streaming to BigQuery for real-time analytics on healthcare data.
    7. **Use conditional operations**: Use conditional operations to avoid race conditions when updating resources.
    8. **Implement proper error handling**: Handle errors appropriately, especially for validation and precondition failures.
    9. **Regularly export data**: Set up regular exports to Google Cloud Storage for backup and disaster recovery.
    10. **Monitor API usage**: Set up monitoring and alerting for API usage to detect and respond to issues quickly.
