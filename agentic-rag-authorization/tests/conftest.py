"""Test fixtures for agentic RAG tests."""

import pytest
from pymilvus import MilvusClient
from agentic_rag.grpc_helpers import create_insecure_spicedb_client


@pytest.fixture
def milvus_client():
    """Create MilvusClient for tests."""
    return MilvusClient(uri="http://localhost:19530")


@pytest.fixture
def spicedb_client():
    """Create SpiceDB client for tests."""
    return create_insecure_spicedb_client("localhost:50051", "devtoken")


@pytest.fixture
def sample_state():
    """Create sample state for testing."""
    return {
        "query": "Test query",
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
