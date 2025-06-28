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
        objects: ClassVar[Manager]
        _meta: ClassVar[Options]

    def __init_subclass__(cls, **kwargs):
        from gcp_pilot.firestore.manager import Manager  # noqa: PLC0415

        super().__init_subclass__(**kwargs)
        cls.objects = Manager(doc_klass=cls)
        meta = getattr(cls, "Meta", None)
        cls._meta = Options(meta=meta, klass=cls)

    def __init__(self, **data: Any):
        super().__init__(**data)
        self._manager = self.__class__.objects

    @property
    def pk(self) -> str | None:
        return self.id

    @property
    def manager(self) -> Manager:
        return self._manager or self.__class__.objects

    async def save(self) -> Document:
        data = self.model_dump(mode="json", by_alias=True, exclude={self._meta.pk_field_name})
        data.pop("id", None)  # Remove id from data, as it's the document key

        if not self.pk:
            created = await self.manager.create(data=data)
            self.id = created.id
            self._manager = created.manager
            return self

        await self.manager.update(pk=self.pk, data=data)
        return self

    async def delete(self) -> None:
        if not self.pk:
            raise ValueError("Cannot delete a document without a primary key.")
        await self.manager.delete(pk=self.pk)

    def __repr__(self):
        return f"<{self.__class__.__name__} pk={self.pk}>"
