# FHIR DB Model Designer (Medplum-style search index)

You are designing the storage for a **FHIR R4** resource in this project. The approach is Medplum's: **the whole resource is stored as one JSON document (`content`, JSONB); only the values a FHIR search parameter filters on are normalized into columns and child tables** — a search index, derived from `content` on every write, never read to build a response. Every rebuilt resource is built this way (`app/models/<resource>/`); the newest and richest templates are Encounter, Appointment, AppointmentResponse, Patient and RelatedPerson, with Organization/Location/Practitioner as the simplest.

The old approach — one column or table per element, flattened References with 15 columns, `Fhir*Mixin`s, a mapper per datatype — is **no longer used for new work**. Its full rules are preserved in `docs/legacy/fhir-db-model-normalized.md` (no resource uses it any more: all 52 are rebuilt).

Use `/new-fhir-resource` for the whole checklist; this skill is only the modelling decisions.

## Step 1 — Read the R4 documentation first

**Never model from memory and never from R5.**

- Resource page: `https://www.hl7.org/fhir/R4/<resource>.html` — read the **Search Parameters** table (`#search`): each parameter's name, type, FHIRPath expression, and (references) target types.
- Search rules: `https://www.hl7.org/fhir/R4/search.html` — what each type matches and which modifiers it takes (string: `:exact`/`:contains`, default starts-with and case/accent-insensitive; token: `system|code`, `:not`/`:text`/`:in`/`:not-in`/`:above`/`:below`/`:of-type`; reference: `Type/id`, URL, `:[type]`/`:identifier`, chaining; date: the nine prefixes; `:missing` on all).
- Parameter registry (expressions + all targets): `https://www.hl7.org/fhir/R4/searchparameter-registry.html`.
- Datatypes used by those expressions: `https://www.hl7.org/fhir/R4/datatypes.html` (HumanName, Address, ContactPoint, CodeableConcept, Period, ...).
- `CodeableReference` does not exist in R4; if you see it you are reading R5.

## Step 2 — The element table is not your schema

You do **not** model the resource's elements. They are all in `content`, whatever they are (Timing, Dosage, nested BackboneElements, extensions, `modifierExtension`, ...). A non-searched element costs nothing, and adding one later needs no migration. Model **only**: one index entry per search parameter, plus the main row's own bookkeeping.

## Step 3 — Map each search parameter to index storage

Every searched string is stored twice: **as written** (answers `:exact`, which is case/accent-sensitive) and **normalized** `*_norm` (`app.fhir.search.normalize`: NFKD, accents stripped, case-folded; answers the default starts-with and `:contains`). Normalize in Python on write, not in SQL, so Postgres and the SQLite test DB behave identically and a plain btree can serve prefix search.

