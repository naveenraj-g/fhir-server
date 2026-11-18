# Add a New FHIR Resource

Complete checklist for adding a FHIR R4 resource to this server, **Medplum-style**: the whole resource is stored as one JSON document, and *only the elements a FHIR search parameter filters on* are normalized into columns/tables (the "search index"). Organization, Location and Practitioner are built this way — copy them. Everything else in the repo that still uses the fully-normalized model (one column/table per element, `payload.py`, `plain.py`, flattened References) is the **old** approach: don't use it for new work. Its old skills are preserved in `docs/legacy/`.

**Always work from the HL7 R4 documentation. Never from memory, never R5.**

| What | URL |
|---|---|
| The resource page (element table + **Search Parameters** table) | `https://www.hl7.org/fhir/R4/<resource>.html` (`#search` for the parameter table) |
| How search works (types, modifiers, prefixes, `_include`, chaining, `_sort`) | `https://www.hl7.org/fhir/R4/search.html` |
| Common params on every resource (`_id`, `_lastUpdated`, `_tag`, ...) | `https://www.hl7.org/fhir/R4/resource.html#search` |
| Every R4 search parameter, with its expression and target types | `https://www.hl7.org/fhir/R4/searchparameter-registry.html` |
| Datatypes (HumanName, Address, ContactPoint, CodeableConcept, Period, ...) | `https://www.hl7.org/fhir/R4/datatypes.html` |
| Validation schema the native validator uses | `fhir.schema.json` (HL7 R4 download) |

Never `https://www.hl7.org/fhir/<resource>.html` (that is R5). `CodeableReference` does not exist in R4.

**This skill covers the fhir-server half.** A resource is only end-to-end when the fhir-gql gateway serves it too (Phase G at the bottom) — we do that after the fhir-server resources are done, when asked.

## ARGUMENTS: $RESOURCE

`$RESOURCE` = the resource name (e.g. `Patient`); `<resource>` = its snake_case form. Paths below use it.

---

## The idea in one minute

- **Write:** the request body *is* a FHIR R4 resource. Validate it as sent (base R4 validation), store it verbatim in `content` (JSONB, minus `resourceType`/`id`/`meta`). Any valid R4 element is kept, even ones nothing searches on. A key that isn't FHIR is a 422.
- **Read:** serve `content` as-is, stamping `id` (public sequence id) and `meta` (from the audit columns). Reads never touch the index tables. Always FHIR R4 JSON — no plain/snake_case form.
- **Search:** one `SearchRegistry` per resource declares every R4 search parameter once. That single declaration drives parsing/validation, SQL, `_sort`, `_include`, the OpenAPI parameter list and `GET /metadata`.
- **Index:** a derived copy of just the searchable values, rebuilt from `content` on every write by `_indexer.py` (the only write-side mapper). Nothing in the index is ever read to build a response.
- **Adding a field later:** if no search parameter uses it, **nothing to do** — it is already in `content`.

---

## Phase 1 — Decide what to index (do this before writing code)

1. Open the R4 resource page. Skip the element table (you store all of it as-is). Read the **Search Parameters** table: for each parameter note its **type**, its **expression**, and (for references) its **target types**.
2. Add the common ones every resource gets: `_id`, `_lastUpdated`. (`_tag/_profile/_security/_source/_text/_content/_list/_has/_type/_filter` are not implemented yet — see `docs/search-architecture/pending-search-capabilities.md`.)
3. For each parameter pick its storage with this table. Every searched string is stored **twice**: as written (answers `:exact`) and normalized (`*_norm`: accents stripped, case-folded via `app.fhir.search.normalize`; answers the default starts-with and `:contains`).

