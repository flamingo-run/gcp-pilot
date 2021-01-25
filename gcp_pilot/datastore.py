from __future__ import annotations

from enum import Enum
from dataclasses import dataclass
from typing import Type, Generator, get_args, Dict, ClassVar, Any, Tuple, get_type_hints, Union, Callable

from google.cloud import datastore

from gcp_pilot import exceptions


DEFAULT_PK_FIELD = 'id'


@dataclass
class DoesNotExist(Exception):
    cls: Type[EmbeddedDocument]
    filters: Dict


@dataclass
class MultipleObjectsFound(Exception):
    cls: Type[EmbeddedDocument]
    filters: Dict


@dataclass
class Manager:
    lookup_operators = {
        'eq': '=',
        'gt': '>',
        'gte': '>=',
        'lt': '<',
        'lte': '<=',
        'in': 'in',
    }

    _client: ClassVar[datastore.Client] = None
    fields: Dict[str, type]
    pk_field: str
    doc_klass: Type[Document]
    kind: str

    @classmethod
    def get_client(cls) -> datastore.Client:
        if not cls._client:
            cls._client = datastore.Client()
        return cls._client

    def build_key(self, pk: Any = None) -> datastore.Key:
        if pk:
            return self.get_client().key(self.kind, pk)
        # If no primary key is provided, we let the server create a new ID
        return self.get_client().allocate_ids(self.get_client().key(self.kind), 1)[0]

    def query(
            self,
            distinct_on: str = None,
            order_by: Union[str, List[str]] = None,
            page_size: int = None,
            **kwargs,
    ) -> datastore.query.Iterator:
        # base query
        query = self.get_client().query(kind=self.kind)
        if order_by:
            query.order = order_by
        if distinct_on:
            query.distinct_on = distinct_on

        # parse lookup args
        for key, value in kwargs.items():
            field, operator, value = self._build_filter(key=key, value=value)
            query.add_filter(field, operator, value)

        # prepare iterator
        cursor = None
        empty = False
        while not empty:
            query_iter = query.fetch(start_cursor=cursor, limit=page_size)
            page = next(query_iter.pages)
            for item in page:
                yield item
            cursor = query_iter.next_page_token
            empty = not bool(cursor)

    def filter(self, **kwargs) -> Generator[Document, None, None]:
        for entity in self.query(**kwargs):
            yield self.from_entity(entity=entity)

    def get(self, **kwargs) -> Document:
        if self.pk_field in kwargs:
            pk = kwargs[self.pk_field]
            entity = self.get_client().get(key=self.build_key(pk=pk))
            if entity:
                return self.from_entity(entity=entity)
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

    def create(self, obj: Document) -> Document:
        entity = self.to_entity(obj=obj)
        self.get_client().put(entity=entity)

        if not obj.pk:
            setattr(obj, obj.Meta.pk_field, entity.id)
        return obj

    def update(self, pk: str, **kwargs) -> Document:
        if kwargs:
            entity = self.get_client().get(key=self.build_key(pk=pk))
            # TODO: enable partial nested updates
            as_data = {
                key: value.Meta.to_dict(obj=value) if isinstance(value, EmbeddedDocument) else value
                for key, value in kwargs.items()
            }
            entity.update(as_data)
            self.get_client().put(entity=entity)
        return self.get(id=pk)

    def delete(self, pk: str = None):
        if pk:
            self.get_client().delete(key=self.build_key(pk=pk))
        else:
            keys = [entity.key for entity in self.query()]
            self.get_client().delete_multi(keys=keys)

    def _build_filter(self, key: str, value: Any) -> Tuple[str, str, Any]:
        lookup_fields = []
        operator = None

        parts = key.split('__') if '__' in key else key.split('.')
        for idx, part in enumerate(parts):
            is_last = idx == len(parts) - 1
            if part in self.lookup_operators:
                if not is_last:
                    raise exceptions.UnsupportedFormatException(f"Unsupported lookup key format {key}")
                operator = part
            elif idx == 0 and part not in self.fields:
                raise exceptions.ValidationError(
                    f"{part} is not a valid field. Excepted one of {' | '.join(self.fields)}"
                )
            else:
                lookup_fields.append(part)

        if isinstance(value, list):
            raise exceptions.ValidationError(
                f"Querying with OR clause is not supported"
            )

        return '.'.join(lookup_fields), (operator or '='), value

    def to_entity(self, obj: Document) -> datastore.Entity:
        entity = datastore.Entity(key=self.build_key(pk=obj.pk))
        if not obj.pk:
            setattr(obj, obj.Meta.pk_field, entity.id)
        entity.update(obj.Meta.to_dict(obj=obj))
        return entity

    def from_entity(self, entity: datastore.Entity) -> Document:
        data = dict(entity.items())
        if self.pk_field not in data:
            data[self.pk_field] = entity.id
        return self.doc_klass.Meta.from_dict(data=data)