| Search parameter over… | Storage |
|---|---|
| `_id` | none (public `<resource>_id` column) |
| `_lastUpdated` | none (`coalesce(updated_at, created_at)`) |
| 0..1 boolean or code → token (`active`, `gender`, `status`) | one nullable column on the main table. `Enum(...)` when the code has a **`required`** binding (a closed list HL7 defines fully); otherwise `String` |
| 0..* `code` with a **required** binding (`AllergyIntolerance.category`) | `ARRAY(Enum(...))` on the main table, one enum type per resource+field, stored by value (`values_callable`); NULL when empty. **Not** rows in a shared token table |
| `code` with a required binding **inside a repeating backbone element or datatype** (`AllergyIntolerance.reaction.severity`, `Appointment.participant.status`, `Address.use`) | an `Enum` column on that element's index-table row (create the row when the element has *any* indexed value, not only the first one) |
| 0..1 string (`name`) | `x`, `x_norm`; add `Index(..., postgresql_ops={"x_norm": "text_pattern_ops"})` for a hot prefix search |
| 0..* list of plain strings (`alias`) | `x ARRAY(String)`, `x_norm ARRAY(String)`; store **NULL, not `[]`**, when empty so `:missing` is `IS NULL`. Never comma-joined text. |
| 0..* HumanName / Address | child table, one row per entry, only the searched parts, raw + `_norm` of each. `family`, `text`, `city`... scalar; `given`/`prefix`/`suffix`/`line` as `ARRAY(String)` so each is matched on its own |
| `phonetic` | a `phonetic` column holding space-padded Soundex codes (`" C614 A350 "`), matched with `LIKE '% C614 %'` (`app.core.phonetic`) |
| token over Identifier | child table: one row per `identifier` × `type.coding`: `system`, `value`, `type_system`, `type_code`, `type_text_norm`, `type_display_norm` (one type-less row when untyped) — for `:of-type` and `:text` |
| token over CodeableConcept / Coding (0..*) | child table: one row per `coding`: `system`, `code`, `display_norm`, `text_norm`; plus one code-less row for a concept with only `text` |
| token over ContactPoint (`telecom`/`phone`/`email`) | child table: `system`, `value`, `use`. R4 token on a ContactPoint: code ↔ `value`, `system|` ↔ `use`; `phone`/`email` add `system = ...` |
| reference, 0..1 (single target **or** several: the type goes in a plain-string `{p}_type`, never a Postgres enum) | columns `{p}_reference` (the raw string exactly as received — an absolute URL to another server lives only here), `{p}_type` + `{p}_id` (resolved **public** id, relative `Type/id` only), `{p}_identifier_system`/`_value` (Reference.identifier, for `:identifier`). **No `ForeignKey`, no relationship** — the target type varies per row. |
| reference, 0..* | child table with the same columns (see `*_endpoint` tables) |
| reference to several resource types, 0..* (`Schedule.actor`, `Appointment.participant.actor`, `Encounter.participant`) | the same child table plus a plain-string `reference_type` column recording which type each relative `Type/<id>` names — a bare id can't be matched across types, so the type is part of every match and of the index `(reference_type, reference_id)`. When the parameter has *narrowed* aliases (`patient`, `practitioner` over `actor`/`participant`) they read the same rows filtered by `reference_type`, so no extra storage. A child table that carries more than the reference (Encounter `location`: reference + `period_start/_end`; Appointment participant: reference + `status`) keeps those values on the same row so parameters that must agree (`location` + `location-period`) stay together |
| Reference(Any) / types the server doesn't model | plain-string `reference_type` as above; a tolerant parse that never raises (an unparseable shape just has no `_type`/`_id` and matches by its raw string). Search `targets` = `ANY_RESOURCE_TYPES` (all R4 types, `app/models/shared/resource_types.py`), never a hand-typed list; chaining / `_include` follow every rebuilt type (`app/repository/_search_targets.py`) |
| date / dateTime / instant | timestamp (or `Date`) column |
| Period | two columns `*_start` / `*_end` holding the **half-open range** [start, end): start = the first instant the period covers, end = the first instant *after* it (so `2026-12` ends at 2027-01-01T00:00Z), NULL = open. Fill them with `period_bounds()` and search with `period_match()` — never store the end as written, or coarse dates (`2026-12`) and open-ended periods search wrong |
| Quantity (`Encounter.length`) | columns `{p}_value` (Numeric/Float-comparable), `{p}_system`, `{p}_code`, `{p}_unit`; search with `quantity_match()` (`app/fhir/search/quantity.py`). Units are compared as written, there is no UCUM conversion, so store the quantity as sent |
| Quantity that can be an **Age or a Range** (`Condition.onset[x]` / `abatement[x]`) | columns `{p}_low`, `{p}_high` (Numeric; an Age is low = high, an open end is NULL) plus one shared `{p}_system`, `{p}_code`, `{p}_unit` (from the low bound, else the high one); matched with `quantity_range_match(low, high, system, code, unit, value)` — R4 range semantics (`eq` = the search range wholly contains the target; `gt/lt/ge/le` = overlap above/below; `sa/eb` = entirely after/before; an open end overlaps everything on its side). The other `onset[x]` choices need their own columns: dateTime / Period as `*_date_start/_end` (`period_bounds`), string as `x` + `x_norm` |
| uri (`Procedure.instantiatesUri`, 0..* uri) | child table with one `uri` column per value (or a column when 0..1); matched with `uri_match(col, value, modifier)` in `app/fhir/search/sql.py` — exact and case-sensitive; `:below` = stored starts with the value, `:above` = stored is a prefix of the value (both as substring comparisons, so they are case-sensitive on SQLite too) |
| canonical URL list (`Procedure.instantiatesCanonical`) | rows in the shared reference table holding the raw URL (and the parsed `Type/<id>` when it is relative); a custom match that also lets an unversioned URL find stored `url|version` values |
| a bare `Coding` (0..1 — Encounter `class`) | `{p}_system`, `{p}_code`, `{p}_display_norm` columns on the main row (a CodeableConcept would be a child table instead) |
| number (a decimal or a Range, `RiskAssessment.prediction.probability`) | `{p}_low`, `{p}_high` Numeric columns (a decimal is low = high; an open end is NULL), matched with `number_range_match` (`app/fhir/search/quantity.py`, R4 range semantics, no unit) |
| composite | store each part's value in a child row with a `slot` column (0 = the resource, n = its n-th repeating element) so the two parts can be required on the same element; the builder is resource-side (`_composite()` in `app/repository/observation/search.py`, `split_composite` in `app/fhir/search/composite.py`) |
| `near`-style special | store the primitives it needs (lat/long columns) and write a custom matcher |

