# The three-layer validation architecture

This is the closing file in this folder by design — everything in Parts 1 and 2 was building
toward being able to state this precisely, grounded in real spec mechanics rather than
analogy. For the concrete engineering decisions (storage schema, validation pipeline steps,
library choices), the authoritative document is
[`docs/architecture/fhir-profiling-and-extensibility-strategy.md`](../architecture/fhir-profiling-and-extensibility-strategy.md) —
this file doesn't repeat those decisions, it shows why they're shaped the way they are.

## The core realization

**Base R4, a country profile, and an organization profile are not three different kinds of
thing.** They are three `StructureDefinition` documents, chained by `baseDefinition`
([`11-profiles-and-derivation.md`](11-profiles-and-derivation.md)), each describable by the
exact same `ElementDefinition` vocabulary covered in Parts 1–2 of this folder:

| Layer | Who authors it | `derivation` | `baseDefinition` points at |
|---|---|---|---|
| **Base R4** | HL7 | `specialization` (for the base resource) | nothing, or a shallow ancestor like `DomainResource` |
| **Country profile** | A national body, or this project on their behalf | `constraint` | the base R4 resource's own canonical URL |
| **Organization profile** | The tenant, via a future admin surface | `constraint` | the country profile's URL (or straight to base R4, if no country layer applies) |

Because all three are the same shape, **one validation engine, applied three times, is the
correct architecture** — not three separate validators. This was confirmed, not assumed: it
matches how HL7's own reference validator and HAPI FHIR's validation module actually work.

## Layer 1 — base R4: HL7 already gives us everything

This is the layer where, as observed at the start of this documentation effort, **HL7 publishes
the rules themselves** — both halves of it:

- **Structural rules** (required elements, cardinality, primitive formats, required-terminology
  bindings) — published as `fhir.schema.json`, a JSON Schema document. Already in this
  codebase: `app/fhir/spec/fhir.schema.json`, validated via `app/fhir/validation/base_r4.py`'s
  `validate_base_r4()`, wired into `OrganizationService.create_organization`/
  `patch_organization` ([`app/services/organization/core.py`](../../app/services/organization/core.py)).
- **Invariants** (cross-field rules) — published as `ElementDefinition.constraint[]` entries
  inside the base resource's own `StructureDefinition` (`profiles-resources.json`). **Verified,
  but not yet enforced**: `org-1`, `org-2`, `org-3` were empirically confirmed against the real
  file this session ([`06-constraints-and-invariants.md`](06-constraints-and-invariants.md)),
  but nothing in `app/fhir/validation/` evaluates them yet — `validate_base_r4()` only checks
  what `fhir.schema.json` can express, and that file has zero invariant logic (confirmed
  empirically: 0 `anyOf`, 2 unrelated `oneOf`, across 60,000+ lines).

So layer 1 is **half-built**: structure is live in production code, invariants are documented
and verified but not yet wired in.

## Layer 2 — country profile: not yet started

A `StructureDefinition` with `baseDefinition` pointing at base R4 Organization, narrowing
cardinality, adding fixed/pattern values, tightening terminology bindings, and/or adding its own
invariants (see every file in [`use-cases/`](use-cases/README.md) for what this concretely looks
like for Organization). Per `docs/architecture/fhir-profiling-and-extensibility-strategy.md`'s
§1, this should be **data**, not a Python class hierarchy — a `ProfileRegistry.for_country(code)`
resolver, not a `USOrganizationProfile`/`INOrganizationProfile` class pair. Nothing in this
category exists in code yet; `fhir_profile` (§3 of that document) is designed but not
implemented.

## Layer 3 — organization profile: not yet started, and structurally different from layer 2

Everything about layer 2 applies here too (same `StructureDefinition` shape, same storage
table), but with one real difference: country profiles can ship as checked-in data, while
organization profiles are **authored at runtime by tenants**, which is why
`docs/architecture/fhir-profiling-and-extensibility-strategy.md`'s §1 flags the narrowing-rule
check (layer `N+1` can never widen what layer `N` already constrained) as something that has to
be enforced **mechanically at save time**, not just assumed — there's no human reviewer in that
path the way there is for a country profile shipped in a PR.

## How one instance gets validated against all three layers

Conceptually (precise pipeline steps are `docs/architecture/fhir-profiling-and-extensibility-strategy.md`
§4's job, reproduced here only to close the loop):

```
1. Resolve the chain for this org_id + resource_type:
     [base_R4_profile, country_profile (if any), org_profile (if any)]

2. Merge into one effective rule set, left to right — each layer only ever
   narrows what came before (05-cardinality-and-multiplicity.md's rule is what
   makes this merge safe to do at all).

3. Check structure (cardinality, types, fixed/pattern, bindings) against the
   effective rule set.

4. Check every invariant from every layer — base, country, and org invariants
   are all evaluated, none replace each other (11-profiles-and-derivation.md's
   "worked example: the whole chain for Organization" shows this concretely).

5. Reject (422, OperationOutcome) on the first failure, or on all failures
   collected together — already this project's existing pattern via
   FhirValidationError.
```

Step 3, for the base layer specifically, is the only one that currently exists in running code.

## What's genuinely still an open decision

Two things this documentation folder deliberately didn't resolve, because they're build
decisions for whoever picks this work up, not spec facts:

1. **Invariant execution: a real FHIRPath library (`fhirpathpy`, as
   `docs/architecture/fhir-profiling-and-extensibility-strategy.md` recommends) vs. hand-written
   Python predicates per `constraint.key`.** The FHIRPath subset `org-1`/`org-2`/`org-3` need is
   small ([`06-constraints-and-invariants.md`](06-constraints-and-invariants.md)'s table), but a
   future org-authored invariant (like [`use-cases/06`](use-cases/06-adding-a-custom-invariant.md)'s
   `.not()`/`or` example) could need more of the language than what's been seen so far — and
   there isn't a way to know the full subset needed in advance, since org profiles are
   tenant-authored and open-ended.
2. **How much of the full profile-validation surface to build at all.** Full spec-complete
   profile validation (snapshot generation, slicing, terminology-server-backed binding
   resolution, extension recursion) is the kind of multi-subsystem undertaking the real HL7
   Java validator took years to mature — versus delegating to that validator directly (as a
   subprocess or sidecar) and only authoring this project's own `StructureDefinition` documents
   for the country/org layers, not the engine that interprets them. Both are legitimate; neither
   has been decided.

## One-sentence summary of where things actually stand

**The base-R4 structural half of layer 1 is live in production code; everything else in this
file — base invariants, the entire country layer, the entire organization layer, and the choice
of how to execute FHIRPath — is accurately designed (in this folder and in
`docs/architecture/fhir-profiling-and-extensibility-strategy.md`) but not yet built.**
