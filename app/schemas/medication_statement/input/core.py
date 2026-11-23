from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

# medication-statement-status (the required binding of MedicationStatement.status).
StatusCode = Literal[
    "active",
    "completed",
    "entered-in-error",
    "intended",
    "stopped",
    "on-hold",
    "unknown",
    "not-taken",
]

_EXAMPLE = {
    "resourceType": "MedicationStatement",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/medication-statement-id",
            "value": "MS-1001",
        }
    ],
    "status": "active",
    "category": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/medication-statement-category",
                "code": "community",
            }
        ]
    },
    "medicationCodeableConcept": {
        "coding": [
            {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "197361",
                "display": "Amlodipine 5 MG Oral Tablet",
            }
        ]
    },
    "subject": {"reference": "Patient/10001"},
    "context": {"reference": "Encounter/20001"},
    "effectiveDateTime": "2026-01-15T10:00:00Z",
    "dateAsserted": "2026-01-15T10:05:00Z",
    "informationSource": {"reference": "Practitioner/30001"},
    "reasonCode": [
        {"coding": [{"system": "http://snomed.info/sct", "code": "38341003"}]}
    ],
    "note": [{"text": "Patient reports taking it in the morning."}],
    "dosage": [
        {
            "text": "5 mg once daily",
            "route": {
                "coding": [{"system": "http://snomed.info/sct", "code": "26643006"}]
            },
            "doseAndRate": [
                {
                    "doseQuantity": {
                        "value": 5,
                        "unit": "mg",
                        "system": "http://unitsofmeasure.org",
                        "code": "mg",
                    }
                }
            ],
        }
    ],
}


class MedicationStatementAnnotationInput(FhirInputModel):
    """Annotation - a note with an author (a Reference or plain text) and a time."""

    authorReference: FhirReferenceInput | None = Field(
        None,
        description="Individual responsible for the annotation - Reference(Practitioner | Patient | RelatedPerson | Organization). A relative reference must exist in the caller's org (422 otherwise).",
    )
    authorString: str | None = Field(
        None, description="Individual responsible for the annotation, as plain text."
    )
    time: str | None = Field(
        None, description="When the annotation was made (a FHIR dateTime)."
    )
    text: str | None = Field(
        None, description="The annotation text, as markdown (required by R4)."
    )


class _MedicationStatementFields(FhirInputModel):
    """Every writable MedicationStatement element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/medicationstatement.html). Create and patch accept exactly the
    same fields. R4 requires `status`, `medication[x]` and `subject`, but only the java_validator
    backend enforces cardinality minimums.

    The validated body is stored whole (MedicationStatementModel.content), so any valid R4
    element is kept - including ones this model does not declare. Server-managed elements are
    ignored if sent: `id` (assigned from the medication_statement_id sequence) and `meta`
    (audit/tenant data, stamped on at read time). org_id and created_by/updated_by come from the
    verified JWT (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["MedicationStatement"] | None = Field(
        None, description="Optional; if supplied it must be 'MedicationStatement'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries - validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None,
        description="External identifier. Searched by `identifier`.",
    )
    basedOn: list[FhirReferenceInput] | None = Field(
        None,
        description="Fulfils plan, proposal or order - Reference(MedicationRequest | CarePlan | ServiceRequest). A relative reference to a resource this server has must exist in the caller's org (422 otherwise).",
    )
    partOf: list[FhirReferenceInput] | None = Field(
        None,
        description="Part of referenced event - Reference(MedicationAdministration | MedicationDispense | MedicationStatement | Procedure | Observation). A relative reference must exist in the caller's org (422 otherwise). Searched by `part-of`.",
    )
    status: StatusCode | None = Field(
        None,
        description="active | completed | entered-in-error | intended | stopped | on-hold | unknown | not-taken (required by R4). Searched by `status`.",
    )
    statusReason: list[FhirCodeableConceptInput] | None = Field(
        None, description="Reason for current status."
    )
    category: FhirCodeableConceptInput | None = Field(
        None, description="Type of medication usage. Searched by `category`."
    )
    medicationCodeableConcept: FhirCodeableConceptInput | None = Field(
        None,
        description="What medication was taken (a CodeableConcept). One of the medication[x] choices (required by R4). Searched by `code`.",
    )
    medicationReference: FhirReferenceInput | None = Field(
        None,
        description="What medication was taken - Reference(Medication). One of the medication[x] choices. A relative reference must exist in the caller's org (422 otherwise). Searched by `medication`.",
    )
    subject: FhirReferenceInput | None = Field(
        None,
        description="Who is/was taking the medication - Reference(Patient | Group) (required by R4). A relative reference must exist in the caller's org (422 otherwise). Searched by `subject` / `patient`.",
    )
    context: FhirReferenceInput | None = Field(
        None,
        description="Encounter / Episode associated with MedicationStatement - Reference(Encounter | EpisodeOfCare). A relative reference must exist in the caller's org (422 otherwise). Searched by `context`.",
    )
    effectiveDateTime: str | None = Field(
        None,
        description="The date/time or interval when the medication is/was/will be taken (a dateTime, possibly partial). One of the effective[x] choices. Searched by `effective`.",
    )
    effectivePeriod: FhirPeriodInput | None = Field(
        None,
        description="The interval when the medication is/was/will be taken. One of the effective[x] choices. Searched by `effective`.",
    )
    dateAsserted: str | None = Field(
        None, description="When the statement was asserted (a FHIR dateTime)."
    )
    informationSource: FhirReferenceInput | None = Field(
        None,
        description="Person or organization that provided the information - Reference(Patient | Practitioner | PractitionerRole | RelatedPerson | Organization). A relative reference must exist in the caller's org (422 otherwise). Searched by `source`.",
    )
    derivedFrom: list[FhirReferenceInput] | None = Field(
        None,
        description="Additional supporting information - Reference(Any). A relative reference to a resource this server has must exist in the caller's org (422 otherwise).",
    )
    reasonCode: list[FhirCodeableConceptInput] | None = Field(
        None, description="Reason for why the medication is being/was taken."
    )
    reasonReference: list[FhirReferenceInput] | None = Field(
        None,
        description="Condition or observation that supports why the medication is being/was taken - Reference(Condition | Observation | DiagnosticReport). A relative reference must exist in the caller's org (422 otherwise).",
    )
    note: list[MedicationStatementAnnotationInput] | None = Field(
        None, description="Further information about the statement."
    )
    dosage: list[dict] | None = Field(
        None,
        description="Details of how the medication is/was taken or should be taken - a list of FHIR R4 Dosage elements (sequence, text, additionalInstruction, patientInstruction, timing, asNeeded[x], site, route, method, doseAndRate, maxDosePerPeriod, maxDosePerAdministration, maxDosePerLifetime), validated as R4 JSON.",
    )


class MedicationStatementCreateSchema(_MedicationStatementFields):
    """POST body - a FHIR R4 MedicationStatement resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class MedicationStatementPatchSchema(_MedicationStatementFields):
    """PATCH body - a partial FHIR R4 MedicationStatement (merge-patch semantics on top-level
    elements). Only supplied elements are written; omitted ones are left untouched. A supplied
    element replaces the stored value wholesale - a list (even `[]`) replaces every existing
    entry, an object such as `subject` replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "stopped",
                "effectivePeriod": {"start": "2026-01-15", "end": "2026-03-01"},
            }
        }
    }