**Several parameters with the same shape → one shared table with a `param` column** (HealthcareService: `healthcare_service_token` for its five CodeableConcept parameters, `healthcare_service_reference` for `location` / `coverage-area` / `endpoint`). Each query adds `param == '<name>'` to its `EXISTS`; there is nothing else to keep in sync. A reference table's `reference_type` can then be a plain string (the value is fixed by `param`) rather than a Postgres enum.

Chained parameters (`partof.name`) and hierarchy (`:above`/`:below`) need **no extra storage**: they join the same index through the registry (`chain=`, `hierarchy=`; Organization's recursive CTE is the example).

## Step 4 — Rules for every index table

- **FK name:** `<resource>_pk` → `<resource>.id` (BigInteger, `index=True`). Never `<resource>_id`: that is the public sequence column.
- **No `TenantAuditMixin`, no `created_by`/`updated_*`, no `extension`, no tenant column** on child tables. Tenant scoping is on the main row; children are reached by correlated `EXISTS`.
- **No DB constraints** — no `CHECK`, no `UNIQUE` on identifier `(system, value)`, no reference-list dedup. R4 rules are the validator's job; uniqueness is a profile decision.
- **All index columns nullable.** Only `content` is `NOT NULL`. Nullability never claims a stricter rule than the spec.
- **Cascade:** `relationship(..., cascade="all, delete-orphan")` on the main model; patch replaces every index relationship wholesale. All `id`s and FKs are `BigInteger`.
- **Index only what a parameter filters on.** If a parameter, modifier or sort you support isn't backed by a column here, it isn't supported.
- A PG enum type shared across resources (`address_use`, `identifier_use`; a reference's `{p}_type` is never an enum) is referenced with `create_type=False`. In a migration the **same** `postgresql.ENUM(..., create_type=False)` object must be used by every `op.create_table` that uses the type.

## Step 5 — The main table

```python
class <Resource>Model(TenantAuditMixin, Base):      # tenant_id, created_by (NOT NULL), updated_by, created_at, updated_at
    __tablename__ = "<resource>"
    id = Column(BigInteger, primary_key=True, autoincrement=True, index=True)          # never exposed
    <resource>_id = Column(BigInteger, <resource>_id_seq, server_default=<resource>_id_seq.next_value(),
                           unique=True, index=True, nullable=False)                      # the public id
    content = Column(JSONB, nullable=False)          # whole resource minus resourceType/id/meta
    # 0..1 index columns from Step 3, then relationships to the child index tables
```
- Sequence: `Sequence("<resource>_pub_seq", start=<next free 10000-block from CLAUDE.md>, increment=1, metadata=Base.metadata)`.
- `TenantAuditMixin` (`app/models/shared/`) supplies the audit/tenant columns; `org_id` from the JWT is stored as `tenant_id`. Don't redeclare them.
- Put a docstring on the model with the **search parameter → storage** table (copy Organization's) — it is the contract between `search.py` and `_indexer.py`.
- **Non-FHIR record state** that must be queryable (Practitioner's `user_id`, the IAM user it is linked to; scopes `/me`): keep it as a **column only**. It is not in `content`, not accepted in the create/patch body, and not settable through them. Set it through a dedicated, permission-gated call (`PUT/DELETE /<resources>/{id}/user`, scope `<resource>:link`) — the equivalent of Medplum's `ProjectMembership.profile`. Enforce "one user per org" in the service.

## Step 6 — Migration

- New resource: `uv run alembic revision --autogenerate -m "add_<resource>_content_and_search_index"`, then hand-fix: reuse shared PG enums with `create_type=False`, create the `<resource>_pub_seq` sequence (`CREATE SEQUENCE IF NOT EXISTS ... START WITH <N>`; strip autogenerate's false-positive `CREATE/DROP SEQUENCE` noise), and leave `downgrade()` unimplemented (the repo's migrations are one-way; say so in the docstring).
- **Converting an old-shape table (none are left; kept for reference):** model the migration on `a7d3f19c2b64` — add `content`, build it per row with a **frozen** copy of the old mapper (never import app code), drop the old child tables and columns, create the index tables, rebuild the index from `content`, set `content` `NOT NULL`. Keep any non-FHIR state (e.g. `user_id`) as a column — never in `content` — and carry it over unchanged.
- If the old model's public id used a Python-side `Sequence` with no server default, the migration sets `DEFAULT nextval('<resource>_pub_seq')` (the new model uses `server_default`).
- A per-field Postgres enum for a reference type is replaced by a plain string column; drop the enum in the migration (but never a shared one such as `organization_reference_type`).
- Converting a column to an enum or backfilling one: use a safe cast (`CASE WHEN col IN (...) THEN col::enum END`) so a stray value becomes NULL instead of failing the migration; rebuild child index rows from `content` with a frozen copy of the indexer logic.
- **Verify on a scratch database, never the dev DB (and never print the `.env` password):** create DB → `alembic upgrade` to the previous head **in steps** (`+10` repeatedly, then a named revision — one go exceeds `max_locks_per_transaction`) → insert old-shape rows (explicit public id if the old schema had no server default; real `datetime` objects for asyncpg) → upgrade to the new head → inspect `content` (absolute URLs, logical references and partial dates preserved) and index rows → `alembic check` and look for drift on your tables → drop DB.

## Step 7 — Required-binding codes: audit every search parameter (mandatory)

Do not decide from the parameter name or from memory. For **every** token search parameter of the resource:

1. Find the element(s) its FHIRPath expression reads (HL7 `SearchParameter-<resource>-<code>.json`, or the resource page).
2. Look at the element's **type and binding strength** in the StructureDefinition (follow into the datatype for `address.use`, `name.use`, ...). Binding strengths: required / extensible / preferred / example.
3. Type `code` + **required** binding → enum column (see the Step 3 table), including when it is 0..*, nested, or reached through a datatype. Anything else (CodeableConcept, Coding, `code` with extensible/preferred/example, string, boolean) → no enum.
4. Run `uv run python scripts/audit_hl7_live.py` - it downloads the live R4 definitions from hl7.org (cached in `.cache/hl7-r4/`, `--refresh` to re-download) and checks every rebuilt resource: parameter names, types, reference targets, required-code enums and their values. Exit 1 on any problem.
5. Add the parameter to `REQUIRED_CODE_STORAGE` in `tests/unit/test_hl7_alignment.py`. That test reads HL7's own R4 package and **fails** if a required-binding `code` parameter is not listed or is not an enum column, and if the registry serves a parameter R4 does not list (or misses one it does). It was added because `AllergyIntolerance.category`/`reaction.severity` and `Appointment.participant.status` were once missed by a name-based check.

## Step 8 — Reminders

- A `:missing=true` on a parameter backed by a *type-narrowed* multi-target reference must also require `type IS NOT NULL` in the "present" condition, or rows that hold only a logical `identifier` reference are wrongly reported as missing.
- Enum columns for status-like codes store the **true FHIR code** (`in-progress`), not the Python member name; an unknown code in a search matches nothing rather than failing the enum cast.
- Search is only as good as the index: after writing `_indexer.py`, test that **every** registry parameter finds a record using a real value (not one that can't match).
- An index column that no search parameter reads is a design smell: either it should back a parameter, or it belongs in `content` only.
- Adding a searchable field later: add the column/table → populate it in `_indexer.py` (and **backfill it from `content` in a migration**) → add the `SearchParam`. Nothing else changes; `/metadata` and OpenAPI follow the registry.
- Removing an unsearched field from a resource: nothing to do.
