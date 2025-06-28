import pytest

from tests.gcp_pilot.firestore_test.conftest import AllDataTypes, AllDataTypesFactory


@pytest.mark.asyncio
class TestFirestoreDataTypes:
    async def test_all_data_types_with_factory(self):
        instance = AllDataTypesFactory.build()
        await instance.save()

        retrieved = await AllDataTypes.objects.get(pk=instance.pk)
        assert retrieved.pk == instance.pk
        assert retrieved.string_field == instance.string_field
        assert retrieved.integer_field == instance.integer_field
        assert retrieved.float_field == instance.float_field
        assert retrieved.boolean_field == instance.boolean_field
        assert retrieved.datetime_field == instance.datetime_field
        assert retrieved.date_field == instance.date_field
        assert retrieved.enum_field == instance.enum_field
        assert retrieved.list_of_strings == instance.list_of_strings
        assert retrieved.dict_field == instance.dict_field
        assert retrieved.nested_model.name == instance.nested_model.name
        assert retrieved.nested_model.value == instance.nested_model.value
        assert len(retrieved.list_of_models) == len(instance.list_of_models)
