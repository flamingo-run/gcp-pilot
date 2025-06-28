from __future__ import annotations

from typing import TYPE_CHECKING, Any, AsyncGenerator, ClassVar

from google.cloud import firestore
from google.cloud.firestore_v1.async_client import AsyncClient
from google.cloud.firestore_v1.async_collection import AsyncCollectionReference
from google.cloud.firestore_v1.async_query import AsyncQuery
from google.cloud.firestore_v1.base_query import FieldFilter
from google.cloud.firestore_v1.field_path import FieldPath

from gcp_pilot.firestore.exceptions import DoesNotExist, MultipleObjectsFound

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

    def __init__(self, doc_klass: type[Document]):
        self.doc_klass = doc_klass

    @property
    def client(self) -> AsyncClient:
        if not self.__class__._client:
            # Using class-level client to have a single instance
            self.__class__._client = firestore.AsyncClient()  # type: ignore
        return self.__class__._client

    @property
    def collection_name(self) -> str:
        return self.doc_klass._meta.collection_name

    @property
    def collection(self) -> AsyncCollectionReference:
        return self.client.collection(self.collection_name)

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
            return self.doc_klass.model_validate(data)

        results = [obj async for obj in self.filter(**kwargs)]
        if not results:
            raise DoesNotExist(self.doc_klass, filters=kwargs)
        if len(results) > 1:
            raise MultipleObjectsFound(self.doc_klass, filters=kwargs)
        return results[0]

    async def create(self, data: dict[str, Any]) -> Document:
        doc_ref = self.collection.document()
        await doc_ref.set(data)
        data["id"] = doc_ref.id
        return self.doc_klass.model_validate(data)

    async def update(self, pk: str, data: dict[str, Any]) -> None:
        doc_ref = self.collection.document(pk)
        await doc_ref.update(data)

    async def delete(self, pk: str) -> None:
        doc_ref = self.collection.document(pk)
        await doc_ref.delete()

    async def filter(self, *, order_by: list[str] | None = None, **kwargs) -> AsyncGenerator[Document, None]:
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
                direction = AsyncQuery.ASCENDING
                if field.startswith("-"):
                    field = field[1:]
                    direction = AsyncQuery.DESCENDING
                query = query.order_by(field, direction=direction)

        stream = query.stream()
        async for doc_snapshot in stream:
            data = doc_snapshot.to_dict() or {}
            data["id"] = doc_snapshot.id
            yield self.doc_klass.model_validate(data)
