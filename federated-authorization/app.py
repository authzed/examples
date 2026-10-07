"""
Federated AuthZ Demo
====================
FastAPI application demonstrating federated identity (Keycloak + GitHub OAuth)
with centralized fine-grained authorization via SpiceDB.
"""
import os
import uuid
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from urllib.parse import urlencode
from contextlib import asynccontextmanager
from typing import Optional

import grpc
import httpx
from authlib.integrations.starlette_client import OAuth
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv

from authzed.api.v1 import (
    SyncClient as Client,
    WriteRelationshipsRequest,
    ReadRelationshipsRequest,
    DeleteRelationshipsRequest,
    CheckPermissionRequest,
    CheckPermissionResponse,
    CheckBulkPermissionsRequest,
    CheckBulkPermissionsRequestItem,
    LookupResourcesRequest,
    LookupSubjectsRequest,
    Relationship,
    RelationshipUpdate,
    ObjectReference,
    SubjectReference,
    RelationshipFilter,
    SubjectFilter,
    WriteSchemaRequest,
    Consistency,
    ZedToken,
)

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SPICEDB_ENDPOINT = os.environ.get("SPICEDB_ENDPOINT", "spicedb:50051")
SPICEDB_KEY = os.environ.get("SPICEDB_PRESHARED_KEY", "demo-token-do-not-use-in-prod")
KEYCLOAK_ISSUER = os.environ.get("KEYCLOAK_ISSUER", "http://keycloak:8080/realms/org-a")
KEYCLOAK_PUBLIC_ISSUER = os.environ.get("KEYCLOAK_PUBLIC_ISSUER", "http://localhost:8080/realms/org-a")
KEYCLOAK_CLIENT_ID = os.environ.get("KEYCLOAK_CLIENT_ID", "federated-authz-demo")
KEYCLOAK_CLIENT_SECRET = os.environ.get("KEYCLOAK_CLIENT_SECRET", "federated-authz-demo-secret")
GITHUB_CLIENT_ID = os.environ.get("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.environ.get("GITHUB_CLIENT_SECRET", "")
SESSION_SECRET = os.environ.get("SESSION_SECRET", "dev-session-secret-change-in-prod")
APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8000")

DB_PATH = os.environ.get("DB_PATH", "/data/app.db")
DOCUMENTS_DIR = Path(os.environ.get("DOCUMENTS_DIR", "/data/documents"))

SCHEMA_PATH = Path(__file__).parent / "spicedb" / "schema.zed"

# ---------------------------------------------------------------------------
# SpiceDB client (module-level singleton set on startup)
# ---------------------------------------------------------------------------

class _BearerTokenInterceptor(
    grpc.UnaryUnaryClientInterceptor, grpc.UnaryStreamClientInterceptor
):
    """Attaches the SpiceDB preshared key as an ``authorization`` header.

    gRPC refuses to attach access-token *call credentials* to an insecure
    channel, and the ``local_channel_credentials`` workaround only permits
    loopback peers — neither works when the app reaches SpiceDB over the
    Docker network. Sending the token as request metadata on a plain insecure
    channel does, which is what this interceptor does. (Insecure transport is
    fine for this local demo; use TLS in production.)
    """

    def __init__(self, token: str):
        self._extra_metadata = [("authorization", f"Bearer {token}")]

    def _with_token(self, details):
        metadata = list(details.metadata or []) + self._extra_metadata
        return details._replace(metadata=metadata)

    def intercept_unary_unary(self, continuation, client_call_details, request):
        return continuation(self._with_token(client_call_details), request)

    def intercept_unary_stream(self, continuation, client_call_details, request):
        return continuation(self._with_token(client_call_details), request)


def make_spicedb_client(endpoint: str, token: str) -> Client:
    """Build a synchronous SpiceDB client over an insecure channel."""
    channel = grpc.intercept_channel(
        grpc.insecure_channel(endpoint), _BearerTokenInterceptor(token)
    )
    client = Client.__new__(Client)
    client.init_stubs(channel)
    return client


_spicedb_client: Optional[Client] = None


def get_spicedb() -> Client:
    if _spicedb_client is None:
        raise RuntimeError("SpiceDB client not initialized")
    return _spicedb_client


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------
def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT,
            display_name TEXT,
            provider TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            filename TEXT NOT NULL,
            owner_user_id TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# SpiceDB helpers
# The authzed Client exposes RPC methods directly; the preshared key is
# injected as request metadata by _BearerTokenInterceptor (see above).
# ---------------------------------------------------------------------------

def _obj(object_type: str, object_id: str) -> ObjectReference:
    return ObjectReference(object_type=object_type, object_id=object_id)


def _subj(object_type: str, object_id: str) -> SubjectReference:
    return SubjectReference(object=_obj(object_type, object_id))


def _consistency(zedtoken: Optional[str]) -> Consistency:
    """Consistency for reads.

    With a ZedToken (returned by a prior write), request ``at_least_as_fresh``
    so the caller reliably sees its own writes without forcing a fully
    consistent (slower) read. Without one, fall back to ``minimize_latency``.
    """
    if zedtoken:
        return Consistency(at_least_as_fresh=ZedToken(token=zedtoken))
    return Consistency(minimize_latency=True)


def write_relationship(client: Client, resource_type: str, resource_id: str,
                        relation: str, subject_type: str, subject_id: str) -> str:
    """Write a relationship; return the ZedToken of the write for read-your-writes."""
    resp = client.WriteRelationships(WriteRelationshipsRequest(
        updates=[RelationshipUpdate(
            operation=RelationshipUpdate.OPERATION_TOUCH,
            relationship=Relationship(
                resource=_obj(resource_type, resource_id),
                relation=relation,
                subject=_subj(subject_type, subject_id),
            ),
        )]
    ))
    return resp.written_at.token


def delete_relationship(client: Client, resource_type: str, resource_id: str,
                         relation: str, subject_type: str, subject_id: str) -> str:
    """Delete a relationship; return the ZedToken of the delete for read-your-writes."""
    resp = client.DeleteRelationships(DeleteRelationshipsRequest(
        relationship_filter=RelationshipFilter(
            resource_type=resource_type,
            optional_resource_id=resource_id,
            optional_relation=relation,
            optional_subject_filter=SubjectFilter(
                subject_type=subject_type,
                optional_subject_id=subject_id,
            ),
        )
    ))
    return resp.deleted_at.token


def check_permission(client: Client, resource_type: str, resource_id: str,
                      permission: str, subject_id: str,
                      zedtoken: Optional[str] = None) -> bool:
    """Return True only if SpiceDB affirmatively grants the permission.

    Fails CLOSED: any error (SpiceDB unavailable, bad request, …) is logged and
    treated as "no permission", so an outage can never fall open into granting
    access. Only PERMISSIONSHIP_HAS_PERMISSION grants; NO_PERMISSION and
    CONDITIONAL_PERMISSION both deny. Every call site reads this as
    ``if not check_permission(...): deny``.
    """
    try:
        resp = client.CheckPermission(CheckPermissionRequest(
            resource=_obj(resource_type, resource_id),
            permission=permission,
            subject=_subj("user", subject_id),
            consistency=_consistency(zedtoken),
        ))
    except Exception as e:
        print(f"[spicedb] CheckPermission({permission} on {resource_type}:{resource_id}) "
              f"failed, denying: {e}")
        return False
    return resp.permissionship == CheckPermissionResponse.PERMISSIONSHIP_HAS_PERMISSION


def check_permissions_bulk(client: Client, resource_type: str, resource_id: str,
                           permissions: list[str], subject_id: str,
                           zedtoken: Optional[str] = None) -> dict[str, bool]:
    """Check several permissions on one resource in a single round-trip.

    Returns ``{permission: granted}``. Fails CLOSED: every permission starts at
    False and only an affirmative HAS_PERMISSION flips it to True, so a failed
    request, a per-item error, or a CONDITIONAL result all deny.
    """
    granted = {p: False for p in permissions}
    try:
        resp = client.CheckBulkPermissions(CheckBulkPermissionsRequest(
            consistency=_consistency(zedtoken),
            items=[CheckBulkPermissionsRequestItem(
                resource=_obj(resource_type, resource_id),
                permission=p,
                subject=_subj("user", subject_id),
            ) for p in permissions],
        ))
    except Exception as e:
        print(f"[spicedb] CheckBulkPermissions on {resource_type}:{resource_id} "
              f"failed, denying all: {e}")
        return granted
    for pair in resp.pairs:
        if pair.HasField("item"):
            granted[pair.request.permission] = (
                pair.item.permissionship == CheckPermissionResponse.PERMISSIONSHIP_HAS_PERMISSION
            )
        else:
            # Per-item error from SpiceDB: leave this permission denied (fail closed).
            print(f"[spicedb] bulk check error for '{pair.request.permission}' on "
                  f"{resource_type}:{resource_id}: {pair.error.message}")
    return granted


def lookup_viewable_documents(client: Client, user_id: str,
                              zedtoken: Optional[str] = None) -> list[str]:
    """Return the ids of documents the user can view.

    Fails CLOSED: on any error, log and return an empty list rather than a
    partially-streamed set — the dashboard shows nothing instead of a misleading
    listing. (LookupResources only ever yields authorized resources, so this can
    never over-list; the empty return is purely to avoid a confusing partial.)
    """
    doc_ids = []
    try:
        for resp in client.LookupResources(LookupResourcesRequest(
            resource_object_type="document",
            permission="view",
            subject=_subj("user", user_id),
            consistency=_consistency(zedtoken),
        )):
            doc_ids.append(resp.resource_object_id)
    except Exception as e:
        print(f"[spicedb] LookupResources(view) for user:{user_id} failed, "
              f"returning no documents: {e}")
        return []
    return doc_ids


def find_idp_binding(client: Client, idp_type: str, idp_subject: str) -> Optional[str]:
    """Return the internal user UUID bound to this IdP account, or None.

    Identity resolution across logins depends on this lookup, so errors are
    NOT swallowed: treating a transient SpiceDB failure as "no binding" would
    mint a fresh user UUID on every login and orphan the previous identity's
    documents. An account with no binding simply yields no subjects, which
    returns None without raising.

    This resolves which internal user an external IdP account maps to. We use
    LookupSubjects on the bound_to relation rather than the ReadRelationships
    escape hatch: it fits the "who is the subject of this relation" query
    shape and, unlike a raw ReadRelationships datastore read, benefits from
    SpiceDB's computed-permission cache.
    """
    for resp in client.LookupSubjects(LookupSubjectsRequest(
        resource=_obj(idp_type, idp_subject),
        permission="bound_to",
        subject_object_type="user",
    )):
        return resp.subject.subject_object_id
    return None


def read_document_relationships(client: Client, doc_id: str,
                                zedtoken: Optional[str] = None) -> list[dict]:
    results = []
    try:
        # Deliberate use of the ReadRelationships escape hatch. This is NOT an
        # access decision (those go through check_permission). The sharing UI
        # needs the *specific grant relation* — viewer vs editor — so it can
        # display and individually revoke each grant. LookupSubjects on the
        # "view" permission would flatten that distinction away and also pull
        # in the owner, so reading the raw grants is the right tool here.
        for resp in client.ReadRelationships(ReadRelationshipsRequest(
            relationship_filter=RelationshipFilter(
                resource_type="document",
                optional_resource_id=doc_id,
            ),
            consistency=_consistency(zedtoken),
        )):
            rel = resp.relationship
            results.append({
                "relation": rel.relation,
                "subject_type": rel.subject.object.object_type,
                "subject_id": rel.subject.object.object_id,
            })
    except Exception as e:
        # Fail closed: on error show no sharees rather than a partial list.
        print(f"[spicedb] ReadRelationships for document:{doc_id} failed, "
              f"returning no sharees: {e}")
        return []
    return results


# ---------------------------------------------------------------------------
# OAuth setup (Authlib)
# ---------------------------------------------------------------------------
oauth = OAuth()

oauth.register(
    name="keycloak",
    client_id=KEYCLOAK_CLIENT_ID,
    client_secret=KEYCLOAK_CLIENT_SECRET,
    # Browser-facing: the user's browser is redirected here to log in.
    # Must use the host-reachable address (localhost), not the container-network name.
    authorize_url=f"{KEYCLOAK_PUBLIC_ISSUER}/protocol/openid-connect/auth",
    # Server-to-server: the app container calls these directly; must use the
    # container-network name ('keycloak'), not localhost, which is unreachable
    # from inside the container.
    access_token_url=f"{KEYCLOAK_ISSUER}/protocol/openid-connect/token",
    # jwks_uri and userinfo_endpoint are stored as server_metadata (Authlib
    # treats unrecognised register() kwargs as static server metadata), so
    # parse_id_token / fetch_jwk_set can find them without an OIDC discovery
    # HTTP request, and they point at the internal container-network address.
    jwks_uri=f"{KEYCLOAK_ISSUER}/protocol/openid-connect/certs",
    userinfo_endpoint=f"{KEYCLOAK_ISSUER}/protocol/openid-connect/userinfo",
    client_kwargs={"scope": "openid email profile"},
)

oauth.register(
    name="github",
    client_id=GITHUB_CLIENT_ID,
    client_secret=GITHUB_CLIENT_SECRET,
    authorize_url="https://github.com/login/oauth/authorize",
    access_token_url="https://github.com/login/oauth/access_token",
    client_kwargs={"scope": "read:user user:email"},
)


# ---------------------------------------------------------------------------
# App lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _spicedb_client
    init_db()

    # Connect to SpiceDB with insecure channel + bearer token
    _spicedb_client = make_spicedb_client(SPICEDB_ENDPOINT, SPICEDB_KEY)

    # Write schema on startup (idempotent — safe to re-run)
    schema = SCHEMA_PATH.read_text()
    try:
        _spicedb_client.WriteSchema(WriteSchemaRequest(schema=schema))
        print("[startup] SpiceDB schema written.")
    except Exception as e:
        print(f"[startup] Schema write warning: {e}")

    yield


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET, max_age=86400)

