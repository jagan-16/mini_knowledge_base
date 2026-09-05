from dataclasses import dataclass
from typing import Any


@dataclass
class UploadMetadata:

    document_data: dict[str, Any]   