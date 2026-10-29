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
| Auth | None for ~24 resources — handled upstream by a GraphQL gateway. **Patient, Practitioner, Organization, Location, HealthcareService, PractitionerRole, Schedule, Slot, Appointment, AppointmentResponse, Encounter, and Questionnaire are the exceptions**: `app/auth/` validates JWTs directly via `pyjwt` + JWKS, with flat RBAC scopes (see Multi-Tenancy & Ownership). Questionnaire keeps `user_id` like Practitioner — see Standard Columns |
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
| AppointmentResponse | 370000 |
| Questionnaire | 380000 |

**Next available block: 390000.** Pick the next unused 10000-block for any new resource.

---

## Multi-Tenancy & Ownership

**This server has no *fine-grained* authentication of its own — with twelve exceptions, see below.** It is a pure CRUD core — never exposed directly to clients — sitting behind a GraphQL gateway, which is the only externally-facing surface. For every resource except Patient, Practitioner, Organization, Location, HealthcareService, PractitionerRole, Schedule, Slot, Appointment, AppointmentResponse, Encounter, and Questionnaire, the gateway validates the caller's JWT and resolves `sub` → `user_id` and the active-org claim → `org_id` itself, then forwards both as ordinary fields on every request. Nothing in this codebase (outside `app/auth/`) decodes a token *for its own RBAC purposes*, checks a JWKS endpoint of its own, or reads `request.state.user` to gate a specific permission.

**⚠️ This is narrower than it may read at first — a bearer JWT is still required on literally every `/api/fhir/v1` route, auth-rollout or not.** `app/main.py`'s `mount_routers()` wires `dependencies=[Depends(get_current_user), Depends(log_route_entry)]` onto the *entire* `api_router` the mounted resources share — `get_current_user` (JWKS signature/`iss`/`aud`/`exp` verification, see `app/auth/dependencies.py`) runs once for every request regardless of which resource it's for, same as it always has; only `require_permission(...)` on top of that is specific to the twelve rollout resources. A default-pattern resource (any not-yet-built one) still 401s on a missing/invalid/expired token — it just does no RBAC/ownership check beyond that, and reads `tenant_id`/`user_id`/`created_by`/`updated_by` as plain request fields instead of from the verified claims. Confirmed building Questionnaire (before its own later auth rollout): a request with no `Authorization` header 401s before ever reaching its router, even when the router itself has no `require_permission` anywhere in it.

**Auth rollout status (in progress, Patient, Practitioner, Organization, Location, HealthcareService, PractitionerRole, Schedule, Slot, Appointment, AppointmentResponse, Encounter, and Questionnaire so far):** All twelve validate JWTs directly — see `app/auth/` (JWKS-based verification via `pyjwt`'s `PyJWKClient`, flat `resource:action` RBAC scopes read off the JWT's `permissions` claim) and every route in `app/routers/patient/`, `app/routers/practitioner/`, `app/routers/organization/`, `app/routers/location/`, `app/routers/healthcare_service/`, `app/routers/practitioner_role/`, `app/routers/schedule/`, `app/routers/slot/`, `app/routers/appointment/`, `app/routers/appointment_response/`, `app/routers/encounter/`, and `app/routers/questionnaire/`, gated with `require_permission("<resource>", <action>)`. For all twelve resources: `created_by`/`updated_by` come from the verified JWT's `sub` (`actor.sub`); `org_id` comes from the verified JWT's `activeOrganizationId` (`actor.org_id`) — **neither is a request body field anymore**, `PatientCreateSchema`/`PatientPatchSchema`, `PractitionerCreateSchema`/`PractitionerPatchSchema`, `OrganizationCreateSchema`/`OrganizationPatchSchema`, `LocationCreateSchema`/`LocationPatchSchema`, `HealthcareServiceCreateSchema`/`HealthcareServicePatchSchema`, `PractitionerRoleCreateSchema`/`PractitionerRolePatchSchema`, `ScheduleCreateSchema`/`SchedulePatchSchema`, `SlotCreateSchema`/`SlotPatchSchema`, `AppointmentCreateSchema`/`AppointmentPatchSchema`, `AppointmentResponseCreateSchema`/`AppointmentResponsePatchSchema`, `EncounterCreateSchema`/`EncounterPatchSchema`, and `QuestionnaireCreateSchema`/`QuestionnairePatchSchema` (plus every one of Patient's and Practitioner's sub-resource Create/Patch schemas — Organization, Location, HealthcareService, PractitionerRole, Schedule, Slot, Appointment, AppointmentResponse, Encounter, and Questionnaire have none, see their Standard Columns note) don't accept them at all. There is **no org-less/super-admin bypass**: a token with no `activeOrganizationId` claim is rejected outright (403) rather than being allowed through — every Patient/Practitioner/Organization/Location/HealthcareService/PractitionerRole/Schedule/Slot/Appointment/AppointmentResponse/Encounter/Questionnaire operation requires an org-scoped actor. `create`/`create_full` reject a missing `actor.org_id`; `patch`/`patch_full`/`delete`/every sub-resource method 404 if the caller's org doesn't match the target resource's stored `org_id` (also 404, never 403, to avoid leaking whether the resource exists in another org) — enforced via a shared `get_<resource>_scoped()` helper on each service's core mixin plus a `<resource>_belongs_to_org()` repository check. `user_id` is unchanged for Patient, Practitioner, and Questionnaire — still a plain, gateway-forwarded input field on create, same as every other resource. **Organization, Location, HealthcareService, PractitionerRole, Schedule, Slot, Appointment, AppointmentResponse, and Encounter are the exceptions to that: none of the nine has a `user_id` at all** (dropped entirely — model column, schemas, mapper, repository/service/router — since all nine are shared tenant-level entities, not scoped to an individual end-user; see their Standard Columns note). **All other ~23 resources are unaffected and follow the description below exactly as written.**

