import pytest

from tests.gcp_pilot.firestore_test.conftest import Product


@pytest.mark.asyncio
class TestQueryBuilding:
    def _filters_to_set(self, filters):
        return {(f.field_path, f.op_string, f.value) for f in filters}

    async def test_query_is_cloned_on_filter(self):
        query1 = Product.objects.all()
        query2 = query1.filter(name="some name")
        assert query1 is not query2
        assert not query1._where_filters
        assert len(query2._where_filters) == 1

    async def test_query_is_cloned_on_order_by(self):
        query1 = Product.objects.all()
        query2 = query1.order_by("name")
        assert query1 is not query2
        assert not query1._order_by
        assert query2._order_by == ["name"]

    async def test_query_is_cloned_on_limit(self):
        query1 = Product.objects.all()
        query2 = query1.limit(10)
        assert query1 is not query2
        assert query1._limit is None
        assert query2._limit == 10

    async def test_query_can_be_reused(self):
        base_query = Product.objects.filter(price__gt=50)

        query1 = base_query.order_by("price")
        query2 = base_query.order_by("-price")

        assert query1._order_by == ["price"]
        assert query2._order_by == ["-price"]

        assert not base_query._order_by

        assert len(base_query._where_filters) == 1
        assert len(query1._where_filters) == 1
        assert len(query2._where_filters) == 1

    async def test_chaining_methods_in_any_order_produces_same_query(self):
        q1 = Product.objects.filter(price__gt=10, stock__gt=0).order_by("-name").limit(5)
        q2 = Product.objects.all().limit(5).order_by("-name").filter(price__gt=10).filter(stock__gt=0)

        assert self._filters_to_set(q1._where_filters) == self._filters_to_set(q2._where_filters)
        assert q1._order_by == q2._order_by
        assert q1._limit == q2._limit
