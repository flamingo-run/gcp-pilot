# Firestore ORM

The `gcp-pilot` library includes a powerful and intuitive Object-Relational Mapper (ORM) for Google Firestore. This ORM is designed to simplify interactions with Firestore by allowing you to work with Python objects and classes instead of raw dictionaries. It provides a high-level abstraction over the native Firestore client library, making your code cleaner, more readable, and easier to maintain.

## Installation

To use the Firestore ORM, you need to install `gcp-pilot`:

```bash
pip install gcp-pilot
```

## Usage

### Defining Models

The core of the Firestore ORM is the `Document` class. You define your data models by inheriting from this class. Each class represents a Firestore collection, and each instance of the class represents a document within that collection.

#### Documents

To define a document, create a class that inherits from `gcp_pilot.firestore.Document`. By default, the collection name in Firestore will be the lowercase version of the class name.

```python
from gcp_pilot.firestore import Document
from pydantic import Field

class Product(Document):
    # This will be mapped to a "product" collection in Firestore
    name: str = Field(...)
    price: int = Field(default=0)
```

You can customize the collection name by adding an inner `Meta` class:

```python
class UserProfile(Document):
    name: str

    class Meta:
        collection_name = "user_profiles"
```

#### Subcollections

You can also define subcollections within a document. First, define your subcollection model just like a regular document model. Then, you attach it to the parent document model using the `Subcollection` descriptor.

```python
from gcp_pilot.firestore import Document, Subcollection

class Review(Document):
    rating: int
    comment: str

    class Meta:
        collection_name = "reviews" # Name of the subcollection

class Product(Document):
    name: str
    price: float
    reviews = Subcollection(Review)

    class Meta:
        collection_name = "products" # Name of the parent collection
```

In this example, `Product` documents can have a "reviews" subcollection containing `Review` documents.


### Creating and Updating Documents

To create a new document in Firestore, you can instantiate your model and use the `.save()` method. If the document already has a primary key (i.e., it was fetched from Firestore or the `id` was manually set), `.save()` will overwrite the existing document's data.

```python
# Create a new document with an auto-generated ID
product = Product(name="Wireless Mouse", price=79.99)
await product.save()
print(f"Product created with ID: {product.id}")

# Create a new document with a specific ID
product = Product(id="my-custom-id", name="Ergonomic Keyboard", price=129.99)
await product.save()

# Update an existing document
product.price = 119.99
await product.save()  # This will overwrite the entire document
```

#### Partial Updates

If you want to update only specific fields without overwriting the entire document, you can use the `.update()` method.

```python
await product.update(price=109.99, stock=100)
```

### Getting Documents

You can retrieve a single document by its ID using the `objects.get()` method on the model class.

```python
# Get a product by its ID
product = await Product.objects.get(pk="my-custom-id")
print(f"Product name: {product.name}")
print(f"Product price: {product.price}")
```

If the document does not exist, a `gcp_pilot.firestore.DoesNotExist` exception will be raised.

You can also get a document by filtering on its fields. This will return the first document that matches the query.

```python
product = await Product.objects.get(name__eq="Ergonomic Keyboard")
```

### Refreshing a Document

If you have a document instance and you want to reload its data from Firestore, you can use the `.refresh()` method.

```python
await product.refresh()
```

### Deleting Documents

To delete a document, call the `.delete()` method on a document instance.

```python
# First, get the document
product = await Product.objects.get(pk="my-custom-id")

# Then, delete it
await product.delete()
```
You can also delete a document by its ID directly from the manager.

```python
await Product.objects.delete(pk="my-custom-id")
```

### Querying Data

The Firestore ORM provides a powerful and intuitive API for querying your data. You can filter, order, and limit your results with ease. To start querying, you use the `.objects` manager on your model class.

#### Getting All Documents

To retrieve all documents from a collection, you can iterate over the result of `.all()`:

```python
all_products = [product async for product in Product.objects.all()]
```

#### Filtering

You can filter your results using the `.filter()` method. You can chain multiple filters together.

```python
# Get all products with a price greater than 100
expensive_products = Product.objects.filter(price__gt=100)

# Get all products with a price between 50 and 100
mid_range_products = Product.objects.filter(price__gte=50, price__lte=100)

# Iterate over the results
async for product in mid_range_products:
    print(product.name)
```

##### Available Lookups

The following filter lookups are available:

| Lookup | Description |
| --- | --- |
| `__eq` | Exact match (this is the default if no lookup is provided) |
| `__ne` | Not equal to |
| `__gt` | Greater than |
| `__gte` | Greater than or equal to |
| `__lt` | Less than |
| `__lte` | Less than or equal to |
| `__in` | Value is in a list |
| `__not_in` | Value is not in a list |
| `__contains` | Array field contains a value |
| `__contains_any` | Array field contains any value from a list |

