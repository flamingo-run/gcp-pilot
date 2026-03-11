from __future__ import annotations

import contextlib
import contextvars
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING

from google.cloud.firestore_v1.async_batch import AsyncWriteBatch
from google.cloud.firestore_v1.async_client import AsyncClient

if TYPE_CHECKING:
    from gcp_pilot.firestore.document import Document

MAX_OPS = 450  # Firestore limit is 500; leave margin


class _Batch:
    """Wraps an AsyncWriteBatch bound to a specific model's database.

    Automatically commits and starts a new batch when reaching MAX_OPS.
    """

    def __init__(self, model: type[Document]) -> None:
        self._model = model
        self._database_id: str = model._meta.database_id
        self._project_id: str | None = model._meta.project_id
        self._client: AsyncClient = model.documents.client
        self._batch: AsyncWriteBatch = self._client.batch()
        self._op_count: int = 0

    def _check_model(self, client: AsyncClient) -> None:
        if client is not self._client:
            raise RuntimeError(
                f"All operations in a batch must use the same database. "
                f"This batch is bound to database '{self._database_id}'."
            )

    async def _flush(self) -> None:
        """Commit current batch and start a new one."""
        await self._batch.commit()
        self._batch = self._client.batch()
        self._op_count = 0

    async def set(self, doc_ref, fields, client: AsyncClient) -> None:
        self._check_model(client)
        if self._op_count >= MAX_OPS:
            await self._flush()
        self._batch.set(doc_ref, fields)
        self._op_count += 1

    async def update(self, doc_ref, fields, client: AsyncClient) -> None:
        self._check_model(client)
        if self._op_count >= MAX_OPS:
            await self._flush()
        self._batch.update(doc_ref, fields)
        self._op_count += 1

    async def delete(self, doc_ref, client: AsyncClient) -> None:
        self._check_model(client)
        if self._op_count >= MAX_OPS:
            await self._flush()
        self._batch.delete(doc_ref)
        self._op_count += 1

    async def commit(self) -> None:
        if self._op_count > 0:
            await self._batch.commit()


_active_batch: contextvars.ContextVar[_Batch | None] = contextvars.ContextVar("_active_batch", default=None)


@contextlib.asynccontextmanager
async def batch(model: type[Document]) -> AsyncGenerator[None]:
    """Context manager for batching Firestore writes.

    All operations inside the batch must belong to the same database
    as the given model. Automatically splits into multiple batches
    if the number of operations exceeds the Firestore limit.

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
