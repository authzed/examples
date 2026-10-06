"""Retrieval node - retrieve documents from Elasticsearch using semantic vector search."""

from langchain_mistralai import MistralAIEmbeddings
from langchain_core.messages import SystemMessage
from langchain_core.documents import Document

from ..state import AgenticRAGState
from ..config import get_config
from ..logging_config import get_logger
from ..elasticsearch_client import get_elasticsearch_client
from ..node_helpers import log_node_execution

logger = get_logger("nodes.retrieval")


def _embed(text: str, api_key: str) -> list[float]:
    embeddings = MistralAIEmbeddings(model="mistral-embed", api_key=api_key)
    return embeddings.embed_query(text)


def retrieval_node(state: AgenticRAGState) -> dict:
    """Retrieve documents from Elasticsearch based on semantic similarity to the query."""
    config = get_config()

    with log_node_execution(
        logger,
        "retrieval",
        {"query": state["query"], "subject_id": state["subject_id"]},
    ):
        try:
            es_client = get_elasticsearch_client(
                config.elasticsearch_url, config.elasticsearch_api_key
            )
            query_embedding = _embed(state["query"], config.mistral_api_key)

            response = es_client.search(
                index="documents",
                knn={
                    "field": "embedding",
                    "query_vector": query_embedding,
                    "k": 5,
                    "num_candidates": 50,
                },
                source=["doc_id", "title", "content", "department", "classification"],
            )

            documents = [
                Document(
                    page_content=hit["_source"]["content"],
                    metadata={
                        "doc_id": hit["_source"]["doc_id"],
                        "title": hit["_source"]["title"],
                        "department": hit["_source"]["department"],
                        "classification": hit["_source"]["classification"],
                    },
                )
                for hit in response["hits"]["hits"]
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
                    SystemMessage(content=f"Retrieved {len(documents)} documents from Elasticsearch")
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
