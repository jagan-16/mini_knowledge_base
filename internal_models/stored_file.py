from dataclasses import dataclass

@dataclass
class StoredFile:

    file_name: str

    file_path: str

    content_type: str

    file_size: int