# What is a StructureDefinition

Spec: [hl7.org/fhir/R4/structuredefinition.html](https://www.hl7.org/fhir/R4/structuredefinition.html)

## One resource, three jobs

`StructureDefinition` is the single FHIR resource behind all three of these, which look like
different features but are the same mechanism applied with a different `kind`/`derivation`:

| Job | How | Example |
|---|---|---|
| **Define a base type** | `kind = "resource"` (or `primitive-type`/`complex-type`), `derivation = "specialization"`, no `baseDefinition` (or a very shallow one) | HL7's own `Organization`, `Patient`, `HumanName`, `Identifier` — the base R4 spec itself is ~650 `StructureDefinition` resources |
| **Profile (constrain) an existing type** | `kind` matches the base, `derivation = "constraint"`, `baseDefinition` points at the parent's canonical URL | A country-specific "IN Core Organization" that requires a GSTIN identifier; this project's planned country/org layers |
| **Define an extension** | `kind = "complex-type"`, `type = "Extension"`, `derivation = "constraint"`, `baseDefinition = ".../StructureDefinition/Extension"`, `context[]` says where it can attach | A `preferred-pharmacy` extension on `Organization` |

There is no separate FHIR resource for "a profile" or "an extension definition" or "a business
rule." All three are a `StructureDefinition` — the only things that change are a handful of
root-level fields (`kind`, `type`, `baseDefinition`, `derivation`, `context`) and what the
`differential.element[]` list actually contains. This is the single most important fact this
whole documentation folder builds on: **one data shape, one validation engine, three uses.**

## Why this matters for the three-layer plan

Because profiling and base-type-definition are the same mechanism, "base R4 → country profile
→ organization profile" isn't three different systems glued together — it's the same
`StructureDefinition`/`ElementDefinition` shape, three times, chained by `baseDefinition`:

```
StructureDefinition-Organization.json   (HL7's own — base R4, derivation=specialization)
        ▲  baseDefinition
        │
StructureDefinition (hypothetical)       ("IN-Organization" — derivation=constraint)
        ▲  baseDefinition
        │
StructureDefinition (hypothetical)       (one hospital's own profile — derivation=constraint)
```

A validator that can walk *one* `StructureDefinition` and check an instance against its
`snapshot.element[]` list can validate against *any* layer, because every layer is the exact
same shape of document. This is confirmed, not speculative — HL7's own validator and HAPI
FHIR's validation module work exactly this way.

## Two views of the same structure: snapshot vs. differential

Every `StructureDefinition` can carry two parallel lists of `ElementDefinition`s describing the
same resource:

- **`differential`** — only the elements this layer actually *changes* relative to its base.
  For a country profile that only touches `Organization.name` and adds one invariant, the
  differential has two or three entries, not the whole resource. This is what a human actually
  authors.
- **`snapshot`** — the *fully resolved* element list: this layer's differential merged on top
  of its base's own snapshot, recursively up the `baseDefinition` chain. This is what a
  validator actually needs, because you can't know whether `Organization.name` is `0..1` or
  `1..1` by looking at a country profile's differential alone if the country profile didn't
  touch it — you have to know what the base said.

**Producing a snapshot from a differential plus a base's snapshot is itself a non-trivial
algorithm** ("snapshot generation"), and it's the first of the harder subsystems referenced in
[`docs/architecture/fhir-profiling-and-extensibility-strategy.md`](../architecture/fhir-profiling-and-extensibility-strategy.md)'s
scope discussion. For HL7's own base resources, the `snapshot` ships pre-computed (that's what
we extracted and tabulated throughout this folder). For a real multi-layer profile chain
authored by this project, something has to generate the merged view — or the validator has to
walk the chain at validation time instead of pre-computing it. Covered in more depth in
[`11-profiles-and-derivation.md`](11-profiles-and-derivation.md).

## Worked example used throughout this folder

This project's own `Organization` resource — concretely, the real, HL7-published
`StructureDefinition-Organization.json` — is used as the running example for every field
explained in this folder, because it's already been empirically verified against this
project's codebase this session:

```
kind:              resource
derivation:        specialization
baseDefinition:    http://hl7.org/fhir/StructureDefinition/DomainResource
type:               Organization
```

And its three invariants (confirmed by reading the actual file, not recalled):

```
Organization           org-1  error  "SHALL at least have a name or an identifier"
                                      (identifier.count() + name.count()) > 0
Organization.address   org-2  error  "can never be of use 'home'"
                                      where(use = 'home').empty()
Organization.telecom   org-3  error  "can never be of use 'home'"
                                      where(use = 'home').empty()
```

These three rows are `ElementDefinition.constraint[]` entries — explained in full in
[`06-constraints-and-invariants.md`](06-constraints-and-invariants.md).
