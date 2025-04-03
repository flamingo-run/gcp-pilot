# Healthcare API

The Healthcare API is a service that enables secure storage, processing, and machine learning for healthcare data. The `HealthcareBase` and `HealthcareFHIR` classes in gcp-pilot provide high-level interfaces for interacting with Google Cloud Healthcare API, with a focus on FHIR (Fast Healthcare Interoperability Resources) data.

## Installation

To use the Healthcare API functionality, you need to install gcp-pilot with the healthcare extra:

```bash
pip install gcp-pilot[healthcare]
```

## Usage

### Initialization

```python
from gcp_pilot.healthcare import HealthcareFHIR

# Initialize with default credentials
healthcare = HealthcareFHIR()

# Initialize with specific project
healthcare = HealthcareFHIR(project_id="my-project")

# Initialize with specific location
healthcare = HealthcareFHIR(location="us-central1")

# Initialize with service account impersonation
healthcare = HealthcareFHIR(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

Note: The Healthcare API is only available in specific regions. If you specify a region that is not supported, the API will default to the multi-region "us".

### Managing Datasets

#### Listing Datasets

```python
# List all datasets in a project
datasets = healthcare.list_datasets(
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
)
for dataset in datasets:
    print(f"Dataset: {dataset['name']}")
```

#### Getting a Dataset

```python
# Get information about a specific dataset
dataset = healthcare.get_dataset(
    name="my-dataset",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
)
print(f"Dataset: {dataset['name']}")
```

#### Creating a Dataset

```python
# Create a new dataset
dataset = healthcare.create_dataset(
    name="my-dataset",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
)
print(f"Dataset created: {dataset['name']}")
```

#### Deleting a Dataset

```python
# Delete a dataset
healthcare.delete_dataset(
    name="my-dataset",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
)
```

### Managing FHIR Stores

#### Listing FHIR Stores

```python
# List all FHIR stores in a dataset
stores = healthcare.list_stores(
    dataset_name="my-dataset",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
)
for store in stores:
    print(f"Store: {store['name']}")
```

#### Getting a FHIR Store

```python
# Get information about a specific FHIR store
store = healthcare.get_store(
    name="my-store",
    dataset_name="my-dataset",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
)
print(f"Store: {store['name']}")
```

#### Creating a FHIR Store

```python
# Create a new FHIR store
store = healthcare.create_store(
    name="my-store",
    dataset_name="my-dataset",
    labels={"environment": "production"},  # Optional: labels to apply to the store
    enable_upsert=True,  # Optional: if True, enables update-as-create semantics
    notify_pubsub_topic="my-topic",  # Optional: Pub/Sub topic for notifications
    notify_pubsub_full_resource=False,  # Optional: if True, sends the full resource in notifications
    notify_pubsub_deletion=True,  # Optional: if True, sends notifications for deletions
    export_to_bigquery_dataset="my-bq-dataset",  # Optional: BigQuery dataset for streaming exports
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
    version="R4",  # Optional: FHIR version, defaults to "R4"
)
print(f"Store created: {store['name']}")
```

#### Updating a FHIR Store

```python
# Update an existing FHIR store
store = healthcare.update_store(
    name="my-store",
    dataset_name="my-dataset",
    labels={"environment": "staging"},  # Optional: new labels to apply to the store
    notify_pubsub_topic="my-new-topic",  # Optional: new Pub/Sub topic for notifications
    notify_pubsub_full_resource=True,  # Optional: if True, sends the full resource in notifications
    notify_pubsub_deletion=True,  # Optional: if True, sends notifications for deletions
    export_to_bigquery_dataset="my-new-bq-dataset",  # Optional: new BigQuery dataset for streaming exports
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
)
print(f"Store updated: {store['name']}")
```

#### Deleting a FHIR Store

```python
# Delete a FHIR store
healthcare.delete_store(
    name="my-store",
    dataset_name="my-dataset",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
)
```

### Managing FHIR Resources

#### Listing Resources

```python
from fhir.resources.patient import Patient

