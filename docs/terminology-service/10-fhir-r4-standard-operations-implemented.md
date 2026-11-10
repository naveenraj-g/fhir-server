# FHIR R4 Standard Operations — What's Implemented

This is the closing report for the rebuild tracked by
[08-fhir-r4-standard-compliance-gap-analysis.md](08-fhir-r4-standard-compliance-gap-analysis.md)
and built against
[09-fhir-r4-terminology-standard-reference.md](09-fhir-r4-terminology-standard-reference.md).
Read those two first if you haven't — this doc assumes you already have
that context and is specifically about **what's real now vs. what's still
a gap**, with no hedging either way.

**Bottom line:** every standard `$`-operation CodeSystem/ValueSet/ConceptMap
define in FHIR R4 now exists as a real, spec-shaped, `$`-prefixed endpoint
at `/api/v1/terminology`, returning real `Parameters`/`ValueSet`/`ConceptMap`
JSON and routing errors through `OperationOutcome`. A real
`TerminologyCapabilities` resource now exists too, dynamically reflecting
what's actually loaded. What's still missing is narrower than before, and
is listed precisely in §4 below — don't assume anything not listed there
is also missing.

---

## 1. What's implemented

### 1.1 CodeSystem operations (`app/routers/terminology/codesystem_operations.py`)

| Operation | Routes | Notes |
|---|---|---|
| `$lookup` | `GET`/`POST /CodeSystem/$lookup` | Returns `name`/`version`/`display` plus `designation[]` built from both `TerminologyConceptSynonym` and `TerminologyConceptTranslation` rows. Not-found is a 400 `OperationOutcome` (`issue.code = not-found`), per spec — not 404. |
| `$validate-code` (CodeSystem) | `GET`/`POST /CodeSystem/$validate-code` | "Is this code known in this system at all" — distinct from the ValueSet variant below. Always 200 with `result: false` on an unknown code; only errors if the CodeSystem itself can't be resolved. |
| `$subsumes` | `GET`/`POST /CodeSystem/$subsumes` | Real transitive IS-A subsumption, not just direct-parent — see §2. Cross-code-system `codingA`/`codingB` pairs are rejected (400 `not-supported`), since no cross-system subsumption is defined here. |
| `$find-matches` | `POST /CodeSystem/$find-matches` | Spec-shaped but **honestly non-functional** — see §4.1. |

Backing service: `app/services/terminology/codesystem_operations.py`. Backing
repository additions: `app/repository/terminology/codesystem_operations.py`
(`get_concept_synonyms`/`get_concept_translations`, for `$lookup`'s
designations) and `app/repository/terminology/hierarchy.py` (for `$subsumes`
— see §2).

### 1.2 ValueSet operations (`app/routers/terminology/valueset_operations.py`)

| Operation | Routes | Notes |
|---|---|---|
| `$expand` | `GET`/`POST /ValueSet/$expand` (canonical URL), `GET /ValueSet/{id}/$expand` (internal id) | Returns a real `ValueSet` resource with a materialized `expansion` — **not** wrapped in `Parameters`, per spec. This closes 08's §1 gap (the old `/value-sets/{id}/expand` endpoint's wrong addressing/shape) by adding the correct operation alongside it, not by replacing it — see §3. |
| `$validate-code` (ValueSet) | `GET`/`POST /ValueSet/$validate-code` (canonical URL), `GET /ValueSet/{id}/$validate-code` (internal id) | "Is this code a *member* of this value set" — this is the operation 08's old `/validate` endpoint was actually standing in for (against a resource+field binding, not a real ValueSet URL). |

Backing service: `app/services/terminology/valueset_operations.py`. Reuses
the existing `expand_value_set()`/`lookup_concept_in_value_set()` repository
methods; the one new repository addition is canonical-URL resolution —
`get_value_set_by_url(url, version)` in `app/repository/terminology/value_sets.py`.

### 1.3 ConceptMap operations (`app/routers/terminology/conceptmap_operations.py`)

| Operation | Routes | Notes |
|---|---|---|
| `$translate` | `GET`/`POST /ConceptMap/$translate` | Resolves by source system+code and `targetsystem` — **never** by a ConceptMap canonical URL (there is no ConceptMap-as-a-resource row to address; see §4.2). Supports `reverse` (swap source/target direction) via a new `get_reverse_translations()` repository method. `result` is only `true` when at least one match's `equivalence` is a real relationship (not `unmatched`/`disjoint`) — implements 09 §4.2's explicit rule, not just "any match found." |
| `$closure` | `POST /$closure` | Real, stateful, **not idempotent** — matches spec exactly, including that it's mounted at the terminology base, not under `/ConceptMap/`. New tables: `terminology_closure_table`, `terminology_closure_concept`. Supports initialize, add-members, and resync-by-version. Returns a `ConceptMap` resource directly (not `Parameters`), per spec. |

