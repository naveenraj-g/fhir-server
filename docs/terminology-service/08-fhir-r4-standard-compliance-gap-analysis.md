# FHIR R4 Terminology Module — Standard Compliance Gap Analysis

> **⚠️ Point-in-time snapshot — most of this list is now closed.** This
> doc captured the gap *before* the rebuild it motivated. For current
> status, read
> [10-fhir-r4-standard-operations-implemented.md](10-fhir-r4-standard-operations-implemented.md)
> instead — it says precisely what's real now vs. what's still open (it's
> narrower than this list: `$subsumes`, `$closure`, `$lookup`/`$validate-code`
> ×2/`$expand`/`$translate`, `ConceptMap.equivalence`, `OperationOutcome`
> routing, and `TerminologyCapabilities` — items 1-8 below — are all now
> done). This doc is kept as the original audit, not updated item-by-item,
> since rewriting "missing" to "done" throughout would erase the record of
> what was actually found before the rebuild.

This file answers one question: **if an external, standards-compliant FHIR
client pointed itself at this server's terminology subsystem, how much of
what it expects would actually be there?** It assumes you've already read
[00-what-is-terminology.md](00-what-is-terminology.md) (what a CodeSystem/
ValueSet/ConceptMap/binding *is*) and at least skimmed
[03-api-routes.md](03-api-routes.md) (what this codebase's own routes
actually do). This file doesn't re-explain either — it lines them up
against the spec and says, item by item, compliant / partial / missing.

**Spec reference:** https://www.hl7.org/fhir/R4/terminology-module.html,
https://www.hl7.org/fhir/R4/terminology-service.html

Related, older planning doc:
[`docs/new-features-comp/01-fhir-operations/02-terminology-operations.md`](../new-features-comp/01-fhir-operations/02-terminology-operations.md)
sketches a from-scratch FHIR-operations implementation plan (raw-JSONB
`CodeSystem`/`ValueSet` tables, `$expand`/`$lookup` routers). It predates —
and its proposed schema diverges from — the relational schema actually
built in [01-data-model.md](01-data-model.md). This file instead audits
what exists **today**, with exact file/line references, rather than
re-proposing a schema from zero.

## What FHIR R4 actually requires

The "terminology module" isn't one endpoint — it's four resource types
plus a fixed set of standard operations, all addressed by **canonical
URL**, all exchanged as real FHIR resource bodies:

| Piece | Spec requirement |
|---|---|
| **`CodeSystem`** resource | Full RESTful CRUD (`create`/`read`/`update`/`delete`/`search`/`history`) at `/CodeSystem`, with `url`, `version`, `status` (draft\|active\|retired\|unknown — required binding), `content` (not-present\|example\|fragment\|complete\|supplement), hierarchical `concept[]` with nested `concept.concept[]`, `designation[]` (synonyms per language/use), `property[]` |
| **`ValueSet`** resource | `/ValueSet` CRUD, `compose.include[]`/`exclude[]` (by system, by explicit `concept[]`, by `filter[]`, or by referencing another ValueSet), `expansion` as a materialized sub-resource |
| **`ConceptMap`** resource | `/ConceptMap` CRUD, `group[].element[].target[]` where each target carries a **required-binding `equivalence`** code: `relatedto\|equivalent\|equal\|wider\|subsumes\|narrower\|specializes\|inexact\|unmatched\|disjoint` |
| **`NamingSystem`** resource | Formally registers an org's own code system OID/URI |
| **`$lookup`** | `GET/POST [base]/CodeSystem/$lookup?system=...&code=...` → a `Parameters` resource with `name`, `display`, `designation[]`, `property[]` |
| **`$validate-code`** | On both `CodeSystem` and `ValueSet` → `Parameters` with `result` (boolean), `message`, `display` |
| **`$expand`** | `[base]/ValueSet/$expand?url=...\|id=...&filter=...&count=...&offset=...` → a full **`ValueSet` resource** with `.expansion.contains[]`, not a bare list |
| **`$translate`** | `[base]/ConceptMap/$translate?system=...&code=...&target=...` → `Parameters` with `result`, `match[]` (each carrying `equivalence` + `concept`) |
| **`$subsumes`** | Tests whether one code subsumes another in a hierarchy → `Parameters.outcome` = `equivalent\|subsumes\|subsumed-by\|not-subsumed` |
| **`$closure`** | Maintains an incremental transitive-closure table across repeated calls |
| `CapabilityStatement` | Must declare, per resource type, which of the above operations the server actually supports |

