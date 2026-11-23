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

# medication-admin-status (the required binding of MedicationAdministration.status).
StatusCode = Literal[
    "in-progress",
    "not-done",
    "on-hold",
    "completed",
    "entered-in-error",
    "stopped",
    "unknown",
]

_EXAMPLE = {
    "resourceType": "MedicationAdministration",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/medication-administration-id",
            "value": "MA-1001",
        }
    ],
    "status": "completed",
    "category": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/medication-admin-category",
                "code": "inpatient",
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
    "performer": [{"actor": {"reference": "Practitioner/30001"}}],
    "reasonCode": [
        {"coding": [{"system": "http://snomed.info/sct", "code": "38341003"}]}
    ],
    "request": {"reference": "MedicationRequest/90001"},
    "dosage": {
        "text": "5 mg orally",
        "route": {"coding": [{"system": "http://snomed.info/sct", "code": "26643006"}]},
        "dose": {
            "value": 5,
            "unit": "mg",
            "system": "http://unitsofmeasure.org",
            "code": "mg",
        },
    },
}


class MedicationAdministrationPerformerInput(FhirInputModel):
    """MedicationAdministration.performer - who performed the administration and in what role."""

    function: FhirCodeableConceptInput | None = Field(
        None, description="Type of performance (e.g. performer, verifier)."
    )
    actor: FhirReferenceInput | None = Field(
        None,
        description="Who performed the administration - Reference(Practitioner | PractitionerRole | Patient | RelatedPerson | Device) (required by R4). A relative reference to a resource this server has must exist in the caller's org (422 otherwise). Searched by `performer`.",
    )


class MedicationAdministrationAnnotationInput(FhirInputModel):
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


class _MedicationAdministrationFields(FhirInputModel):
    """Every writable MedicationAdministration element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/medicationadministration.html). Create and patch accept exactly
    the same fields. R4 requires `status`, `medication[x]`, `subject` and `effective[x]`, but
    only the java_validator backend enforces cardinality minimums.

    The validated body is stored whole (MedicationAdministrationModel.content), so any valid R4
    element is kept - including ones this model does not declare. Server-managed elements are
    ignored if sent: `id` (assigned from the medication_administration_id sequence) and `meta`
    (audit/tenant data, stamped on at read time). org_id and created_by/updated_by come from the
    verified JWT (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["MedicationAdministration"] | None = Field(
        None, description="Optional; if supplied it must be 'MedicationAdministration'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries - validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="External identifier. Searched by `identifier`."
    )
    instantiates: list[str] | None = Field(
        None, description="Instantiates protocol or definition (a list of URIs)."
    )
    partOf: list[FhirReferenceInput] | None = Field(
        None,
        description="Part of referenced event - Reference(MedicationAdministration | Procedure). A relative reference must exist in the caller's org (422 otherwise).",
    )
    status: StatusCode | None = Field(
        None,
        description="in-progress | not-done | on-hold | completed | entered-in-error | stopped | unknown (required by R4). Searched by `status`.",
    )
    statusReason: list[FhirCodeableConceptInput] | None = Field(
        None,
        description="Reason administration not performed. Searched by `reason-not-given`.",
    )
    category: FhirCodeableConceptInput | None = Field(
        None, description="Type of medication usage."
    )
    medicationCodeableConcept: FhirCodeableConceptInput | None = Field(
        None,
        description="What was administered (a CodeableConcept). One of the medication[x] choices (required by R4). Searched by `code`.",
    )
    medicationReference: FhirReferenceInput | None = Field(
        None,
        description="What was administered - Reference(Medication). One of the medication[x] choices. A relative reference must exist in the caller's org (422 otherwise). Searched by `medication`.",
    )
    subject: FhirReferenceInput | None = Field(
        None,
        description="Who received the medication - Reference(Patient | Group) (required by R4). A relative reference must exist in the caller's org (422 otherwise). Searched by `subject` / `patient`.",
    )
    context: FhirReferenceInput | None = Field(
        None,
        description="Encounter or Episode of Care administered as part of - Reference(Encounter | EpisodeOfCare). A relative reference must exist in the caller's org (422 otherwise). Searched by `context`.",
    )
    supportingInformation: list[FhirReferenceInput] | None = Field(
        None,
        description="Additional information to support administration - Reference(Any). A relative reference to a resource this server has must exist in the caller's org (422 otherwise).",
    )
    effectiveDateTime: str | None = Field(
        None,
        description="Start and end time of administration (a dateTime, possibly partial). One of the effective[x] choices (required by R4). Searched by `effective-time`.",
    )
    effectivePeriod: FhirPeriodInput | None = Field(
        None,
        description="Start and end time of administration. One of the effective[x] choices. Searched by `effective-time`.",
    )
    performer: list[MedicationAdministrationPerformerInput] | None = Field(
        None,
        description="Who performed the medication administration and what they did.",
    )
    reasonCode: list[FhirCodeableConceptInput] | None = Field(
        None, description="Reason administration performed. Searched by `reason-given`."
    )
    reasonReference: list[FhirReferenceInput] | None = Field(
        None,
        description="Condition or observation that supports why the medication was administered - Reference(Condition | Observation | DiagnosticReport). A relative reference must exist in the caller's org (422 otherwise).",
    )
    request: FhirReferenceInput | None = Field(
        None,
        description="Request administration performed against - Reference(MedicationRequest). A relative reference must exist in the caller's org (422 otherwise). Searched by `request`.",
    )
    device: list[FhirReferenceInput] | None = Field(
        None,
        description="Device used to administer - Reference(Device). Searched by `device`.",
    )
    note: list[MedicationAdministrationAnnotationInput] | None = Field(
        None, description="Information about the administration."
    )
    dosage: dict | None = Field(
        None,
        description="Details of how medication was taken - one FHIR R4 MedicationAdministration.dosage (text, site, route, method, dose, rateRatio / rateQuantity), validated as R4 JSON.",
    )
    eventHistory: list[FhirReferenceInput] | None = Field(
        None,
        description="A list of events of interest in the lifecycle - Reference(Provenance).",
    )


class MedicationAdministrationCreateSchema(_MedicationAdministrationFields):
    """POST body - a FHIR R4 MedicationAdministration resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class MedicationAdministrationPatchSchema(_MedicationAdministrationFields):
    """PATCH body - a partial FHIR R4 MedicationAdministration (merge-patch semantics on
    top-level elements). Only supplied elements are written; omitted ones are left untouched. A
    supplied element replaces the stored value wholesale - a list (even `[]`) replaces every
    existing entry, an object such as `dosage` replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "stopped",
                "statusReason": [{"text": "Patient refused"}],
            }
        }
    }
