"""Helper functions for authorization operations."""

from typing import List, Tuple
from authzed.api.v1 import (
    CheckBulkPermissionsRequest,
    CheckBulkPermissionsRequestItem,
    ObjectReference,
    SubjectReference,
    Client,
)
from langchain_core.documents import Document
from .logging_config import get_logger

logger = get_logger("authorization_helpers")


def batch_check_permissions(
    client: Client,
    subject_id: str,
    documents: List[Document],
) -> Tuple[List[Document], List[str]]:
    """
    Check permissions for multiple documents using SpiceDB's bulk API.

    Uses CheckBulkPermissions for efficient batch checking in a single request.
    This is 5-10x faster than sequential individual permission checks.

    Args:
        client: SpiceDB client
        subject_id: User/subject ID to check permissions for
        documents: List of documents to check permissions for

    Returns:
        Tuple of (authorized_documents, denied_doc_ids)
    """
    if not documents:
        return [], []

    logger.debug(
        "Starting batch permission check",
        extra={
            "subject_id": subject_id,
            "document_count": len(documents),
        },
    )

    try:
        # Build bulk request items
        items = []
        for doc in documents:
            doc_id = doc.metadata.get("doc_id")
            items.append(
                CheckBulkPermissionsRequestItem(
                    resource=ObjectReference(object_type="document", object_id=doc_id),
                    permission="view",
                    subject=SubjectReference(
                        object=ObjectReference(object_type="user", object_id=subject_id)
                    ),
                )
            )

        # Single bulk request to SpiceDB
        request = CheckBulkPermissionsRequest(items=items)
        response = client.CheckBulkPermissions(request)

        # Process results
        authorized_docs = []
        denied_doc_ids = []

        for i, pair in enumerate(response.pairs):
            doc = documents[i]
            doc_id = doc.metadata.get("doc_id")

            # Check if permission is granted
            # permissionship: 0=UNSPECIFIED, 1=NO_PERMISSION, 2=HAS_PERMISSION
            if pair.item.permissionship == 2:
                authorized_docs.append(doc)
            else:
                denied_doc_ids.append(doc_id)

        logger.debug(
            "Batch permission check complete",
            extra={
                "subject_id": subject_id,
                "authorized": len(authorized_docs),
                "denied": len(denied_doc_ids),
            },
        )

        return authorized_docs, denied_doc_ids

    except Exception as e:
        logger.error(
            "Batch permission check failed",
            extra={
                "subject_id": subject_id,
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )

        # Fail closed - treat error as all denied (security-safe default)
        denied_doc_ids = [doc.metadata.get("doc_id", "unknown") for doc in documents]
        return [], denied_doc_ids
