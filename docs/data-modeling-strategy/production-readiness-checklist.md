# Production-readiness checklist for the current model

These are ordered so the highest-leverage, lowest-effort items come first. None of them require abandoning the fully-normalized relational approach described in [`storage-strategies.md`](./storage-strategies.md) — they're safety nets that make hand-normalization survivable at production scale, and doubly so given the AI/MCP-consumer angle in [`ai-native-considerations.md`](./ai-native-considerations.md). The last section describes the optional, larger step (hybrid JSONB) if the team decides hand-normalization keeps being too expensive to maintain.

---

## 1. Automated FHIR conformance testing (highest leverage)

This single item would have caught the Encounter/Appointment R5 drift automatically instead of requiring a manual audit.

- Run the official **HL7 FHIR validator** (`org.hl7.fhir.validation` / `validator_cli.jar`, Java) against sample resources produced by your `to_fhir_*` mappers, in CI, for every resource type. It validates structure, cardinality, and value sets against the actual R4 (or R4B) specification — not against a hand-maintained comment.
- Alternatively/additionally, use the **`fhir.resources`** Python package (Pydantic models auto-generated from HL7's own StructureDefinitions for R4) purely as a validation oracle: deserialize your mapper's JSON output into `fhir.resources`'s `Patient`/`Encounter`/etc. classes and let *its* validation catch spec violations, without touching your own ORM models or mappers.
- Add a CI job that runs this validation against a fixture set (one representative instance per resource) on every PR that touches `app/models/`, `app/fhir/mappers/`, or `app/schemas/`.

## 2. One source of truth for cardinality/required-ness

Right now, "is this field required" is documented in three disconnected places per resource: a code comment (`# 1..1 Reference(...)`), the SQLAlchemy `nullable=` flag, and (sometimes) Pydantic schema validation. The audit found these three disagree with each other in most resources.

- Pick exactly one layer to *enforce* required-ness — most FastAPI/Pydantic-based projects enforce it at the Pydantic schema layer (input validation) and treat the DB `nullable` flag as a secondary safety net, not the primary contract.
- Whichever layer you pick, make it the only one referenced by the `/new-fhir-resource` and `/fhir-db-model` skill docs, so new resources don't reintroduce the same three-way disagreement.

## 3. Generate models from the spec instead of hand-writing them

The root cause of most audit findings (missing elements, wrong cardinality, R5 leakage, forked enum types) is that every resource is typed out by hand from a human's reading of the spec page.

- Consider generating the *enum value sets* at minimum from HL7's machine-readable FHIR R4 definitions (`profiles-types.json`/`valuesets.json` from the FHIR R4 spec package, or via `fhir.resources`'s already-generated Python enums) rather than hand-typing `class EncounterStatus(str, Enum): ...`. This alone would have prevented the Observation `obs_encounter_ref_type` fork and the Encounter/Appointment R5 value-set drift.
- Full SQLAlchemy model generation from StructureDefinitions is a bigger investment and not necessary immediately — but even generating just the enums and the required/optional cardinality table (as a checked-in JSON manifest each model can be diffed against in CI) would remove an entire class of future bugs cheaply.

## 4. A repo-wide reference-integrity sweep

The audit found ~12 resources where a `Reference` column to a table that demonstrably exists locally (Encounter, Organization, Location, Patient) is missing `ForeignKey`, `index=True`, and `lazy="selectin"` — inconsistently, not systematically, which suggests it's an oversight rather than a deliberate choice.

- Treat this as a standalone, mechanical cleanup pass — resource by resource, using `DocumentReference.custodian`, `RelatedPerson.patient`, and `ServiceRequest.encounter` as the reference implementations to match.
- Add a lint/CI check (even a simple script grepping for `_type = Column(Enum(...ReferenceType...` without a matching `ForeignKey` on the sibling `_id` column) so this doesn't silently regress again.

## 5. Decide what "shared enum" means, in writing, and enforce it

`organization_reference_type` and `encounter_reference_type` are meant to be singleton Postgres enum types reused everywhere — CLAUDE.md says so explicitly — but the audit found this rule violated in both directions (a duplicate type created for Observation; a missing `create_type=False` for Patient).

- Add a migration-time check (or a unit test that inspects `Base.metadata` for duplicate enum type *names* mapped to different Python enum classes) so a forked type is caught before the migration ships, not after.

## 6. Plan for resource history / versioning now, even if you don't build it yet

FHIR's `vread`/`_history` operations expect every resource to have a version history. A fully normalized schema makes this expensive to add later (a parallel history table per resource, doubling the schema again). Decide explicitly whether this project needs to support FHIR resource versioning:
- If yes: budget for it now while the resource count is 35, not later when it's 100+.
- If no (i.e., this server is not meant to be a spec-complete general-purpose FHIR server, just a FHIR-*shaped* API over an app-specific system): document that as an intentional scope decision, since it affects how "production-ready" is even being measured.

## 7. AI/MCP-specific hardening

Since every endpoint here doubles as an MCP tool for an AI agent (per `CLAUDE.md`'s "OpenAPI Spec = MCP Contract"), a couple of items are specific to that consumer and don't apply the same way to a human-only API. See `ai-native-considerations.md` for the full reasoning.

- **Item 1 above (conformance testing) is the single most important item on this whole list for that reason** — an autonomous agent has no equivalent of a human noticing a chart "looks wrong," so a spec-fidelity bug that would just be an annoyance in a human UI can get silently acted on by an agent instead.
- **Keep MCP-facing `summary`/`description` strings accurate as a first-class review item**, not just documentation — they're the LLM's only source of truth for what a field/route means. Fold this into whatever review process already checks `/openapi.json` after schema changes.
- **Verify agent-initiated writes are distinguishable from human-initiated ones** in `created_by`/`updated_by` and in `AuditEvent`/`Provenance` entries, now that MCP exposes create/update operations to an AI caller, not just reads. If that distinction isn't currently captured, decide whether it needs to be before AI-driven writes go to production.

## 8. If hand-normalization keeps proving expensive: the hybrid JSONB option

If, after doing 1–6, new resources still keep introducing spec-fidelity bugs because the schema surface is simply too large to hand-maintain, the pragmatic next step is **not** a full document-store rewrite — it's adding a `resource_json JSONB` column to each resource table alongside the existing normalized columns, per the hybrid pattern in `storage-strategies.md`:

- Make the JSONB column the write-time source of truth (validate it against the FHIR schema, per item 1, on every write).
- Derive the handful of normalized "hot" columns you actually query/join on (`user_id`, `org_id`, `status`, `subject_id`, the standard columns) from that JSON at write time, rather than the two independent mapper files (`fhir.py`/`plain.py`) reconstructing FHIR JSON from 20 child tables after the fact.
- This can be introduced resource-by-resource, starting with the resources the audit flagged as highest-risk (Encounter, Appointment, PractitionerRole, InsurancePlan) — it directly sidesteps their R4/R5 drift problem, since the stored JSON would just *be* correct R4 JSON once validated, with no lossy flatten/reconstruct round-trip in between.
