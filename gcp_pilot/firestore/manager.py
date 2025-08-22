from __future__ import annotations

from typing import TYPE_CHECKING, Any

from google.cloud import firestore
from google.cloud.firestore_v1.async_client import AsyncClient
from google.cloud.firestore_v1.async_collection import AsyncCollectionReference

from gcp_pilot.firestore.atomic import _active_batch
from gcp_pilot.firestore.exceptions import DoesNotExist
from gcp_pilot.firestore.query import Query

if TYPE_CHECKING:
    from gcp_pilot.firestore.document import Document


class Manager:
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
        return self.__class__._client  # type: ignore

    @property
    def collection_name(self) -> str:
        return self.doc_klass._meta.collection_name

    @property
    def collection(self) -> AsyncCollectionReference:
        if not self.parent:
            return self.client.collection(self.collection_name)

        if not self.parent.pk:
            raise ValueError("Cannot access subcollection on a document without a primary key.")

        return self.parent.documents.collection.document(self.parent.pk).collection(self.collection_name)

    def _get_query(self) -> Query:
        return Query(manager=self)

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

        return await self.filter(**kwargs).get()

    async def create(self, data: dict[str, Any], pk: str | None = None) -> Document:
        doc_ref = self.collection.document(pk)
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

    def __getattr__(self, name: str) -> Any:
        return getattr(self._get_query(), name)
