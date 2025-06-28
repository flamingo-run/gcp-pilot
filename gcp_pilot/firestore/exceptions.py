from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gcp_pilot.firestore.document import Document


@dataclass
class DoesNotExist(Exception):
    cls: type[Document]
    filters: dict


@dataclass
class MultipleObjectsFound(Exception):
    cls: type[Document]
    filters: dict


class InvalidCursor(TypeError):
    pass
