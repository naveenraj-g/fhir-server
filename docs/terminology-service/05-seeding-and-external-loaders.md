# Seeding and External Loaders

**What this file is:** none of the code systems described conceptually in
[00-what-is-terminology.md](00-what-is-terminology.md) — LOINC, SNOMED CT,
ICD-10-CM, RxNorm, HL7's own FHIR-published code systems — ship with this
codebase. They're large, separately-published files that have to be
downloaded and loaded into this project's own database tables (see
[01-data-model.md](01-data-model.md)) before any lookup or validation can
use them. This file explains the scripts that do that loading, one per
source format, plus the two scripts that decide which fields are bound to
which value sets afterward.

This is the subsystem's data-ingestion half: one CLI with five source-format
loaders feeding the tables from [01-data-model.md](01-data-model.md), plus
two independent scripts that populate `TerminologyFieldBinding` afterward.
Everything here uses **raw `asyncpg`, not SQLAlchemy** — deliberately, for
bulk-insert performance (`app/terminology/import_/base.py`'s own framing).

## The CLI: `app/terminology/import_/cli.py` (114 lines)

Argparse entry point, `--source` one of `fhir-r4 | loinc | icd10cm | rxnorm
| snomed | all`, plus `--file`/`--dir` (or source-specific flags when
`--source all`: `--fhir-r4-file`, `--icd10cm-file`, `--rxnorm-file`,
`--loinc-file`, `--snomed-dir`). `run()` maps `--source` to a loader class
and does:

```python
async with loader_cls(db_url) as loader:
    await loader.load(path)
```

Invoked via `just terminology-<source>` recipes (see "justfile recipes"
below) or `just terminology-all`, which chains
`terminology-fhir-r4 → terminology-icd10cm → terminology-rxnorm →
terminology-loinc → terminology-snomed → terminology-seed-bindings-r4` — in
that order, because the field-binding seed (last) depends on the ValueSets
the fhir-r4 load (first) creates.

## `app/terminology/import_/base.py` — `BaseLoader` (137 lines)

The shared toolkit every format-specific loader builds on:

- `BATCH_SIZE = 2000` — all bulk inserts chunk at this size.
- `upsert_code_system(canonical_url, name, ...)` — `ON CONFLICT
  (canonical_url) DO UPDATE`, using `COALESCE(EXCLUDED.x, existing.x)`-style
  preserve-if-null semantics so a re-run with a sparser record doesn't blank
  out fields a previous, richer load already populated.
- `bulk_insert_concepts(code_system_id, rows)` — `ON CONFLICT
  (code_system_id, code) WHERE org_id IS NULL DO NOTHING`, matching
  [01-data-model.md](01-data-model.md)'s partial unique index exactly (the
  `WHERE` clause has to be present and has to match the index's predicate,
  not just the column list, for Postgres to use it as the conflict target).
  `search_vector` is computed inline in the same INSERT via
  `to_tsvector('english', $5)` — no separate UPDATE pass.
- `bulk_insert_synonyms(...)`, `bulk_insert_relationships(...)` — same
  batched-insert pattern.
- `fetch_concept_id_map(code_system_id) -> {code: db_id}` — every loader
  that needs to resolve a code back to its internal `id` (for synonyms,
  relationships, or hierarchy) calls this once and works off the in-memory
  dict rather than querying per row.

## The five format loaders (`app/terminology/import_/loaders/`)

### `fhir_r4.py` (272 lines) — HL7 FHIR Bundle/CodeSystem/ValueSet JSON

`FhirR4Loader.load(path)` accepts a Bundle JSON file, a single
CodeSystem/ValueSet JSON file, or a directory of `CodeSystem-*.json` /
`ValueSet-*.json` files.

- `_load_code_system`: HL7 CodeSystem JSON nests concepts recursively
  (`concept[].concept[]...`). `_flatten_concepts` walks that tree once,
  tracking each concept's `parent_code` as it goes, then
  `_set_parent_concept_ids` runs a single raw SQL `UPDATE` that joins an
  **unnested array** of `(child_code, parent_code)` pairs against the
  concept table to set `parent_concept_id` for the whole code system in one
  statement — not a per-row round trip.
- `_load_value_set`: `binding_strength = "required" if
  vs.get("immutable") else "extensible"` — this is the loader heuristic
  referenced in [01-data-model.md](01-data-model.md)'s warning that
  `TerminologyValueSet.binding_strength` isn't consulted by `validate()`.
  Handles three `compose.include` shapes: `filter` entries with
  `op: is-a`/`is-not-a` (resolved via a **recursive CTE** walking the IS-A
  subtree, not an in-Python tree walk), inline `concept[]` arrays (specific
  codes named directly in the ValueSet), and whole-system includes (every
  concept in a named CodeSystem). All three insert rows into
  `terminology_value_set_concept`.

