import pytest

from gcp_pilot.firestore import atomic
from tests.gcp_pilot.firestore_test.conftest import Product


@pytest.mark.asyncio
class TestAtomicWrites:
    async def test_batch_create(self):
        async with atomic.batch():
            await Product.objects.create(data={"name": "Product 1", "price": 10})
            await Product.objects.create(data={"name": "Product 2", "price": 20})

        products = [item async for item in Product.objects.filter(name__in=["Product 1", "Product 2"])]
        assert len(products) == 2

    async def test_batch_update(self):
        p1 = await Product.objects.create(data={"name": "Product 1", "price": 10})
        p2 = await Product.objects.create(data={"name": "Product 2", "price": 20})

        async with atomic.batch():
            p1.price = 15
            p2.price = 25
            await p1.save()
            await p2.save()

        updated_p1 = await Product.objects.get(pk=p1.pk)
        updated_p2 = await Product.objects.get(pk=p2.pk)

        assert updated_p1.price == 15
        assert updated_p2.price == 25

    async def test_batch_delete(self):
        p1 = await Product.objects.create(data={"name": "Product 1", "price": 10})
        p2 = await Product.objects.create(data={"name": "Product 2", "price": 20})

        async with atomic.batch():
            await p1.delete()
            await p2.delete()

        products = [item async for item in Product.objects.filter(name__in=["Product 1", "Product 2"])]
        assert len(products) == 0
