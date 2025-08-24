import pytest
from google.cloud.firestore import AsyncClient

from gcp_pilot.firestore import Document, DoesNotExist
from tests.gcp_pilot.firestore_test.conftest import Product


@pytest.mark.asyncio
class TestBasicFirestoreORM:
    async def test_client_is_async(self):
        assert isinstance(Product.documents.client, AsyncClient)

    async def test_document_create(self, product_data):
        product = Product(**product_data)
        assert product.fqn is None

        product = await product.save()
        assert product.fqn is not None
        assert product.name == product_data["name"]

    async def test_document_get(self, saved_product):
        product = await Product.documents.get(id=saved_product.id)
        assert product.id == saved_product.id
        assert product.name == saved_product.name

    async def test_document_save_update(self, saved_product):
        new_name = "Updated Product Name"
        saved_product.name = new_name
        await saved_product.save()

        updated_product = await Product.documents.filter(name__eq=new_name).get()
        assert updated_product.name == new_name

    async def test_document_delete(self, saved_product):
        pk = saved_product.id
        await saved_product.delete()

        with pytest.raises(DoesNotExist):
            await Product.documents.get(id=pk)

    async def test_manager_update_with_id_builds_fqn_and_updates(self):
        # Create a product
        p = await Product.documents.create(name="Before", price=1)
        assert p.id is not None
        assert p.fqn is not None

        # Update using manager directly with only the ID
        await Product.documents.update(id=p.id, name="After")

        # Fetch again; should reflect updated value
        updated = await Product.documents.get(id=p.id)
        assert updated.name == "After"


@pytest.mark.asyncio
class TestCustomDatabase:
    async def test_document_fqn_uses_custom_database(self):
        class AltProduct(Document):
            name: str

            class Meta:
                collection_name = "alt_products"
                database_id = "test-db"

        # Create and save; id will be auto-generated
        obj = AltProduct(name="Widget")
        await obj.save()

        # FQN should include the custom database id
        assert "/databases/test-db/" in (obj.fqn.full_name if obj.fqn else "")
