"""Pydantic models for API requests and responses."""

from typing import List, Optional
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for RAG query."""

    query: str = Field(..., min_length=1, max_length=1000)
    subject_id: str
    max_attempts: int = Field(default=1, ge=1, le=5)


class DocumentSummary(BaseModel):
    """Summary of an authorized document."""

    doc_id: str
    title: str
    content_preview: str


class DeniedDocumentSummary(BaseModel):
    """Summary of a denied document."""

    doc_id: str
    title: str
    reason: str


class QueryStats(BaseModel):
    """Statistics about query execution."""

    retrieved_count: int
    authorized_count: int
    denied_count: int
    retrieval_attempts: int
    execution_time_ms: int


class QueryResponseData(BaseModel):
    """Data returned from a successful query."""

    query: str
    subject_id: str
    answer: str
    authorized_documents: List[DocumentSummary]
    denied_documents: List[DeniedDocumentSummary]
    stats: QueryStats


class APIResponse(BaseModel):
    """Standard API response wrapper."""

    success: bool
    data: Optional[QueryResponseData] = None
    error: Optional[dict] = None


class User(BaseModel):
    """User information."""

    id: str
    name: str
    department: str


class UsersResponse(BaseModel):
    """Response containing list of users."""

    success: bool
    data: dict


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    services: dict
