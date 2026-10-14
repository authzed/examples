"""Live integration test that pulls documents from a real Elasticsearch.

Requires Elasticsearch running and indexed by ``examples/setup_environment.py``,
plus a configured ``MISTRAL_API_KEY`` for the query embedding. Skipped
automatically when those are unavailable. Run with ``pytest -m integration``.
"""

import pytest

from agentic_rag.elasticsearch_client import reset_elasticsearch_client
from agentic_rag.nodes.retrieval_node import retrieval_node


@pytest.fixture(autouse=True)
def _reset_es_singleton():
    """Isolate the module-level Elasticsearch client around each test."""
    reset_elasticsearch_client()
    yield
    reset_elasticsearch_client()


@pytest.mark.integration
def test_retrieval_pulls_documents_from_elasticsearch(require_services):
    require_services(elasticsearch=True, mistral=True)

    state = {
        "query": "What are our engineering best practices?",
        "subject_id": "alice",
        "max_attempts": 1,
        "retrieval_attempt": 0,
        "messages": [],
        "reasoning": [],
        "retrieved_documents": [],
        "authorized_documents": [],
        "denied_count": 0,
        "authorization_passed": False,
        "answer": "",
    }

    out = retrieval_node(state)

    docs = out["retrieved_documents"]
    assert len(docs) > 0, "Expected Elasticsearch to return at least one document"
    assert out["retrieval_attempt"] == 1
    for doc in docs:
        assert doc.metadata.get("doc_id")
        assert "department" in doc.metadata
        assert "classification" in doc.metadata
        assert doc.page_content
