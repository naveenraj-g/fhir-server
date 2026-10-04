# Use case: requiring a custom identifier system

**Scenario:** a country-layer profile requires every Organization to carry a national
registry identifier (e.g. a GSTIN-style number) — not just "an identifier of some kind"
(already covered by base `org-1`), but specifically one whose `system` is the country's own
registry URI.

## Combining three mechanisms at once

This is a good example precisely because it isn't one single `ElementDefinition` field — it's
cardinality ([`05`](../05-cardinality-and-multiplicity.md)) plus a pattern value
([`04`](../04-data-types-and-choice-elements.md)) plus, if slicing is wanted for precision, the
slicing mechanism ([`07`](../07-slicing.md)):

**Simplest version — no slicing, just "at least one identifier with this system exists
somewhere in the list":** this isn't actually expressible as a plain cardinality/pattern
combination on `Organization.identifier` itself, because `min`/`pattern` apply element-wide,
not "at least one entry in the array must match." This specific shape — "the array as a whole
must contain at least one entry satisfying X" — is exactly what an **invariant** is for, not a
structural constraint:

```json
{
  "path": "Organization",
  "constraint": [
    {
      "key": "org-country-1",
      "severity": "error",
      "human": "Organization must have at least one identifier from the national registry",
      "expression": "identifier.where(system = 'https://example.gov/registry-id').exists()"
    }
  ]
}
```

**More precise version — using slicing**, if the profile additionally wants to say "and that
slice specifically is cardinality `1..1`, not just present somewhere":

```json
{
  "path": "Organization.identifier",
  "slicing": {
    "discriminator": [{ "type": "value", "path": "system" }],
    "rules": "open"
  }
},
{
  "path": "Organization.identifier",
  "sliceName": "national-registry",
  "min": 1,
  "max": "1",
  "patternIdentifier": { "system": "https://example.gov/registry-id" }
}
```

This is the exact worked example already given in [`07-slicing.md`](../07-slicing.md), repeated
here to show *why* you'd reach for slicing over a plain invariant: the invariant version can
only say "at least one exists," while the slicing version can additionally cap it
(`max: "1"` — no more than one registry identifier), order it, and make tooling aware there's a
named, specifically-constrained sub-group within the array rather than an ad hoc rule bolted on
separately.

## Which approach this project should prefer, practically

Given slicing is a genuinely larger subsystem to implement correctly
([`07-slicing.md`](../07-slicing.md)'s closing section), and given the invariant-only version
already expresses the *existence* requirement (the part that actually matters most in
practice — "must have one," as opposed to "must have no more than one"), the pragmatic
sequencing is: build invariant evaluation first (needed anyway for `org-1`/`org-2`/`org-3`,
per [`06-constraints-and-invariants.md`](../06-constraints-and-invariants.md)), and only reach
for slicing later if a real profile genuinely needs the tighter cardinality-per-slice guarantee.

## Shaped for this project's planned storage (invariant-only version)

```json
{
  "invariants": [
    {
      "key": "org-country-1",
      "severity": "error",
      "expression": "identifier.where(system = 'https://example.gov/registry-id').exists()",
      "description": "Organization must have at least one national registry identifier."
    }
  ]
}
```

This is exactly the shape already given as the worked example in
`docs/architecture/fhir-profiling-and-extensibility-strategy.md`'s §3 (`org-clinic-1`, a
different rule but the identical JSON shape) — confirming this use case fits the already-decided
storage design without any change needed to that document.
