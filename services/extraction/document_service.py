from uuid import uuid4
from internal_models import extracted_document
from services.extraction.file_storage_service import FileStorageService
from fastapi import UploadFile
from sqlalchemy.orm import Session
from services.extraction.extraction_service import ExtractionService
from services.extraction.dockling_chuncking_service import ChunkingService
from services.extraction.embedding_service import EmbeddingService
from repositories.document_repository import DocumentRepository
from repositories.chunk_repository import ChunkRepository
from internal_models.upload_data import UploadMetadata
from services.validation.document_validation import (
    DocumentValidator,
)
from pathlib import Path



class DocumentService:




    def generate_document_title(
        self ,
        filename: str | None,
    ) -> str:

        if not filename:
            return "document"

        return Path(filename).stem
    
    
    def __init__(self, db: Session):
        
        self.db = db
        
        
        self.document_repository = DocumentRepository(db)
        self.chunk_repository = ChunkRepository(db)
        
        self.document_validator = DocumentValidator()
        
        
        self.file_storage_service = FileStorageService()
        self.extraction_service = ExtractionService()
        self.chunking_service = ChunkingService()
        self.embedding_service = EmbeddingService()

    def process_document(
        self,
        file: UploadFile,
        metadata: UploadMetadata
        
    ):
        
        self.document_validator.validate_file(file)

        document_id = uuid4()
        stored_file = None
       
        try:
           
                    # Step 1 : Store original file
                    stored_file = self.file_storage_service.save_file(

                        document_id = document_id,

                        file= file,
                    )
                    # Step 2: Extract PDF
                    extracted_document = self.extraction_service.extract(file)

                

                    # Step 3: Save document
                    self.document_repository.create_document(
                        document_id=document_id,
                        title = self.generate_document_title(file.filename),
                        stored_file=stored_file,
                        metadata=metadata,
                        
                    )

                    # Step 4: Create chunks
                    chunks = self.chunking_service.chunk_document(
                        extracted_document
                    )

                    # Step 5: Generate embeddings
                    embeddings = self.embedding_service.generate_embeddings(
                        chunks
                    )

                    # Step 6: Save chunks
                    self.chunk_repository.save_chunks(
                        document_id=document_id,
                        chunks=chunks,
                        embeddings=embeddings,
                    )
                    
                    
                    self.db.commit()
                    
                    return {
                            "document_id": str(document_id),
                            "message": "Upload successful"
                        }
        except Exception:

            self.db.rollback()
            
            if stored_file is not None:

                    self.file_storage_service.delete_file(
                        stored_file.file_path
                    )

            raise

        