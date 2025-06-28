from __future__ import annotations

import contextlib
import contextvars
from collections.abc import AsyncGenerator

from google.cloud import firestore_v1
from google.cloud.firestore_v1.async_batch import AsyncWriteBatch

_active_batch: contextvars.ContextVar[AsyncWriteBatch | None] = contextvars.ContextVar("_active_batch", default=None)


@contextlib.asynccontextmanager
async def batch() -> AsyncGenerator[None]:
    if _active_batch.get() is not None:
        raise RuntimeError("Cannot start a new batch within an existing one.")

    firestore_batch = firestore_v1.AsyncClient().batch()
    token = _active_batch.set(firestore_batch)
    try:
        yield
        await firestore_batch.commit()
    finally:
        _active_batch.reset(token)
