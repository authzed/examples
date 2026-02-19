"""Helper functions for gRPC and SpiceDB authentication."""

import grpc
from threading import Lock
from typing import Optional


class BearerTokenInterceptor(grpc.UnaryUnaryClientInterceptor, grpc.UnaryStreamClientInterceptor):
    """
    gRPC interceptor that adds bearer token to all requests.

    This is for local development with SpiceDB's --grpc-no-tls flag.
    """

    def __init__(self, token: str):
        self._token = token

    def _add_authorization(self, client_call_details):
        """Add authorization metadata to the call."""
        metadata = []
        if client_call_details.metadata is not None:
            metadata = list(client_call_details.metadata)
        metadata.append(("authorization", f"Bearer {self._token}"))

        return grpc._interceptor._ClientCallDetails(
            client_call_details.method,
            client_call_details.timeout,
            metadata,
            client_call_details.credentials,
            client_call_details.wait_for_ready,
            client_call_details.compression,
        )

    def intercept_unary_unary(self, continuation, client_call_details, request):
        """Intercept unary-unary calls."""
        new_details = self._add_authorization(client_call_details)
        return continuation(new_details, request)

    def intercept_unary_stream(self, continuation, client_call_details, request):
        """Intercept unary-stream calls."""
        new_details = self._add_authorization(client_call_details)
        return continuation(new_details, request)


# Global singleton for SpiceDB client with thread-safe initialization
_spicedb_client: Optional["Client"] = None
_spicedb_lock = Lock()


def create_insecure_spicedb_client(endpoint: str, token: str):
    """
    Create a SpiceDB client for insecure connections (local development).

    This is for SpiceDB running with --grpc-no-tls flag.

    Args:
        endpoint: The SpiceDB endpoint (e.g., "localhost:50051")
        token: The bearer token (e.g., "devtoken")

    Returns:
        authzed.api.v1.Client configured for insecure connection
    """
    from authzed.api.v1 import Client

    # Create insecure channel with bearer token interceptor
    channel = grpc.insecure_channel(endpoint)
    interceptor = BearerTokenInterceptor(token)
    intercepted_channel = grpc.intercept_channel(channel, interceptor)

    # Create client bypassing __init__ and initialize with our channel
    client = Client.__new__(Client)
    client.init_stubs(intercepted_channel)

    return client


def get_spicedb_client(endpoint: str, token: str):
    """
    Get or create reusable SpiceDB client (singleton, thread-safe).

    This function provides connection pooling for SpiceDB by maintaining
    a single client instance across requests, eliminating connection overhead.

    Args:
        endpoint: The SpiceDB endpoint (e.g., "localhost:50051")
        token: The bearer token (e.g., "devtoken")

    Returns:
        authzed.api.v1.Client configured for insecure connection
    """
    from authzed.api.v1 import Client

    global _spicedb_client

    # Fast path: client already exists
    if _spicedb_client is not None:
        return _spicedb_client

    # Slow path: create new client with thread-safe lock
    with _spicedb_lock:
        # Double-check after acquiring lock
        if _spicedb_client is None:
            _spicedb_client = create_insecure_spicedb_client(endpoint, token)

    return _spicedb_client


def reset_spicedb_client():
    """
    Reset singleton (useful for testing).

    This allows tests to clear the cached client and create a fresh one.
    """
    global _spicedb_client
    with _spicedb_lock:
        _spicedb_client = None


# Backward compatibility - keep the old function name
def insecure_bearer_token_credentials(token: str):
    """
    Deprecated: Use create_insecure_spicedb_client instead.

    This function is kept for backward compatibility but doesn't work
    with authzed Client for insecure connections.
    """
    raise NotImplementedError(
        "For insecure SpiceDB connections, use create_insecure_spicedb_client() instead"
    )
