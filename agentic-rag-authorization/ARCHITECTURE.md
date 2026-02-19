# Architecture Deep Dive

Technical details for those implementing similar systems or extending this one.

## System Design

### Core Components

```
┌─────────────────────────────────────────────────────────┐
│            Agentic RAG System Architecture              │
│                                                         │
│  ┌──────────────┐              ┌──────────────┐        │
│  │   CLI Tool   │              │   Web UI     │        │
│  │  (Python)    │              │  (Browser)   │        │
│  └──────┬───────┘              └──────┬───────┘        │
│         │                             │                │
│         │ run_agentic_rag()           │ HTTP API       │
│         │ (sync)                      │ (async)        │
│         │                             │                │
│         └─────────────┬───────────────┘                │
│                       ▼                                │
│            ┌────────────────────────┐                  │
│            │   FastAPI Backend      │                  │
│            │  - POST /api/query     │                  │
│            │  - GET /api/users      │                  │
│            │  - GET /api/health     │                  │
│            │  - Pydantic validation │                  │
│            └──────────┬─────────────┘                  │
│                       ▼                                │
│            ┌────────────────────────┐                  │
│            │  LangGraph Engine      │                  │
│            │  (State Machine)       │                  │
│            └──────────┬─────────────┘                  │
│                       │                                │
│            ┌──────────┼──────────┐                     │
│            ▼          ▼          ▼                     │
│        Weaviate    SpiceDB    OpenAI                   │
│        (Search)    (AuthZ)    (LLM)                    │
└─────────────────────────────────────────────────────────┘
```

## System Interfaces

This system provides two interfaces for interacting with the agentic RAG pipeline:

### 1. Command-Line Interface (CLI)

**Purpose:** Direct programmatic access, scripting, testing, and development.

**Entry Point:** `agentic_rag.graph.run_agentic_rag()`

**Usage:**
```python
from agentic_rag.graph import run_agentic_rag

result = run_agentic_rag(
    query="What are our engineering practices?",
    subject_id="alice",
    max_attempts=1
)
```

**Characteristics:**
- Synchronous execution
- Returns full state dictionary
- Direct access to all state fields (messages, reasoning, documents, etc.)
- Used in tests and examples
- Ideal for automation and scripting

**Return Value:**
```python
{
    "query": str,
    "subject_id": str,
    "answer": str,
    "authorized_documents": List[Document],
    "retrieved_documents": List[Document],
    "denied_count": int,
    "messages": List[BaseMessage],
    "reasoning": List[str],
    "retrieval_attempt": int,
    "authorization_passed": bool,
}
```

### 2. Web Interface

**Purpose:** User-friendly demonstration and interactive exploration of authorization behavior.

**Architecture:**
- **Frontend:** Single-page HTML/CSS/JS application (`ui/index.html`, 544 lines)
- **Backend:** FastAPI REST API (`api/` directory)
- **Launcher:** Python script with pre-flight checks (`run_ui.py`)

**API Endpoints:**
- `POST /api/query` - Execute RAG query with authorization
- `GET /api/users` - List available demo users
- `GET /api/health` - Check backend service health

**Entry Point:** `api.main.app` (FastAPI application)

**Launch Methods:**

*Automated (recommended):*
```bash
python3 run_ui.py
```
This launcher performs pre-flight checks:
- Verifies Weaviate connectivity
- Verifies SpiceDB connectivity
- Checks OpenAI API key configuration
- Validates documents are loaded
- Auto-opens browser to http://localhost:8000

*Manual:*
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Request/Response Flow:**
```
1. User selects identity (alice, bob, hr_manager, etc.) in browser
2. User enters query in textarea
3. Frontend JavaScript sends POST to /api/query:
   {
     "query": "What are our practices?",
     "subject_id": "alice",
     "max_attempts": 1
   }
4. FastAPI validates request (Pydantic models)
5. Backend calls run_agentic_rag_async()
6. LangGraph executes state machine (retrieve → authorize → generate)
7. API formats response:
   - Authorized documents (doc_id, title, content preview)
   - Denied documents (doc_id, title, reason)
   - Query statistics (counts, execution time)
8. Frontend renders results with visual indicators:
   - Green cards for authorized documents
   - Red cards for denied documents with explanations
   - Statistics panel showing retrieval/authorization metrics
```

**Key Difference:** The web interface uses `run_agentic_rag_async()` for non-blocking execution, while the CLI uses the synchronous `run_agentic_rag()`. Both execute the same LangGraph state machine but differ in their execution model to suit their respective environments.

### Interface Comparison

| Feature | CLI | Web UI |
|---------|-----|--------|
| Execution | Synchronous | Asynchronous |
| Entry Point | `run_agentic_rag()` | `run_agentic_rag_async()` |
| Use Case | Scripting, testing, automation | Interactive demos, exploration |
| Output Format | Python dict | JSON (HTTP response) |
| User Experience | Code-based | Visual, browser-based |
| Pre-flight Checks | Manual | Automated (via run_ui.py) |
| Observability | Full state access | Formatted summaries + stats |

## API Layer Architecture

