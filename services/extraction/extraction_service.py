from services.extraction.extraction_factory import ExtractionFactory


class ExtractionService:

    def __init__(self):

        self.factory = ExtractionFactory()

    def extract(self, file):

        extractor = self.factory.get_extractor(
            file.content_type
        )

        return extractor.extract(file)