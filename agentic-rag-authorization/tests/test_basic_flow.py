"""Basic integration tests for agentic RAG."""

import pytest
from agentic_rag.graph import build_agentic_rag_graph


@pytest.mark.asyncio
async def test_authorized_access():
    """Test that authorized user can access documents."""
    graph = build_agentic_rag_graph()

    result = await graph.ainvoke(
        {
            "query": "What are our engineering best practices?",
            "subject_id": "alice",
            "max_attempts": 3,
            "retrieval_attempt": 0,
            "messages": [],
            "reasoning": [],
            "retrieved_documents": [],
            "authorized_documents": [],
            "denied_count": 0,
            "authorization_passed": False,
            "answer": "",
        }
    )

    # Alice should have access to engineering documents
    assert len(result["authorized_documents"]) > 0
    assert result["authorization_passed"] is True
    assert result["answer"] != ""


@pytest.mark.asyncio
async def test_denied_access():
    """Test that unauthorized user is denied access."""
    graph = build_agentic_rag_graph()

    result = await graph.ainvoke(
        {
            "query": "What are the HR policies and employee guidelines?",
            "subject_id": "bob",
            "max_attempts": 3,
            "retrieval_attempt": 0,
            "messages": [],
            "reasoning": [],
            "retrieved_documents": [],
            "authorized_documents": [],
            "denied_count": 0,
            "authorization_passed": False,
            "answer": "",
        }
    )

    # Bob (sales) should not have access to HR documents
    assert len(result["authorized_documents"]) == 0
    assert result["denied_count"] > 0
    assert result["answer"] != ""
    # Answer should explain the access denial
    assert "access" in result["answer"].lower() or "permission" in result["answer"].lower()


@pytest.mark.asyncio
async def test_retrieval_attempts():
    """Test that system respects max retrieval attempts."""
    graph = build_agentic_rag_graph()

    result = await graph.ainvoke(
        {
            "query": "Query that will fail authorization",
            "subject_id": "unauthorized_user",
            "max_attempts": 2,
            "retrieval_attempt": 0,
            "messages": [],
            "reasoning": [],
            "retrieved_documents": [],
            "authorized_documents": [],
            "denied_count": 0,
            "authorization_passed": False,
            "answer": "",
        }
    )

    # Should not exceed max attempts
    assert result["retrieval_attempt"] <= 2
    assert result["answer"] != ""
