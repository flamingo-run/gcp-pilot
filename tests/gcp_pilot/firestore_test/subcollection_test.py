import pytest

from gcp_pilot.firestore import Document
from gcp_pilot.firestore.exceptions import DoesNotExist
from gcp_pilot.firestore.subcollection import Subcollection


class Review(Document):
    content: str

    class Meta:
        collection_name = "reviews"


class Product(Document):
    name: str
    reviews = Subcollection(Review)

    class Meta:
        collection_name = "products"


@pytest.mark.asyncio
class TestSubcollections:
    async def test_subcollection_crud(self):
        # 1. Create a parent document
        product = Product(name="Laptop")
        await product.save()
        assert product.fqn

        # 2. Create a sub-document
        review_content = "This is a great laptop!"
        review = await product.reviews.create(content=review_content)
        assert review.fqn
        assert review.content == review_content

        # 3. Get the sub-document
        retrieved_review = await product.reviews.get(id=review.id)
        assert retrieved_review.fqn == review.fqn
        assert retrieved_review.content == review_content

        # 4. Update the sub-document
        updated_content = "This is an even better laptop!"
        retrieved_review.content = updated_content
        await retrieved_review.save()

        updated_review = await product.reviews.get(id=review.id)
        assert updated_review.content == updated_content

        # 5. Delete the sub-document
        await updated_review.delete()
        with pytest.raises(DoesNotExist):
            await product.reviews.get(id=review.id)

    async def test_subcollection_filtering(self):
        # 1. Create parent and sub-documents
        product = Product(name="Gaming Mouse")
        await product.save()

        await product.reviews.create(content="Great for FPS")
        await product.reviews.create(content="A bit small")
        await product.reviews.create(content="Also great")

        # 2. Filter the sub-documents
        results = [item async for item in product.reviews.filter(content__eq="Great for FPS")]
        assert len(results) == 1
        assert results[0].content == "Great for FPS"
