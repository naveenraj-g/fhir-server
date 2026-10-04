# Use case: prohibiting an element the base spec allows

**Scenario:** a highly specialized tenant profile — say, for a type of Organization that
should never have sub-organizations under it at all — wants to forbid `Organization.partOf`
from ever being populated, even though base R4 allows it (`0..1`).

## The mechanism: `max: "0"`

Per [`05-cardinality-and-multiplicity.md`](../05-cardinality-and-multiplicity.md): setting an
inherited element's `max` to `0` is a legal narrowing (`0` is always `≤` whatever the base
allowed), and it means exactly what it looks like — this element may not appear at all under
this profile.

```json
{
  "path": "Organization.partOf",
  "max": "0"
}
```

`min` doesn't need to change (it's already `0` in the base spec, and `0..0` is the valid
resulting range — "appears zero times, and zero is also the maximum").

## Why this is a real, named technique and not a misuse of cardinality

This sometimes gets questioned as "weird" because it looks unusual to see cardinality used for
outright prohibition rather than just narrowing a range — but it follows directly and legally
from the narrowing rule with no special-casing needed: forbidding an element is simply the most
extreme possible narrowing of its `max`. HL7's own guidance explicitly documents "zeroing out"
an element as the standard way to express "not applicable under this profile," rather than
introducing a separate `forbidden: true` flag — the general cardinality mechanism already covers
this case without needing a new one.

## Contrast with a `0..0` element that's simply never been given a value

This is worth being precise about: a `max: "0"` constraint is a **profile-authored prohibition**,
checked by a validator against incoming/outgoing data — an instance that includes `partOf`
anyway is invalid under this profile, full stop. That's different from an ordinary `0..1` field
that simply happens to be empty on a given instance, which is perfectly valid under the base
spec with no profile involvement at all. Don't conflate "nobody happened to set this field" with
"this profile forbids this field" — only the latter is what `max: "0"` expresses.

## Shaped for this project's planned storage

```json
{
  "elements": {
    "partof": { "max": 0 }
  }
}
```

Fits directly into `docs/architecture/fhir-profiling-and-extensibility-strategy.md`'s §3
`structure.elements[field]` shape alongside the `min`-narrowing example already given there —
the same key (`max`, here set to its most restrictive legal value) rather than a separate
mechanism.

## What's needed to actually enforce this (not built yet)

Checking a resolved `max: 0` constraint against a payload is, if anything, *simpler* than most
other mechanisms in this folder — it's a presence check ("is this field populated at all"),
which doesn't need FHIRPath, slicing logic, or terminology resolution. It still depends on the
same not-yet-built prerequisite everything else in this folder does: a resolved, per-tenant
effective rule set to check the payload against, which doesn't exist yet
(`app/fhir/validation/base_r4.py` only ever checks the unprofiled base spec).
