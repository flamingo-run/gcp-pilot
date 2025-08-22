from __future__ import annotations

import abc
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from gcp_pilot.firestore.subcollection import Subcollection

if TYPE_CHECKING:
    from gcp_pilot.firestore.manager import Manager


DEFAULT_PK_FIELD_NAME = "id"


class Options:
    def __init__(self, meta, klass: type[Document]):
        self.meta = meta
        self.model_class = klass
        self.collection_name: str = getattr(meta, "collection_name", klass.__name__.lower())
        self.pk_field_name: str = self._get_pk_field_name()

    def _get_pk_field_name(self) -> str:
        pk_field = [
            name for name, field in self.model_class.model_fields.items() if field.alias == DEFAULT_PK_FIELD_NAME
        ]
        if not pk_field:
            raise TypeError("No primary key field found.")
        return pk_field[0]


class Document(BaseModel, abc.ABC):
    id: str | None = Field(default=None, alias="id")
    _manager: Manager | None = PrivateAttr(default=None)

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
    def pk(self) -> str | None:
        return self.id

    @property
    def manager(self) -> Manager:
        return self._manager or self.__class__.documents

    async def save(self) -> Document:
        data = self.model_dump(mode="json", by_alias=True, exclude={self._meta.pk_field_name})

        saved_doc = await self.manager.create(data=data, pk=self.pk)
        self.id = saved_doc.pk
        return self

    async def update(self, **kwargs: Any) -> None:
        if not self.pk:
            raise ValueError("Cannot update a document without a primary key.")
        await self.manager.update(pk=self.pk, data=kwargs)

    async def refresh(self) -> None:
        if not self.pk:
            raise ValueError("Cannot refresh a document without a primary key.")
        refreshed_doc = await self.manager.get(pk=self.pk)
        object_attributes = refreshed_doc.model_dump()
        for key, value in object_attributes.items():
            setattr(self, key, value)

    async def delete(self) -> None:
        if not self.pk:
            raise ValueError("Cannot delete a document without a primary key.")
        await self.manager.delete(pk=self.pk)

    def __repr__(self):
        return f"<{self.__class__.__name__} pk={self.pk}>"
