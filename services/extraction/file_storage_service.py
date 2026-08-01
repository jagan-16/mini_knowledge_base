from pathlib import Path
from uuid import UUID
import shutil

from fastapi import UploadFile

from internal_models.stored_file import StoredFile


class FileStorageService:

    def __init__(
        self,
        upload_directory: str = "uploads",
    ):

        self.upload_directory = Path(upload_directory)

        self.upload_directory.mkdir(
            parents=True,
            exist_ok=True
        )

    def save_file(
        self,
        document_id: UUID,
        file: UploadFile,
    ) -> StoredFile:

        extension = Path(
            file.filename
        ).suffix

        file_name = f"{document_id}{extension}"

        file_path = self.upload_directory / file_name

        file.file.seek(0)

        with open(
            file_path,
            "wb",
        ) as output:

            shutil.copyfileobj(
                file.file,
                output
            )

        file.file.seek(0)

        return StoredFile(

            file_name=file_name,

            file_path=str(file_path),

            file_size=file_path.stat().st_size,

            content_type=file.content_type,
        )
        
    def delete_file(
        self,
        file_path: str,
    ):

        path = Path(file_path)

        if path.exists():

            path.unlink()