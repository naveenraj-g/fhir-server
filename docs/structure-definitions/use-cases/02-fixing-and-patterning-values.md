# Use case: fixing and patterning values

**Scenario A (fixed):** a single-purpose clinic profile where every Organization is, by
definition, a healthcare provider — the `type` should always be exactly `prov`
(`http://terminology.hl7.org/CodeSystem/organization-type`), with no other value ever legal.

**Scenario B (pattern):** a country profile requiring every Organization's `active` status to
be explicitly populated (not absent) with a specific minimum shape, while leaving room for
other fields on the same element.

## Why this is `fixed[x]`, not `pattern[x]`, for scenario A

Per [`04-data-types-and-choice-elements.md`](../04-data-types-and-choice-elements.md): `fixed[x]`
means "must equal this exactly," appropriate when there's genuinely only one legal value and
nothing else should ever be allowed alongside it — scenario A fits this exactly, since a
single-purpose clinic profile has no reason to allow *any* other `type` value, custom or
standard.

```json
{
  "path": "Organization.type",
  "fixedCodeableConcept": {
    "coding": [
      { "system": "http://terminology.hl7.org/CodeSystem/organization-type", "code": "prov" }
    ]
  }
}
```

Note this is `fixedCodeableConcept` on `Organization.type` as a whole (the `CodeableConcept`),
not on `.coding` — fixing the whole concept this way means `text` must also be absent (or match
exactly whatever's fixed, since nothing else was specified), consistent with `fixed[x]`'s
"nothing beyond what's specified" rule for complex types.

## Why scenario B should use `pattern[x]`, not `fixed[x]`

If instead the goal were "every Organization must have at least a `prov` coding, but can still
add its own custom codings alongside it" (the crosswalk pattern from
[`08-terminology-and-codeable-concepts.md`](../08-terminology-and-codeable-concepts.md)), that's
`pattern[x]`, not `fixed[x]` — `pattern[x]` only requires the *named* sub-elements to be present
and matching, while still allowing additional, unmentioned content:

```json
{
  "path": "Organization.type",
  "patternCodeableConcept": {
    "coding": [
      { "system": "http://terminology.hl7.org/CodeSystem/organization-type", "code": "prov" }
    ]
  }
}
```

Structurally identical JSON to the `fixed` example — the difference is entirely in which
keyword is used (`pattern...` vs `fixed...`) and therefore which enforcement semantics apply.
This is the single easiest mistake to make when authoring a profile: picking `fixed[x]` when
`pattern[x]` was actually meant locks out legitimate custom coding that should have been
allowed.

## Shaped for this project's planned storage

```json
{
  "elements": {
    "type": {
      "pattern": {
        "coding": [
          { "system": "http://terminology.hl7.org/CodeSystem/organization-type", "code": "prov" }
        ]
      }
    }
  }
}
```

(`docs/architecture/fhir-profiling-and-extensibility-strategy.md`'s §3 `structure.elements[field]`
shape doesn't yet explicitly show a `fixed`/`pattern` key in its worked example — only `min`/
`binding` — this is the natural extension of that same shape for this mechanism, not a
contradiction of it.)

## What's needed to actually enforce this (not built yet)

Checking `fixed[x]`/`pattern[x]` against an actual payload means a structural deep-equality
check (for `fixed`) or a structural subset-match check (for `pattern`) against the resolved
value at that path — neither exists in `app/fhir/validation/` today. `fhir.schema.json`'s base
layer has no concept of per-tenant fixed/pattern values at all (it only knows the base spec's
*type* constraints, not any profile's *value* constraints).
