"""Tests for production-hardening features: structured logging, connection
pooling, input validation, and configuration.

(Moved from the repo-root ``test_improvements.py`` and converted from a
print/``main()`` script into real pytest assertions.)
"""

import json
import logging

import pytest


def test_structured_logging_emits_json(capsys):
    from agentic_rag.logging_config import setup_logging, get_logger

    root = logging.getLogger()
    saved_handlers, saved_level = root.handlers[:], root.level
    try:
        setup_logging(level="INFO")
        logger = get_logger("improvements_test")
        logger.info(
            "Test message",
            extra={"subject_id": "alice", "document_count": 5, "duration_ms": 123.45},
        )
        lines = [ln for ln in capsys.readouterr().out.splitlines() if ln.strip()]
        entry = json.loads(lines[-1])
    finally:
        root.handlers, root.level = saved_handlers, saved_level

    assert entry["level"] == "INFO"
    assert entry["logger"] == "agentic_rag.improvements_test"
    assert entry["message"] == "Test message"
    assert entry["subject_id"] == "alice"
    assert entry["document_count"] == 5
    assert entry["duration_ms"] == 123.45


def test_connection_pooling_helpers_exist():
    from agentic_rag.grpc_helpers import get_spicedb_client, reset_spicedb_client
    from agentic_rag.elasticsearch_client import (
        get_elasticsearch_client,
        reset_elasticsearch_client,
    )

    assert callable(get_spicedb_client)
    assert callable(reset_spicedb_client)
    assert callable(get_elasticsearch_client)
    assert callable(reset_elasticsearch_client)


def test_spicedb_authorizer_filter_documents_signature():
    import inspect
    from langchain_spicedb.core import SpiceDBAuthorizer

    params = inspect.signature(SpiceDBAuthorizer.filter_documents).parameters
    assert "subject_id" in params
    assert "documents" in params


def test_input_validation():
    from agentic_rag.validation import (
        validate_query,
        validate_subject_id,
        ValidationError,
    )

    assert validate_query("  test query  ") == "test query"
    assert validate_subject_id("alice_123") == "alice_123"

    with pytest.raises(ValidationError):
        validate_query("")
    with pytest.raises(ValidationError):
        validate_subject_id("alice@example.com")

    assert len(validate_query("x" * 2000)) == 1000


# Node error-handling is covered behaviorally rather than by source-text grep:
#   - retrieval  -> test_retrieval_node.py::test_retrieval_node_increments_attempt_on_failure
#   - authorization -> test_authorization_node.py


def test_config_has_log_level():
    from agentic_rag.config import get_config

    config = get_config()
    assert hasattr(config, "log_level")
    assert config.log_level == "INFO"


def test_graph_entrypoint_signature():
    import inspect
    from agentic_rag.graph import run_agentic_rag

    params = inspect.signature(run_agentic_rag).parameters
    assert "query" in params
    assert "subject_id" in params
