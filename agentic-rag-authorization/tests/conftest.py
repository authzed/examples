"""Shared fixtures and service-reachability helpers for the test suite.

Deterministic tests mock Elasticsearch/SpiceDB/Mistral and run with no infra.
Tests marked ``@pytest.mark.integration`` exercise real services; they use the
``require_services`` fixture to skip automatically when a service is unreachable.
Run the live suite with ``pytest -m integration`` after ``setup_environment.py``.
"""

import socket
from urllib.parse import urlparse

import pytest
from elasticsearch import Elasticsearch

from agentic_rag.grpc_helpers import create_insecure_spicedb_client


def _tcp_reachable(host: str, port: int, timeout: float = 0.5) -> bool:
    """Return True if a TCP connection to host:port succeeds quickly."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def elasticsearch_reachable(url: str = "http://localhost:9200") -> bool:
    parsed = urlparse(url)
    return _tcp_reachable(parsed.hostname or "localhost", parsed.port or 9200)


def spicedb_reachable(endpoint: str = "localhost:50051") -> bool:
    host, _, port = endpoint.partition(":")
    return _tcp_reachable(host or "localhost", int(port or "50051"))


def mistral_configured() -> bool:
    from agentic_rag.config import get_config

    return bool(get_config().mistral_api_key)


@pytest.fixture
def require_services():
    """Skip the calling test unless the requested live services are available.

    Reachability is checked against the SAME endpoints the code connects to
    (``config.elasticsearch_url`` / ``config.spicedb_endpoint``), so pointing
    those env vars at a non-localhost host gates the tests correctly.
    """
    from agentic_rag.config import get_config

    def _require(*, elasticsearch: bool = False, spicedb: bool = False, mistral: bool = False):
        config = get_config()
        if elasticsearch and not elasticsearch_reachable(config.elasticsearch_url):
            pytest.skip(f"Elasticsearch not reachable at {config.elasticsearch_url}")
        if spicedb and not spicedb_reachable(config.spicedb_endpoint):
            pytest.skip(f"SpiceDB not reachable at {config.spicedb_endpoint}")
        if mistral and not mistral_configured():
            pytest.skip("MISTRAL_API_KEY not configured")

    return _require


@pytest.fixture
def elasticsearch_client():
    """Create Elasticsearch client for integration tests."""
    return Elasticsearch("http://localhost:9200")


@pytest.fixture
def spicedb_client():
    """Create SpiceDB client for integration tests."""
    return create_insecure_spicedb_client("localhost:50051", "devtoken")


@pytest.fixture
def sample_state():
    """Create a sample graph state for testing."""
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
