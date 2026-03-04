"""Reasoning node - agent reasons about authorization failures."""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage

from ..state import AgenticRAGState
from ..logging_config import get_logger
from ..node_helpers import get_llm, log_node_execution

logger = get_logger("nodes.reasoning")

REASONING_PROMPT = """You are an intelligent reasoning agent. The user's query could not be fully answered because some documents were denied due to permissions.

Current situation:
- Query: {query}
- User: {subject_id}
- Retrieved documents: {retrieved_count}
- Authorized documents: {authorized_count}
- Denied: {denied_count}
- Attempt: {attempt}/{max_attempts}

Previous reasoning: {reasoning}

Options:
1. If there are authorized documents, proceed with generating an answer from them
2. If no authorized documents and attempts remain, try a different search strategy
3. If no authorized documents and no attempts remain, explain why access was denied

What should we do next? Be specific and actionable."""


def reasoning_node(state: AgenticRAGState) -> dict:
    """Agent reasons about authorization results and decides next steps.

    This node allows the agent to adapt when authorization fails:
    - Try different search strategies
    - Explain authorization constraints
    - Make informed decisions about how to proceed
    """
    with log_node_execution(
        logger,
        "reasoning",
        {
            "subject_id": state["subject_id"],
            "authorized_count": len(state["authorized_documents"]),
            "denied_count": state["denied_count"],
            "attempt": state["retrieval_attempt"],
        }
    ):
        llm = get_llm()

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", REASONING_PROMPT),
            ]
        )

        chain = prompt | llm

        result = chain.invoke(
            {
                "query": state["query"],
                "subject_id": state["subject_id"],
                "retrieved_count": len(state["retrieved_documents"]),
                "authorized_count": len(state["authorized_documents"]),
                "denied_count": state["denied_count"],
                "attempt": state["retrieval_attempt"],
                "max_attempts": state["max_attempts"],
                "reasoning": "\n".join(state.get("reasoning", [])),
            }
        )

        reasoning = state.get("reasoning", [])
        reasoning.append(result.content)

        logger.info(
            "Reasoning decision",
            extra={
                "decision_length": len(result.content),
            },
        )

        return {
            "reasoning": reasoning,
            "messages": [AIMessage(content=f"Reasoning: {result.content}")],
        }
