"""Milvus client connection pooling."""

from pymilvus import MilvusClient
from threading import Lock
from typing import Optional

_milvus_client: Optional[MilvusClient] = None
_milvus_lock = Lock()


def get_milvus_client(uri: str, token: str = "") -> MilvusClient:
    """Get or create reusable MilvusClient (singleton, thread-safe)."""
    global _milvus_client
    if _milvus_client is not None:
        return _milvus_client
    with _milvus_lock:
        if _milvus_client is None:
            _milvus_client = MilvusClient(uri=uri, token=token)
    return _milvus_client


def reset_milvus_client():
    """Reset singleton (useful for testing)."""
    global _milvus_client
    with _milvus_lock:
        _milvus_client = None
