"""Unit tests for Milvus client singleton."""

from unittest.mock import patch, MagicMock


def test_get_milvus_client_returns_singleton():
    from agentic_rag.milvus_client import get_milvus_client, reset_milvus_client
    reset_milvus_client()
    with patch("agentic_rag.milvus_client.MilvusClient") as mock_cls:
        mock_cls.return_value = MagicMock()
        client1 = get_milvus_client("http://localhost:19530")
        client2 = get_milvus_client("http://localhost:19530")
    assert client1 is client2
    mock_cls.assert_called_once_with(uri="http://localhost:19530", token="")


def test_reset_clears_singleton():
    from agentic_rag.milvus_client import get_milvus_client, reset_milvus_client
    reset_milvus_client()
    with patch("agentic_rag.milvus_client.MilvusClient") as mock_cls:
        mock_cls.return_value = MagicMock()
        get_milvus_client("http://localhost:19530")
        reset_milvus_client()
        get_milvus_client("http://localhost:19530")
    assert mock_cls.call_count == 2
