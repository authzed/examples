"""API route handlers."""

import time
from typing import List
from fastapi import APIRouter, HTTPException

from .models import (
    QueryRequest,
    APIResponse,
    DocumentSummary,
    DeniedDocumentSummary,
    QueryStats,
    QueryResponseData,
    User,
)

# Import the existing RAG system
from agentic_rag.graph import run_agentic_rag_async

router = APIRouter()

# Available users for the demo
USERS: List[User] = [
    User(id="alice", name="Alice", department="Engineering"),
    User(id="bob", name="Bob", department="Sales"),
    User(id="hr_manager", name="HR Manager", department="HR"),
    User(id="finance_manager", name="Finance Manager", department="Finance"),
]


@router.get("/users")
async def get_users():
    """Get list of available users."""
    return {"success": True, "data": {"users": [user.dict() for user in USERS]}}


@router.get("/health")
async def health_check():
    """Check health of backend services."""
    # TODO: Actually check Weaviate + SpiceDB connectivity
    # For now, return optimistic health status
    return {
        "status": "healthy",
        "services": {
            "weaviate": "connected",
            "spicedb": "connected",
            "openai": "configured",
        },
    }


@router.post("/query")
async def execute_query(request: QueryRequest) -> APIResponse:
    """Execute a RAG query with authorization."""
    try:
        start_time = time.time()

        # Call the existing RAG system
        result = await run_agentic_rag_async(
            query=request.query,
            subject_id=request.subject_id,
            max_attempts=request.max_attempts,
        )

        execution_time_ms = int((time.time() - start_time) * 1000)

        # Format authorized documents
        authorized_docs = [
            DocumentSummary(
                doc_id=doc.metadata["doc_id"],
                title=doc.metadata["title"],
                content_preview=(
                    doc.page_content[:200] + "..."
                    if len(doc.page_content) > 200
                    else doc.page_content
                ),
            )
            for doc in result["authorized_documents"]
        ]

        # Format denied documents (retrieved but not authorized)
        denied_docs = []
        authorized_doc_ids = {doc.doc_id for doc in authorized_docs}

        for doc in result["retrieved_documents"]:
            doc_id = doc.metadata["doc_id"]
            if doc_id not in authorized_doc_ids:
                denied_docs.append(
                    DeniedDocumentSummary(
                        doc_id=doc_id,
                        title=doc.metadata["title"],
                        reason=f"User '{request.subject_id}' does not have permission to access this document",
                    )
                )

        # Build response
        response_data = QueryResponseData(
            query=result["query"],
            subject_id=result["subject_id"],
            answer=result["answer"],
            authorized_documents=authorized_docs,
            denied_documents=denied_docs,
            stats=QueryStats(
                retrieved_count=len(result["retrieved_documents"]),
                authorized_count=len(result["authorized_documents"]),
                denied_count=result["denied_count"],
                retrieval_attempts=result["retrieval_attempt"],
                execution_time_ms=execution_time_ms,
            ),
        )

        return APIResponse(success=True, data=response_data)

    except Exception as e:
        return APIResponse(
            success=False, error={"code": "EXECUTION_ERROR", "message": str(e)}
        )
