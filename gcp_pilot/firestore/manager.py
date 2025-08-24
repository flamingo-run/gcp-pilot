from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

from google.cloud import firestore
from google.cloud.firestore_v1.async_client import AsyncClient
from google.cloud.firestore_v1.async_collection import AsyncCollectionReference

from gcp_pilot.firestore.atomic import _active_batch
from gcp_pilot.firestore.exceptions import DoesNotExist
from gcp_pilot.firestore.fqn import FQN
from gcp_pilot.firestore.query import Query

if TYPE_CHECKING:
    from gcp_pilot.firestore.document import Document


class Manager:
    _client: AsyncClient | None = None

    def __init__(self, doc_klass: type[Document], parent: Document | None = None):
        self.doc_klass = doc_klass
        self.parent = parent

    def _to_document(self, doc_snapshot: Any) -> Document:
        """Create a Document strictly from a Firestore DocumentSnapshot."""
        data: dict[str, Any] = doc_snapshot.to_dict() or {}
        data["id"] = doc_snapshot.id
        document = self.doc_klass.model_validate(data)
        document._manager = self

        # Build FQN using the reference path from the snapshot
        project = self.doc_klass._meta.project_id or self.client.project
        database = self.doc_klass._meta.database_id
        path: str = doc_snapshot.reference.path  # 'col/doc' or 'col/doc/sub/doc'
        collection_path, doc_id = path.rsplit("/", 1)
        document._fqn = FQN.from_parts(
            project_id=project,
            database_id=database,
            collection_path=collection_path,
            document_id=doc_id,
        ).full_name
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

        if not self.parent._fqn:
            raise ValueError("Cannot access subcollection on a document without a fully qualified name (fqn).")
        # parent._fqn is full path; parse and get relative path
        relative = FQN.parse(self.parent._fqn).relative_path
        parent_doc = self.client.document(relative)
        return parent_doc.collection(self.collection_name)

    def _get_query(self) -> Query:
        return Query(manager=self)

    def _normalize_for_firestore(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {k: self._normalize_for_firestore(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._normalize_for_firestore(v) for v in value]
        if isinstance(value, datetime.date) and not isinstance(value, datetime.datetime):
            return datetime.datetime.combine(value, datetime.time.min)
        return value

    async def get(self, id: str | None = None, **kwargs) -> Document:
        if id and kwargs:
            raise ValueError("Cannot use id and kwargs together.")

        if id:
            doc_ref = self.collection.document(id)
            doc_snapshot = await doc_ref.get()
            if not doc_snapshot.exists:
                raise DoesNotExist(self.doc_klass, {"id": id})

            return self._to_document(doc_snapshot)

        return await self.filter(**kwargs).get()

    async def create(self, id: str | None = None, **fields: Any) -> Document:
        doc_ref = self.collection.document(id)
        fields = self._normalize_for_firestore(fields)
        batch = _active_batch.get()
        if batch is not None:
            batch.set(doc_ref, fields)
            # Cannot fetch snapshot before commit; build document without using _to_document
            payload = {"id": doc_ref.id, **fields}
            document = self.doc_klass.model_validate(payload)
            document._manager = self
            project = self.doc_klass._meta.project_id or self.client.project
            database = self.doc_klass._meta.database_id
            collection_path = (
                self.collection_name
                if not self.parent
                else f"{FQN.parse(self.parent._fqn).relative_path}/{self.collection_name}"
            )
            document._fqn = FQN.from_parts(
                project_id=project,
                database_id=database,
                collection_path=collection_path,
                document_id=doc_ref.id,
            ).full_name
            return document
        else:
            await doc_ref.set(fields)
            doc_snapshot = await doc_ref.get()
            return self._to_document(doc_snapshot)

    async def update(self, id: str, **fields: Any) -> None:
        doc_ref = self.collection.document(id)
        fields = self._normalize_for_firestore(fields)
        batch = _active_batch.get()
        if batch is not None:
            batch.update(doc_ref, fields)
        else:
            await doc_ref.update(fields)

    async def delete(self, id: str) -> None:
        doc_ref = self.collection.document(id)
        batch = _active_batch.get()
        if batch is not None:
            batch.delete(doc_ref)
        else:
            await doc_ref.delete()

    def __getattr__(self, name: str) -> Any:
        return getattr(self._get_query(), name)