The web interface is built on a FastAPI backend that wraps the core LangGraph engine with HTTP endpoints, validation, and response formatting.

### Components

**1. FastAPI Application (`api/main.py`)**

Entry point for the web API with:
- CORS middleware for cross-origin requests (localhost only)
- Static file serving for the UI (mounts `ui/` directory)
- Route registration (via `api/routes.py`)
- Root endpoint serving `index.html`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Agentic RAG Authorization API",
    version="1.0.0",
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes under /api prefix
app.include_router(router, prefix="/api")
```

**2. Route Handlers (`api/routes.py`)**

Implements three core endpoints:

*POST /api/query:*
```python
@router.post("/query")
async def execute_query(request: QueryRequest) -> APIResponse:
    # 1. Validate request (Pydantic)
    # 2. Start execution timer
    # 3. Call run_agentic_rag_async()
    # 4. Format authorized documents
    # 5. Extract denied documents (retrieved but not authorized)
    # 6. Calculate statistics
    # 7. Return APIResponse with data or error
```

*GET /api/users:*
```python
@router.get("/users")
async def get_users():
    # Returns list of demo users:
    # - alice (Engineering)
    # - bob (Sales)
    # - hr_manager (HR)
    # - finance_manager (Finance)
```

*GET /api/health:*
```python
@router.get("/health")
async def health_check():
    # Returns service status
    # TODO: Actually check Weaviate/SpiceDB connectivity
```

**3. Pydantic Models (`api/models.py`)**

Type-safe request/response contracts:

```python
class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    subject_id: str
    max_attempts: int = Field(default=1, ge=1, le=5)

class DocumentSummary(BaseModel):
    doc_id: str
    title: str
    content_preview: str  # First 200 chars

class DeniedDocumentSummary(BaseModel):
    doc_id: str
    title: str
    reason: str  # "User 'bob' does not have permission..."

class QueryStats(BaseModel):
    retrieved_count: int
    authorized_count: int
    denied_count: int
    retrieval_attempts: int
    execution_time_ms: int

class QueryResponseData(BaseModel):
    query: str
    subject_id: str
    answer: str
    authorized_documents: List[DocumentSummary]
    denied_documents: List[DeniedDocumentSummary]
    stats: QueryStats

class APIResponse(BaseModel):
    success: bool
    data: Optional[QueryResponseData] = None
    error: Optional[dict] = None
```

**4. Configuration (`api/config.py`)**

API-level configuration (separate from core `agentic_rag.config`):

```python
class APIConfig(BaseModel):
    cors_origins: List[str] = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    api_prefix: str = "/api"
```

### Request Processing Flow

Detailed flow through the API layer:

```
Browser
  │
  ▼ HTTP POST /api/query
  │ Content-Type: application/json
  │ Body: {
  │   "query": "What are our engineering practices?",
  │   "subject_id": "alice",
  │   "max_attempts": 1
  │ }
  │
FastAPI Router (routes.py)
  │
  ▼ Pydantic validation
  │ - query: 1-1000 chars ✓
  │ - subject_id: present ✓
  │ - max_attempts: 1-5 ✓
  │
  ▼ Start timer (time.time())
  │
run_agentic_rag_async()
  │
  ▼ Execute LangGraph
  │ 1. Retrieval Node → Weaviate BM25 search
  │ 2. Authorization Node → SpiceDB permission checks
  │ 3. Generation Node → LLM answer generation
  │
  ▼ Returns state dict:
  │ {
  │   "query": "...",
  │   "subject_id": "alice",
  │   "answer": "Based on...",
  │   "retrieved_documents": [doc1, doc2, doc3],
  │   "authorized_documents": [doc1, doc2],
  │   "denied_count": 1,
  │   "retrieval_attempt": 1,
  │   ...
  │ }
  │
Route Handler Processing
  │
  ▼ Calculate execution time
  │ execution_time_ms = int((time.time() - start_time) * 1000)
  │
  ▼ Format authorized documents
  │ For each in authorized_documents:
  │   DocumentSummary(
  │     doc_id=doc.metadata["doc_id"],
  │     title=doc.metadata["title"],
  │     content_preview=doc.page_content[:200]
  │   )
  │
  ▼ Extract denied documents
  │ Compare retrieved_documents vs authorized_documents by doc_id
  │ For each denied:
  │   DeniedDocumentSummary(
  │     doc_id=...,
  │     title=...,
  │     reason="User 'alice' does not have permission..."
  │   )
  │
  ▼ Build statistics
  │ QueryStats(
  │   retrieved_count=3,
  │   authorized_count=2,
  │   denied_count=1,
  │   retrieval_attempts=1,
  │   execution_time_ms=3420
  │ )
  │
  ▼ Wrap in APIResponse
  │ APIResponse(
  │   success=True,
  │   data=QueryResponseData(...)
  │ )
  │
  ▼ JSON serialization (FastAPI automatic)
  │
