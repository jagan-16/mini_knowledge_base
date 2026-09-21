from io import BytesIO

from fastapi import HTTPException, UploadFile
from services.extraction.picture_semantic_service import PictureSemanticService
from docling.datamodel.base_models import DocumentStream , InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    TableStructureOptions,
    LayoutObjectDetectionOptions,
    TableFormerMode
)
from docling.document_converter import(
    DocumentConverter,
    PdfFormatOption,
    
)


class PDFExtractionService:

    def __init__(self,
        picture_semantic_service: PictureSemanticService,):
        self.picture_semantic_service = picture_semantic_service
        
        pipeline_options = PdfPipelineOptions(
             do_ocr = False ,
             do_table_structure = True , 
             generate_page_images=True
                    
    )
        
        pipeline_options.table_structure_options = TableStructureOptions(
            do_cell_matching = True,
            mode = TableFormerMode.ACCURATE
          
         
        )
        
        pipeline_options.layout_options = (
                    LayoutObjectDetectionOptions.from_preset(
                        "layout_heron_101"
                    )
                )
                        
   
        
       # pipeline_options.table_structure_options.do_cell_matching = True
        
        self.converter = DocumentConverter(
            format_options = {
                InputFormat.PDF:PdfFormatOption(
                    pipeline_options = pipeline_options
                )
            }
        )

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
            
        # Enrich PictureItems
        document = self.picture_semantic_service.enrich_document(
            result.document
        )
        return document 