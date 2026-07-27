# Patient — End-to-End Developer Guide

This doc walks a single resource, **Patient**, all the way through every layer of
this codebase — router → schemas → service → repository → ORM model → FHIR/plain
mappers → DI wiring — so a new developer can see the whole shape of "one
resource" in one place. Patient is the first resource documented this way;
the same layout will be produced for every other resource next.

If you haven't read it yet, read `CLAUDE.md` first — it documents the
*conventions* (naming, layering rules, content negotiation, multi-tenancy).
This doc documents *this specific resource* concretely: real file paths, real
function names, real line numbers, and a couple of full request traces.

---

## 1. File map

| Layer | File | Purpose |
|---|---|---|
| Model | `app/models/patient/patient.py` | `PatientModel` + 11 sub-resource tables (`PatientIdentifier`, `PatientName`, `PatientTelecom`, `PatientAddress`, `PatientPhoto`, `PatientContact` + 2 grandchild tables, `PatientCommunication`, `PatientGeneralPractitioner`, `PatientLink`) |
| Model enums | `app/models/patient/enums.py` | `PatientGender`, `PatientLinkType`, `PatientGeneralPractitionerType`, `PatientLinkOtherType`, plus the datatype enums (`AddressUse`, `AddressType`, `ContactPointSystem`, `ContactPointUse`, `HumanNameUse`) — the model layer owns these; schemas import them, not the other way around |
| Shared enums | `app/models/enums.py` | Cross-resource enums Patient reuses: `OrganizationReferenceType`, `IdentifierUse` |
| Input schemas | `app/schemas/patient/input.py` | `PatientCreateSchema`/`PatientPatchSchema`/`PatientFullCreateSchema`/`PatientFullPatchSchema` + one Create/Patch pair per sub-resource |
| Response schemas | `app/schemas/patient/response.py` | `FHIRPatientSchema`/`PlainPatientResponse` + per-sub-resource FHIR/Plain shapes + list-response wrappers |
| Schema package root | `app/schemas/patient/__init__.py` | Re-exports everything from `input.py`/`response.py` — this is what router/service/repository import from |
| Shared FHIR datatypes | `app/schemas/common/fhir.py` | `FHIRReference`, `FHIRIdentifier`, `FHIRHumanName`, `FHIRAddress`, `FHIRContactPoint`, `FHIRCodeableConcept`, `FHIRBundle`, etc. — shared by ~20 resources, not Patient-specific |
| Mappers | `app/fhir/mappers/patient/fhir.py`, `.../plain.py`, `.../__init__.py` | ORM row → FHIR camelCase dict / snake_case dict |
| Shared mapper helpers | `app/fhir/datatypes.py` | `fhir_identifier`/`plain_identifier`, `fhir_human_name`, `fhir_telecom`, `fhir_address`, `fhir_photo`, `fhir_communication`, `fhir_enum`, `fhir_split` — shared by ~13 resources whose child tables have the same shape |
| Repository | `app/repository/patient_repository.py` | All DB I/O — ~50 methods, one `async with self.session_factory()` block per operation |
| Service | `app/services/patient_service.py` | Thin orchestration — every method is a 1-2 line pass-through to the repository, plus the four `_to_fhir`/`_to_plain`/`_to_fhir_core`/`_to_plain_core` formatters |
| Resolve deps | `app/deps/patient_deps.py` | `resolve_patient` / `resolve_patient_core` — load-by-public-ID-or-404, used as `Depends(...)` in routes |
| DI module | `app/di/modules/patient.py` | `PatientContainer` — wires `PatientRepository` + `PatientService` |
| DI dependency | `app/di/dependencies/patient.py` | `get_patient_service()` — the `@inject`-wrapped FastAPI dependency routes actually call |
| DI root | `app/di/container.py` | Mounts `PatientContainer` as `Container.patient` |
| Router | `app/routers/patient.py` | All HTTP routes — ~1560 lines, 9 sub-resources × (POST/GET-list/PATCH/DELETE) + the Patient resource itself |
| Router mount | `app/routers/__init__.py` | `api_router.include_router(patient_router, prefix="/patients", tags=["Patients"])` |

---

## 2. The layering rule, concretely

