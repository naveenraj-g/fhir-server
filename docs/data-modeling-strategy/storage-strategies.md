# How production FHIR servers actually store resources

There are three broad strategies in use in real deployments. This project currently uses #1 — and for a **native EMR** (a system whose main job is running clinical/business workflows, with FHIR as an interop/export interface on top) that's the right choice, not a compromise. Options 2 and 3 below come from systems whose main job *is* FHIR exchange itself — a different problem with a different natural answer. Real EMR vendors (Epic, Cerner, athenahealth, OpenMRS, OpenEMR) all use option 1 internally for exactly this reason.

---

## 1. Fully normalized relational model (this project's current approach)

Every FHIR resource type gets its own table. Every `0..*` (repeating) BackboneElement gets its own child table. `CodeableConcept` fields get flattened into `code`/`system`/`display`/`text` columns. `Reference` fields become `_type` + `_id` column pairs, optionally with a real foreign key. This is what `app/models/` does for all 35 resources.

**Who else does this (in part):** internal/vertical systems that expose a FHIR-*shaped* API over what is fundamentally an app-specific schema, rather than trying to be a general-purpose, spec-complete FHIR server. It's common in EHR-adjacent products that only need to support a handful of resource types deeply, not the whole R4 resource list.

**Pros:**
- Real foreign keys, real `NOT NULL` constraints, real indexes — the database itself can (in principle) enforce integrity.
- Trivial to write ordinary SQL joins/reports/analytics queries against.
- No separate "search index" system needed — you query the normalized columns directly.
- Familiar to any backend team; no FHIR-specific infrastructure to run.

**Cons (all confirmed as *live issues* in this codebase by the audit):**
- Every resource is a **manual spec-translation exercise**. There is no automatic check that a hand-written `Enum` matches the FHIR R4 value set, that a `0..*` element got a child table instead of a flattened column, or that a `1..1` required field got `nullable=False`. The audit found all three failure modes across multiple resources.
- **No defense against spec-version drift.** `Encounter`, `Appointment`, and `PractitionerRole` were built against FHIR **R5** instead of R4 with nothing catching it — because there's no automated conformance check, just code comments.
- **Extensions are second-class.** FHIR resources can carry arbitrary `extension` arrays; a fully normalized schema either ignores them, needs a generic side-table, or requires a migration every time a new extension needs to be queryable.
- **Resource history/versioning (`vread`, `_history`) is expensive to bolt on** — you'd need a parallel history table per resource, doubling the schema surface again.
- **Schema churn scales with resource count.** Every new FHIR element, every new resource type, is a migration plus a matching mapper change in two directions (`to_fhir_*` / `to_plain_*`). At 35 resources and ~18,600 lines of model code already, this cost is already visible.

---

## 2. Document store + generic search-parameter index (what most production FHIR servers actually do)

The resource is stored as-is — a JSON (or JSONB) document — in a resource-type or even fully generic table. A **separate indexing layer** extracts only the fields FHIR defines as "SearchParameters" (e.g. `Patient.name`, `Observation.code`, `Encounter.date`) into narrow, generic index tables that support search without needing a bespoke column for every element.

**Real examples:**
- **HAPI FHIR JPA Server** (the most widely deployed FHIR reference implementation): stores each resource version as a compressed JSON/XML blob in `hfj_resource`/`hfj_res_ver`, then extracts search parameters into generic tables like `hfj_spidx_string`, `hfj_spidx_token`, `hfj_spidx_date`, `hfj_spidx_quantity`, `hfj_spidx_number`, `hfj_spidx_uri`, `hfj_spidx_coords` — one narrow table *per datatype*, shared across every resource type, not one table per resource element.
- **Azure Health Data Services / Microsoft FHIR Server** (open source): stores the resource as JSON (SQL Server JSON columns, or Cosmos DB as a native document store), with search parameters extracted into indexed columns/tables.
- **Google Cloud Healthcare API FHIR store:** fully managed; the resource is a document, full stop — there is no relational schema exposed at all. Analytics is handled separately via BigQuery export/flattening, decoupled from the transactional store.
- **IBM FHIR Server:** Db2/Postgres-backed; same blob-plus-generic-search-parameter-table split as HAPI (`logical_resources`, `resource_versions`, then per-parameter-type value tables).

