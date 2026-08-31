from dataclasses import dataclass


@dataclass
class UploadMetadata:

    document_data: dict[str, str]   