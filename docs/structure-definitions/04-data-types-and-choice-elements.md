# Data types, choice elements, and fixed/pattern/default values

This is the field group that answers "what data type is this, and what values is it allowed
to hold" — the part of `ElementDefinition` most directly relevant to how this project's own
Pydantic schemas and SQLAlchemy columns were designed (see `CLAUDE.md`'s "FHIR DB Model
Design" section — the cardinality → storage mapping rules there are a direct consequence of
the fields documented here).

## `type` — what kind of value this element holds

`ElementDefinition.type` is `0..*` (an array), not `0..1` — because a single element can
legally hold *more than one possible data type* (see "choice elements" below). Each entry is:

| Field | Card. | Type | Why it exists |
|---|---|---|---|
| `type.code` | `1..1` | `uri` | The actual data type or resource type (e.g. `"string"`, `"CodeableConcept"`, `"Reference"`, `"Organization"`). |
| `type.profile` | `0..*` | `canonical` | If populated, the value must conform to one of these profiles (not just the base type) — "one must apply." This is how a profile can say "this element isn't just any `Identifier`, it must be an `Identifier` shaped like *our* profile of Identifier." |
| `type.targetProfile` | `0..*` | `canonical` | Only meaningful when `type.code` is `Reference` or `canonical` — constrains *what the reference points at*, not the Reference wrapper itself (e.g. `Reference` where `targetProfile` says the target must conform to a specific Organization profile). |
| `type.aggregation` | `0..*` | `code` | Only meaningful for `Reference` types: `contained \| referenced \| bundled` — how the target is expected to be delivered alongside the referencing resource. Not used by this project (we don't use FHIR `Bundle`-based delivery for writes). |
| `type.versioning` | `0..1` | `code` | Only meaningful for `Reference`/`canonical`: `either \| independent \| specific` — whether the reference is expected to pin a specific version of the target. Not used by this project. |

**Why `type` is an array at all — choice elements.** Some FHIR elements can legitimately hold
one of *several* different data types, and the instance's JSON key itself encodes which one was
chosen — these are the `value[x]`-style fields (`Extension.value[x]`,
`ElementDefinition.fixed[x]`, `Observation.value[x]`, etc.). In the `ElementDefinition` for such
a field, `type[]` lists every type that's legal, and the actual JSON serialization replaces the
`[x]` with the concrete type name: `valueString`, `valueBoolean`, `valueCodeableConcept`, and so
on — exactly one of these keys appears in any given instance, never more than one, never the
literal `value[x]` itself. `Extension.value[x]` is the most relevant choice element to this
project — see [`09-extensions.md`](09-extensions.md).

## `fixed[x]` / `pattern[x]` / `defaultValue[x]` — the three ways to constrain a concrete value

All three are choice elements themselves (hence the `[x]`, same mechanism as above) — a profile
picks the concrete type matching the element it's constraining
(`fixedCodeableConcept`, `patternUri`, `defaultValueBoolean`, etc.). **They mean three
different things, and conflating them is a common mistake worth being precise about:**

| Field | Meaning | Example |
|---|---|---|
| `defaultValue[x]` | The value an instance should be treated as having **if the field is absent entirely**. Does not make the field required, and does not forbid other values — it only fills a gap when nothing was sent. | A profile could default `Organization.active` to `true` for instances that don't set it. |
| `fixed[x]` | The value **must equal this exactly** — for a complex type, every sub-element must match exactly what's specified, and no additional sub-elements beyond what's listed may be populated. The strictest of the three. | A profile fixing `Organization.type.coding.system` to always be one specific URI — every Organization under that profile must use that exact system, nothing else. |
| `pattern[x]` | The specified sub-elements **must be present and match**, but additional sub-elements *not* mentioned in the pattern are still allowed. For a complex type this is a "must contain at least this" check, not "must equal exactly this." | A profile could `patternCodeableConcept` requiring `coding.system = "http://hl7.org/fhir/sid/us-npi"` to be present somewhere in `Organization.identifier.type.coding[]`, while still allowing the org to add its own additional codings alongside it — this is *exactly* the dual-coding/crosswalk pattern covered in [`08-terminology-and-codeable-concepts.md`](08-terminology-and-codeable-concepts.md), and it's why `pattern[x]`, not `fixed[x]`, is the right mechanism for "require a standard code, but still allow custom codes alongside it." |

**`example`** (`0..*`, type `Element` with `label` + `value[x]`) is a fourth, unrelated field —
it supplies sample values purely for documentation/tooling (e.g. rendered into a generated IG
page), and is never checked by a validator at all.

## `minValue[x]` / `maxValue[x]` / `maxLength`

| Field | Card. | Applies to | Why it exists |
|---|---|---|---|
| `minValue[x]` / `maxValue[x]` | `0..1` each | ordered types only: `date`, `dateTime`, `instant`, `time`, `decimal`, `integer`, `positiveInt`, `unsignedInt`, `Quantity` | A bound on the *value*, not the cardinality — e.g. a profile could require `Encounter.period.start` to be no earlier than a given date. Not used anywhere in this project's current resources. |
| `maxLength` | `0..1` | string-like types | Caps string length — e.g. a profile could cap `Organization.name` at 100 characters even though the base type has no such limit. |

## How this maps to this project's own schema-design rules

`CLAUDE.md`'s "FHIR DB Model Design" skill reference already encodes several practical
consequences of the fields above, worth connecting explicitly:

- **"CodeableConcept / Reference / choice-type flattening"** in that skill is this project's
  concrete storage answer to `type[]` being an array (choice elements) and to `CodeableConcept`
  being a complex type with its own `coding[]` — e.g. `OrganizationModel.partof_type`/`partof_id`
  is the flattened storage for a `Reference`'s polymorphism, and the new `OrganizationTypeCoding`
  child table (built this session) is the storage answer to `CodeableConcept.coding` being
  `0..*`, not `0..1`.
- **Cardinality → storage mapping** (`0..1` flat column vs. `0..*` child table) is a direct
  consequence of `ElementDefinition.max` — see [`05-cardinality-and-multiplicity.md`](05-cardinality-and-multiplicity.md).
- This project doesn't yet implement `fixed[x]`/`pattern[x]` enforcement anywhere (no profile
  layer exists yet) — when the country/org profile layer is built per
  `docs/architecture/fhir-profiling-and-extensibility-strategy.md`, this is the field pair that
  implements "a clinic profile fixes `Organization.type` to always be `prov`" from that
  document's §2 table.