### `icd10cm.py` (67 lines) — ICD-10-CM

Auto-detects tab-delimited vs. fixed-width input (fixed-width is detected by
checking whether the first 7 characters of a line look like a code).
`ICD10CM_URL = "http://hl7.org/fhir/sid/icd-10-cm"`. ~72k codes per the
justfile's own comment, no hierarchy extraction — flat code list.

### `rxnorm.py` (88 lines) — RxNorm RRF

Pipe-delimited RRF format. `INCLUDED_TTY = {"IN", "PIN", "MIN", "BN", "SCD",
"SBD", "GPCK", "BPCK"}` — only these term-type rows become concepts (RxNorm's
RRF carries many more TTYs than this; everything outside this set is
skipped). `TTY_PRIORITY` dict ranks which TTY's string wins as the stored
`display` when one RXCUI has multiple matching rows (`IN` = priority 0,
highest). Filters to `LAT == "ENG"` only — no non-English RxNorm terms are
loaded.

### `loinc.py` (68 lines) — LOINC CSV

`csv.DictReader` over LOINC's table-core CSV export.
`ACTIVE_STATUSES = {"ACTIVE", "TRIAL"}` — other LOINC statuses (e.g.
deprecated/discouraged codes) are skipped on load. Columns used: `LOINC_NUM`
→ `code`, `LONG_COMMON_NAME` (falling back to `COMPONENT` when blank) →
`display`, `DEFINITION_DESCRIPTION` → `definition`.

> **`CLASS` is not loaded as a synonym.** An earlier version of this
> loader's docstring claimed `CLASS` was "stored as synonym for search" —
> `load()` never actually read `row.get("CLASS")`. Fixed by correcting the
> docstring rather than implementing the feature: `bulk_insert_concepts()`
> does a plain `executemany()` INSERT with no `RETURNING`, so there's no
> way to learn which `concept_db_id` a given `LOINC_NUM` landed at without
> either a follow-up `SELECT` or restructuring `bulk_insert_concepts()`'s
> return contract — which every other loader also depends on. Real feature,
> genuinely not built; the docstring just no longer pretends otherwise.

### `snomed.py` (146 lines) — SNOMED CT RF2

Tab-delimited RF2 snapshot files, located via glob against the configured
directory: `sct2_Concept_Snapshot_*.txt`, `sct2_Description_Snapshot-en_*.txt`,
`sct2_Relationship_Snapshot_*.txt`. Constants `FSN_TYPE_ID`,
`SYNONYM_TYPE_ID`, `IS_A_TYPE_ID` identify which description/relationship
rows matter. Reads active concept IDs first, then extracts each concept's
**FSN** (Fully Specified Name, with the trailing `(semantic tag)`
parenthetical stripped) as its canonical `display`, and separately extracts
every **synonym** description row into `TerminologyConceptSynonym`. IS-A
relationships are inserted into the standalone `TerminologyRelationship`
table — **not** via `TerminologyConcept.parent_concept_id`, the mechanism
the FHIR R4 loader uses. These are two genuinely different hierarchy
representations in this codebase (see
[01-data-model.md](01-data-model.md)'s `TerminologyRelationship` section);
SNOMED's poly-hierarchy (a concept can have more than one IS-A parent) is
exactly why it can't use the single-`parent_concept_id`-column shape the
FHIR R4 loader relies on.

## Field-binding seeding: two different scripts, two different sources

Both scripts populate the same table (`TerminologyFieldBinding`), both are
idempotent (`ON CONFLICT (resource_type, field_name) DO UPDATE SET
value_set_id=..., binding_strength=..., multiple_allowed=..., active=TRUE`
— the exact `UniqueConstraint` from [01-data-model.md](01-data-model.md)
is the conflict target in both), both skip-and-count a binding whose
`value_set_id` can't be resolved (the referenced ValueSet isn't loaded yet)
rather than failing the whole run, and **both use raw `asyncpg`, not an ORM
session.** Beyond that, they are unrelated:

### `seed_field_bindings.py` (228 lines) — hand-curated

A hardcoded Python list, `FIELD_BINDINGS`, of
`(resource_type, field_name, value_set_url, binding_strength,
multiple_allowed)` tuples — someone manually decided which ~85 fields
across ~30 resource types (Patient, Practitioner, PractitionerRole,
Encounter, Appointment, Condition, Observation, MedicationRequest,
Medication, Procedure, DiagnosticReport, ServiceRequest, DeviceRequest,
AllergyIntolerance, Immunization, DocumentReference, Coverage, Claim,
ClaimResponse, Invoice, CarePlan, Task, EpisodeOfCare, AuditEvent, Schedule,
Slot, Location, Organization, Provenance, Specimen, RelatedPerson,
HealthcareService) should be bound, and to what. `seed(db_url)` walks the
list, resolves each `value_set_url` to an `id`, and upserts.