@dataclass
class Metadata:
    fields: Dict[str, type]
    doc_klass: Type[EmbeddedDocument]
    pk_field: str = None

    def from_dict(self, data: Dict) -> EmbeddedDocument:
        data = data.copy()

        def _build(klass: Union[EmbeddedDocument, Callable], value: Any):
            if value is None:
                return value

            if issubclass(klass, EmbeddedDocument):
                return klass.Meta.from_dict(data=value)

            return klass(value)

        parsed_data = {}
        for field_name, field_klass in self.fields.items():
            try:
                raw_value = data[field_name]
            except KeyError:
                continue

            if getattr(field_klass, '_name', '') == 'List':
                inner_klass = get_args(field_klass)[0]  # TODO: test composite types
                item = [_build(klass=inner_klass, value=i) for i in raw_value]
            elif getattr(field_klass, '_name', '') == 'Dict':
                inner_klass_key, inner_klass_value = get_args(field_klass)
                item = {
                    _build(klass=inner_klass_key, value=k): _build(klass=inner_klass_value, value=v)
                    for k, v in raw_value.items()
                }
            else:
                item = _build(klass=field_klass, value=raw_value)
            parsed_data[field_name] = item

        return self.doc_klass(**parsed_data)

    def to_dict(self, obj: EmbeddedDocument, select_fields: List[str] = None) -> dict:
        # TODO handle custom dynamic fields
        def _unbuild(value):
            if value is None:
                return value
            if isinstance(value, EmbeddedDocument):
                return value.Meta.to_dict(obj=value)
            if isinstance(value, Enum):
                return value.value
            return value

        data = {}
        for field, field_klass in self.fields.items():
            if select_fields and field not in select_fields:
                continue

            raw_value = getattr(obj, field)

            if getattr(field_klass, '_name', '') == 'List':
                item = [_unbuild(value=i) for i in raw_value]
            elif getattr(field_klass, '_name', '') == 'Dict':
                item = {
                    _unbuild(value=k): _unbuild(value=v)
                    for k, v in raw_value.items()
                }
            else:
                item = _unbuild(value=raw_value)

            data[field] = item

        return data


class ORM(type):
    def __new__(cls, name, bases, attrs):
        is_abstract_model = name in ['Document', 'EmbeddedDocument']
        is_concrete_model = 'Document' in [base.__name__ for base in bases]

        if not is_abstract_model:
            all_fields = cls._extract_fields(attrs=attrs)

            # Since it was not explicitly provided, add id: str = None
            if DEFAULT_PK_FIELD not in attrs['__annotations__'] and is_concrete_model:
                attrs['__annotations__'][DEFAULT_PK_FIELD] = int
                attrs[DEFAULT_PK_FIELD] = None

        new_cls = super().__new__(cls, name, bases, attrs)

        if is_abstract_model:
            return new_cls

        # Metadata initialization
        hints = get_type_hints(new_cls)
        typed_fields = {k: v for k, v in hints.items() if k in all_fields}
        new_cls.Meta = Metadata(
            fields=typed_fields,
            doc_klass=new_cls,
        )

        # Manager initialization
        if is_concrete_model:
            new_cls.documents = Manager(
                fields=all_fields,
                pk_field=DEFAULT_PK_FIELD,
                doc_klass=new_cls,
                kind=name,
            )

            new_cls.Meta.pk_field = DEFAULT_PK_FIELD

        return new_cls

    @classmethod
    def _extract_fields(cls, attrs: Dict) -> Dict[str, type]:
        return attrs.get('__annotations__', {})


@dataclass
class EmbeddedDocument(metaclass=ORM):
    Meta: ClassVar[Metadata]

    @classmethod
    def deserialize(cls, **kwargs) -> EmbeddedDocument:
        return cls.Meta.from_dict(data=kwargs)

    def serialize(self) -> Dict:
        return self.Meta.to_dict(obj=self)


@dataclass
class Document(EmbeddedDocument):
    documents: ClassVar[Manager]

    @property
    def pk(self):
        return getattr(self, self.Meta.pk_field)

    def save(self) -> Document:
        return self.documents.create(obj=self)

    def delete(self) -> None:
        self.documents.delete(pk=self.id)
