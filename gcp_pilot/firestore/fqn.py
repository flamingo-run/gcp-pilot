from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FQN:
    project_id: str
    database_id: str
    relative_path: str

    @classmethod
    def from_parts(cls, *, project_id: str, database_id: str, collection_path: str, document_id: str) -> FQN:
        relative = f"{collection_path}/{document_id}"
        return cls(project_id=project_id, database_id=database_id, relative_path=relative)

    @classmethod
    def parse(cls, full_name: str) -> FQN:
        # projects/<proj>/databases/<db>/documents/<relative>
        parts = full_name.split("/")
        if len(parts) < 6 or parts[0] != "projects" or parts[2] != "databases" or parts[4] != "documents":
            raise ValueError("Invalid Firestore FQN format")
        project_id = parts[1]
        database_id = parts[3]
        relative = "/".join(parts[5:])
        return cls(project_id=project_id, database_id=database_id, relative_path=relative)

    @property
    def full_name(self) -> str:
        return f"projects/{self.project_id}/databases/{self.database_id}/documents/{self.relative_path}"

    @property
    def document_id(self) -> str:
        return self.relative_path.rsplit("/", 1)[-1]

    def child(self, *segments: str) -> FQN:
        return FQN(
            project_id=self.project_id,
            database_id=self.database_id,
            relative_path=f"{self.relative_path}/{'/'.join(segments)}",
        )
