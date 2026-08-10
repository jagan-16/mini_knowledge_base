from dataclasses import dataclass
from uuid import UUID


@dataclass
class RetrievalFilter:
    
    top_k: int = 20,
    
    document_id: UUID | None = None

    document_type: str | None = None

    department: str | None = None