| R4 param type / source element | Index storage |
|---|---|
| `_id` | none — it is the public `<resource>_id` column |
| `_lastUpdated` | none — `coalesce(updated_at, created_at)` |
| token on a 0..1 boolean/code (`active`, `gender`, `status`) | one column on the main table. `Enum(...)` if the code has a `required` binding (closed list), else `String`. |
| string on a 0..1 element (`name`) | `x` + `x_norm` columns (+ a `text_pattern_ops` index on `x_norm` if it is a hot prefix search) |
| string on a plain 0..* list (`alias`) | `ARRAY(String)` pair `x` + `x_norm`, NULL (not `[]`) when empty so `:missing` is `IS NULL` |
| string on a structured 0..* (HumanName, Address) | child table, one row per entry, searched parts only, raw + `_norm` each; `line`/`given`/`prefix`/`suffix` stay `ARRAY(String)` so each is matched on its own |
| `phonetic` | a `phonetic` column of space-padded Soundex codes (`app.core.phonetic.phonetic_key`) |
| token on Identifier | child table: one row per `identifier` × `type.coding` (system, value, type_system, type_code, type_text_norm, type_display_norm) — `identifier_rows()` builds it |
| token on CodeableConcept / Coding (0..*) | child table: one row per coding (system, code, display_norm, text_norm) + a code-less row for text-only concepts — `type_rows()` builds it |
| token on ContactPoint (`telecom`, `phone`, `email`) | child table (system, value, use). R4: the code matches `value`, the `system|` part matches `use` |
| reference, 0..1 | columns `{p}_reference` (raw string), `{p}_type`, `{p}_id` (public id, relative refs only; **no FK**), `{p}_identifier_system`/`_value` — `reference_columns()` builds them |
| reference, 0..* | child table with the same columns — `endpoint_row()` is the model |
| reference to **several resource types** (`Schedule.actor`: Patient \| Practitioner \| ... \| Location) | a child table like the 0..* reference above, plus a plain-string `reference_type` holding the type of each relative `Type/<id>` (read it with a regex, not by position). Search needs a type (`actor=Type/id` or `actor:Type=id`; a bare id is ambiguous → 400) and the type is part of the match. Declare `targets=` with every allowed type, a `chain_targets` entry (and a chain that filters `reference_type == target`) only for the types that are searchable resources here, and **one `IncludeTarget` per modeled target type** so `_include=X:param` brings in all of them. Existence-check only the types registered in `RESOURCE_REGISTRY`; the others are stored as sent. |
| date / dateTime / instant | a timestamp (or date) column; matched with `date_match` |
| Period (e.g. `PractitionerRole.period` -> `date`) | two timestamp columns from `period_bounds(period)` in `app/repository/_content_index.py`: `*_start` = first instant covered, `*_end` = first instant **after** it (half-open, NULL = open); matched with `period_match` in `app/fhir/search/sql.py`, which implements the R4 range table (`eq` = the search range wholly contains the period, `gt/lt/ge/le` = overlap above/below, `sa/eb` = entirely after/before) |
| number, quantity, uri, composite | **not in the engine yet** — add a builder to `app/fhir/search/sql.py` + parser to `values.py` first, with tests |
| `near`-style special | a custom matcher in the resource's `search.py` (see Location `near`) |

> **Several parameters of the same shape?** Use **one shared table with a `param` column** instead of one table each: HealthcareService keeps its five CodeableConcept token parameters in `healthcare_service_token` and its three 0..* reference parameters in `healthcare_service_reference`. Build the rows with `functools.partial(Model, param="...")`.

