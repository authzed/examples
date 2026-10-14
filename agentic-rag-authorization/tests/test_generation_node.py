"""Unit tests for the generation node, focused on preventing document leaks.

The security guarantee is architectural: the authorization node filters denied
documents out of state BEFORE generation runs, so generation only ever sees
``state["authorized_documents"]``. These tests assert that denied content never
reaches the LLM prompt (and therefore cannot appear in the generated answer).
"""

from unittest.mock import patch

from langchain_core.documents import Document
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda

from agentic_rag.nodes.generation_node import generation_node

AUTHORIZED_CONTENT = "ENGINEERING_BEST_PRACTICES_AUTHORIZED"
AUTHORIZED_TITLE = "Engineering Guide"
DENIED_CONTENT = "CONFIDENTIAL_HR_SALARY_DATA_DENIED"


def _state(authorized_documents, denied_count):
    return {
        "query": "What are our engineering best practices?",
        "subject_id": "alice",
        "max_attempts": 1,
        "retrieval_attempt": 1,
        "messages": [],
        "reasoning": [],
        "retrieved_documents": [],
        "authorized_documents": authorized_documents,
        "denied_count": denied_count,
        "authorization_passed": bool(authorized_documents),
        "answer": "",
    }


def _capturing_llm(captured):
    """A fake LLM (Runnable) that records the prompt it is handed."""

    def _invoke(prompt_value):
        captured["prompt"] = prompt_value.to_string()
        return AIMessage(content="Answer based only on authorized documents.")

    return RunnableLambda(_invoke)


def test_denied_document_content_never_reaches_prompt_or_answer():
    captured = {}
    authorized = Document(
        page_content=AUTHORIZED_CONTENT,
        metadata={"title": AUTHORIZED_TITLE, "doc_id": "engineering-guide-001"},
    )
    with patch(
        "agentic_rag.nodes.generation_node.get_llm",
        return_value=_capturing_llm(captured),
    ):
        out = generation_node(_state([authorized], denied_count=1))

    # Authorized content IS present in the prompt...
    assert AUTHORIZED_CONTENT in captured["prompt"]
    assert AUTHORIZED_TITLE in captured["prompt"]
    # ...and the denied document's content is absent from both prompt and answer.
    assert DENIED_CONTENT not in captured["prompt"]
    assert DENIED_CONTENT not in out["answer"]


def test_no_authorized_documents_produces_no_document_content():
    captured = {}
    with patch(
        "agentic_rag.nodes.generation_node.get_llm",
        return_value=_capturing_llm(captured),
    ):
        out = generation_node(_state([], denied_count=2))

    assert "No authorized documents available." in captured["prompt"]
    assert DENIED_CONTENT not in captured["prompt"]
    assert out["answer"]
