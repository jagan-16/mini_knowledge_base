from uuid import UUID
from internal_models.stored_file import StoredFile
from sqlalchemy.orm import Session
from internal_models.extracted_document import ExtractedDocument
from database_model import Document
from internal_models.upload_data import UploadMetadata
from dataclasses import asdict


class DocumentRepository:

    def __init__(self, db: Session):

        self.db = db

    def create_document(
        self,
        document_id: UUID,
        extracted_document: ExtractedDocument,
        stored_file: StoredFile,
        metadata : UploadMetadata
    ):
        
        doc_metadata = {**asdict(metadata) }

        document = Document(
            
            id = document_id,

            title=extracted_document.title,

            file_name=stored_file.file_name,
            
            file_path=stored_file.file_path,


            content_type=stored_file.content_type,

            file_size=stored_file.file_size,

            doc_metadata =  doc_metadata

            
        )

        self.db.add(document)


    def list_documents(
    self,
    document_type: str | None = None,
    department: str | None = None,
) -> list[Document]:

        query = self.db.query(Document)

        if document_type is not None:

            query = query.filter(
                Document.doc_metadata["document_type"].astext
                == document_type
            )

        if department is not None:

            query = query.filter(
                Document.doc_metadata["department"].astext
                == department
            )

        return (
            query
            .order_by(Document.created_at.desc())
            .all()
        )

        

       