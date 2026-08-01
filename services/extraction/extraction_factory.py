from services.extraction.txt_extractor import TXTExtractionService
from services.extraction.pdf_extractor import PDFExtractionService
from fastapi import HTTPException

class ExtractionFactory:

    def __init__(self):

        self.extractors = {

            "application/pdf": PDFExtractionService(),

            "text/plain": TXTExtractionService()

        }

    def get_extractor(self, content_type):

        extractor = self.extractors.get(content_type)

        if extractor is None:
           raise HTTPException(
                           status_code=415,
                           detail="Unsupported file type."
                       )

        return extractor