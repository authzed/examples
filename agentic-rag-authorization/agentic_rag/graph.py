"""LangGraph state machine for agentic RAG with authorization."""

from langgraph.graph import StateGraph, END
from .state import AgenticRAGState
from .nodes import (
    retrieval_node,
    authorization_node,
    reasoning_node,
    generation_node,
)
from .validation import validate_query, validate_subject_id, ValidationError


def should_retry_or_generate(state: AgenticRAGState) -> str:
    """Decide whether to retry retrieval or generate answer.

    After reasoning about authorization failures, decide:
    - If attempts remain and no authorized docs: retry retrieval
    - Otherwise: generate answer (possibly explaining access denial)
    """
    if (
        state["retrieval_attempt"] < state["max_attempts"]
        and len(state["authorized_documents"]) == 0
    ):
        return "retrieve"
    return "generate"


def should_reason_or_generate(state: AgenticRAGState) -> str:
    """Decide whether to reason about failures or generate answer.

    After authorization:
    - If we have authorized documents: generate answer
    - If no authorized documents AND attempts remain (max_attempts > 1): reason about what to do
    - If no authorized documents AND no attempts remain: generate answer with explanation

    Note: With max_attempts=1 (default), reasoning is skipped and we go directly to generation.
    This is more efficient for simple use cases where retry isn't needed.
    """
    if state["authorization_passed"]:
        return "generate"

    # Only reason if we have attempts remaining (max_attempts > 1 and not exhausted)
    if (
        state["max_attempts"] > 1
        and state["retrieval_attempt"] < state["max_attempts"]
    ):
        return "reason"

    # Otherwise, generate answer (possibly explaining access denial)
    return "generate"


def build_agentic_rag_graph():
    """Build the agentic RAG graph with deterministic authorization.

    Simplified Flow:
    1. Retrieval: Fetch documents from Weaviate
    2. Authorization: Deterministic permission check (security boundary)
    3. Conditional:
       - If authorized docs exist: Generate answer
       - If no authorized docs AND max_attempts > 1: Reason about retry strategy
       - If no authorized docs AND max_attempts == 1: Generate answer (with explanation)
    4. After reasoning (only with max_attempts > 1):
       - If attempts remain: Retry retrieval
       - Otherwise: Generate answer explaining constraints

    Note: With max_attempts=1 (default), the flow is just 3 nodes:
    Retrieve → Authorize → Generate
    """
    workflow = StateGraph(AgenticRAGState)

    # Add nodes
    workflow.add_node("retrieve", retrieval_node)
    workflow.add_node("authorize", authorization_node)  # ALWAYS runs
    workflow.add_node("reason", reasoning_node)
    workflow.add_node("generate", generation_node)

    # Define flow - start directly at retrieval
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "authorize")  # Deterministic auth

    # Conditional: after auth, either reason or generate
    workflow.add_conditional_edges(
        "authorize",
        should_reason_or_generate,
        {
            "reason": "reason",
            "generate": "generate",
        },
    )

    # Conditional: after reasoning, retry retrieval or generate
    workflow.add_conditional_edges(
        "reason",
        should_retry_or_generate,
        {
            "retrieve": "retrieve",
            "generate": "generate",
        },
    )

    workflow.add_edge("generate", END)

    return workflow.compile()


def run_agentic_rag(query: str, subject_id: str, max_attempts: int = 1) -> dict:
    """
    Run the agentic RAG graph with input validation (synchronous).

    This is the main entry point for running the agentic RAG system.
    It validates inputs before processing to ensure security and stability.

    Args:
        query: User query string
        subject_id: User/subject identifier for authorization
        max_attempts: Maximum number of retrieval attempts (default 1)

    Returns:
        Final state dict with answer and metadata

    Raises:
        ValidationError: If inputs are invalid
    """
    # Validate inputs
    query = validate_query(query)
    subject_id = validate_subject_id(subject_id)

    # Build graph
    graph = build_agentic_rag_graph()

    # Run graph
    initial_state = {
        "query": query,
        "subject_id": subject_id,
        "max_attempts": max_attempts,
        "retrieved_documents": [],
        "authorized_documents": [],
        "denied_count": 0,
        "reasoning": [],
        "retrieval_attempt": 0,
        "authorization_passed": False,
        "messages": [],
        "answer": None,
    }

    result = graph.invoke(initial_state)
    return result


async def run_agentic_rag_async(query: str, subject_id: str, max_attempts: int = 1) -> dict:
    """
    Run the agentic RAG graph with input validation (asynchronous).

    Async version of run_agentic_rag for use in async contexts.

    Args:
        query: User query string
        subject_id: User/subject identifier for authorization
        max_attempts: Maximum number of retrieval attempts (default 1)

    Returns:
        Final state dict with answer and metadata

    Raises:
        ValidationError: If inputs are invalid
    """
    # Validate inputs
    query = validate_query(query)
    subject_id = validate_subject_id(subject_id)

    # Build graph
    graph = build_agentic_rag_graph()

    # Run graph
    initial_state = {
        "query": query,
        "subject_id": subject_id,
        "max_attempts": max_attempts,
        "retrieved_documents": [],
        "authorized_documents": [],
        "denied_count": 0,
        "reasoning": [],
        "retrieval_attempt": 0,
        "authorization_passed": False,
        "messages": [],
        "answer": None,
    }

    result = await graph.ainvoke(initial_state)
    return result