Addressing is always by **canonical URL** (optionally `\|version`), never an
internal DB integer PK — that's the mechanism that lets one FHIR server's
ValueSet reference be resolved by any *other* FHIR system without a
proprietary lookup step first.

## What this codebase actually has

Everything lives under a **non-FHIR custom REST API** at
`/api/v1/terminology` (`app/routers/terminology/__init__.py` — mounted
separately from `/api/fhir/v1`, per its own docstring). None of it speaks
FHIR resource shapes:

| Endpoint (`app/routers/terminology/`) | What it does | FHIR equivalent it's standing in for |
|---|---|---|
| `GET /code-systems` | Lists `TerminologyCodeSystem` rows as `CodeSystemListResponse` | `GET /CodeSystem` search — returns a DB-row shape, not a `CodeSystem` resource |
| `GET /value-sets`, `GET /value-sets/{id}/expand` | Lists/expands by **internal integer `id`** (`value_sets.py:42`) | `GET /ValueSet`, `$expand` — wrong key (no canonical-URL addressing), returns a flat list, not a `ValueSet.expansion` |
| `POST /lookup`, `/lookup-batch` | system+code → concept row | `$lookup` — custom `LookupResult` JSON, not a `Parameters` resource |
| `POST /validate` | resource+field+system+code → valid/invalid | `$validate-code` — scoped to this app's own `TerminologyFieldBinding` (resource+field), not a ValueSet URL; no `Coding`/`CodeableConcept` input |
| `POST /translate`, `GET/POST /concept-maps` | system+code+target → stored mappings | `$translate` / `ConceptMap` — `mapping_type` is a free-text string, not FHIR's required `equivalence` enum |
| `GET/POST/PATCH/DELETE /org-concepts` | Org-scoped custom codes | No FHIR equivalent — closest is a `CodeSystem` with `content=supplement` plus a `NamingSystem`, not modeled that way here |
| *(none)* | **No `$subsumes`**, despite `TerminologyRelationship` (an IS-A hierarchy table, `app/models/terminology/terminology.py:139-154`) already existing and populated | Missing entirely |
| *(none)* | **No `$closure`** | Missing entirely |
| *(none)* | **No `TerminologyCapabilities`** resource for this server's terminology operations | Missing entirely — see [09-fhir-r4-terminology-standard-reference.md §6](09-fhir-r4-terminology-standard-reference.md#6-terminologycapabilities) for why this, not a generic `CapabilityStatement` entry, is the actual terminology-specific gap |

`/display-overrides` and `/audit-log` (org-scoped relabeling of existing codes, and a governance trail) used to be listed here — both were removed outright (not just deferred) rather than carried forward half-built while this rebuild is underway. See [09-fhir-r4-terminology-standard-reference.md](09-fhir-r4-terminology-standard-reference.md) for the standard this rebuild follows, and `app/repository/terminology/__init__.py`'s docstring for why audit logging specifically needs an app-wide design, not a terminology-only one.

## Core gaps, concretely

1. **Wrong addressing scheme.** `expand_value_set(value_set_id: int, ...)`
   (`app/routers/terminology/value_sets.py:42`) takes the internal PK. A
   compliant `$expand` takes `url` (+ optional `|version`). There's also no
   "resolve canonical URL → internal id" lookup exposed, so an external
   caller has no path in at all.