- Every row stores `user_id` and `org_id`; every `<Resource>CreateSchema`/`PatchSchema` declares them as plain input fields (see each schema's `json_schema_extra` example), and every router reads them straight off the validated payload (e.g. `payload.user_id`, `payload.org_id`) — never from a token. (Patient, Practitioner, and Questionnaire are exceptions: `user_id` still follows this, but `org_id`, like `created_by`/`updated_by`, comes from the verified token instead — see rollout status above. Organization, Location, HealthcareService, PractitionerRole, Schedule, Slot, Appointment, AppointmentResponse, and Encounter are further exceptions: no `user_id` at all.)
- `created_by`/`updated_by` are the same for every resource except Patient, Practitioner, Organization, Location, HealthcareService, PractitionerRole, Schedule, Slot, Appointment, AppointmentResponse, Encounter, and Questionnaire: plain input fields set from whatever "acting user" value the gateway forwards, never derived locally.
- `resolve_<resource>()` deps (`app/deps/<resource>_deps.py`) only load the resource by public ID and raise 404 if missing — they do **not** enforce ownership. Tenant/ownership scoping happens entirely via `user_id`/`org_id` `WHERE` clauses in the repository's `list()`/`get_me()` queries. Used as `Depends(resolve_<resource>)` in route signatures.
- Keeping `user_id`/`org_id` on every resource (Organization/Location/HealthcareService/PractitionerRole/Schedule/Slot/Appointment aside) is deliberate: it gives the GraphQL gateway one uniform scoping contract across all other resource types, with no joins, and it's the only mechanism that works for resources with no patient/subject link at all (Encounter — whose `subject` may be a Group, not a Patient — etc.).

---

## Content Negotiation

`format_response()` / `format_paginated_response()` in `app/core/content_negotiation.py` dispatch on `Accept` header:
- `application/fhir+json` → FHIR R4 camelCase dict / Bundle
- `application/json` (or absent) → snake_case dict / `{total, limit, offset, data[]}`

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
7. **`payload.py`** — add the same camelCase key to both `payload_to_fhir_<resource>()` (CREATE) and `patch_fragment_to_fhir_<resource>()` (PATCH, plus its field-group membership set if the new field is part of a flattened group) — see "Base R4 Validation" below. Easy to forget since it's a third, parallel copy of the same shape `to_fhir_*` already has — forgetting it means the new field is silently never validated pre-write.
8. **FHIR Response Schema** — add to both `FHIRXxxSchema` and `PlainXxxResponse`
9. **Verify `/openapi.json`** — field must appear in request body and both response content types

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

Once `input.py`/`response.py` grow large (many sub-resources), split each into a same-named package (`input/core.py` + one file per sub-resource + `input/__init__.py` re-exporting everything) — see the `/split-resource-package` skill. Patient, Practitioner, Organization, Location, HealthcareService, PractitionerRole, Schedule, and Slot all do this; the module→package conversion is transparent to every existing import. Appointment deliberately stays flat (`input.py`/`response.py`, no package) despite being the largest resource yet — splitting is optional ("once it grows large"), not mandatory, and a flat file was still manageable here.

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

### Base R4 Validation — mandatory for every resource

Every resource's `create_<resource>()`/`patch_<resource>()` service methods validate the request **before** writing to the DB — not just Pydantic's own field-level checks, but the *real* FHIR R4 structure (via `app.fhir.validation.validate_resource()`, see below). This is mandatory, not opportunistic — Organization, Location, HealthcareService, and Practitioner all do it; a new resource's `/new-fhir-resource` build is not complete without it.

**`payload.py` — the third mapper file.** `app/fhir/mappers/<resource>/` gets a third file alongside `fhir.py`/`plain.py`:

| File | Purpose |
|---|---|
| `fhir.py` | ORM model (post-insert) → FHIR camelCase dict, for GET responses |
| `plain.py` | ORM model (post-insert) → plain snake_case dict, for GET responses |
| `payload.py` | **Validated Pydantic input schema** (pre-insert) → FHIR camelCase dict, for pre-write validation |

`payload.py` is `fhir.py`'s mirror image, written field-for-field parallel to it — same CodeableConcept/coding-list/ContactPoint/Address builders, same flattened-Reference pattern — but reading off `<Resource>CreateSchema`/`<Resource>PatchSchema` instead of the ORM model. The two can't fully share code: a Reference field on the input schema only has the raw `{prefix}` string the caller submitted (no resolved `{prefix}_type`/`{prefix}_id` — that only exists after `RESOURCE_REGISTRY`'s existence check at write time), so `payload.py`'s own `_reference_from_payload(obj, prefix)` reads `getattr(obj, prefix)` directly rather than `{prefix}_type`/`{prefix}_id`.

It exports two orchestrators:
- `payload_to_fhir_<resource>(create_schema) -> dict` — full-resource conversion for CREATE; every field is considered present (a create payload is the resource's entire initial state).
- `patch_fragment_to_fhir_<resource>(patch_schema) -> tuple[dict, set[str]]` — tri-state conversion for PATCH, using `payload.model_fields_set` (the same source of truth the repository's own `model_dump(exclude_unset=True)` uses): returns only the FHIR keys the request actually touched, plus that same key set. A touched key absent from the fragment means "clear it" (an explicit null, or an empty-list sub-resource replacement); an untouched key means "leave it alone."

**`merge_patch_fragment(existing, fragment, touched)`** (`app.fhir.datatypes` — shared, not per-resource: it has zero resource-specific logic) shallow-merges a patch fragment onto the resource's current full FHIR representation (`to_fhir_<resource>(existing_row)`): drops every touched key from `existing` first, then overlays `fragment` on top. This is what makes PATCH validation possible at all — a partial payload can't be meaningfully validated on its own, so the service builds "what the resource would look like after this patch" and validates *that*.

**Service wiring** — every `create_<resource>()`/`patch_<resource>()` does this (see `app/services/organization/core.py` for the original, or any of the other three for the identical copy):

```python
# create_<resource>()
await self._validate_base_r4(payload_to_fhir_<resource>(payload), org_id)
<resource> = await self.repository.create_full(payload, org_id, created_by)

# patch_<resource>() — needs the current full row, not just an existence check
existing = await self.repository.get_by_<resource>_id_in_org(<resource>_id, org_id)
if not existing: raise NotFoundError(...)
fragment, touched = patch_fragment_to_fhir_<resource>(payload)
merged = merge_patch_fragment(to_fhir_<resource>(existing), fragment, touched)
await self._validate_base_r4(merged, org_id)
updated = await self.repository.patch_full(<resource>_id, payload, updated_by)
```

Each service also has its own `_validate_base_r4` static method — a thin, identical-everywhere wrapper (just the resource-type string literal changes):

```python
@staticmethod
async def _validate_base_r4(fhir_resource: dict, org_id: str | None = None) -> None:
    errors = await validate_resource("<Resource>", fhir_resource, org_id=org_id)
    if errors:
        logger.warning("<Resource> failed base R4 validation", extra={"event": "<resource>.base_r4_invalid", "errors": errors})
        raise FhirValidationError(errors)
```

`validate_resource()` (`app/fhir/validation/dispatch.py`) is already fully resource-agnostic — it takes `resource_type` as a plain string and dispatches to whichever backend `settings.fhir_validation.backend` selects (`native`: this project's own structural JSON-Schema check against HL7's published `fhir.schema.json`, no profile concept; `java_validator`: the HL7 Java validator sidecar, which also walks the base → country → organization profile chain and enforces real terminology bindings) — nothing resource-specific needs to be built there. It also runs every `fhir_resource` dict through `jsonable_encoder()` before validating, since a payload mapper's output can carry `Decimal`/`date`/`Enum` values a persisted ORM row never would (e.g. `Location.position`'s `Decimal` longitude/latitude) — this keeps "what gets validated" and "what gets shipped" (`format_response()` applies the same encoder) from ever drifting apart, and avoids the java_validator sidecar's own httpx POST choking on a type `json.dumps` was never going to accept.

**⚠️ Known `java_validator` gotcha — don't pick test fixture codes that trigger a live terminology lookup.** Some CodeableConcept/Coding fields carry a real HL7 binding that makes the sidecar attempt to verify the code against an *external* ValueSet — e.g. any `Coding.system = "urn:ietf:bcp:47"` (language codes) triggers a check against the full "All Languages" ValueSet (`http://hl7.org/fhir/ValueSet/languages`), and `Attachment.contentType` is checked against the full IANA MimeType ValueSet via a remote `tx.fhir.org` cache lookup. In a sandboxed/offline dev environment these can hang for minutes (confirmed via the sidecar's own container logs: `Operation took too long - longer than 60000ms ... codeInValueSet: urn:ietf:bcp:47#en`, 180s+) instead of failing fast. **When writing a test fixture:** omit `system`/`contentType` on fields like these (they're legitimately optional per spec) rather than supplying a real-world value, unless you specifically intend to test that lookup. `http://example.org/*` systems are a separate, *fast*-reject gotcha (the sidecar explicitly blocks example-domain URLs with a quick "Example URLs are not allowed in this context" error) — use this project's own `https://fhir-server.dev/fhir/identifier-system/<name>` convention instead.

### Conformance testing the FHIR half

`tests/conformance/` validates `to_fhir_<resource>()` output against **`google-fhir-r4`** (dev group only — nothing in `app/` imports it; FHIR is output-only here, so there is nothing to validate at runtime). It carries HL7's published R4 StructureDefinitions as protobuf, so it is an *independent* oracle: the rest of the suite asserts what we believe the spec says, and if we misread it those assertions encode the same misreading and pass.

Location (`test_location_fhir.py`, 24 shapes), HealthcareService (`test_healthcare_service_fhir.py`, 35 shapes), PractitionerRole (`test_practitioner_role_fhir.py`, 25 shapes), Schedule (`test_schedule_fhir.py`, 23 shapes), Slot (`test_slot_fhir.py`, 18 shapes), Patient (`test_patient_fhir.py`, 35 shapes), Practitioner (`test_practitioner_fhir.py`, 23 shapes), and Organization (`test_organization_fhir.py`, 16 shapes) are done; the other resources are not yet covered.

- Feed it **JSON text**, not the mapper dict — `json_fhir_object_to_proto` rejects a Python `float` outright, since a FHIR `decimal` carries precision a float has already lost. `assert_valid()` in `tests/conformance/support.py` goes through `jsonable_encoder` + `json.dumps`, which is also exactly what `format_response()` ships.
- Each file ends with `test_validator_rejects_invalid_fhir` — deliberately broken payloads that must fail. Without it, a version bump that quietly breaks validation would leave every conformance test passing while checking nothing.
- It catches wrong key names, wrong nesting, bad codes against required bindings, and malformed primitives. It does **not** catch semantics (mapping `address_city` into `state` is still valid FHIR), extensible bindings (`Location.type` codes aren't policed), or a single-element array where the spec says 0..1.
- A failure does not automatically mean the mapper is wrong — it can also mean the model lets in a value the spec forbids (fix upstream, possibly a migration), or that the oracle is over-strict (document and skip). Triage before changing anything, and remember a mapper change has to move in lockstep with the `FHIR<Resource>Schema` response model.

---

## Standard Columns

Every resource row: `id` (PK), `<resource>_id` (sequence), `user_id`, `org_id`, `created_at`, `updated_at`, `created_by`, `updated_by`. **Organization, Location, HealthcareService, PractitionerRole, Schedule, Slot, Appointment, AppointmentResponse, and Encounter are the nine exceptions: none has a `user_id` column at all** — dropped end-to-end (model, migration, schemas, mapper, repository/service/router) since an Organization, a physical Location, a HealthcareService, a PractitionerRole, a Schedule, a Slot, an Appointment, an AppointmentResponse, and an Encounter are all shared tenant-level entities, not scoped to an individual end-user, unlike every other resource.

Every `id` and every sub-resource table's `id` is **`BigInteger`**, as is every `<resource>_id` sequence column, every sub-resource FK back to its parent, and every flattened cross-resource reference `_id`. `org_id`/`user_id` are `String` tenant fields and are not part of that rule.
- `created_by` / `updated_by` — plain input fields, set from whatever acting-user value the GraphQL gateway forwards; never derived from a token in this codebase, **except Patient, Practitioner, Organization, Location, HealthcareService, PractitionerRole, Schedule, Slot, Appointment, AppointmentResponse, Encounter, and Questionnaire**, where all twelve come from the verified JWT's `sub` (see Multi-Tenancy & Ownership's "Auth rollout status")
- `org_id` / `user_id` are **tenant/ownership fields forwarded by the gateway**, not a reference to the FHIR Organization resource — **except Patient's, Practitioner's, Organization's, HealthcareService's, PractitionerRole's, Schedule's, Slot's, Appointment's, AppointmentResponse's, Encounter's, and Questionnaire's own `org_id`**, which comes from the verified JWT's `activeOrganizationId` instead (see Multi-Tenancy & Ownership's "Auth rollout status"); Patient's, Practitioner's, and Questionnaire's `user_id` is unaffected, but Organization, Location, HealthcareService, PractitionerRole, Schedule, Slot, Appointment, AppointmentResponse, and Encounter have no `user_id` field at all. (Note: on the Organization resource itself, this `org_id` tenant-scoping column is a distinct concept from the Organization *entity* being represented by the row — see `OrganizationCreateSchema`'s docstring.)

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

**Routes — explicit, one per handler.** Every one of the 111 handlers across the eight resources carries its own `logger.info(...)` with `event: "route.<operation_id>"` plus its path identifiers. Written out in the handler body, not injected — you can see it when you open the file. Write handlers additionally call `log_payload(...)` right before the service call.

```python
async def get_organization(...):
    logger.info(
        "Retrieve an Organization resource by public organization_id",
        extra={"event": "route.get_organization_by_id", "organization_id": organization_id},
    )
```

**Services + repositories — `@trace_methods`.** The class decorator in `app/core/logging.py` makes every public async method announce itself: **one INFO line naming the call** (`PatientService.list_patients` — `component` + `method`, nothing else), and at DEBUG the same line carrying `call_args` plus a completion line with `duration_ms`/result. Applied to the eight composed classes in `app/services/<res>/__init__.py` and `app/repository/<res>/__init__.py`; it walks the whole MRO, so methods on the per-sub-resource mixins are covered automatically and **a new mixin method needs no logging code of its own**. Underscore-prefixed methods (`_to_fhir`, `_apply_list_filters`) are skipped deliberately — they run per row and would bury the flow. At INFO the wrapper does one `isEnabledFor` check and calls straight through.

**Plus** `log_route_entry` in `app/main.py`, a router-level dependency that adds a DEBUG line with full path/query params for every mounted resource — including the ~29 that have no per-handler logging of their own.

When adding a route to one of these eight resources, add the `logger.info` line by hand; when adding a service or repository method, do nothing.

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

Currently instrumented end-to-end: **Patient, Practitioner, Organization, Location, HealthcareService, PractitionerRole, Schedule, Slot, Appointment, AppointmentResponse, Encounter, Questionnaire, QuestionnaireResponse, ServiceRequest, MedicationRequest, Observation, DiagnosticReport** — all 162 routes (explicit per-handler `logger.info`), all 164 service methods and all 188 repository methods (`@trace_methods`). QuestionnaireResponse, ServiceRequest, MedicationRequest, Observation, and DiagnosticReport all get this same treatment despite being default/non-auth-rollout resources — logging instrumentation and the auth-rollout decision are independent (see "Adding a New FHIR Resource" below). The other ~19 resources get the global plumbing (access log, slow queries, errors, auth) but no flow trace; add it by applying `@trace_methods` to their service/repository classes.

---

## Dependency Injection

Pattern per resource: `di/modules/<resource>.py` (Factory for repo + service) → `di/dependencies/<resource>.py` (`@inject` wrapper returning service) → wired in `di/container.py`. See any existing module for the boilerplate.

---

## Environment

Config comes from four sources across three precedence tiers, highest-to-lowest — see `app/core/config.py`'s `Settings.settings_customise_sources()`:

1. **Real env var** (e.g. exported in the shell, or set by an orchestrator)
2. **`.env`** — true per-environment secrets only:
   ```
   FHIR_DATABASE_URL=postgresql+asyncpg://user:password@localhost/fhir-server
   REDIS_URL=redis://localhost:6379

   # BetterAuth / IAM — used by app/auth/ to verify JWTs via JWKS (Patient, Practitioner, Organization, Location, HealthcareService, PractitionerRole, Schedule, Slot, Appointment, AppointmentResponse, Encounter, and Questionnaire only, so far)
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

   redis:
     enabled: true   # global switch — see below

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
4. **`configs/cache.yaml`** — a sibling file, same precedence tier as `configs/config.yaml` (not a fallback chain between the two — they never share a top-level key), holding only settings for things that are genuinely a *cache* (something stored to avoid a re-fetch, with an eviction concept):
   ```yaml
   fhir_profile_cache:
     backend: redis
   ```

`IAM_JWKS_URL`/`IAM_ISSUER` exist because Patient, Practitioner, Organization, Location, HealthcareService, PractitionerRole, Schedule, Slot, Appointment, AppointmentResponse, Encounter, and Questionnaire now validate JWTs directly (see Multi-Tenancy & Ownership's "Auth rollout status") — same BetterAuth instance the `fhir-gql` gateway validates against. The other ~23 resources still don't authenticate; the upstream GraphQL gateway owns that for them.

`redis.enabled` and `rate_limit` both live in `config.yaml`, not `cache.yaml`, deliberately: neither is a caching-feature setting. Redis isn't only used for caching here — it also backs sessions (`app/core/session.py`) and the `get_redis()` DI dependency — so whether it's available at all is an infra-level decision. `rate_limit` is Redis-backed too, but it isn't a cache either — it's a shared sliding-window counter enforcing a request quota, not something stored to avoid re-fetching it. `redis.enabled` is still a global on/off switch: `false` forces every Redis-backed dependent (`rate_limit.backend` here, `fhir_profile_cache.backend` in `cache.yaml`) to its non-Redis fallback regardless of what's written under that dependent — see `Settings._apply_redis_switch()`. `rate_limit.backend` selects `RateLimitMiddleware`'s (`app/middleware/rate_limit.py`) counting backend ("redis", coordinated across instances, or "memory", per-process only). `rate_limit.read_limit`/`write_limit`/`window_seconds` are the actual per-window request caps — all four are wired straight into `app.add_middleware(RateLimitMiddleware, ...)` in `app/main.py`. `fhir_profile_cache.backend` is for caching `fhir_profile` DB rows (base + country layers) read by the FHIR validation dispatch path — base profiles are never invalidated (no admin write path exists for them), country profiles will need an evict-on-write once one does.

`logging.*` drives `app/core/logging.py`'s `setup_logging()`, `app/middleware/access_log.py`, and `app/core/database.py`'s query listeners — see the "Logging & Observability" section above. Both `YamlConfigSettingsSource` instances are constructed with `yaml_file_encoding="utf-8"` because they otherwise open the file with the platform default (cp1252 on Windows), which fails on any non-ASCII byte in the committed config.

`routes.enabled` is the list consumed by `app/main.py`'s `mount_routers()` — see "Enabling/Disabling Resources" below.

Any nested field can still be overridden by an env var using `__` as the nesting delimiter, without touching either committed file — e.g. `RATE_LIMIT__BACKEND=memory` or `RATE_LIMIT__WRITE_LIMIT=7` (`model_config`'s `env_nested_delimiter="__"`).

There is no hand-rolled loader: `Settings` is a `pydantic_settings.BaseSettings`, so `configs/config.yaml` and `configs/cache.yaml` are each wired in as their own `PydanticBaseSettingsSource` (pydantic-settings' built-in `YamlConfigSettingsSource`) in that precedence tuple. A future secrets-manager source (AWS Secrets Manager, SSM, etc.) would slot into the same tuple the same way — no changes needed anywhere that reads `settings.*`.

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
- **Two reference conventions exist — check which one the resource follows before touching a `_id` column.**
  - *Flattened reference (Patient, Practitioner, Organization, Location, HealthcareService, PractitionerRole, Schedule, Slot, Appointment, AppointmentResponse, Encounter, Questionnaire, QuestionnaireResponse, ServiceRequest, MedicationRequest, Observation, DiagnosticReport — the reworked resources, and the one to use for new work):* **four** columns, not three — `{prefix}_reference` (String, the raw literal string exactly as received: relative or an absolute URL to another system entirely, kept regardless of whether it resolves locally) + `{prefix}_type` + `{prefix}_id` + `{prefix}_display`, where `{prefix}_id` stores the **public sequence ID**, not the internal PK, and only when `{prefix}_reference` actually resolves to a local row. There is deliberately **no `ForeignKey` and no relationship** — the target table varies per row by `{prefix}_type`, so a real FK is impossible. Existence is checked at write time by `ensure_resource_exists()` (`app/core/reference_resolver.py`), which matches on `model.<resource>_id`; the target type must be registered in `RESOURCE_REGISTRY` or the check fails closed and rejects every reference. The mapper emits `f"{type}/{id}"` directly off `{prefix}_type`/`{prefix}_id` — `{prefix}_reference` exists purely to preserve an external absolute URL that `{prefix}_id` can never resolve to, and is easy to drop by mistake since the mapper never reads it (confirmed widespread on a full audit: every flattened Reference field on Location, HealthcareService, PractitionerRole, Schedule, and Slot shipped without it — `managingOrganization`/`partOf`/`identifier.assigner`/`endpoint`/`providedBy`/`location`/`coverageArea`/`practitioner`/`organization`/`healthcareService`/`actor`/`schedule`, all fixed. Organization and Practitioner already had it right everywhere). Pair it with the `{prefix}_identifier_*` logical-reference fallback for targets that aren't resources in this system.
  - *Legacy single-target reference (most of the other ~24 resources):* a real `ForeignKey("resource.id")` storing the **internal `resource.id` PK**, with `index=True` and a `lazy="selectin"` relationship; the mapper reads the public ID back through that relationship.

  These are not interchangeable: `task.location_id` is a real FK holding an internal PK, while `location.part_of_id` holds a public `location_id` with no FK at all.
- **Nullability must match the real FHIR cardinality** — `nullable=False` only when a field's spec cardinality minimum is `1`. Never invent a stricter-than-spec `NOT NULL` for a sub-field that's `0..1` on its own datatype (e.g. `Address.city`/`state`/`postalCode`/`country`, or `Identifier.system`/`.value`) just because the parent field embedding it usually carries a value, and don't upgrade a genuinely `0..1` top-level field (e.g. a status/mode/name/active-shaped code, string, or boolean) to `NOT NULL` because it reads as "obviously always present." A full audit against freshly-fetched R4 spec pages found this on `Identifier.value` on five of seven already-built resources (Location, HealthcareService, PractitionerRole, Schedule, Slot — Organization/Practitioner already had it right), plus `Location.status`/`.name`/`.mode`, `HealthcareService.active`/`.name`, and `Schedule.active`. All fixed. See `/fhir-db-model`'s nullability rule and its `Identifier` section.
- **Every Address/ContactPoint/Coding embed uses its shared `Fhir*Mixin`** (`app/models/shared/`), even when it's the only datatype group on that table with no prefix collision to avoid — never hand-declare the same columns again just because there's nothing to prefix against (confirmed shipped wrong once already on Location's `address`, which is also how its `line` ended up as comma-separated `Text` instead of the mixin's `ARRAY(String)`). See `/fhir-db-model` Step 5.
- **DB `CheckConstraint`s are otherwise avoided** — every R4 structural rule is enforced by the FHIR validator layer instead, including ones that technically could be a single-table `CHECK` (see `OrganizationModel`'s docstring, `app/models/organization/core.py`) — **except** for sibling columns that are jointly `1..1` *within* an already-`0..1` BackboneElement on the same row (e.g. `Location.position.longitude`/`.latitude`), which use a plain `CheckConstraint` in `__table_args__` instead. See `/fhir-db-model`'s "Conditionally-required sibling columns" rule.
- **No comma-separated-Text exception for `0..*` scalar lists — always `ARRAY(String)`.** `daysOfWeek[]` (`LocationHoursOfOperation`/`HealthcareServiceAvailableTime`/`PractitionerRoleAvailableTime.days_of_week`) briefly was a documented comma-Text exception, justified as "never filtered individually, so a child table would add a join for nothing" — that reasoning only argues against a *child table*, not against a plain array column (which isn't a join). Fixed on all three; don't recreate the same conflation for a future field.
- **Every resource gets an `extension` JSONB column — it's not resource-specific.** `extension[]` (0..*) is inherited from base `DomainResource`, not a per-resource field, so every resource's main table carries one (`Column(JSONB, nullable=False, server_default=text("'[]'"))`, raw `[{url, valueType, value}, ...]`, validated by the profile pipeline rather than the DB) regardless of whether that resource "needs" it today. Currently on Organization, Location, HealthcareService, Practitioner, PractitionerRole, Schedule, Slot, Appointment, AppointmentResponse, Encounter, Questionnaire, QuestionnaireResponse, ServiceRequest, MedicationRequest, Observation, and DiagnosticReport — Appointment, AppointmentResponse, Encounter, Questionnaire, QuestionnaireResponse, ServiceRequest, MedicationRequest, Observation, and DiagnosticReport were all built with it readable AND writable from the start; the other seven's own extension rollout history (five initially shipped read-only) is covered above. See `/fhir-db-model` Step 4a. `modifierExtension` is the semantically-different sibling field (unsafe to ignore if unrecognized, vs. `extension`'s safe-to-ignore) and is a separate, currently-unimplemented gap — not bundled into this fix.
- **A bulk Core `delete()` of a parent CodeableConcept-list row does not cascade to its grandchild coding rows — delete grandchildren first, or PATCH-replacing a populated list throws a `ForeignKeyViolationError`.** None of this codebase's child/grandchild FK pairs (e.g. `AppointmentResponseParticipantType` → `...TypeCoding`) declare `ondelete="CASCADE"`, at either the model or the migration level — `cascade="all, delete-orphan"` on the SQLAlchemy *relationship* only fires on an ORM-level `session.delete(parent_instance)`, not on a Core-level `delete(ParentTable).where(...)` bulk statement, which is what every resource's `patch_full()` uses to replace a sub-resource list wholesale. Discovered building AppointmentResponse (its own `participant_type` patch-replace hit this immediately in testing) — the same latent gap almost certainly exists in every earlier resource's `patch_full()` for any CC-list field whose child rows can carry grandchild coding rows (Slot/Schedule/Appointment's serviceCategory/serviceType/specialty/reasonCode/identifier.type, etc.), simply because no prior smoke test happened to PATCH-replace a list that already had coding rows attached. Fixed for AppointmentResponse by deleting grandchildren via a `.in_(select(ParentTable.id).where(...))` subquery before deleting the parent rows; apply the same fix to a resource's own list-replace block if it's ever actually hit there too — don't assume `cascade="all, delete-orphan"` alone covers a bulk Core delete.
- **A CodeableConcept-list field living inside a 0..* BackboneElement nests 3 levels deep — eager-load every level, or `DetachedInstanceError` at render time.** `Appointment.participant.type` (0..* CodeableConcept, itself inside `participant`, 0..*) needed `AppointmentParticipant` → `AppointmentParticipantType` → `AppointmentParticipantTypeCoding`, the deepest nesting in this codebase so far. The structure itself is nothing new (same child→grandchild pattern as `Identifier.type.coding[]`), but `_with_relationships()`'s `selectinload()` chain has to walk every level explicitly — `selectinload(Parent.participants).selectinload(Participant.types)` alone eager-loads two levels and silently leaves the third (`.types.codings`) lazy, which then blows up as a `DetachedInstanceError` the moment the mapper reads it outside the session (the session is already closed by then, not just lazy — caught by an actual end-to-end smoke test, not by reading the code). The fix is one more `.selectinload(...)` hop: `selectinload(Parent.participants).selectinload(Participant.types).selectinload(ParticipantType.codings)`. Count the levels in a new BackboneElement-of-BackboneElement-of-CodeableConcept shape and eager-load every one.
- **`Reference(Any)` (a field with no enumerable, finite target-type set) needs a plain `String` reference-type column, not a Postgres `Enum`.** Every other polymorphic Reference field in this codebase (`Schedule.actor`, `Appointment.participant.actor`, `Appointment.reasonReference`/`basedOn`/`slot`) still has a small, real, finite list of allowed target types straight from the spec, so each gets its own `Enum` + `parse_reference(ref, SomeEnum)` — which 422-rejects any type string outside that list. `Appointment.supportingInformation` is `Reference(Any)` — genuinely any resource type, no list to enumerate — so forcing it through an `Enum` would 422 every reference to a type this system doesn't happen to model. Use a plain `reference_type = Column(String, nullable=True)` instead, and a tolerant parser (`app.repository.appointment._shared._parse_any_ref`) that splits `"Type/id"` without validating `Type` against anything and never raises — an unparseable shape (an absolute URL, a non-numeric id) just comes back `(None, None)` and falls back to the raw `reference_reference` string + identifier fallback, same as any other unresolvable reference. Never force a true `Reference(Any)` field through the `Enum`-per-field convention used everywhere else.
- Alembic autogenerate enum values are correct (key = value convention); still replace `sa.Enum` with `postgresql.ENUM` pattern in migrations for proper create/drop handling. **The same shared `postgresql.ENUM(..., create_type=False)` object must be referenced by every `op.create_table()` column using that type** — `create_type=False` on a fresh per-column `sa.Enum(...)` literal is silently ignored by `op.create_table()`, causing a deterministic (not a race) `DuplicateObjectError` the moment a second table uses the same type. See `/fhir-db-model` Step 7 for the full failure signature.
- **A `Fhir*Mixin`'s prefix (e.g. `FhirCodingMixin._coding_prefix`) renames only the underlying DB `Column`'s first positional (column-name) argument — never the Python-level `declared_attr` attribute name, which stays the bare `system`/`version`/`code`/`display`/`user_selected` (or `line`/`city`/... for `FhirAddressMixin`, etc.) no matter how many prefixed groups share a row.** Every ORM constructor kwarg, `getattr`, and mapper read against a prefixed embed must use the bare name — `EncounterModel(class_system=...)` raises `TypeError: 'class_system' is an invalid keyword argument`; the right call is `EncounterModel(system=...)`. Only a function building a *plain-JSON output dict's keys* (not touching the ORM at all) should apply the prefix, and only to that dict's own keys, never to the attribute read. First surfaced on `Encounter.class` (the first top-level, non-list bare-Coding field in this codebase) — every earlier prefixed-Coding use happened to be inside its own one-purpose child table where this never came up. Audit any new prefixed mixin use the same way. **Confirmed to bite twice over on `Questionnaire.item`** — `QuestionnaireItemEnableWhen`/`QuestionnaireItemAnswerOption`/`QuestionnaireItemInitial` each combine a prefixed `FhirCodingMixin` (and, on `Initial`, a prefixed `FhirAttachmentMixin` too) with several *other* plain hand-declared `answer_quantity_*`/`value_reference_*`-style columns on the same row — easy to reflexively pass the Coding/Attachment fields through with the same prefixed name as every sibling column around them, both in the repository's ORM constructor calls (`TypeError: 'answer_coding_system' is an invalid keyword argument`) and in the FHIR/plain mapper's own attribute *reads* (silently wrong output, no exception, since `getattr`/attribute access on a nonexistent prefixed name doesn't raise the same way a constructor kwarg does — caught only by actually exercising a live create+read round trip, not by code review).
- **A recursive BackboneElement (one whose own child list is the *same* BackboneElement type, nested to unbounded depth) does not fit the chain-of-`selectinload()` pattern every other 0..*-inside-0..* shape in this codebase uses** — `Questionnaire.item` (`item.item` nests arbitrarily deep) is the first of these built here. Model it as a single self-referential child table with **two** parent-pointing columns on every row, at every depth: a real self-referential `parent_item_id` FK (nullable, NULL = top-level, no `relationship()` needed for it) for the actual tree edge, AND a denormalized `questionnaire_pk` FK straight back to the root resource row (not just to the immediate parent item). The second column is what makes this tractable — one `selectinload(QuestionnaireModel.items)` eager-loads the *entire* tree (every item at every depth) in one extra query regardless of nesting depth, the mapper reconstructs the nested FHIR `item[]` shape in plain Python by grouping that flat list on `parent_item_id` (`O(n)`, no recursive queries), and `patch_full()`'s whole-tree replace becomes a single `DELETE ... WHERE questionnaire_pk = :id` for the item table itself (plus one more `DELETE ... WHERE item_id IN (SELECT id FROM questionnaire_item WHERE questionnaire_pk = :id)` per *grandchild* table — `item.code`/`.enableWhen`/`.answerOption`/`.initial` — since those still only FK to their one immediate parent item, not to the root) instead of walking the tree level by level. Reach for this shape again for any future recursive structure (e.g. a `QuestionnaireResponse.item` rebuild, `Composition.section`). **⚠️ The no-`relationship()`-for-`parent_item_id` choice has a sharp edge at plain ORM-level delete (`session.delete(parent_instance)`, as opposed to `patch_full()`'s own Core-level bulk deletes above, which are unaffected):** SQLAlchemy's unit-of-work orders a `cascade="all, delete-orphan"` collection's per-row DELETEs using the relationship graph it knows about, and a self-referential edge with no `relationship()` object isn't part of that graph — it deletes every `questionnaire_item` row in whatever order the collection happened to load them, which 500s with `ForeignKeyViolationError: ... is still referenced from table "questionnaire_item"` the moment a parent item is ordered before a child that still points at it (confirmed live on `DELETE /questionnaires/{id}` for any questionnaire with more than one level of nesting). The fix is the same Core-level bulk-delete sequence `patch_full()` already uses for its own list-replace — delete the item subtree (and its own grandchildren) via explicit `DELETE ... WHERE questionnaire_pk = :id`/`WHERE item_id IN (...)` statements *before* `session.delete(q)` ever reaches the ORM cascade, rather than adding the `relationship()` back (which would need `remote_side=[id]` and still wouldn't help patch_full's own bulk-delete code path, which never goes through the ORM cascade at all). See `app/repository/questionnaire/core.py`'s `delete()`.
- **Converting a Pydantic schema enum's `.value` into the model-layer Postgres enum must always go by member *name*, never by value — including for enums whose values aren't readable FHIR codes at all.** The established `_model_status`-style helper (Pydantic member → model member, matched by `.name`) already covers hyphenated codes (`in-progress` → `IN_PROGRESS`); it applies just as much to a field like `Encounter.length.comparator`, whose FHIR values are bare comparison symbols (`<`, `<=`, `>=`, `>`) with no identifier-safe form at all. Passing `.value` straight through where the Postgres enum's labels are `LT`/`LE`/`GE`/`GT` throws `InvalidTextRepresentationError: invalid input value for enum ...: "<"` at write time, in both `create_full`'s constructor call and `patch_full`'s setattr. Write a `_model_<field>(value)` converter for every schema-enum-to-model-enum edge, not just the ones that happen to look like hyphenated codes.

---

## What "End-to-End" Means

When a resource is asked for **"end to end,"** that phrase covers **both repos**, not just this one — a resource isn't end-to-end until a GraphQL client talking to the gateway can actually use it, on **both** connectors:

1. **fhir-server (this repo)** — model → migration → schemas (input/response) → mapper (`fhir.py`/`plain.py`/`payload.py`) → repository → service → DI → router. The complete, authoritative checklist is `/new-fhir-resource`'s 17 steps — see below.
2. **fhir-gql (`D:\code\work\projects\fhir-gql`, sibling repo, GraphQL gateway in front of this one)** — not optional, not a follow-up task to circle back to later:
   - `app/fhir/schemas/<resource>.py` — the canonical FHIR-shaped Pydantic `Response`/`Input` models (mirror an existing resource, e.g. `organization.py`)
   - **`app/connectors/internal/translators/<resource>.py` AND `app/connectors/medplum/translators/<resource>.py`** — both connectors, always, never just the one that's currently active in `configs/config.yaml`'s `connectors.active`. These are not interchangeable stubs: they have genuinely different wire conventions (e.g. `to_wire_patch()` — fhir-server's own PATCH accepts a plain partial-fields dict, Medplum's PATCH requires an RFC 6902 JSON Patch array over `application/json-patch+json`, confirmed this was silently broken for every resource's `updateFhirX` mutation until caught by actually exercising the medplum connector, not by code review alone)
   - Both registered in `app/connectors/translator_registry.py` (`<RESOURCE>_TRANSLATORS` dict + `active_<resource>_translator()`)
   - `app/gql/<resource>/types/{response,input}.py` — GraphQL types via `strawberry.experimental.pydantic`, `all_fields=True`; any field whose Pydantic type isn't a native GraphQL scalar (a bare `dict`, e.g. `extension`) needs an explicit `: JSON | None` override in the type body — `all_fields=True` alone does not handle it and the schema fails to build without it
   - `app/gql/<resource>/queries.py` / `mutations.py`, wired into the root `Query`/`Mutation` in `app/gql/schema.py`

**"Done" means tested on both connectors, not just one.** A connector can look correct by code inspection and still be broken in practice — the Medplum PATCH bug above passed every code read-through because the *shape* looked plausible; it only surfaced by actually calling `createFhirX`/`updateFhirX`/etc. against a live Medplum instance with `connectors.active: medplum`. Don't declare a resource (or a cross-cutting field like `extension`) end-to-end-complete on the strength of the `internal` connector working alone.

---

## Adding a New FHIR Resource

Use the `/new-fhir-resource` skill (`.claude/commands/new-fhir-resource.md`) for the complete 17-step checklist covering model → migration → schemas → mapper → repository → service → DI → router. That skill covers the fhir-server half only — see "What 'End-to-End' Means" above for the fhir-gql half every resource also needs.

Two related skills, used opportunistically rather than as part of every new resource:
- `/split-resource-package` — once a resource's model/repository/service/router/schema file grows large (many sub-resources), split it into a per-sub-resource package. Patient, Practitioner, Organization, Location, HealthcareService, PractitionerRole, Schedule, and Slot all do this across every layer; Appointment deliberately didn't (see the Schema Conventions section) despite being larger than any of them.
- `/resource-auth-rollout` — only if explicitly asked to add direct JWT/RBAC auth to a resource (the Patient/Practitioner/Organization/Location/HealthcareService/PractitionerRole/Schedule/Slot/Appointment/AppointmentResponse/Encounter/Questionnaire pattern — twelve resources now, see Multi-Tenancy & Ownership's "Auth rollout status"). Questionnaire was built against the plain default pattern first, then explicitly asked to be rolled into auth afterward — so it's also the live example of *converting* an already-built default-pattern resource (strip `tenant_id`/`created_by`/`updated_by` from its schemas, delete its `resolve_questionnaire()` dep, add `get_questionnaire_scoped()`, wire `require_permission(...)` on every route) rather than building one from scratch already auth-rolled-out. Still don't add the auth-rollout treatment to a new resource without being asked; it changes org_id/created_by/updated_by provenance throughout the whole stack, not just the router. Note this does NOT mean a default-pattern resource skips authentication entirely — see Multi-Tenancy & Ownership's `get_current_user` callout above; a valid JWT is still required to reach it at all, just with no RBAC/ownership check on top.

---

## Enabling/Disabling Resources

Which resource routers get mounted under `/api/fhir/v1` is controlled entirely by **`configs/config.yaml`'s `routes.enabled` list** (repo root's `configs/` folder, committed — not a secret, same spirit as `alembic.ini`), not by editing source. Each router already carries its own `prefix=`/`tags=` (set at construction in the resource's own module/package, e.g. `router = APIRouter(prefix="/patients", tags=["Patients"])`) — `app/routers/__init__.py`'s `discover_routers()` introspects the package namespace for every submodule exposing a module-level `router: APIRouter` and returns a `{name: router}` dict, so there's no separate prefix/tag table to keep in sync. `app/main.py`'s `mount_routers(app)` mounts only the names present in `routes.enabled`, and is called from inside the FastAPI `lifespan` handler at actual ASGI startup (not at module-import time) — mirrors txtai's `api/application.py::lifespan()` pattern. Toggling a resource on/off is a one-line YAML edit + restart — no code change, no redeploy of different source.

Every router is still always imported in `app/routers/__init__.py` via `from . import <name> as <name>` (cheap, no side effects, and required for `discover_routers()`'s introspection to see it) — only *mounting* is conditional. Adding a new resource: give its `APIRouter()` a `prefix=`/`tags=`, add the `from . import <name> as <name>` re-export + `__all__` entry, and append its name to `configs/config.yaml`'s `routes.enabled` list once it's ready to expose, per Step 17 of `/new-fhir-resource`.

`terminology_router`, `fhir_profile_router`, and `fhir_validate_router` are each mounted separately in `app/main.py` at module level, under their own distinct prefix (`/api/v1/terminology`, `/api/v1/fhir-profiles`, `/api/v1/validate`) rather than the shared `/api/fhir/v1` `discover_routers()`/`mount_routers()` mounts everything else under — they aren't FHIR resources with public sequence IDs, so folding them into that generic mechanism would also move their URLs under `/api/fhir/v1`. Still gated by the same `routes.enabled` list, just via a plain `if "<name>" in settings.routes.enabled:` check around each one's own `app.include_router(...)` call instead of going through `discover_routers()`.

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
- **Fixed, but easy to regress: a create route's `format_response(...)` call must pass `status_code=status.HTTP_201_CREATED` explicitly.** `format_response()`/`format_list_response()`/`format_paginated_response()` (`app/core/content_negotiation.py`) default to `status_code=200` and always build a plain `JSONResponse(...)` — FastAPI uses a *returned* `Response` object's own status verbatim and ignores the route decorator's `status_code=` the moment the handler returns a `Response` instance instead of a plain dict, so the decorator's `status_code=201` is cosmetic (OpenAPI docs only) unless the call site also passes it. Every existing create endpoint (Organization, Location, HealthcareService, Practitioner, PractitionerRole, Schedule, Slot, Appointment, AppointmentResponse, Encounter, Questionnaire) now does this — confirmed live, `POST` returns a real `201`. **A new resource's create route must do the same** — `return format_response(fhir, plain, request, status_code=status.HTTP_201_CREATED)` — or it silently reverts to 200 despite a correct-looking `status_code=201` decorator.