app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------
def current_user(request: Request) -> Optional[dict]:
    return request.session.get("user")



def get_or_create_user(idp_type: str, idp_subject: str, email: str, display_name: str, provider: str) -> str:
    """
    Resolve or create an internal user, writing the SpiceDB IdP binding.
    Returns the internal user UUID (canonical identity across all IdPs).
    """
    client = get_spicedb()

    existing = find_idp_binding(client, idp_type, idp_subject)
    if existing:
        return existing

    user_id = str(uuid.uuid4())
    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO users (id, email, display_name, provider, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, email, display_name, provider, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()

    write_relationship(client, idp_type, idp_subject, "bound_to", "user", user_id)

    return user_id


# ---------------------------------------------------------------------------
# Routes: Landing page
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    user = current_user(request)
    if not user:
        return templates.TemplateResponse(request, "login.html")

    client = get_spicedb()
    doc_ids = lookup_viewable_documents(client, user["id"], request.session.get("zedtoken"))

    db = get_db()
    docs = []
    if doc_ids:
        placeholders = ",".join("?" * len(doc_ids))
        docs = db.execute(
            f"SELECT * FROM documents WHERE id IN ({placeholders})", doc_ids
        ).fetchall()
    db.close()

    return templates.TemplateResponse(request, "dashboard.html", {
        "user": user,
        "documents": docs,
    })


# ---------------------------------------------------------------------------
# Routes: Keycloak OAuth
# ---------------------------------------------------------------------------
@app.get("/auth/keycloak/login")
async def keycloak_login(request: Request):
    redirect_uri = f"{APP_BASE_URL}/auth/keycloak/callback"
    return await oauth.keycloak.authorize_redirect(request, redirect_uri)


@app.get("/auth/keycloak/callback")
async def keycloak_callback(request: Request):
    try:
        token = await oauth.keycloak.authorize_access_token(request)
    except Exception as e:
        return templates.TemplateResponse(request, "error.html", {
            "error": f"Keycloak login failed: {e}",
        })

    # Authlib populates userinfo from the OIDC userinfo endpoint automatically
    userinfo = token.get("userinfo") or {}

    # Fall back to manually decoding the id_token JWT payload if needed
    if not userinfo.get("sub"):
        import base64
        parts = token.get("id_token", "..").split(".")
        if len(parts) >= 2:
            padded = parts[1] + "=" * (4 - len(parts[1]) % 4)
            userinfo = json.loads(base64.urlsafe_b64decode(padded))

    sub = userinfo.get("sub", "unknown")
    email = userinfo.get("email", f"{sub}@keycloak.org")
    display_name = userinfo.get("name") or userinfo.get("preferred_username") or email

    user_id = get_or_create_user(
        idp_type="keycloak_account",
        idp_subject=sub,
        email=email,
        display_name=display_name,
        provider="keycloak",
    )

    request.session["user"] = {
        "id": user_id,
        "email": email,
        "display_name": display_name,
        "provider": "Keycloak (Org A)",
    }
    # Keep the id_token so /auth/logout can end the Keycloak SSO session via a
    # front-channel RP-initiated logout (id_token_hint).  Without ending that
    # session, clearing our own cookie leaves Keycloak's browser SSO session
    # alive and the next "Log in with Keycloak" silently re-authenticates with
    # no password prompt — so logout appears to do nothing.
    if token.get("id_token"):
        request.session["keycloak_id_token"] = token["id_token"]
    return RedirectResponse("/", status_code=302)


# ---------------------------------------------------------------------------
# Routes: GitHub OAuth
# ---------------------------------------------------------------------------
@app.get("/auth/github/login")
async def github_login(request: Request):
    if not GITHUB_CLIENT_ID:
        return templates.TemplateResponse(request, "error.html", {
            "error": "GitHub OAuth is not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in .env",
        })
    redirect_uri = f"{APP_BASE_URL}/auth/github/callback"
    return await oauth.github.authorize_redirect(request, redirect_uri)


@app.get("/auth/github/callback")
async def github_callback(request: Request):
    try:
        token = await oauth.github.authorize_access_token(request)
    except Exception as e:
        return templates.TemplateResponse(request, "error.html", {
            "error": f"GitHub login failed: {e}",
        })

    # Fetch GitHub user profile
    async with httpx.AsyncClient() as http:
        resp = await http.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {token['access_token']}",
                     "Accept": "application/vnd.github+json"},
        )
        gh_user = resp.json()

        # Fetch primary email if not in profile
        email = gh_user.get("email")
        if not email:
            email_resp = await http.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {token['access_token']}",
                         "Accept": "application/vnd.github+json"},
            )
            emails = email_resp.json()
            primary = next((e for e in emails if e.get("primary")), None)
            email = primary["email"] if primary else f"{gh_user['login']}@github.local"

    github_id = str(gh_user["id"])
    display_name = gh_user.get("name") or gh_user.get("login")

    user_id = get_or_create_user(
        idp_type="github_account",
        idp_subject=github_id,
        email=email,
        display_name=display_name,
        provider="github",
    )

    request.session["user"] = {
        "id": user_id,
        "email": email,
        "display_name": display_name,
        "provider": "GitHub (Org B)",
    }
    return RedirectResponse("/", status_code=302)


