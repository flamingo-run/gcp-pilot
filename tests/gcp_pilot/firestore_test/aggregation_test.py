import uuid

import pytest
import pytest_asyncio

from gcp_pilot.firestore import Document


class Sale(Document):
    product: str
    amount: float
    run_id: str

    class Meta:
        collection_name = "sales"


@pytest_asyncio.fixture
async def sales():
    run_id = str(uuid.uuid4())
    sales_to_create = [
        Sale(product="A", amount=10, run_id=run_id),
        Sale(product="A", amount=20, run_id=run_id),
        Sale(product="B", amount=30, run_id=run_id),
        Sale(product="A", amount=30, run_id=run_id),
    ]
    for sale in sales_to_create:
        await sale.save()
    return run_id, sales_to_create


@pytest.mark.asyncio
async def test_sum_aggregation(sales):
    run_id, _ = sales
    total = await Sale.documents.filter(product="A", run_id=run_id).sum("amount")
    assert total == 60


@pytest.mark.asyncio
async def test_avg_aggregation(sales):
    run_id, _ = sales
    average = await Sale.documents.filter(product="A", run_id=run_id).avg("amount")
    assert average == 20
