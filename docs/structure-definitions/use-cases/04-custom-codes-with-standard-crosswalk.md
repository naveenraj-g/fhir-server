# Use case: custom codes with a standard crosswalk

This use case is already **implemented**, not hypothetical — included here because it's the
concrete answer to the question that started this whole documentation effort, and it's worth
seeing end-to-end as a single worked trail from spec mechanism to actual running code.

**Scenario:** a hospital network wants to tag its Organizations with its own internal
classification (`"main-clinic"`, `"satellite-office"`, `"billing-only"`) — codes that mean
something specific inside the network's own systems — while still publishing the standard FHIR
`organization-type` code alongside it, so anything consuming this data via standard FHIR tooling
still understands what it's looking at.

## The spec mechanism (full detail in file 08)

[`08-terminology-and-codeable-concepts.md`](../08-terminology-and-codeable-concepts.md):
`Organization.type` is an `extensible`-bound `CodeableConcept`, and `CodeableConcept.coding` is
`0..*` — so both the standard coding and the custom coding belong in the *same* `coding[]` array
on the *same* `CodeableConcept`, not as two separate `type` entries:

```json
{
  "type": [
    {
      "coding": [
        { "system": "http://terminology.hl7.org/CodeSystem/organization-type", "code": "prov", "display": "Healthcare Provider" },
        { "system": "https://hospital-network.dev/fhir/CodeSystem/facility-class", "code": "main-clinic", "display": "Main Clinic" }
      ],
      "text": "Main clinic"
    }
  ]
}
```

## The actual implementation, file by file

| Layer | File | What it does |
|---|---|---|
| Storage | `app/models/organization/type.py` — `OrganizationType` (text only) + `OrganizationTypeCoding` (one row per `Coding`, FK `organization_type_id`) | One `OrganizationType` row (the `CodeableConcept`) can own many `OrganizationTypeCoding` rows (the `coding[]` array) — the `0..*` cardinality from file 05's storage table. |
| Input | `app/schemas/organization/input/_shared.py` — `OrganizationCodingInput` (system/version/code/display/user_selected) | `app/schemas/organization/input/type.py` — `OrganizationTypeInput.coding: list[OrganizationCodingInput] \| None` | One entry per `Coding`, reused identically for `identifier.type` and `contact.purpose` since they're all the same shape. |
| Response | `app/schemas/organization/response/_shared.py` — `PlainOrganizationCoding` | `type.py`'s `PlainOrganizationType.codings: list[PlainOrganizationCoding] \| None` | Same list shape on the way out. |
| Mapper (DB → FHIR) | `app/fhir/mappers/organization/fhir.py` — `_fhir_coding_list()` | Renders every `OrganizationTypeCoding` row into the `coding[]` array — standard and custom codings side by side, exactly as in the spec example above. |
| Mapper (payload → FHIR, for validation) | `app/fhir/mappers/organization/payload.py` — `_coding_list()` | The input-side mirror, used by `payload_to_fhir_organization()` to build the same shape *before* writing, so `app/fhir/validation/base_r4.py` validates the create/patch payload in true FHIR shape. |

## Why `extensible`, not `required`, is what makes this legal

If `Organization.type`'s binding were `required` instead, per
[`08-terminology-and-codeable-concepts.md`](../08-terminology-and-codeable-concepts.md)'s table,
*every* code would have to come from the standard value set — the custom
`"main-clinic"`/`"satellite-office"` codes would not be spec-conformant at all, crosswalk or no
crosswalk. This only works because the base spec itself chose `extensible` for this element —
confirm the binding strength before assuming this pattern applies to some *other* coded field;
not every `CodeableConcept` in FHIR is bound loosely enough to allow it.

## What validating this would eventually check (not built yet)

Today, `app/fhir/validation/base_r4.py` only confirms the *shape* is a valid `coding[]` array
(each entry has the right field types) — it does not check whether the standard-looking coding
(`http://terminology.hl7.org/CodeSystem/organization-type` / `"prov"`) is actually a real member
of that value set, nor does it know the binding is `extensible` rather than `required` at all.
That's the terminology-validation pipeline step (`docs/architecture/fhir-profiling-and-extensibility-strategy.md`
§4, step 3) — not yet wired up for Organization.
