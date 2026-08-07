# Structured logging across every layer — router → service → repository, with a debug mode and a propagated request ID

## Context

fhir-server has the *foundation* of a good logging system and almost none of the actual logging. `app/core/logging.py` already ships a `JsonFormatter` that emits one JSON object per line, auto-injects `request_id` from a `ContextVar`, and merges any `extra={...}` dict into the output — that design is correct and stays. What's missing is everything built on top of it.

Naveen wants logging present at every layer (router → service → repository), driven by a mode: **debug mode on → log everything, including payloads and full detail; debug mode off → log the flow plus the important data only**. The request ID must appear on every line. Today the request ID is generated inside this server; going forward it will arrive from the GraphQL gateway (`fhir-gql`) instead, and the two must be the same ID so a single trace spans both services.

This plan covers the plumbing, the rules for deciding *what* to log *where*, the other places worth logging beyond the three main layers, and a rollout order that proves the pattern on one resource before replicating it across ~35.

## Current state (read from the source, not assumed)

**What exists:**

| Place | What it logs |
|---|---|
| `app/core/logging.py` | `JsonFormatter` (timestamp/level/logger/message + auto `request_id` + all `extra` fields + traceback), `setup_logging()`, `get_logger()` |
| `app/errors/handlers.py` | Every error path — method, path, query_params, client_ip; `info` for validation, `warning` for operational, `error`/`critical` for non-operational and unhandled. **Already good; the strongest logging in the codebase.** |
| `app/main.py` | Startup/shutdown, enabled-routes line, Redis connect failure, readiness-probe DB/Redis failures |
| `app/middleware/rate_limit.py`, `app/core/session.py`, `app/core/database.py` | A handful of lines each |

**What's missing or broken:**

1. **Zero logging in `app/routers/`, `app/services/`, `app/repository/`** — all ~35 resources. The entire happy path is invisible.
2. **No access log.** A successful `POST /organizations` → 201 produces *no log line at all*. There is no record that the request happened.
3. **Request ID is always freshly generated.** `app/core/request_context.py` does `request_id = str(uuid.uuid4())` unconditionally — it never reads an inbound header. When `fhir-gql` starts sending its own ID, correlation breaks *silently*: both services log valid-looking IDs that never match.
4. **No debug mode.** `setup_logging()` hardcodes `root.setLevel(logging.INFO)`. There is no `logging:` section in `configs/config.yaml` and no `LogConfig` in `app/core/config.py`.
5. **Duplicate middleware.** `app/core/request_context.py` and `app/middleware/request_context.py` are byte-identical copies of `request_context_middleware`. `app/main.py` imports the `core` one; `app/middleware/__init__.py` exports the other. Whichever is edited, half the codebase points at the other.
6. **No context beyond `request_id`.** Logs can't be filtered by `org_id` or acting user — which, on a multi-tenant server, is the first thing anyone will want to filter by.
7. **`get_request_id()` fragility** — `app/errors/handlers.py:35` reads `request.state.request_id` unguarded. If the request-context middleware didn't run (e.g. an exception raised in a middleware layered above it), the error handler itself raises `AttributeError`.

---

## Phase 1 — Plumbing (done once, benefits every layer)

### 1.1 `logging:` section in `configs/config.yaml`

New `LogConfig(BaseModel)` in `app/core/config.py`, wired as `logging: LogConfig = Field(default_factory=LogConfig)` on `Settings` — same shape as the existing `RateLimitConfig`/`RoutesConfig`, so it inherits the whole precedence chain (real env var > `.env` > `configs/config.yaml` > defaults) for free.

```yaml
logging:
  level: INFO            # root log level
  format: json           # json | console  (console = human-readable local dev)
  debug_payloads: false  # ⚠️ THE debug-mode switch — logs full request/response bodies
  slow_query_ms: 500     # warn on any SQL statement slower than this
  sql_echo: false        # log every SQL statement at DEBUG
  redact:                # field names masked even when debug_payloads is on
    - authorization
    - token
    - password
    - ssn
```

Per-environment override with no file edit, via the existing `env_nested_delimiter="__"`: `LOGGING__DEBUG_PAYLOADS=true`, `LOGGING__LEVEL=DEBUG`.

> **⚠️ PHI warning — must be a comment in `config.yaml` itself, not just here.** This is a FHIR server. `debug_payloads: true` writes patient names, addresses, birth dates, and identifiers to the log stream. It is a local-development switch. It must never be enabled in production, and the `redact` list is a backstop for obvious secrets — **not** a PHI safeguard.

### 1.2 Expand the context vars

