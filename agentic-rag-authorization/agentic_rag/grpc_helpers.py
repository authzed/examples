"""Helper functions for SpiceDB client creation."""

from threading import Lock
from typing import Optional

from authzed.api.v1 import InsecureClient

_spicedb_client: Optional[InsecureClient] = None
_spicedb_lock = Lock()


def create_insecure_spicedb_client(endpoint: str, token: str) -> InsecureClient:
    """
    Create a SpiceDB client for insecure connections (local development).

    For SpiceDB running with --grpc-no-tls flag.
    """
    return InsecureClient(endpoint, token)


def get_spicedb_client(endpoint: str, token: str) -> InsecureClient:
    """
    Get or create reusable SpiceDB client (singleton, thread-safe).
    """
    global _spicedb_client

    if _spicedb_client is not None:
        return _spicedb_client

    with _spicedb_lock:
        if _spicedb_client is None:
            _spicedb_client = create_insecure_spicedb_client(endpoint, token)

    return _spicedb_client


def reset_spicedb_client():
    """Reset singleton (useful for testing)."""
    global _spicedb_client
    with _spicedb_lock:
        _spicedb_client = None