#### Ordering

You can order your results using the `.order_by()` method. To order in descending order, prefix the field name with a `-`.

```python
# Get all products ordered by price in ascending order
products_by_price = Product.objects.order_by("price")

# Get all products ordered by price in descending order
products_by_price_desc = Product.objects.order_by("-price")
```

#### Limiting Results

You can limit the number of results using the `.limit()` method.

```python
# Get the 3 most expensive products
most_expensive_products = Product.objects.order_by("-price").limit(3)
```

#### Counting Results

To count the number of documents that match a query, you can use the `.count()` method.

```python
num_products = await Product.objects.filter(price__gt=100).count()
```

### Atomic Operations

The ORM supports atomic operations to ensure data consistency. You can perform multiple write operations as a single atomic unit using batched writes, and you can also perform atomic updates on specific fields.

#### Batched Writes

When you need to perform multiple write operations (create, update, or delete) at once, you can use a batch to ensure that all operations succeed or none of them do. The ORM provides an `atomic.batch()` context manager for this purpose.

```python
from gcp_pilot.firestore import atomic

# Create multiple products in a single batch
async with atomic.batch():
    await Product(name="Laptop Stand", price=49.99).save()
    await Product(name="USB-C Hub", price=89.99).save()

# Update and delete in the same batch
product_to_update = await Product.objects.get(name__eq="Laptop Stand")
product_to_delete = await Product.objects.get(name__eq="USB-C Hub")

async with atomic.batch():
    product_to_update.price = 45.99
    await product_to_update.save()
    await product_to_delete.delete()
```

All operations within the `async with atomic.batch():` block are sent to Firestore as a single atomic unit. If any operation fails, none of them are applied.

#### Field-level Atomic Operations

Firestore supports atomic operations on specific field types, such as numbers and arrays.

##### Incrementing a Number

You can atomically increment or decrement a numeric field using the `Increment` operation.

```python
from gcp_pilot.firestore.operations import Increment

product = await Product.objects.get(name__eq="Laptop Stand")
await product.update(stock=Increment(1))  # Atomically increments the stock by 1
await product.update(stock=Increment(-1)) # Atomically decrements the stock by 1
```

##### Updating an Array

You can atomically add or remove elements from an array field using `ArrayUnion` and `ArrayRemove`.

```python
from gcp_pilot.firestore.operations import ArrayUnion, ArrayRemove

product = await Product.objects.get(name__eq="Laptop Stand")

# Add new tags to the 'tags' array field
await product.update(tags=ArrayUnion(["new", "featured"]))

# Remove a tag from the 'tags' array field
await product.update(tags=ArrayRemove(["old"]))
```

### Pagination

When dealing with large datasets, it's often necessary to paginate the results. The ORM provides `limit()`, `start_at()`, and `start_after()` methods for this purpose. For pagination to work correctly, you must also order the results with `order_by()`.

```python
# Get the first page of 10 products, ordered by price
page1 = [p async for p in Product.objects.order_by("price").limit(10)]

if page1:
    # To get the next page, use the last document of the current page as a cursor
    last_product_on_page1 = page1[-1]
    page2 = [p async for p in Product.objects.order_by("price").limit(10).start_after(last_product_on_page1)]

    # To get a page starting from a specific document, use start_at()
    page_starting_from_last = [p async for p in Product.objects.order_by("price").limit(10).start_at(last_product_on_page1)]
```

The cursor can be a document instance (as in the example above), or a dictionary containing the values of the fields used for ordering.

```python
# Using a dictionary as a cursor
cursor = {"price": 100}
page = [p async for p in Product.objects.order_by("price").limit(10).start_after(cursor)]
```

### Working with Subcollections

You can access the subcollection through an instance of the parent document. The subcollection attribute on the instance acts as a manager for the subcollection, similar to the `.objects` manager on a model class.

```python
# Get a product document
product = await Product.objects.get(pk="my-product-id")

# Now you can work with its "reviews" subcollection
all_reviews = [r async for r in product.reviews.all()]
```

#### Creating Subcollection Documents

You can create documents in a subcollection using the `.create()` or `.save()` methods on the subcollection manager.

```python
# Get the parent document
product = await Product.objects.get(pk="my-product-id")

# Create a new review in the "reviews" subcollection
new_review = await product.reviews.create(data={"rating": 5, "comment": "Excellent product!"})
```

#### Querying Subcollections

You can filter, order, and limit subcollection documents just like top-level collections.

```python
# Get the parent document
product = await Product.objects.get(pk="my-product-id")

# Get all 5-star reviews for this product
five_star_reviews = [r async for r in product.reviews.filter(rating__eq=5)]
```
