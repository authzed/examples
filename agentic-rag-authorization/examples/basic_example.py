"""Basic example showing agentic RAG with authorization."""

import sys
import os

# Add parent directory to path so we can import from agentic_rag
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from agentic_rag.graph import run_agentic_rag_async
from agentic_rag.config import get_config


async def run_query(query: str, subject_id: str):
    """Run a single query through the agentic RAG system."""
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"User: {subject_id}")
    print('='*60)

    # Use the simplified helper function
    result = await run_agentic_rag_async(
        query=query,
        subject_id=subject_id,
        max_attempts=1
    )

    print(f"\n📊 Results:")
    print(f"  - Retrieved: {len(result['retrieved_documents'])} documents")
    print(f"  - Authorized: {len(result['authorized_documents'])} documents")
    print(f"  - Denied: {result['denied_count']} documents")
    print(f"  - Attempts: {result['retrieval_attempt']}")

    if result['authorized_documents']:
        print(f"\n📄 Authorized Documents:")
        for doc in result['authorized_documents']:
            print(f"  - {doc.metadata['doc_id']}: {doc.metadata['title']}")

    print(f"\n💭 Agent Reasoning:")
    for i, reasoning in enumerate(result['reasoning'], 1):
        print(f"  {i}. {reasoning[:100]}...")

    print(f"\n✨ Answer:")
    print(f"{result['answer']}")
    print()

    return result


async def main():
    """Run basic examples."""
    config = get_config()

    if not config.openai_api_key:
        print("❌ Error: OPENAI_API_KEY not set")
        print("Please set it in your .env file or environment")
        return

    print("\n" + "="*60)
    print("Agentic RAG with Authorization - Basic Examples")
    print("="*60)

    # Example 1: Alice (engineering) queries engineering documents
    print("\n🔵 SCENARIO 1: Department Access - Engineering")
    await run_query(
        "What are our microservices architecture patterns?",
        "alice"
    )

    # Example 2: Bob (sales) queries sales documents
    print("\n🔵 SCENARIO 2: Department Access - Sales")
    await run_query(
        "What sales proposals do we have?",
        "bob"
    )

    # Example 3: Cross-department document access
    print("\n🔵 SCENARIO 3: Cross-Department Access")
    await run_query(
        "What architecture documentation is available for sales?",
        "bob"
    )

    # Example 4: Individual exception - Alice accessing sales doc
    print("\n🔵 SCENARIO 4: Individual Exception")
    await run_query(
        "Show me sales proposals",
        "alice"
    )

    # Example 5: Public document access
    print("\n🔵 SCENARIO 5: Public Document Access")
    await run_query(
        "What are the company handbook guidelines?",
        "bob"
    )

    # Example 6: Finance manager queries
    print("\n🔵 SCENARIO 6: Finance Department Access")
    await run_query(
        "What are the quarterly financial reports?",
        "finance_manager"
    )

    # Example 7: Access denial - Alice queries sales (except individual exception)
    print("\n🔵 SCENARIO 7: Access Denial")
    await run_query(
        "What are all the sales playbooks?",
        "alice"
    )

    # Example 8: HR manager queries
    print("\n🔵 SCENARIO 8: HR Department Access")
    await run_query(
        "What HR policies do we have?",
        "hr_manager"
    )


if __name__ == "__main__":
    asyncio.run(main())
