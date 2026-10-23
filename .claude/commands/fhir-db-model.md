# FHIR DB Model Designer

You are designing a SQLAlchemy ORM model for a **FHIR R4** resource in this project. Follow every rule below without deviation.

## Step 1 — Fetch the R4 spec first

The user will provide a FHIR resource name or URL. **Always fetch the R4 spec before doing anything else** — use `https://www.hl7.org/fhir/R4/<resource>.html`. Never use `https://www.hl7.org/fhir/<resource>.html` (that serves R5). Read the full element definition table — every field, cardinality, and type. Then fetch and read the R4 spec page for every named datatype used (Annotation, CodeableConcept, Timing, Dosage, Identifier, etc). Never model from memory. Note: `CodeableReference` does **not exist** in R4 — if you see it, you are reading R5.

## Step 2 — Map cardinality to storage

| FHIR cardinality | Storage |
|---|---|
| `1..1` or `0..1` | Flat columns on the main model table |
| `0..*` | Separate child table + one-to-many relationship |

Never put a `0..*` field in a single column. The default for a `0..*` *scalar* list that's embedded in a bigger row (not its own child table) is a real Postgres `ARRAY(String)` column — confirmed in the reworked resources: `HumanName.given[]`/`prefix[]`/`suffix[]` (`FhirAddressMixin`'s sibling, the flattened `name_*` group — see `app/models/organization/contact.py`) and `Address.line[]` (`FhirAddressMixin` itself, `app/models/shared/datatypes/fhir_address.py`) are both `ARRAY(String)`, not comma-separated Text — the project moved off comma-text for these specifically because array membership needs to stay queryable/structured. The one confirmed remaining comma-separated-Text exception is `daysOfWeek[]` (`LocationHoursOfOperation`/`HealthcareServiceAvailableTime.days_of_week`) — never filtered individually, so a real array (or a child table) buys nothing. `instantiatesCanonical[]`/`instantiatesUri[]` have no live example in the current codebase to confirm against; default to `ARRAY(String)` for these too unless you find a concrete reason not to.

## Step 3 — Apply type-specific storage rules

### Primitive (`string`, `boolean`, `dateTime`, `integer`, `decimal`, `uri`, `code`)
→ Single flat column with matching SQLAlchemy type.

### CodeableConcept (0..1) and CodeableConcept[] (0..*) — same rule either way
`coding[]` is **always** real 0..* per spec, even when the CodeableConcept that owns it is 0..1 — a deployment routinely needs its own custom code for a concept *and* a crosswalk to a standard terminology (e.g. SNOMED CT) on the same concept at once. So **always promote `coding[]` to its own dedicated child table** (one row per `Coding`, via the shared `FhirCodingMixin` — see "Shared mixins" below), regardless of the CodeableConcept's own cardinality. Confirmed live in every reworked resource: `Organization.type`/`.identifier.type`/`.contact.purpose`, `Location.type`/`.identifier.type`/`.physicalType`, `HealthcareService.category`/`.type`/`.specialty`/etc.

- If the CodeableConcept itself is **0..1** (e.g. `Location.physicalType`): the CC's own `text` field is a flat column on whichever table already hosts that field (main table, or the CC's parent BackboneElement/child table) — e.g. `physical_type_text` on `LocationModel` — and `coding[]` is a **new sibling child table** (e.g. `LocationPhysicalTypeCoding`) FK'd to that same table.
- If the CodeableConcept itself is **0..*** (e.g. `Organization.type`): it already needs its own child table for the CC rows (`text` lives there), and `coding[]` becomes a **grandchild** table FK'd to that child table (e.g. `OrganizationType.text` + `OrganizationTypeCoding` FK'd to `organization_type.id`).

`FhirCodingMixin` provides `system`/`version`/`code`/`display`/`user_selected` (all nullable). Never hand-write these five columns — mix it in.

### Reference (0..1 or 0..*) — the pattern to use for new work
Flattened columns, **no `ForeignKey`, no relationship**: `<field>_type` (Enum if closed-set, String if open) + `<field>_id` + `<field>_display` (String) — for 0..* wrap the same three in a child table (fixed column names `reference_type`/`reference_id`/`reference_display`, regardless of the FHIR field name — e.g. `Encounter.participant.actor` lives on `encounter_participant.reference_type`/`.reference_id`/`.reference_display`, not `actor_type`/etc.; use the field-specific prefix only for a flat 0..1 column on the main table).

