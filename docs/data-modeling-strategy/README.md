# Is the current data model production-ready?

**Context this doc assumes:** this is an **AI-native EMR/EHR**, not a general-purpose FHIR interoperability repository. FHIR is one interface into the system (and the interop/export contract, and — per `CLAUDE.md`'s "OpenAPI Spec = MCP Contract" section — the schema AI agents interact with as tools), not the system's only job. Both halves of "AI-native EMR" matter for how the data should be modeled — see below.

**Short answer:** for a native EMR, one hand-normalized SQL table per FHIR resource (with a child table for every `0..*` element) is the *standard, correct* architecture — not a compromise. Real EMR vendors (Epic's Chronicles/Clarity, Cerner's Millennium, athenahealth, OpenMRS, OpenEMR) all keep a deeply normalized internal relational schema built around clinical workflows and generate FHIR as an export/interop layer on top, exactly like this project's `Router → Service → Repository → ORM Model` + `fhir.py`/`plain.py` mapper pattern. A native EMR needs real joins, real referential integrity, and typed columns for scheduling, billing, and clinical logic — a JSONB blob store would make that job *harder*, not easier, which is why systems whose sole job is FHIR exchange (see below) make a different tradeoff than a system like this one.

What that reframing changes is *where the risk sits*: since FHIR here is an adapter/export contract over the real source of truth (the normalized schema), not the source of truth itself, "production-ready" mostly means making sure that adapter layer can't silently drift from the spec — which is exactly what the [model audit](../test/models-fhir-r4-audit.md) caught happening (Encounter/Appointment built against R5 instead of R4) with nothing automated to catch it. That's the real gap to close, not the choice of relational storage itself.

This folder has four documents:

| File | What it covers |
|---|---|
| [`storage-strategies.md`](./storage-strategies.md) | How HAPI FHIR, Azure/Microsoft FHIR Server, Google Cloud Healthcare API, IBM FHIR Server, and Aidbox store resources internally, why that's a different problem from a native EMR, and where a hybrid pattern still applies here |
| [`ai-native-considerations.md`](./ai-native-considerations.md) | Why granular typed data serves an AI/MCP tool-calling agent even better than a human UI, and why spec-fidelity bugs are *more* dangerous with an autonomous consumer than a human one |
| [`production-readiness-checklist.md`](./production-readiness-checklist.md) | Concrete, incremental steps to harden the current architecture — mainly around keeping the FHIR mapper/adapter layer spec-faithful over time |
| [`scalability-performance-analysis.md`](./scalability-performance-analysis.md) | A different angle: given the normalized relational choice is correct, is the actual query/index/FK/pagination design ready for real multi-tenant load — indexing, referential integrity, round-trip counts, bulk writes |
| [`organization-reference-design.md`](./organization-reference-design.md) | A clean-slate, spec-verified reference schema for Organization — every column justified against the actual R4 binding strength/cardinality, applying the lessons of the two docs above to one resource end-to-end |

## The one-paragraph version

Systems whose *entire job* is being a FHIR interoperability repository (HAPI, Azure Health Data Services, Google Cloud Healthcare API, IBM FHIR Server, Aidbox) store the resource as a **JSON/JSONB document** and layer a generic search-parameter index on top, because for them FHIR *is* the data model — there's no separate internal domain to serve. A native EMR is a different animal: FHIR is an export/interop contract sitting on top of a schema that also has to support the actual clinical/business logic of running a care setting, so full relational normalization (what this project does) is the right call, not a corner cut. The thing that *does* need production-grade rigor is the translation layer between the two — the mappers and enums that turn normalized rows into FHIR JSON — because that's where spec drift (like the R4/R5 mixup found in the audit) actually lives. See the checklist doc for how to harden that layer.

## Recommendation for this codebase

1. Fix the audit's action items first (they're real bugs regardless of architecture).
2. Harden the mapper/adapter layer per `production-readiness-checklist.md` — spec-conformance testing in CI is now the **highest-priority** item, not just the highest-leverage one: with an MCP/AI agent as a consumer, a wrong FHIR value (like the R5 codes the audit found) can get acted on autonomously with no human in the loop to notice it looks off, per `ai-native-considerations.md`.
3. Verify agent-initiated writes are distinguishable from human-initiated ones in `created_by`/`updated_by`/`Provenance`/`AuditEvent` — this matters specifically because MCP exposes write operations to an AI caller, not just read ones.
4. Treat the JSONB-hybrid idea in `storage-strategies.md` as a narrow, optional tool for specific pain points (e.g. genuinely open-ended FHIR `extension` data, or resource history/versioning) rather than a referendum on the overall architecture — the core normalized schema is the right foundation for an AI-native EMR and isn't what needs reconsidering.
