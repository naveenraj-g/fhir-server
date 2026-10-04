# Use case: business rules that go beyond a single resource instance

Every other use case in this folder is "Tier 1" per
`docs/architecture/fhir-profiling-and-extensibility-strategy.md`'s §6 split — a rule
expressible as a FHIRPath statement about *one* resource instance, using only that instance's
own fields. This file is about **Tier 2**: rules that genuinely need something outside the
instance being validated — a database lookup, another resource's state, or a cross-resource
relationship.

## Why this is categorically different, not just "a bigger invariant"

[`06-constraints-and-invariants.md`](../06-constraints-and-invariants.md)'s FHIRPath mechanism
operates entirely within the JSON document being validated — `identifier.count()`,
`telecom.where(...)`, etc. all read fields that are already present in the payload. A rule like
*"this Organization's billing contact must correspond to a Practitioner who already has an
active `PractitionerRole` at this Organization"* cannot be expressed this way at all — it needs
to query a different resource type entirely, scoped by tenant, as of the current moment. No
amount of FHIRPath sophistication closes this gap, because FHIRPath evaluates against a single
instance's data, not your database.

## Worked example

**Rule:** "An Organization may only be marked `active: true` if it has at least one
`PractitionerRole` currently pointing at it." (A plausible real policy: don't let a facility go
live in search results before any practitioner is actually staffed there.)

This cannot be a `constraint.expression` on Organization's own `StructureDefinition` — the data
it needs (`PractitionerRole` rows) isn't part of the Organization instance at all. It has to be
evaluated as a distinct pipeline step, with its own database access, scoped to the acting
tenant:

```python
# illustrative only — not implemented anywhere in this codebase today
async def check_active_requires_staffing(org: OrganizationModel, session) -> list[str]:
    if org.active:
        has_role = await practitioner_role_repository.exists_for_organization(org.organization_id, org.tenant_id)
        if not has_role:
            return ["Organization cannot be marked active with no PractitionerRole assigned to it."]
    return []
```

## Why this needs a deliberately scoped, non-Turing-complete mechanism — not arbitrary code

`docs/architecture/fhir-profiling-and-extensibility-strategy.md` §6 is explicit and deliberate
about this, and it's worth restating here rather than softening it: **do not let organizations
upload arbitrary executable code for Tier 2 rules.** This is a multi-tenant system — if a
hospital's "custom business rule" runs as real Python/JS inside this process, one tenant's rule
becomes a sandbox-escape and cross-tenant-data-exfiltration vector the moment it's able to read
anything beyond its own scope or exhaust shared resources. The safer alternative that
document recommends is a **declarative, non-Turing-complete rule format** (something in the
shape of JSONLogic, or a small whitelisted expression grammar) that can only express
comparisons/boolean logic over the resource's own fields plus a narrow, explicitly-allow-listed
set of lookups (e.g. "does a PractitionerRole exist matching X, scoped to this org") — never
arbitrary queries, never arbitrary code execution.

## Where this fits in the overall validation pipeline

`docs/architecture/fhir-profiling-and-extensibility-strategy.md`'s §4 pipeline places this
deliberately *last* — step 5, after structure (step 2), terminology (step 3), and invariants
(step 4) have all already passed:

```
1. resolve_profile_chain(...)
2. validate_structure(...)        -- cardinality, fixed/pattern
3. validate_terminology(...)      -- coded fields against resolved bindings
4. validate_invariants(...)       -- FHIRPath, Tier 1, incl. org-1/org-2/org-3
5. validate_business_rules(...)   -- Tier 2, only for rules not expressible as (4)
6. Repository.create_full(...)    -- only reached if 1–5 all pass
```

This ordering matters: there's no reason to run an expensive cross-resource database lookup
(Tier 2) against a payload that's already structurally invalid or fails a cheap in-memory
invariant check (Tier 1) — fail fast on the cheaper checks first.

## What's needed to actually build this (not started, and flagged as needing a security decision before it is)

Per that architecture document's §9: the actual rule language for Tier 2 (JSONLogic, a custom
DSL, or something else) is explicitly listed as a decision this project has deliberately not
made yet, and §8's suggested order of work places Tier 2 business rules **last**, after base,
country, and organization structural/invariant layers are all working — specifically so the
security-sensitive rule-language choice isn't made under feature-delivery pressure.