Browser
  │
  ▼ Frontend JavaScript receives JSON
  │
  ▼ Render answer
  │ Display in answer card
  │
  ▼ Render authorized documents
  │ Green cards with doc_id, title, preview
  │
  ▼ Render denied documents
  │ Red cards with doc_id, title, reason
  │
  ▼ Display statistics
  │ "Retrieved: 3 | Authorized: 2 | Denied: 1"
  │ "Execution time: 3.42s"
```

### Frontend Architecture

**Single-Page Application (`ui/index.html`)**

The frontend is a self-contained HTML file (544 lines) with embedded CSS and JavaScript:

**Structure:**
- Header with title and description
- User selection dropdown (populated via GET /api/users)
- Query textarea input
- Submit button with loading state
- Results section (hidden until query executes)
  - Answer card
  - Authorized documents section (green styling)
  - Denied documents section (red styling)
  - Statistics panel

**Key JavaScript Functions:**
```javascript
// Load available users on page load
async function loadUsers() {
    const response = await fetch('/api/users');
    // Populate dropdown
}

// Execute query
async function executeQuery() {
    const response = await fetch('/api/query', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            query: queryText,
            subject_id: selectedUserId,
            max_attempts: 1
        })
    });
    const data = await response.json();
    displayResults(data);
}

// Render results with authorization transparency
function displayResults(data) {
    // Show answer
    // Render authorized docs (green cards)
    // Render denied docs (red cards with reasons)
    // Display statistics
}
```

**Design Philosophy:**
- Zero build tools (vanilla HTML/CSS/JS)
- Responsive design (works on mobile)
- Clear visual distinction between authorized and denied content
- Transparency: always show what was denied and why

### Security Considerations

**Current State (Demo-Focused):**

The API layer is designed for **demonstration and education**, not production use. Current security characteristics:

1. **No API Authentication**
   - Endpoints are publicly accessible
   - No JWT, API keys, or session management
   - Anyone can query as any user

2. **Client-Side User Selection**
   - User identity selected in browser dropdown
   - No server-side identity verification
   - Trivial to impersonate any user

3. **CORS Limited to Localhost**
   ```python
   allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"]
   ```
   - Restricts browser-based access to local development
   - Does not protect against direct HTTP requests

4. **No Rate Limiting**
   - No protection against abuse or DoS
   - OpenAI API costs could accumulate

**Why This Is Acceptable for Demo:**
- System demonstrates authorization concepts (SpiceDB)
- Not intended for production deployment
- Educational value outweighs security limitations
- Clear documentation of what NOT to do in production

**Production Recommendations:**

To deploy this system in production, implement:

1. **API Authentication**
   ```python
   from fastapi import Depends, HTTPException
   from fastapi.security import HTTPBearer

   security = HTTPBearer()

   @router.post("/query")
   async def execute_query(
       request: QueryRequest,
       credentials: HTTPAuthorizationCredentials = Depends(security)
   ):
       # Validate JWT or API key
       user = validate_token(credentials.credentials)

       # Use authenticated user identity
       result = await run_agentic_rag_async(
           query=request.query,
           subject_id=user.id,  # From token, not client
           max_attempts=request.max_attempts
       )
   ```

2. **Server-Side Identity Verification**
   - Extract user identity from authenticated session
   - Never trust client-provided subject_id
   - Validate user exists in authorization system

3. **Rate Limiting**
   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address

   limiter = Limiter(key_func=get_remote_address)

   @router.post("/query")
   @limiter.limit("10/minute")
   async def execute_query(...):
       # Process request
   ```

4. **Request Logging and Audit Trails**
   ```python
   import structlog

   logger = structlog.get_logger()

   @router.post("/query")
   async def execute_query(request: QueryRequest):
       logger.info(
           "query_request",
           subject_id=request.subject_id,
           query=request.query,
           timestamp=datetime.utcnow(),
       )
       # Execute query
   ```

5. **HTTPS in Production**
   - Terminate TLS at load balancer or reverse proxy
   - Never send credentials over HTTP

6. **Input Sanitization**
   - Already done: Pydantic validates query length (1-1000 chars)
   - Consider additional sanitization for prompt injection

7. **CORS Restrictions**
   ```python
   allow_origins=[
       "https://your-production-domain.com",
       "https://app.your-domain.com",
   ]
   ```

**Security Boundary Remains Intact:**

Importantly, API-level security issues do NOT compromise the core authorization model:
- SpiceDB still enforces document-level permissions
- Authorization node still cannot be bypassed
- Even if an attacker queries as any user, they only see documents that user can access
- The demonstration successfully shows how authorization works, even without API auth

### Async Execution Model

**Why Async for Web Interface:**

The web interface uses `run_agentic_rag_async()` instead of the synchronous `run_agentic_rag()`:

**Synchronous (CLI):**
```python
def run_agentic_rag(query: str, subject_id: str, max_attempts: int) -> dict:
    # Blocks until complete
    result = graph.invoke(initial_state)
    return result
```

**Asynchronous (Web API):**
```python
async def run_agentic_rag_async(query: str, subject_id: str, max_attempts: int) -> dict:
    # Non-blocking, allows concurrent requests
    result = await graph.ainvoke(initial_state)
    return result
```

