from fastapi import HTTPException, UploadFile


class DocumentValidator:

    def validate_file(
        self,
        file: UploadFile,
    ) -> None:

        file.file.seek(0, 2)

        file_size = file.file.tell()

        file.file.seek(0)

        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty.",
            )