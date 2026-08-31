from uuid import UUID
from internal_models.stored_file import StoredFile
from sqlalchemy.orm import Session
from database_model import Document
from internal_models.upload_data import UploadMetadata



class DocumentRepository:

    def __init__(self, db: Session):

        self.db = db

    def create_document(
        self,
        document_id: UUID,
        title: str,
        stored_file: StoredFile,
        metadata : UploadMetadata
    ):
        
        

        document = Document(
            
            id = document_id,
            
            title=title,

            file_name=stored_file.file_name,
            
            file_path=stored_file.file_path,


            content_type=stored_file.content_type,

            file_size=stored_file.file_size,

            doc_metadata =  metadata.document_data

            
        )

        self.db.add(document)


    def list_documents(
    self,
    
) -> list[Document]:

        query = (self.db.query(Document)
                .order_by(Document.created_at.desc())
                 .all()
                )
        return query

                

            