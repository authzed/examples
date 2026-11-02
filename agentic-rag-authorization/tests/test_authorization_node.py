"""Unit tests for the authorization node (the security boundary), SpiceDB mocked.

The authorization node ALWAYS runs and filters retrieved documents through
SpiceDB. These tests mock ``SpiceDBAuthorizer`` so the node's state-handling
logic is covered deterministically, with no live SpiceDB. For a real round-trip
against SpiceDB, see ``test_authorization_integration.py``.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.documents import Document
from langchain_spicedb.core import AuthorizationResult

from agentic_rag.nodes.authorization_node import authorization_node


def _doc(doc_id, content="content", title="Title", dept="engineering"):
    return Document(
        page_content=content,
        metadata={
            "doc_id": doc_id,
            "title": title,
            "department": dept,
            "classification": "internal",
        },
    )


def _state(documents, subject_id="alice"):
    return {
        "query": "q",
        "subject_id": subject_id,
        "max_attempts": 1,
        "retrieval_attempt": 1,
        "messages": [],
        "reasoning": [],
        "retrieved_documents": documents,
        "authorized_documents": [],
        "denied_count": 0,
        "authorization_passed": False,
        "answer": "",
    }


def _patch_authorizer(result):
    """Patch the module-level authorizer to return ``result`` from filter_documents."""
    authorizer = MagicMock()
    authorizer.filter_documents = AsyncMock(return_value=result)
    return patch(
        "agentic_rag.nodes.authorization_node._get_authorizer",
        return_value=authorizer,
    ), authorizer


@pytest.mark.asyncio
async def test_all_documents_authorized():
    docs = [_doc("doc-001"), _doc("doc-002")]
    result = AuthorizationResult(
        authorized_documents=docs,
        total_retrieved=2,
        total_authorized=2,
        authorization_rate=1.0,
        denied_resource_ids=[],
    )
    cm, authorizer = _patch_authorizer(result)
    with cm:
        out = await authorization_node(_state(docs))

    assert out["authorization_passed"] is True
    assert out["denied_count"] == 0
    assert out["authorized_documents"] == docs
    authorizer.filter_documents.assert_awaited_once_with(documents=docs, subject_id="alice")


@pytest.mark.asyncio
async def test_no_documents_authorized():
    docs = [_doc("doc-001"), _doc("doc-002")]
    result = AuthorizationResult(
        authorized_documents=[],
        total_retrieved=2,
        total_authorized=0,
        authorization_rate=0.0,
        denied_resource_ids=["doc-001", "doc-002"],
    )
    cm, _ = _patch_authorizer(result)
    with cm:
        out = await authorization_node(_state(docs))

    assert out["authorization_passed"] is False
    assert out["denied_count"] == 2
    assert out["authorized_documents"] == []


@pytest.mark.asyncio
async def test_mixed_authorization_some_but_not_all():
    """User can view some retrieved documents but not others (the common case)."""
    authorized = _doc("engineering-guide-001", dept="engineering")
    denied = _doc("hr-policy-003", dept="hr")
    result = AuthorizationResult(
        authorized_documents=[authorized],
        total_retrieved=2,
        total_authorized=1,
        authorization_rate=0.5,
        denied_resource_ids=["hr-policy-003"],
    )
    cm, _ = _patch_authorizer(result)
    with cm:
        out = await authorization_node(_state([authorized, denied]))

    # At least one authorized document means the flow may proceed to generation,
    # but the partial denial must still be recorded.
    assert out["authorization_passed"] is True
    assert out["denied_count"] == 1
    assert out["authorized_documents"] == [authorized]
    # The denied document must never leak into the authorized set.
    assert denied not in out["authorized_documents"]


@pytest.mark.asyncio
async def test_empty_retrieved_documents():
    result = AuthorizationResult(
        authorized_documents=[],
        total_retrieved=0,
        total_authorized=0,
        authorization_rate=0.0,
        denied_resource_ids=[],
    )
    cm, authorizer = _patch_authorizer(result)
    with cm:
        out = await authorization_node(_state([]))

    assert out["authorization_passed"] is False
    assert out["denied_count"] == 0
    authorizer.filter_documents.assert_awaited_once_with(documents=[], subject_id="alice")
