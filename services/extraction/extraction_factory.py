from services.extraction.txt_extractor import TXTExtractionService
from services.extraction.image_link_service import ImageService
from services.groq_service import GroqService
from services.extraction.dockling_extraction import PDFExtractionService
from services.extraction.picture_semantic_service import PictureSemanticService

from fastapi import HTTPException

class ExtractionFactory:

    def __init__(self):

        self.extractors = {

            "application/pdf": PDFExtractionService(PictureSemanticService(
                        groq_service=GroqService(),
                        image_service=ImageService()
                )),

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