import fitz
from fastapi import UploadFile
from io import BytesIO
from internal_models.extracted_document import ExtractedPage ,ExtractedDocument



class PDFExtractionService:

    def extract(self, file: UploadFile) -> ExtractedDocument:

        pdf_bytes = file.file.read()

        pdf = fitz.open(
            stream=BytesIO(pdf_bytes),
            filetype="pdf"
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
    metadata=metadata,
    pages=pages
)
        
  