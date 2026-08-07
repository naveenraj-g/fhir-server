# FHIR Server — Architecture & Agent Guide

## FHIR References

**This project targets FHIR R4. Always use R4 spec URLs.**

- R4 base: https://www.hl7.org/fhir/R4/
- Datatypes R4: https://www.hl7.org/fhir/R4/datatypes.html
- Resource index R4: https://www.hl7.org/fhir/R4/resourcelist.html

---

## Project Overview

FHIR R4-compliant REST API server built with FastAPI + PostgreSQL. Every endpoint supports dual-format responses: full FHIR R4 JSON (`application/fhir+json`) and simplified snake_case JSON (`application/json`), selected via the `Accept` header.

This is a pure CRUD core with no authentication of its own — it is never exposed directly to clients. A GraphQL gateway sits in front of it as the only externally-facing surface; the gateway validates JWTs and forwards `user_id`/`org_id`/`created_by`/`updated_by` explicitly as request fields. See "Multi-Tenancy & Ownership" below.

---

## Tech Stack

| Concern | Library |
|---|---|
| Web framework | FastAPI + Uvicorn |
| Database | PostgreSQL 15 (async via asyncpg) |
| ORM | SQLAlchemy 2.0+ (async) |
| Auth | None for ~32 resources — handled upstream by a GraphQL gateway. **Patient, Practitioner, and Organization are the exceptions**: `app/auth/` validates JWTs directly via `pyjwt` + JWKS, with flat RBAC scopes (see Multi-Tenancy & Ownership) |
| Sessions | Redis 7 (server-side) |
| DI container | dependency-injector |
| Config | pydantic-settings (.env) |
| Package manager | uv |
| Python | 3.12+ |

---

## Directory Layout

```
app/
├── core/           # config, database, logging, redis, content_negotiation, schema_utils
├── deps/           # resolve_<resource>() — load-by-public-ID-or-404, used as Depends(resolve_<resource>)
├── di/             # container.py, modules/<resource>.py, dependencies/<resource>.py
├── models/         # SQLAlchemy ORM — one package per resource + shared enums.py
├── fhir/mappers/   # per-resource packages: fhir.py (camelCase) + plain.py (snake_case) + __init__.py
│                   # fhir/datatypes.py — shared helpers (fhir_human_name, fhir_identifier, plain_name, etc.)
├── repository/     # <resource>_repository.py — all DB I/O
├── services/       # <resource>_service.py — thin orchestration
├── routers/        # <resource>.py + __init__.py (mounts all routers)
├── schemas/        # input.py + response.py (FHIR + plain) per resource, schemas/common/ for shared FHIR datatypes
└── errors/         # ApplicationError hierarchy, handlers → FHIR OperationOutcome
```

---

## Layered Architecture

```
Router → Service → Repository → ORM Model
```

- **Router**: validates body (Pydantic), reads `user_id`/`org_id`/`created_by` straight off the validated payload, calls service, calls `format_response()`
- **Service**: thin orchestration, hosts `_to_fhir()` / `_to_plain()` wrappers
- **Repository**: all DB I/O, session-per-operation, `_with_relationships()`, `_apply_list_filters()`
- **Model**: declarative async SQLAlchemy, internal `id` PK + public sequence-based `<resource>_id`

---

## Public vs. Internal IDs

| Column | Exposed? |
|---|---|
| `id` | Never — DB-internal PK only |
| `<resource>_id` | Yes — all APIs, FHIR references, starts at resource-specific sequence |

### Sequence allocation

| Resource | Start |
|---|---|
| Patient | 10000 |
| Encounter | 20000 |
| Practitioner | 30000 |
| Appointment | 40000 |
| QuestionnaireResponse | 60000 |
| Vitals | 70000 |
| ServiceRequest | 80000 |
| MedicationRequest | 90000 |
| Procedure | 100000 |
| DiagnosticReport | 110000 |
| Condition | 120000 |
| DeviceRequest | 130000 |
| PractitionerRole | 140000 |
| HealthcareService | 150000 |
| Observation | 160000 |
| Claim | 170000 |
| ClaimResponse | 180000 |
| Organization | 190000 |
| Schedule | 200000 |
| Invoice | 210000 |
| Slot | 220000 |
| Location | 230000 |
| Coverage | 240000 |
| Medication | 250000 |
| AllergyIntolerance | 260000 |
| Provenance | 270000 |
| Task | 280000 |
| CarePlan | 290000 |
| RelatedPerson | 300000 |
| Specimen | 310000 |
| DocumentReference | 320000 |
| Immunization | 330000 |
| AuditEvent | 340000 |
| EpisodeOfCare | 350000 |
| InsurancePlan | 360000 |

