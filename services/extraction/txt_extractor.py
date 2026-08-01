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

        text = (
            file.file.read()
            .decode("utf-8")
            .strip()
        )

        metadata = {
            "title": file.filename,
            "author": None,
            "format": "Text File",
            "content_type": file.content_type,
        }

        return ExtractedDocument(
            filename=file.filename,
            title=file.filename,
            author=None,
            page_count=1,
            metadata=metadata,
            pages=[
                ExtractedPage(
                    page_number=1,
                    text=text,
                )
            ],
        )