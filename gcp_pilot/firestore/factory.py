from __future__ import annotations

import asyncio
from typing import Any, TypeGuard, TypeVar

from polyfactory.factories.pydantic_factory import ModelFactory
from polyfactory.persistence import AsyncPersistenceProtocol

from gcp_pilot.firestore.document import Document

T = TypeVar("T", bound=Document)


class FirestorePersistenceHandler(AsyncPersistenceProtocol[T]):
    async def save(self, data: T) -> T:
        return await data.save()

    async def save_many(self, data: list[T]) -> list[T]:
        results = await asyncio.gather(*[self.save(item) for item in data])
        return list(results)


class FirestoreFactory(ModelFactory[T]):
    __is_async__ = True
    __async_persistence__ = FirestorePersistenceHandler
    __is_base_factory__ = True

    @classmethod
    def is_supported_type(cls, value: Any) -> TypeGuard[type[T]]:
        return issubclass(value, Document)
