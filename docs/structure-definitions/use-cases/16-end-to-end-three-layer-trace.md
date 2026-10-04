# Use case: one payload, walked through all three layers end to end

Every other file in this folder explains one mechanism in isolation. This file does the
opposite: takes a single, concrete `POST /organizations` payload and walks it through base R4,
a hypothetical country profile, and a hypothetical organization profile, in sequence, showing
exactly where each layer would accept or reject it. This is the concrete realization of
[`12-three-layer-validation-architecture.md`](../12-three-layer-validation-architecture.md)'s
conceptual pipeline — read that file first if you haven't.

## The payload

```json
{
  "active": true,
  "name": "Riverside Clinic",
  "type": [
    { "coding": [{ "system": "http://terminology.hl7.org/CodeSystem/organization-type", "code": "prov" }] }
  ],
  "identifier": [
    { "system": "https://example.gov/registry-id", "value": "RC-4471" }
  ],
  "telecom": [{ "system": "email", "value": "contact@riverside.example" }]
}
```

Using the layer stack from this folder's running hypothetical
([`11-profiles-and-derivation.md`](../11-profiles-and-derivation.md)'s worked example, combined
with [`03-requiring-a-custom-identifier-system.md`](03-requiring-a-custom-identifier-system.md)'s
country rule and [`06-adding-a-custom-invariant.md`](06-adding-a-custom-invariant.md)'s org
rule):

- **Base R4** — `org-1`/`org-2`/`org-3`, plus ordinary structure.
- **Country layer** — requires at least one identifier with `system = "https://example.gov/registry-id"`.
- **Org layer** — requires at least one `telecom` with `system = "phone"` when `type` includes `prov`.

## Step 1 — base R4 structural check (`app/fhir/validation/base_r4.py`, built today)

Converts the payload to true FHIR JSON (`payload_to_fhir_organization()`) and runs it through
`fhir.schema.json`. Required fields present (`resourceType` gets added by the converter), every
value's primitive format is valid, `type[].coding[].code` is a well-formed `code` string. **Pass.**

## Step 2 — base R4 invariants (`org-1`/`org-2`/`org-3` — documented, not yet wired in)

- `org-1`: `(identifier.count() + name.count()) > 0` → `1 + 1 > 0` → **pass**.
- `org-2`: no `address[]` at all in this payload, so `address.where(use='home').empty()` is
  vacuously true → **pass**.
- `org-3`: no `telecom` entry has `use: "home"` (this one has no `use` set at all) →
  **pass**.

All three pass. Nothing in this payload would have been caught *as a difference* if invariant
checking were wired in versus not — worth noting, since it shows why this gap hasn't surfaced as
a visible bug yet despite being a real, documented one: a well-formed payload like this one
sails through regardless.

## Step 3 — country layer: registry identifier requirement (not built)

`identifier.where(system = 'https://example.gov/registry-id').exists()` → the payload's
`identifier[0].system` is exactly that URI → **pass**.

## Step 4 — organization layer: phone-for-providers requirement (not built)

`type.coding.where(code = 'prov').exists().not() or telecom.where(system = 'phone').exists()` —
`type` does include a `prov` coding, so the first half (`.not()` of "is a provider") is `false`.
The second half checks for a `phone`-system telecom — this payload only has an `email` telecom,
no `phone` entry at all. `false or false` → **`false` → fails.**

## Result

This specific payload would be **rejected at step 4**, by the *organization* layer specifically
— not because anything is wrong per base R4, and not because the country's registry-identifier
rule is unmet (it is met), but because this particular tenant's own additional rule (providers
need a phone number on file) isn't satisfied. The error returned should identify exactly this:

```json
{
  "resourceType": "OperationOutcome",
  "issue": [
    {
      "severity": "error",
      "code": "invalid",
      "diagnostics": "Clinics must record at least one phone contact.",
      "expression": ["Organization"]
    }
  ]
}
```

Reusing this project's existing `FhirValidationError` → `OperationOutcome` shape
(`app/errors/validation.py`, `app/errors/handlers.py`) — a profile-layer failure is "just
another source of 422s," exactly as
`docs/architecture/fhir-profiling-and-extensibility-strategy.md` §4 states, not a parallel error
system.

## What this trace demonstrates about layering, concretely

1. **Layers are additive, never substitutive** — the payload had to satisfy base R4, *and* the
   country rule, *and* the org rule, all at once, not whichever one happened to run last.
2. **A payload can pass every layer below the one that rejects it** — this payload is perfectly
   valid base R4, and perfectly valid under the country profile; only the org-specific layer
   objects. A validator has to keep checking every layer even after earlier ones pass, not
   short-circuit on the first success.
3. **The failure message should trace back to which layer's rule fired** — in a full
   implementation, `constraint.source` ([`06-constraints-and-invariants.md`](../06-constraints-and-invariants.md))
   is exactly the field that would let the error response (or at least the server's internal
   logging) identify *which* profile layer rejected the instance, which matters operationally
   for debugging "why was my valid-looking Organization rejected."

## What's actually runnable today, versus this full trace

Only Step 1 exists in this codebase right now. Steps 2–4 are accurately specified (here and in
the architecture document) but not implemented — this file is a specification of intended
behavior, not a description of what `POST /organizations` currently does end to end.