**Next available block: 370000.** Pick the next unused 10000-block for any new resource.

---

## Multi-Tenancy & Ownership

**This server has no authentication of its own — with three exceptions, see below.** It is a pure CRUD core — never exposed directly to clients — sitting behind a GraphQL gateway, which is the only externally-facing surface. For every resource except Patient, Practitioner, and Organization, the gateway validates the caller's JWT and resolves `sub` → `user_id` and the active-org claim → `org_id` itself, then forwards both as ordinary fields on every request. Nothing in this codebase (outside `app/auth/`) decodes a token, checks a JWKS endpoint, or reads `request.state.user`.

**Auth rollout status (in progress, Patient, Practitioner, and Organization so far):** All three validate JWTs directly — see `app/auth/` (JWKS-based verification via `pyjwt`'s `PyJWKClient`, flat `resource:action` RBAC scopes read off the JWT's `permissions` claim) and every route in `app/routers/patient/`, `app/routers/practitioner/`, and `app/routers/organization/`, gated with `require_permission("patient", <action>)` / `require_permission("practitioner", <action>)` / `require_permission("organization", <action>)` respectively. For all three resources: `created_by`/`updated_by` come from the verified JWT's `sub` (`actor.sub`); `org_id` comes from the verified JWT's `activeOrganizationId` (`actor.org_id`) — **neither is a request body field anymore**, `PatientCreateSchema`/`PatientPatchSchema`, `PractitionerCreateSchema`/`PractitionerPatchSchema`, and `OrganizationCreateSchema`/`OrganizationPatchSchema` (plus every one of Patient's and Practitioner's sub-resource Create/Patch schemas — Organization has none, see its own Standard Columns note) don't accept them at all. There is **no org-less/super-admin bypass**: a token with no `activeOrganizationId` claim is rejected outright (403) rather than being allowed through — every Patient/Practitioner/Organization operation requires an org-scoped actor. `create`/`create_full` reject a missing `actor.org_id`; `patch`/`patch_full`/`delete`/every sub-resource method 404 if the caller's org doesn't match the target resource's stored `org_id` (also 404, never 403, to avoid leaking whether the resource exists in another org) — enforced via a shared `get_<resource>_scoped()` helper on each service's core mixin plus a `<resource>_belongs_to_org()` repository check. `user_id` is unchanged for Patient and Practitioner — still a plain, gateway-forwarded input field on create, same as every other resource. **Organization is the one exception to that: it has no `user_id` at all** (dropped entirely — model column, schemas, mapper, repository/service/router — since an Organization is a shared tenant-level entity, not scoped to an individual end-user; see its own Standard Columns note). **All other ~32 resources are unaffected and follow the description below exactly as written.**

