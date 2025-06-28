import pytest

from tests.gcp_pilot.firestore_test.conftest import AllDataTypes


@pytest.mark.asyncio
class TestFirestoreFiltering:
    async def test_get_by_filter(self, populated_db):
        target = populated_db[0]
        retrieved = await AllDataTypes.objects.get(integer_field=target.integer_field)
        assert retrieved.pk == target.pk

    async def test_filter_equal(self, populated_db):
        target = populated_db[0]
        results = [item async for item in AllDataTypes.objects.filter(integer_field__eq=target.integer_field)]
        assert len(results) == 1
        assert results[0].pk == target.pk

    async def test_filter_not_equal(self, populated_db):
        target = populated_db[0]
        results = [item async for item in AllDataTypes.objects.filter(integer_field__ne=target.integer_field)]
        assert len(results) == len(populated_db) - 1
        assert target.pk not in [item.pk for item in results]

    async def test_filter_greater_than(self, populated_db):
        results = [item async for item in AllDataTypes.objects.filter(integer_field__gt=30)]
        assert len(results) == 1
        for item in results:
            assert item.integer_field > 30

    async def test_filter_greater_than_or_equal(self, populated_db):
        results = [item async for item in AllDataTypes.objects.filter(integer_field__gte=30)]
        assert len(results) == 3
        for item in results:
            assert item.integer_field >= 30

    async def test_filter_less_than(self, populated_db):
        results = [item async for item in AllDataTypes.objects.filter(integer_field__lt=30)]
        assert len(results) == 2
        for item in results:
            assert item.integer_field < 30

    async def test_filter_less_than_or_equal(self, populated_db):
        results = [item async for item in AllDataTypes.objects.filter(integer_field__lte=30)]
        assert len(results) == 4
        for item in results:
            assert item.integer_field <= 30

    async def test_filter_in(self, populated_db):
        results = [item async for item in AllDataTypes.objects.filter(integer_field__in=[10, 30, 50])]
        assert len(results) == 4
        for item in results:
            assert item.integer_field in [10, 30, 50]

    async def test_filter_not_in(self, populated_db):
        results = [item async for item in AllDataTypes.objects.filter(integer_field__not_in=[10, 30, 50])]
        assert len(results) == 1
        for item in results:
            assert item.integer_field not in [10, 30, 50]

    async def test_filter_array_contains(self, populated_db):
        results = [item async for item in AllDataTypes.objects.filter(list_of_strings__contains="a")]
        assert len(results) == 3
        for item in results:
            assert "a" in item.list_of_strings

    async def test_filter_array_contains_any(self, populated_db):
        results = [item async for item in AllDataTypes.objects.filter(list_of_strings__contains_any=["b", "c"])]
        assert len(results) == 2
        for item in results:
            assert "b" in item.list_of_strings or "c" in item.list_of_strings

    async def test_filter_nested_field(self, populated_db):
        target = populated_db[0]
        results = [item async for item in AllDataTypes.objects.filter(nested_model__name__eq=target.nested_model.name)]
        assert len(results) >= 1  # Could be more if factory generated same names
        assert target.pk in [item.pk for item in results]

    async def test_filter_chaining(self, populated_db):
        results = [
            item async for item in AllDataTypes.objects.filter(integer_field__gte=30, list_of_strings__contains="a")
        ]
        assert len(results) == 2
        for item in results:
            assert item.integer_field >= 30
            assert "a" in item.list_of_strings
