from uuid import UUID
from fastapi import FastAPI, UploadFile, File, Depends ,  Form
from services.conversation_service import ConversationService
from sqlalchemy.orm import Session
from database import get_db
from services.extraction.document_service import DocumentService
from repositories.document_repository import DocumentRepository
from database import Base , engine
from internal_models.upload_data import UploadMetadata
from services.query_service import QueryService
from pydantic_validation import (
    ConversationSummaryResponse,
    DocumentSummaryResponse,
    QuestionRequest,
    ConversationResponse
)

from fastapi.staticfiles import StaticFiles




app = FastAPI(title="Mini Knowledge Base")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
Base.metadata.create_all(bind=engine)


@app.post("/upload", tags=["Document"] , summary = "upload the document to query")
def upload(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    document_service = DocumentService(db)
    


    return document_service.process_document(file = file 
                                             )
@app.post(
    "/query",
    tags=["Query"],
    summary="Ask a question"
)
def ask_question(
    request: QuestionRequest,
    db: Session = Depends(get_db),
):

    query_service = QueryService(db=db)

    return query_service.ask(request)

@app.get(
    "/conversations",
    tags=["Conversation"],
    summary="List all conversations",
    response_model=list[ConversationSummaryResponse],
)
def list_conversations(
    db: Session = Depends(get_db),
):

    conversation_service = ConversationService(db)

    return conversation_service.list_conversations()


@app.get(
    "/documents",
    tags=["Document"],
    summary="List uploaded documents",
    response_model=list[DocumentSummaryResponse],
)
def list_documents(
        db: Session = Depends(get_db),
    ):

        repository = DocumentRepository(db)

        documents = repository.list_documents()

        return [

            DocumentSummaryResponse(

                document_id=document.id,

                title=document.title,

                metadata = document.doc_metadata ,

                created_at=document.created_at,
                
                updated_at=document.updated_at,

            )

            for document in documents

        ]
        
@app.get(
    "/conversations/{conversation_id}",
    tags=["Conversation"],
    summary="Get conversation messages",
    response_model=ConversationResponse,
)
def get_conversation(
    conversation_id: UUID,
    db: Session = Depends(get_db),
):

    conversation_service = ConversationService(
        db
    )

    return conversation_service.get_conversation(
        conversation_id
    )