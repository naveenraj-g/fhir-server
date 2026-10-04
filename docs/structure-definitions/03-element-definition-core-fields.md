# ElementDefinition — core fields

`ElementDefinition` is a FHIR complex type (`kind: complex-type` on its own
`StructureDefinition`) — it never appears as a standalone resource, only as entries in
`StructureDefinition.snapshot.element[]` and `StructureDefinition.differential.element[]`. This
is the structure that does essentially all of the actual work described anywhere in this
folder: cardinality, types, fixed/pattern values, constraints, bindings, slicing, and the
element-level flags are all fields *on* `ElementDefinition`, not on `StructureDefinition`
itself.

This file covers the navigational/descriptive fields. The fields with enough depth to need
their own treatment are split out: [`04-data-types-and-choice-elements.md`](04-data-types-and-choice-elements.md)
(`type`, `fixed[x]`/`pattern[x]`/`defaultValue[x]`/`example`), [`05-cardinality-and-multiplicity.md`](05-cardinality-and-multiplicity.md)
(`min`/`max`/`base`), [`06-constraints-and-invariants.md`](06-constraints-and-invariants.md)
(`constraint`), [`07-slicing.md`](07-slicing.md) (`slicing`), [`08-terminology-and-codeable-concepts.md`](08-terminology-and-codeable-concepts.md)
(`binding`), and [`10-element-flags.md`](10-element-flags.md) (`mustSupport`/`isModifier`/`isSummary`).

## Identity and position

| Field | Card. | Type | Why it exists |
|---|---|---|---|
| `path` | `1..1` | `string` | The dotted path identifying which element this entry describes, e.g. `"Organization.address"` or `"Organization.contact.telecom"`. This is the primary key within an element list — a validator walks an instance and, for each value it finds, looks up the matching `ElementDefinition` by `path` (and `sliceName`, if sliced). |
| `representation` | `0..*` | `code` | How this element is represented in non-JSON serializations (`xmlAttr \| xmlText \| typeAttr \| cdaText \| xhtml`). Irrelevant to this project — we only ever produce/consume JSON. |
| `sliceName` | `0..1` | `string` | If this entry describes one named slice of a sliced repeating element, its name (e.g. `"mrn"` for one slice of `Patient.identifier`). See [`07-slicing.md`](07-slicing.md). |
| `sliceIsConstraining` | `0..1` | `boolean` | Whether this slice entry is itself narrowing a slice already defined by an ancestor profile (as opposed to defining a brand-new slice). Only matters once profiles-of-profiles with slicing are in play — not relevant to this project's current scope. |
| `label` | `0..1` | `string` | A display label/prompt for this element, for form-generation tooling. Not used by validation. |
| `code` | `0..*` | `Coding` | Codes from external terminologies corresponding to this element itself (not its *value* — the element's identity), for cross-mapping to other standards (e.g. HL7 v2 segment/field codes). Informational. |

## Documentation

| Field | Card. | Type | Why it exists |
|---|---|---|---|
| `short` | `0..1` | `string` | A concise, one-line definition — what you'd show in a compact table (this is, in fact, exactly what every table in this documentation folder pulled directly from the spec data). |
| `definition` | `0..1` | `markdown` | The full, formal, narrative definition — what you'd show a human author trying to understand *why* a field is shaped the way it is. |
| `comment` | `0..1` | `markdown` | Additional guidance about using the element correctly — edge cases, common mistakes, clarifications that don't belong in the formal definition. |
| `requirements` | `0..1` | `markdown` | Why this element exists at all — the business/clinical justification. |
| `alias` | `0..*` | `string` | Other names this concept is known by elsewhere, to help someone searching for it under a different term. |

None of the five fields above affect validation in any way — they're pure documentation,
carried through to generated IGs/webpages. A validator can safely ignore all of them.

## Structural navigation

| Field | Card. | Type | Why it exists |
|---|---|---|---|
| `base` | `0..1` | `Element` (`path`, `min`, `max`) | Records what this element's cardinality was on the **original** base definition, before any profile (including this one) narrowed it. Lets tooling show "this profile narrowed `0..1` down to `1..1`" without having to walk the whole `baseDefinition` chain to find out. Covered alongside `min`/`max` in [`05-cardinality-and-multiplicity.md`](05-cardinality-and-multiplicity.md). |
| `contentReference` | `0..1` | `uri` | Lets one element's structure be defined by *reusing* another element's definition wholesale, instead of repeating it — a same-document, same-shape reference (e.g. `Questionnaire.item` can contain nested `Questionnaire.item`, and rather than redefining the whole item structure recursively, the nested occurrence just references `#Questionnaire.item`). Not used anywhere in this project's resources today. |
| `orderMeaning` | `0..1` | `string` | For a repeating (`0..*`/`1..*`) element, explains whether/why the *order* of the array is semantically meaningful (as opposed to just "a set of these values in no particular order"). Informational, not enforced structurally. |
| `mapping` | `0..*` | Element (`identity`, `language`, `map`, `comment`) | Maps this specific element to an entry in the parent `StructureDefinition.mapping[]` list by `identity` — the per-element half of the cross-mapping declared at the resource level. |

## Worked example: `Organization.address`'s own core fields

From the real file:

```
path:        Organization.address
short:       An address for the organization
definition:  An address for the organization.
min:         0
max:         *
base.path:   Organization.address
base.min:    0
base.max:    *
```

This single `ElementDefinition` entry is also the one carrying the `org-2` constraint
("can never be of use 'home'") — see [`06-constraints-and-invariants.md`](06-constraints-and-invariants.md)
for the full `constraint[]` structure, and [`05-cardinality-and-multiplicity.md`](05-cardinality-and-multiplicity.md)
for what the `0..*` cardinality shown here actually governs.