4. **Everything else is not modelled at all.** No columns for non-searched elements, no `extension` column (it lives in `content`), no per-row audit columns on index tables, no DB `CHECK`/`UNIQUE` constraints (R4 rules are the validator's job; identifier uniqueness is a profile decision).
5. Nullability follows real cardinality — never a stricter-than-spec `NOT NULL`. (Index columns are all nullable; only `content` is `NOT NULL`.)
6. State which references the resource holds to other resources, and whether any resource that points *at* this one is already on the engine (that decides `_include` / `_revinclude` targets).

---

## Phase 2 — Files to create or change

Copy Organization (`app/**/organization/**`), the simplest example, or Practitioner (user-scoped + `/me`, names/telecom/communication). Location adds a special param (`near`) and cross-resource includes.

### A. Model — `app/models/<resource>/`
- `core.py` — `<Resource>Model(TenantAuditMixin, Base)`:
  - `id` (BigInteger PK, never exposed) + public `<resource>_id` (BigInteger via `Sequence("<resource>_pub_seq", start=<next free block from CLAUDE.md>, ...)`, `unique`, `index`, `server_default=seq.next_value()`)
  - `content = Column(JSONB, nullable=False)`
  - the 0..1 index columns from Phase 1
  - relationships to each index child table with `cascade="all, delete-orphan"`
  - a docstring with the **search parameter → storage** table (Organization's is the template)
- one file per index child table (`identifier.py`, `name.py`, `telecom.py`, `address.py`, `type.py`, ...) — **no `TenantAuditMixin`**, FK column named `<resource>_pk` (never `<resource>_id`, which is the public id), `back_populates` both ways
- `enums.py` if a column or child table needs a resource-specific enum (shared ones: `app/schemas/enums.py`, `app/models/enums.py` — `organization_reference_type` is a shared Postgres type: always `create_type=False`)
- `__init__.py` exporting every class
- `migrations/env.py` — import the new models so autogenerate sees them

### B. Migration — `migrations/versions/<rev>_<resource>_...py`
- Create `<resource>` (with `content`) + index tables + the `<resource>_pub_seq` sequence. Reuse shared Postgres enums with `postgresql.ENUM(name=..., create_type=False)` referenced by every `create_table` that uses them.
- **Converting an existing normalized resource?** Copy `a7d3f19c2b64` (Practitioner): build `content` from the old tables with a *frozen* copy of the old mapper (never import app code in a migration), drop the old child tables, create the index tables, rebuild the index from `content`. Verify on a **scratch database** (create DB → `alembic upgrade <previous head>` → insert old-shape rows → upgrade → inspect → `alembic check` for drift on your tables → drop DB). Never experiment on the dev DB.
- Apply: `uv run alembic upgrade head`.

### C. Schemas — `app/schemas/<resource>/`
- `input/core.py` — `<Resource>CreateSchema` / `<Resource>PatchSchema`, both built on one `_<Resource>Fields(FhirInputModel)` base. Genuine FHIR camelCase shape using the shared datatypes in `app/schemas/fhir_input/` (`FhirIdentifierInput`, `FhirHumanNameInput`, `FhirAddressInput`, `FhirContactPointInput`, `FhirCodeableConceptInput`, `FhirReferenceInput`, `FhirPeriodInput`, `FhirAttachmentInput`). Add a missing datatype there, once, for everyone. `extra="ignore"` — the **raw body**, not this model, is what is validated and stored; these models exist to document the request in OpenAPI and type required-binding codes as enums. Add `input/<backbone>.py` per BackboneElement (e.g. Practitioner's qualification). Tenant/audit fields are never in the body.
- `response/core.py` — `FHIR<Resource>Schema`, `FHIR<Resource>BundleEntry`, `FHIR<Resource>Bundle` (searchset: `total`, `link`, `entry[].search`); `response/<backbone>.py` as needed. Reuse `app.schemas.datatypes.FHIR*`. There is **no** `Plain*` / `Paginated*` schema.
- `__init__.py` at each level re-exporting.

### D. Mapper — `app/fhir/mappers/<resource>/`
- `fhir.py` — `to_fhir_<resource>(row)` is one line: `content_resource("<Resource>", row.<resource>_id, row)` (`app/fhir/mappers/content.py`)
- `__init__.py` — export it
- **No `plain.py`, no `payload.py`** — the body is already FHIR.

### E. Repository — `app/repository/<resource>/`
- `_indexer.py` — `index_columns(document)`, `index_rows(document)` → `{relationship: [rows]}`, `INDEX_RELATIONSHIPS`, plus reference collectors. Compose the builders in `app/repository/_content_index.py` (`identifier_rows`, `type_rows`, `endpoint_row`, `reference_columns`, `strings`, `norms`, `relative`). This is the only place that knows how a document maps to the index.
- `search.py` — `<resource>_search()` (`@cache`) returning a `SearchRegistry`: one `SearchParam(name, type, description, expression, match, present, modifiers, sort=..., targets/chain/hierarchy for references)` per parameter, plus `summary_elements` (the Σ elements from the R4 page), `includes`/`revincludes` (`IncludeTarget`), `default_sort`, and `_register_kind()` (a `ResourceKind` so the engine can render the resource and build `fullUrl`s). Builders to reuse from `app/fhir/search/sql.py`: `string_match`, `array_string_match`, `token_match`, `token_condition`, `coded_token_match`, `token_text_match`, `date_match`, `reference_match`, `reference_target`, `earliest`, `ArrayAggregate`. Every condition reads **only index columns** and EXISTS-correlates child tables to the main row.
- `core.py` — `get_by_<resource>_id`, `get_by_<resource>_id_in_org`, `<resource>_belongs_to_org`, `search(request, ctx, ...)` (calls `execute_search(...)`; `extra_conditions=` ANDs a non-parameter scope such as `/me`'s `user_id`), `delete`.
- `full.py` — `create_full(document, org_id, created_by)` and `patch_full(<resource>_id, document, updated_by)`: existence-check local references (scoped to the tenant; 422 if missing), store `content=_storable(document)`, set `**index_columns(...)`, `**index_rows(...)`; patch eager-loads the index relationships (`_with_relationships`) and replaces them all. Set `updated_by` explicitly. Resource-specific business rules live here (Organization's partOf cycle check).
- `_shared.py` — `_with_relationships` (re-export the `_reference_shared` helpers you use) and any hierarchy helper.
- `__init__.py` — `<Resource>Repository(_CoreMixin, _FullMixin, BaseRepository)`.

### F. Service — `app/services/<resource>/`
- `core.py` — `get_<resource>_scoped` (403 org-less, 404 cross-org), `search_<resource>s(query, org_id, strict=, fhir_base=)` (`parse_search(...)` → `SearchContext` → repository), `create_<resource>(payload, org_id, created_by, body=)`, `patch_<resource>(...)`, `delete_<resource>`, `_to_fhir`, `_raw`, `_validate_base_r4`, `_log_org_scope_miss`.
  - create: `document = fhir_create_document(raw_body, "<Resource>")` → `_validate_base_r4` → `repository.create_full`
  - patch: load current row → `fragment, touched = fhir_patch_fragment(raw_body)` → `merged = merge_patch_fragment(to_fhir_<resource>(existing), fragment, touched)` → validate `merged` → `repository.patch_full(id, merged, updated_by)`. Merge-patch on top-level elements; a supplied element replaces wholesale, `null`/`[]` clears.
  - Anything that is not a FHIR element but is part of the record (Practitioner's `user_id`, the IAM user it is linked to) never goes in the body or `content`. It is a column set by its own permission-gated call (`PUT/DELETE /<resources>/{id}/user`, scope `<resource>:link`), exactly like Medplum's ProjectMembership link. See Practitioner (`link_user`/`unlink_user`) for the pattern. A resource a person can create for themselves (Patient) also takes `?link_me=true` on create, which links the new record to the caller's JWT `sub` (self-signup, needs only `<resource>:create`); see Patient's `create_patient(link_user_id=...)`.
- `__init__.py` — `<Resource>Service(_CoreMixin)`.

### G. DI — `app/di/modules/<resource>.py`, `app/di/dependencies/<resource>.py`, wired in `app/di/container.py`
Same three lines as Organization.

### H. Router — `app/routers/<resource>/`
- `_responses.py` — `_CONTENT_NEG`, `_ERR_*`, `_SINGLE_200/201`, `_LIST_200` (FHIR content type only, `inline_schema(...)`)
- `core.py` — `APIRouter(default_response_class=FHIRJSONResponse, dependencies=[Depends(require_fhir_json)], ...)`. Routes: `POST /`, `GET /` (search), `POST /_search`, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}` (and `GET /me` **before** `/{id}` if the resource is end-user scoped). Search routes read the raw query (`get_query`/`post_query`), pass `strict_handling(request)`, and answer with `searchset_response(...)`; the OpenAPI parameters come from `search_parameters(registry, ...)`. Every route: `require_permission("<resource>", "create|read|update|delete")`, `actor.org_id` / `actor.sub`, an explicit `logger.info(... "route.<operation_id>")`, `operation_id`/`summary`/`description`/`responses=`. Create returns `fhir_response(..., status_code=201)`. Never `response_model=`.
- `__init__.py` — `APIRouter(prefix="/<resources>", tags=["<Resources>"])`.
- `app/routers/__init__.py` — `from . import <resource> as <resource>` + `__all__` entry.
- `app/core/openapi_tags.py` — add the tag.

### I. Shared registrations
- `app/core/reference_resolver.py` — add `"<Resource>": (<Resource>Model, "<resource>_id")` to `RESOURCE_REGISTRY` (otherwise nothing can reference it).
  - **If already-rebuilt resources hold references to it** (Endpoint did: `Organization.endpoint`, `Location.endpoint`, `HealthcareService.endpoint`), wire them in the same change: add the relative-reference existence check to their `full.py`/`_indexer.py`, replace their "accepted, adds nothing" `IncludeTarget` with a real fetch, add the reverse `_revinclude` on the new resource, and update the existing tests that referenced a nonexistent id (seed the row with `tests/helpers/seed.py`).
- `app/fhir/capability.py` — add one line to `SEARCH_REGISTRIES` so `/metadata` lists it; add it to the `expected` map in `tests/integration/capability/test_metadata.py`.
- `configs/config.yaml` — append the name to `routes.enabled` once it is ready (an unlisted router is not mounted and every test against it 404s).
- `CLAUDE.md` — sequence-allocation table; the Medplum-style section (one paragraph: what is indexed, any end-user link, includes).
- `docs/search-architecture/pending-search-capabilities.md` — scope + parameter tables.

### J. Tests — `tests/` (see `/add-resource-tests`)
`tests/integration/<resource>/{__init__,conftest,support,test_core,test_search}.py`, `tests/conformance/test_<resource>_fhir.py`, and `assert_fhir_<resource>` in `tests/helpers/assertions.py`.

---

## Phase 3 — Verify

```bash
uv run python -c "import app.main"                       # imports + DI wiring
uv run pytest tests/integration/<resource> tests/conformance/test_<resource>_fhir.py tests/integration/capability -q
```
- Open `/openapi.json`: the search parameters must be listed on `GET /` and `POST /_search`, the create body must show the FHIR shape, and there must be no duplicate-operation-id warnings (`warnings.simplefilter("error")` while calling `app.openapi()` finds them).
- `GET /api/fhir/v1/metadata` lists the resource with every search parameter.
- `configs/config.yaml`'s `fhir_validation.enabled` can be `false` locally, which skips base validation entirely, so never rely on it being on. Tests that assert "non-FHIR key → 422" must switch the native validator on themselves (a `native_validation` monkeypatch fixture, as in `tests/integration/practitioner/test_core.py`).
- Migration: verified on a scratch DB as described in B.

---

## Phase G — fhir-gql half (after the fhir-server resources, when asked)

In `D:\code\work\projects\fhir-gql`, mirror an existing resource's package. fhir-server is FHIR-only now, so the `internal` connector's translators are thin.
- `app/fhir/schemas/<resource>.py` — `Fhir<Resource>Response` / `Fhir<Resource>Input` Pydantic models.
- Translators for **both** connectors, registered in `app/connectors/translator_registry.py`: `app/connectors/internal/translators/<resource>.py` and `app/connectors/medplum/translators/<resource>.py` (Medplum's PATCH needs an RFC 6902 array via `to_json_patch`).
- `app/gql/<resource>/types/{response,input}.py` (any `dict` field needs an explicit `JSON` override), `queries.py`, `mutations.py`, wired into `app/gql/schema.py`.
- Exercise create/get/search/update/delete on **both** connectors; an import that compiles is not a working connector.

---

## Files added for one new resource (summary)

```
app/models/<r>/            core.py  <index child>.py ×N  enums.py?  __init__.py
migrations/versions/       <rev>_<r>_content_jsonb_and_search_index.py        (+ migrations/env.py import)
app/schemas/<r>/           __init__.py  input/{core,<backbone>?,__init__}.py  response/{core,<backbone>?,__init__}.py
app/schemas/fhir_input/    <datatype>.py  (only if a datatype is missing)
app/fhir/mappers/<r>/      __init__.py  fhir.py
app/repository/<r>/        __init__.py  _shared.py  _indexer.py  search.py  core.py  full.py
app/services/<r>/          __init__.py  core.py
app/di/modules/<r>.py      app/di/dependencies/<r>.py            (+ app/di/container.py)
app/routers/<r>/           __init__.py  _responses.py  core.py   (+ app/routers/__init__.py)
tests/integration/<r>/     __init__.py  conftest.py  support.py  test_core.py  test_search.py
tests/conformance/         test_<r>_fhir.py                      (+ tests/helpers/assertions.py)
```
Edited, not created: `app/core/reference_resolver.py`, `app/fhir/capability.py`, `app/core/openapi_tags.py`, `configs/config.yaml`, `tests/integration/capability/test_metadata.py`, `CLAUDE.md`, `docs/search-architecture/pending-search-capabilities.md`. Only if the resource needs a search type the engine lacks: `app/fhir/search/sql.py`, `values.py`, `params.py`.
