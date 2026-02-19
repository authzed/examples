"""Weaviate client connection pooling."""

import weaviate
from threading import Lock
from typing import Optional

# Global singleton for Weaviate client with thread-safe initialization
_weaviate_client: Optional[weaviate.Client] = None
_weaviate_lock = Lock()


def get_weaviate_client(url: str) -> weaviate.Client:
    """
    Get or create reusable Weaviate client (singleton, thread-safe).

    This function provides connection pooling for Weaviate by maintaining
    a single client instance across requests, eliminating connection overhead.

    Args:
        url: The Weaviate URL (e.g., "http://localhost:8080")

    Returns:
        weaviate.Client configured for the given URL
    """
    global _weaviate_client

    # Fast path: client already exists
    if _weaviate_client is not None:
        return _weaviate_client

    # Slow path: create new client with thread-safe lock
    with _weaviate_lock:
        # Double-check after acquiring lock
        if _weaviate_client is None:
            _weaviate_client = weaviate.Client(url)

    return _weaviate_client


def reset_weaviate_client():
    """
    Reset singleton (useful for testing).

    This allows tests to clear the cached client and create a fresh one.
    """
    global _weaviate_client
    with _weaviate_lock:
        _weaviate_client = None
