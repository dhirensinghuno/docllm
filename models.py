"""Data models for API requests and responses."""

from typing import List, Optional
from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """Response model for document upload."""

    document_id: str
    filename: str
    status: str
    message: str


class QuestionRequest(BaseModel):
    """Request model for asking questions."""

    question: str = Field(..., min_length=1, max_length=1000)
    document_id: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=20)


class AnswerResponse(BaseModel):
    """Response model for question answering."""

    answer: str
    sources: List[dict]
    document_id: Optional[str] = None


class DocumentListResponse(BaseModel):
    """Response model for document listing."""

    documents: List[dict]
    total: int


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    vector_db: str
    llm_type: str
