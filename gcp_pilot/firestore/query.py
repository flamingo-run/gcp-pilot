from __future__ import annotations

import copy
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any, cast

from google.cloud.firestore_v1.async_query import AsyncQuery
from google.cloud.firestore_v1.base_query import FieldFilter
from pydantic import BaseModel

from gcp_pilot.firestore.exceptions import (
    DoesNotExist,
    InvalidCursor,
    MultipleObjectsFound,
)

if TYPE_CHECKING:
    from gcp_pilot.firestore.document import Document
    from gcp_pilot.firestore.manager import Manager
    from gcp_pilot.firestore.paginator import Paginator


class Query:
    LOOKUP_OPERATORS = {
        "eq": "==",
        "ne": "!=",
        "gt": ">",
        "gte": ">=",
        "lt": "<",
        "lte": "<=",
        "in": "in",
        "not_in": "not-in",
        "contains": "array_contains",
        "contains_any": "array_contains_any",
    }

    def __init__(self, manager: Manager):
        self._manager = manager
        self._where_filters: list[FieldFilter] = []
        self._order_by: list[str] = []
        self._limit: int | None = None
        self._start_after: Document | dict[str, Any] | None = None
        self._start_at: Document | dict[str, Any] | None = None
        self._filters_for_repr: dict[str, Any] = {}

    def _clone(self) -> Query:
        new_query = self.__class__(manager=self._manager)
        new_query._where_filters = self._where_filters.copy()
        new_query._order_by = self._order_by.copy()
        new_query._limit = self._limit
        new_query._start_after = copy.copy(self._start_after)
        new_query._start_at = copy.copy(self._start_at)
        new_query._filters_for_repr = self._filters_for_repr.copy()
        return new_query

    def filter(self, **kwargs) -> Query:
        clone = self._clone()
        clone._filters_for_repr.update(kwargs)
        for key, value in kwargs.items():
            parts = key.split("__")
            if len(parts) > 1 and parts[-1] in self.LOOKUP_OPERATORS:
                operator = self.LOOKUP_OPERATORS[parts[-1]]
                field_path = ".".join(parts[:-1])
            else:
                operator = "=="
                field_path = ".".join(parts)
            field_filter = FieldFilter(field_path, operator, value)
            clone._where_filters.append(field_filter)
        return clone

    def order_by(self, *fields: str) -> Query:
        clone = self._clone()
        clone._order_by.extend(fields)
        return clone

    def limit(self, count: int) -> Query:
        clone = self._clone()
        clone._limit = count
        return clone

    def start_after(self, cursor: Document | dict[str, Any]) -> Query:
        clone = self._clone()
        clone._start_after = cursor
        return clone

    def start_at(self, cursor: Document | dict[str, Any]) -> Query:
        clone = self._clone()
        clone._start_at = cursor
        return clone

    def all(self) -> Query:
        return self._clone()

    def paginate(self, per_page: int) -> Paginator:
        from gcp_pilot.firestore.paginator import Paginator  # noqa: PLC0415

        return Paginator(query=self, per_page=per_page)

    async def get(self) -> Document:
        query_for_get = self.limit(2)
        results = [obj async for obj in query_for_get]

        if not results:
            raise DoesNotExist(self._manager.doc_klass, filters=self._filters_for_repr)
        if len(results) > 1:
            raise MultipleObjectsFound(self._manager.doc_klass, filters=self._filters_for_repr)
        return results[0]

    async def count(self) -> int:
        query = self._build_query()
        aggregation_query = query.count()
        result = await aggregation_query.get()
        return int(result[0][0].value)

    async def sum(self, field: str) -> int | float:
        query = self._build_query()
        aggregation_query = query.sum(field)
        result = await aggregation_query.get()
        return result[0][0].value

    async def avg(self, field: str) -> int | float:
        query = self._build_query()
        aggregation_query = query.avg(field)
        result = await aggregation_query.get()
        return result[0][0].value

    def _build_query(self) -> AsyncQuery:
        query = self._apply_filters()
        query = self._apply_ordering(query)
        query = self._apply_pagination(query)
        query = self._apply_limit(query)
        return cast(AsyncQuery, query)

    def _apply_filters(self) -> AsyncQuery:
        query: AsyncQuery = self._manager.collection
        for field_filter in self._where_filters:
            query = query.where(filter=field_filter)
        return query

    def _apply_ordering(self, query: AsyncQuery) -> AsyncQuery:
        if not self._order_by:
            return query

        for field in self._order_by:
            if field.startswith("-"):
                field_name = field[1:]
                direction = AsyncQuery.DESCENDING
            else:
                field_name = field.lstrip("+")
                direction = AsyncQuery.ASCENDING
            # Support ordering by document id by translating to Firestore's special __name__ field
            firestore_field = "__name__" if field_name == "id" else field_name
            query = query.order_by(firestore_field, direction=direction)
        return query

    def _dump_cursor(self, cursor: BaseModel | dict[str, Any] | str) -> dict[str, Any]:
        """Normalize a cursor for Firestore.

        Supports:
        - dict/Pydantic models (existing behavior)
        - Document instances: dump model to dict
        - string: convert to DocumentReference
        """
        if isinstance(cursor, dict):
            # Support id-based cursors by translating to Firestore's __name__
            if "id" in cursor and "__name__" not in cursor:
                doc_ref = self._manager.collection.document(str(cursor["id"]))
                return {"__name__": doc_ref}
            return cursor
        if isinstance(cursor, BaseModel):
            return cursor.model_dump()
        if isinstance(cursor, str):
            doc_ref = self._manager.collection.document(cursor)
            return {"__name__": doc_ref}

        raise InvalidCursor("Cursor must be a dictionary or a Pydantic model.")

    def _infer_ordering_field(self) -> str | None:
        """Infer an ordering field from the pagination cursor when none is provided.

        - If cursor is a string: implies ordering by document name ("__name__")
        - If cursor is a dict/BaseModel with a single key: order by that key (asc)
        - If key is "id": we will map to "__name__"
        """
        if self._order_by:
            return None

        raw_cursor: Document | dict[str, Any] | str | None = self._start_after or self._start_at
        if raw_cursor is None:
            return None

        if isinstance(raw_cursor, str):
            return "__name__"
        if isinstance(raw_cursor, BaseModel):
            data = raw_cursor.model_dump()
        elif isinstance(raw_cursor, dict):
            data = raw_cursor
        else:
            return None

        if len(data) != 1:
            return None
        key = next(iter(data.keys()))
        return "__name__" if key == "id" else key

    def _apply_pagination(self, query: AsyncQuery) -> AsyncQuery:
        # Auto-infer ordering when possible (single-field cursor or string id)
        inferred_field = self._infer_ordering_field()
        if not self._order_by and inferred_field:
            query = query.order_by(inferred_field, direction=AsyncQuery.ASCENDING)
        elif not self._order_by and (self._start_after or self._start_at):
            raise ValueError("`order_by` is required when paginating.")

        if self._start_after:
            cursor_data = self._dump_cursor(self._start_after)
            query = query.start_after(cursor_data)

        if self._start_at:
            cursor_data = self._dump_cursor(self._start_at)
            query = query.start_at(cursor_data)

        return query

    def _apply_limit(self, query: AsyncQuery) -> AsyncQuery:
        if not self._limit:
            return query
        return query.limit(self._limit)

    async def __aiter__(self) -> AsyncGenerator[Document]:
        query = self._build_query()
        stream = query.stream()
        async for doc_snapshot in stream:
            yield self._manager._to_document(doc_snapshot)