# List all Patient resources in a FHIR store
patients = healthcare.list_resources(
    store_name="my-store",
    dataset_name="my-dataset",
    resource_class=Patient,
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
    query={"name": "John"},  # Optional: query parameters to filter resources
    limit=100,  # Optional: maximum number of resources to return per page
    cursor=None,  # Optional: cursor for pagination
)

# Iterate through all patients
for patient in patients:
    print(f"Patient: {patient.id}")
    print(f"Name: {patient.name[0].given[0]} {patient.name[0].family}")

# Get the first patient
try:
    first_patient = patients.first()
    print(f"First patient: {first_patient.id}")
except exceptions.NotFound:
    print("No patients found")
```

#### Getting a Resource

```python
from fhir.resources.patient import Patient

# Get a specific Patient resource
patient = healthcare.get_resource(
    resource_class=Patient,
    resource_id="patient-id",
    store_name="my-store",
    dataset_name="my-dataset",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
)
print(f"Patient: {patient.id}")
print(f"Name: {patient.name[0].given[0]} {patient.name[0].family}")
```

#### Creating a Resource

```python
from fhir.resources.patient import Patient
from fhir.resources.humanname import HumanName
from fhir.resources.identifier import Identifier

# Create a new Patient resource
patient = Patient(
    id="patient-id",
    identifier=[
        Identifier(
            system="http://example.org/fhir/ids",
            value="12345"
        )
    ],
    name=[
        HumanName(
            given=["John"],
            family="Doe"
        )
    ]
)

# Create the patient in the FHIR store
created_patient = healthcare.create_resource(
    resource=patient,
    store_name="my-store",
    dataset_name="my-dataset",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
)
print(f"Patient created: {created_patient.id}")
```

#### Updating a Resource

```python
# Update an existing Patient resource
patient.name[0].family = "Smith"
updated_patient = healthcare.update_resource(
    resource=patient,
    store_name="my-store",
    dataset_name="my-dataset",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
)
print(f"Patient updated: {updated_patient.id}")
```

#### Patch Updating a Resource

```python
# Patch update a Patient resource
updated_patient = healthcare.patch_update(
    resource_class=Patient,
    data={"name": [{"given": ["John"], "family": "Smith"}]},
    resource_id="patient-id",
    store_name="my-store",
    dataset_name="my-dataset",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
)
print(f"Patient patched: {updated_patient.id}")
```

#### Conditional Patch Update

```python
# Conditionally patch update a Patient resource
updated_patient = healthcare.conditional_patch_resource(
    resource_class=Patient,
    query={"identifier": "http://example.org/fhir/ids|12345"},
    json_patch=[
        {"op": "replace", "path": "/name/0/family", "value": "Smith"}
    ],
    store_name="my-store",
    dataset_name="my-dataset",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
)
print(f"Patient conditionally patched: {updated_patient.id}")
```

#### Creating or Updating a Resource

```python
# Create or update a Patient resource
patient = Patient(
    identifier=[
        Identifier(
            system="http://example.org/fhir/ids",
            value="12345"
        )
    ],
    name=[
        HumanName(
            given=["John"],
            family="Doe"
        )
    ]
)

# Create or update the patient in the FHIR store
patient = healthcare.create_or_update_resource(
    resource=patient,
    store_name="my-store",
    dataset_name="my-dataset",
    query={"identifier": "http://example.org/fhir/ids|12345"},  # Optional: query to find existing resource
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
)
print(f"Patient created or updated: {patient.id}")
```

#### Deleting a Resource

```python
# Delete a Patient resource
healthcare.delete_resource(
    resource_class=Patient,
    resource_id="patient-id",
    store_name="my-store",
    dataset_name="my-dataset",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
)
```

### Resource History

```python
# Get the history of a Patient resource
history = healthcare.get_resource_history(
    resource_class=Patient,
    resource_id="patient-id",
    store_name="my-store",
    dataset_name="my-dataset",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
)