**`<field>_id` stores the target's PUBLIC `<resource>_id` value — never the internal PK — and there is deliberately no FK column at all.** The target table varies per row by `<field>_type`, so a real FK is impossible for a genuinely polymorphic reference, and this project applies the same no-FK/public-ID shape uniformly even to references whose allowed type happens to be a single, fixed resource (e.g. every `*_organization_id`/`partof_id`/`assigner_id` in `app/models/organization/core.py` and `identifier.py`) — one pattern for every cross-resource reference, rather than real FKs for the single-target cases and flattened columns for the rest. Existence is checked at **write time**, not via a DB constraint, by `ensure_resource_exists()` (`app/core/reference_resolver.py`) against `RESOURCE_REGISTRY` — register the target type there or every reference to it is rejected. The mapper emits `f"{type}/{id}"` directly off the stored public id (no relationship to navigate). Even when only **one resource type** is allowed, still use a single-value Enum for `<field>_type` (never a bare Integer column) — keeps the pattern uniform and the allowed type self-documenting.

A *legacy* convention exists on resources that predate this rework (see CLAUDE.md's "FHIR DB Model Design" section): a real `ForeignKey("resource.id")` storing the **internal** PK, `index=True` + `lazy="selectin"` relationship, mapper reads the public id back through the relationship. **Do not use this for new work** — it's kept only because it's still live on not-yet-reworked resources, and it is *not* what "Reference (0..1 or 0..*)" above describes.

### CodeableReference (0..1 or 0..*) — R5
Not used in R4 (see Reminders) — if you ever do need it, both halves live on the same row, with the concept half following the CodeableConcept rule above (flat `text` + a sibling/grandchild `coding[]` table via `FhirCodingMixin`) and the reference half following the Reference rule above (`reference_type`/`reference_id`/`reference_display`, no FK).

### Annotation (0..*)
→ Child table with: `text` (Text, NOT NULL), `time` (DateTime), `author_string` (String), `author_reference_type` (Enum or String), `author_reference_id` (Integer, public id, no FK), `author_reference_display` (String).

### Identifier (0..*)
→ Child table with: `use`, `type_text`, `system`, `value`, `period_start`, `period_end`, plus the `assigner` Reference's flattened columns (`assigner_reference`, `assigner_type`/`assigner_id`/`assigner_display`, and its own `assigner_identifier_*` logical-reference fallback — see `app/models/organization/identifier.py`). `type` is a CodeableConcept — `type_text` stays flat here, but `type`'s `coding[]` is a **grandchild** table (`FhirCodingMixin`) FK'd to this Identifier child table, per the CodeableConcept rule above — not flattened `type_system`/`type_code`/etc. columns.

### Period (0..1)
→ Two flat columns: `<field>_start` (DateTime), `<field>_end` (DateTime).

### HumanName (0..*)
→ Child table. `given`, `prefix`, `suffix` are `ARRAY(String)` columns (see Step 2) — never individually filtered, but kept as real arrays, not comma-text.

### choice type (`foo[x]`)
→ One column per variant, all nullable. Mapper uses whichever is non-null.

### BackboneElement (0..*)
→ Child table. Any `0..*` inside the BackboneElement becomes a grandchild table.

## Step 4 — Enum rules

Use `Enum(MyClass, name="pg_type_name")` when the allowed reference types are a **closed, known set**.

**Where the Python enum lives depends on who else needs it:**
- **Resource-specific** (a reference type closed to this one resource's own field, e.g. `OrganizationEndpointReferenceType`) → `app/models/<resource>/enums.py`.
- **Shared across resources** (reused reference-type enums like `OrganizationReferenceType`/`EncounterReferenceType`/`SubjectReferenceType`, or shared non-reference codes like `IdentifierUse`) → the top-level `app/models/enums.py`, imported by every resource's model file that needs it — never redeclare a copy per resource.
- **FHIR datatype codes that the Pydantic input schemas also validate** (`ContactPointSystem`/`ContactPointUse`, `AddressType`/`AddressUse`, `HumanNameUse`) → these already live in `app/schemas/enums.py` as the schema-layer source of truth, and the model layer imports the **same classes** directly (see `app/models/shared/datatypes/fhir_contact_point.py`/`fhir_address.py`) rather than declaring model-layer duplicates. `IdentifierUse` is a known, narrow exception that currently has two independent copies — one in `app/models/enums.py` (model layer) and one in `app/schemas/enums.py` (schema layer) — with matching values; don't "fix" this by merging them, it's existing debt, not a pattern to repeat deliberately for a new enum.

### Two enum patterns — key always equals value

**Reference type enums** (FHIR resource names): both name and value are the PascalCase FHIR resource name.

```python
class MyResourceFieldReferenceType(str, Enum):
    Condition = "Condition"
    PractitionerRole = "PractitionerRole"
```

**Status / code enums** (FHIR code values): both name and value are the same lowercase FHIR code string.

```python
class MyResourceStatus(str, Enum):
    active = "active"
    completed = "completed"
```

Because key = value in every enum, SQLAlchemy, the PostgreSQL enum type, and the FHIR output all use the same string — no mismatch is possible. Alembic autogenerate emits the correct values; no manual renaming needed.

Naming: `<Resource><Field>ReferenceType` in Python, `<table_name>_reference_type` as the PostgreSQL type name.

## Step 5 — Standard columns on every model

Use the shared `TenantAuditMixin` (`app/models/shared/tenant_audit.py`) instead of hand-declaring tenant/audit columns — mix it into the model class (`class MyResourceModel(TenantAuditMixin, Base):`). It provides, via `declared_attr` (required — a bare `Column(...)` instance can't be reused across multiple tables):

```python
tenant_id   = Column(String, nullable=False, index=True)   # was "org_id" — see the mixin's own docstring for the rename rationale
created_by  = Column(String, nullable=False)                # NOT NULL — every write identifies an actor, whatever the source
updated_by  = Column(String, nullable=True)
created_at  = Column(DateTime(timezone=True), server_default=func.now(), index=True)
updated_at  = Column(DateTime(timezone=True), onupdate=func.now(), index=True)
```

The mixin does **not** include `id`, `<res>_id`, or `user_id` — declare those yourself on the main table:

```python
id          = Column(BigInteger, primary_key=True, autoincrement=True, index=True)   # internal — never exposed
<res>_id    = Column(BigInteger, <seq>, server_default=<seq>.next_value(), unique=True, index=True, nullable=False)
```

**Every `id`/`<res>_id`/sequence column is `BigInteger`, never `Integer`** — same for every containment FK and every flattened cross-resource reference `_id` (see CLAUDE.md's Standard Columns section). `tenant_id`/`user_id` stay `String` — they're tenant fields, not part of that rule.

**`user_id`**: Organization/Location/HealthcareService (the resources reworked so far) dropped `user_id` entirely because they're shared tenant-level entities, not scoped to an individual end-user — see CLAUDE.md's Standard Columns note. That is **not** the default: most resources (and any new resource built without the auth-rollout treatment — see `/resource-auth-rollout` and CLAUDE.md's Multi-Tenancy & Ownership section) keep a plain `user_id = Column(String, nullable=True, index=True)` alongside `TenantAuditMixin`'s columns, the same as before the rework — there's currently no live non-auth resource in this codebase to point to as a concrete example (every surviving resource happens to be an auth-rollout one), so don't take Organization/Location/HealthcareService's lack of `user_id` as the new universal default; it's specific to *those* resources' own reasoning.

**Child/grandchild tables** also mix in `TenantAuditMixin` (confirmed on every child/grandchild table in Organization/Location/HealthcareService — `OrganizationType`, `OrganizationTypeCoding`, etc. all do `class X(TenantAuditMixin, Base)`, sometimes combined with a `Fhir*Mixin` too, e.g. `class OrganizationTypeCoding(FhirCodingMixin, TenantAuditMixin, Base)`), plus:
- `id` (BigInteger PK)
- a containment FK to its parent table — see the naming rule immediately below
- the parent relationship declares `cascade="all, delete-orphan"`

**Containment FK naming — `_pk` vs plain `_id`:** a child table's FK to the **main resource table** is named `<resource>_pk` (e.g. `organization_pk`, `location_pk`), *not* `<resource>_id` — because the main table already has its own public-facing `<resource>_id` sequence column, and reusing that name for an internal-PK FK would collide in meaning (see `app/models/organization/type.py`'s `organization_pk`). A **grandchild** table's FK to its immediate parent **child** table uses the ordinary `<parent_table>_id` name (e.g. `organization_identifier_id` on `OrganizationIdentifierTypeCoding`, `contact_id` on `OrganizationContactTelecom`) — there's no collision there, because the child table (`OrganizationIdentifier`, `OrganizationContact`, ...) has no public sequence id of its own to collide with. Apply `_pk` only at the one level where the collision is real.

### Shared mixins (`app/models/shared/`)

Beyond `TenantAuditMixin`, three `Fhir*Mixin` classes cover the datatype-column groups that repeat across almost every resource — always use these instead of hand-declaring the same columns again:

| Mixin | Provides | Prefix hook |
|---|---|---|
| `FhirCodingMixin` | `system`/`version`/`code`/`display`/`user_selected` (one `Coding` row) | `_coding_prefix` |
| `FhirAddressMixin` | `use`/`type`/`text`/`line` (`ARRAY(String)`)/`city`/`district`/`state`/`postal_code`/`country`/`period_start`/`period_end` (one `Address`) | `_address_prefix` |
| `FhirContactPointMixin` | `system`/`value`/`use`/`rank`/`period_start`/`period_end` (one `ContactPoint`) | `_contact_point_prefix` |

Each mixin defaults to no prefix (for a dedicated one-purpose table, e.g. `OrganizationTelecom`). Set the prefix class attribute when the same table hosts more than one datatype group alongside unrelated fields (e.g. `OrganizationContact` sets `_address_prefix = "address_"` so its `address.*` columns sit next to its own `purpose_*`/`name_*` groups on one row) — the **Python-side attribute names stay bare** (`contact.city`, `contact.use`) regardless of the DB-column prefix; only the column name changes. A class can only use one Address/ContactPoint/Coding mixin instance at a time (one `_address_prefix` value per class) — use `sqlalchemy.orm.composite()` instead if a table ever genuinely needs two.

All three `Fhir*Mixin` classes use `declared_attr` for the same reason `TenantAuditMixin` does, and — like it — must not have `-> Column` return-type annotations (SQLAlchemy 2.0's Annotated-Declarative scanner misreads the hint and raises `MappedAnnotationError`).

### FHIR Organization reference fields (e.g. `managingOrganization`, `serviceProvider`, `contact.organization`)

Don't confuse these with `tenant_id`/`user_id` — those are tenant/auth fields, not FHIR data; an Organization *reference* is ordinary FHIR content pointing at an actual Organization row.

Follow the **Reference (0..1 or 0..*)** rule from Step 3 above: flattened `_type`/`_id`/`_display`, **no FK**, `_id` stores the Organization's **public** `organization_id`. Use the shared `OrganizationReferenceType` enum (`app/models/enums.py`, single value `Organization = "Organization"`), PostgreSQL type name `organization_reference_type` with `create_type=False` (it's defined once and shared — never create/drop it again). Example for a 0..1 `Reference(Organization)` on the main table:

```python
from app.models.enums import OrganizationReferenceType

managing_organization_reference = Column(String, nullable=True)  # raw literal string as received
managing_organization_id = Column(BigInteger, nullable=True, index=True)  # PUBLIC organization_id, no FK
managing_organization_type = Column(
    Enum(OrganizationReferenceType, name="organization_reference_type", create_type=False),
    nullable=True,
)
managing_organization_display = Column(String, nullable=True)
# plus managing_organization_identifier_* logical-reference-fallback columns,
# same shape as Organization.identifier.assigner — see app/models/organization/identifier.py
```

- Input schema: `managing_organization: Optional[str] = Field(None, description="FHIR reference, e.g. 'Organization/190100'.")`
- Repository/service: existence is checked at write time via `ensure_resource_exists()` (`app/core/reference_resolver.py`) against `RESOURCE_REGISTRY` — not a DB lookup-then-store-internal-PK step, since there's no FK to populate.
- Mapper FHIR output: `f"Organization/{model.managing_organization_id}"` directly off the stored public id — no relationship to navigate.
- Response schema: expose `managing_organization_type`, `managing_organization_id`, `managing_organization_display` (plus the identifier-fallback fields).

This is the same no-FK/public-id shape as every other reference on a reworked resource — Organization references aren't special-cased with a real FK the way they were before this rework (see Step 3's "legacy convention" note — a pre-rework resource may still have a real `ForeignKey("organization.id")` to an internal PK; don't copy that for new work).

## Step 6 — Sequence allocation

Pick the next unused 10000-block. **CLAUDE.md's "Sequence allocation" table is the single source of truth** — always read it fresh rather than hard-coding a list here, since it grows with every new resource and duplicating it drifts out of date. It also states the current "next available block" explicitly.

## Step 7 — Migration

After writing the model, generate a migration:
```
uv run alembic revision --autogenerate -m "<description>"
```

Autogenerate enum values are reliable (all enums use key = value convention — no name/value mismatch). Still update the generated file to use the `postgresql.ENUM` pattern for proper create/drop handling:
1. Replace `sa.Enum(...)` with `postgresql.ENUM(...)` at module level: `_my_enum = postgresql.ENUM('VALUE1', 'VALUE2', name='pg_type_name')`.
2. Call `_my_enum.create(op.get_bind(), checkfirst=True)` at the start of `upgrade()`.
3. Use `create_type=False` on any `add_column`/`alter_column` that references the type.
4. If converting VARCHAR → Enum, add `postgresql_using='col::pg_type_name'`.
5. In `downgrade()`, revert columns first, then call `_my_enum.drop(op.get_bind(), checkfirst=True)`.

Apply with: `uv run alembic upgrade head`

## Step 8 — Full stack checklist

After the model and migration, walk every layer:

- [ ] `app/models/<resource>/enums.py` — new Enum classes
- [ ] `app/models/<resource>/<resource>.py` — ORM model + child tables
- [ ] `app/models/<resource>/__init__.py` — exports
- [ ] `app/schemas/<resource>/input.py` (or `input/` package once it grows — see `/split-resource-package`) — CreateSchema, PatchSchema; CodeableConcept-coding fields are `list[CodingInput]` (import the shared `CodingInput` from `app.schemas.datatypes`, not a resource-prefixed redeclaration); CodeableReference inputs include both concept and reference fields
- [ ] `app/schemas/<resource>/response.py` (or `response/` package) — FHIRXxxSchema, PlainXxxResponse, PaginatedXxxResponse, FHIRXxxBundle; exported from `app/schemas/<resource>/__init__.py`. Shared FHIR datatypes (`FHIRCoding`, `FHIRAddress`, `FHIRIdentifier`, ...) and their plain/audit-row counterparts (`AuditFields`, `PlainCodingRow`, `ContactPointInput`, `PlainContactPointRow`, ...) come from `app.schemas.datatypes` — there is no `app/schemas/fhir/` package
- [ ] `app/fhir/mappers/<resource>/` package (`fhir.py` + `plain.py` + `__init__.py`) — to_fhir / to_plain; CodeableReference outputs `{"concept": {...}, "reference": {...}}`
- [ ] `app/repository/<resource>_repository.py` (or `_repository/` package) — CRUD, `_with_relationships`, `_apply_list_filters` built from the shared `app/core/filters.py` helpers (`apply_child_exists_filter`, `apply_token_filter`, `parse_reference`) and `app/core/pagination.py`'s `resolve_sort`/`ListParams` rather than hand-rolled SQLAlchemy `.where()` chains and inline `Query(...)` params; `_cast_ref_type` for closed-set enums
- [ ] If `input.py`/`response.py`/the repository/service/router grow too large (many sub-resources), split each into a per-sub-resource package — see `/split-resource-package` (Organization, Location, and HealthcareService all do this already)
- [ ] Migration generated and manually fixed
- [ ] `uv run alembic upgrade head` applied

## Reminders

- **This project uses FHIR R4** — always fetch `https://www.hl7.org/fhir/R4/<resource>.html`. Never use `build.fhir.org` or `https://www.hl7.org/fhir/<resource>.html` (R5).
- **Never model from memory** — always fetch the spec URL first.
- **CodeableReference does not exist in R4** — in R4 use separate `reasonCode[]` + `reasonReference[]` arrays, separate `complication[]` + `complicationDetail[]`, separate `usedCode[]` + `usedReference[]`, etc.
- **Exception: PractitionerRole** — this project intentionally uses the R5 structure for PractitionerRole (contact + availability). Do not change it.
- **Enum values in autogenerate are correct** (key = value) — still apply the `postgresql.ENUM` create/drop pattern manually.
- **Verify imports compile** — run `uv run python -c "from app.models.<resource> import ..."` after writing.
