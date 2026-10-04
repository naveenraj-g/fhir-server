# Terminology bindings and CodeableConcepts

This file directly answers the question that kicked off this documentation effort: **can we
use our own `CodeableConcept`/`Coding` systems and codes, and if so, how do we keep them lined
up with the "real" ones?** Short answer: yes, and the mechanism for doing it correctly is
already built into this project's Organization work this session — this file explains why that
design is spec-correct, not just convenient.

## The shape: `Coding` and `CodeableConcept`

Two FHIR data types, used throughout the spec and already used extensively in this project's
own schemas (`app/schemas/common/fhir.py`):

- **`Coding`** — one single coded value: `system` (a URI identifying *which* code system —
  e.g. `http://terminology.hl7.org/CodeSystem/organization-type`, or your own org's URI),
  `version`, `code` (the actual symbol, e.g. `"prov"`), `display`, `userSelected`.
- **`CodeableConcept`** — a concept that can be expressed as **one or more** `Coding`s
  (`coding: 0..*`), plus a plain-text fallback (`text: 0..1`). The `0..*` is the important
  part: a single concept is allowed to carry more than one coded representation at once.

This `0..*` cardinality on `coding[]` is exactly why this session's Organization rework turned
`identifier.type`, `type`, and `contact.purpose` from a single flattened coding into real child
tables (`OrganizationIdentifierTypeCoding`, `OrganizationTypeCoding`,
`OrganizationContactPurposeCoding`) — see [`05-cardinality-and-multiplicity.md`](05-cardinality-and-multiplicity.md)'s
cardinality → storage table. A `CodeableConcept` that can only ever hold one `Coding` wasn't
wrong by accident — it was under-modeling what the type actually allows.

## `ElementDefinition.binding` — how a coded element gets constrained

| Field | Card. | Type | Why it exists |
|---|---|---|---|
| `binding.strength` | `1..1` | `code` | How strictly codes are constrained to a value set — the four values below. |
| `binding.description` | `0..1` | `string` | Human explanation of the value set's intent. |
| `binding.valueSet` | `0..1` | `canonical` | The `ValueSet` this element's codes should (or must) come from. |

### `binding.strength` — the four values, HL7's own definitions

| Code | Meaning | What it means for "can we use our own code" |
|---|---|---|
| `required` | "To be conformant, the concept in this element SHALL be from the specified value set." | **No.** This is a closed list — every code must come from the named `ValueSet`, with no exceptions, at every profile layer, forever (a `required` binding can never be loosened by a child profile). `docs/architecture/fhir-profiling-and-extensibility-strategy.md`'s §7 "Category A" (`IdentifierUse`, `PatientGender`, etc.) are exactly the fields bound this way — correctly kept as Postgres `Enum` columns for exactly this reason. |
| `extensible` | "SHALL be from the specified value set if any of the codes within the value set can apply to the concept being communicated. If the value set does not cover the concept, alternate codings (or text) may be included instead." | **Yes, conditionally.** If the standard value set has a code that fits your concept, you're expected to use it. If it genuinely doesn't (your concept isn't covered), you may use your own code instead. This is the binding strength that makes "custom code with standard crosswalk" a *recommended* pattern, not just a tolerated one. |
| `preferred` | "Instances are encouraged to draw from the specified codes for interoperability purposes but are not required to do so." | **Yes, freely** — using the standard codes is just a courtesy to interoperability, not a requirement. |
| `example` | "Instances are not expected or even encouraged to draw from the specified value set. The value set merely provides examples." | **Yes, essentially unconstrained** — the value set is illustrative only. |

Organization's own base-spec bindings (`type`, `identifier.type`, `contact.purpose`, address/
telecom `use`) are `extensible` or `example`-level in the base spec (not `required`) — which is
exactly why this project's design lets them carry a real `coding[]` list with custom entries,
while `IdentifierUse`/`ContactPointUse`/`AddressUse` (required bindings on simple `code` fields,
not `CodeableConcept`s) are correctly still closed Postgres enums.

## The crosswalk pattern, concretely

For an `extensible`-bound `CodeableConcept`, the spec-correct way to use your own code *and*
stay aligned with the standard one, when an equivalent standard code genuinely exists, is to
put **both** `Coding` entries in the same `coding[]` array — not to pick one or the other:

```json
{
  "coding": [
    { "system": "http://terminology.hl7.org/CodeSystem/organization-type", "code": "prov", "display": "Healthcare Provider" },
    { "system": "https://clinic-x.dev/fhir/CodeSystem/org-type", "code": "main-clinic", "display": "Main Clinic Location" }
  ],
  "text": "Main clinic"
}
```

A consumer that only understands the standard terminology reads the first `Coding` and ignores
the second. A consumer that understands this org's own system (e.g. its own GraphQL gateway, or
internal reporting) reads the second. Neither consumer has to know about the other's coding
scheme, and nothing is lost. **This is the exact design already implemented this session:**

- `OrganizationCodingInput` (`app/schemas/organization/input/_shared.py`) — one entry of a
  `coding[]` list, reused wherever Organization has an `extensible`/`example`-bound
  `CodeableConcept`.
- `OrganizationTypeCoding`, `OrganizationIdentifierTypeCoding`, `OrganizationContactPurposeCoding`
  — the real child tables storing `0..*` codings per concept, one row per `Coding`, exactly
  matching the array shape above.
- `_fhir_coding_list()` in both `app/fhir/mappers/organization/fhir.py` and `payload.py` —
  renders/reads the array in exactly this shape, standard and custom codings side by side.

The docstring already written on `OrganizationCodingInput` states this reasoning directly: "an
org may need its own custom code for a concept AND a crosswalk to a standard terminology (e.g.
SNOMED CT) at the same time."

## What this project does *not* yet do

- **No `ValueSet`/`CodeSystem` resolution against a real terminology server.** Nothing today
  checks whether a `code` claimed to be from `http://terminology.hl7.org/CodeSystem/organization-type`
  is actually a real member of that value set — `extensible`/`preferred`/`example` bindings
  aren't enforced at all right now, only `required` bindings (via Postgres enum columns).
  `docs/architecture/fhir-profiling-and-extensibility-strategy.md`'s §4 pipeline step 3
  (`validate_terminology`) is where this would plug in, delegating to the already-existing
  `TerminologyService`/`TerminologyFieldBinding` (`app/models/terminology/terminology.py`).
- **No formal `ConceptMap` between this org's custom codes and the standard ones.** The
  crosswalk pattern above works by *co-locating* both codings in the same array — it doesn't
  require (though it doesn't preclude) also publishing a formal `ConceptMap` resource declaring
  the equivalence rule once, system-wide, instead of per-instance. Not built, not currently
  needed given the co-location approach already works for this project's actual use case.
- **No enforcement that a custom `system` URI is actually registered/owned by the tenant
  asserting it.** Anyone can currently put any URI in a `Coding.system` field. If this becomes
  a real integrity concern, it's the same closed-world-registration idea already proposed for
  extension `url`s in that architecture document's §5 — worth deciding deliberately if/when it
  matters, not assumed.