2. **No FHIR resource output anywhere.** Every response is a bespoke
   Pydantic shape (`ValueSetExpandResponse`, `ValidateResponse`,
   `TranslateResponse`, … — `app/schemas/terminology.py`). A compliant
   server must be able to return an actual `ValueSet`/`Parameters`/
   `CodeSystem` body, at minimum behind `Accept: application/fhir+json` —
   the same dual-format pattern this codebase already applies to every
   other resource (per the root `CLAUDE.md`'s Content Negotiation section)
   but never extended here.
3. **Errors bypass `OperationOutcome`.** The terminology router raises
   plain `HTTPException(status_code=..., detail=...)` throughout (e.g.
   `value_sets.py:50`, all of `org_concepts.py`). Every other resource in
   this server funnels errors through `ApplicationError` →
   `OperationOutcome` (`app/errors/handlers.py`); terminology does not —
   this is an inconsistency with the rest of the codebase, independent of
   the FHIR-spec question.
4. **`ConceptMap.equivalence` isn't modeled.** `TerminologyConceptMap
   .mapping_type` (`app/models/terminology/terminology.py:304`) is an
   unconstrained string. FHIR requires one of the 10 `equivalence` codes
   under a required binding — nothing today stops
   `mapping_type="whatever"`.
5. **No `$validate-code` against a real ValueSet URL.** `/validate` only
   checks against this app's own `TerminologyFieldBinding` (resource +
   field) — a local convenience concept, not the spec's `ValueSet
   /$validate-code` (validates a code against *any* ValueSet by URL,
   independent of which resource field uses it).
6. **No `$subsumes`**, even though the hierarchy data
   (`TerminologyRelationship`, IS-A edges) already exists in the DB — this
   is the cheapest gap to close, since the storage layer is already there
   and only an operation needs to be built on top of it.
7. **No `TerminologyCapabilities` resource** for terminology — a real FHIR
   client (or a conformance tester) has no way to discover what's
   supported here. Not the same gap as a generic `CapabilityStatement`
   entry (every mounted resource needs one of those regardless of
   terminology) — see
   [09-fhir-r4-terminology-standard-reference.md §6](09-fhir-r4-terminology-standard-reference.md#6-terminologycapabilities).
8. **Designations/properties not exposed.**
   `TerminologyConceptSynonym`/`TerminologyConceptTranslation`
   (`app/models/terminology/terminology.py:109-136`) exist in the DB but
   `$lookup`'s response (`LookupResult`) never surfaces them as FHIR
   `designation[]`.

## Bottom line

What exists today is a **working, useful internal terminology service** —
code systems, value sets, lookup, translate, and org-scoped custom codes.
But it is **not FHIR R4
terminology-module compliant** in any formal sense: it doesn't expose
`CodeSystem`/`ValueSet`/`ConceptMap` as FHIR resources, doesn't address by
canonical URL, doesn't implement the standard `$lookup`/`$validate-code`/
`$expand`/`$translate`/`$subsumes` operation contracts, and doesn't return
`Parameters`/`OperationOutcome`. It's internally consistent and well-built
for *this app's own validator* to consume (see
[06-validation-and-field-bindings.md](06-validation-and-field-bindings.md))
— but a third-party FHIR client pointed at this server's terminology
endpoints today would get nothing it recognizes.

## Suggested remediation order (not yet started)

Cheapest-to-most-involved, matched against what the data layer already
supports:

1. **`$subsumes`** — pure read over the already-populated
   `TerminologyRelationship` table; no schema change needed.
2. **`$lookup`/`$validate-code`/`$expand`/`$translate` as FHIR-shaped
   wrappers** — keep the existing service/repository logic, add a
   thin `Parameters`-in/`Parameters`-out (or `ValueSet`-out, for
   `$expand`) adapter layer in front of it, and switch `$expand`'s/
   `$validate-code`'s addressing from internal `id` to `canonical_url`
   (+ optional `version`).
3. **`ConceptMap.equivalence`** — add the real FHIR enum, migrate
   `mapping_type` onto it (same `_model_<field>`-by-name-not-value
   pattern the root `CLAUDE.md` already documents for other enum
   conversions).
4. **`OperationOutcome` on error** — route terminology errors through the
   same `ApplicationError` hierarchy every other resource already uses.
5. **Full `CodeSystem`/`ValueSet`/`ConceptMap` resource CRUD +
   a `TerminologyCapabilities` resource** — the bigger lift; only worth it
   once an actual external-FHIR-client consumer is in scope, as opposed to
   this server's own internal validator being the only caller.
