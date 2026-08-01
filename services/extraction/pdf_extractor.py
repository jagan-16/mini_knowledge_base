from fastapi import HTTPException
import fitz
from fastapi import UploadFile
from io import BytesIO
from fitz import FileDataError
from internal_models.extracted_document import ExtractedPage ,ExtractedDocument



class PDFExtractionService:

    def extract(self, file: UploadFile) -> ExtractedDocument:

        pdf_bytes = file.file.read()


        try:

            pdf = fitz.open(
                stream=BytesIO(pdf_bytes),
                filetype="pdf",
            )

        except FileDataError as exc:

            raise HTTPException(
                status_code=400,
                detail="Invalid or corrupted PDF file."
            ) from exc

        if pdf.is_encrypted:

            raise HTTPException(
                status_code=400,
                detail="Encrypted PDF files are not supported."
            )
    

        metadata = pdf.metadata

        pages = []

        for index, page in enumerate(pdf):

            pages.append(
                ExtractedPage(
                    page_number=index + 1,
                    text=page.get_text("text").strip()
                )
            )

        return ExtractedDocument(
    filename=file.filename,
    title=metadata.get("title") or file.filename,
    author=metadata.get("author"),
    page_count=len(pdf),
    pages=pages
)
        
  