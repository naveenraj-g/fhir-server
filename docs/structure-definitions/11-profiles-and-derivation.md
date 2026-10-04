# Profiles and derivation

This file ties together `derivation`, `baseDefinition`, and `snapshot`/`differential`
(introduced individually in files 01 and 02) into the actual mechanics of how one profile
builds on another — the piece directly underneath the three-layer plan.

## `derivation` and `baseDefinition`, restated precisely

- `derivation: "specialization"` — this `StructureDefinition` defines a genuinely new type,
  adding elements to its base. HL7 does this exactly once per base resource/datatype. This
  project will never author a `specialization`.
- `derivation: "constraint"` — this `StructureDefinition` adds *additional rules* to an
  existing concrete type, without changing what resource type it is. Every profile this
  project will ever author — country layer, organization layer, extension definitions — is
  `constraint`.
- `baseDefinition` — the canonical `url` of the parent. For `constraint`, this is almost always
  populated and points at whatever this profile narrows (which may itself be another profile,
  not necessarily the base spec directly — profiles can chain more than two deep, which is
  exactly the base → country → organization shape).

## Snapshot generation, in more depth

A `differential` is what a human authors — the minimal set of elements this layer actually
changes. A `snapshot` is the *complete, resolved* element list a validator needs, because
validating an instance against "only the elements this layer mentions" is meaningless — you
need to know the full set of rules in effect, including everything inherited silently from
every ancestor.

Producing a snapshot from a differential is, conceptually, a merge operation walked up the
`baseDefinition` chain:

```
snapshot(this) = merge(snapshot(baseDefinition(this)), differential(this))
```

Where "merge" means, per element path: the differential's entry *overrides whatever fields it
explicitly sets* (narrower `min`/`max`, an added `fixed[x]`/`pattern[x]`, an added
`constraint[]` entry, a tightened `binding.strength`) while every field the differential
*doesn't* mention is inherited unchanged from the base snapshot. The recursion bottoms out at a
`StructureDefinition` with no `baseDefinition` (or one of HL7's own base resources, whose
`snapshot` ships pre-computed, as extracted throughout this folder).

**This is non-trivial to implement correctly** — it has to handle: elements the differential
adds that don't exist on the base at all (a brand-new slice, or an extension's own internal
elements), elements the differential narrows versus elements it leaves untouched, and multiple
constraint layers' `constraint[]` lists needing to be *accumulated*, not replaced (a child
profile doesn't remove its parent's invariants — `org-1`/`org-2`/`org-3` still apply to every
Organization even under a country/org profile; the child only ever *adds* to that list). This is
exactly the "snapshot generation" subsystem flagged as one of the harder pieces in the
architecture document's scope discussion.

## How the three-layer plan uses this without necessarily pre-computing a merged snapshot

`docs/architecture/fhir-profiling-and-extensibility-strategy.md`'s §3 design doesn't store a
full merged snapshot at all — it stores each layer's own trimmed differential-shaped
`structure` JSONB, and §3's "Profile resolution" section walks the chain *at resolution time*:

```
chain = [base_profile, country_profile, org_profile]
```

then merges left-to-right into one *effective* constraint set when validating a given
`(org_id, resource_type)` pair, caching the resolved chain since it changes rarely. This is the
same snapshot-generation idea described above, just computed lazily per effective chain rather
than pre-stored as a literal `snapshot.element[]` array on each layer — a reasonable
simplification given this project doesn't need to *publish* its profiles as standalone,
externally-consumable `StructureDefinition` resources (yet) the way HL7 or a public IG does.

## Worked example: the whole chain for Organization

```
StructureDefinition-Organization.json          (HL7 base R4)
  derivation: specialization
  baseDefinition: .../StructureDefinition/DomainResource
  constraints: org-1, org-2, org-3

        ▲ baseDefinition

(hypothetical) IN-Organization                  (country layer)
  derivation: constraint
  baseDefinition: .../StructureDefinition/Organization
  adds: identifier 0..1 → 1..1 (require at least one identifier, narrowing within
        org-1's "name or identifier" requirement toward "identifier specifically")
  adds: a new invariant requiring a GSTIN-shaped identifier for certain org types

        ▲ baseDefinition

(hypothetical) clinic-x-Organization            (organization layer, tenant-authored)
  derivation: constraint
  baseDefinition: .../StructureDefinition/IN-Organization   (chains through the
                                                               country layer, not
                                                               straight to base R4)
  adds: a required custom extension for a preferred-pharmacy reference
  adds: an invariant requiring at least one phone-system telecom entry
```

Validating one instance of this tenant's Organization means: `org-1`/`org-2`/`org-3` from the
base layer still apply (inherited, never removed), *plus* the country layer's tightened
`identifier` cardinality and GSTIN invariant, *plus* the org layer's extension requirement and
phone invariant — all evaluated together as one effective rule set, because every ancestor
narrowed, never widened, what came before it ([`05-cardinality-and-multiplicity.md`](05-cardinality-and-multiplicity.md)'s
rule is what guarantees this composition is even safe to do).

## What's actually implemented today, versus this design

Only the base layer exists in code right now, and only its *structural* half:
`app/fhir/spec/fhir.schema.json` + `app/fhir/validation/base_r4.py` validate cardinality/
required-fields/primitive-formats/required-bindings for base R4 Organization. There is no
country layer, no organization layer, no `fhir_profile` table, and no invariant evaluation
(`org-1`/`org-2`/`org-3` are not yet checked anywhere in code, despite being verified and
documented). The closing file in this folder,
[`12-three-layer-validation-architecture.md`](12-three-layer-validation-architecture.md),
lays out exactly where the line between "built" and "designed but not built" currently sits.
