from __future__ import annotations

import abc
import inspect
import itertools
import json
import os
from collections import defaultdict
from collections.abc import Callable, Generator, Iterable
from dataclasses import dataclass
from datetime import date, datetime
from functools import cached_property
from typing import Any, ClassVar

from google.cloud import datastore
from pydantic import BaseModel

from gcp_pilot import exceptions

DEFAULT_NAMESPACE = os.environ.get("GCP_DATASTORE_NAMESPACE", default=None)
DEFAULT_PK_FIELD_NAME = "id"
DEFAULT_PK_FIELD_TYPE = int
MAX_ITEMS_PER_OPERATIONS = 500  # Datastore cannot write more than 500 items per call


def _chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


@dataclass
class DoesNotExist(Exception):
    cls: type[EmbeddedDocument]
    filters: dict


@dataclass
class MultipleObjectsFound(Exception):
    cls: type[EmbeddedDocument]
    filters: dict


def _starts_with_operator(lookup_fields, value) -> list[tuple[str, str, Any]]:
    field_name = ".".join(lookup_fields)
    return [
        (field_name, ">=", value),
        (field_name, "<=", f"{value}\ufffd"),
    ]


@dataclass
class Manager:
    LOOKUP_OPERATORS: ClassVar[dict[str, (str | Callable)]] = {
        "eq": "=",
        "gt": ">",
        "gte": ">=",
        "lt": "<",
        "lte": "<=",
        "in": "in",
        "startswith": _starts_with_operator,
    }
    doc_klass: type[EmbeddedDocument]

    @cached_property
    def client(self) -> datastore.Client:
        return datastore.Client(namespace=self.namespace)

    @property
    def namespace(self) -> str:
        return getattr(self.doc_klass.__config__, "namespace", ())

    @property
    def exclude_from_indexes(self):
        return getattr(self.doc_klass.__config__, "exclude_from_indexes", ())

    @property
    def kind(self) -> str:
        return "EmbeddedKind" if self.is_embedded else self.doc_klass.__name__

    @property
    def is_embedded(self) -> bool:
        return not issubclass(self.doc_klass, Document)

    @property
    def fields(self) -> Iterable[str]:
        return self.doc_klass.__fields__.keys()

    def build_key(self, pk: Any | None = None) -> datastore.Key:
        if self.is_embedded:
            return self.client.key(self.kind)

        if pk:
            typed_pk = DEFAULT_PK_FIELD_TYPE(pk)
            return self.client.key(self.kind, typed_pk)
        # If no primary key is provided, we let the server create a new ID
        return self.client.allocate_ids(self.client.key(self.kind), 1)[0]

    def _iterate(self, query, page_size: int = 10):
        cursor = None
        empty = False

        while not empty:
            query_iter = query.fetch(start_cursor=cursor, limit=page_size)

            page = next(query_iter.pages, [])
            yield from page
            next_cursor = query_iter.next_page_token
            empty = not bool(cursor) or cursor == next_cursor
            cursor = next_cursor

    def query(
        self,
        distinct_on: str | None = None,
        order_by: str | list[str] | None = None,
        page_size: int | None = None,
        **kwargs,
    ) -> datastore.query.Iterator:
        # base query
        query = self.client.query(kind=self.kind)
        if order_by:
            query.order = order_by
        if distinct_on:
            query.distinct_on = distinct_on

        # parse lookup args
        cross_filters = []
        for key, value in kwargs.items():
            all_filters = self._build_filter(key=key, value=value)
            for field_name, operator, field_value in all_filters:
                if operator == "in":
                    cross_filters.append((field_name, operator, field_value))
                else:
                    query.add_filter(field_name, operator, field_value)

        if not cross_filters:
            yield from self._iterate(query=query, page_size=page_size)
        else:
            # prepare combinations
            options = defaultdict(list)
            for name, operator, values in cross_filters:
                for value in values:
                    options[name].append((name, "=", value))

            combinations = itertools.product(*list(options.values()))

            found = set()
            for combination in combinations:
                current_query = query
                for field_name, operator, value in combination:
                    current_query = current_query.add_filter(field_name, operator, value)

                for item in self._iterate(query=current_query, page_size=page_size):
                    if item.id not in found:
                        yield item
                        found.add(item.id)

    def filter(self, **kwargs) -> Generator[Document, None, None]:
        for entity in self.query(**kwargs):
            yield self.doc_klass.from_entity(entity=entity)

    def get(self, **kwargs) -> Document:
        if DEFAULT_PK_FIELD_NAME in kwargs:
            pk = kwargs[DEFAULT_PK_FIELD_NAME]
            entity = self.client.get(key=self.build_key(pk=pk))
            if entity:
                return self.doc_klass.from_entity(entity=entity)
            raise DoesNotExist(self.doc_klass, pk)

        # Since we can't fetch directly from the key,
        # we filter and hope for just one object
        one_obj = None
        for obj in self.filter(**kwargs):
            if one_obj is not None:
                raise MultipleObjectsFound(self.doc_klass, filters=kwargs)
            one_obj = obj
        if not one_obj:
            raise DoesNotExist(self.doc_klass, filters=kwargs)
        return one_obj

    def create(self, **kwargs) -> Document:
        obj = self.doc_klass(**kwargs)
        entity = obj.to_entity()
        self.client.put(entity=entity)

        # if successfully saved, we assure the auto-generated ID is added to the final object
        if not obj.pk:
            setattr(obj, DEFAULT_PK_FIELD_NAME, entity.id)
        return obj

    def update(self, pk: str, **kwargs) -> Document:
        if kwargs:
            entity = self.client.get(key=self.build_key(pk=pk))
            # TODO: enable partial nested updates
            as_data = {
                key: value.to_dict() if isinstance(value, EmbeddedDocument) else value for key, value in kwargs.items()
            }
            entity.update(as_data)
            self.client.put(entity=entity)
        return self.get(id=pk)

    def delete(self, pk: str | None = None):
        if pk:
            self.client.delete(key=self.build_key(pk=pk))
        else:
            keys = [entity.key for entity in self.query()]
            for chunk in _chunks(keys, MAX_ITEMS_PER_OPERATIONS):
                self.client.delete_multi(keys=chunk)

    def _build_filter(self, key: str, value: Any) -> list[tuple[str, str, Any]]:
        operator = None

        *field_parts, lookup = key.split("__")
        if lookup:
            try:
                operator = self.LOOKUP_OPERATORS[lookup]

                if callable(operator):
                    field_name = ".".join(field_parts)
                    return operator(field_name, value)
            except KeyError:
                field_parts.append(lookup)

        if len(field_parts) > 1 and field_parts[0] not in self.fields:
            raise exceptions.ValidationError(
                f"{field_parts[0]} is not a valid field. Excepted one of {' | '.join(self.fields)}",
            )

        field_name = ".".join(field_parts)
        return [(field_name, (operator or "="), value)]


