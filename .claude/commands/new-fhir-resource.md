# Add a New FHIR Resource

Complete step-by-step checklist for adding a new FHIR R4 resource to this server.

**Before starting:** run `/fhir-db-model` with the R4 spec URL to design the ORM model, enums, and migration first.

**This skill covers the fhir-server half only.** Per CLAUDE.md's "What 'End-to-End' Means" — a resource isn't end-to-end complete until the fhir-gql gateway (`D:\code\work\projects\fhir-gql`, sibling repo) can serve it too, on **both** connectors (`internal` and `medplum`), not just one. Step 18 below covers that half; don't skip it or treat it as a separate follow-up task.

## ARGUMENTS: $RESOURCE

Steps use `$RESOURCE` = the resource name (e.g. `Observation`, `Claim`). Adjust paths accordingly.

---

## Checklist

1. **Model** — `app/models/<resource>/<resource>.py` (+ one file per sub-resource once there are several — Organization/Location/HealthcareService all do `core.py` + `<sub>.py` + `__init__.py`)
   - `id` (internal, `BigInteger` PK, never exposed) + public `<resource>_id` (`BigInteger`, via a `Sequence("<resource>_pub_seq", start=<block>, increment=1, metadata=Base.metadata)` — not `<resource>_id_seq`; next available block from CLAUDE.md)
   - Mix in `TenantAuditMixin` (`app/models/shared/`) for `tenant_id`/`created_by`(NOT NULL)/`updated_by`/`created_at`/`updated_at` — don't hand-declare these. Add a plain `user_id = Column(String, nullable=True, index=True)` alongside it unless this resource is getting the auth-rollout treatment (see step 14a) — see `/fhir-db-model`'s Step 5 for the full reasoning, including why there's no live non-auth example to copy from today.
   - Every CodeableConcept's `coding[]` (0..1 or 0..*) is a dedicated child/grandchild table built from `FhirCodingMixin`, never flattened columns. Every Address/ContactPoint 0..1 use `FhirAddressMixin`/`FhirContactPointMixin` instead of hand-declared columns — prefixed when sharing a row with other field groups, but mixed in regardless even when it's the only datatype group on that table (never hand-roll just because there's nothing to prefix against). Every Reference field gets all **four** flattened columns (`_reference`/`_type`/`_id`/`_display`), not three. Nullability matches the real FHIR cardinality — never a stricter-than-spec `NOT NULL`. Every resource's main table also gets a mandatory `extension` JSONB column (inherited from base `DomainResource`, not resource-specific — see `/fhir-db-model` Step 4a). See `/fhir-db-model` Steps 2, 3, 4a, and 5.
   - Child tables mix in `TenantAuditMixin` too; FK to the **main** resource table is named `<resource>_pk` (not `<resource>_id` — would collide with the public sequence column); a grandchild's FK to its immediate parent child table is ordinary `<parent_table>_id`.
   - Child tables with `cascade="all, delete-orphan"` on parent side

2. **Enums** — `app/models/<resource>/enums.py`

3. **`__init__.py`** — `app/models/<resource>/__init__.py` — export all model classes

4. **Register in migrations** — add `import app.models.<resource>.<resource>  # noqa: F401` to `migrations/env.py`

5. **Migration** — `uv run alembic revision --autogenerate -m "add_<resource>_tables"` then manually fix:
   - Autogenerate emits `sa.Enum('VALUE1', ...)` using Python member names — **keep those values as-is**. For reference type enums they are `UPPERCASE_SNAKE` (e.g. `'PRACTITIONER_ROLE'`); for status enums they are `lowercase`. Both are correct — never change them to TitleCase.
   - Replace `sa.Enum(...)` with module-level `postgresql.ENUM('VALUE1', ..., name='pg_type_name')` + `.create(bind, checkfirst=True)` in `upgrade()`
   - Add `op.execute("CREATE SEQUENCE IF NOT EXISTS <resource>_pub_seq START WITH <N> INCREMENT BY 1")` — matches the model's own `Sequence("<resource>_pub_seq", ...)` name (confirmed: `organization_pub_seq`, `location_pub_seq`, `healthcare_service_pub_seq`); autogenerate itself emits a batch of false-positive `CREATE/DROP SEQUENCE IF EXISTS` lines for this sequence — a known Alembic quirk, strip them rather than keep duplicates
   - `organization_reference_type` — always `create_type=False`, never create/drop (shared type)
   - `downgrade()`: drop tables in reverse FK order, drop sequence, drop new enum types (not shared ones)
   - Apply: `uv run alembic upgrade head`

6. **Input Schemas** — `app/schemas/<resource>/input.py`
   - `<Resource>CreateSchema` — `extra="forbid"`, `json_schema_extra` with complete example including `user_id`, `tenant_id` (not `org_id` — the model column, and the input field name that mirrors it, are `tenant_id` for any resource built against `TenantAuditMixin`; `org_id` is only the name on resources that predate the rename and haven't been reworked yet — see `/fhir-db-model` Step 5), and `created_by` (required — `TenantAuditMixin.created_by` is `NOT NULL`, whatever the source)
   - Every CodeableConcept-coding field is `list[CodingInput]`, importing the shared `CodingInput` from `app.schemas.datatypes` — never redeclare a resource-prefixed copy (`<Resource>CodingInput`). Likewise reuse `ContactPointInput`/`AuditFields`/`PlainCodingRow`/`PlainContactPointRow` from the same package wherever the shape matches exactly; only subclass to override a field (e.g. making `system`/`value` required) — see `app/schemas/datatypes/__init__.py` for the full list.
   - `<Resource>PatchSchema` — all optional; exclude immutable fields
   - If the resource has many sub-resources and this file grows large, split it into an `input/` package instead (`core.py` + one file per sub-resource + `__init__.py`) — see `/split-resource-package`. Organization/Location/HealthcareService all do this (Patient/Practitioner/PractitionerRole/Schedule/Slot did too, before they were removed from this codebase — see CLAUDE.md's current resource list before assuming they still exist).

7. **FHIR Response Schemas** — `app/schemas/<resource>/response.py`
   - `FHIR<Resource>Schema` (camelCase + `resourceType`, plus `meta: FHIRMeta | None` — see `app/schemas/datatypes/meta.py` and each reworked resource's mapper `_fhir_meta()` helper for the `lastUpdated`/`created-by`/etc. extension pattern)
   - `Plain<Resource>Response` (snake_case)
   - `Paginated<Resource>Response` (wraps plain with `total`, `limit`, `offset`, `data[]`)
   - `FHIR<Resource>Bundle` (FHIR Bundle with `entry[]`)
   - Reuse `app.schemas.datatypes`' shared FHIR types (`FHIRCoding`, `FHIRAddress`, `FHIRIdentifier`, `FHIRContactPoint`, `FHIRHumanName`, `FHIRReference`, `FHIRMeta`, `FHIRBundle`/`FHIRBundleEntry`) and their plain-row counterparts (`AuditFields`, `PlainCodingRow`, `PlainContactPointRow`) rather than redeclaring resource-prefixed copies — there is no `app/schemas/fhir/` or `app/schemas/common/` package; it's `app/schemas/datatypes/`
   - Export from `app/schemas/<resource>/__init__.py` — the router imports response schemas directly from `app/schemas/<resource>/response.py` (or the `__init__.py`), never through a shared aggregator
   - Same split option as input.py — see `/split-resource-package` — Organization/Location/HealthcareService all split `response.py` this way

8. **Mapper** — `app/fhir/mappers/<resource>/` package
   - `fhir.py` — per-child-model FHIR builder functions + `to_fhir_<resource>()` orchestrator
     - Import shared types from `app.fhir.datatypes` (the mapper-helper module — distinct from the `app.schemas.datatypes` Pydantic package used in steps 6/7): `fhir_human_name`, `fhir_identifier`, `fhir_telecom`, `fhir_address`, `fhir_photo`, `fhir_communication`, `fhir_enum`, `fhir_split`, `fhir_instant` (renders a datetime as a tz-safe FHIR instant/dateTime — use it for every `meta.lastUpdated` and any `created-at`-style extension; SQLite in tests doesn't preserve tzinfo on naive datetimes, which otherwise fails FHIR validation with a missing-offset error)
     - A local `_fhir_coding_list(codings)` + `_fhir_meta(model)` helper (see Organization/Location/HealthcareService's own `fhir.py`) for the promoted coding-table rendering and `meta.lastUpdated`/`extension` block
     - `to_fhir_<resource>`: `"id": str(model.<resource>_id)`, strip None at end
   - `plain.py` — per-child-model plain/snake_case builder functions + `to_plain_<resource>()` orchestrator
     - Import shared types from `app.fhir.datatypes`: `plain_name`, `plain_identifier`, `plain_telecom`, `plain_address`, `plain_photo`, `plain_communication`, `fhir_enum`, `fhir_split`
     - `to_plain_<resource>`: `"id": model.<resource>_id` as int
   - `payload.py` — **mandatory, not optional** — `fhir.py`'s mirror image: the same builders, field-for-field, but reading the *validated Pydantic input schema* (pre-insert) instead of the ORM model (post-insert), so the result can be validated before anything is written. A Reference field here only has the raw `{prefix}` string the caller submitted (no resolved `{prefix}_type`/`{prefix}_id` yet) — its own `_reference_from_payload(obj, prefix)` reads `getattr(obj, prefix)` directly. Exports `payload_to_fhir_<resource>(create_schema) -> dict` (full conversion, every field present) and `patch_fragment_to_fhir_<resource>(patch_schema) -> tuple[dict, set[str]]` (tri-state, via `payload.model_fields_set` — only touched FHIR keys, plus that key set). Re-export `merge_patch_fragment` from `app.fhir.datatypes` (shared, resource-agnostic — don't redeclare it) alongside these two. See CLAUDE.md's "Base R4 Validation" section for the full pattern and the exact service-layer wiring — this is mandatory for every resource, same as Organization/Location/HealthcareService/Practitioner.
   - `__init__.py` — re-export all public functions from `fhir.py`, `plain.py`, **and `payload.py`** (plus `merge_patch_fragment`)
   - Any child-model helper exported from `__init__.py` is also imported directly by the router's sub-resource GET routes (zero inline dicts in router)

9. **Repository** — `app/repository/<resource>_repository.py` (or `app/repository/<resource>/` package — `core.py`/`_shared.py`/`full.py` or per-sub-resource mixins, see Organization/Location/HealthcareService)
   - `_with_relationships(stmt)` — `selectinload` for every child relationship
   - `_apply_list_filters(stmt, user_id, tenant_id, ...)` — build it from the shared, resource-agnostic helpers in `app/core/filters.py` (`apply_child_exists_filter`, `apply_token_filter`, `parse_reference`) rather than hand-writing the same `.where()`/EXISTS-subquery/Reference-parsing patterns again; `app/core/pagination.py`'s `resolve_sort` (sort-string → column) and `ListParams` (the `Depends()`-based limit/offset/sort query-param dependency) cover the rest of `list()`'s signature
   - Any 0..1 or 0..* `Reference(Organization)` field with an identifier fallback (e.g. `identifier.assigner`, `qualification.issuer`) — build its write-side kwargs from `app/repository/_reference_shared.py`'s `_parse_org_ref`/`_org_ref_kwargs`/`_reference_kwargs`/`_validate_reference` (re-exported from the resource's own `_shared.py`) instead of re-deriving the same reference-parsing/identifier-fallback/existence-check logic per resource — it was extracted from Patient specifically so new resources (this one included) can reuse it
   - Methods: `get_by_<resource>_id()`, `get_me()`, `list()`, `create()`, `patch()`, `delete()`
   - `get_me()` calls `_apply_list_filters()` with `user_id`/`tenant_id` always set
   - Session-per-operation: `async with self.session_factory() as session:`
   - Once this file gets large (many sub-resource CRUD methods), split into `app/repository/<resource>/` — see `/split-resource-package`

10. **Service** — `app/services/<resource>_service.py`
    - `_to_fhir(model)` and `_to_plain(model)` wrappers around the mapper
    - `get_raw_by_<resource>_id()` — for auth dep (no relationships needed)
    - `get_me()`, `list_<resource>s()`, `create_<resource>()`, `patch_<resource>()`, `delete_<resource>()`
    - **`_validate_base_r4(fhir_resource, org_id=None)` — mandatory, not optional.** A thin `@staticmethod` wrapper calling `app.fhir.validation.validate_resource("<Resource>", fhir_resource, org_id=org_id)` and raising `FhirValidationError` on any returned error — identical shape on every resource, just the resource-type string literal changes. `create_<resource>()` calls it with `payload_to_fhir_<resource>(payload)` before `repository.create_full(...)`. `patch_<resource>()` fetches the current full row first (`get_by_<resource>_id_in_org`, not just an existence check), builds `fragment, touched = patch_fragment_to_fhir_<resource>(payload)`, merges with `merge_patch_fragment(to_fhir_<resource>(existing), fragment, touched)`, and validates *that* before `repository.patch_full(...)`. See CLAUDE.md's "Base R4 Validation" section for the exact code shape — copy it from any of the four resources that already have it (Organization's is the original).
    - Same split option as the repository — see `/split-resource-package`

11. **DI Module** — `app/di/modules/<resource>.py`
    ```python
    class <Resource>Container(containers.DeclarativeContainer):
        core = providers.DependenciesContainer()
        <resource>_repository = providers.Factory(<Resource>Repository, session_factory=core.database.provided.session)
        <resource>_service = providers.Factory(<Resource>Service, repository=<resource>_repository)
    ```

12. **DI Dependency** — `app/di/dependencies/<resource>.py`
    ```python
    @inject
    def get_<resource>_service(
        service: <Resource>Service = Depends(Provide[Container.<resource>.<resource>_service]),
    ) -> <Resource>Service:
        return service
    ```

13. **Wire container** — `app/di/container.py`
    - `<resource> = providers.Container(<Resource>Container, core=core)`

14. **Auth** — a new resource is built with direct JWT/RBAC auth **by default now** — every currently-built resource in this codebase already has this (see CLAUDE.md's "Multi-Tenancy & Ownership"), so there's no separate `app/deps/<resource>_deps.py`/`resolve_<resource>()` dependency to write at all. Instead:
    - Service layer gets `get_<resource>_scoped(resource_id, org_id)` — raises `PermissionDeniedError` (403) for a missing `org_id`, else `NotFoundError` (404, never 403) if the resource doesn't exist or belongs to a different org
    - Repository gets `get_by_<resource>_id_in_org(resource_id, org_id)` and `<resource>_belongs_to_org(resource_id, org_id) -> bool`
    - `create_full()`/`patch_full()` take `org_id`/`created_by`/`updated_by` as **explicit parameters**, never read off the payload — `<Resource>CreateSchema`/`PatchSchema` don't declare `tenant_id`/`org_id`/`created_by`/`updated_by` fields at all (`user_id`, where this resource has one, is unaffected and stays a plain input field)
    - `patch_full()` must explicitly set `model.updated_by = updated_by` on the main row — the generic field-by-field PATCH loop only touches fields still present in the schema, and `updated_by` isn't one of them

    **14a. Exception — resource should skip RBAC and use the old plain pattern.** Only if explicitly told this specific resource should NOT have RBAC (a deliberate, rare deviation now, the mirror image of how this used to be the default) — use the plain `resolve_<resource>()` dependency instead (`app/deps/<resource>_deps.py`, loads by public ID, 404 if missing, no ownership check; recreate the `app/deps/` folder if it doesn't exist). Reads `user_id`/`tenant_id`/`created_by`/`updated_by` straight off the validated request body instead of a verified token. If you ever actually do this, say so explicitly in CLAUDE.md's "Multi-Tenancy & Ownership" — don't let "every resource" silently become false there without updating it.

15. **Router** — `app/routers/<resource>.py` (or `app/routers/<resource>/` package — `core.py` + `_responses.py` holding the `_SINGLE_200`/etc. constants, see any existing resource for the template)
    - Module-level constants: `_SINGLE_200`, `_SINGLE_201`, `_LIST_200` using `inline_schema()`
    - Route order: `POST /`, `GET /me`, `GET /{id}`, `PATCH /{id}`, `GET /`, `DELETE /{id}`
    - `/me` **must** come before `/{id}` to prevent FastAPI treating `me` as a path param. Omit `/me` entirely only if this resource has no `user_id` at all (Organization/Location/HealthcareService/PractitionerRole/Schedule/Slot/Appointment/AppointmentResponse/Encounter dropped it for that reason; a resource that keeps `user_id` keeps `/me`, see step 1).
    - **Every route takes `actor: AuthUser = Depends(require_permission("<resource>", "create|read|update|delete"))`** (`app/auth/rbac.py`) instead of a bare `Depends(get_current_user)` or a `resolve_<resource>` dependency — `org_id` comes from `actor.org_id`, `created_by`/`updated_by` from `actor.sub`. Drop any `tenant_id`/`user_id` *filter* query params from `GET /` and `GET /me` — org scoping is derived from the token, not client-suppliable; `user_id` scoping (where this resource has one) only happens via `/me`'s own `actor.sub`. Only skip all of this if step 14a's exception applies.
    - If `status` is a query param, rename to `<res>_status` with `alias="status"` to avoid shadowing `fastapi.status`
    - Never use `response_model=` — use inline `responses=` with `inline_schema()` only
    - **Sub-resource GET + DELETE routes** (for every `0..*` child table — names, identifiers, telecom, etc.):
      - Add `<Resource><Sub>ListItem` (plain sub-schema + `id: int`) and `<Resource><Sub>ListResponse` to `response.py` (or the sub-resource's own file if split), export from `app/schemas/<resource>/__init__.py`
      - Add module-level `_SUBRES_<SUB>_200` constant using `inline_schema()` — `application/json` only (no `application/fhir+json`)
      - `GET /{resource_id}/<sub>` → `JSONResponse({"data": [...with id...], "total": N})`
      - `DELETE /{resource_id}/<sub>/{id}` → 204 No Content; repository verifies `child.<resource>_id == parent.id` before deleting
      - See CLAUDE.md "Sub-Resource GET + DELETE Endpoints" for the full pattern
    - Once this file gets large (many sub-resource routes), split into `app/routers/<resource>/` — see `/split-resource-package`

16. **Register router** — `app/routers/__init__.py`
    - Give the resource's `router = APIRouter()` a `prefix=`/`tags=` at construction: `APIRouter(prefix="/<resources>", tags=["<Resources>"])`
    - Add `from . import <resource> as <resource>` to the import block + the sorted `__all__` list — `discover_routers()` introspects this namespace for modules exposing `router: APIRouter`, so no separate prefix/tag table to update
    - Do **not** add the resource to `configs/config.yaml`'s `routes.enabled` list yet — leave it unlisted (disabled) until the resource is ready to expose, then append its name — see CLAUDE.md's "Enabling/Disabling Resources"

17. **Update CLAUDE.md** — add the new resource to the sequence allocation table

18. **fhir-gql half — the other repo, not optional.** In `D:\code\work\projects\fhir-gql`, mirror an existing resource's package (Organization's is the reference; Organization's own `app/gql/organization` module docstrings explain the pattern in full):
    - `app/fhir/schemas/<resource>.py` — canonical FHIR-shaped `Fhir<Resource>Response`/`Fhir<Resource>Input` Pydantic models. Any field whose value is a raw `dict` (e.g. `extension`) still gets typed as `list[dict] | None` here — the GraphQL-scalar override happens one layer up, in the type files below, not here.
    - **Both connectors, always:**
      - `app/connectors/internal/translators/<resource>.py` — translates to/from fhir-server's own flattened REST conventions (`to_wire_create`/`to_wire_patch` emit the plain partial-fields dict fhir-server's PATCH expects)
      - `app/connectors/medplum/translators/<resource>.py` — translates to/from genuine FHIR R4 wire format. **`to_wire_patch()` must return an RFC 6902 JSON Patch array via `app.connectors.medplum.json_patch.to_json_patch(data)`, never a plain resource dict** — Medplum's PATCH rejects a plain body outright with `400 Invalid patch body`, and this was silently wrong for every one of the 7 existing resources until caught by actually calling `updateFhirX` against a live Medplum instance, not by reading the code
      - Register both in `app/connectors/translator_registry.py`: a `<RESOURCE>_TRANSLATORS = {"internal": ..., "medplum": ...}` dict + `active_<resource>_translator()` function
    - `app/gql/<resource>/types/response.py` and `types/input.py` — `@strawberry.experimental.pydantic.type`/`.input` with `all_fields=True`, built from the Pydantic models in the first bullet. **Any field that isn't a native GraphQL scalar needs an explicit override in the class body** — `extension: JSON | None` (response) / `extension: JSON | None = None` (input), importing `from strawberry.scalars import JSON`. `all_fields=True` does not handle this on its own; the schema fails to build (`TypeError: ... fields cannot be resolved. Unexpected type '<class 'dict'>'`) without it.
    - `app/gql/<resource>/queries.py` (`getFhir<Resource>`, `getFhir<Resource>s`) and `mutations.py` (`createFhir<Resource>`, `updateFhir<Resource>`, `deleteFhir<Resource>`) — call `active_<resource>_translator()`, never a hardcoded connector
    - Wire the new `Fhir<Resource>Query`/`Fhir<Resource>Mutation` mixins into the root `Query`/`Mutation` in `app/gql/schema.py`

## Verify

```bash
uv run python -c "from app.models.<resource> import *; print('OK')"
uv run fastapi dev app/main.py
# Check http://localhost:8000/openapi.json — confirm all fields in request + response schemas
```

**Then verify the fhir-gql half, on BOTH connectors — don't stop at step 18 compiling/importing cleanly:**

```bash
# In fhir-gql:
uv run python -c "import app.gql.schema; print('schema builds OK')"
```

Actually exercise `createFhir<Resource>`/`getFhir<Resource>`/`getFhir<Resource>s`/`updateFhir<Resource>`/`deleteFhir<Resource>` with `connectors.active: internal`, then again with `connectors.active: medplum` (`configs/config.yaml`, or override at runtime for a test). A connector can look correct by code inspection and still be broken in practice — code review alone did not catch the Medplum JSON-Patch bug above; only actually calling the mutation against a live Medplum instance did.