- Every row stores `user_id` and `org_id`; every `<Resource>CreateSchema`/`PatchSchema` declares them as plain input fields (see each schema's `json_schema_extra` example), and every router reads them straight off the validated payload (e.g. `payload.user_id`, `payload.org_id`) — never from a token. (Patient and Practitioner are exceptions: `user_id` still follows this, but `org_id`, like `created_by`/`updated_by`, comes from the verified token instead — see rollout status above. Organization is a further exception: no `user_id` at all.)
- `created_by`/`updated_by` are the same for every resource except Patient, Practitioner, and Organization: plain input fields set from whatever "acting user" value the gateway forwards, never derived locally.
- `resolve_<resource>()` deps (`app/deps/<resource>_deps.py`) only load the resource by public ID and raise 404 if missing — they do **not** enforce ownership. Tenant/ownership scoping happens entirely via `user_id`/`org_id` `WHERE` clauses in the repository's `list()`/`get_me()` queries. Used as `Depends(resolve_<resource>)` in route signatures.
- Keeping `user_id`/`org_id` on every resource (Organization aside) is deliberate: it gives the GraphQL gateway one uniform scoping contract across all other resource types, with no joins, and it's the only mechanism that works for resources with no patient/subject link at all (Location, HealthcareService, Appointment — whose `participant` list is polymorphic 0..* and may contain zero patients — etc.).

---

## Content Negotiation

`format_response()` / `format_paginated_response()` in `app/core/content_negotiation.py` dispatch on `Accept` header:
- `application/fhir+json` → FHIR R4 camelCase dict / Bundle
- `application/json` (or absent) → snake_case dict / `{total, limit, offset, data[]}`

Vitals only returns plain JSON via `JSONResponse` — no content negotiation.

---

## OpenAPI Spec = MCP Contract

The emitted OpenAPI spec is consumed by a FastMCP server that exposes every endpoint as an AI tool. **Drift breaks MCP callers silently.**

Rules:
- Every DB field must appear in the response schema
- Every accepted input field must appear in the create/patch schema
- Both `application/json` and `application/fhir+json` content types must be complete
- `inline_schema()` constants auto-update on import — verify at `/openapi.json` after changes
- Route/field summary strings matter — MCP uses them to explain tools to AI

---

## Full-Flow Checklist (Field Change)

When adding, renaming, or removing any field, walk every layer:

1. **ORM Model** — add/change Column, generate + apply Alembic migration
2. **CreateSchema** — add field + example value (include `user_id`/`org_id` in example)
3. **PatchSchema** — add field (all optional; skip immutable fields)
4. **Repository `create()`** — pass field to ORM constructor
5. **Repository `patch()`** — apply field when present in `model_dump(exclude_unset=True)`
6. **FHIR Mapper** — `to_fhir_*`: add camelCase key; `to_plain_*`: add snake_case key
7. **FHIR Response Schema** — add to both `FHIRXxxSchema` and `PlainXxxResponse`
8. **Verify `/openapi.json`** — field must appear in request body and both response content types

Removing a field: same order in reverse (mapper → schemas → repo → model).

---

## OpenAPI Response Schema Pattern

```python
# Module-level constants (computed once at import)
_SINGLE_200 = {200: {"content": {
    "application/json": {"schema": inline_schema(PlainXxxResponse.model_json_schema())},
    "application/fhir+json": {"schema": inline_schema(FHIRXxxSchema.model_json_schema())},
}}}
_SINGLE_201 = {201: _SINGLE_200[200]}
_LIST_200   = {200: {"content": {
    "application/json": {"schema": inline_schema(PaginatedXxxResponse.model_json_schema())},
    "application/fhir+json": {"schema": inline_schema(FHIRXxxBundle.model_json_schema())},
}}}
```

Never use `response_model=` — always inline `responses=` with `inline_schema()`.

---

## Repository Conventions

- **Session-per-operation**: `async with self.session_factory() as session:` in every method
- **Eager-load always**: wrap every query with `_with_relationships(stmt)` using `selectinload` for each relationship; never lazy-load in async context
- **Filter helper**: `_apply_list_filters(stmt, user_id, org_id, ...)` — conditional WHERE clauses; reused by both `list()` and `get_me()` (latter always has `user_id`/`org_id` set)
- **Count + rows in one session**: run count query and data query in the same `async with` block

---

## Schema Conventions

Three schema types per resource, all with `model_config = ConfigDict(extra="forbid")`:

| Schema | Purpose |
|---|---|
| `<Resource>CreateSchema` | Request body for POST; `json_schema_extra` example must include `user_id` + `org_id` |
| `<Resource>PatchSchema` | All fields optional; excludes immutable fields |
| `FHIR<Resource>Schema` / `Plain<Resource>Response` | Response — FHIR camelCase vs. snake_case |

Recursive schemas (e.g. QuestionnaireResponse items) must call `model_rebuild()` after class definition.

Once `input.py`/`response.py` grow large (many sub-resources), split each into a same-named package (`input/core.py` + one file per sub-resource + `input/__init__.py` re-exporting everything) — see the `/split-resource-package` skill. Patient, Practitioner, and Organization all do this; the module→package conversion is transparent to every existing import.

---

## FHIR Mapper Pattern

Each resource gets a **package** at `app/fhir/mappers/<resource>/`:

| File | Purpose |
|---|---|
| `fhir.py` | Per-child-model FHIR builder functions + `to_fhir_<resource>()` orchestrator |
| `plain.py` | Per-child-model plain/snake_case builder functions + `to_plain_<resource>()` orchestrator |
| `__init__.py` | Re-exports all public functions from both files |

**Shared standard-type helpers** live in `app/fhir/datatypes.py` and are imported by both `fhir.py` and the router:
- FHIR: `fhir_human_name`, `fhir_identifier`, `fhir_telecom`, `fhir_address`, `fhir_photo`, `fhir_communication`, `fhir_enum`, `fhir_split`
- Plain: `plain_name`, `plain_identifier`, `plain_telecom`, `plain_address`, `plain_photo`, `plain_communication`

**Resource-specific child-model helpers** are defined in `fhir.py`/`plain.py` (e.g. `fhir_contact`, `plain_qualification`) and exported from `__init__.py`. Sub-resource GET routes in the router **import and reuse** these same functions — zero inline dicts in either the mapper orchestrators or the router.

Rules:
- `to_fhir_<resource>`: `"id": str(model.<resource>_id)`, strip `None` at end with dict comprehension
- `to_plain_<resource>`: `"id": model.<resource>_id` as int
- References: stored as `(subject_type: Enum, subject_id: int)` → output as `"Patient/10001"` string via `fhir_enum()`
- `fhir_enum(v)` handles both SQLAlchemy Enum objects and plain strings transparently

---

## Standard Columns

Every resource row: `id` (PK), `<resource>_id` (sequence), `user_id`, `org_id`, `created_at`, `updated_at`, `created_by`, `updated_by`. **Organization is the one exception: it has no `user_id` column at all** — dropped end-to-end (model, migration, schemas, mapper, repository/service/router) since an Organization is a shared tenant-level entity, not scoped to an individual end-user, unlike every other resource.
- `created_by` / `updated_by` — plain input fields, set from whatever acting-user value the GraphQL gateway forwards; never derived from a token in this codebase, **except Patient, Practitioner, and Organization**, where all three come from the verified JWT's `sub` (see Multi-Tenancy & Ownership's "Auth rollout status")
- `org_id` / `user_id` are **tenant/ownership fields forwarded by the gateway**, not a reference to the FHIR Organization resource — **except Patient's, Practitioner's, and Organization's own `org_id`**, which comes from the verified JWT's `activeOrganizationId` instead (see Multi-Tenancy & Ownership's "Auth rollout status"); Patient's and Practitioner's `user_id` is unaffected, but Organization has no `user_id` field at all. (Note: on the Organization resource itself, this `org_id` tenant-scoping column is a distinct concept from the Organization *entity* being represented by the row — see `OrganizationCreateSchema`'s docstring.)

