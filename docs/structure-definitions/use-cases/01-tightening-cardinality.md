# Use case: tightening cardinality

**Scenario:** base R4 allows `Organization.name` to be absent (`0..1`, as long as `org-1` is
satisfied by having an `identifier` instead). A hospital-network tenant decides every
Organization in *their* system must have a name — no identifier-only organizations allowed.

## The spec mechanism

[`05-cardinality-and-multiplicity.md`](../05-cardinality-and-multiplicity.md)'s narrowing rule:
a profile may tighten `min` upward (never loosen it). The profile's differential needs exactly
one entry:

```json
{
  "path": "Organization.name",
  "min": 1
}
```

No `max` change needed (`max` stays `1`, inherited unchanged). This is the smallest possible
profile — a single-field cardinality override, nothing else.

## Shaped for this project's planned storage (per the architecture document's §3)

```json
{
  "elements": {
    "name": { "min": 1 }
  }
}
```

## What changes for an instance

- An Organization with `name` omitted but `identifier` populated — **currently valid** under
  base R4 (satisfies `org-1`) — would become **invalid** under this org's profile, because the
  org layer's `min: 1` on `name` applies *in addition to* `org-1`, not instead of it. Both the
  base invariant and the org-layer cardinality rule must pass.
- This is also a good illustration of why layers *compose* rather than *replace* each other:
  `org-1` ("name or identifier") still exists and is still evaluated; the org layer just adds a
  stricter requirement on top of it that happens to make one of `org-1`'s two satisfying
  conditions mandatory.

## What's needed to actually enforce this (not built yet)

A `validate_structure` step (per the architecture document's §4 pipeline) that, for each field
the resolved profile chain narrows, checks the payload against the *effective* `min`/`max` —
not just against the base Pydantic schema's own (currently unprofiled) optionality. Today,
`OrganizationCreateSchema.name` is simply `str | None` with no per-tenant variability — there's
no mechanism yet for a profile to make it conditionally required only for specific tenants.