**Benefits of Async:**

1. **Concurrency**
   - Server can handle multiple queries simultaneously
   - Other requests aren't blocked while one query waits for OpenAI

2. **Resource Efficiency**
   - Async I/O doesn't waste threads on waiting
   - Better scalability under load

3. **FastAPI Integration**
   - FastAPI is async-first framework
   - Async route handlers are more efficient

4. **Consistent Performance**
   - Queries don't queue behind each other
   - Response time remains consistent under load

**Implementation:**

Both execution paths use the same LangGraph state machine, just different invocation methods:

```python
# graph.py
from langgraph.graph import StateGraph

workflow = StateGraph(AgenticRAGState)
# ... add nodes, edges ...
graph = workflow.compile()

# Synchronous wrapper (CLI)
def run_agentic_rag(query, subject_id, max_attempts):
    return graph.invoke({
        "query": query,
        "subject_id": subject_id,
        "max_attempts": max_attempts,
        # ... other initial state
    })

# Asynchronous wrapper (Web API)
async def run_agentic_rag_async(query, subject_id, max_attempts):
    return await graph.ainvoke({
        "query": query,
        "subject_id": subject_id,
        "max_attempts": max_attempts,
        # ... other initial state
    })
```

**Node Compatibility:**

All nodes work with both sync and async execution:
- LangChain components support async (Weaviate client, OpenAI)
- SpiceDB gRPC client is synchronous but fast (~40-50ms)
- No code duplication required

### LangGraph State Machine

**Default Flow (max_attempts=1):**
```
START
  ↓
Retrieval Node (Weaviate BM25)
  ↓
Authorization Node (SpiceDB) ◄── Security Boundary (deterministic)
  ↓
Generation Node (LLM with context + explanations)
  ↓
END
```

### State Schema

```python
AgenticRAGState = TypedDict("AgenticRAGState", {
    # Input
    "query": str,
    "subject_id": str,
    "max_attempts": int,

    # Tracking
    "messages": List[BaseMessage],
    "reasoning": List[str],
    "retrieval_attempt": int,

    # Documents
    "retrieved_documents": List[Document],
    "authorized_documents": List[Document],
    "denied_count": int,

    # Results
    "authorization_passed": bool,
    "answer": str,
})
```

## Node Responsibilities

### Retrieval Node (Deterministic)

**Purpose**: Execute semantic/keyword search in Weaviate.

**Input**: `query` from state

**Operation**:
- Weaviate BM25 keyword search (default)
- Returns top-k documents (typically 5)
- No authorization filtering at this stage
- Direct execution without planning overhead

**Output**: Updates `retrieved_documents`, `retrieval_attempt`

Note: This node runs immediately on query input. There is no planning phase before retrieval.

### Authorization Node (Deterministic - Security Boundary)

**Purpose**: Filter documents by permissions using SpiceDB.

**Critical property**: This node ALWAYS runs and cannot be bypassed by the agent.

**Operation**:
```python
authorized = []
denied_count = 0

for doc in retrieved_documents:
    response = spicedb_client.CheckPermission(
        resource=f"document:{doc.id}",
        permission="view",
        subject=f"user:{subject_id}"
    )

    if response.permissionship == HAS_PERMISSION:
        authorized.append(doc)
    else:
        denied_count += 1

return {
    "authorized_documents": authorized,
    "denied_count": denied_count,
    "authorization_passed": len(authorized) > 0
}
```

**Output**: Updates `authorized_documents`, `denied_count`, `authorization_passed`

### Generation Node (LLM-based)

**Purpose**: Generate final answer incorporating authorization context.

**Input**: `query`, `authorized_documents`, `denied_count`, `reasoning`

**Behavior:**
- Uses authorized documents as context for answer
- Mentions if documents were denied (transparency)
- Explains access limitations when applicable
- Provides helpful answer within authorization constraints
- Always runs (even if no authorized documents)

**Output**: Updates `answer`

Note: This is the only node that always uses the LLM in default mode (max_attempts=1). It handles both successful retrievals and authorization failures with appropriate explanations.

## Authorization Model (SpiceDB)

### Schema Definition

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

### Permission Check Flow

```
1. User makes query
   subject_id: "alice"

2. Weaviate retrieves documents
   [eng-001, eng-002, hr-001]

3. For each document, SpiceDB checks:

   eng-001:
   └─ viewer = engineering#member
      └─ alice is engineering#member?
         └─ alice → engineering → member ✅
         Result: ALLOWED

   hr-001:
   └─ viewer = hr_manager
      └─ alice is hr_manager?
         └─ alice ≠ hr_manager ❌
         Result: DENIED
```

### Relationship Graph Example

```
alice (user) ──member──> engineering (department)

eng-001 (document) ──viewer──> engineering#member
                               (allows all engineering members)

hr-001 (document) ──viewer──> hr_manager (user)
                              (allows only hr_manager)
```

## Security Architecture

### Trust Boundaries

**With Web Interface:**

