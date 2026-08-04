from fastapi import HTTPException

from fastapi import UploadFile

from internal_models.extracted_document import (
    ExtractedDocument,
    ExtractedPage,
)


class TXTExtractionService:

    def extract(
        self,
        file: UploadFile,
    ) -> ExtractedDocument:

        try:

            text = (
                file.file.read()
                .decode("utf-8")
                .replace("\x00", "")
                .strip()
            )

        except UnicodeDecodeError as exc:

            raise HTTPException(
                status_code=400,
                detail="Text file must be UTF-8 encoded."
            ) from exc
        return ExtractedDocument(
            filename=file.filename,
            title=file.filename,
            author=None,
            page_count=1,
            pages=[
                ExtractedPage(
                    page_number=1,
                    text=text,
                )
            ],
        )