class EmbeddedDocument(BaseModel, abc.ABC):
    class Config:
        arbitrary_types_allowed = True
        use_enum_values = True
        keep_untouched = (cached_property,)

    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
        cls.documents = Manager(doc_klass=cls)

    @classmethod
    def from_dict(cls, **kwargs) -> EmbeddedDocument:
        return cls(**kwargs)

    def to_dict(self) -> dict:
        return self.dict()

    @classmethod
    def from_entity(cls, entity: datastore.Entity) -> EmbeddedDocument:
        data = dict(entity.items())
        data[DEFAULT_PK_FIELD_NAME] = entity.id
        return cls.from_dict(**data)

    def to_entity(self) -> datastore.Entity:
        exclude_from_indexes = self.documents.exclude_from_indexes
        if isinstance(self, Document):
            entity = datastore.Entity(
                key=self.documents.build_key(pk=self.pk),
                exclude_from_indexes=exclude_from_indexes,
            )
            if not self.pk:
                setattr(self, DEFAULT_PK_FIELD_NAME, entity.id)
        else:
            entity = datastore.Entity(
                key=self.documents.build_key(),
                exclude_from_indexes=exclude_from_indexes,
            )

        dict_obj = json.loads(self.json())

        data = {}
        for field_name, field_info in self.__fields__.items():
            if inspect.isclass(field_info.type_) and issubclass(field_info.type_, EmbeddedDocument):
                # recursively generate entities
                field_value = getattr(self, field_name)
                if isinstance(field_value, list | tuple):
                    value = [item.to_entity() for item in field_value]
                else:
                    value = field_value.to_entity() if field_value else None
            else:
                value = dict_obj[field_name]  # fetch json-friendly value
            data[field_name] = value

        entity.update(data)
        return entity


class Document(EmbeddedDocument, abc.ABC):
    id: DEFAULT_PK_FIELD_TYPE | None = None

    class Config(EmbeddedDocument.Config):
        exclude_from_indexes = ()
        namespace = DEFAULT_NAMESPACE
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.update_forward_refs()  # needed when base model has optional field o.O

    @property
    def pk(self):
        return getattr(self, "id", None)

    def save(self) -> Document:
        return self.documents.create(**self.dict())

    def delete(self) -> None:
        self.documents.delete(pk=self.pk)


__all__ = (
    "DoesNotExist",
    "MultipleObjectsFound",
    "EmbeddedDocument",
    "Document",
)
