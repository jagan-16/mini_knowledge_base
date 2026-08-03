from uuid import UUID
from datetime import datetime
from pydantic import BaseModel , Field , field_validator
from typing import List

class UploadResponse(BaseModel):
    document_id: UUID
    title: str
    file_name: str
    content_type: str
    file_size: int
    chunk_count: int
    status: str
    created_at: datetime


class QuestionRequest(BaseModel):


    conversation_id: UUID | None = None
    
    question: str = Field(
        ...,
        min_length=3,
        max_length=2000
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=20
    )
    
    document_id: UUID | None = None
    
    document_type: str | None = None

    department: str | None = None
    
    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str):
        value = value.strip()
        if not value:
            raise ValueError(
                "Question cannot be empty."
            )
        return value



class Citation(BaseModel):
    document_id: UUID
    title: str
    page_number: int | None = None
    document_url : str | None = None


class QuestionResponse(BaseModel):
    conversation_id: UUID
    answer: str
    citations: List[Citation]
    
class DocumentSummaryResponse(BaseModel):

    document_id: UUID

    title: str

    document_type: str | None

    department: str | None

    created_at: datetime
    
class ConversationSummaryResponse(BaseModel):

    conversation_id: UUID

    created_at: datetime

    
class MessageResponse(BaseModel):
    
    id : UUID

    role: str

    content: str

    created_at: datetime
    
class ConversationResponse(BaseModel):

    conversation_id: UUID

    messages: list[MessageResponse]