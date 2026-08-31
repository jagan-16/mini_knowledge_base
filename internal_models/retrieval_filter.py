from dataclasses import dataclass
from uuid import UUID


@dataclass
class RetrievalFilter:

    top_k: int = 20

    document_id: UUID | None = None

    metadata_filters: dict[str, str] | None = None