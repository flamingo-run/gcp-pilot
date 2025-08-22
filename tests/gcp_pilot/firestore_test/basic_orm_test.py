import pytest
from google.cloud.firestore import AsyncClient

from gcp_pilot.firestore import DoesNotExist
from tests.gcp_pilot.firestore_test.conftest import Product


@pytest.mark.asyncio
class TestBasicFirestoreORM:
    async def test_client_is_async(self):
        assert isinstance(Product.documents.client, AsyncClient)

    async def test_document_create(self, product_data):
        product = Product(**product_data)
        assert product.pk is None

        product = await product.save()
        assert product.pk is not None
        assert product.name == product_data["name"]

    async def test_document_get(self, saved_product):
        product = await Product.documents.get(pk=saved_product.pk)
        assert product.pk == saved_product.pk
        assert product.name == saved_product.name

    async def test_document_save_update(self, saved_product):
        new_name = "Updated Product Name"
        saved_product.name = new_name
        await saved_product.save()

        updated_product = await Product.documents.filter(name__eq=new_name).get()
        assert updated_product.name == new_name

    async def test_document_delete(self, saved_product):
        pk = saved_product.pk
        await saved_product.delete()

        with pytest.raises(DoesNotExist):
            await Product.documents.get(pk=pk)
