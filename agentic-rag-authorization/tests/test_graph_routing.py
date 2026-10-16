"""Unit tests for the graph routing / conditional-edge functions (graph.py:14-51).

These pure functions decide the control flow of the state machine after
authorization and after reasoning. They are deterministic, so no mocking or
live services are required.
"""

from agentic_rag.graph import should_retry_or_generate, should_reason_or_generate


def _state(**overrides):
    state = {
        "retrieval_attempt": 0,
        "max_attempts": 1,
        "authorized_documents": [],
        "authorization_passed": False,
    }
    state.update(overrides)
    return state


class TestShouldRetryOrGenerate:
    def test_retries_when_attempts_remain_and_no_authorized_docs(self):
        state = _state(retrieval_attempt=1, max_attempts=3, authorized_documents=[])
        assert should_retry_or_generate(state) == "retrieve"

    def test_generates_when_authorized_docs_exist(self):
        state = _state(retrieval_attempt=1, max_attempts=3, authorized_documents=["doc"])
        assert should_retry_or_generate(state) == "generate"

    def test_generates_when_attempts_exhausted(self):
        state = _state(retrieval_attempt=3, max_attempts=3, authorized_documents=[])
        assert should_retry_or_generate(state) == "generate"

    def test_generates_when_exhausted_even_with_docs(self):
        state = _state(retrieval_attempt=3, max_attempts=3, authorized_documents=["doc"])
        assert should_retry_or_generate(state) == "generate"


class TestShouldReasonOrGenerate:
    def test_generates_when_authorization_passed(self):
        state = _state(authorization_passed=True, max_attempts=3, retrieval_attempt=1)
        assert should_reason_or_generate(state) == "generate"

    def test_reasons_when_denied_and_attempts_remain(self):
        state = _state(authorization_passed=False, max_attempts=3, retrieval_attempt=1)
        assert should_reason_or_generate(state) == "reason"

    def test_generates_when_denied_and_single_attempt(self):
        # Default max_attempts=1 skips reasoning entirely for efficiency.
        state = _state(authorization_passed=False, max_attempts=1, retrieval_attempt=1)
        assert should_reason_or_generate(state) == "generate"

    def test_generates_when_denied_and_attempts_exhausted(self):
        state = _state(authorization_passed=False, max_attempts=2, retrieval_attempt=2)
        assert should_reason_or_generate(state) == "generate"
