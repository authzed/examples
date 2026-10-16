"""Live integration test for authorization against a real SpiceDB.

Requires SpiceDB running with the schema and relationships created by
``examples/setup_environment.py``. Skipped automatically when SpiceDB is
unreachable. Run with ``pytest -m integration``.
"""

import pytest
from langchain_core.documents import Document
from langchain_spicedb.core import SpiceDBAuthorizer

from agentic_rag.config import get_config


def _doc(doc_id, dept):
    return Document(
        page_content=f"content of {doc_id}",
        metadata={"doc_id": doc_id, "department": dept},
    )


@pytest.mark.integration
@pytest.mark.asyncio
async def test_mixed_authorization_against_live_spicedb(require_services):
    """alice (engineering) can view engineering docs but not HR docs: a mixed result.

    This is the "some but not all" case against real SpiceDB. We use fixed,
    known document IDs rather than semantic retrieval so the authorized/denied
    split is deterministic.
    """
    require_services(spicedb=True)

    config = get_config()
    authorizer = SpiceDBAuthorizer(
        spicedb_endpoint=config.spicedb_endpoint,
        spicedb_token=config.spicedb_token,
        resource_type="document",
        subject_type="user",
        permission="view",
        resource_id_key="doc_id",
    )

    documents = [
        _doc("engineering-architecture-001", "engineering"),  # alice CAN view
        _doc("hr-policy-003", "hr"),                           # alice CANNOT view
    ]

    result = await authorizer.filter_documents(documents=documents, subject_id="alice")

    authorized_ids = {d.metadata["doc_id"] for d in result.authorized_documents}
    assert "engineering-architecture-001" in authorized_ids
    assert "hr-policy-003" not in authorized_ids
    assert "hr-policy-003" in result.denied_resource_ids
    assert result.total_authorized == 1
    assert result.total_retrieved == 2