```
HTTP request
   │
   ▼
Router (app/routers/patient.py)
   - validates the body against a Pydantic schema (FastAPI does this automatically
     from the type hint, e.g. `payload: PatientFullCreateSchema`)
   - pulls user_id/org_id/created_by straight off the validated payload
     (there is no auth middleware — see CLAUDE.md "Multi-Tenancy & Ownership")
   - resolves path params via Depends(resolve_patient) → 404 if missing
   - calls exactly one PatientService method
   - passes the result through format_response()/format_paginated_response()
   │
   ▼
Service (app/services/patient_service.py)
   - no business logic here — every method is `return await self.repository.xxx(...)`
   - owns the four formatter methods (_to_fhir, _to_plain, _to_fhir_core, _to_plain_core)
     so the router never imports the mapper functions directly for the main
     resource (it does still import mapper functions directly for sub-resource
     GET routes — see §5)
   │
   ▼
Repository (app/repository/patient_repository.py)
   - the only place that touches the database
   - one `async with self.session_factory() as session:` block per method —
     never holds a session across two repository calls
   - every read wraps its SELECT in _with_relationships() (line 85) so every
     sub-resource relationship is eager-loaded via selectinload — no lazy-load
     ever happens on an async session
   - every reference field that targets exactly one resource type gets
     resolved via a small `_parse_*` / `_resolve_*` helper before being stored
   │
   ▼
ORM Model (app/models/patient/patient.py)
   - PatientModel + child tables, pure SQLAlchemy 2.0 declarative classes
   - internal `id` (PK, never exposed) + public `patient_id` (sequence, starts
     at 10000, exposed everywhere)
   │
   ▼
Mapper (app/fhir/mappers/patient/{fhir,plain}.py)
   - to_fhir_patient(model) → FHIR R4 camelCase dict
   - to_plain_patient(model) → snake_case dict
   - both are called by the service's formatter methods, never by the
     repository or router directly
```

---

## 3. Trace #1 — `POST /api/fhir/v1/patients/full`

This is the richest write path (create Patient + every sub-resource
atomically), so it's the best one to trace end to end.

1. **Router** (`app/routers/patient.py:334`, `create_patient_full`)
   FastAPI validates the JSON body against `PatientFullCreateSchema`
   (`app/schemas/patient/input.py`). Every `extra="forbid"` on that schema
   means an unknown field is a 422, not silently dropped.
   ```python
   async def create_patient_full(payload: PatientFullCreateSchema, request: Request, patient_service=Depends(get_patient_service)):
       patient = await patient_service.create_patient_full(payload, payload.user_id, payload.org_id, payload.created_by)
       return format_response(patient_service._to_fhir(patient), patient_service._to_plain(patient), request)
   ```
   Note `user_id`/`org_id`/`created_by` come **straight off the payload** —
   there's no JWT decode anywhere in this service (see CLAUDE.md).

2. **Service** (`app/services/patient_service.py:129`, `create_patient_full`)
   ```python
   async def create_patient_full(self, payload, user_id, org_id=None, created_by=None):
       return await self.repository.create_full(payload, user_id, org_id, created_by)
   ```
   Zero logic — pure pass-through.

3. **Repository** (`app/repository/patient_repository.py:366`, `create_full`)
   - Opens one session (`async with self.session_factory() as session:`).
   - Constructs `PatientModel(...)` from the scalar fields, resolving
     `managing_organization` (a `"Organization/190001"` string) into
     `(managing_organization_type, managing_organization_id)` via
     `_parse_org_ref()` (line 60).
   - `session.add(patient); await session.flush()` to get `patient.id`
     (the internal PK) before inserting children.
   - Loops over every optional sub-resource list on the payload
     (`payload.names`, `payload.identifiers`, `payload.telecom`, …) and
     `session.add(...)`s a child-table row for each, using `patient.id` as
     the FK. Contacts get special handling since they have their own
     grandchildren (`relationship[]`, `telecom[]`).
   - Commits once at the end; rolls back and re-raises on any exception.
   - Returns `await self.get_by_patient_id(patient.patient_id)` — a fresh,
     fully eager-loaded read (see §4) rather than trusting the in-memory
     object, so every relationship is populated for the mapper.

4. **Mapper** (called back in the service's `_to_fhir`/`_to_plain`, not in
   the repository)
   - `to_fhir_patient()` (`app/fhir/mappers/patient/fhir.py`) builds the
     scalar fields via the shared `_core_fields()` helper, then appends each
     sub-resource array only if non-empty (`if patient.identifiers: result["identifier"] = [fhir_identifier(i) for i in patient.identifiers]`,
     using the **shared** `fhir_identifier()` from `app/fhir/datatypes.py` —
     Patient does not have its own identifier mapper; it uses the same one
     as ~13 other resources).
   - `to_plain_patient()` (`.../plain.py`) does the snake_case equivalent.

