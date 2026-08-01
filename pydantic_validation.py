from uuid import UUID
from datetime import datetime
from pydantic import BaseModel , Field
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




class Citation(BaseModel):
    document_id: UUID
    title: str
    page_number: int | None = None
    chunk_index: int


class QuestionResponse(BaseModel):
    answer: str
    citations: List[Citation]