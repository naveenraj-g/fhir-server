# Validation and Field Bindings

**What this file is:** the part of the subsystem that actually *enforces*
or *translates* codes, as opposed to just storing them. If you haven't
read [00-what-is-terminology.md](00-what-is-terminology.md) yet, read it
first for what a "binding" and a "concept map" are conceptually — this
file is about exactly how strict this codebase's enforcement really is
(narrower than the FHIR spec's own four-level model, explained below) and
exactly what gets checked when.

This is the part of the subsystem that answers two different questions:
"is this coded value legal for this field?" (`validate()`) and "what's the
equivalent code in another system?" (`translate()`). Both live in
`app/services/terminology/validation.py`, backed by
`app/repository/terminology/validation.py` (see
[02-repository-and-service-layers.md](02-repository-and-service-layers.md)
for the exact repository method signatures).

## The binding-strength trap

FHIR defines four binding strengths — `required`, `extensible`,
`preferred`, `example` — and the spec's intent is that each carries
different enforcement semantics (`required` must come from the ValueSet,
`extensible` should unless no suitable code exists, `preferred`/`example`
are purely advisory). **This codebase does not implement that four-way
distinction at validation time.** There are two different
`binding_strength` columns in play, and only one of them is ever read by
`validate()`:

- `TerminologyValueSet.binding_strength` — set by loader heuristics (the
  FHIR R4 loader sets it from `ValueSet.immutable`, see
  [05](05-seeding-and-external-loaders.md)). **`validate()` never reads
  this column.** It's effectively descriptive metadata about the ValueSet
  itself today, not an enforcement input.
- `TerminologyFieldBinding.binding_strength` — set by whichever seed script
  wrote the binding (hand-curated or HL7-StructureDefinition-derived, see
  [05](05-seeding-and-external-loaders.md)). **This is the one
  `validate()` actually checks.**

And even that check is binary, not four-way: `validate()`'s strength check
only treats the literal string `"required"` as "this must be satisfied or
the validation fails." Every other strength value (`extensible`,
`preferred`, `example`, or anything else) is treated as non-blocking — the
concept lookup still happens and the result still reports whether the code
was found/in-ValueSet, but a miss doesn't fail validation. If you're
reasoning about what `validate()` will actually reject, the only lever that
matters is: does `TerminologyFieldBinding.binding_strength` for this
`(resource_type, field_name)` equal `"required"`?

## `validate(req)` control flow

1. `get_field_binding(resource_type, field_name)` — if no binding exists at
   all for this field, short-circuit and return a "no value set bound" /
   not-applicable result. A field with no `TerminologyFieldBinding` row
   simply has nothing to validate against — this is not an error state.
2. `lookup_concept_in_value_set(value_set_id, system, code)` — resolves the
   `(system, code)` pair against the binding's ValueSet, returning the
   `CodeSystem`, the `Concept` (if the code exists at all, anywhere), and a
   separate `in_value_set: bool` (is it actually a member of *this*
   ValueSet, not just a valid code somewhere).
3. Strength check: if `binding.binding_strength == "required"` and the code
   isn't in the ValueSet (or doesn't exist at all), the result reports
   failure. Any other strength value never fails the result on this basis.
4. Wrapped into `ValidateResponse` and returned.

## `translate(req)` control flow

1. `lookup_concept(system, code)` — resolve the source `(system, code)` to
   its internal concept id. If it doesn't resolve, there's nothing to
   translate from.
2. `get_translations(source_concept_id, target_system)` — queries
   `TerminologyConceptMap` for every mapping whose source is this concept
   and whose target concept belongs to `target_system`.
3. Each match becomes a `TranslationResult`; all of them are collected into
   `TranslateResponse`. Note this is a different table
   (`TerminologyConceptMap`) from everything `validate()` touches
   (`TerminologyValueSet`/`TerminologyFieldBinding`/`TerminologyValueSetConcept`)
   — translation and field-binding validation are two unrelated data paths
   that happen to share the same `Concept`/`CodeSystem` foundation
   underneath, per [01-data-model.md](01-data-model.md)'s framing of
   ConceptMap as "a separate, parallel translation layer."

## Practical implication for anyone adding a new resource's bindings

If you want a field's coded value to actually be enforced at
`POST`/`PATCH` time via this mechanism (note: nothing in the router/service
layer for the ~34 non-terminology resources currently *calls*
`validate()` automatically — that wiring, if it exists, would live in each
resource's own service layer, not here), the binding you create (via either
seed script, or directly) needs `binding_strength = "required"` on the
`TerminologyFieldBinding` row specifically — setting `"required"` on the
`TerminologyValueSet` row instead does nothing for this purpose.
