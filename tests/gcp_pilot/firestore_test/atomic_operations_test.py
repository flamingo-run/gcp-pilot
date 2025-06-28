import pytest
from pydantic import Field

from gcp_pilot.firestore import Document
from gcp_pilot.firestore.factory import FirestoreFactory
from gcp_pilot.firestore.operations import ArrayRemove, ArrayUnion, Increment


class Product(Document):
    """A test model for atomic operations."""

    name: str = Field(...)
    price: int | None = Field(default=0)
    stock: int | None = Field(default=0)
    tags: list[str] = Field(default_factory=list)

    class Meta:
        collection_name = "products"


class ProductFactory(FirestoreFactory[Product]): ...


@pytest.mark.asyncio
async def test_atomic_increment():
    """Verify that Increment operator works correctly."""
    product = await ProductFactory.create_async(stock=10)
    assert product.stock == 10

    await product.update(stock=Increment(1))
    assert product.stock == 10  # Local object should not be updated

    await product.refresh()
    assert product.stock == 11  # Local object should be updated after refresh


@pytest.mark.asyncio
async def test_atomic_array_union():
    """Verify that ArrayUnion operator works correctly."""
    product = await ProductFactory.create_async(tags=["a", "b"])
    assert product.tags == ["a", "b"]

    await product.update(tags=ArrayUnion(["c", "d"]))
    assert product.tags == ["a", "b"]

    await product.refresh()
    assert sorted(product.tags) == ["a", "b", "c", "d"]


@pytest.mark.asyncio
async def test_atomic_array_remove():
    """Verify that ArrayRemove operator works correctly."""
    product = await ProductFactory.create_async(tags=["a", "b", "c"])
    assert product.tags == ["a", "b", "c"]

    await product.update(tags=ArrayRemove(["b"]))
    assert product.tags == ["a", "b", "c"]

    await product.refresh()
    assert sorted(product.tags) == ["a", "c"]
