from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Type, Generator, get_type_hints, get_args, Dict

from google.cloud import datastore


class ClientMixin:
    _client = None

    @classmethod
    def _get_client(cls) -> datastore.Client:
        if not cls._client:
            cls._client = datastore.Client()
        return cls._client


@dataclass
class DoesNotExist(Exception):
    cls: Type[EmbeddedDocument]
    pk: str


@dataclass
class MultipleObjectsFound(Exception):
    cls: Type[EmbeddedDocument]
    filters: Dict


operators = {
    'eq': '==',
    'gt': '>',
    'gte': '>=',
    'lt': '<',
    'lte': '<=',
    'in': 'in',
}


def query_operator(key: str) -> tuple:
    parts = key.split('__')
    field = parts[0]
    if len(parts) == 1:
        operator = '=='
    else:
        try:
            operator = operators[parts[1]]
        except KeyError as e:
            raise Exception(f"Unsupported query operator {parts[1]}") from e
    return field, operator


@dataclass
class EmbeddedDocument:
    @classmethod
    def _fields(cls):
        resolved_hints = get_type_hints(cls)
        field_names = [field.name for field in fields(cls)]
        return {
            name: resolved_hints[name]
            for name in field_names
            if not name.startswith('_')
        }

    @classmethod
    def deserialize(cls, **kwargs) -> EmbeddedDocument:
        return cls._from_dict(**kwargs)

    @classmethod
    def _from_dict(cls, **kwargs) -> EmbeddedDocument:
        data = kwargs.copy()

        def _build(klass, value):
            if value is None:
                return value

            if issubclass(klass, EmbeddedDocument):
                return klass._from_dict(**value)
            return klass(value)

        parsed_data = {}
        for field_name, field_klass in cls._fields().items():
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

        return cls(**parsed_data)

    def serialize(self) -> Dict:
        return self._to_dict()

    def _to_dict(self) -> dict:
        # TODO handle custom dynamic fields
        def _unbuild(value):
            if value is None:
                return value
            if isinstance(value, EmbeddedDocument):
                return value._to_dict()
            return value

        data = {}
        for field, field_klass in self.__class__._fields().items():
            raw_value = getattr(self, field)

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


@dataclass
class Document(ClientMixin, EmbeddedDocument):
    @property
    def pk(self) -> str:
        raise NotImplementedError()

    @classmethod
    def _get_key(cls, pk: str = None) -> datastore.Key:
        return cls._get_client().key(cls._kind(), pk)

    @property
    def _key(self):
        return self._get_key(pk=self.pk)

    @classmethod
    def _kind(cls) -> str:
        return cls.__name__

    @classmethod
    def list(cls, **kwargs) -> Generator[Document, None, None]:
        query = cls._get_client().query(kind=cls._kind())

        for key, value in kwargs.items():
            field, operator = query_operator(key=key)
            query.add_filter(field, operator, value)

        for entity in query.fetch():
            yield cls._from_dict(**cls.from_entity(entity=entity))

    @classmethod
    def get(cls, pk: str = None, **kwargs) -> Document:
        if pk is not None:
            entity = cls._get_client().get(key=cls._get_key(pk=pk))
            if entity:
                return cls._from_dict(**cls.from_entity(entity=entity))
        else:
            one_obj = None
            for obj in cls.list(**kwargs):
                if one_obj is not None:
                    raise MultipleObjectsFound(cls, filters=kwargs)
                one_obj = obj
            return one_obj
        raise DoesNotExist(cls, pk)

    def to_entity(self) -> datastore.Entity:
        if not self.pk:
            raise Exception()

        entity = datastore.Entity(key=self._key)
        entity.update(self._to_dict())
        return entity

    @classmethod
    def from_entity(cls, entity: datastore.Entity) -> Dict:
        return dict(entity.items())

    @classmethod
    def create(cls, **kwargs) -> Document:
        data = kwargs.copy()
        obj = cls.deserialize(**data)
        return obj.save()

    def save(self) -> Document:
        self._get_client().put(entity=self.to_entity())
        return self.get(pk=self.pk)

    @classmethod
    def update(cls, pk: str, **kwargs) -> Document:
        if kwargs:
            entity = cls._get_client().get(key=cls._get_key(pk=pk))
            # TODO: enable partial nested updates
            as_data = {
                key: value._to_dict() if isinstance(value, EmbeddedDocument) else value
                for key, value in kwargs.items()
            }
            entity.update(as_data)
            cls._get_client().put(entity=entity)
        return cls.get(pk=pk)

    @classmethod
    def delete(cls, pk: str) -> None:
        cls._get_client().delete(key=cls._get_key(pk=pk))