### `seed_field_bindings_r4.py` (241 lines) — auto-derived from HL7 StructureDefinitions

Mechanically derives **every** binding actually present in HL7's own R4
StructureDefinition bundles — `terminology_data/profiles-resources.json`
and `terminology_data/profiles-types.json` (both required inputs, checked
for existence up front; the script exits with an error if either is
missing). Two-pass:

1. **Pass 1 — `build_type_bindings(types_bundle)`**: walks every
   `complex-type` / `derivation: specialization` StructureDefinition in
   `profiles-types.json` (datatypes like `Address`, `ContactPoint`,
   `HumanName`, `Identifier`) and extracts each sub-field's own binding —
   e.g. `Address.use`'s binding, `ContactPoint.system`'s binding. Returns
   `{type_name: [(sub_field, vs_url, strength, multiple_allowed), ...]}`.
2. **Pass 2 — `extract_bindings(resources_bundle, type_bindings)`**: walks
   every non-abstract `kind: resource` / `derivation: specialization`
   StructureDefinition in `profiles-resources.json` (skipping a fixed set
   of infrastructure types — `Resource`, `DomainResource`, `Bundle`,
   `CapabilityStatement`, `StructureDefinition`, etc. — via
   `_SKIP_RESOURCE_TYPES`), and for every element:
   - if the element itself has a `binding`, record `(resource_type,
     field_name, vs_url, strength, multiple)` directly;
   - **additionally**, for every non-primitive type the element's `type[]`
     declares, look up that type's own sub-bindings from Pass 1 and record
     them as `(resource_type, f"{field_name}.{sub_field}", vs_url, strength,
     sub_multiple)`. This is how `Patient.address` (typed `Address`)
     mechanically produces a `Patient.address.use` binding without
     `Patient`'s own StructureDefinition ever mentioning `use` directly —
     it's inherited from `Address`'s own binding in Pass 1 and attached
     under the `Patient.address.` prefix.

   `multiple_allowed` is computed the same way in both passes: `max == "*"`
   or `max` parses as an int `> 1` (`_max_to_multiple()`).

Results are deduplicated by `(resource_type, field_name)` into a dict
(last-write-wins on collision) before the DB loop runs, so a field that
picked up a binding from both a direct element binding and a Pass-1
inherited expansion only gets upserted once, using whichever of the two was
recorded last.

The justfile recipe comments (`just terminology-seed-bindings-r4`) and
`terminology-all`'s dependency chain both call this one **"preferred over
the manual seed"** — `terminology-all` depends on
`terminology-seed-bindings-r4`, not `terminology-seed-bindings`. Because
both upsert into the same `(resource_type, field_name)` conflict target,
running the R4 auto-seed *after* the hand-curated one will silently
overwrite any hand-curated binding for a field the R4 StructureDefinitions
also happen to bind — which, since HL7's own base R4 bindings cover most
coded fields, is most of them. Run order matters if you want the
hand-curated list's choices to stick for any field that also has an R4
binding; as shipped (`terminology-all`), the R4 auto-seed always runs and
the hand-curated script is a separate, manually-invoked recipe not part of
the default chain.

## justfile recipes (confirmed against the actual `justfile`)

```
terminology-icd10cm FILE=...          # ~72k codes, ~2 min
terminology-rxnorm FILE=...           # ~100k drugs, ~3 min
terminology-loinc FILE=...            # ~100k codes, ~3 min
terminology-snomed DIR=...            # ~350k concepts + IS-A hierarchy, ~15 min
terminology-fhir-r4                   # v3-codesystems -> v2-tables -> valuesets, load order matters
terminology-seed-bindings             # hand-curated; run after terminology-fhir-r4
terminology-seed-bindings-r4          # "preferred over manual seed"; requires profiles-resources.json + profiles-types.json
terminology-all: terminology-fhir-r4 terminology-icd10cm terminology-rxnorm terminology-loinc terminology-snomed terminology-seed-bindings-r4
```

`terminology-fhir-r4` itself is three sequential CLI invocations, order
documented inline in the justfile as load-order-dependent:
`v3-codesystems.json` (HL7 terminology.hl7.org CodeSystems) →
`v2-tables.json` (HL7 v2 CodeSystems, e.g. `v2-0131` for
`patient-contactrelationship`) → `valuesets.json` (references both v3 and
v2 systems in `compose.include`, so it has to load last).
