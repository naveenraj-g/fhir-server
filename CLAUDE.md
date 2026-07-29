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
| Auth | None for ~34 resources — handled upstream by a GraphQL gateway. **Patient is the exception**: `app/auth/` validates JWTs directly via `pyjwt` + JWKS, with flat RBAC scopes (see Multi-Tenancy & Ownership) |
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
├── schemas/        # input schemas + schemas/fhir/ (FHIR + plain response schemas)
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

**This server has no authentication of its own — with one exception, see below.** It is a pure CRUD core — never exposed directly to clients — sitting behind a GraphQL gateway, which is the only externally-facing surface. For every resource except Patient, the gateway validates the caller's JWT and resolves `sub` → `user_id` and the active-org claim → `org_id` itself, then forwards both as ordinary fields on every request. Nothing in this codebase (outside `app/auth/`) decodes a token, checks a JWKS endpoint, or reads `request.state.user`.

**Auth rollout status (in progress, Patient-first):** Patient now validates JWTs directly — see `app/auth/` (JWKS-based verification via `pyjwt`'s `PyJWKClient`, flat `resource:action` RBAC scopes read off the JWT's `permissions` claim) and every route in `app/routers/patient.py`, gated with `require_permission("patient", <action>)`. For Patient specifically: `created_by`/`updated_by` come from the verified JWT's `sub` (`actor.sub`); `org_id` comes from the verified JWT's `activeOrganizationId` (`actor.org_id`) — **neither is a request body field anymore**, `PatientCreateSchema`/`PatientPatchSchema` don't accept them at all. There is **no org-less/super-admin bypass**: a token with no `activeOrganizationId` claim is rejected outright (403) rather than being allowed through — every Patient operation requires an org-scoped actor. `create`/`create_full` reject a missing `actor.org_id`; `patch`/`patch_full`/`delete` 404 if the caller's org doesn't match the target patient's stored `org_id` (also 404, never 403, to avoid leaking whether the patient exists in another org). `user_id` alone is unchanged — still a plain, gateway-forwarded input field on create, same as every other resource. **All other ~34 resources are unaffected and follow the description below exactly as written.**

- Every row stores `user_id` and `org_id`; every `<Resource>CreateSchema`/`PatchSchema` declares them as plain input fields (see each schema's `json_schema_extra` example), and every router reads them straight off the validated payload (e.g. `payload.user_id`, `payload.org_id`) — never from a token. (Patient is the one exception: `user_id` still follows this, but `org_id`, like `created_by`/`updated_by`, comes from the verified token instead — see rollout status above.)
- `created_by`/`updated_by` are the same for every resource except Patient: plain input fields set from whatever "acting user" value the gateway forwards, never derived locally.
- `resolve_<resource>()` deps (`app/deps/<resource>_deps.py`) only load the resource by public ID and raise 404 if missing — they do **not** enforce ownership. Tenant/ownership scoping happens entirely via `user_id`/`org_id` `WHERE` clauses in the repository's `list()`/`get_me()` queries. Used as `Depends(resolve_<resource>)` in route signatures.
- Keeping `user_id`/`org_id` on every resource (not just Patient/Practitioner) is deliberate: it gives the GraphQL gateway one uniform scoping contract across all ~35 resource types, with no joins, and it's the only mechanism that works for resources with no patient/subject link at all (Organization, Location, HealthcareService, Appointment — whose `participant` list is polymorphic 0..* and may contain zero patients — etc.).

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

Every resource row: `id` (PK), `<resource>_id` (sequence), `user_id`, `org_id`, `created_at`, `updated_at`, `created_by`, `updated_by`.
- `created_by` / `updated_by` — plain input fields, set from whatever acting-user value the GraphQL gateway forwards; never derived from a token in this codebase, **except Patient**, where both come from the verified JWT's `sub` (see Multi-Tenancy & Ownership's "Auth rollout status")
- `org_id` / `user_id` are **tenant/ownership fields forwarded by the gateway**, not FHIR Organization references — **except Patient's `org_id`**, which comes from the verified JWT's `activeOrganizationId` instead (see Multi-Tenancy & Ownership's "Auth rollout status"); Patient's `user_id` is unaffected

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

## Dependency Injection

Pattern per resource: `di/modules/<resource>.py` (Factory for repo + service) → `di/dependencies/<resource>.py` (`@inject` wrapper returning service) → wired in `di/container.py`. See any existing module for the boilerplate.

---

## Environment

```
FHIR_DATABASE_URL=postgresql+asyncpg://user:password@localhost/fhir-server
REDIS_URL=redis://localhost:6379

# BetterAuth / IAM — used by app/auth/ to verify JWTs via JWKS (Patient only, so far)
IAM_JWKS_URL=http://localhost:5001/api/auth/jwks
IAM_ISSUER=http://localhost:5001
```

`IAM_JWKS_URL`/`IAM_ISSUER` exist because Patient now validates JWTs directly (see Multi-Tenancy & Ownership's "Auth rollout status") — same BetterAuth instance the `fhir-gql` gateway validates against. The other ~34 resources still don't authenticate; the upstream GraphQL gateway owns that for them.

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
