# Directory

Directory is a service that allows you to manage Google Workspace users and groups. The `Directory` class in gcp-pilot provides a high-level interface for interacting with Google Workspace Directory API.

## Installation

To use the Directory functionality, you need to install gcp-pilot:

```bash
pip install gcp-pilot
```

## Usage

### Initialization

```python
from gcp_pilot.directory import Directory

# Initialize with default credentials and a specific email
directory = Directory(email="admin@example.com")

# Initialize with service account impersonation
directory = Directory(
    email="admin@example.com",
    impersonate_account="service-account@project-id.iam.gserviceaccount.com"
)
```

The `email` parameter should be the email of a Google Workspace admin user that has permissions to manage users and groups.

### Managing Groups

#### Listing Groups

```python
# List all groups in the organization
groups = directory.get_groups()
for group in groups:
    print(f"Group: {group['name']}, Email: {group['email']}")

# List groups in a specific customer
groups = directory.get_groups(customer="C01234567")
for group in groups:
    print(f"Group: {group['name']}, Email: {group['email']}")

# List groups in a specific domain
groups = directory.get_groups(domain="example.com")
for group in groups:
    print(f"Group: {group['name']}, Email: {group['email']}")
```

#### Getting a Group

```python
# Get information about a specific group
group = directory.get_group(group_id="group@example.com")
print(f"Group: {group['name']}")
print(f"Email: {group['email']}")
print(f"Description: {group['description']}")
```

#### Creating and Updating Groups

```python
# Create a new group
group = directory.create_or_update_group(
    email="newgroup@example.com",
    name="New Group",
    description="A new group for testing"
)
print(f"Created group: {group['name']}")

# Update an existing group
group = directory.create_or_update_group(
    email="existinggroup@example.com",
    name="Updated Group Name",
    description="Updated description"
)
print(f"Updated group: {group['name']}")

# Create or update a group with a specific ID
group = directory.create_or_update_group(
    email="group@example.com",
    name="Group Name",
    description="Group description",
    group_id="specific-group-id"
)
```

#### Deleting a Group

```python
# Delete a group
directory.delete_group(group_id="group@example.com")
```

### Managing Group Members

#### Listing Group Members

```python
# List all members of a group
members = directory.get_group_members(group_id="group@example.com")
for member in members:
    print(f"Member: {member['email']}, Role: {member['role']}")
```

#### Adding a Member to a Group

```python
# Add a member to a group with the default role (MEMBER)
directory.add_group_member(
    group_id="group@example.com",
    email="user@example.com"
)

# Add a member to a group with a specific role
directory.add_group_member(
    group_id="group@example.com",
    email="admin@example.com",
    role="OWNER"  # Can be OWNER, MANAGER, or MEMBER
)
```

#### Removing a Member from a Group

```python
# Remove a member from a group
directory.delete_group_member(
    group_id="group@example.com",
    member_id="user@example.com"
)
```

### Managing Users

#### Listing Users

```python
# List all users in the organization
users = directory.get_users()
for user in users:
    print(f"User: {user['name']['fullName']}, Email: {user['primaryEmail']}")

# List users in a specific customer
users = directory.get_users(customer="C01234567")
for user in users:
    print(f"User: {user['name']['fullName']}, Email: {user['primaryEmail']}")

# List users in a specific domain
users = directory.get_users(domain="example.com")
for user in users:
    print(f"User: {user['name']['fullName']}, Email: {user['primaryEmail']}")
```

#### Getting a User

```python
# Get information about a specific user
user = directory.get_user(user_id="user@example.com")
print(f"User: {user['name']['fullName']}")
print(f"Email: {user['primaryEmail']}")
print(f"Is Admin: {user.get('isAdmin', False)}")
print(f"Is Suspended: {user.get('suspended', False)}")
```

#### Creating a User

```python
# Add a new user
user = directory.add_user(
    email="newuser@example.com",
    first_name="John",
    last_name="Doe",
    password="SecurePassword123"
)
print(f"Created user: {user['name']['fullName']}")
```

#### Updating a User

```python
# Update a user's information
user = directory.update_user(
    user_id="user@example.com",
    first_name="Jane",
    last_name="Smith",
    password="NewSecurePassword456"
)
print(f"Updated user: {user['name']['fullName']}")

# Update a user's email
user = directory.update_user(
    user_id="user@example.com",
    email="newuser@example.com"
)
print(f"Updated user email: {user['primaryEmail']}")

# Suspend a user
user = directory.update_user(
    user_id="user@example.com",
    suspended=True
)
print(f"User suspended: {user.get('suspended', False)}")
```

#### Deleting and Undeleting Users

```python
# Delete a user
directory.delete_user(user_id="user@example.com")

# Undelete a recently deleted user
directory.undelete_user(user_id="user@example.com")
```

#### Managing User Status

```python
# Suspend a user
directory.suspend_user(user_id="user@example.com")

# Reestablish (unsuspend) a user
directory.reestablish_user(user_id="user@example.com")

# Make a user an admin
directory.make_admin(user_id="user@example.com")

# Remove admin privileges from a user
directory.unmake_admin(user_id="user@example.com")
```

## Error Handling

The Directory class handles common errors and converts them to more specific exceptions:

```python
from gcp_pilot import exceptions

try:
    directory.get_user(user_id="non-existent-user@example.com")
except exceptions.NotFound:
    print("User not found")

try:
    directory.get_group(group_id="non-existent-group@example.com")
except exceptions.NotFound:
    print("Group not found")
```

## Authentication and Permissions

To use the Directory API, you need:

1. A Google Workspace account with admin privileges
2. The Directory API enabled in your Google Cloud project
3. A service account with domain-wide delegation enabled
4. The service account granted the necessary OAuth scopes in the Google Workspace Admin Console

The required OAuth scopes for the Directory API include:
- `https://www.googleapis.com/auth/admin.directory.user`
- `https://www.googleapis.com/auth/admin.directory.group`

For more information on setting up authentication, see the [Authentication](../authentication.md) documentation.