**Pros:**
- **Spec fidelity by construction.** The stored document *is* the FHIR resource — there's no hand-flattening step where an R4/R5 mismatch or a missed cardinality rule can creep in. Validate the JSON against the official FHIR schema/profile once, on write, and you're done.
- **Extensions and profile variants are free** — they're just more JSON, no schema change needed.
- **Versioning/history is nearly free** — insert a new document row per version instead of a parallel table.
- **New resource types are cheap to add** — no 500-line model file, just a new resource-type partition/table and (if needed) new search-parameter extraction rules.

**Cons:**
- Complex relational joins/aggregations across resources are harder — you're querying JSON paths or a secondary index, not normalized columns.
- Requires either a real FHIR validator (to enforce conformance on write) or you lose the "spec fidelity by construction" benefit.
- Less familiar to teams used to plain relational/ORM development; DI/repository patterns need to be rethought around a document store instead of ORM models.

---

## 3. Hybrid: normalized "hot" columns + JSONB source of truth

A middle ground used in practice by platforms like **Aidbox** (Health Samurai): one table per resource type, but the row's core content is a `JSONB` column holding the canonical FHIR resource, plus a handful of **generated/indexed columns** (via Postgres generated columns or expression indexes) for the specific fields that need to be searched or joined on quickly (tenant `org_id`/`user_id`, `status`, `subject_id`, etc.).

**Pros:**
- Keeps the tenant/ownership columns, FK-style joins, and hot-path query performance this codebase already relies on (`user_id`, `org_id`, `<resource>_id` sequences, standard columns).
- The JSONB column is always a complete, valid FHIR resource — no lossy round-trip through 20 child tables and two mapper files. Even if a normalized column is wrong or missing, the canonical resource is still correct.
- Feasible to *retrofit* onto an existing normalized schema incrementally, resource by resource, instead of a big-bang rewrite.
- Naturally solves the extensions and versioning problems from option 1 — extensions just live in the JSONB blob; a history table only needs to store the JSONB + version number, not 20 child tables' worth of rows.

**Cons:**
- Two representations of the same data (JSONB + normalized columns) can drift out of sync if not written transactionally together — needs a single write path, not two independent ones.
- Doesn't eliminate the mapper-correctness problem entirely if the normalized columns are still derived by hand from the JSONB rather than the other way around; the highest-value version of this pattern makes the **JSONB the source of truth** and derives normalized columns from it (via generated columns or a write-time projection step), not the reverse.

---

## Which one is "correct" — for a native EMR specifically

For a native EMR, option 1 (this project's approach) is correct: the schema needs to serve real clinical/business logic — scheduling, billing, decision support, reporting — not just store-and-forward FHIR documents, and that requires real joins and real referential integrity that a document store makes harder. The systems that chose option 2 (HAPI, Azure, Google, IBM) are solving a narrower problem — being *only* a spec-compliant FHIR repository for exchange — where the resource *is* the whole data model and there's no separate internal domain to serve.

What does carry over from those systems, though, is the lesson about *how they got spec fidelity*: not by hand-flattening, but by validating against the spec mechanically. For a native EMR, the equivalent move isn't to switch storage models — it's to make sure the mapper/adapter layer that translates normalized rows into FHIR JSON is validated the same rigorous way (see `production-readiness-checklist.md`), since that's the layer actually doing the same job those systems do natively. Option 3 (hybrid JSONB) is worth keeping in your back pocket narrowly — for genuinely open-ended data like FHIR `extension` arrays, or if resource history/versioning becomes a real requirement — not as a wholesale replacement for the normalized core.
