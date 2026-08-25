from io import BytesIO

from fastapi import HTTPException, UploadFile

from docling.datamodel.base_models import DocumentStream
from docling.document_converter import DocumentConverter



class PDFExtractionService:

    def __init__(self):
        self.converter = DocumentConverter()

    def extract(self, file: UploadFile):

        try:
            pdf_bytes = file.file.read()

            if not pdf_bytes:
                raise HTTPException(
                    status_code=400,
                    detail="Uploaded PDF is empty."
                )

            source = DocumentStream(
                name=file.filename or "document.pdf",
                stream=BytesIO(pdf_bytes),
            )

            result = self.converter.convert(
                source,
                max_file_size=20 * 1024 * 1024,
                max_num_pages=50,
                )   

        except HTTPException:
            raise

        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail="Failed to extract PDF."
            ) from exc

        if result.document is None:
            raise HTTPException(
                status_code=400,
                detail="Docling failed to create a document."
            )

        return result.document