```
┌───────────────────────────────────┐
│       Untrusted Zone              │
│  Browser, User Input              │
│  - User selects identity          │
│  - User enters query              │
└─────────────┬─────────────────────┘
              ▼
┌───────────────────────────────────┐
│   API Layer (Demo: No Auth)       │
│  FastAPI Backend                  │
│  - Request validation             │
│  - CORS protection                │
│  - Response formatting            │
│  ⚠️  Production needs auth here   │
└─────────────┬─────────────────────┘
              ▼
┌───────────────────────────────────┐
│   Semi-Trusted Zone               │
│  LangGraph Agent                  │
│  - Can plan strategies            │
│  - Can check permissions          │
│  - Cannot bypass auth             │
└─────────────┬─────────────────────┘
              ▼
┌───────────────────────────────────┐
│   SECURITY BOUNDARY               │
│  Authorization Node               │
│  - Deterministic                  │
│  - Always runs                    │
│  - No LLM involvement             │
│  - SpiceDB permission checks      │
└─────────────┬─────────────────────┘
              ▼
┌───────────────────────────────────┐
│    Trusted Zone                   │
│  SpiceDB + Weaviate               │
│  Authorized data                  │
└───────────────────────────────────┘
```

**CLI Interface (Direct Access):**

```
┌───────────────────────────┐
│    Untrusted Zone         │
│  User Input, Query        │
└──────────┬────────────────┘
           ▼
┌───────────────────────────┐
│   Semi-Trusted Zone       │
│  Agent (LLM) + Tools      │
│  - Can plan strategies    │
│  - Can check permissions  │
│  - Cannot bypass auth     │
└──────────┬────────────────┘
           ▼
┌───────────────────────────┐
│   SECURITY BOUNDARY       │
│  Authorization Node       │
│  - Deterministic          │
│  - Always runs            │
│  - No LLM involvement     │
└──────────┬────────────────┘
           ▼
┌───────────────────────────┐
│    Trusted Zone           │
│  SpiceDB + Weaviate       │
│  Authorized data          │
└───────────────────────────┘
```

### Security Guarantees

1. **Authorization cannot be bypassed**
   ```python
   # Hardcoded in graph.py
   workflow.add_edge("retrieve", "authorize")
   # Agent cannot skip this edge
   ```

2. **Deterministic permission checks**
   ```python
   # Not LLM-based, uses SpiceDB directly
   response = spicedb_client.CheckPermission(...)
   if response.permissionship == HAS_PERMISSION:
       allow()
   ```

3. **Agent observes, doesn't control**
   ```python
   # Authorization happens first
   authorize() → reason()
   # Agent sees results, but doesn't make decisions
   ```

4. **Fail closed by default**
   ```python
   # Explicit permission required
   if not explicitly_allowed:
       deny()
   ```

## Conditional Logic

### After Authorization: Generate or Reason?

```python
def should_reason_or_generate(state: AgenticRAGState) -> str:
    if state["authorization_passed"]:
        return "generate"  # Have docs, answer the query
    else:
        return "reason"    # No docs, agent decides what to do
```

### After Reasoning: Retry or Generate?

```python
def should_retry_or_generate(state: AgenticRAGState) -> str:
    if (state["retrieval_attempt"] < state["max_attempts"]
        and len(state["authorized_documents"]) == 0):
        return "plan"      # Try again with different strategy
    else:
        return "generate"  # Give best answer we can
```

## Design Decisions

### Why Post-Filter Authorization?

**Alternative 1: Pre-filter (embed permissions in metadata)**
```python
# Query with permission filter
query.where({"department": user_department})
```
Problems:
- Limits search space (worse semantic results)
- Stale permissions (metadata not always current)
- Doesn't work with computed permissions

**Alternative 2: Post-filter (this approach)**
```python
# 1. Search without constraints (best semantic results)
docs = search(query)

# 2. Filter by up-to-date permissions
authorized = [d for d in docs if check_permission(d)]
```
Benefits:
- Best semantic search results
- Always current permissions
- Works with complex authorization logic

### Why LangGraph State Machine?

**Alternative: Pure ReAct loop**
```python
while not done:
    action = agent.choose_action()
    result = execute(action)
```
Problems:
- Agent controls flow (can skip steps)
- Harder to enforce security boundary
- Less observable

**LangGraph approach:**
```python
# Explicit state machine
workflow.add_edge("retrieve", "authorize")  # Always runs
```
Benefits:
- Enforces authorization node
- Observable state transitions
- Easier to debug/audit

### Why Deterministic Authorization Node?

**Not this:**
```python
def authorize(state):
    # Ask LLM to decide
    decision = llm("Should user access this doc?")
    return decision  # ❌ Non-deterministic
```

**This:**
```python
def authorize(state):
    # Direct SpiceDB check
    response = spicedb.CheckPermission(...)
    return response.permissionship == HAS_PERMISSION  # ✅ Deterministic
```

**Reason:** Security decisions must be deterministic, auditable, and policy-based.

## Modes of Operation

### Default Mode (max_attempts=1)

```
Query
  ↓
Retrieve (BM25 search)
  ↓
Authorize (filter)
  ↓
Generate (with explanations)
  ↓
Answer
```

