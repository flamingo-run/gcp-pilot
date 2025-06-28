from __future__ import annotations

import abc
from typing import TYPE_CHECKING, ClassVar

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from gcp_pilot.firestore.manager import Manager


DEFAULT_PK_FIELD_NAME = "id"


class Options:
    def __init__(self, meta, klass: type[Document]):
        self.meta = meta
        self.model_class = klass
        self.collection_name: str = getattr(meta, "collection_name", klass.__name__)
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

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        use_enum_values=True,
    )

    if TYPE_CHECKING:
        objects: ClassVar[Manager]
        _meta: ClassVar[Options]

    def __init_subclass__(cls, *args, **kwargs):
        from gcp_pilot.firestore.manager import Manager  # noqa: PLC0415

        super().__init_subclass__(*args, **kwargs)
        cls.objects = Manager(doc_klass=cls)

        meta = getattr(cls, "Meta", None)
        cls._meta = Options(meta=meta, klass=cls)

    @property
    def pk(self):
        return self.id

    async def save(self) -> Document:
        data = self.model_dump(mode="json", by_alias=True, exclude={self._meta.pk_field_name})

        if not self.pk:
            created = await self.objects.create(data=data)
            self.id = created.id
            return self

        await self.objects.update(pk=self.pk, data=data)
        return self

    async def delete(self) -> None:
        if not self.pk:
            raise ValueError("Cannot delete a document without a primary key.")
        await self.objects.delete(pk=self.pk)

    def __repr__(self):
        return f"<{self.__class__.__name__} pk={self.pk}>"
