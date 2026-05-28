"""Retrieval node - retrieve documents from Milvus using semantic vector search."""

import openai
from langchain_core.messages import SystemMessage
from langchain_core.documents import Document

from ..state import AgenticRAGState
from ..config import get_config
from ..logging_config import get_logger
from ..milvus_client import get_milvus_client
from ..node_helpers import log_node_execution

logger = get_logger("nodes.retrieval")


def _embed(text: str, api_key: str) -> list[float]:
    client = openai.OpenAI(api_key=api_key)
    response = client.embeddings.create(model="text-embedding-3-small", input=text)
    return response.data[0].embedding


def retrieval_node(state: AgenticRAGState) -> dict:
    """Retrieve documents from Milvus based on semantic similarity to the query."""
    config = get_config()

    with log_node_execution(
        logger,
        "retrieval",
        {"query": state["query"], "subject_id": state["subject_id"]},
    ):
        try:
            milvus_client = get_milvus_client(config.milvus_uri, config.milvus_token)
            query_embedding = _embed(state["query"], config.openai_api_key)

            results = milvus_client.search(
                collection_name="Documents",
                data=[query_embedding],
                anns_field="embedding",
                limit=5,
                output_fields=["doc_id", "title", "content", "department", "classification"],
            )

            documents = [
                Document(
                    page_content=hit["entity"]["content"],
                    metadata={
                        "doc_id": hit["entity"]["doc_id"],
                        "title": hit["entity"]["title"],
                        "department": hit["entity"]["department"],
                        "classification": hit["entity"]["classification"],
                    },
                )
                for hit in results[0]
            ]

            logger.info(
                "Retrieved documents",
                extra={
                    "document_count": len(documents),
                    "doc_ids": [doc.metadata.get("doc_id") for doc in documents],
                },
            )

            return {
                "retrieved_documents": documents,
                "retrieval_attempt": state["retrieval_attempt"] + 1,
                "messages": [
                    SystemMessage(content=f"Retrieved {len(documents)} documents from Milvus")
                ],
            }

        except Exception as e:
            logger.error(
                "Retrieval failed",
                extra={
                    "query": state["query"],
                    "error": str(e),
                    "error_type": type(e).__name__,
                },
                exc_info=True,
            )
            return {
                "retrieved_documents": [],
                "retrieval_attempt": state["retrieval_attempt"] + 1,
                "messages": [
                    SystemMessage(
                        content=f"Retrieval failed: {str(e)}. Unable to retrieve documents."
                    )
                ],
            }