# ---------------------------------------------------------------------------
# Routes: Logout
# ---------------------------------------------------------------------------
@app.get("/auth/logout")
async def logout(request: Request):
    # Clearing our own session cookie only logs the user out of THIS app.  For a
    # Keycloak user we must also end the upstream SSO session, otherwise the
    # browser's Keycloak cookie survives and the next login silently
    # re-authenticates — making it look like logout did nothing.
    #
    # This uses an OIDC front-channel (RP-initiated) logout: the browser is
    # redirected to Keycloak's end-session endpoint on the public issuer
    # (KEYCLOAK_PUBLIC_ISSUER / localhost:8080), which the browser can reach.
    # Keycloak only honours an id_token_hint whose issuer matches that endpoint's
    # host, so the realm pins frontendUrl to the public address (see
    # realm-export.json): every token it mints carries iss=http://localhost:8080/
    # even though the app exchanges the auth code over the internal address
    # (keycloak:8080).  Without that pin the hint would be issued for keycloak:8080
    # and Keycloak would reject it against the localhost request, leaving the SSO
    # session alive.  Keycloak ends the session and redirects the browser back to
    # post_logout_redirect_uri (registered on the client in the realm).
    #
    # GitHub has no equivalent: a third-party app cannot (and should not) end a
    # user's github.com session, so clearing our session is the complete logout.
    id_token = request.session.get("keycloak_id_token")
    request.session.clear()
    if id_token:
        params = urlencode({
            "id_token_hint": id_token,
            "post_logout_redirect_uri": f"{APP_BASE_URL}/",
        })
        return RedirectResponse(
            f"{KEYCLOAK_PUBLIC_ISSUER}/protocol/openid-connect/logout?{params}",
            status_code=302,
        )
    return RedirectResponse("/", status_code=302)


