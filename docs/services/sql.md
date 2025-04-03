# Cloud SQL

Cloud SQL is a fully managed relational database service for MySQL, PostgreSQL, and SQL Server. The `CloudSQL` class in gcp-pilot provides a high-level interface for interacting with Google Cloud SQL.

## Installation

To use the Cloud SQL functionality, you need to install gcp-pilot:

```bash
pip install gcp-pilot
```

## Usage

### Initialization

```python
from gcp_pilot.sql import CloudSQL

# Initialize with default credentials
sql = CloudSQL()

# Initialize with specific project
sql = CloudSQL(project_id="my-project")

# Initialize with service account impersonation
sql = CloudSQL(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

### Managing Instances

#### Listing Instances

```python
# List all SQL instances in a project
instances = sql.list_instances(
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
for instance in instances:
    print(f"Instance: {instance['name']}")
    print(f"State: {instance['state']}")
    print(f"Database Version: {instance['databaseVersion']}")
    print(f"Region: {instance['region']}")
```

#### Getting an Instance

```python
# Get information about a specific SQL instance
instance = sql.get_instance(
    name="my-instance",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Instance: {instance['name']}")
print(f"State: {instance['state']}")
print(f"Database Version: {instance['databaseVersion']}")
print(f"Region: {instance['region']}")
```

#### Creating an Instance

```python
# Create a new SQL instance
instance = sql.create_instance(
    name="my-instance",
    version="MYSQL_5_7",  # Database version (e.g., MYSQL_5_7, POSTGRES_13, SQLSERVER_2019_STANDARD)
    tier="db-n1-standard-1",  # Machine type (e.g., db-n1-standard-1, db-custom-2-7680)
    region="us-central1",  # Region where the instance will be created
    ha=False,  # Optional: if True, enables high availability
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    exists_ok=True,  # Optional: if True, returns the existing instance if it already exists
    wait_ready=True,  # Optional: if True, waits for the instance to be ready before returning
)
print(f"Instance created: {instance['name']}")
print(f"State: {instance['state']}")
```

### Managing Databases

#### Getting a Database

```python
# Get information about a specific database in an instance
database = sql.get_database(
    instance="my-instance",
    database="my-database",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Database: {database['name']}")
print(f"Instance: {database['instance']}")
print(f"Charset: {database['charset']}")
print(f"Collation: {database['collation']}")
```

#### Creating a Database

```python
# Create a new database in an instance
database = sql.create_database(
    name="my-database",
    instance="my-instance",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    exists_ok=True,  # Optional: if True, returns the existing database if it already exists
)
print(f"Database created: {database['name']}")
```

### Managing Users

#### Listing Users

```python
# List all users in an instance
users = sql.list_users(
    instance="my-instance",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
for user in users:
    print(f"User: {user['name']}")
    print(f"Host: {user.get('host', '%')}")
```

#### Creating a User

```python
# Create a new user in an instance
user = sql.create_user(
    name="my-user",
    password="my-password",
    instance="my-instance",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"User created: {user['name']}")
```

### Managing SSL Certificates

#### Creating an SSL Certificate

```python
# Create a new SSL certificate for an instance
cert = sql.create_ssl_cert(
    instance="my-instance",
    ssl_name="my-cert",  # Optional: defaults to a random UUID
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
print(f"Certificate created: {cert['commonName']}")
print(f"Certificate valid from: {cert['validFrom']}")
print(f"Certificate valid until: {cert['validUntil']}")
print(f"Certificate SHA1 fingerprint: {cert['sha1Fingerprint']}")
print(f"Certificate private key: {cert['privateKey']}")  # This is only returned once when the certificate is created
print(f"Certificate server CA: {cert['serverCaCert']}")
```

#### Listing SSL Certificates

```python
# List all SSL certificates for an instance
certs = sql.list_ssl_certs(
    instance="my-instance",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
)
for cert in certs:
    print(f"Certificate: {cert['commonName']}")
    print(f"Certificate valid from: {cert['validFrom']}")
    print(f"Certificate valid until: {cert['validUntil']}")
    print(f"Certificate SHA1 fingerprint: {cert['sha1Fingerprint']}")
```

#### Deleting an SSL Certificate

```python
# Delete an SSL certificate from an instance
sql.delete_ssl_cert(
    instance="my-instance",
    ssl_name="my-cert",
    project_id="my-project",  # Optional: defaults to the project associated with credentials
    not_found_ok=True,  # Optional: if True, doesn't raise an error if the certificate doesn't exist
)
```

## Error Handling

The CloudSQL class handles common errors and converts them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    sql.get_instance(name="non-existent-instance")
except exceptions.NotFound:
    print("Instance not found")

try:
    sql.create_instance(name="existing-instance", version="MYSQL_5_7", tier="db-n1-standard-1", region="us-central1", exists_ok=False)
except exceptions.AlreadyExists:
    print("Instance already exists")

try:
    sql.create_instance(name="recently-deleted-instance", version="MYSQL_5_7", tier="db-n1-standard-1", region="us-central1")
except exceptions.DeletedRecently:
    print("Instance was recently deleted and cannot be recreated yet")

try:
    sql.create_database(name="my-database", instance="not-ready-instance")
except exceptions.HttpError as e:
    if "is not running" in str(e):
        print("Instance is not ready yet")
```

## Working with Service Account Impersonation

Service account impersonation allows you to act as a service account without having its key file. This is a more secure approach than downloading and storing service account keys.

```python
# Initialize with service account impersonation
sql = CloudSQL(impersonate_account="service-account@project-id.iam.gserviceaccount.com")

# Now all operations will be performed as the impersonated service account
instances = sql.list_instances()
```

For more information on service account impersonation, see the [Authentication](../authentication.md) documentation.

## Best Practices

Here are some best practices for working with Cloud SQL:

1. **Use appropriate instance sizes**: Choose instance sizes based on your workload requirements to optimize cost and performance.
2. **Enable high availability for production**: Use the `ha=True` parameter when creating instances for production workloads.
3. **Use SSL certificates**: Create and use SSL certificates to secure connections to your databases.
4. **Implement proper backup strategies**: Set up automated backups for your databases.
5. **Monitor your instances**: Set up monitoring and alerting for your Cloud SQL instances.
6. **Use connection pooling**: Implement connection pooling to improve performance and reduce resource usage.
7. **Secure your instances**: Use strong passwords, limit network access, and follow the principle of least privilege when granting permissions.