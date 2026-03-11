import pytest

from gcp_pilot.firestore import atomic
from gcp_pilot.firestore.atomic import MAX_OPS
from tests.gcp_pilot.firestore_test.conftest import Product


@pytest.mark.asyncio
class TestBulkCreate:
    async def test_basic(self):
        items = [{"name": f"Product {i}", "price": float(i)} for i in range(5)]
        count = await Product.documents.bulk_create(items)

        assert count == 5
        products = [p async for p in Product.documents.filter()]
        assert len(products) == 5

    async def test_with_ids(self):
        items = [
            {"id": "custom-1", "name": "Product 1", "price": 10.0},
            {"id": "custom-2", "name": "Product 2", "price": 20.0},
        ]
        count = await Product.documents.bulk_create(items)

        assert count == 2
        p1 = await Product.documents.get(id="custom-1")
        assert p1.name == "Product 1"
        p2 = await Product.documents.get(id="custom-2")
        assert p2.name == "Product 2"

    async def test_auto_split(self):
        n = MAX_OPS + 100
        items = [{"name": f"Product {i}", "price": float(i)} for i in range(n)]
        count = await Product.documents.bulk_create(items)

        assert count == n
        total = await Product.documents.count()
        assert total == n

    async def test_inside_batch_raises(self):
        with pytest.raises(RuntimeError, match="bulk_create cannot be used inside"):
            async with atomic.batch(Product):
                await Product.documents.bulk_create([{"name": "X", "price": 1.0}])

    async def test_empty_list(self):
        count = await Product.documents.bulk_create([])
        assert count == 0


@pytest.mark.asyncio
class TestBatchAutoSplit:
    async def test_batch_exceeding_limit(self):
        n = MAX_OPS + 100
        async with atomic.batch(Product):
            for i in range(n):
                await Product.documents.create(name=f"Product {i}", price=float(i))

        total = await Product.documents.count()
        assert total == n
