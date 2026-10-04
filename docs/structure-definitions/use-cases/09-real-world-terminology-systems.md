# Use case: real-world terminology systems (SNOMED CT, LOINC, RxNorm, and your own)

[`08-terminology-and-codeable-concepts.md`](../08-terminology-and-codeable-concepts.md)
explained the mechanism (`Coding.system` + `Coding.code`, `coding[]` as `0..*`, binding
strength). This file names the actual systems in practical use, and is honest about which ones
apply to Organization versus the rest of this server's ~35 other resources.

## The systems themselves

`Coding.system` is just a URI identifying *which* code system a `code` is drawn from — there's
no FHIR-enforced list of "valid" systems; any published terminology (or your own) can be used,
subject to whatever binding strength the target element declares
([`08`](../08-terminology-and-codeable-concepts.md)'s table). The ones that come up constantly
in real healthcare FHIR data:

| System | Canonical URI | Used for | Relevant to |
|---|---|---|---|
| **SNOMED CT** | `http://snomed.info/sct` | General clinical terminology — diagnoses, findings, procedures, body structures, and (relevantly) organization/facility *types* in some jurisdictions | `Condition.code`, `Procedure.code`, and — the one that does apply to Organization — some profiles bind `Organization.type` or `Location.type` to SNOMED concepts for facility classification |
| **LOINC** | `http://loinc.org` | Laboratory and clinical observations — the "what was measured" half of a lab result | `Observation.code`, `DiagnosticReport.code` — not Organization |
| **RxNorm** | `http://www.nlm.nih.gov/research/umls/rxnorm` | Normalized drug names (US-specific) | `MedicationRequest.medicationCodeableConcept`, `Medication.code` — not Organization |
| **HL7-published CodeSystems** | `http://terminology.hl7.org/CodeSystem/...` | HL7's own value sets for structural concepts (e.g. `organization-type`, `contactentity-type`) | Already what this project's Organization work uses as the "standard" half of every crosswalk example |
| **A tenant's own system** | Any URI the org controls (e.g. `https://hospital-network.dev/fhir/CodeSystem/facility-class`) | Internal classification with no external equivalent | Already implemented — `OrganizationCodingInput`/`OrganizationTypeCoding` etc. |

**Honest scoping note:** SNOMED CT, LOINC, and RxNorm are overwhelmingly *clinical* and
*pharmacy* terminologies — they matter enormously elsewhere in this FHIR server (per
`CLAUDE.md`'s resource list: `Observation`, `Condition`, `MedicationRequest`, `Procedure`,
`DiagnosticReport`, `AllergyIntolerance`, and more all have `CodeableConcept` fields that would
realistically bind to one of these three in a production deployment). For **Organization**
specifically, the only one of the three with any real-world relevance is SNOMED CT, and only for
`Organization.type`/`Location.type` facility classification in jurisdictions that profile it
that way — LOINC and RxNorm have no natural application to an Organization resource at all.
This file names them because the mechanism is identical everywhere in FHIR, not because all
three apply to the resource this project has actually built so far.

## Choosing the right system for a given field — the actual decision

This is the practical question an implementer faces, and it's governed entirely by the target
element's `binding` (file 08), not by preference:

1. **Check the element's binding strength and `valueSet`.** If `required`, the value set
   (and therefore the system(s) it draws from) is fixed — not a choice at all.
2. **If `extensible`/`preferred`/`example`, check whether the concept you need to represent is
   actually covered by the bound value set.** If SNOMED CT (or whichever system the binding
   points at) already has a code for your concept, use it — per the `extensible` definition
   itself, that's not optional once a matching code exists.
3. **Only if no covering code exists** (the `extensible` binding's own escape hatch,
   [`08`](../08-terminology-and-codeable-concepts.md)'s table) does a tenant's own system become
   the right choice — and even then, per the crosswalk pattern, it belongs *alongside* a search
   for a standard code, not as an automatic substitute for one.

## Worked example, Organization-anchored: classifying a facility type with SNOMED alongside this project's own classification

Extending [`04-custom-codes-with-standard-crosswalk.md`](04-custom-codes-with-standard-crosswalk.md)'s
example with a third, genuinely different terminology source in the same array — showing that
`coding[]`'s `0..*` cardinality isn't limited to "one standard + one custom," it's "as many
independently meaningful codings as are relevant":

```json
{
  "type": [
    {
      "coding": [
        { "system": "http://terminology.hl7.org/CodeSystem/organization-type", "code": "prov", "display": "Healthcare Provider" },
        { "system": "http://snomed.info/sct", "code": "22232009", "display": "Hospital" },
        { "system": "https://hospital-network.dev/fhir/CodeSystem/facility-class", "code": "main-clinic", "display": "Main Clinic" }
      ],
      "text": "Main clinic — hospital facility"
    }
  ]
}
```

Three independent `Coding`s, three independent consumers: a generic FHIR tool reads the first
(the structural "this is a provider organization" signal), a clinical-terminology-aware system
reads the second (SNOMED's specific facility-type classification — `22232009` is a real SNOMED
CT concept for "Hospital"), and this project's own internal tooling reads the third. None of
them need to know the others exist.

## What's needed to actually validate any of this (not built yet)

Same gap as [`04`](04-custom-codes-with-standard-crosswalk.md)'s closing section: no terminology
server integration exists today to confirm `22232009` is actually a real, current SNOMED CT
concept, or that it's a legitimate "Hospital"-type code rather than an arbitrary string that
happens to look like a SNOMED ID. `app/fhir/validation/base_r4.py` only checks the *shape* is a
valid `coding[]` array — the terminology-validation pipeline step is designed
(`docs/architecture/fhir-profiling-and-extensibility-strategy.md` §4, step 3) but not wired up.
