import pytest

from tests.gcp_pilot.firestore_test.conftest import AllDataTypes, AllDataTypesFactory


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

    async def test_filter_array_contains_any(self):
        obj1 = await AllDataTypesFactory.create_async(list_of_strings=["a", "b"])
        obj2 = await AllDataTypesFactory.create_async(list_of_strings=["c", "d"])
        await AllDataTypesFactory.create_async(list_of_strings=["e", "f"])

        results = [item async for item in AllDataTypes.objects.filter(list_of_strings__contains_any=["a", "d"])]
        assert len(results) == 2
        assert {r.pk for r in results} == {obj1.pk, obj2.pk}

    async def test_filter_in_list_nested(self):
        obj1 = await AllDataTypesFactory.create_async(nested_model={"name": "test1", "value": 1})
        obj2 = await AllDataTypesFactory.create_async(nested_model={"name": "test2", "value": 2})
        await AllDataTypesFactory.create_async(nested_model={"name": "test3", "value": 3})

        results = [item async for item in AllDataTypes.objects.filter(nested_model__name__in=["test1", "test2"])]
        assert len(results) == 2
        assert {r.pk for r in results} == {obj1.pk, obj2.pk}

    async def test_filter_not_in_list(self):
        obj1 = await AllDataTypesFactory.create_async()
        await AllDataTypesFactory.create_batch_async(2, integer_field=obj1.integer_field)
        await AllDataTypesFactory.create_batch_async(3, integer_field=obj1.integer_field + 1)

        results = [item async for item in AllDataTypes.objects.filter(integer_field__not_in=[obj1.integer_field])]
        assert len(results) == 3

    async def test_filter_nested_field(self):
        obj = await AllDataTypesFactory.create_async(nested_model={"name": "test", "value": 1})
        retrieved = await AllDataTypes.objects.get(nested_model__name="test")
        assert retrieved.pk == obj.pk

    async def test_filter_chaining(self, populated_db):
        results = [
            item async for item in AllDataTypes.objects.filter(integer_field__gte=30, list_of_strings__contains="a")
        ]
        assert len(results) == 2
        for item in results:
            assert item.integer_field >= 30
            assert "a" in item.list_of_strings
