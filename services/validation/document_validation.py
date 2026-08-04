from fastapi import HTTPException

from internal_models.extracted_document import ExtractedDocument


class DocumentValidator:

    def validate(
        self,
        document: ExtractedDocument,
    ) -> None:

        if document.page_count == 0:

            raise HTTPException(
                status_code=400,
                detail="Document contains no pages."
            )

        has_text = any(

            page.text.strip().replace("\x00", "")

            for page in document.pages

        )

        if not has_text:

            raise HTTPException(
                status_code=400,
                detail="No extractable text found."
            )