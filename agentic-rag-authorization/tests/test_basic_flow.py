"""End-to-end integration tests for the agentic RAG graph.

These run the full graph against live Elasticsearch + SpiceDB + Mistral, so they
are marked ``integration`` and skip automatically when those services are
unavailable. Run with ``pytest -m integration`` after seeding the environment
via ``examples/setup_environment.py``.
"""

import pytest
from agentic_rag.graph import build_agentic_rag_graph


def _initial_state(query, subject_id, max_attempts):
    return {
        "query": query,
        "subject_id": subject_id,
        "max_attempts": max_attempts,
        "retrieval_attempt": 0,
        "messages": [],
        "reasoning": [],
        "retrieved_documents": [],
        "authorized_documents": [],
        "denied_count": 0,
        "authorization_passed": False,
        "answer": "",
    }


@pytest.mark.integration
@pytest.mark.asyncio
async def test_authorized_access(require_services):
    """Authorized user (alice, engineering) can access engineering documents."""
    require_services(elasticsearch=True, spicedb=True, mistral=True)
    graph = build_agentic_rag_graph()

    result = await graph.ainvoke(
        _initial_state("What are our engineering best practices?", "alice", 3)
    )

    assert len(result["authorized_documents"]) > 0
    assert result["authorization_passed"] is True
    assert result["answer"] != ""


@pytest.mark.integration
@pytest.mark.asyncio
async def test_denied_access(require_services):
    """Unauthorized user (bob, sales) is denied access to HR documents."""
    require_services(elasticsearch=True, spicedb=True, mistral=True)
    graph = build_agentic_rag_graph()

    result = await graph.ainvoke(
        _initial_state("What are the HR policies and employee guidelines?", "bob", 3)
    )

    assert len(result["authorized_documents"]) == 0
    assert result["denied_count"] > 0
    assert result["answer"] != ""
    # Answer should explain the access denial.
    assert "access" in result["answer"].lower() or "permission" in result["answer"].lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_retrieval_attempts(require_services):
    """System respects max retrieval attempts when authorization keeps failing."""
    require_services(elasticsearch=True, spicedb=True, mistral=True)
    graph = build_agentic_rag_graph()

    result = await graph.ainvoke(
        _initial_state("Query that will fail authorization", "unauthorized_user", 2)
    )

    assert result["retrieval_attempt"] <= 2
    assert result["answer"] != ""
