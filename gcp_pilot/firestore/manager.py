from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any, ClassVar

from google.cloud import firestore
from google.cloud.firestore_v1.async_client import AsyncClient
from google.cloud.firestore_v1.async_collection import AsyncCollectionReference
from google.cloud.firestore_v1.async_query import AsyncQuery
from google.cloud.firestore_v1.base_query import FieldFilter
from pydantic import BaseModel

from gcp_pilot.firestore.atomic import _active_batch
from gcp_pilot.firestore.exceptions import DoesNotExist, InvalidCursor, MultipleObjectsFound

if TYPE_CHECKING:
    from gcp_pilot.firestore.document import Document


class Manager:
    LOOKUP_OPERATORS: ClassVar[dict[str, str]] = {
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
    _client: AsyncClient | None = None

    def __init__(self, doc_klass: type[Document], parent: Document | None = None):
        self.doc_klass = doc_klass
        self.parent = parent

    def _to_document(self, data: dict[str, Any]) -> Document:
        document = self.doc_klass.model_validate(data)
        document._manager = self
        return document

    @property
    def client(self) -> AsyncClient:
        if not self.__class__._client:
            self.__class__._client = firestore.AsyncClient()
        return self.__class__._client

    @property
    def collection_name(self) -> str:
        return self.doc_klass._meta.collection_name

    @property
    def collection(self) -> AsyncCollectionReference:
        if not self.parent:
            return self.client.collection(self.collection_name)

        if not self.parent.pk:
            raise ValueError("Cannot access subcollection on a document without a primary key.")

        return self.parent.objects.collection.document(self.parent.pk).collection(self.collection_name)

    async def get(self, pk: str | None = None, **kwargs) -> Document:
        if pk and kwargs:
            raise ValueError("Cannot use pk and kwargs together.")

        if pk:
            doc_ref = self.collection.document(pk)
            doc_snapshot = await doc_ref.get()
            if not doc_snapshot.exists:
                raise DoesNotExist(self.doc_klass, {"id": pk})

            data = doc_snapshot.to_dict() or {}
            data["id"] = doc_snapshot.id
            return self._to_document(data)

        results = [obj async for obj in self.filter(**kwargs)]
        if not results:
            raise DoesNotExist(self.doc_klass, filters=kwargs)
        if len(results) > 1:
            raise MultipleObjectsFound(self.doc_klass, filters=kwargs)
        return results[0]

    async def create(self, data: dict[str, Any]) -> Document:
        doc_ref = self.collection.document()
        document = self._to_document({"id": doc_ref.id, **data})

        batch = _active_batch.get()
        if batch is not None:
            batch.set(doc_ref, data)
        else:
            await doc_ref.set(data)

        return document

    async def update(self, pk: str, data: dict[str, Any]) -> None:
        doc_ref = self.collection.document(pk)
        batch = _active_batch.get()
        if batch is not None:
            batch.update(doc_ref, data)
        else:
            await doc_ref.update(data)

    async def delete(self, pk: str) -> None:
        doc_ref = self.collection.document(pk)
        batch = _active_batch.get()
        if batch is not None:
            batch.delete(doc_ref)
        else:
            await doc_ref.delete()

    async def filter(
        self,
        *,
        order_by: list[str] | None = None,
        limit: int | None = None,
        start_after: Document | dict[str, Any] | None = None,
        start_at: Document | dict[str, Any] | None = None,
        **kwargs,
    ) -> AsyncGenerator[Document]:
        query: Any = self.collection
        for key, value in kwargs.items():
            parts = key.split("__")
            if len(parts) > 1 and parts[-1] in self.LOOKUP_OPERATORS:
                operator = self.LOOKUP_OPERATORS[parts[-1]]
                field_path = ".".join(parts[:-1])
            else:
                operator = "=="
                field_path = ".".join(parts)

            field_filter = FieldFilter(field_path, operator, value)
            query = query.where(filter=field_filter)

        if order_by:
            for field in order_by:
                if field.startswith("-"):
                    field_name = field[1:]
                    direction = AsyncQuery.DESCENDING
                else:
                    field_name = field.lstrip("+")
                    direction = AsyncQuery.ASCENDING
                query = query.order_by(field_name, direction=direction)

        if not order_by and (start_after or start_at):
            raise ValueError("`order_by` is required when using `start_after` or `start_at`.")

        if start_after:
            if isinstance(start_after, dict | BaseModel):
                dumped_cursor = start_after if isinstance(start_after, dict) else start_after.model_dump()
                query = query.start_after(dumped_cursor)
            else:
                raise InvalidCursor("Cursor must be a dictionary or a Pydantic model.")

        if start_at:
            if not order_by:
                raise ValueError("`order_by` is required when using `start_at`.")
            if isinstance(start_at, dict | BaseModel):
                dumped_cursor = start_at if isinstance(start_at, dict) else start_at.model_dump()
                query = query.start_at(dumped_cursor)
            else:
                raise InvalidCursor("Cursor must be a dictionary or a Pydantic model.")

        if limit:
            query = query.limit(limit)

        stream = query.stream()
        async for doc_snapshot in stream:
            data = doc_snapshot.to_dict() or {}
            data["id"] = doc_snapshot.id
            yield self._to_document(data)