**Characteristics:**
- Simple, predictable (3 nodes)
- Fast (~3-4s total)
- No retry logic
- Transparent explanations of authorization
- Single LLM call (generation only)
- Deterministic retrieval strategy

### Adaptive Mode (max_attempts > 1)

```
Query
  ↓
Retrieve
  ↓
Authorize ← Security boundary
  ↓
[Reason if needed] ← LLM decides retry
  ↓
Generate or Retry
  ↓
Answer + Reasoning Trace
```

**Characteristics:**
- Can adapt to failures (4 nodes)
- Slower (~5-8s with retries)
- Retry logic when authorization fails
- Rich reasoning traces
- Multiple LLM calls (reasoning + generation)
- Can try different retrieval approaches

Note: Default mode is intentionally simple and deterministic, not highly agentic. Enable adaptive mode only when you need retry logic.

## Extension Points

### Adding New Nodes

```python
def custom_node(state: AgenticRAGState) -> dict:
    # Custom logic
    result = process(state["query"])
    return {"custom_field": result}

# Add to graph
workflow.add_node("custom", custom_node)
workflow.add_edge("authorize", "custom")
workflow.add_edge("custom", "reason")
```

### Adding New Tools

```python
from langchain.tools import BaseTool

class CustomTool(BaseTool):
    name = "custom_tool"
    description = "What this tool does"

    def _run(self, query: str) -> str:
        # Implementation
        return result

# Agent will have access in planning node
```

### Modifying Authorization Logic

```python
def authorization_node(state: AgenticRAGState):
    # Add custom checks
    if special_case(state["subject_id"]):
        return special_authorization(state)

    # Default SpiceDB logic
    return spicedb_authorization(state)
```

### Extending the Web Interface

**Adding New API Endpoints:**

```python
# In api/routes.py
from fastapi import APIRouter

@router.get("/documents")
async def list_documents():
    """List all documents with metadata."""
    # Query Weaviate for all documents
    # Return structured list
    return {"documents": [...]}

@router.get("/permissions/{subject_id}")
async def get_user_permissions(subject_id: str):
    """Get all documents accessible to a user."""
    # Query SpiceDB for user's accessible documents
    # Useful for authorization debugging
    return {"accessible_documents": [...]}
```

**Adding Frontend Features:**

The UI is a single HTML file with embedded CSS and JavaScript. To extend:

1. **Add UI Section** (HTML):
```html
<div class="card" id="document-browser">
    <h2>Document Browser</h2>
    <div id="document-list"></div>
</div>
```

2. **Add Styling** (CSS in `<style>` tag):
```css
#document-browser {
    margin-top: 20px;
}
.document-item {
    padding: 10px;
    border-bottom: 1px solid #e5e7eb;
}
```

3. **Add JavaScript Handler**:
```javascript
async function loadDocuments() {
    const response = await fetch('/api/documents');
    const data = await response.json();
    displayDocuments(data.documents);
}

function displayDocuments(documents) {
    const container = document.getElementById('document-list');
    // Render documents
}
```

**Custom Authentication:**

To add API authentication for production:

```python
# In api/main.py or new api/auth.py
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

security = HTTPBearer()

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Verify JWT token and return user claims."""
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# In api/routes.py
@router.post("/query")
async def execute_query(
    request: QueryRequest,
    user: dict = Depends(verify_token)
):
    # Use authenticated user identity
    result = await run_agentic_rag_async(
        query=request.query,
        subject_id=user["sub"],  # From JWT, not client
        max_attempts=request.max_attempts,
    )
    # ... format and return response
```

**Custom Response Formatters:**

To change how documents are presented in the API:

```python
# In api/routes.py or new api/formatters.py
def format_document_detailed(doc: Document) -> dict:
    """Custom document formatter with more metadata."""
    return {
        "doc_id": doc.metadata["doc_id"],
        "title": doc.metadata["title"],
        "department": doc.metadata.get("department"),
        "content_preview": doc.page_content[:300],
        "content_length": len(doc.page_content),
        "retrieval_score": doc.metadata.get("score"),
        "timestamp": doc.metadata.get("created_at"),
    }
```

## Project Structure

