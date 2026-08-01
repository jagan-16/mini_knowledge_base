from dataclasses import dataclass


@dataclass
class UploadMetadata:

    document_type: str

    department: str | None = None