# Use case: tightening a terminology binding's strength

Distinct from [`04-custom-codes-with-standard-crosswalk.md`](04-custom-codes-with-standard-crosswalk.md)
(which uses the base spec's existing `extensible` binding as-is) — this use case is about a
profile *changing the binding itself*, which is a narrowing operation in its own right, governed
by the same "only narrow, never loosen" rule as cardinality.

**Scenario:** base R4 binds `Organization.type` as `extensible` against
`http://terminology.hl7.org/CodeSystem/organization-type` — any tenant may add custom codes
alongside a standard one, or (per the `extensible` definition) use their own code entirely if
nothing standard fits. A government-regulated country profile decides this is too loose for
their jurisdiction: every Organization operating there must use *only* a code from the
country's own published registry — no custom codes, no exceptions.

## The binding override

```json
{
  "path": "Organization.type",
  "binding": {
    "strength": "required",
    "valueSet": "https://example.gov/fhir/ValueSet/organization-type-registry"
  }
}
```

This is a complete replacement of the element's `binding`, not a merge — the country profile
is substituting its own closed value set in place of the base spec's open one.

## Why this direction is legal and the reverse is not

Per [`08-terminology-and-codeable-concepts.md`](../08-terminology-and-codeable-concepts.md)'s
strength table, read as an ordering from loosest to strictest: `example` → `preferred` →
`extensible` → `required`. [`05-cardinality-and-multiplicity.md`](../05-cardinality-and-multiplicity.md)'s
narrowing rule applies to binding strength exactly as it applies to `min`/`max`: a child profile
may only move *rightward* on that scale (loosen-to-strict), never leftward. Base R4's
`extensible` → country `required` is a legal narrowing. The reverse — a profile trying to loosen
a `required` binding back down to `extensible` — would mean the profile is claiming to accept
values the base spec forbids, which breaks "conforms to the profile implies conforms to the
base" the same way an illegally widened cardinality would
([`05`](../05-cardinality-and-multiplicity.md)'s whole point).

## The consequence for this use case's own crosswalk ability

This is worth being explicit about, since it directly contradicts
[`04`](04-custom-codes-with-standard-crosswalk.md)'s pattern for any Organization under *this*
country's profile specifically: once `Organization.type`'s binding is tightened to `required`
against the country's own closed registry, **the dual-coding crosswalk pattern from use-case 04
is no longer legal for this field, for Organizations under this profile.** A `required` binding
means every `Coding` in `coding[]` must come from the one named value set — there's no more room
for an additional custom coding alongside it, because `required` doesn't carry `extensible`'s
"if the value set doesn't cover the concept, alternate codings may be included instead" escape
hatch at all. This is a genuine, spec-correct tension a profile author needs to be deliberate
about: tightening a binding for compliance reasons trades away the flexibility the crosswalk
pattern depends on, for that specific field, under that specific profile.

## What's needed to actually enforce this (not built yet)

The terminology-validation pipeline step
(`docs/architecture/fhir-profiling-and-extensibility-strategy.md` §4, step 3) would need to
resolve the *effective* binding for a field — not just the base spec's own binding, but whatever
the most specific layer in the chain declares — before checking a submitted code against it.
Today there's no profile-chain resolution at all, so every field is validated (to the limited
extent it's validated today) only against the base spec's own binding.
