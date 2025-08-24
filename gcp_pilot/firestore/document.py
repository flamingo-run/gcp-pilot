from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from gcp_pilot.firestore.fqn import FQN
from gcp_pilot.firestore.subcollection import Subcollection

if TYPE_CHECKING:
    from gcp_pilot.firestore.manager import Manager


DEFAULT_PK_FIELD_NAME = "id"


class Options:
    def __init__(self, meta, klass: type[Document]):
        self.meta = meta
        self.model_class = klass
        self.project_id = getattr(meta, "project_id", None)
        self.database_id = getattr(meta, "database_id", "(default)")
        self.collection_name: str = getattr(meta, "collection_name", klass.__name__.lower())


class Document(BaseModel, abc.ABC):
    id: str | None = Field(default=None)
    _manager: Manager | None = PrivateAttr(default=None)
    _fqn: str | None = PrivateAttr(default=None)

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        use_enum_values=True,
        ignored_types=(Subcollection,),
    )

    if TYPE_CHECKING:
        documents: ClassVar[Manager]
        _meta: ClassVar[Options]

    def __init_subclass__(cls, **kwargs):
        from gcp_pilot.firestore.manager import Manager  # noqa: PLC0415

        super().__init_subclass__(**kwargs)
        manager = Manager(doc_klass=cls)
        cls.documents = manager
        meta = getattr(cls, "Meta", None)
        cls._meta = Options(meta=meta, klass=cls)

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._manager = self.__class__.documents

    @property
    def manager(self) -> Manager:
        return self._manager or self.__class__.documents

    async def save(self) -> Document:
        data = self.model_dump(mode="json", by_alias=True, exclude={"id"})

        # For new documents, pass only the ID (or None to auto-generate) and fields as kwargs
        saved_doc = await self.manager.create(id=self.id, **data)

        # Sync identifiers from persisted document
        self.id = saved_doc.id
        self._fqn = saved_doc._fqn
        return self

    async def update(self, **kwargs: Any) -> None:
        if not (self.id or self.fqn):
            raise ValueError("Cannot update a document without a fully qualified name (fqn).")
        await self.manager.update(id=self.document_id, **kwargs)

    async def refresh(self) -> None:
        if not (self.id or self.fqn):
            raise ValueError("Cannot refresh a document without a fully qualified name (fqn).")
        refreshed_doc = await self.manager.get(id=self.document_id)
        object_attributes = refreshed_doc.model_dump()
        for key, value in object_attributes.items():
            setattr(self, key, value)
        # Ensure fqn (path) is also refreshed
        self._fqn = refreshed_doc._fqn

    async def delete(self) -> None:
        if not (self.id or self.fqn):
            raise ValueError("Cannot delete a document without a fully qualified name (fqn).")
        await self.manager.delete(id=self.document_id)

    def __repr__(self):
        return f"<{self.__class__.__name__} fqn={self.fqn}>"

    @property
    def fqn(self) -> FQN | None:
        return FQN.parse(self._fqn) if self._fqn else None

    @property
    def document_id(self) -> str | None:
        if self.id:
            return self.id
        if self.fqn:
            return self.fqn.document_id
        raise ValueError("FQN is not set.")
