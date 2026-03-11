from __future__ import annotations

import contextlib
import contextvars
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from google.cloud.firestore_v1.async_batch import AsyncWriteBatch
from google.cloud.firestore_v1.async_client import AsyncClient

if TYPE_CHECKING:
    from gcp_pilot.firestore.document import Document


class _Batch:
    """Wraps an AsyncWriteBatch bound to a specific model's database."""

    def __init__(self, model: type[Document]) -> None:
        self._model = model
        self._database_id: str = model._meta.database_id
        self._project_id: str | None = model._meta.project_id
        self._client: AsyncClient = model.documents.client
        self._batch: AsyncWriteBatch = self._client.batch()

    def _check_model(self, client: AsyncClient) -> None:
        if client is not self._client:
            raise RuntimeError(
                f"All operations in a batch must use the same database. "
                f"This batch is bound to database '{self._database_id}'."
            )

    def set(self, doc_ref, fields, client: AsyncClient) -> None:
        self._check_model(client)
        self._batch.set(doc_ref, fields)

    def update(self, doc_ref, fields, client: AsyncClient) -> None:
        self._check_model(client)
        self._batch.update(doc_ref, fields)

    def delete(self, doc_ref, client: AsyncClient) -> None:
        self._check_model(client)
        self._batch.delete(doc_ref)

    async def commit(self) -> None:
        await self._batch.commit()


_active_batch: contextvars.ContextVar[_Batch | None] = contextvars.ContextVar("_active_batch", default=None)


@contextlib.asynccontextmanager
async def batch(model: type[Document]) -> AsyncGenerator[None]:
    """Context manager for batching Firestore writes.

    All operations inside the batch must belong to the same database
    as the given model.

    Usage:
        async with atomic.batch(Product):
            await Product.documents.create(name="A", price=10)
            await Product.documents.create(name="B", price=20)
    """
    if _active_batch.get() is not None:
        raise RuntimeError("Cannot start a new batch within an existing one.")

    b = _Batch(model)
    token = _active_batch.set(b)
    try:
        yield
        await b.commit()
    finally:
        _active_batch.reset(token)
