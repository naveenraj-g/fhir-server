# Use case: slicing a repeating element

A dedicated worked example of [`07-slicing.md`](../07-slicing.md)'s mechanism, scoped to
Organization — filling the gap from the previous round where slicing was only mentioned
inline inside use-case 03, not given its own full scenario.

**Scenario:** a country profile requires every Organization to carry *two* specific kinds of
identifier, each with its own rule: exactly one tax-registration identifier, and zero-or-one
national-registry identifier — while still allowing the org to add any number of other,
unrelated identifiers.

## The slicing definition

```json
{
  "path": "Organization.identifier",
  "slicing": {
    "discriminator": [{ "type": "value", "path": "system" }],
    "rules": "open",
    "description": "Sliced by identifier.system to separate tax and registry identifiers from everything else."
  }
},
{
  "path": "Organization.identifier",
  "sliceName": "tax-id",
  "min": 1,
  "max": "1",
  "patternIdentifier": { "system": "https://example.gov/tax-id" }
},
{
  "path": "Organization.identifier",
  "sliceName": "registry-id",
  "min": 0,
  "max": "1",
  "patternIdentifier": { "system": "https://example.gov/registry-id" }
}
```

Three `ElementDefinition` entries at the *same* `path`, distinguished by `sliceName`. The first
carries the `slicing` block itself (discriminator + rules), the other two are the actual slices.
`rules: "open"` is what permits an org to still add e.g. a DUNS number or an internal reference
code alongside the two required slices — if this were `closed` instead, *any* identifier not
matching one of the two declared slices would be rejected outright, which is rarely what you
want for a field like `identifier` that naturally accumulates unrelated values over time.

## Why `discriminator.type: "value"` here, not `"pattern"`

Per [`07-slicing.md`](../07-slicing.md)'s discriminator table: `value` means "slices differ by
having different literal values at the nominated path" — here, literally comparing
`identifier.system` against two fixed URIs. `pattern` discrimination would instead mean "slices
differ by matching each slice's own declared pattern" — functionally similar for this simple
case, but `value` is the more direct, more common choice when the distinguishing field really is
just one scalar value being compared, which is exactly this situation.

## What this adds beyond a plain invariant (contrast with use-case 03)

[`03-requiring-a-custom-identifier-system.md`](03-requiring-a-custom-identifier-system.md)'s
simpler, invariant-only version can say "at least one registry identifier exists" but can't cap
it at exactly one, can't independently track a *second*, differently-ruled identifier kind in
the same list, and can't give tooling (a profile-authoring UI, a documentation generator) a
named concept ("the tax-id slice") to display and validate against directly. Slicing is the
right tool specifically when more than one named sub-group needs independent rules within the
same repeating element — a single invariant doesn't scale cleanly past one informal condition.

## What's needed to actually enforce this (not built yet)

Beyond the invariant evaluator already needed for `org-1`/`org-2`/`org-3`
([`06-constraints-and-invariants.md`](../06-constraints-and-invariants.md)), slicing needs its
own bucketing logic: for each entry in the actual `identifier[]` array, evaluate the
discriminator to decide which declared slice (if any) it belongs to, then check each slice's own
`min`/`max` independently, then check `rules` to decide whether leftover unmatched entries are
permitted. None of this exists in `app/fhir/validation/` today — flagged in
[`12-three-layer-validation-architecture.md`](../12-three-layer-validation-architecture.md) as
one of the subsystems not yet started.