```
agentic-rag-weaviate/
├── agentic_rag/               # Core RAG engine
│   ├── graph.py               # LangGraph state machine (sync + async entry points)
│   ├── state.py               # AgenticRAGState TypedDict definition
│   ├── config.py              # Configuration management (env vars)
│   ├── nodes/
│   │   ├── retrieval_node.py  # Weaviate BM25 search
│   │   ├── authorization_node.py  # SpiceDB filtering (security boundary)
│   │   ├── reasoning_node.py  # Optional: adaptive retry logic
│   │   └── generation_node.py # Final answer with context
│   ├── authorization_helpers.py  # Batch permission checking
│   ├── weaviate_client.py     # Connection pooling for Weaviate
│   ├── grpc_helpers.py        # Connection pooling for SpiceDB
│   ├── logging_config.py      # Structured JSON logging
│   ├── node_helpers.py        # Shared utilities for nodes
│   └── validation.py          # Input validation and sanitization
│
├── api/                       # FastAPI web backend
│   ├── main.py                # FastAPI app entry point, CORS, static files
│   ├── routes.py              # API route handlers (query, users, health)
│   ├── models.py              # Pydantic request/response models
│   └── config.py              # API configuration (CORS origins, prefix)
│
├── ui/                        # Web frontend
│   └── index.html             # Single-page app (HTML/CSS/JS, 544 lines)
│
├── examples/                  # Demo scripts
│   ├── setup_environment.py   # Initialize data (loads 50 documents + permissions)
│   └── basic_example.py       # 8 demo scenarios (CLI-based)
│
├── scripts/                   # Utility scripts
│   ├── parse_documents.py     # Parse documents into structured objects
│   └── verify_permissions.py  # Test authorization patterns
│
├── tests/                     # Test suite
│   ├── conftest.py            # Pytest fixtures
│   └── test_basic_flow.py     # Integration tests
│
├── data/
│   ├── documents/             # 50 .txt files (5 departments × 10 docs)
│   ├── schema.zed             # SpiceDB permission schema
│   └── PERMISSIONS.md         # Permission matrix and patterns
│
├── run_ui.py                  # Web UI launcher with pre-flight checks
├── docker-compose.yml         # Weaviate + SpiceDB services
├── requirements.txt           # Python dependencies (includes fastapi, uvicorn)
├── .env.example               # Environment variable template
├── README.md                  # Overview, quick start, usage guide
└── ARCHITECTURE.md            # This file: deep technical dive
```

### Key Files by Interface

**CLI Interface:**
- Entry: `agentic_rag/graph.py::run_agentic_rag()`
- Examples: `examples/basic_example.py`
- Tests: `tests/test_basic_flow.py`

**Web Interface:**
- Launcher: `run_ui.py`
- Backend: `api/main.py`, `api/routes.py`
- Frontend: `ui/index.html`
- Entry: `agentic_rag/graph.py::run_agentic_rag_async()`

**Shared Core:**
- State machine: `agentic_rag/graph.py`
- Nodes: `agentic_rag/nodes/*.py`
- Services: `agentic_rag/weaviate_client.py`, `agentic_rag/grpc_helpers.py`

## Performance Characteristics

### CLI Interface Performance

**Default Mode (max_attempts=1):**
```
Query → Retrieval → Authorization → Generation
        ~0.5-1s     ~40-50ms       ~2-3s
```
**Total**: ~3-4 seconds per query

**Adaptive Mode (max_attempts > 1, with retry):**
```
Query → Retrieval → Authorization → Reasoning → Retrieval → Authorization → Generation
        ~0.5-1s     ~40-50ms       ~1-2s       ~0.5-1s     ~40-50ms       ~2-3s
```
**Total**: ~5-8 seconds per query (depends on retry count)

### Web Interface Performance

**API Request Overhead:**
```
Browser → FastAPI → LangGraph → Response Formatting → Browser
          ~10-20ms  ~3-4s       ~5-10ms              ~5-10ms
```
**Total**: ~3.5-4.5 seconds per query (default mode)

**Breakdown:**
- Network latency (localhost): ~5-10ms
- Pydantic request validation: ~2-5ms
- LangGraph execution: ~3-4s (same as CLI)
- Document formatting: ~3-5ms
- Response serialization (JSON): ~2-3ms
- Network response: ~5-10ms

**Under Load (Multiple Concurrent Queries):**

Async execution allows concurrent query handling:

- **Single query**: ~3.5-4.5s
- **5 concurrent queries**: ~4-5s each (minimal overhead)
- **10 concurrent queries**: ~5-6s each (slight queueing at OpenAI)

**Bottlenecks:**
1. OpenAI API calls (~2-3s) - most significant
2. Weaviate search (~0.5-1s)
3. SpiceDB checks (~40-50ms for 3-5 documents)
4. API/network overhead (~30-50ms total)

**Async Benefits Demonstrated:**

Without async (hypothetical):
- Query 1: 0s → 4s
- Query 2: 4s → 8s (blocked behind query 1)
- Query 3: 8s → 12s (blocked behind queries 1 & 2)

With async (actual):
- Query 1: 0s → 4s
- Query 2: 0s → 4.2s (concurrent)
- Query 3: 0s → 4.5s (concurrent)

### Optimization Opportunities

1. **Batch permission checks**
   ```python
   # Instead of N individual checks
   results = spicedb.BulkCheckPermission(documents)
   ```

2. **Cache permission results**
   ```python
   @lru_cache(maxsize=1000)
   def check_permission(subject, resource):
       return spicedb.CheckPermission(...)
   ```

3. **Parallel agent calls**
   ```python
   # Run planning and permission checks in parallel
   await asyncio.gather(
       agent.plan(),
       check_permissions()
   )
   ```

## Observability

### State Tracking

