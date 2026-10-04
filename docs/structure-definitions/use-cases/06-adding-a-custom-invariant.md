# Use case: adding a custom invariant

**Scenario:** a hospital network wants to require that every Organization of type `prov`
(healthcare provider) have at least one phone-system telecom entry — a rule that spans two
different elements (`type` and `telecom`) and can't be expressed as a cardinality or
fixed/pattern constraint on either one alone.

## Why this has to be an invariant

Per [`06-constraints-and-invariants.md`](../06-constraints-and-invariants.md): cardinality and
fixed/pattern values each constrain *one element's own shape*. A rule that says "if element A
has value X, then element B must satisfy Y" is inherently cross-field, and FHIR's only
mechanism for cross-field rules is `ElementDefinition.constraint[]` with a FHIRPath
`expression` — exactly the mechanism behind `org-1` itself (which is already cross-field:
"`identifier` or `name`").

```json
{
  "path": "Organization",
  "constraint": [
    {
      "key": "org-clinic-1",
      "severity": "error",
      "human": "Clinics must record at least one phone contact.",
      "expression": "type.coding.where(code = 'prov').exists().not() or telecom.where(system = 'phone').exists()"
    }
  ]
}
```

Reading the FHIRPath: `type.coding.where(code = 'prov').exists()` is true if any `type` entry's
coding has `code = 'prov'`. The whole expression is `(not a provider) or (has a phone)` — which
is the standard logical-implication pattern ("if provider, then phone") expressed without an
`if`, since FHIRPath invariants are boolean expressions, not conditionals. This is slightly more
of the FHIRPath language than `org-1`/`org-2`/`org-3` individually need (adds `.not()` and
boolean `or`), but it's still well within what a general-purpose FHIRPath library handles — see
[`06-constraints-and-invariants.md`](../06-constraints-and-invariants.md)'s note on why
`docs/architecture/fhir-profiling-and-extensibility-strategy.md` recommends `fhirpathpy` over a
hand-rolled subset specifically because of examples like this one.

This is, in fact, the *exact* example already given in that architecture document's §3 worked
JSON (`org-clinic-1`, same rule, shown there as "Clinics must record at least one phone
contact.") — this file exists to show the *derivation* from the underlying spec mechanism that
example assumes, not to introduce a new idea.

## Where "Tier 1" vs "Tier 2" matters here

This rule is squarely **Tier 1** per that architecture document's §6 — fully expressible as a
FHIRPath statement about a single resource instance, no external lookups or cross-resource
queries needed. A rule like *"this Organization's billing contact must already exist as an
active Practitioner at this org"* would instead be **Tier 2** (needs a database lookup, not just
the instance's own fields) and would need the separate, deliberately-scoped mechanism that
document's §6 discusses (and explicitly recommends against allowing arbitrary tenant-uploaded
code for, given the multi-tenant security exposure).

## Shaped for this project's planned storage

```json
{
  "invariants": [
    {
      "key": "org-clinic-1",
      "severity": "error",
      "expression": "type.coding.where(code = 'prov').exists().not() or telecom.where(system = 'phone').exists()",
      "description": "Clinics must record at least one phone contact."
    }
  ]
}
```

## What's needed to actually enforce this (not built yet)

Exactly the same gap as `org-1`/`org-2`/`org-3` themselves: no FHIRPath evaluator is wired into
this codebase yet, and no `fhir_profile`-style invariant storage exists. Building the base-layer
invariant check (`org-1`/`org-2`/`org-3`, which this project already knows it needs) and
building org-layer custom invariants like this one are the *same* piece of work — a FHIRPath
evaluator plus a per-resource list of `{key, severity, human, expression}` rows, run against the
same FHIR-shaped payload `app/fhir/validation/base_r4.py` already produces via
`payload_to_fhir_organization()`/`merge_patch_fragment()`. There's no reason to build these as
two separate systems.
