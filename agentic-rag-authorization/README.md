# Agentic RAG with Fine-Grained Authorization


This repository demonstrates how to combine agentic behavior with deterministic fine-grained authorization using LangGraph, SpiceDB, and Weaviate. You'll learn to build RAG systems where a user can view information only based on the documents they have access to.

This project uses the [LangChain SpiceDB](https://pypi.org/project/langchain-spicedb/) library

![screengrab](agentic-rag.gif)

## Documentation Navigation

- **[README.md](README.md)** (you are here) - Overview, quick start, core concepts
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Deep dive into system design, security model, and trade-offs
- **[data/PERMISSIONS.md](data/PERMISSIONS.md)** - Permission matrix and authorization patterns

## What You'll Learn

This repo demonstrates:

1. **Fine-grained authorization in RAG** - How to enforce document-level permissions with SpiceDB to ensure the user only information based on what they have access to
2. **Security architecture** - Deterministic authorization boundary that cannot be bypassed
3. **Production features** - Structured logging, connection pooling, batch operations, error handling
4. **Real-world complexity** - 50 documents, 4 permission patterns with hierarchies.

Note: Despite the "agentic RAG" name, the default mode is intentionally simple and deterministic (3 nodes: retrieve → authorize → generate). This provides fast, predictable behavior suitable for most use cases.

## The Problem This Solves

Traditional RAG retrieves documents by semantic similarity without considering permissions. This creates two issues:

1. **Security risk**: Users might see documents they shouldn't access
2. **Poor UX**: Silent failures when documents are denied, with no explanation

Read the [OWASP Top 10 for LLM](https://owasp.org/www-project-top-10-for-large-language-model-applications/) and [OWASP Top 10 Risks to Web Apps](https://owasp.org/Top10/2025/A01_2025-Broken_Access_Control/) for more information on why access control matters.

## The Solution

This implementation shows how to combine:
- **Retrieval-first approach**: Direct semantic/keyword search without upfront planning overhead
- **Deterministic security**: SpiceDB authorization that cannot be bypassed
- **Transparency**: Users understand what they can/can't access and why

```
Traditional RAG:  Query → Retrieve → Generate
                           ↓
                    (no permission checks)

This approach (default):  Query → Retrieve → [SpiceDB Authorizes] → Generate
                                               ↓
                                       Security boundary
```

## Quick Example

```bash
# Alice (engineering department) queries engineering docs
Query: "What are our system architecture best practices?"
User: alice

Result:
✅ Retrieved: 3 documents via semantic search
✅ Authorized: 2 documents (eng-001, eng-002)
❌ Denied: 1 document (hr-001)

Answer: "Based on the engineering documents, our system uses microservices
architecture with event-driven patterns..."
```

```bash
# Bob (sales department) queries engineering docs
Query: "What are our system architecture best practices?"
User: bob

Result:
✅ Retrieved: 3 documents
❌ Authorized: 0 documents
❌ Denied: 3 documents

Answer: "I don't have access to the engineering documents needed to answer
this question. This information is restricted to the engineering department."
```

The agent transparently explains access limitations instead of failing silently.

## Setup (5 minutes)

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- OpenAI API key

### Steps

```bash
# 1. Start services
docker-compose up -d

# 2. Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env with your actual OpenAI API key (never commit .env!)

# 4. Initialize data
python3 examples/setup_environment.py

# 5. Run demo
python3 examples/basic_example.py
```


## Web UI

A web interface is available to demonstrate the authorization capabilities interactively.

### Quick Start

```bash
# 1. Ensure services are running and data is initialized
docker-compose up -d
python3 examples/setup_environment.py  # If not already done

# 2. Install web dependencies
pip install -r requirements.txt  # Includes fastapi and uvicorn

# 3. Launch UI (includes pre-flight checks)
python3 run_ui.py
```

The launcher will:
- ✅ Check that Weaviate, SpiceDB, and OpenAI are configured
- ✅ Verify documents are loaded
- 🚀 Start the FastAPI server
- 🌐 Open your browser to http://localhost:8000

### Manual Start

```bash
# Terminal 1: Start services (if not running)
docker-compose up -d

# Terminal 2: Start API server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Browser
open http://localhost:8000
```

## How It Works

### 1. Authorization Model (SpiceDB)

```zed
definition user {}

definition department {
    relation member: user
}

definition document {
    relation viewer: user | department#member
    permission view = viewer
}
```

**Relationships:**
- `alice` is a member of `engineering` department
- `eng-001` document has viewer = `engineering#member`
- Result: alice can view eng-001 ✅

### 2. State Flow

**Default Mode**
```
User Query
    ↓
Retrieval Node ← Weaviate BM25 keyword search
    ↓
Authorization Node ← SpiceDB filters (SECURITY BOUNDARY - cannot be bypassed)
    ↓
Generation Node ← Answer with authorized context + explanations
```

### 3. Security Guarantees

- **Authorization always runs**: Hardcoded in LangGraph workflow, agent cannot skip
- **Deterministic checks**: SpiceDB enforces permissions (no LLM involved)
- **Fail closed**: Access denied unless explicitly granted
- **Observable**: Full audit trail in state

## Project Structure

```
agentic-rag-weaviate/
├── agentic_rag/
│   ├── graph.py               # LangGraph state machine
│   ├── state.py               # State schema
│   ├── config.py              # Configuration management
│   ├── nodes/
│   │   ├── retrieval_node.py  # Weaviate BM25 search
│   │   ├── authorization_node.py  # SpiceDB filtering (security boundary)
│   │   ├── reasoning_node.py  # Optional: adaptive retry logic
│   │   └── generation_node.py # Final answer with context
│   ├── authorization_helpers.py  # Batch permission checking
│   ├── weaviate_client.py     # Connection pooling for Weaviate
│   ├── grpc_helpers.py        # Connection pooling for SpiceDB
│   ├── logging_config.py      # Structured JSON logging
│   └── validation.py          # Input validation and sanitization
├── examples/
│   ├── setup_environment.py   # Initialize data (loads 50 documents)
│   └── basic_example.py       # 8 demo scenarios
├── scripts/
│   ├── generate_documents.py  # Generate 50 .txt files
│   ├── parse_documents.py     # Parse documents into objects
│   └── verify_permissions.py  # Test authorization patterns
├── data/
│   ├── documents/             # 50 .txt files (5 departments)
│   ├── schema.zed             # SpiceDB permission schema
│   └── PERMISSIONS.md         # Permission matrix
└── docker-compose.yml         # Weaviate + SpiceDB
```

## Configuration

Environment variables (`.env`):

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional (defaults shown)
WEAVIATE_URL=http://localhost:8080
SPICEDB_ENDPOINT=localhost:50051
SPICEDB_TOKEN=devtoken
MAX_RETRIEVAL_ATTEMPTS=3
```

## Dataset Overview

The repository includes a realistic 50-document dataset across 5 departments.

**Authorization Patterns:**
1. Department-based access (primary pattern)
2. Cross-department collaboration (3 shared documents)
3. Individual user exceptions (3 special grants)
4. Public documents (accessible to all users)

See [data/PERMISSIONS.md](data/PERMISSIONS.md) for the complete permission matrix.

## Sample Scenarios

The `examples/basic_example.py` demonstrates 8 scenarios:

1. **Department Access** - alice queries engineering documents
2. **Access Denial** - bob attempts to access engineering documents
3. **Cross-Department** - bob accesses shared architecture document
4. **Individual Exception** - alice accesses sales proposal (special grant)
5. **Public Access** - Anyone can access company handbooks
6. **Finance Department** - finance_manager queries financial reports
7. **HR Department** - hr_manager queries HR policies
8. **Transparent Explanations** - Agent explains why access was denied

## Contributing & Extending

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Adding documents and permissions
- Customizing agent behavior
- Extending the system

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_basic_flow.py::test_authorized_access
```

## Learn More

- **SpiceDB**: https://authzed.com/docs
- **Weaviate**: https://weaviate.io/developers/weaviate
- **LangGraph**: https://langchain-ai.github.io/langgraph/

## License

MIT
