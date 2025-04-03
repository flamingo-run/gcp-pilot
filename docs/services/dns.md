# Cloud DNS

Cloud DNS is a scalable, reliable, and managed authoritative Domain Name System (DNS) service running on the same infrastructure as Google. The `CloudDNS` class in gcp-pilot provides a high-level interface for interacting with Google Cloud DNS.

## Installation

To use the Cloud DNS functionality, you need to install gcp-pilot with the dns extra:

```bash
pip install gcp-pilot[dns]
```

## Usage

### Initialization

```python
from gcp_pilot.dns import CloudDNS

# Initialize with default credentials
dns = CloudDNS()

# Initialize with specific project
dns = CloudDNS(project_id="my-project")

# Initialize with service account impersonation
dns = CloudDNS(impersonate_account="service-account@project-id.iam.gserviceaccount.com")
```

### Managing DNS Zones

#### Listing Zones

```python
# List all DNS zones in the project
zones = dns.list_zones()
for zone in zones:
    print(f"Zone: {zone.name}, DNS Name: {zone.dns_name}")
```

#### Creating a Zone

```python
# Create a new DNS zone
zone = dns.create_zone(
    name="my-zone",  # The name of the zone in Cloud DNS
    dns_name="example.com.",  # The DNS name of the zone (must end with a period)
    description="My DNS zone",  # Optional: a description for the zone
    exists_ok=True,  # Optional: if True, doesn't raise an error if the zone already exists
)
print(f"Created zone: {zone.name}, DNS Name: {zone.dns_name}")
```

#### Deleting a Zone

```python
# Delete a DNS zone
dns.delete_zone(
    name="my-zone",  # The name of the zone in Cloud DNS
    dns_name="example.com.",  # The DNS name of the zone (must end with a period)
    exists_ok=True,  # Optional: if True, doesn't raise an error if the zone doesn't exist
)
```

### Managing DNS Records

#### Listing Records

```python
# List all records in a zone
records = dns.list_records(
    zone_name="my-zone",  # The name of the zone in Cloud DNS
    zone_dns="example.com.",  # The DNS name of the zone (must end with a period)
)
for record in records:
    print(f"Record: {record.name}, Type: {record.record_type}, Data: {record.rrdatas}")
```

#### Adding Records

```python
from gcp_pilot.dns import CloudDNS, RecordType

# Add an A record
dns.add_record(
    zone_name="my-zone",  # The name of the zone in Cloud DNS
    zone_dns="example.com.",  # The DNS name of the zone (must end with a period)
    name="www",  # The name of the record (without the domain)
    record_type=RecordType.A,  # The type of record
    record_data=["192.0.2.1"],  # The IP address(es) for the A record
    ttl=300,  # Optional: TTL in seconds (default: 300)
    wait=True,  # Optional: wait for the change to propagate (default: True)
    exists_ok=True,  # Optional: don't raise an error if the record already exists (default: True)
)

# Add a CNAME record
dns.add_record(
    zone_name="my-zone",
    zone_dns="example.com.",
    name="blog",
    record_type=RecordType.CNAME,
    record_data=["www.example.com."],  # The target domain (must end with a period)
    ttl=300,
)

# Add an MX record
dns.add_record(
    zone_name="my-zone",
    zone_dns="example.com.",
    name="",  # Empty string for the root domain
    record_type=RecordType.MX,
    record_data=["10 mail.example.com."],  # Priority and mail server
    ttl=3600,
)

# Add a TXT record
dns.add_record(
    zone_name="my-zone",
    zone_dns="example.com.",
    name="",  # Empty string for the root domain
    record_type=RecordType.TXT,
    record_data=["v=spf1 include:_spf.example.com ~all"],
    ttl=3600,
)
```

#### Deleting Records

```python
from gcp_pilot.dns import CloudDNS, RecordType

# Delete an A record
dns.delete_record(
    zone_name="my-zone",  # The name of the zone in Cloud DNS
    zone_dns="example.com.",  # The DNS name of the zone (must end with a period)
    name="www",  # The name of the record (without the domain)
    record_type=RecordType.A,  # The type of record
    wait=True,  # Optional: wait for the change to propagate (default: True)
)

# Delete a CNAME record
dns.delete_record(
    zone_name="my-zone",
    zone_dns="example.com.",
    name="blog",
    record_type=RecordType.CNAME,
)
```

## Record Types

The `RecordType` enum provides the supported DNS record types:

```python
from gcp_pilot.dns import RecordType

# Available record types
RecordType.A      # Address record (maps a domain to an IPv4 address)
RecordType.CNAME  # Canonical name record (maps a domain to another domain)
RecordType.MX     # Mail exchange record (specifies mail servers)
RecordType.TXT    # Text record (stores text information)
```

The `RecordType` class also provides helper methods for preparing record data:

```python
from gcp_pilot.dns import RecordType

# Build a DNS name (ensure it ends with a period)
dns_name = RecordType.build_dns_name("example.com")  # Returns "example.com."
dns_name = RecordType.build_dns_name("example.com.")  # Returns "example.com."

# Prepare record data based on the record type
cname_record = RecordType.prepare(RecordType.CNAME, "example.com")  # Returns "example.com."
```

## Error Handling

The CloudDNS class handles common errors and converts them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    # Try to create a zone that already exists
    dns.create_zone(name="existing-zone", dns_name="example.com.", exists_ok=False)
except exceptions.AlreadyExists:
    print("Zone already exists")

try:
    # Try to add a record that already exists
    dns.add_record(
        zone_name="my-zone",
        zone_dns="example.com.",
        name="www",
        record_type=RecordType.A,
        record_data=["192.0.2.1"],
        exists_ok=False,
    )
except exceptions.AlreadyExists:
    print("Record already exists")

try:
    # Try to delete a zone that doesn't exist
    dns.delete_zone(name="non-existent-zone", dns_name="example.com.", exists_ok=False)
except exceptions.NotFound:
    print("Zone not found")
```

## Waiting for Changes

DNS changes can take time to propagate. By default, the `add_record` and `delete_record` methods wait for the changes to complete before returning. You can disable this behavior by setting `wait=False`:

```python
# Add a record without waiting for the change to complete
dns.add_record(
    zone_name="my-zone",
    zone_dns="example.com.",
    name="www",
    record_type=RecordType.A,
    record_data=["192.0.2.1"],
    wait=False,
)
```

When `wait=True` (the default), the method will poll the change status every 60 seconds until it's complete.