# ---------------------------------------------------------------------------
# Routes: Documents
# ---------------------------------------------------------------------------
@app.get("/documents/new", response_class=HTMLResponse)
async def new_document_form(request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse(request, "document_new.html", {"user": user})


@app.post("/documents/new")
async def create_document(request: Request, title: str = Form(...), content: str = Form(...)):
    user = current_user(request)
    if not user:
        return RedirectResponse("/", status_code=302)

    doc_id = str(uuid.uuid4())
    filename = f"{doc_id}.md"
    filepath = DOCUMENTS_DIR / filename

    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding="utf-8")

    db = get_db()
    db.execute(
        "INSERT INTO documents (id, title, filename, owner_user_id, created_at) VALUES (?, ?, ?, ?, ?)",
        (doc_id, title, filename, user["id"], datetime.utcnow().isoformat()),
    )
    db.commit()
    db.close()

    # Write owner relationship to SpiceDB; remember the ZedToken so the very
    # next read (the redirect below) reliably sees this write.
    client = get_spicedb()
    token = write_relationship(client, "document", doc_id, "owner", "user", user["id"])
    request.session["zedtoken"] = token

    return RedirectResponse(f"/documents/{doc_id}", status_code=302)


@app.get("/documents/{doc_id}", response_class=HTMLResponse)
async def view_document(request: Request, doc_id: str):
    user = current_user(request)
    if not user:
        return RedirectResponse("/", status_code=302)

    db = get_db()
    doc = db.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    db.close()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    client = get_spicedb()
    zedtoken = request.session.get("zedtoken")

    # One round-trip for all three permissions on this document; fails closed
    # (every permission defaults to denied if the check errors).
    perms = check_permissions_bulk(
        client, "document", doc_id, ["view", "edit", "share"], user["id"], zedtoken
    )
    if not perms["view"]:
        return templates.TemplateResponse(request, "error.html", {
            "error": "Access denied. You do not have permission to view this document.",
            "user": user,
        }, status_code=403)

    can_edit = perms["edit"]
    can_share = perms["share"]

    content = ""
    filepath = DOCUMENTS_DIR / doc["filename"]
    if filepath.exists():
        content = filepath.read_text(encoding="utf-8")

    sharees = []
    if can_share:
        # Read all relationships and enrich with display names
        rels = read_document_relationships(client, doc_id, zedtoken)
        db2 = get_db()
        for rel in rels:
            if rel["relation"] in ("viewer", "editor") and rel["subject_type"] == "user":
                uid = rel["subject_id"]
                row = db2.execute("SELECT display_name, email, provider FROM users WHERE id = ?", (uid,)).fetchone()
                sharees.append({
                    "user_id": uid,
                    "relation": rel["relation"],
                    "display_name": row["display_name"] if row else uid,
                    "email": row["email"] if row else "",
                    "provider": row["provider"] if row else "",
                })
        db2.close()

    # All other users for the sharing dropdown. List by internal user id (the
    # UUID) — NOT deduped by email. Each internal user is a distinct shareable
    # identity, and its id is exactly the UUID that identity authenticates as
    # and that document relationships reference. Collapsing by email would hand
    # back a UUID nobody logs in as (breaking the share) and would also merge
    # two legitimately-separate identities that share an email across providers.
    all_users = []
    if can_share:
        db3 = get_db()
        rows = db3.execute(
            "SELECT id, display_name, email, provider FROM users WHERE id != ? ORDER BY display_name",
            (user["id"],),
        ).fetchall()
        db3.close()
        sharee_ids = {s["user_id"] for s in sharees}
        all_users = [r for r in rows if r["id"] not in sharee_ids]

    return templates.TemplateResponse(request, "document_view.html", {
        "user": user,
        "doc": doc,
        "content": content,
        "can_edit": can_edit,
        "can_share": can_share,
        "sharees": sharees,
        "all_users": all_users,
    })


