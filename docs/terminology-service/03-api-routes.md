# API Routes

**What this file is:** the HTTP surface — every URL path a client (or the
MCP tool layer, see the root `CLAUDE.md`'s "OpenAPI Spec = MCP Contract")
can actually call to read or write a code system, concept, value set,
concept map, org concept, or display override. If those words aren't
familiar yet, read
[00-what-is-terminology.md](00-what-is-terminology.md) first — this file
assumes you already know what each one means and is only about how to
reach it over HTTP.

Source: `app/routers/terminology/` — 8 sub-routers composed in
`__init__.py`, plus `_responses.py` (169 lines) for the shared OpenAPI
response-schema constants and the org-scoping helper. All terminology
routes live under a single mount point; see `app/main.py`'s
`mount_routers()` / `configs/config.yaml`'s `routes.enabled` list (root
`CLAUDE.md`'s "Enabling/Disabling Resources") for how that mount is toggled.

## Router composition order

`app/routers/terminology/__init__.py` chains `router.include_router()` in
this order:

```
code_systems, value_sets, concepts, validation, concept_maps,
org_concepts, display_overrides, audit_log
```

This mirrors the repository/service mixin order from
[02-repository-and-service-layers.md](02-repository-and-service-layers.md)
exactly — each sub-router is the HTTP face of the matching mixin, one file
per mixin, same name.

## `_responses.py` — the two shared building blocks

1. **`_require_org_id(request)`** — every org-scoped route (org-concepts,
   display-overrides) calls this first. It reads
   `request.state.user.get("activeOrganizationId")` and raises **403** if
   absent. This is the terminology subsystem's own, independent
   org-scoping check — it does **not** route through `app/auth/`'s
   JWT/JWKS verification the way Patient/Practitioner/etc. do (see root
   `CLAUDE.md`'s Multi-Tenancy & Ownership section). Terminology isn't one
   of the eight auth-rollout resources; it still relies on whatever upstream
   middleware/gateway already populated `request.state.user`, it just adds
   its own presence check on top before trusting `activeOrganizationId` for
   write-scoping.
2. **OpenAPI response constants** — every `_XXX_200`/`_XXX_201`/etc. built
   via `inline_schema(...)` at module level, following the exact
   dual-content-type pattern (`application/json` + `application/fhir+json`)
   the root `CLAUDE.md`'s "OpenAPI Response Schema Pattern" section
   specifies for every other resource. Terminology isn't FHIR-resource-
   shaped the way Patient/Encounter/etc. are (a `TerminologyConcept` isn't
   itself a FHIR resource type with its own StructureDefinition), so the
   "`application/fhir+json`" variant here is this project's own plain
   terminology-response shape duplicated under that content type, not a
   real HL7 FHIR resource serialization — check `app/schemas/terminology.py`
   directly before assuming a `FHIRXxxSchema`/`PlainXxxResponse` pair exists
   the way it does for the 8 auth-rollout resources; terminology's schemas
   don't follow that FHIR/plain split at all (see below).

## Schemas: `app/schemas/terminology.py` (240 lines, 29 classes)

Unlike every other resource (which has a `FHIR<Resource>Schema` /
`Plain<Resource>Response` pair per the root `CLAUDE.md`'s "Schema
Conventions"), terminology has **one schema per shape**, used for both
content types — there's no FHIR-camelCase-vs-plain-snake_case duality here
because none of these rows is a FHIR resource with its own canonical FHIR
JSON shape. Representative classes: `CodeSystemResponse`,
`CodeSystemListResponse`, `ValueSetResponse`, `ConceptResponse`,
`ValidateResponse`, `TranslationResult`/`TranslateResponse`,
`OrgConceptResponse`, `OrgConceptListResponse`, `DisplayOverrideResponse`,
`DisplayOverrideListResponse`, `AuditLogRecord`/`AuditLogListResponse`,
`ConceptMapResponse`/`ConceptMapListResponse`. All use
`model_config = ConfigDict(extra="forbid")` on inputs, matching the
convention described in the root `CLAUDE.md`.

## `org_concepts.py` router (153 lines, 5 endpoints)

| Method | Path | Notes |
|---|---|---|
| POST | `/org-concepts` | 201 on create; 403 (no org on request), 404 (code system not found), 409 (concept already exists for this org) all documented in `responses=` |
| GET | `/org-concepts` | list, filterable |
| GET | `/org-concepts/{concept_id}` | 404 if not found |
| PATCH | `/org-concepts/{concept_id}` | 404 if not found |
| DELETE | `/org-concepts/{concept_id}` | 404 if not found |

## `display_overrides.py` router (144 lines, 5 endpoints)

Structurally identical to `org_concepts.py` — same five-endpoint shape, same
403/404 pattern, POST targets `/display-overrides` keyed by `(system, code)`
instead of inventing a new concept directly (see
[07](07-org-concepts-and-display-overrides.md) for why the create payload
differs even though the router shape doesn't).

## `concept_maps.py` router

`GET /concept-maps` (list — see
[02-repository-and-service-layers.md](02-repository-and-service-layers.md)
for the count-query fix applied to this endpoint's pagination `total`)
and `POST /concept-maps` (`add_concept_map`). The POST handler returns a
**plain dict**, not a Pydantic response model — deliberately not routed
through `jsonable_encoder` the way every other write handler is, since a
plain `{"created": bool}`-shaped dict has no `datetime` fields that would
need it (see the `jsonable_encoder` note below).

## The `jsonable_encoder` fix

Every other write/read handler that returns a Pydantic model wraps it as
`JSONResponse(content=jsonable_encoder(response_model))`, not
`JSONResponse(content=response_model.model_dump())`. This matters
specifically because several of these response schemas carry `datetime`
fields (`created_at`, `updated_at` on org-concepts/display-overrides/audit
records) — `model_dump()` leaves those as Python `datetime` objects, which
`JSONResponse`'s default encoder can't serialize, and `jsonable_encoder`
converts them to ISO-8601 strings first. This was a real, previously-shipped
bug in this subsystem; it's why `concept_maps.py`'s dict-returning
`add_concept_map` handler is the one exception that correctly doesn't need
the same treatment — it has no datetime field to break on.

## Validation endpoints

`validation.py` router exposes `validate()`/`translate()` as HTTP endpoints
over the service methods described in full in
[06-validation-and-field-bindings.md](06-validation-and-field-bindings.md).
