# Use case: a custom display label for a fixed code, without changing the code itself

This is the direct answer to a specific question: *"HL7 gives us fixed enum-style `code`
values — can an organization show their own label for one of those codes to their users,
without changing the underlying value we store and transmit?"*

**Yes — but the mechanism is different from, and must not be confused with, the
CodeableConcept crosswalk pattern in [`04-custom-codes-with-standard-crosswalk.md`](04-custom-codes-with-standard-crosswalk.md).**
That distinction is the whole point of this file.

## Two different FHIR shapes, two different answers

| | plain `code` | `CodeableConcept` |
|---|---|---|
| Wire shape | A bare string, e.g. `"official"`. No sub-structure at all. | An object: `{ "coding": [...], "text": "..." }`. |
| Has a `display`? | **No** — a `code` primitive is *only* the string itself. | Yes — each `Coding` in `coding[]` carries its own `display`, and the whole concept has `text`. |
| Can you add your own code alongside the standard one? | **No** — there's nowhere to put a second value; the field holds exactly one string. | **Yes** — `coding[]` is `0..*` (file 08's whole subject), so a custom `Coding` can sit right next to the standard one. |
| Binding strength, typically | `required` — a closed, permanent list (e.g. `IdentifierUse`: `usual \| official \| temp \| secondary \| old`). | Often `extensible`/`preferred`/`example` — open to custom codes by design. |

A `required`-bound `code` field (what `docs/architecture/fhir-profiling-and-extensibility-strategy.md`
§7 calls "Category A" — `IdentifierUse`, `AddressUse`, and this project's other closed Postgres
enum columns) genuinely cannot carry a second, org-defined value the way `CodeableConcept.coding[]`
can — there's no array, no second field, nothing to attach a custom value to. **This is exactly
why the instinct "we don't need to change HL7's actual code enum" is correct** — for a
`required`-bound `code`, you shouldn't, and structurally can't, swap in your own value; the
underlying stored/transmitted value must stay whatever HL7 defines.

## So where does the "organization wants their own label" need actually go?

Nowhere *inside* the resource instance. It's a presentation-layer concern, and FHIR has two
legitimate ways to handle it, depending on how formal you want to be:

### Option A — the FHIR-native mechanism: `CodeSystem.concept.designation`

Verified directly against the real `CodeSystem` StructureDefinition (not assumed):

| Field | Card. | Type | Why it exists |
|---|---|---|---|
| `CodeSystem.concept.display` | `0..1` | `string` | The code's **primary** display text, as the code system's own publisher defines it. |
| `CodeSystem.concept.designation` | `0..*` | `BackboneElement` | **Additional** representations of the same concept — alternate labels, for different audiences/languages/contexts, *without changing the code itself*. |
| `designation.language` | `0..1` | `code` | Which human language this alternate label is in. |
| `designation.use` | `0..1` | `Coding` | What *kind* of alternate representation this is (a synonym, a fully-specified name, etc. — drawn from an external terminology's own designation-type concepts, not a small closed HL7 list). |
| `designation.value` | `1..1` | `string` | The actual alternate text. |

Concretely: if a resource's `status` field (say, on `Task` or `MedicationRequest` elsewhere in
this server — Organization itself has no lifecycle `status` field, only the boolean `active`)
has a `required` binding to a `CodeSystem` like `http://hl7.org/fhir/task-status`, and the real
code for a given state is `"completed"`, an organization that wants its own staff to see
*"Fulfilled"* instead of *"Completed"* in their UI would register a `designation`:

```json
{
  "code": "completed",
  "display": "Completed",
  "designation": [
    { "language": "en", "value": "Fulfilled" }
  ]
}
```

The stored/transmitted resource still says `"status": "completed"` — nothing about the instance
data changes. The designation lives on the **`CodeSystem` resource** (terminology metadata),
not on the `Task`/`MedicationRequest` instance, and a UI layer that knows to prefer an org's
registered designation renders `"Fulfilled"` instead of the default `"Completed"` when
displaying that same underlying code.

### Option B — the pragmatic shortcut most real applications actually use

Maintaining real `CodeSystem` resources with `designation[]` entries is the fully spec-native
way, but it's a meaningful amount of terminology-server-shaped infrastructure
(`docs/architecture/fhir-profiling-and-extensibility-strategy.md`'s §4 step 3 already notes this
project's terminology validation isn't built out that far yet). The much more common pragmatic
approach — used by plenty of production FHIR-adjacent systems — is a plain **presentation-layer
lookup table**, entirely outside the FHIR resource itself: `{tenant_id, field, code) → label}`,
maintained by (or for) the org, consulted only when rendering to a human, never touching the
stored or transmitted FHIR value. Functionally equivalent to Option A for the "show my own
label" goal, with none of the `CodeSystem`/`designation` infrastructure — the tradeoff is it's
this project's own convention, not something a generic external FHIR tool would know how to
interpret the way it would a real `designation`.

## Why this is correctly *not* the same mechanism as the CodeableConcept crosswalk

[`04-custom-codes-with-standard-crosswalk.md`](04-custom-codes-with-standard-crosswalk.md)'s
pattern works because `CodeableConcept.coding[]` genuinely has room for a second, independently
meaningful `Coding` — the custom code there is a **real, separate code** an org's own systems
use internally (e.g. `"main-clinic"`), existing *alongside* the standard one. The use case in
this file is different: the organization doesn't want a second code with its own meaning, it
wants a **different label for the exact same underlying value**. Reaching for the
`CodeableConcept` crosswalk pattern to solve this would be a mismatch — among other things, most
of the fields this concern applies to (`IdentifierUse`, status fields) aren't `CodeableConcept`s
in the first place; they're plain `code`s, so the crosswalk mechanism isn't even available on
them.

## What's needed to actually enforce/support this (not built yet)

This project doesn't currently model `CodeSystem`/`designation` data anywhere, nor a
presentation-layer label-override table. If this becomes a real product need, Option B is by far
the smaller lift (one small lookup table + a gateway/frontend read), and is the pragmatic
recommendation unless there's a concrete reason this project needs to interoperate with external
FHIR tooling that would specifically understand a real `designation`.