def _safe_doc_id(doc_id: str) -> str:
    """Return the canonical form of a document id, or 404 on anything invalid.

    Document ids are always generated with ``uuid.uuid4()`` (see
    ``create_document``), so a value that isn't a UUID can only be a bad or
    malicious request. Normalizing through ``uuid.UUID`` also guarantees the id
    is safe to interpolate into a redirect ``Location``: it can contain only hex
    digits and hyphens, so it cannot break out of the ``/documents/`` path.
    """
    try:
        return str(uuid.UUID(doc_id))
    except ValueError:
        raise HTTPException(status_code=404, detail="Document not found")


@app.post("/documents/{doc_id}/edit")
async def edit_document(request: Request, doc_id: str, content: str = Form(...)):
    user = current_user(request)
    if not user:
        return RedirectResponse("/", status_code=302)

    doc_id = _safe_doc_id(doc_id)

    client = get_spicedb()
    if not check_permission(client, "document", doc_id, "edit", user["id"],
                            request.session.get("zedtoken")):
        raise HTTPException(status_code=403, detail="You cannot edit this document")

    db = get_db()
    doc = db.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
    db.close()
    if not doc:
        raise HTTPException(status_code=404)

    filepath = DOCUMENTS_DIR / doc["filename"]
    filepath.write_text(content, encoding="utf-8")

    return RedirectResponse(f"/documents/{doc_id}", status_code=302)


