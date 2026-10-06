"""Unit tests for Elasticsearch client singleton."""

from unittest.mock import patch, MagicMock


def test_get_elasticsearch_client_returns_singleton():
    from agentic_rag.elasticsearch_client import (
        get_elasticsearch_client,
        reset_elasticsearch_client,
    )
    reset_elasticsearch_client()
    with patch("agentic_rag.elasticsearch_client.Elasticsearch") as mock_cls:
        mock_cls.return_value = MagicMock()
        client1 = get_elasticsearch_client("http://localhost:9200")
        client2 = get_elasticsearch_client("http://localhost:9200")
    assert client1 is client2
    mock_cls.assert_called_once_with("http://localhost:9200")


def test_reset_clears_singleton():
    from agentic_rag.elasticsearch_client import (
        get_elasticsearch_client,
        reset_elasticsearch_client,
    )
    reset_elasticsearch_client()
    with patch("agentic_rag.elasticsearch_client.Elasticsearch") as mock_cls:
        mock_cls.return_value = MagicMock()
        get_elasticsearch_client("http://localhost:9200")
        reset_elasticsearch_client()
        get_elasticsearch_client("http://localhost:9200")
    assert mock_cls.call_count == 2


def test_api_key_passed_when_set():
    from agentic_rag.elasticsearch_client import (
        get_elasticsearch_client,
        reset_elasticsearch_client,
    )
    reset_elasticsearch_client()
    with patch("agentic_rag.elasticsearch_client.Elasticsearch") as mock_cls:
        mock_cls.return_value = MagicMock()
        get_elasticsearch_client("http://localhost:9200", api_key="secret")
    mock_cls.assert_called_once_with("http://localhost:9200", api_key="secret")
