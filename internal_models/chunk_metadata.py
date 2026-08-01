from dataclasses import dataclass

@dataclass
class ChunkMetadata:

    document_type: str

    department: str | None = None