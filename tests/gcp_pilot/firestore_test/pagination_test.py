import pytest
import pytest_asyncio
from google.api_core.exceptions import InvalidArgument
from pydantic import BaseModel

from gcp_pilot.firestore.exceptions import InvalidCursor
from tests.gcp_pilot.firestore_test.conftest import Product


@pytest.mark.asyncio
class TestPagination:
    @pytest_asyncio.fixture(autouse=True)
    async def setup_products(self):
        for i in range(20):
            await Product.documents.create(data={"name": f"Product {i}", "price": i * 10})

    async def test_limit(self):
        products = [item async for item in Product.documents.all().order_by("price").limit(5)]
        assert len(products) == 5
        assert products[0].name == "Product 0"
        assert products[4].name == "Product 4"

    async def test_pagination_with_cursor(self):
        # First page
        page1 = [item async for item in Product.documents.all().order_by("price").limit(10)]
        assert len(page1) == 10
        assert page1[0].name == "Product 0"
        assert page1[9].name == "Product 9"

        # Second page
        cursor = page1[-1]
        page2 = [item async for item in Product.documents.all().order_by("price").limit(10).start_after(cursor)]
        assert len(page2) == 10
        assert page2[0].name == "Product 10"
        assert page2[9].name == "Product 19"

        # Third page (should be empty)
        cursor = page2[-1]
        page3 = [item async for item in Product.documents.all().order_by("price").limit(10).start_after(cursor)]
        assert len(page3) == 0

    async def test_pagination_descending(self):
        # First page
        page1 = [item async for item in Product.documents.all().order_by("-price").limit(10)]
        assert len(page1) == 10
        assert page1[0].name == "Product 19"
        assert page1[9].name == "Product 10"

        # Second page
        cursor = page1[-1]
        page2 = [item async for item in Product.documents.all().order_by("-price").limit(10).start_after(cursor)]
        assert len(page2) == 10
        assert page2[0].name == "Product 9"
        assert page2[9].name == "Product 0"

    async def test_start_after_without_order_by_raises_error(self):
        page1 = [item async for item in Product.documents.all().limit(1)]
        cursor = page1[0]
        with pytest.raises(ValueError):
            [item async for item in Product.documents.all().start_after(cursor)]

    async def test_negative_limit_raises_error(self):
        with pytest.raises(InvalidArgument):
            [item async for item in Product.documents.all().order_by("price").limit(-1)]

    async def test_start_after_with_dict_cursor_missing_order_by_key_raises_error(self):
        cursor = {"name": "Product 5"}  # Missing "price" which is used for ordering
        with pytest.raises(ValueError):
            [item async for item in Product.documents.all().order_by("price", "name").start_after(cursor)]

    async def test_start_at_with_dict_cursor_missing_order_by_key_raises_error(self):
        cursor = {"name": "Product 5"}  # Missing "price" which is used for ordering
        with pytest.raises(ValueError):
            [item async for item in Product.documents.all().order_by("price", "name").start_at(cursor)]

    class SimpleCursor(BaseModel):
        price: int

    async def test_start_after_with_dict_cursor(self):
        cursor = {"price": 90}
        page = [item async for item in Product.documents.all().order_by("price").limit(10).start_after(cursor)]
        assert len(page) == 10
        assert page[0].name == "Product 10"
        assert page[9].name == "Product 19"

    async def test_start_at_with_dict_cursor(self):
        cursor = {"price": 100}
        page = [item async for item in Product.documents.all().order_by("price").limit(10).start_at(cursor)]
        assert len(page) == 10
        assert page[0].name == "Product 10"
        assert page[9].name == "Product 19"

    async def test_start_at_with_document_cursor(self):
        page1 = [item async for item in Product.documents.all().order_by("price").limit(10)]
        cursor = page1[9]  # Product 9
        page2 = [item async for item in Product.documents.all().order_by("price").limit(10).start_at(cursor)]
        assert len(page2) == 10
        assert page2[0].name == "Product 9"
        assert page2[9].name == "Product 18"

    async def test_start_after_with_pydantic_model_cursor(self):
        cursor = self.SimpleCursor(price=90)
        page = [
            item async for item in Product.documents.all().order_by("price").limit(10).start_after(cursor.model_dump())
        ]
        assert len(page) == 10
        assert page[0].name == "Product 10"
        assert page[9].name == "Product 19"

    async def test_start_at_with_pydantic_model_cursor(self):
        cursor = self.SimpleCursor(price=100)
        page = [
            item async for item in Product.documents.all().order_by("price").limit(10).start_at(cursor.model_dump())
        ]
        assert len(page) == 10
        assert page[0].name == "Product 10"
        assert page[9].name == "Product 19"

    async def test_start_after_with_invalid_cursor_type_raises_error(self):
        cursor = [90]  # list is not a valid cursor
        with pytest.raises(InvalidCursor, match="Cursor must be a dictionary or a Pydantic model."):
            [item async for item in Product.documents.all().order_by("price").start_after(cursor)]

    async def test_start_at_with_invalid_cursor_type_raises_error(self):
        cursor = (100,)  # tuple is not a valid cursor
        with pytest.raises(InvalidCursor, match="Cursor must be a dictionary or a Pydantic model."):
            [item async for item in Product.documents.all().order_by("price").start_at(cursor)]