---

## Paginated Response

Plain JSON list:
```json
{ "total": 150, "limit": 50, "offset": 0, "data": [...] }
```
FHIR Bundle (`Accept: application/fhir+json`):
```json
{ "resourceType": "Bundle", "type": "searchset", "total": 150, "entry": [{"resource": {...}}] }
```
Pagination params: `limit: int = Query(50, ge=1, le=200)`, `offset: int = Query(0, ge=0)`.

---

## `/me` Route

Scopes list to the authenticated user's `sub` + `activeOrganizationId`. Supports same filters as `GET /`. **Declare `/me` before `/{id}`** in the router file — order matters in FastAPI.

---

## Error Handling

All errors return FHIR `OperationOutcome`. Handlers in `app/errors/handlers.py`:
- `ApplicationError` → 400/401/403/404/500
- `RequestValidationError` → 422 (Pydantic body validation)
- `HTTPException` → FastAPI standard
- `Exception` → 500 catch-all

---

## Logging & Observability

One JSON object per line (`app/core/logging.py`'s `JsonFormatter`), configured entirely from `configs/config.yaml`'s `logging:` block — see the Environment section.

### Two modes, driven by `logging.level`

- **INFO (default/production)** — the call chain and nothing more: one line per route handler, one per service method, one per repository method, plus the access line and the hand-placed business events. Enough to answer "what did this request actually do" without any detail to sift through.
- **DEBUG** — everything: the same chain plus call arguments, per-method `duration_ms`, result types, full path/query params and every SQL statement. Add `debug_payloads: true` for request bodies.

One `GET /patients/10001` at **INFO** — the call chain, names only:

```
[INFO] Retrieve a Patient resource by public patient_id   route.get_patient_by_id      patient_id
[INFO] PatientService.get_patient_scoped                  patient.service.get_patient_scoped
[INFO] PatientRepository.get_by_patient_id_in_org         patient.repository.get_by_patient_id_in_org
[INFO] GET /api/fhir/v1/patients/10001 -> 200             http.request   status, duration_ms, actor_*
```

The same request at **DEBUG** — same lines, now carrying `call_args`, plus a
completion line per method with `duration_ms` and the result type:

```
[INFO ] Retrieve a Patient resource by public patient_id
[INFO ] PatientService.get_patient_scoped                 call_args={patient_id, org_id}
[INFO ] PatientRepository.get_by_patient_id_in_org        call_args={patient_id, org_id}
[DEBUG] PatientRepository.get_by_patient_id_in_org ok     duration_ms, result
[DEBUG] PatientService.get_patient_scoped ok              duration_ms, result
[INFO ] GET /api/fhir/v1/patients/10001 -> 200
```

Plus `route.entered` (path/query params) and every SQL statement when
`sql_echo` is on.

### How each layer is wired

**Routes — explicit, one per handler.** Every one of the 86 handlers across the three resources carries its own `logger.info(...)` with `event: "route.<operation_id>"` plus its path identifiers. Written out in the handler body, not injected — you can see it when you open the file. Write handlers additionally call `log_payload(...)` right before the service call.

```python
async def get_organization(...):
    logger.info(
        "Retrieve an Organization resource by public organization_id",
        extra={"event": "route.get_organization_by_id", "organization_id": organization_id},
    )
```

**Services + repositories — `@trace_methods`.** The class decorator in `app/core/logging.py` makes every public async method announce itself: **one INFO line naming the call** (`PatientService.list_patients` — `component` + `method`, nothing else), and at DEBUG the same line carrying `call_args` plus a completion line with `duration_ms`/result. Applied to the six composed classes in `app/services/<res>/__init__.py` and `app/repository/<res>/__init__.py`; it walks the whole MRO, so methods on the per-sub-resource mixins are covered automatically and **a new mixin method needs no logging code of its own**. Underscore-prefixed methods (`_to_fhir`, `_apply_list_filters`) are skipped deliberately — they run per row and would bury the flow. At INFO the wrapper does one `isEnabledFor` check and calls straight through.

**Plus** `log_route_entry` in `app/main.py`, a router-level dependency that adds a DEBUG line with full path/query params for every mounted resource — including the ~32 that have no per-handler logging of their own.

When adding a route to one of these three resources, add the `logger.info` line by hand; when adding a service or repository method, do nothing.

### Correlation — and the one trap

`app/core/request_context.py` holds three ContextVars (`request_id`, `actor_user_id`, `actor_org_id`); the formatter injects whichever are set into every line.

**The actor keys are prefixed `actor_` deliberately.** Resource rows and request payloads carry their own `user_id`/`org_id` columns (see Standard Columns), so a bare `user_id` in a log line would be ambiguous — the caller, or the record being written? `actor_*` always means *who made this request*, taken from the verified JWT. Never emit bare `user_id`/`org_id` as a logging key. A repository has no access to `Request`, so this is the only way to correlate a repo line back to its request without touching hundreds of signatures.

**⚠️ ContextVars propagate DOWNWARD only.** Starlette's `BaseHTTPMiddleware` runs the downstream app in a child anyio task that *copies* the context at creation. So:

- `request_id`, set in the outermost middleware, reaches everything below it. ✅
- `actor_user_id`/`actor_org_id`, set in the route's dependency (inside that child task), are **invisible to any middleware above** — including the access log. ❌

That's why `bind_actor()` writes to **both** the ContextVars *and* `request.state` (backed by the shared `scope` dict, which is the same object in both directions), and why `AccessLogMiddleware` reads them via `get_request_actor(request)` rather than the ContextVars. If you add another middleware that needs request-scoped data set below it, use `request.state`, not a ContextVar.

### Layer table

| Layer | Always on (INFO/WARN) | DEBUG | `debug_payloads` | Never |
|---|---|---|---|---|
| Middleware | access line (`http.request`): method, path, status, `duration_ms`, `operation_id`, `actor_user_id`, `actor_org_id` | — | — | `Authorization` header |
| Auth | WARN on 401/403 + reason (`auth.failed`, `auth.permission_denied`); INFO on JWKS fetch | — | decoded claims | raw JWT |
| Router | `route.<operation_id>` + path ids — explicit `logger.info` in **every** handler | `route.entered` (params) | `log_payload(...)` of the validated schema | — |
| Service | every method call by name (`component`+`method`); outcomes `<res>.created`/`.updated`/`.deleted`; WARN `<res>.org_scope_miss` | `.ok`/`.error` + `duration_ms` + result | call args on the entry line | — |
| Repository | every method call by name (`component`+`method`); WARN `db.slow_query` | `.ok`/`.error` + `duration_ms`; `<res>.listed`, `.sublists_replaced` | call args, SQL (`sql_echo`) | bound SQL params |
| Errors | wired in `handlers.py` (`error.*` events) | — | request payload | stack traces to client |

### Conventions

- Structured data goes in `extra={...}`, never f-stringed into the message.
- Every line carries an `event` key: dotted, resource-first, past-tense — `organization.created`, `db.slow_query`, `auth.permission_denied`.
- Don't put `actor_user_id`/`actor_org_id` in `extra` — the formatter already injects them, and a colliding key is dropped. A *different* identity needs a different name (see `rate_limit_key` in `app/middleware/rate_limit.py`). Conversely, a resource's own `user_id`/`org_id` is fine to log under those bare names — that's exactly the distinction the `actor_` prefix buys.
- **Never call `inspect.signature()` / `get_type_hints()` on repository methods.** Under PEP 649 (Python 3.14) that evaluates annotations lazily, and `app/repository/<res>/core.py`'s method is named `list` while its own parameters are annotated `list[str]` — inside the class body `list` resolves to the method, so evaluation raises `TypeError: 'function' object is not subscriptable`. `trace_methods` reads parameter names from `fn.__code__.co_varnames` for exactly this reason. **This landmine is still live** for anything else that introspects those classes.
- **`extra` keys must not collide with `LogRecord` attributes** — `args`, `name`, `msg`, `module`, `filename`, `process`, … `logging.makeRecord()` raises `KeyError: Attempt to overwrite 'x' in LogRecord`. That's why the trace decorator emits `call_args`, not `args`. Full list: `_RESERVED_ATTRS` in `app/core/logging.py`.
- **⚠️ `debug_payloads` logs PHI.** `log_payload()` writes patient names, addresses, birth dates and identifiers. It no-ops unless the flag is on *and* the logger is DEBUG-enabled, so it's free in production — but it must never be enabled there. `logging.redact` masks obvious secrets; it is not a PHI safeguard.
- `app/core/database.py` instruments **every** query for all resources from one place. Never time queries per call site.
- **Uvicorn's own access log is off** (`logging.uvicorn_access: false`) — `app/middleware/access_log.py` already logs every request with more detail, and the `uvicorn.access` logger sets `propagate=False` with its own handler, so its line stays plain text even under `format: json` and breaks stream parsing. Flip the flag to see both effects.
- `logging.level` and `logging.format` are matched case-insensitively (`JSON`, `Debug`, … all work) — they're the two settings people hand-edit, and a `literal_error` at import time is a hostile failure mode.

Currently instrumented end-to-end: **Patient, Practitioner, Organization** — all 86 routes (explicit per-handler `logger.info`), all 88 service methods and all 95 repository methods (`@trace_methods`). The other ~32 resources get the global plumbing (access log, slow queries, errors, auth) but no flow trace; add it by applying `@trace_methods` to their service/repository classes.

---

## Dependency Injection

Pattern per resource: `di/modules/<resource>.py` (Factory for repo + service) → `di/dependencies/<resource>.py` (`@inject` wrapper returning service) → wired in `di/container.py`. See any existing module for the boilerplate.

---

## Environment

Config comes from three layers, precedence highest-to-lowest — see `app/core/config.py`'s `Settings.settings_customise_sources()`:

1. **Real env var** (e.g. exported in the shell, or set by an orchestrator)
2. **`.env`** — true per-environment secrets only:
   ```
   FHIR_DATABASE_URL=postgresql+asyncpg://user:password@localhost/fhir-server
   REDIS_URL=redis://localhost:6379

   # BetterAuth / IAM — used by app/auth/ to verify JWTs via JWKS (Patient, Practitioner, and Organization only, so far)
   IAM_JWKS_URL=http://localhost:5001/api/auth/jwks
   IAM_ISSUER=http://localhost:5001
   ```
3. **`configs/config.yaml`** — checked-in application-behavior config, not a secret (same spirit as `alembic.ini`):
   ```yaml
   logging:
     level: INFO
     format: json           # json | console (both matched case-insensitively)
     debug_payloads: false  # ⚠️ PHI — local dev only
     slow_query_ms: 500
     sql_echo: false
     uvicorn_access: false  # Uvicorn's own plaintext access line
     redact: [authorization, token, password, secret]

   rate_limit:
     backend: redis
     read_limit: 100
     write_limit: 20
     window_seconds: 60

   routes:
     enabled:
       - patient
       - practitioner
       - organization
   ```

`IAM_JWKS_URL`/`IAM_ISSUER` exist because Patient, Practitioner, and Organization now validate JWTs directly (see Multi-Tenancy & Ownership's "Auth rollout status") — same BetterAuth instance the `fhir-gql` gateway validates against. The other ~32 resources still don't authenticate; the upstream GraphQL gateway owns that for them.

`rate_limit.backend` selects `RateLimitMiddleware`'s (`app/middleware/rate_limit.py`) counting backend ("redis", coordinated across instances, or "memory", per-process only) — Redis is still required regardless, for sessions (`app/core/session.py`) and the `get_redis()` DI dependency. `rate_limit.read_limit`/`write_limit`/`window_seconds` are the actual per-window request caps — all four are wired straight into `app.add_middleware(RateLimitMiddleware, ...)` in `app/main.py`.

`logging.*` drives `app/core/logging.py`'s `setup_logging()`, `app/middleware/access_log.py`, and `app/core/database.py`'s query listeners — see the "Logging & Observability" section above. `YamlConfigSettingsSource` is constructed with `yaml_file_encoding="utf-8"` because it otherwise opens the file with the platform default (cp1252 on Windows), which fails on any non-ASCII byte in the committed config.

`routes.enabled` is the list consumed by `app/main.py`'s `mount_routers()` — see "Enabling/Disabling Resources" below.

Any nested field can still be overridden by an env var using `__` as the nesting delimiter, without touching the committed file — e.g. `RATE_LIMIT__BACKEND=memory` or `RATE_LIMIT__WRITE_LIMIT=7` (`model_config`'s `env_nested_delimiter="__"`).

There is no hand-rolled loader: `Settings` is a `pydantic_settings.BaseSettings`, so `configs/config.yaml` is wired in as one more `PydanticBaseSettingsSource` (pydantic-settings' built-in `YamlConfigSettingsSource`) in that precedence tuple. A future secrets-manager source (AWS Secrets Manager, SSM, etc.) would slot into the same tuple the same way — no changes needed anywhere that reads `settings.*`.

Dev server: `uv run fastapi dev app/main.py` — OpenAPI at `http://localhost:8000/docs`.

---

## FHIR DB Model Design

Use the `/fhir-db-model` skill (`.claude/commands/fhir-db-model.md`) for detailed rules on:
- Fetching R4 spec + datatypes before modeling
- Cardinality → storage mapping (0..1 flat, 0..* child table)
- CodeableConcept / Reference / choice-type flattening
- PostgreSQL enum creation + migration fixes
- Shared enum types (`organization_reference_type`, `subject_reference_type`)

**Key invariants:**
- R4 only — never `https://www.hl7.org/fhir/<resource>.html` (that's R5)
- `CodeableReference` does not exist in R4
- `organization_reference_type` PG type is shared — always `create_type=False`, never create/drop it again
- `encounter_reference_type` PG type is shared — always `create_type=False`, never create/drop it again
- All reference `_id` columns store the **internal `resource.id` PK**, never the public sequence ID. Add `ForeignKey("resource.id")`, `index=True`, and `lazy="selectin"` relationship. Mapper reads the public ID through the relationship.
- Alembic autogenerate enum values are correct (key = value convention); still replace `sa.Enum` with `postgresql.ENUM` pattern in migrations for proper create/drop handling

---

## Adding a New FHIR Resource

Use the `/new-fhir-resource` skill (`.claude/commands/new-fhir-resource.md`) for the complete 17-step checklist covering model → migration → schemas → mapper → repository → service → DI → router.

Two related skills, used opportunistically rather than as part of every new resource:
- `/split-resource-package` — once a resource's model/repository/service/router/schema file grows large (many sub-resources), split it into a per-sub-resource package. Patient, Practitioner, and Organization all do this across every layer.
- `/resource-auth-rollout` — only if explicitly asked to add direct JWT/RBAC auth to a resource (the Patient/Practitioner/Organization pattern). This is a rare, deliberate deviation from the default gateway-trusts-everything pattern, not something to apply by default.

---

## Enabling/Disabling Resources

Which resource routers get mounted under `/api/fhir/v1` is controlled entirely by **`configs/config.yaml`'s `routes.enabled` list** (repo root's `configs/` folder, committed — not a secret, same spirit as `alembic.ini`), not by editing source. Each router already carries its own `prefix=`/`tags=` (set at construction in the resource's own module/package, e.g. `router = APIRouter(prefix="/patients", tags=["Patients"])`) — `app/routers/__init__.py`'s `discover_routers()` introspects the package namespace for every submodule exposing a module-level `router: APIRouter` and returns a `{name: router}` dict, so there's no separate prefix/tag table to keep in sync. `app/main.py`'s `mount_routers(app)` mounts only the names present in `routes.enabled`, and is called from inside the FastAPI `lifespan` handler at actual ASGI startup (not at module-import time) — mirrors txtai's `api/application.py::lifespan()` pattern. Toggling a resource on/off is a one-line YAML edit + restart — no code change, no redeploy of different source.

Every router is still always imported in `app/routers/__init__.py` via `from . import <name> as <name>` (cheap, no side effects, and required for `discover_routers()`'s introspection to see it) — only *mounting* is conditional. Adding a new resource: give its `APIRouter()` a `prefix=`/`tags=`, add the `from . import <name> as <name>` re-export + `__all__` entry, and append its name to `configs/config.yaml`'s `routes.enabled` list once it's ready to expose, per Step 17 of `/new-fhir-resource`.

`vitals_router`/`terminology_router` are mounted separately in `app/main.py` under their own prefixes (`/api/v1/vitals`, `/api/v1/terminology`) at module level and aren't covered by `routes.enabled`.

---

## Sub-Resource GET + DELETE Endpoints

Use the `/sub-resource-endpoints` skill (`.claude/commands/sub-resource-endpoints.md`) for the complete pattern covering schemas, repository, service, and router for `GET /{id}/<sub>` and `DELETE /{id}/<sub>/{sub_id}` routes.

Key invariants (full details in the skill):
- Document **both** `application/json` and `application/fhir+json` in `_SUBRES_*_200` constants — MCP needs both
- Every list item must include `id` — callers need it for DELETE
- Every route must have `operation_id`, `summary`, `description`, `responses=` — MCP uses all of these

---

## Common Pitfalls

- **Never `response_model=`** — use inline `responses=` + `inline_schema()`
- **`/me` before `/{id}`** — route order matters
- **`status` param shadowing** — rename to `<res>_status` with `alias="status"`
- **Always eager-load** — `_with_relationships()` on every serialized query
- **Session-per-operation** — never hold a session across multiple repository calls
- **`model_dump(exclude_unset=True)`** in PATCH to only apply provided fields
- **`user_id`/`org_id` in `json_schema_extra` example** — required on every CreateSchema
- **`inline_schema()` at module level** — not inside route handlers
- **Sub-resource GET + DELETE** — use `/sub-resource-endpoints` skill; every route needs `operation_id`, `summary`, `description`, `responses=` with both content types
- **Verify `/openapi.json`** after any schema change before marking task done
