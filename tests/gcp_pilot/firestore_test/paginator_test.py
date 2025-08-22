import pytest
import pytest_asyncio

from gcp_pilot.firestore import Document


class City(Document):
    name: str

    class Meta:
        collection_name = "cities"


@pytest_asyncio.fixture
async def cities():
    cities_to_create = [City(id=f"city-{i}", name=f"City {i:02d}") for i in range(25)]
    for city in cities_to_create:
        await city.save()
    return cities_to_create


@pytest.mark.asyncio
async def test_paginator_iteration(cities):
    paginator = City.documents.order_by("name").paginate(per_page=10)

    pages = [page async for page in paginator]
    assert len(pages) == 3

    # Check page content
    assert len(pages[0].object_list) == 10
    assert pages[0].number == 1
    assert pages[0].object_list[0].name == "City 00"
    assert pages[0].object_list[-1].name == "City 09"

    assert len(pages[1].object_list) == 10
    assert pages[1].number == 2
    assert pages[1].object_list[0].name == "City 10"
    assert pages[1].object_list[-1].name == "City 19"

    assert len(pages[2].object_list) == 5
    assert pages[2].number == 3
    assert pages[2].object_list[0].name == "City 20"
    assert pages[2].object_list[-1].name == "City 24"


@pytest.mark.asyncio
async def test_paginator_count(cities):
    paginator = City.documents.paginate(per_page=10)
    count = await paginator.count()
    assert count == 25


@pytest.mark.asyncio
async def test_paginator_num_pages(cities):
    paginator = City.documents.paginate(per_page=10)
    num_pages = await paginator.num_pages
    assert num_pages == 3


@pytest.mark.asyncio
async def test_paginator_large_per_page(cities):
    paginator = City.documents.paginate(per_page=50)
    pages = [page async for page in paginator]
    assert len(pages) == 1
    assert len(pages[0].object_list) == 25
