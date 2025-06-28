from __future__ import annotations

import asyncio
import datetime
from typing import Any, TypeGuard, TypeVar, cast

from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.persistence import AsyncPersistenceProtocol

from gcp_pilot.firestore.document import Document

T = TypeVar("T", bound=Document)


def _convert_dates_to_datetimes(data: Any) -> Any:
    if isinstance(data, dict):
        return {key: _convert_dates_to_datetimes(value) for key, value in data.items()}
    if isinstance(data, list):
        return [_convert_dates_to_datetimes(item) for item in data]
    if isinstance(data, datetime.date) and not isinstance(data, datetime.datetime):
        return datetime.datetime.combine(data, datetime.time.min)
    return data


class FirestorePersistenceHandler(AsyncPersistenceProtocol[T]):
    async def save(self, data: T) -> T:
        doc_data = data.model_dump(by_alias=True, exclude={"id"})
        converted_data = _convert_dates_to_datetimes(doc_data)
        created_doc = await data.__class__.objects.create(data=converted_data)
        return cast(T, created_doc)

    async def save_many(self, data: list[T]) -> list[T]:
        # TODO: This can be optimized to use a single batch operation
        return await asyncio.gather(*[self.save(item) for item in data])


class FirestoreFactory(ModelFactory[T]):
    __is_async__ = True
    __async_persistence__ = FirestorePersistenceHandler
    __is_base_factory__ = True

    @classmethod
    def is_supported_type(cls, value: Any) -> TypeGuard[type[T]]:
        return issubclass(value, Document)