Every node updates the state with:
- `messages`: What happened (for debugging)
- `reasoning`: Why it happened (agent's thought process)
- Metrics: counts, attempts, etc.

### Example Message Flow

```
[AIMessage] Planning: Searching for engineering documents...
[SystemMessage] Retrieved 3 documents from Weaviate
[SystemMessage] Authorization: 2/3 documents authorized (1 denied)
[AIMessage] Reasoning: User has partial access, generating answer from available docs
[AIMessage] Answer: Based on the 2 authorized documents...
```

### Debugging (CLI)

```python
# Print state at each step
for event in graph.stream(initial_state):
    print(f"Node: {event}")
    print(f"State: {state}")
```

### API Request Tracing

The web interface provides additional observability layers:

**Frontend Observability:**

Users see transparent authorization information:

```javascript
// Displayed in browser UI
{
  "answer": "Based on the engineering documents...",
  "authorized_documents": [
    {
      "doc_id": "eng-001",
      "title": "System Architecture Guide",
      "content_preview": "Our system uses microservices..."
    },
    {
      "doc_id": "eng-002",
      "title": "API Design Standards",
      "content_preview": "RESTful API guidelines..."
    }
  ],
  "denied_documents": [
    {
      "doc_id": "hr-001",
      "title": "Employee Handbook",
      "reason": "User 'alice' does not have permission to access this document"
    }
  ],
  "stats": {
    "retrieved_count": 3,
    "authorized_count": 2,
    "denied_count": 1,
    "retrieval_attempts": 1,
    "execution_time_ms": 3420
  }
}
```

**Visual Indicators:**
- Green cards for authorized documents (doc_id, title, preview)
- Red cards for denied documents (doc_id, title, reason)
- Statistics panel showing counts and timing
- Loading spinner during execution

**Backend Observability:**

API layer provides structured response format:

```python
# api/routes.py
@router.post("/query")
async def execute_query(request: QueryRequest) -> APIResponse:
    start_time = time.time()

    try:
        result = await run_agentic_rag_async(...)
        execution_time_ms = int((time.time() - start_time) * 1000)

        # Format response with full observability
        return APIResponse(
            success=True,
            data=QueryResponseData(
                query=result["query"],
                subject_id=result["subject_id"],
                answer=result["answer"],
                authorized_documents=[...],  # Formatted
                denied_documents=[...],      # Extracted
                stats=QueryStats(
                    retrieved_count=...,
                    authorized_count=...,
                    denied_count=...,
                    retrieval_attempts=...,
                    execution_time_ms=execution_time_ms
                )
            )
        )
    except Exception as e:
        return APIResponse(
            success=False,
            error={
                "code": "EXECUTION_ERROR",
                "message": str(e)
            }
        )
```

**Logging Opportunities:**

Add structured logging to API layer for production observability:

```python
import structlog

logger = structlog.get_logger()

@router.post("/query")
async def execute_query(request: QueryRequest):
    logger.info(
        "query_start",
        subject_id=request.subject_id,
        query_length=len(request.query),
        max_attempts=request.max_attempts,
    )

    start_time = time.time()
    result = await run_agentic_rag_async(...)
    execution_time_ms = int((time.time() - start_time) * 1000)

    logger.info(
        "query_complete",
        subject_id=request.subject_id,
        retrieved_count=len(result["retrieved_documents"]),
        authorized_count=len(result["authorized_documents"]),
        denied_count=result["denied_count"],
        execution_time_ms=execution_time_ms,
    )

    return response
```

**Monitoring Metrics to Track:**

For production deployment, consider tracking:

1. **Performance Metrics:**
   - API response time (p50, p95, p99)
   - LangGraph execution time
   - Individual node execution times
   - OpenAI API latency

2. **Authorization Metrics:**
   - Authorization pass rate (per user)
   - Average denied documents per query
   - Most frequently denied documents
   - Permission check latency

3. **Usage Metrics:**
   - Queries per user per day
   - Query length distribution
   - Most queried topics
   - Concurrent request count

4. **Error Metrics:**
   - API error rate
   - Validation failures
   - OpenAI API errors
   - Service connectivity failures (Weaviate, SpiceDB)

## Summary

This architecture demonstrates:

1. **Security**: Deterministic authorization that cannot be bypassed by the agent or API layer
2. **Flexibility**: Agent adapts strategies when authorization fails (adaptive mode)
3. **Transparency**: Clear reasoning about what was allowed/denied, visible in both CLI and web UI
4. **Observability**: Full state tracking through the flow, with rich metrics in the API
5. **Extensibility**: Easy to add nodes, tools, API endpoints, or custom logic
6. **Dual Interface**: Same core engine powers both CLI (sync) and web UI (async) interfaces
7. **Production-Ready Patterns**: Demonstrates proper separation of concerns, though API auth needed for production

The key insights:

**Agentic behavior and security guarantees are compatible.** The agent provides flexibility and explanation AFTER the security boundary, not as a replacement for it.

**Interface flexibility doesn't compromise security.** Whether accessed via CLI or web UI, the authorization node always runs and enforces document-level permissions deterministically.

**Transparency builds trust.** By showing users exactly what they can and cannot access (and why), the system demonstrates how fine-grained authorization works in RAG systems, educating users about the security model.
