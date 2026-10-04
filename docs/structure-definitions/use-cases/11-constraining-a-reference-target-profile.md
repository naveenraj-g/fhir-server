# Use case: constraining what a Reference is allowed to point at

**Scenario:** a country or organization profile requires that `Organization.partOf` doesn't
just point at *any* Organization, but specifically at one that itself conforms to that same
country's Organization profile — preventing a compliant child organization from being attached
to a parent that was created without the country's required fields.

## The mechanism: `type.targetProfile`

From [`04-data-types-and-choice-elements.md`](../04-data-types-and-choice-elements.md)'s
`type[]` table: `type.targetProfile` is specifically for `Reference`/`canonical`-typed elements,
and constrains *what the referenced resource must conform to*, independent of whatever
constrains the `Reference` wrapper itself.

```json
{
  "path": "Organization.partOf",
  "type": [
    {
      "code": "Reference",
      "targetProfile": ["https://example.gov/fhir/StructureDefinition/IN-Organization"]
    }
  ]
}
```

Reading this: `Organization.partOf` remains a `Reference` (the wrapper type is unchanged from
base R4), but the thing it points at must conform to the country's own `IN-Organization`
profile — not merely "any Organization," and not even merely "any Organization matching base
R4," but specifically a fully country-profile-conformant one.

## Why this matters specifically for Organization

Organization is one of the few resources in this project with a **self-reference**
(`partOf: Reference(Organization)`) — `docs/architecture/fhir-profiling-and-extensibility-strategy.md`'s
broader design doesn't call this out, but it's a real structural property worth being aware of:
a self-referencing hierarchy means profile *conformance* can propagate up a tree. If every
Organization's `partOf` must point at a profile-conformant parent, and that parent's own
`partOf` must point at a profile-conformant grandparent, conformance becomes a property of the
whole chain, not just one row — which has real implications for how validation would need to
work (checking a target's conformance means loading and validating the target too, not just the
reference string pointing at it), distinct from every other `targetProfile` use case in this
server where the target is a different resource type entirely.

## Contrast with this project's current reference validation

Today, `app/core/reference_resolver.py`'s `ensure_resource_exists()` only checks that
`partof_id` resolves to a real row of the right *type*
(`RESOURCE_REGISTRY`-driven — confirmed it exists, confirmed it's an Organization) — it has no
concept of checking that the target *conforms to a specific profile*. `targetProfile` validation
is a strictly higher bar than existence validation, and would need the full profile-resolution
machinery from [`12-three-layer-validation-architecture.md`](../12-three-layer-validation-architecture.md)
applied recursively to the referenced resource, not just the one being written.

## What's needed to actually enforce this (not built yet)

Beyond everything else flagged as not-yet-built in this folder: resolving a reference's target,
running the *target's own* profile-chain validation against it (recursively, since the target
might itself have a `partOf` needing the same check), and treating a non-conformant target as a
validation failure on the *referencing* resource, not just a 404-if-missing check. This is a
meaningfully larger scope than every other use case in this folder, flagged here honestly rather
than glossed over.
