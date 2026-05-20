"""Authorization node - deterministic permission filtering via SpiceDB."""

from langchain_core.messages import SystemMessage
from langchain_spicedb.core import SpiceDBAuthorizer

from ..state import AgenticRAGState
from ..config import get_config
from ..logging_config import get_logger

logger = get_logger("nodes.authorization")

_authorizer: SpiceDBAuthorizer | None = None


def _get_authorizer() -> SpiceDBAuthorizer:
    global _authorizer
    if _authorizer is None:
        config = get_config()
        _authorizer = SpiceDBAuthorizer(
            spicedb_endpoint=config.spicedb_endpoint,
            spicedb_token=config.spicedb_token,
            resource_type="document",
            subject_type="user",
            permission="view",
            resource_id_key="doc_id",
        )
    return _authorizer


async def authorization_node(state: AgenticRAGState) -> dict:
    """
    Deterministic authorization node - ALWAYS runs, cannot be bypassed.

    Filters retrieved documents through SpiceDB's CheckBulkPermissions API.
    This is a security boundary - the agent cannot bypass this check.
    """
    authorizer = _get_authorizer()

    logger.info(
        "Starting authorization",
        extra={
            "subject_id": state["subject_id"],
            "document_count": len(state["retrieved_documents"]),
        },
    )

    result = await authorizer.filter_documents(
        documents=state["retrieved_documents"],
        subject_id=state["subject_id"],
    )

    logger.info(
        "Authorization results",
        extra={
            "authorized": result.total_authorized,
            "denied": len(result.denied_resource_ids),
            "denied_doc_ids": result.denied_resource_ids,
        },
    )

    return {
        "authorized_documents": result.authorized_documents,
        "denied_count": len(result.denied_resource_ids),
        "authorization_passed": result.total_authorized > 0,
        "messages": [
            SystemMessage(
                content=f"Authorization: {result.total_authorized}/{result.total_retrieved} documents authorized"
            )
        ],
    }
