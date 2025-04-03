# Google People API

Google People API is a service that provides access to information about profiles and contacts. The `People` class in gcp-pilot provides a high-level interface for interacting with Google People API.

## Installation

To use the People API functionality, you need to install gcp-pilot:

```bash
pip install gcp-pilot
```

## Usage

### Initialization

```python
from gcp_pilot.people import People

# Initialize with a specific email
people = People(email="user@example.com")

# Initialize with service account impersonation
people = People(
    email="user@example.com",
    impersonate_account="service-account@project-id.iam.gserviceaccount.com"
)
```

The `email` parameter is required and specifies the user whose contacts will be accessed.

### Getting People

You can retrieve people from the directory:

```python
# Get all people in the directory
all_people = people.get_people()
for person in all_people:
    print(f"Person: {person['names'][0]['displayName'] if 'names' in person else 'Unknown'}")
    print(f"Email: {person['emailAddresses'][0]['value'] if 'emailAddresses' in person else 'Unknown'}")

# Search for people by query
search_results = people.get_people(query="John")
for person in search_results:
    print(f"Person: {person['names'][0]['displayName'] if 'names' in person else 'Unknown'}")
    print(f"Email: {person['emailAddresses'][0]['value'] if 'emailAddresses' in person else 'Unknown'}")

# Get specific fields for people
specific_fields = people.get_people(fields=["names", "emailAddresses", "phoneNumbers"])
for person in specific_fields:
    print(f"Person: {person['names'][0]['displayName'] if 'names' in person else 'Unknown'}")
    print(f"Email: {person['emailAddresses'][0]['value'] if 'emailAddresses' in person else 'Unknown'}")
    if "phoneNumbers" in person:
        print(f"Phone: {person['phoneNumbers'][0]['value']}")
```

### Available Fields

The People API provides access to various fields of information about people. The `USER_FIELDS` constant in the `people` module lists all available fields:

```python
from gcp_pilot.people import USER_FIELDS

print(f"Available fields: {USER_FIELDS}")
```

The available fields include:

- `addresses`: Postal addresses
- `ageRanges`: Age ranges
- `biographies`: Biographies
- `birthdays`: Birthdays
- `calendarUrls`: Calendar URLs
- `clientData`: Client data
- `coverPhotos`: Cover photos
- `emailAddresses`: Email addresses
- `events`: Events
- `externalIds`: External IDs
- `genders`: Genders
- `imClients`: IM clients
- `interests`: Interests
- `locales`: Locales
- `locations`: Locations
- `memberships`: Memberships
- `metadata`: Metadata
- `miscKeywords`: Miscellaneous keywords
- `names`: Names
- `nicknames`: Nicknames
- `occupations`: Occupations
- `organizations`: Organizations
- `phoneNumbers`: Phone numbers
- `photos`: Photos
- `relations`: Relations
- `sipAddresses`: SIP addresses
- `skills`: Skills
- `urls`: URLs
- `userDefined`: User-defined fields

You can specify which fields to retrieve by passing a list of field names to the `fields` parameter of the `get_people` method.

## Example: Finding a Person by Email

```python
from gcp_pilot.people import People

# Initialize the People API client
people = People(email="user@example.com")

# Search for a person by email
search_results = people.get_people(query="john@example.com", fields=["names", "emailAddresses"])
for person in search_results:
    if "emailAddresses" in person:
        for email in person["emailAddresses"]:
            if email["value"].lower() == "john@example.com":
                print(f"Found person: {person['names'][0]['displayName'] if 'names' in person else 'Unknown'}")
                break
```

## Example: Getting Organization Information

```python
from gcp_pilot.people import People

# Initialize the People API client
people = People(email="user@example.com")

# Get organization information for people
org_info = people.get_people(fields=["names", "organizations"])
for person in org_info:
    print(f"Person: {person['names'][0]['displayName'] if 'names' in person else 'Unknown'}")
    if "organizations" in person:
        for org in person["organizations"]:
            print(f"  Organization: {org.get('name', 'Unknown')}")
            print(f"  Title: {org.get('title', 'Unknown')}")
            print(f"  Department: {org.get('department', 'Unknown')}")
```

## Error Handling

The People class handles common errors and converts them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    people = People(email="user@example.com")
    results = people.get_people(query="invalid query")
except exceptions.HttpError as e:
    print(f"HTTP error: {e}")
except Exception as e:
    print(f"Error: {e}")
```

## Working with Service Account Impersonation

Service account impersonation allows you to act as a service account without having its key file. This is a more secure approach than downloading and storing service account keys.

```python
# Initialize with service account impersonation
people = People(
    email="user@example.com",
    impersonate_account="service-account@project-id.iam.gserviceaccount.com"
)

# Now all operations will be performed as the impersonated service account
results = people.get_people()
```

For more information on service account impersonation, see the [Authentication](../authentication.md) documentation.

## Required Permissions

To use the People API, the service account or user must have the following permissions:

- `https://www.googleapis.com/auth/contacts`: For read/write access to the user's contacts
- `https://www.googleapis.com/auth/directory.readonly`: For read-only access to the user's domain directory

These permissions are automatically requested when you initialize the `People` class.

## Domain-Wide Delegation

If you're using a service account to access the People API, you'll need to set up domain-wide delegation in your Google Workspace domain. This allows the service account to impersonate users in your domain.

For more information on setting up domain-wide delegation, see the [Authentication](../authentication.md) documentation.