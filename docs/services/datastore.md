# Datastore

Datastore is a highly scalable NoSQL database for your applications. The `datastore` module in gcp-pilot provides an ORM-like interface for interacting with Google Cloud Datastore.

## Installation

To use the Datastore functionality, you need to install gcp-pilot with the datastore extra:

```bash
pip install gcp-pilot[datastore]
```

## Usage

The `datastore` module provides a way to define document classes and perform CRUD operations on them.

### Defining Document Classes

To define a document class, you need to inherit from the `Document` class:

```python
from gcp_pilot.datastore import Document, EmbeddedDocument
from datetime import datetime
from typing import List, Optional

# Define an embedded document class
class Address(EmbeddedDocument):
    street: str
    city: str
    state: str
    zip_code: str
    
    # You can customize the kind name (collection name)
    class Config:
        kind = "addresses"

# Define a document class
class User(Document):
    name: str
    email: str
    age: int
    created_at: datetime = datetime.now()
    address: Optional[Address] = None
    tags: List[str] = []
    
    # You can customize the kind name (collection name)
    # and exclude fields from indexing
    class Config:
        kind = "users"
        exclude_from_indexes = ["address"]
```

### Creating Documents

```python
# Create a new user
user = User(
    name="John Doe",
    email="john@example.com",
    age=30,
    address=Address(
        street="123 Main St",
        city="Anytown",
        state="CA",
        zip_code="12345"
    ),
    tags=["customer", "premium"]
)

# Save the user to Datastore
user.save()
print(f"User created with ID: {user.pk}")

# You can also create a document using the Manager
from gcp_pilot.datastore import Manager

# Create a manager for the User class
user_manager = Manager(User)

# Create a user using the manager
user = user_manager.create(
    name="Jane Smith",
    email="jane@example.com",
    age=25,
    address=Address(
        street="456 Oak St",
        city="Othertown",
        state="NY",
        zip_code="67890"
    ),
    tags=["customer"]
)
print(f"User created with ID: {user.pk}")
```

### Querying Documents

```python
from gcp_pilot.datastore import Manager, DoesNotExist, MultipleObjectsFound

# Create a manager for the User class
user_manager = Manager(User)

# Get a user by primary key
user = user_manager.get(pk="user_id_here")
print(f"User: {user.name}, Email: {user.email}")

# Get a user by a field value
try:
    user = user_manager.get(email="john@example.com")
    print(f"User: {user.name}, Email: {user.email}")
except DoesNotExist:
    print("User not found")
except MultipleObjectsFound:
    print("Multiple users found with the same email")

# Query users with filters
users = user_manager.filter(age__gt=25)  # Users older than 25
for user in users:
    print(f"User: {user.name}, Age: {user.age}")

# Query with multiple filters
users = user_manager.filter(age__gt=25, tags__contains="premium")
for user in users:
    print(f"User: {user.name}, Age: {user.age}, Tags: {user.tags}")

# Query with ordering
users = user_manager.query(order_by="age")  # Order by age ascending
for user in users:
    print(f"User: {user.name}, Age: {user.age}")

users = user_manager.query(order_by="-age")  # Order by age descending
for user in users:
    print(f"User: {user.name}, Age: {user.age}")

# Query with pagination
users = user_manager.query(page_size=10)  # Get 10 users per page
for user in users:
    print(f"User: {user.name}")

# Query with distinct values
users = user_manager.query(distinct_on="age")
for user in users:
    print(f"User: {user.name}, Age: {user.age}")
```

### Updating Documents

```python
# Update a user by primary key
user_manager.update(
    pk="user_id_here",
    name="John Smith",
    age=31
)

# Update a user object
user = user_manager.get(pk="user_id_here")
user.name = "John Smith"
user.age = 31
user.save()
```

### Deleting Documents

```python
# Delete a user by primary key
user_manager.delete(pk="user_id_here")

# Delete a user object
user = user_manager.get(pk="user_id_here")
user.delete()
```

## Advanced Usage

### Custom Managers

You can create custom managers for your document classes to add specialized query methods:

```python
from gcp_pilot.datastore import Manager, Document

class UserManager(Manager):
    def get_premium_users(self):
        return self.filter(tags__contains="premium")
    
    def get_users_by_age_range(self, min_age, max_age):
        return self.filter(age__gte=min_age, age__lte=max_age)

class User(Document):
    name: str
    email: str
    age: int
    tags: list = []
    
    # Attach the custom manager
    objects = UserManager()
    
    class Config:
        kind = "users"

# Use the custom manager
premium_users = User.objects.get_premium_users()
for user in premium_users:
    print(f"Premium user: {user.name}")

# Get users in an age range
users_25_to_35 = User.objects.get_users_by_age_range(25, 35)
for user in users_25_to_35:
    print(f"User: {user.name}, Age: {user.age}")
```

### Query Operators

The Datastore module supports various query operators:

- `__eq`: Equal to (default if no operator is specified)
- `__ne`: Not equal to
- `__lt`: Less than
- `__lte`: Less than or equal to
- `__gt`: Greater than
- `__gte`: Greater than or equal to
- `__in`: In a list of values
- `__contains`: Contains a value (for lists)
- `__startswith`: Starts with a value (for strings)
- `__endswith`: Ends with a value (for strings)

```python
# Examples of query operators
users = user_manager.filter(age__lt=30)  # Users younger than 30
users = user_manager.filter(name__startswith="J")  # Users whose name starts with J
users = user_manager.filter(tags__contains="premium")  # Users with the premium tag
users = user_manager.filter(age__in=[25, 30, 35])  # Users of specific ages
```

### Embedded Documents

Embedded documents are stored as part of their parent document:

```python
from gcp_pilot.datastore import Document, EmbeddedDocument
from typing import List, Optional

class Address(EmbeddedDocument):
    street: str
    city: str
    state: str
    zip_code: str

class Contact(EmbeddedDocument):
    phone: str
    email: str

class User(Document):
    name: str
    address: Optional[Address] = None
    contacts: List[Contact] = []
    
    class Config:
        kind = "users"

# Create a user with embedded documents
user = User(
    name="John Doe",
    address=Address(
        street="123 Main St",
        city="Anytown",
        state="CA",
        zip_code="12345"
    ),
    contacts=[
        Contact(phone="555-1234", email="john@example.com"),
        Contact(phone="555-5678", email="john@work.com")
    ]
)

# Save the user
user.save()

# Query users by embedded document fields
user_manager = Manager(User)
users = user_manager.filter(**{"address.city": "Anytown"})
for user in users:
    print(f"User: {user.name}, City: {user.address.city}")
```

## Error Handling

The Datastore module provides custom exceptions for handling common errors:

```python
from gcp_pilot.datastore import Manager, DoesNotExist, MultipleObjectsFound

user_manager = Manager(User)

try:
    # Try to get a user that doesn't exist
    user = user_manager.get(email="nonexistent@example.com")
except DoesNotExist:
    print("User not found")

try:
    # Try to get a user when multiple users have the same email
    user = user_manager.get(age=30)  # Multiple users might be 30 years old
except MultipleObjectsFound:
    print("Multiple users found")
```