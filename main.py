

from fastapi import FastAPI, UploadFile, File, Depends ,  Form
from sqlalchemy.orm import Session
from database import get_db
from services.extraction.document_service import DocumentService
from database import Base , engine
from internal_models.upload_data import UploadMetadata




app = FastAPI(title="Mini Knowledge Base")

Base.metadata.create_all(bind=engine)


@app.post("/upload", tags=["Document"] , summary = "upload the document to query")
def upload(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    department: str | None = Form(None),
    db: Session = Depends(get_db),
):

    document_service = DocumentService(db)
    
    metadata = UploadMetadata(
    document_type=document_type,
    department=department,
)

    return document_service.process_document(file = file , metadata = metadata
                                             )

