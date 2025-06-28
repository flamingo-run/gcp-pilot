from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from gcp_pilot.firestore.document import Document
    from gcp_pilot.firestore.manager import Manager


class Subcollection:
    def __init__(self, document_class: type[Document]):
        self.document_class = document_class
        self._manager_cache = {}

    def __get__(self, instance: Document | None, owner: type[Document]) -> Manager | Subcollection:
        if instance is None:
            return self

        instance_id = id(instance)
        if instance_id not in self._manager_cache:
            from gcp_pilot.firestore.manager import Manager  # noqa: PLC0415

            manager = Manager(doc_klass=self.document_class, parent=instance)
            self._manager_cache[instance_id] = manager
        return self._manager_cache[instance_id]
