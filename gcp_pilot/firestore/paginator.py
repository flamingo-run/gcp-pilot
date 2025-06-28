from __future__ import annotations

import math
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
    from gcp_pilot.firestore.query import Query

T = TypeVar("T")


class Page[T]:
    def __init__(self, object_list: list[T], number: int, paginator: Paginator[T]):
        self.object_list = object_list
        self.number = number
        self.paginator = paginator

    def __repr__(self):
        return f"<Page {self.number} of {self.paginator.num_pages}>"

    def __len__(self):
        return len(self.object_list)

    def __getitem__(self, index):
        return self.object_list[index]

    def has_next(self) -> bool:
        return self.number < self.paginator.num_pages

    def has_previous(self) -> bool:
        return self.number > 1

    def has_other_pages(self) -> bool:
        return self.has_previous() or self.has_next()

    def next_page_number(self) -> int:
        return self.number + 1

    def previous_page_number(self) -> int:
        return self.number - 1


class Paginator[T]:
    def __init__(self, query: Query[T], per_page: int):
        self._query = query
        self.per_page = per_page
        self._count = None

    async def __aiter__(self) -> AsyncIterator[Page[T]]:
        cursor = None
        page_num = 1
        while True:
            page_query = self._query.limit(self.per_page)
            if cursor:
                page_query = page_query.start_after(cursor)

            results = [item async for item in page_query]
            if not results:
                break

            cursor = results[-1]
            yield Page(object_list=results, number=page_num, paginator=self)
            page_num += 1

            if len(results) < self.per_page:
                break  # Last page

    async def count(self) -> int:
        if self._count is None:
            self._count = await self._query.count()
        return self._count

    @property
    async def num_pages(self) -> int:
        if self.per_page == 0:
            return 0
        count = await self.count()
        return math.ceil(count / self.per_page)
