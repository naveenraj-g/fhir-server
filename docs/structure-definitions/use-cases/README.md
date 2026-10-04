# Use cases

Each file here is one concrete, realistic scenario for this project, written against
Organization (the resource already rebuilt to strict R4 shape this session) so every example
can point at real files instead of hypotheticals. Read [`../README.md`](../README.md)'s Part 1
first — these use cases assume you already know what `min`/`max`, `fixed[x]`/`pattern[x]`,
`constraint[]`, `coding[]`, and `binding` mean.

None of these are built yet — no country/organization profile layer exists in code today (see
[`../12-three-layer-validation-architecture.md`](../12-three-layer-validation-architecture.md)
for exactly what does exist). Each file shows what the *profile data* for the scenario would
look like, using the shape `docs/architecture/fhir-profiling-and-extensibility-strategy.md`'s
§3 already designed (`fhir_profile.structure`), and which `ElementDefinition` fields from
Part 1 it relies on.

**Structural/value mechanisms:**

1. [Tightening cardinality](01-tightening-cardinality.md) — making an optional field required.
2. [Fixing and patterning values](02-fixing-and-patterning-values.md) — locking a field to one
   value, or requiring a sub-value while still allowing more alongside it.
3. [Requiring a custom identifier system](03-requiring-a-custom-identifier-system.md) — an
   invariant-based approach to "must have at least one identifier from system X."
7. [Slicing a repeating element](07-slicing-a-repeating-element.md) — the dedicated, more
   precise version of #3, giving each identifier kind its own independent cardinality.
11. [Constraining a Reference's target profile](11-constraining-a-reference-target-profile.md) —
    `Organization.partOf` must point at a profile-conformant parent.
14. [Prohibiting an inherited element](14-prohibiting-an-inherited-element.md) — `max: 0`,
    forbidding something the base spec allows.
12. [mustSupport and defaultValue\[x\]](12-must-support-and-default-values.md) — conformance
    expectations and absent-value interpretation, as distinct from hard validity rules.

**Terminology and CodeableConcepts:**

4. [Custom codes with a standard crosswalk](04-custom-codes-with-standard-crosswalk.md) — the
   dual-coding pattern, already implemented.
9. [Real-world terminology systems](09-real-world-terminology-systems.md) — SNOMED CT, LOINC,
   RxNorm, HL7's own CodeSystems, and a tenant's own system, named concretely.
10. [Tightening a terminology binding's strength](10-tightening-a-terminology-binding.md) —
    narrowing `extensible` to `required`, and what it costs the crosswalk pattern.
8. [A custom display label for a fixed code](08-custom-display-for-a-fixed-code.md) — the
   `code`-vs-`CodeableConcept` distinction, and `CodeSystem.designation` as the correct
   mechanism for relabeling without changing the underlying enum value.

**Extensions and business rules:**

5. [Adding a required extension](05-adding-a-required-extension.md) — defining a tenant-specific
   extension and making a profile require it.
13. [A modifier extension](13-modifier-extensions.md) — when an extension changes the
    resource's meaning and unrecognized content must not be silently ignored.
6. [Adding a custom invariant](06-adding-a-custom-invariant.md) — a cross-field FHIRPath rule
   (Tier 1) beyond `org-1`/`org-2`/`org-3`.
15. [Cross-resource business rules](15-cross-resource-business-rules.md) — Tier 2 rules that
    need a database lookup, and why they must not be arbitrary tenant-uploaded code.

**Putting it all together:**

16. [One payload, walked through all three layers](16-end-to-end-three-layer-trace.md) — a
    concrete request traced step by step through base R4, a country rule, and an org rule, with
    a worked pass/fail at each step.