Backing service: `app/services/terminology/conceptmap_operations.py`.
Backing repository: `app/repository/terminology/conceptmap_operations.py`
(reverse-direction translate) and `app/repository/terminology/closure.py`
(closure-table state — `get_closure_table`, `create_closure_table`,
`reinitialize_closure_table`, `get_closure_members`, `add_closure_members`,
`get_closure_additions_since`).

### 1.4 `ConceptMap.equivalence` is now real

08's §4 gap — `TerminologyConceptMap.mapping_type` was a free string. It's
now `TerminologyConceptMap.equivalence`, a real Postgres enum
(`app/models/terminology/enums.py`'s `ConceptMapEquivalence`) with the exact
10 FHIR codes (`relatedto`/`equivalent`/`equal`/`wider`/`subsumes`/
`narrower`/`specializes`/`inexact`/`unmatched`/`disjoint`) — migration
`633f7e50edb8`. This is a column **rename + retype**, not an addition —
every existing caller of the old `mapping_type` field (the pre-existing
`/concept-maps` CRUD routes, `/translate`) was updated to match, so there's
no stale field left anywhere. **This is also exactly the mechanism behind
the SNOMED CT ↔ ICD-10-CM mapping use case discussed when this round of
work was scoped** — once reseeded, a SNOMED→ICD-10-CM row is a
`TerminologyConceptMap` row with a real `equivalence` value, translatable
via `$translate` like any other mapping.

### 1.5 `TerminologyCapabilities` — `GET /api/v1/terminology/metadata`

Closes 08's §7 gap. Dynamically built, not static boilerplate: `codeSystem[]`
reflects whatever's actually loaded in the DB right now (empty on a fresh
instance), and `codeSystem[].subsumption` is only `true` for a code system
that actually has `is-a` `TerminologyRelationship` rows (verified live
against both a code system with hierarchy data and one without). See
§4.4 for exactly what this does/doesn't cover (it's not literally at the
spec's own `[base]/metadata` path, since this app has no app-wide
`/metadata` endpoint yet).

### 1.6 Shared infrastructure (reusable beyond terminology)

- **`app/fhir/parameters.py`** — generic FHIR `Parameters` resource
  builder/parser (`build_parameters`, `param_string`/`param_boolean`/
  `param_code`/`param_coding`/`param_integer`/`param_part`, `get_param`/
  `get_param_resource`/`get_params_list`). Deliberately not terminology-specific
  — a future non-terminology operation (ActivityDefinition's `$apply`, the
  example discussed when the `$`-prefix convention itself was being decided)
  reuses this, not a second copy.
- **`app/repository/terminology/hierarchy.py`** — `subsumption_relationship(a, b)`,
  a transitive (recursive-CTE-based, not just direct-edge) IS-A subsumption
  check shared by `$subsumes` and `$closure`. Each operation maps its raw
  `equal`/`a_subsumes_b`/`b_subsumes_a`/`disjoint` result to its own output
  vocabulary — `$subsumes` to `equivalent`/`subsumes`/`subsumed-by`/
  `not-subsumed`, `$closure` to `equal`/`subsumes`/`specializes` (never
  `subsumed-by`, and `disjoint` pairs are omitted rather than reported).
- **OperationOutcome on every error** — closes 08's §7 gap for every new
  route. Every operation raises `app.errors.base.ApplicationError` (never
  `HTTPException`) for its error cases, so the existing global exception
  handler (`app/errors/handlers.py`) converts it to a real `OperationOutcome`
  automatically — no new error-handling code was needed to close this gap,
  just using the mechanism that already existed for every other resource.

### 1.7 What was deliberately left untouched

Every pre-existing non-standard endpoint (`/code-systems`, `/value-sets`,
`/value-sets/{id}/expand`, `/search`, `/lookup`, `/lookup-batch`, `/concepts`,
`/validate`, `/translate`, `/concept-maps`, `/org-concepts`) still exists,
unchanged, at its old path, with its old (bespoke, non-FHIR) response shape.
The new `$`-operations are **additional** routes, not replacements — nothing
that depended on the old shapes breaks. Over time, some of the old endpoints
may become thin redirects to the new ones (e.g. `/translate` → `$translate`),
but that consolidation wasn't part of this round and isn't assumed here.