5. **Router again** — `format_response()` (`app/core/content_negotiation.py`)
   checks the `Accept` header and returns either the FHIR dict
   (`application/fhir+json`) or the plain dict (anything else), always as a
   raw `JSONResponse` (never through FastAPI's `response_model=` — see
   CLAUDE.md "Common Pitfalls").

---

## 4. Trace #2 — `GET /api/fhir/v1/patients/{patient_id}`

1. **Router** (`app/routers/patient.py:353`, `get_patient`) doesn't call the
   service to *load* the patient — that already happened in the
   `Depends(resolve_patient)` parameter.
2. **Dep** (`app/deps/patient_deps.py:7`, `resolve_patient`) calls
   `patient_service.get_raw_by_patient_id(patient_id)`, which is a straight
   pass-through to `repository.get_by_patient_id()`. If it returns `None`,
   the dep raises `HTTPException(404)` *before* the route body ever runs.
3. **Repository** (`app/repository/patient_repository.py:109`,
   `get_by_patient_id`) — one `SELECT ... WHERE patient_id = :id`, wrapped in
   `_with_relationships()` so every one of the 9 sub-resource collections is
   eager-loaded in the same round trip (via `selectinload`, not a JOIN — one
   extra query per relationship, but no lazy-load risk).
4. **Router** hands the already-loaded `PatientModel` straight to
   `patient_service._to_fhir(patient)` / `_to_plain(patient)`, then
   `format_response()` picks the representation based on `Accept`.

The `/core` variant (`GET /{patient_id}/core`) is the same shape but uses
`resolve_patient_core` → `get_core_by_patient_id()` (repository line 117),
which is a single-table `SELECT` with **no** `selectinload` at all — use it
when you only need the Patient's own scalar columns and want to skip the 9
extra relationship queries.

---

## 5. Sub-resource pattern (identifiers, names, telecom, …)

Every one of the 9 sub-resources (`names`, `identifiers`, `telecom`,
`addresses`, `photos`, `contacts`, `communications`,
`general_practitioners`, `links`) follows the exact same 4-route shape in
the router:

| Route | Router function | Repository method | Notes |
|---|---|---|---|
| `POST /{patient_id}/identifiers` | `add_identifier` (line 619) | `add_identifier` (line 863) | Appends one row |
| `GET /{patient_id}/identifiers` | `list_identifiers` (line 899) | `get_identifiers` (line 1141) | Calls the **shared** `fhir_identifier`/`plain_identifier` mapper functions directly — not through the service's `_to_fhir` |
| `PATCH /{patient_id}/identifiers/{identifier_id}` | `patch_identifier` (line 1344) | `patch_identifier` (line 1346) | `model_dump(exclude_unset=True)` + generic `setattr` loop |
| `DELETE /{patient_id}/identifiers/{identifier_id}` | `delete_identifier` (line 926) | `delete_identifier` (line 1257) | 204 on success, 404 if the child belongs to a different patient |

The `GET`/list routes are the one place the router imports mapper functions
directly (`fhir_identifier`, `plain_name`, `fhir_contact`, etc. — see the
import block at the top of `app/routers/patient.py`) rather than going
through the service, because these routes return a bare list + count, not a
full Patient representation.

`add_contact`/`patch_contact` are the most complex of the nine because
`PatientContact` has two of its own child tables
(`PatientContactRelationship`, `PatientContactTelecom`) — see repository
lines 976 and 1417 for how the grandchildren are rebuilt on patch.

---

## 6. Reference resolution — the one pattern worth understanding deeply

Patient has two kinds of reference field, and they're handled differently
on purpose:

- **Single-target** (`managingOrganization` → always `Organization`):
  flattened to 3 columns — `managing_organization_type` (enum, currently
  always `Organization`), `managing_organization_id`, `managing_organization_display`.
  Parsed via `_parse_org_ref()` (`patient_repository.py:59`), which delegates
  to the shared `app.core.filters.parse_reference()`.
