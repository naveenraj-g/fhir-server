# FHIR StructureDefinition — field reference and use-case guide

This folder is the prerequisite reading for
[`docs/architecture/fhir-profiling-and-extensibility-strategy.md`](../architecture/fhir-profiling-and-extensibility-strategy.md).
That document decides *how this codebase will implement* profiling, extensions, and
org-defined business rules (storage schema, validation pipeline, build-vs-buy on FHIRPath).
This folder explains *what the underlying FHIR mechanism actually is*, field by field, so
those decisions make sense on their own terms instead of being taken on faith.

Every field name, cardinality, and code value in this folder was pulled from the real,
machine-readable HL7 R4 definitions — `StructureDefinition`'s own `StructureDefinition`,
`ElementDefinition`'s own `StructureDefinition`, and the official code systems for
`binding-strength`, `constraint-severity`, `discriminator-type`, `type-derivation-rule`, and
`resource-slicing-rules` — not recalled from memory. Where this project's own Organization
work is used as a worked example, it's the actual, already-verified base R4 constraints
(`org-1`/`org-2`/`org-3`, confirmed empirically against HL7's `profiles-resources.json` — see
[`06-constraints-and-invariants.md`](06-constraints-and-invariants.md)) and the actual files
already built this session (`app/fhir/spec/fhir.schema.json`, `app/fhir/validation/base_r4.py`,
`app/fhir/mappers/organization/`).

Spec source: [hl7.org/fhir/R4/structuredefinition.html](https://www.hl7.org/fhir/R4/structuredefinition.html)

## Reading order

**Part 1 — what the resource is and what every field on it means:**

1. [What is a StructureDefinition](01-what-is-a-structuredefinition.md) — the big picture: one
   resource, three jobs (define a base type, profile/constrain an existing one, define an
   extension).
2. [StructureDefinition root-level fields](02-structuredefinition-root-fields.md) — field by
   field: `url`, `version`, `status`, `kind`, `abstract`, `type`, `baseDefinition`,
   `derivation`, `snapshot`/`differential`, and everything else at the top level.
3. [ElementDefinition core fields](03-element-definition-core-fields.md) — the structure that
   actually does the work, living inside `snapshot.element[]`/`differential.element[]`: `path`,
   `min`/`max`, `short`/`definition`, `base`, and the rest of the navigational fields.
4. [Data types and choice elements](04-data-types-and-choice-elements.md) — `type[]`,
   polymorphic `value[x]`-style fields, `fixed[x]`/`pattern[x]`/`defaultValue[x]`, and the
   difference between "must equal exactly" and "must contain at least."
5. [Cardinality and multiplicity](05-cardinality-and-multiplicity.md) — `min`/`max` in depth,
   and the one rule the whole three-layer plan depends on: a profile can only narrow, never
   widen.
6. [Constraints and invariants](06-constraints-and-invariants.md) — `ElementDefinition.constraint[]`,
   FHIRPath, `org-1`/`org-2`/`org-3` as the worked example, and how this maps to
   `app/fhir/validation/`.
7. [Slicing](07-slicing.md) — splitting a repeating element into named, independently-ruled
   sub-lists. Not used by Organization today; documented because a country/org profile for a
   different resource will likely need it.
8. [Terminology and CodeableConcepts](08-terminology-and-codeable-concepts.md) — `binding`,
   the four binding strengths, and directly answers "can we use our own codes and still line
   up with the standard ones" — the dual-coding pattern this project already implements.
9. [Extensions](09-extensions.md) — how an extension is itself a `StructureDefinition`, simple
   vs. complex extensions, `modifierExtension`'s safety rule, and this project's own
   `extension` JSONB column.
10. [Element flags — mustSupport, isModifier, isSummary](10-element-flags.md) — the three
    boolean flags that change how a consumer is allowed to treat an element.
11. [Profiles and derivation](11-profiles-and-derivation.md) — `derivation`, `baseDefinition`
    chaining, and why `snapshot` and `differential` both exist (snapshot generation).

**Part 2 — concrete use cases for this project:**

See [`use-cases/README.md`](use-cases/README.md) for the index. Each file is one realistic
scenario (tightening cardinality, fixing a value, requiring a custom identifier system,
custom codes with a standard crosswalk, requiring a custom extension, adding a custom
invariant), written against Organization since that's the resource already built to strict R4
shape this session.

**Part 3 — the three-layer validation architecture, last, as requested:**

12. [Three-layer validation architecture](12-three-layer-validation-architecture.md) — how
    base R4 (which HL7 already gives us, fully formed) → country profile → organization
    profile fit together as one mechanism applied to three documents, what's already built in
    this codebase, and what's still open.

## What this folder is not

It is not a replacement for `docs/architecture/fhir-profiling-and-extensibility-strategy.md`.
That document has already made real decisions (the `fhir_profile` table shape, the six-step
validation pipeline, `fhirpathpy` as the FHIRPath library, the Tier 1/Tier 2 business-rule
split) — this folder doesn't re-litigate or repeat those; it explains the spec mechanics those
decisions are built on top of, and the closing file links back to that document rather than
duplicating it.