### 1.8 Data cleared for reseed

Every terminology table was truncated (10 original tables + the 2 new
closure tables) before this work started, per instruction — the schema
changes (especially `ConceptMap.equivalence`'s retype) are clean because
there was no data to migrate. **All terminology tables are empty right
now.** Reseeding (including the SNOMED CT ↔ ICD-10-CM mapping data) is a
separate, explicitly deferred next step — not part of this round.

---

## 2. Verification performed

- `uvx ruff check` clean on every touched/new file (26 files, scoped
  explicitly — not a bare `ruff check app/`, see the note in §5 below about
  why that distinction matters).
- `configure_mappers()` + full app import — clean.
- `mount_routers()` + `app.openapi()` — all 23 terminology paths mount with
  no path or `operation_id` collisions against the 11 pre-existing routes.
- Live end-to-end smoke test against the real dev Postgres DB (temporary
  rows inserted, exercised every operation via the actual `TerminologyService`
  — not mocks — then truncated back to empty): `$lookup` returns correct
  `name`/`display`; `$validate-code` (both variants) returns correct
  `result`; `$subsumes` correctly returns `subsumes`/`subsumed-by`/
  `not-subsumed` for a broader/narrower/unrelated pair; `$expand` returns a
  real `ValueSet` with the right `expansion.contains`; `$translate` returns
  a `match` with the right `equivalence`; `$closure` correctly initializes,
  adds members, and reports the right `subsumes`/`specializes` relationship
  between two newly-added related concepts.
- `TerminologyCapabilities` tested separately, twice: once against an
  empty DB (`codeSystem: []`), once with two temporary code systems (one
  with an `is-a` relationship seeded, one without) confirming
  `codeSystem[].subsumption` is `true`/`false` correctly per code system,
  not a blanket flag — then truncated back to empty both times.
- `pytest --collect-only` across the whole repo — 1130 tests collect; the 9
  pre-existing collection errors (duplicate `test_core.py` module-name
  collisions across resource test folders lacking `__init__.py`) are
  unrelated to this work and predate it — none involve terminology.
- **No terminology-specific automated tests exist** — this was true before
  this round too (confirmed in the original gap-analysis survey) and
  remains true now. The verification above was a manual, live smoke test,
  not a committed regression suite. Writing one is listed as pending work
  in §4.5.

---

## 3. Design decisions worth knowing about

- **Plain `dict`, not Pydantic schemas, for every new operation's
  request/response.** `Parameters.parameter[].value[x]` is a true choice
  type across ~50 FHIR types; a generic dict built via `app/fhir/parameters.py`
  is less code and less drift-risk than either one giant union-typed model
  or 8 near-identical per-operation ones. OpenAPI docs for these routes
  therefore show a generic `object` schema, not a fully-typed one — this is
  a real (accepted) documentation-completeness tradeoff, not an oversight.
- **GET and POST both exist for every idempotent operation**, and always
  converge on the exact same service method — no behavioral drift between
  the two invocation forms. `$closure` is POST-only since it's the one
  non-idempotent operation.
- **Three parallel implementation passes (one per resource: CodeSystem,
  ValueSet, ConceptMap), each creating only new files**, reviewed and wired
  together in one pass afterward (Protocol/DI/router registration, plus
  the `TerminologyClient` Protocol and `RemoteTerminologyClient` additions)
  to avoid merge conflicts on shared files. All three passed their own
  `ruff check`/import checks before integration; the integration pass added
  the cross-cutting wiring and ran the live smoke test in §2.

---

## 4. What's still pending / deliberately out of scope

This is the honest list — don't assume silence elsewhere in this doc means
"done."

### 4.1 `$find-matches` is spec-shaped but non-functional

No `CodeSystem.property` key/value data exists anywhere in this schema to
match against (confirmed: no such table). The endpoint validates its input
correctly and always returns an empty `match[]` with an explanatory
`comment` parameter, rather than faking a result. Building real support
requires adding a generic property store to `TerminologyConcept` first —
not attempted here, and not obviously worth it unless a compositional code
system (e.g. real SNOMED CT post-coordination) is actually going to be used.

### 4.2 `$translate`/`$validate-code`/`$expand` can't resolve by a real resource canonical URL for ConceptMap specifically

`TerminologyConceptMap` has no canonical `url`/`version`/`status` of its
own — it's a flat set of (source, target, equivalence) rows, not a
ConceptMap *resource*. `$translate`'s `url`/`conceptMap`/`conceptMapVersion`
parameters are therefore rejected (400 `not-supported`) rather than
silently ignored, since resolving them would require inventing a fake
canonical URL. CodeSystem and ValueSet don't have this problem — both
already have real canonical URLs on their own tables.

### 4.3 No full `CodeSystem`/`ValueSet`/`ConceptMap` resource CRUD

This was always the explicitly-deferred, bigger item (08's remediation
item 5) — building and seeding operations is a different, smaller problem
than exposing full create/read/update/delete over these as real FHIR
resources with their own lifecycle. Still not started. The existing
`/code-systems`, `/value-sets`, `/org-concepts`/`/concept-maps` CRUD-ish
endpoints remain the only write paths, and they're non-standard (§1.6).

### 4.4 ~~No `TerminologyCapabilities` resource~~ — now implemented

Closed in a follow-up pass after this doc was first written: `GET
/api/v1/terminology/metadata` (`app/routers/terminology/capabilities.py`,
`app/services/terminology/capabilities.py`, backed by a new
`code_systems_with_hierarchy_data()` repository method). Returns `kind:
"instance"`, a dynamically-built `codeSystem[]` (reflecting whatever's
actually loaded right now — empty on a fresh/cleared DB, per §1.7), with
`codeSystem[].subsumption` correctly `true` only for a code system that
actually has `is-a` `TerminologyRelationship` rows (verified live: `true`
for a code system with hierarchy data seeded, `false` for one without).
`expansion.parameter[]` lists the actually-supported `$expand` params.
`validateCode.translations: false`, `translation.needsMap: true`,
`closure.translation: false` — each reflects this implementation's real
behavior, not spec boilerplate.

Not literally at the spec's own `[base]/metadata?mode=terminology` —
this app has no app-wide `/metadata`/`CapabilityStatement` endpoint yet
(that's still a separate, broader, deferred gap affecting every resource
in this server, not just terminology — see
[08-fhir-r4-standard-compliance-gap-analysis.md §7](08-fhir-r4-standard-compliance-gap-analysis.md)),
so it's mounted at this router's own base instead. `mode` is accepted as
a query param (for a spec-literal client) but not branched on, since this
path only ever returns `TerminologyCapabilities`.

### 4.5 No automated tests

Confirmed in §2 — the verification performed for this round was a manual
live smoke test against temporary data, not a committed test suite.
Writing `tests/integration/terminology/` (or similar) that exercises every
operation against the SQLite test fixture this repo's other integration
tests use (`tests/conftest.py`) is real, unstarted work.

### 4.6 Several IN parameters are accepted-and-ignored, not implemented

Each operation's own router-file docstring/description names exactly which
params are live vs. silently ignored vs. actively rejected — this is not
duplicated here param-by-param since it would drift out of sync with the
code. The general pattern: a parameter that would only ADD detail to an
otherwise-correct answer (e.g. `$expand`'s `includeDesignations`,
`activeOnly`, `excludeNested`) is accepted and ignored; a parameter that
would silently change WHICH answer is correct (e.g. `$expand`'s `context`,
inline `valueSet`) is rejected with a 400 `not-supported` instead of
quietly producing a wrong result.

### 4.7 `$lookup`'s `property[]` OUT field (distinct from `designation[]`) isn't implemented

The spec's own worked example response for `$lookup` only exercises
`name`/`version`/`display` and doesn't show `property[]` in use (standard
values would be `parent`/`child`, backed by `TerminologyConcept.parent_concept_id`)
— `designation[]` (the part that *is* implemented) was the field the
example actually demonstrates. Adding `property[]` later is a small,
isolated addition to `lookup_operation()` in
`app/services/terminology/codesystem_operations.py`, not a redesign.

### 4.8 Single-version-per-canonical-URL limitation (CodeSystem and ValueSet)

Both `TerminologyCodeSystem.canonical_url` and `TerminologyValueSet.canonical_url`
are unique columns — this schema stores exactly one version of each,
not a version history. Every operation that accepts a `version`/
`valueSetVersion` parameter checks it against the one stored version
(mismatch = not found) rather than selecting among several. Multi-version
storage would be a schema change (dropping the `unique=True` constraint
and adding version-aware lookup), not attempted here.