`app/core/request_context.py` becomes **ContextVars only** (the middleware moves out — see 1.3):

```python
request_id_ctx_var: ContextVar[str | None]
user_id_ctx_var:    ContextVar[str | None]   # actor.sub
org_id_ctx_var:     ContextVar[str | None]   # actor.org_id
```

`JsonFormatter.format()` injects every non-`None` one automatically, exactly as it already does for `request_id`.

**This is the central design decision of the plan.** A repository method has no access to the `Request` object and never will — threading `request_id` through 35 repositories × ~15 methods each is not viable. ContextVars are the only mechanism that correlates a repository log line back to its HTTP request without touching a single function signature. They also work correctly under asyncio: each request task gets its own copy.

`user_id`/`org_id` get set where they first become known — in `require_permission()`'s `_check` (`app/auth/rbac.py`), right after `check_permission()` returns the typed `AuthUser`. That's a single place covering every auth-gated route.

### 1.3 Request ID: inherit it from upstream

The whole change is one line in the middleware:

```python
request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
```

Today it generates (no upstream sends the header, so behavior is unchanged); once `fhir-gql` sets `X-Request-ID` on its forwarded calls, the same ID spans gateway and server with no further work. The response already echoes `X-Request-ID` back, which stays.

**Delete the duplicate:** `app/core/request_context.py` keeps the ContextVars, `app/middleware/request_context.py` keeps the middleware function, and `app/main.py:16` changes to import from `app.middleware`. One definition, one import path.

### 1.4 New `app/middleware/access_log.py` — one line per request, always on

```json
{"event":"http.request","method":"POST","path":"/api/fhir/v1/organizations",
 "status":201,"duration_ms":84,"request_id":"...","org_id":"...","user_id":"..."}
```

Metadata only — **not** the body. Reading the request body inside middleware fights Starlette's single-consumption request stream and risks breaking every route that depends on it. Payload logging belongs at the router layer instead (see 2.x), where the *validated Pydantic model* is already in hand, is trivially redactable, and costs nothing extra to serialize.

Level: `INFO` for 2xx/3xx, `WARNING` for 4xx, `ERROR` for 5xx. Skip the paths `RateLimitMiddleware` already excludes (`/health`, `/health/ready`, `/docs`, `/openapi.json`, `/favicon.ico`) so probes don't flood the stream.

### 1.5 One helper for debug mode — `app/core/logging.py`

```python
def log_payload(logger: logging.Logger, event: str, payload: BaseModel | dict) -> None:
    """No-op unless settings.logging.debug_payloads. Redacts configured
    field names, then logs at DEBUG with the payload under `payload`."""
```

Internally guarded with `logger.isEnabledFor(logging.DEBUG)` **and** the config flag, so `payload.model_dump()` never runs in production. This is the *only* helper — everything else stays explicit hand-placed `logger.info(..., extra={...})` calls. Same reasoning as the DI auto-discovery decision: what gets logged should be under direct control, not inferred by a decorator that has to guess what matters.

### 1.6 SQLAlchemy event listeners in `app/core/database.py`

`before_cursor_execute` / `after_cursor_execute` on the async engine's sync engine:

- `sql_echo: true` → every statement logged at DEBUG with duration
- any statement over `slow_query_ms` → WARNING with statement + duration

**Highest value-per-line change in this plan**: it instruments every query in all ~35 resources from one file, with no per-repository work at all, and it's the thing most likely to explain a production latency complaint.

### 1.7 Fix `setup_logging()`

- Read `level` and `format` from `settings.logging` instead of hardcoding `INFO`/JSON.
- Add a plain `console` formatter branch for local dev.
- Explicitly set `uvicorn.access` to `WARNING`. Uvicorn's own plaintext access log otherwise duplicates ours *and* emits non-JSON lines into a JSON stream, which breaks log aggregation downstream.
- Set `sqlalchemy.engine` explicitly rather than letting `sql_echo` fight the root level.

### 1.8 Harden `get_request_id()`

`app/errors/handlers.py:35` → read from `request_id_ctx_var.get()` with `getattr(request.state, "request_id", None)` as fallback. An error handler must never itself raise.

---

## Phase 2 — The layer rules (how to decide what goes where)

Two governing principles:

1. **Log at the layer that knows the *meaning*.** `organization_repository` knows "3 rows deleted"; it does not know *why*. `organization_service` knows "replacing the telecom list during a patch". So business events log in the service; the repository logs only mechanical facts that can't be reconstructed from higher up.
2. **One line per meaningful event — not per function call.** Entry+exit logging at every layer produces ~8 lines for one request. That's noise, not observability. The access log covers "a request happened"; everything else should earn its line.

