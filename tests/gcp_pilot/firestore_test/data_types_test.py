import pytest

from tests.gcp_pilot.firestore_test.conftest import AllDataTypes, AllDataTypesFactory


@pytest.mark.asyncio
class TestFirestoreDataTypes:
    async def test_all_data_types_with_factory(self):
        instance = AllDataTypesFactory.build()
        instance.id = None
        saved_instance = await instance.save()

        retrieved_instance = await AllDataTypes.documents.get(id=saved_instance.id)

        # Compare saved and retrieved data
        assert saved_instance.fqn == retrieved_instance.fqn
        assert saved_instance.string_field == retrieved_instance.string_field
        assert saved_instance.integer_field == retrieved_instance.integer_field
        assert saved_instance.float_field == retrieved_instance.float_field
        assert saved_instance.boolean_field == retrieved_instance.boolean_field
        assert saved_instance.datetime_field == retrieved_instance.datetime_field
        assert saved_instance.date_field == retrieved_instance.date_field
        assert saved_instance.enum_field == retrieved_instance.enum_field
        assert saved_instance.list_of_strings == retrieved_instance.list_of_strings
        assert saved_instance.dict_field == retrieved_instance.dict_field
        assert saved_instance.nested_model == retrieved_instance.nested_model
        assert saved_instance.list_of_models == retrieved_instance.list_of_models
