from dataclasses import dataclass
from uuid import UUID


@dataclass
class RetrievedChunk:

    document_id: UUID

    document_title: str

    file_path: str

    page_number: int

    chunk_text: str

    similarity_score: float