"""Unit tests for retrieval node."""

import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document


@pytest.fixture
def sample_state():
    return {
        "query": "What are engineering best practices?",
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


def _make_hit(doc_id="doc-001", title="Test Doc", content="Content", dept="engineering", classification="internal"):
    return {
        "entity": {
            "doc_id": doc_id,
            "title": title,
            "content": content,
            "department": dept,
            "classification": classification,
        }
    }


def test_retrieval_node_returns_documents(sample_state):
    from agentic_rag.nodes.retrieval_node import retrieval_node

    with patch("agentic_rag.nodes.retrieval_node.get_milvus_client") as mock_get_client, \
         patch("agentic_rag.nodes.retrieval_node._embed") as mock_embed:
        mock_embed.return_value = [0.1] * 1536
        mock_client = MagicMock()
        mock_client.search.return_value = [[_make_hit()]]
        mock_get_client.return_value = mock_client

        result = retrieval_node(sample_state)

    assert len(result["retrieved_documents"]) == 1
    doc = result["retrieved_documents"][0]
    assert isinstance(doc, Document)
    assert doc.metadata["doc_id"] == "doc-001"
    assert doc.metadata["title"] == "Test Doc"
    assert doc.metadata["department"] == "engineering"
    assert doc.metadata["classification"] == "internal"
    assert doc.page_content == "Content"
    assert result["retrieval_attempt"] == 1


def test_retrieval_node_increments_attempt_on_failure(sample_state):
    from agentic_rag.nodes.retrieval_node import retrieval_node

    with patch("agentic_rag.nodes.retrieval_node.get_milvus_client") as mock_get_client, \
         patch("agentic_rag.nodes.retrieval_node._embed") as mock_embed:
        mock_embed.side_effect = RuntimeError("OpenAI unavailable")
        mock_get_client.return_value = MagicMock()

        result = retrieval_node(sample_state)

    assert result["retrieved_documents"] == []
    assert result["retrieval_attempt"] == 1


def test_embed_calls_openai():
    from agentic_rag.nodes.retrieval_node import _embed

    mock_response = MagicMock()
    mock_response.data = [MagicMock(embedding=[0.5] * 1536)]

    with patch("agentic_rag.nodes.retrieval_node.openai.OpenAI") as mock_oai:
        mock_oai.return_value.embeddings.create.return_value = mock_response
        result = _embed("hello world", "sk-test")

    assert result == [0.5] * 1536
    mock_oai.return_value.embeddings.create.assert_called_once_with(
        model="text-embedding-3-small", input="hello world"
    )
