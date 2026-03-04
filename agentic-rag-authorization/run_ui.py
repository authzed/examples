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

    # Check Weaviate
    try:
        from agentic_rag.config import get_config
        from agentic_rag.weaviate_client import get_weaviate_client

        config = get_config()
        weaviate_client = get_weaviate_client(config.weaviate_url)
        print("  ✅ Weaviate connected")
    except Exception as e:
        print(f"  ❌ Weaviate not available: {e}")
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
        result = weaviate_client.query.get("Documents", ["doc_id"]).with_limit(1).do()
        doc_count = len(result.get("data", {}).get("Get", {}).get("Documents", []))
        if doc_count > 0:
            print("  ✅ Documents loaded in Weaviate")
        else:
            print("  ⚠️  No documents found in Weaviate")
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
