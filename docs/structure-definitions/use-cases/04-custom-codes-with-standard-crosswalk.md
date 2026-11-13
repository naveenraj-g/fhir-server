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

Organization is stored Medplum-style (see CLAUDE.md, "Medplum-style storage"): the whole FHIR
resource lives in one `content` JSONB column, and the search index is derived from it. So
there is no per-field mapping for `type` anywhere — the `coding[]` array above is stored and
served exactly as sent, standard and custom codings side by side.

| Layer | File | What it does |
|---|---|---|
| Input (docs only) | `app/schemas/fhir_input/codeable_concept.py` — `FhirCodeableConceptInput.coding: list[FhirCodingInput]` (`coding.py`: system/version/code/display/userSelected) | Documents the request shape in OpenAPI and type-checks it early. Not what gets stored — the raw request body is (see `app/services/organization/core.py`). |
| Validation document | `app/fhir/input_payload.py` — `fhir_create_document()` / `fhir_patch_fragment()` | Turns the raw body into the FHIR resource to validate: drops server-managed `id`/`meta`, stamps `resourceType`, prunes nulls and empty values. The `type` array passes through untouched. |
| Storage | `app/models/organization/core.py` — `OrganizationModel.content` | The validated document, `type[]` included, exactly as sent. |
| Search index | `app/models/organization/type.py` — `OrganizationType`, built by `app/repository/_content_index.py`'s `type_rows()` (called from `app/repository/organization/_indexer.py`) | One row per `coding` (`system`, `code`, `display_norm`, `text_norm`), so `type=prov` and `type=https://hospital-network.dev/fhir/CodeSystem/facility-class\|main-clinic` both find the example above. Derived from `content` on every write; never read to build a response. |
| Search | `app/repository/organization/search.py` — the `type` `SearchParam` | Token search over those rows, including `:text`, `:not`, and `:in` / `:not-in` / `:above` / `:below` resolved through the terminology service. |
| Read (DB → FHIR) | `app/fhir/mappers/organization/fhir.py`, via `app/fhir/mappers/content.py` | Serves `content` as-is and stamps `id` + `meta` — the `coding[]` array comes back in the same order it was sent. |

## Why `extensible`, not `required`, is what makes this legal

If `Organization.type`'s binding were `required` instead, per
[`08-terminology-and-codeable-concepts.md`](../08-terminology-and-codeable-concepts.md)'s table,
*every* code would have to come from the standard value set — the custom
`"main-clinic"`/`"satellite-office"` codes would not be spec-conformant at all, crosswalk or no
crosswalk. This only works because the base spec itself chose `extensible` for this element —
confirm the binding strength before assuming this pattern applies to some *other* coded field;
not every `CodeableConcept` in FHIR is bound loosely enough to allow it.

## What validation checks today

Validation runs on the whole document before it's written, through
`app/fhir/validation/dispatch.py`'s `validate_resource()`. What it checks depends on
`fhir_validation.backend` in `configs/config.yaml`:

- **`native`** (`app/fhir/validation/base_r4.py`) checks shape only, against HL7's published
  `fhir.schema.json`: each `coding[]` entry has the right field types. It does not know the
  binding is `extensible`, and doesn't check whether `prov` is really in the
  `organization-type` value set.
- **`java_validator`** (the HL7 Java validator sidecar, the configured default) walks the
  base → country → organization profile chain and checks terminology bindings too. So a
  standard coding with an unknown code can be flagged, while an `extensible` binding still
  lets the custom `facility-class` coding sit alongside it.

See `docs/architecture/fhir-profiling-and-extensibility-strategy.md` for the wider plan.
