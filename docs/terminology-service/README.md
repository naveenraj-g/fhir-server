# Terminology Service

A FHIR R4 terminology subsystem: CodeSystems, ValueSets, Concepts, cross-system
ConceptMaps, per-resource field bindings, and two org-scoped customization
mechanisms (org-owned concepts, display overrides) — all behind a single
`TerminologyClient` Protocol that the rest of the server (and, if
`terminology.backend: remote`, other services) calls without caring whether
the implementation is in-process or over HTTP.

If any of those words — CodeSystem, ValueSet, Concept, ConceptMap, binding
— don't mean anything to you yet, **don't start here.** Start with
[00-what-is-terminology.md](00-what-is-terminology.md), which explains
those ideas from scratch with no code and no schemas. Everything below
assumes you already have that vocabulary and is about how this specific
codebase implements it.

Read in this order if you're new to the subsystem:

0. **[00-what-is-terminology.md](00-what-is-terminology.md)** — what
   "terminology" even means here, explained for someone with zero prior
   FHIR/healthcare-data background. Read this first.
1. **[01-data-model.md](01-data-model.md)** — every table, every constraint,
   why each one exists (`app/models/terminology/terminology.py`).
2. **[02-repository-and-service-layers.md](02-repository-and-service-layers.md)**
   — the mixin composition, what each repository/service method actually
   does, one confirmed bug.
3. **[03-api-routes.md](03-api-routes.md)** — every HTTP route, org-scoping
   enforcement, OpenAPI response-schema pattern.
4. **[04-dispatch-and-remote-client.md](04-dispatch-and-remote-client.md)** —
   the `TerminologyClient` Protocol, embedded-vs-remote dispatch, DI wiring.
5. **[05-seeding-and-external-loaders.md](05-seeding-and-external-loaders.md)**
   — the bulk-import CLI, all five source-format loaders, and the two field-
   binding seed scripts (hand-curated vs. auto-derived from HL7
   StructureDefinitions).
6. **[06-validation-and-field-bindings.md](06-validation-and-field-bindings.md)**
   — what `validate()`/`translate()` actually check, and the real semantics
   of FHIR binding strength in this codebase (hint: it's narrower than the
   spec implies).
7. **[07-org-concepts-and-display-overrides.md](07-org-concepts-and-display-overrides.md)**
   — the two org-scoped customization mechanisms, how they differ, and the
   shared audit log both write to.

## Why this exists as a separate service-shaped thing

Every other resource in this server (`app/routers/<resource>/`, Patient,
Encounter, …) is a thin CRUD layer over one FHIR resource type with no
internal cross-references. Terminology isn't that: a ValueSet references
many Concepts across many CodeSystems, a ConceptMap cross-references two
Concepts that may live in different CodeSystems, and `validate()`/`translate()`
are read-heavy operations against that web of references rather than CRUD on
a single row. It's also the one subsystem explicitly designed to be callable
either **embedded** (same process, same DB, default) or **remote** (a
separate terminology microservice reached over HTTP) — see
[04-dispatch-and-remote-client.md](04-dispatch-and-remote-client.md) — because
a shared terminology service is a realistic thing to split out once multiple
FHIR-server instances need to agree on the same code systems.

## Core model at a glance

```
TerminologyCodeSystem  (one named vocabulary, e.g. "http://loinc.org")
        │ 1-to-many
        ▼
TerminologyConcept      (one code; synonyms, translations, embedding, display_overrides hang off it)
        │ many-to-many (via TerminologyValueSetConcept)
        ▼
TerminologyValueSet     (curated subset of concepts, can span multiple CodeSystems)
        │ 1-to-many
        ▼
TerminologyFieldBinding (wires one resource_type.field_name to one governing ValueSet)

TerminologyConceptMap   (separate, parallel: concept -> concept translation across systems)
TerminologyDisplayOverride (org-scoped relabel of an existing concept's display text)
TerminologyAuditLog     (append-only record of every org-scoped write, from both of the above)
```

Full column-level detail for every one of these is in
[01-data-model.md](01-data-model.md).

## Source files map

| Layer | Path |
|---|---|
| Models | `app/models/terminology/terminology.py` |
| Repository | `app/repository/terminology/` (9-mixin package) |
| Service | `app/services/terminology/` (9-mixin package) |
| Schemas | `app/schemas/terminology.py` |
| Routers | `app/routers/terminology/` (8 sub-routers + `_responses.py`) |
| Client protocol + dispatch | `app/terminology/client.py`, `app/terminology/dispatch.py` |
| Remote HTTP client | `app/terminology/remote_client.py` |
| DI wiring | `app/di/modules/terminology.py`, `app/di/dependencies/terminology.py` |
| Bulk import CLI + loaders | `app/terminology/import_/` |
| Field-binding seed scripts | `app/terminology/seed_field_bindings.py`, `app/terminology/seed_field_bindings_r4.py` |
| Config | `app/core/config.py` — `TerminologyConfig`/`TerminologyRemoteConfig` |

Note: none of the ~34 terminology tables/routes currently have the
`@trace_methods` structured-logging instrumentation described in the root
`CLAUDE.md`'s "Logging & Observability" section — that's only wired up for
the eight auth-rollout resources (Patient, Practitioner, Organization,
Location, HealthcareService, PractitionerRole, Schedule, Slot) plus the
global access-log/error plumbing every resource gets for free.
