# Slicing

Not used by Organization today — none of its repeating elements are sliced in the base spec,
and nothing built this session introduces slicing either. Documented here because a future
country/org profile for a *different* resource (the classic textbook case is `Patient.identifier`
— requiring one slice that's an MRN and a separate slice that's an SSN, each with its own rules)
is very likely to need it, and because `docs/architecture/fhir-profiling-and-extensibility-strategy.md`
's §2 table already flags it as "not urgent for Organization; relevant later."

## What slicing actually is

A repeating element (`0..*`/`1..*`) is normally just "a list of N things, all validated by the
same `ElementDefinition`." Slicing lets a profile say instead: "this list must contain specific
named sub-groups, each with its *own* cardinality and *own* rules" — e.g. "`Patient.identifier`
must contain exactly one identifier where `system` is the MRN namespace, and may contain zero or
one where `system` is the SSN namespace."

Each named sub-group is a **slice**. In a differential, a slice is expressed as one or more
additional `ElementDefinition` entries sharing the same `path` but each carrying a distinct
`sliceName` — the first entry at that `path` also carries the `slicing` definition itself
(the discriminator rule that says *how* to tell which slice an instance value belongs to).

## `ElementDefinition.slicing`

| Field | Card. | Type | Why it exists |
|---|---|---|---|
| `slicing.discriminator` | `0..*` | Element (`type`, `path`) | How to decide which slice a given array entry belongs to — see below. More than one discriminator can combine (e.g. match on both `type` and a nested `value`). |
| `slicing.description` | `0..1` | `string` | Human explanation of the slicing scheme, for anyone reading the profile. |
| `slicing.ordered` | `0..1` | `boolean` | Whether array entries must appear in the same order as the slices are declared. |
| `slicing.rules` | `1..1` | `code` | `closed \| open \| openAtEnd` — see below. |

### `discriminator.type` — the five ways to tell slices apart

| Code | Meaning |
|---|---|
| `value` | Slices differ by having different literal values at the nominated `path`. |
| `exists` | Slices differ by whether the nominated element is present at all (not by its value). |
| `pattern` | Slices differ by matching against the applicable `ElementDefinition.pattern[x]` at the nominated path — i.e., the *slice's own declared pattern* is what distinguishes it, not a fixed literal check. |
| `type` | Slices differ by the data type of the nominated element (relevant for choice elements like `value[x]`). |
| `profile` | Slices differ by which profile the nominated element (or, if the path ends in `.resolve()`, the resolved `Reference` target) conforms to. |

### `slicing.rules` — how strict the "no other entries" check is

| Code | Meaning |
|---|---|
| `closed` | No array entry is allowed that doesn't match one of the declared slices. |
| `open` | Additional, unslicced entries are allowed anywhere in the array. |
| `openAtEnd` | Additional entries are allowed, but only after all the declared slices — requires `ordered: true`, and HL7's own guidance calls this one out as something that "should only be done where absolutely required" since it's harder for tooling to work with. |

## Worked (hypothetical) example

A country profile requiring every `Organization.identifier` list to contain exactly one
national-registry identifier, while still allowing any number of other identifiers:

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

Reading this: the first entry declares that slices of `Organization.identifier` are
distinguished by the literal value at `.system`, and that unslicced entries are still allowed
(`open`) — so an org can still add arbitrary other identifiers. The second entry defines one
slice, named `national-registry`, which must appear exactly once (`1..1`) and must have
`system` equal to the registry's URI (`patternIdentifier`, not `fixedIdentifier` — using the
"must contain at least this" semantics from
[`04-data-types-and-choice-elements.md`](04-data-types-and-choice-elements.md), so the registry
identifier can still carry its own `value`/`use`/`period` alongside the required `system`).

## Why this isn't in scope yet

Building a validator that correctly implements slicing requires, at minimum: evaluating the
discriminator against every array entry to bucket it into the right slice (or "unsliced"),
checking each slice's own `min`/`max` independently, and respecting `rules`/`ordered`. This is
one of the five subsystems `docs/architecture/fhir-profiling-and-extensibility-strategy.md`'s
scope discussion calls out as genuinely non-trivial — not something to build speculatively
before a real use case (a sliced element on some resource this project actually profiles)
exists.