@app.post("/documents/{doc_id}/share")
async def share_document(
    request: Request,
    doc_id: str,
    target_user_id: str = Form(...),
    permission_level: str = Form(...),
):
    user = current_user(request)
    if not user:
        return RedirectResponse("/", status_code=302)

    doc_id = _safe_doc_id(doc_id)

    client = get_spicedb()
    if not check_permission(client, "document", doc_id, "share", user["id"],
                            request.session.get("zedtoken")):
        raise HTTPException(status_code=403, detail="Only the document owner can share")

    if permission_level not in ("viewer", "editor"):
        raise HTTPException(status_code=400, detail="Invalid permission level")

    # Sharing with yourself is a no-op: as owner you already have view/edit/share.
    # Reject it so a redundant viewer/editor grant can't be created (and later
    # "revoked" with no visible effect).
    if target_user_id == user["id"]:
        raise HTTPException(status_code=400, detail="You cannot share a document with yourself")

    token = write_relationship(client, "document", doc_id, permission_level, "user", target_user_id)
    request.session["zedtoken"] = token

    return RedirectResponse(f"/documents/{doc_id}", status_code=302)


@app.post("/documents/{doc_id}/unshare")
async def unshare_document(
    request: Request,
    doc_id: str,
    target_user_id: str = Form(...),
    relation: str = Form(...),
):
    user = current_user(request)
    if not user:
        return RedirectResponse("/", status_code=302)

    doc_id = _safe_doc_id(doc_id)

    client = get_spicedb()
    if not check_permission(client, "document", doc_id, "share", user["id"],
                            request.session.get("zedtoken")):
        raise HTTPException(status_code=403, detail="Only the document owner can revoke access")

    if relation not in ("viewer", "editor"):
        raise HTTPException(status_code=400, detail="Invalid relation")

    token = delete_relationship(client, "document", doc_id, relation, "user", target_user_id)
    request.session["zedtoken"] = token

    return RedirectResponse(f"/documents/{doc_id}", status_code=302)
