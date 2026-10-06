"""Elasticsearch client connection pooling."""

from elasticsearch import Elasticsearch
from threading import Lock
from typing import Optional

_es_client: Optional[Elasticsearch] = None
_es_lock = Lock()


def get_elasticsearch_client(url: str, api_key: str = "") -> Elasticsearch:
    """Get or create reusable Elasticsearch client (singleton, thread-safe)."""
    global _es_client
    if _es_client is not None:
        return _es_client
    with _es_lock:
        if _es_client is None:
            if api_key:
                _es_client = Elasticsearch(url, api_key=api_key)
            else:
                _es_client = Elasticsearch(url)
    return _es_client


def reset_elasticsearch_client():
    """Reset singleton (useful for testing)."""
    global _es_client
    with _es_lock:
        _es_client = None