for method, version in history:
    print(f"Method: {method}")
    if version:
        print(f"Version: {version.id}")
        print(f"Name: {version.name[0].given[0]} {version.name[0].family}")
```

### Validating Resources

```python
# Validate a Patient resource
try:
    healthcare.validate_resource(
        resource=patient,
        store_name="my-store",
        dataset_name="my-dataset",
        project_id="my-project",  # Optional: defaults to the project associated with credentials
        location="us-central1",  # Optional: defaults to the default location
    )
    print("Resource is valid")
except exceptions.ValidationError as e:
    print(f"Validation errors: {e}")
```

### Importing and Exporting Resources

#### Exporting Resources

```python
# Export FHIR resources to Google Cloud Storage
export_info = healthcare.export_resources(
    gcs_path="my-bucket/exports",
    store_name="my-store",
    dataset_name="my-dataset",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
    resource_names=["Patient", "Observation"],  # Optional: specific resource types to export
)
print(f"Export operation ID: {export_info['operation_id']}")

# Check the status of the export operation
operation = healthcare.get_operation(
    operation_id=export_info["operation_id"],
    dataset_name=export_info["dataset_name"],
    project_id=export_info["project_id"],
    location=export_info["location"],
)
print(f"Operation status: {operation['metadata']['state']}")
```

#### Importing Resources

```python
# Import FHIR resources from Google Cloud Storage
import_operation = healthcare.import_resources(
    gcs_path="my-bucket/imports/resources.ndjson",
    store_name="my-store",
    dataset_name="my-dataset",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
)
print(f"Import operation: {import_operation['name']}")
```

### Natural Language Processing

```python
# Analyze medical entities in text using NLP
entities = healthcare.analyze_entities(
    content="Patient has a history of hypertension and type 2 diabetes.",
    use_idc10=True,  # Optional: if True, includes ICD-10 codes
    use_snomed=True,  # Optional: if True, includes SNOMED CT codes
    location="us-central1",  # Optional: defaults to the default location
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    fhir_output=True,  # Optional: if True, returns results as FHIR resources
)
print(f"Entities: {entities}")
```

### Configuring Search

```python
# Configure search for a FHIR store
search_config = healthcare.configure_search(
    canonical_urls=["http://hl7.org/fhir/StructureDefinition/Patient"],
    store_name="my-store",
    dataset_name="my-dataset",
    validate_only=False,  # Optional: if True, validates the configuration without applying it
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    location="us-central1",  # Optional: defaults to the default location
)
print(f"Search configuration: {search_config}")
```

## Error Handling

The Healthcare classes handle common errors and convert them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    healthcare.get_dataset(name="non-existent-dataset")
except exceptions.NotFound:
    print("Dataset not found")

try:
    healthcare.create_or_update_resource(
        resource=patient,
        store_name="my-store",
        dataset_name="my-dataset",
        query={"identifier": "http://example.org/fhir/ids|12345"},
    )
except exceptions.FailedPrecondition as e:
    print(f"Failed precondition: {e}")

try:
    healthcare.validate_resource(
        resource=invalid_patient,
        store_name="my-store",
        dataset_name="my-dataset",
    )
except exceptions.ValidationError as e:
    print(f"Validation errors: {e}")
```

## Working with Service Account Impersonation

Service account impersonation allows you to act as a service account without having its key file. This is a more secure approach than downloading and storing service account keys.

```python
# Initialize with service account impersonation
healthcare = HealthcareFHIR(impersonate_account="service-account@project-id.iam.gserviceaccount.com")

# Now all operations will be performed as the impersonated service account
datasets = healthcare.list_datasets()
```

For more information on service account impersonation, see the [Authentication](../authentication.md) documentation.

## Best Practices

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
