#!/usr/bin/env python3
"""Launch script for the Agentic RAG UI."""

import subprocess
import sys
import time
import webbrowser
import os


def check_services():
    """Pre-flight check for required services."""
    print("🔍 Checking services...")

    # Check if .env exists
    if not os.path.exists(".env"):
        print("  ⚠️  .env file not found")
        print("     Copy .env.example to .env and configure it")
        return False

    # Check Milvus
    try:
        from agentic_rag.config import get_config
        from agentic_rag.milvus_client import get_milvus_client

        config = get_config()
        milvus_client = get_milvus_client(config.milvus_uri, config.milvus_token)
        print("  ✅ Milvus connected")
    except Exception as e:
        print(f"  ❌ Milvus not available: {e}")
        print("     Run: docker-compose up -d")
        return False

    # Check SpiceDB
    try:
        from agentic_rag.grpc_helpers import get_spicedb_client

        spicedb_client = get_spicedb_client(config.spicedb_endpoint, config.spicedb_token)
        print("  ✅ SpiceDB connected")
    except Exception as e:
        print(f"  ❌ SpiceDB not available: {e}")
        print("     Run: docker-compose up -d")
        return False

    # Check OpenAI key
    if not config.openai_api_key or config.openai_api_key == "your-openai-api-key-here":
        print("  ❌ OPENAI_API_KEY not configured")
        print("     Set it in .env file")
        return False
    print("  ✅ OpenAI API key configured")

    # Check if documents are loaded
    try:
        if milvus_client.has_collection("Documents"):
            results = milvus_client.query(
                collection_name="Documents",
                filter='doc_id != ""',
                output_fields=["doc_id"],
                limit=1,
            )
            if results:
                print("  ✅ Documents loaded in Milvus")
            else:
                print("  ⚠️  No documents found in Milvus")
                print("     Run: python examples/setup_environment.py")
                return False
        else:
            print("  ⚠️  Documents collection does not exist in Milvus")
            print("     Run: python examples/setup_environment.py")
            return False
    except Exception as e:
        print(f"  ⚠️  Could not verify documents: {e}")

    return True


def main():
    """Launch the UI."""
    print("🚀 Agentic RAG UI Launcher")
    print("=" * 50)

    if not check_services():
        print("\n❌ Pre-flight checks failed. Please fix the issues above.")
        sys.exit(1)

    print("\n✅ All services ready!")
    print("\n🌐 Starting FastAPI server...")
    print("   URL: http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs")
    print("   Press Ctrl+C to stop\n")

    # Open browser after 2 seconds
    def open_browser():
        time.sleep(2)
        print("🌐 Opening browser...")
        webbrowser.open("http://localhost:8000")

    import threading

    threading.Thread(target=open_browser, daemon=True).start()

    # Start uvicorn
    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "api.main:app",
                "--host",
                "0.0.0.0",
                "--port",
                "8000",
                "--reload",
            ]
        )
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        sys.exit(0)


if __name__ == "__main__":
    main()
