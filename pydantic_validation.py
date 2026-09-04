from __future__ import annotations
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel , Field , field_validator
from typing import List , Literal , Any



class MetadataConditionRequest(BaseModel):
    field: str
    operator: Literal["eq", "neq", "in", "not_in" , "gt" , "lt" , "gte" , "lte"]
    value: str | int | float | list[str]


class MetadataFilterGroupRequest(BaseModel):
    operator: Literal["and", "or"]
    conditions: list[
        MetadataConditionRequest | MetadataFilterGroupRequest
    ]

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
    
    metadata_filters: MetadataFilterGroupRequest | None = None
    
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
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    
class ConversationSummaryResponse(BaseModel):

    conversation_id: UUID

    created_at: datetime
    
    updated_at: datetime

    
class MessageResponse(BaseModel):
    
    id : UUID

    role: str

    content: str
    
    citations: list[Citation]  = Field(default_factory=list)
    

    created_at: datetime
    
    updated_at: datetime
    
class ConversationResponse(BaseModel):

    conversation_id: UUID

    messages: list[MessageResponse]
    


