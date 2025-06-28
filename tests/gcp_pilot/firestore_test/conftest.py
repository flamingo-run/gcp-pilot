import asyncio
import datetime
import enum
import os

import pytest
import pytest_asyncio
from pydantic import BaseModel

from gcp_pilot.firestore import Document
from gcp_pilot.firestore.factory import FirestoreFactory
from gcp_pilot.firestore.manager import Manager

# Set emulator host
os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:8080"


class Status(enum.StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class SubItem(BaseModel):
    name: str
    value: int


class AllDataTypes(Document):
    string_field: str
    integer_field: int
    float_field: float
    boolean_field: bool
    datetime_field: datetime.datetime
    date_field: datetime.date
    enum_field: Status
    list_of_strings: list[str]
    dict_field: dict[str, int]
    nested_model: SubItem
    list_of_models: list[SubItem]

    class Meta:
        collection_name = "all_data_types"


class Product(Document):
    name: str
    price: float

    class Meta:
        collection_name = "products"


class AllDataTypesFactory(FirestoreFactory[AllDataTypes]): ...


@pytest.fixture
def product_data():
    return {"name": "Test Product", "price": 9.99}


@pytest.fixture
def existing_product(product_data):
    return Product(**product_data)


@pytest_asyncio.fixture
async def saved_product(existing_product):
    return await existing_product.save()


@pytest_asyncio.fixture
async def populated_db():
    # Create specific data for predictable testing
    base_data = [
        {"integer_field": 10, "float_field": 10.1, "boolean_field": True, "list_of_strings": ["a", "x"]},
        {"integer_field": 20, "float_field": 20.2, "boolean_field": False, "list_of_strings": ["y"]},
        {"integer_field": 30, "float_field": 30.3, "boolean_field": True, "list_of_strings": ["a", "b"]},
        {"integer_field": 30, "float_field": 40.4, "boolean_field": False, "list_of_strings": ["z"]},
        {"integer_field": 50, "float_field": 50.5, "boolean_field": True, "list_of_strings": ["a", "c"]},
    ]

    instances = []
    for data in base_data:
        # Build a full instance with factory, then override specific fields
        instance = AllDataTypesFactory.build(**data)
        instance.id = None
        saved_instance = await instance.save()
        instances.append(saved_instance)
    return instances


@pytest.fixture(autouse=True)
def safe_client():
    """
    This fixture ensures that the firestore client is properly created
    and closed for each test, preventing "Event loop is closed" errors.
    """
    yield

    if Manager._client:
        # This is not an async fixture, so we can't await here.
        # We need to run the async close method in the current loop.

        try:
            loop = asyncio.get_running_loop()
            loop.run_until_complete(Manager._client.close())
        except RuntimeError:
            # Loop is already closed, nothing to do.
            pass
        finally:
            Manager._client = None


@pytest_asyncio.fixture(autouse=True)
async def clear_collections(safe_client):
    yield
    # Clear collections after each test
    for model in [Product, AllDataTypes]:
        all_docs = model.objects.collection.stream()
        async for doc in all_docs:
            await doc.reference.delete()