- **Polymorphic** (`generalPractitioner` → `Organization | Practitioner | PractitionerRole`):
  same shape (`reference_type` + `reference_id` + `reference_display` on
  `PatientGeneralPractitioner`), but a single FK column can't reference three
  different tables, so `reference_id` is currently stored as a **plain
  integer, unresolved** — the client-supplied public ID, not the internal PK.

That second point is a known gap, not a design choice: every other
similarly-polymorphic-but-locally-resolvable reference in this codebase
(e.g. `EpisodeOfCare.care_manager`, also `Practitioner | PractitionerRole`)
was fixed this project to resolve to the internal PK via **one nullable FK
column per possible target table**, gated by the type discriminator, with
`viewonly=True` relationships keyed off `primaryjoin`. `PatientGeneralPractitioner`
hasn't had that fix applied yet — see `docs/test/models-fhir-r4-action-items.md`
history for the pattern this repo already uses everywhere else it applies.

`PatientIdentifier.assigner` and (if you're reading old history)
`managingOrganization.identifier.assigner` were, for a while this session,
also upgraded to the resolved-FK shape — and then deliberately reverted back
to a flat display `String`, matching the convention used by every other
`Identifier.assigner` field in this codebase (~40 other resources). The
lesson: **resolve to internal PK + FK whenever the target is one known
table; don't do it for `Identifier.assigner` anywhere in this codebase,
Patient included — that field stays a flat string everywhere.**

---

## 7. Schema conventions specific to Patient

- Three schema "kinds" live in `app/schemas/patient/`:
  `<X>CreateSchema`/`<X>PatchSchema` (input), `FHIR<X>Schema`/`Plain<X>Response`
  (output) — see `input.py` and `response.py`.
- `PatientFullCreateSchema`/`PatientFullPatchSchema` **inherit** from
  `PatientCreateSchema`/`PatientPatchSchema` and just add the 9 sub-resource
  list fields — they are not separately-maintained duplicates.
- Every enum Patient's schemas use (`PatientGender`, `HumanNameUse`,
  `AddressUse`, etc.) is imported from the **model** layer
  (`app.models.patient.enums` / `app.models.enums`), not redefined in the
  schema layer — the model is the single source of truth for what values are
  valid.
- Every field on every Patient input/response schema has a `Field(description=...)`
  grounded in the actual FHIR R4 element it represents (e.g.
  `IdentifierCreate.system`'s description is drawn from R4 `Identifier.system`).
  This is what makes the generated OpenAPI spec — and therefore the FastMCP
  tool descriptions built from it (see CLAUDE.md "OpenAPI Spec = MCP
  Contract") — actually useful to a caller who's never read the FHIR spec.
- `app/schemas/patient/__init__.py` is the **only** import surface other
  layers should use (`from app.schemas.patient import X`) — never reach into
  `.input`/`.response` from outside the package, and never go through
  `app.schemas.resources` (deleted — it used to exist as a Patient-only
  re-export hub with no reason to exist; see git history).

---

## 8. DI wiring, concretely

```
app/di/container.py
  Container.patient = providers.Container(PatientContainer, core=core)
        │
        ▼
app/di/modules/patient.py
  PatientContainer.patient_repository = providers.Factory(PatientRepository, session_factory=core.database.provided.session)
  PatientContainer.patient_service    = providers.Factory(PatientService, repository=patient_repository)
        │
        ▼
app/di/dependencies/patient.py
  get_patient_service() -- @inject, Depends(Provide[Container.patient.patient_service])
        │
        ▼
app/routers/patient.py
  every route: patient_service: PatientService = Depends(get_patient_service)
```

`session_factory` ultimately resolves to `Database.session` (an
`@asynccontextmanager` method on the `Database` class in
`app/core/database.py`) — this is what every repository method's
`async with self.session_factory() as session:` actually opens.

---

## 9. Where to look next

- `CLAUDE.md` — the conventions this doc assumes you already know.
- `.claude/commands/new-fhir-resource.md` — the 17-step checklist for adding
  a brand new resource from scratch (Patient already exists, but the
  checklist is the generalized version of everything in this doc).
- `.claude/commands/sub-resource-endpoints.md` — the pattern behind §5.
- `.claude/commands/fhir-db-model.md` — the CodeableConcept/Identifier/Reference
  flattening rules referenced in §6.
- `docs/test/models-fhir-r4-action-items.md` — the audit history that
  produced most of Patient's current shape (reference-ID resolver sweep,
  CodeableConcept convention, etc.).