| Layer | Always on (INFO / WARN) | Debug mode only | Never |
|---|---|---|---|
| **Middleware** | 1 access line: method, path, status, `duration_ms` | headers, body size, query params | `Authorization` header |
| **Auth** (`dependencies.py`, `rbac.py`) | WARN on 401/403 with reason + sub/org; INFO on JWKS refetch | decoded claims | raw JWT |
| **Router** | nothing — the access log already covers it | `log_payload(...)` of the validated Create/Patch schema | — |
| **Service** | INFO on business outcomes: `organization.created` + new public id; cycle-check rejection; org-scope mismatch (the 404-not-403 path) | method arguments | — |
| **Repository** | WARN on slow query; WARN on unexpected row counts (e.g. delete affected 0) | generated IDs, rows affected, filter params | full result sets |
| **Errors** | already correct — only add `org_id`/`user_id` from context | the request payload | stack traces to the client (already handled) |

Event naming: dotted, resource-first, past-tense for outcomes — `organization.created`, `organization.patch.rejected_cycle`, `db.slow_query`, `auth.permission_denied`. Passed as `extra={"event": ...}` so the JSON stream is filterable without regex over `message`.

---

## Phase 3 — Other places worth logging

Beyond the three main layers, these are single-location changes with disproportionate value:

- **Startup config summary** (`app/main.py` lifespan) — environment, log level, rate-limit backend, enabled route count. One line that answers most "why is prod behaving differently from dev" questions without shell access.
- **DB pool** — connect / disconnect / pool exhaustion (partially present in `app/core/database.py`).
- **Rate limiting** (`app/middleware/rate_limit.py`) — every 429 with the offending key, and the **redis → memory fallback, which currently degrades silently**. A production instance quietly losing cross-instance rate limiting is exactly the kind of thing that should be loud.
- **Reference resolver** (`app/core/reference_resolver.py`) — failed reference validation is a real business event (a caller pointed at a resource that doesn't exist) and is completely invisible today.
- **Auth** (`app/auth/dependencies.py`) — JWKS cache miss / refetch. `PyJWKClient` makes a network call on the request hot path when it sees an unknown `kid`; today there's no way to see that happening.
- **Content negotiation** (`app/core/content_negotiation.py`) — DEBUG only, which branch was taken (FHIR vs. plain). Useful when a client swears it asked for FHIR.

---

## Phase 4 — Rollout order

Do **not** touch all ~35 resources at once.

1. **Phase 1 plumbing (1.1–1.8) only.** Verify the app boots, tests stay green, and a real request produces exactly one access line with a correlating `request_id`. At this point — before a single resource file is touched — you already have: gateway-propagated request IDs, an access log, slow-query detection across every resource, and a working debug switch.
2. **Organization end-to-end** as the reference implementation, applying the Phase 2 table. It's the smallest of the three auth'd resources (`app/routers/organization/`, `app/services/organization/`, `app/repository/organization/`) and already has the split-package layout the others use.
3. **Review the actual log output** from a real create/patch/list/delete against the Phase 2 rules. Tune before replicating. Then write the settled pattern into `CLAUDE.md` and an `/add-resource-logging` skill.
4. **Patient and Practitioner** next — they're already the auth'd tier and share Organization's package layout.
5. **Remaining ~32 resources** opportunistically, or in one mechanical pass once the pattern is proven.

---

## Verification

- `uv run python -c "import app.main; print('OK')"` after each of 1.1–1.8.
- `uv run pytest tests/ -q` stays green throughout — this touches observability plumbing, not business logic. Same pass count as before the change is the regression bar.
- `curl -i localhost:8000/health` → response carries `X-Request-ID`; the log line for that request carries the **same** id.
- `curl -H 'X-Request-ID: test-abc-123' ...` → the log line shows `"request_id":"test-abc-123"`, not a fresh UUID. This is the gateway-propagation check.
- Flip `LOGGING__DEBUG_PAYLOADS=true` and re-run a `POST /organizations` → the payload appears at DEBUG, with any `redact`-listed field masked. Flip it back → payload gone, access line still present.
- Set `LOGGING__SLOW_QUERY_MS=1` → list endpoints emit `db.slow_query` warnings. Restore.
- Confirm no duplicate access lines (i.e. `uvicorn.access` is actually silenced) and that every emitted line is valid JSON: `uv run fastapi dev app/main.py 2>&1 | while read l; do echo "$l" | python -c 'import sys,json;json.loads(sys.stdin.read())'; done`.
- `/openapi.json` unaffected — no schema or route surface changes anywhere in this plan.
