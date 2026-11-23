from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirReferenceInput,
)

# medicationdispense-status (the required binding of MedicationDispense.status).
StatusCode = Literal[
    "preparation",
    "in-progress",
    "cancelled",
    "on-hold",
    "completed",
    "entered-in-error",
    "stopped",
    "declined",
    "unknown",
]

_EXAMPLE = {
    "resourceType": "MedicationDispense",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/medication-dispense-id",
            "value": "MD-1001",
        }
    ],
    "status": "completed",
    "category": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/medicationdispense-category",
                "code": "outpatient",
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
    "performer": [{"actor": {"reference": "Practitioner/30001"}}],
    "authorizingPrescription": [{"reference": "MedicationRequest/90001"}],
    "type": {
        "coding": [
            {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "FF"}
        ]
    },
    "quantity": {"value": 30, "unit": "tablet"},
    "daysSupply": {
        "value": 30,
        "unit": "Day",
        "system": "http://unitsofmeasure.org",
        "code": "d",
    },
    "whenPrepared": "2026-01-15T09:00:00Z",
    "whenHandedOver": "2026-01-15T10:00:00Z",
    "destination": {"reference": "Location/230001"},
    "receiver": [{"reference": "Patient/10001"}],
    "dosageInstruction": [{"text": "1 tablet daily"}],
}


class MedicationDispensePerformerInput(FhirInputModel):
    """MedicationDispense.performer - who performed the dispense and what they did."""

    function: FhirCodeableConceptInput | None = Field(
        None, description="Who performed the dispense and what they did."
    )
    actor: FhirReferenceInput | None = Field(
        None,
        description="Individual who was performing - Reference(Practitioner | PractitionerRole | Organization | Patient | Device | RelatedPerson) (required by R4). A relative reference to a resource this server has must exist in the caller's org (422 otherwise). Searched by `performer`.",
    )


class MedicationDispenseAnnotationInput(FhirInputModel):
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


class MedicationDispenseSubstitutionInput(FhirInputModel):
    """MedicationDispense.substitution - whether a substitution was performed on the dispense."""

    wasSubstituted: bool | None = Field(
        None,
        description="Whether a substitution was or was not performed (required by R4).",
    )
    type: FhirCodeableConceptInput | None = Field(
        None,
        description="Code signifying whether a different drug was dispensed from what was prescribed.",
    )
    reason: list[FhirCodeableConceptInput] | None = Field(
        None, description="Why was substitution made."
    )
    responsibleParty: list[FhirReferenceInput] | None = Field(
        None,
        description="Who is responsible for the substitution - Reference(Practitioner | PractitionerRole). A relative reference must exist in the caller's org (422 otherwise). Searched by `responsibleparty`.",
    )


class _MedicationDispenseFields(FhirInputModel):
    """Every writable MedicationDispense element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/medicationdispense.html). Create and patch accept exactly the
    same fields. R4 requires `status` and `medication[x]`, but only the java_validator backend
    enforces cardinality minimums.

    The validated body is stored whole (MedicationDispenseModel.content), so any valid R4 element
    is kept - including ones this model does not declare. Server-managed elements are ignored if
    sent: `id` (assigned from the medication_dispense_id sequence) and `meta` (audit/tenant data,
    stamped on at read time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["MedicationDispense"] | None = Field(
        None, description="Optional; if supplied it must be 'MedicationDispense'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries - validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="External identifier. Searched by `identifier`."
    )
    partOf: list[FhirReferenceInput] | None = Field(
        None,
        description="Event that dispense is part of - Reference(Procedure). A relative reference must exist in the caller's org (422 otherwise).",
    )
    status: StatusCode | None = Field(
        None,
        description="preparation | in-progress | cancelled | on-hold | completed | entered-in-error | stopped | declined | unknown (required by R4). Searched by `status`.",
    )
    statusReasonCodeableConcept: FhirCodeableConceptInput | None = Field(
        None,
        description="Why a dispense was not performed (a CodeableConcept). One of the statusReason[x] choices.",
    )
    statusReasonReference: FhirReferenceInput | None = Field(
        None,
        description="Why a dispense was not performed - Reference(DetectedIssue). One of the statusReason[x] choices.",
    )
    category: FhirCodeableConceptInput | None = Field(
        None, description="Type of medication dispense."
    )
    medicationCodeableConcept: FhirCodeableConceptInput | None = Field(
        None,
        description="What medication was supplied (a CodeableConcept). One of the medication[x] choices (required by R4). Searched by `code`.",
    )
    medicationReference: FhirReferenceInput | None = Field(
        None,
        description="What medication was supplied - Reference(Medication). One of the medication[x] choices. A relative reference must exist in the caller's org (422 otherwise). Searched by `medication`.",
    )
    subject: FhirReferenceInput | None = Field(
        None,
        description="Who the dispense is for - Reference(Patient | Group). A relative reference must exist in the caller's org (422 otherwise). Searched by `subject` / `patient`.",
    )
    context: FhirReferenceInput | None = Field(
        None,
        description="Encounter / Episode associated with event - Reference(Encounter | EpisodeOfCare). A relative reference must exist in the caller's org (422 otherwise). Searched by `context`.",
    )
    supportingInformation: list[FhirReferenceInput] | None = Field(
        None,
        description="Information that supports the dispensing of the medication - Reference(Any). A relative reference to a resource this server has must exist in the caller's org (422 otherwise).",
    )
    performer: list[MedicationDispensePerformerInput] | None = Field(
        None, description="Who performed event."
    )
    location: FhirReferenceInput | None = Field(
        None,
        description="Where the dispense occurred - Reference(Location). A relative reference must exist in the caller's org (422 otherwise).",
    )
    authorizingPrescription: list[FhirReferenceInput] | None = Field(
        None,
        description="Medication order that authorizes the dispense - Reference(MedicationRequest). A relative reference must exist in the caller's org (422 otherwise). Searched by `prescription`.",
    )
    type: FhirCodeableConceptInput | None = Field(
        None,
        description="Trial fill, partial fill, emergency fill, etc. Searched by `type`.",
    )
    quantity: dict | None = Field(
        None,
        description="Amount dispensed (a SimpleQuantity: value, unit, system, code).",
    )
    daysSupply: dict | None = Field(
        None,
        description="Amount of medication expressed as a timing amount (a SimpleQuantity).",
    )
    whenPrepared: str | None = Field(
        None,
        description="When product was packaged and reviewed (a FHIR dateTime, possibly partial). Searched by `whenprepared`.",
    )
    whenHandedOver: str | None = Field(
        None,
        description="When product was given out (a FHIR dateTime, possibly partial). Searched by `whenhandedover`.",
    )
    destination: FhirReferenceInput | None = Field(
        None,
        description="Where the medication was sent - Reference(Location). A relative reference must exist in the caller's org (422 otherwise). Searched by `destination`.",
    )
    receiver: list[FhirReferenceInput] | None = Field(
        None,
        description="Who collected the medication - Reference(Patient | Practitioner). A relative reference must exist in the caller's org (422 otherwise). Searched by `receiver`.",
    )
    note: list[MedicationDispenseAnnotationInput] | None = Field(
        None, description="Information about the dispense."
    )
    dosageInstruction: list[dict] | None = Field(
        None,
        description="How the medication is to be used by the patient or administered by the caregiver - a list of FHIR R4 Dosage elements, validated as R4 JSON.",
    )
    substitution: MedicationDispenseSubstitutionInput | None = Field(
        None, description="Whether a substitution was performed on the dispense."
    )
    detectedIssue: list[FhirReferenceInput] | None = Field(
        None,
        description="Clinical issue with action - Reference(DetectedIssue). A relative reference must exist in the caller's org (422 otherwise).",
    )
    eventHistory: list[FhirReferenceInput] | None = Field(
        None, description="A list of relevant lifecycle events - Reference(Provenance)."
    )


class MedicationDispenseCreateSchema(_MedicationDispenseFields):
    """POST body - a FHIR R4 MedicationDispense resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class MedicationDispensePatchSchema(_MedicationDispenseFields):
    """PATCH body - a partial FHIR R4 MedicationDispense (merge-patch semantics on top-level
    elements). Only supplied elements are written; omitted ones are left untouched. A supplied
    element replaces the stored value wholesale - a list (even `[]`) replaces every existing
    entry, an object such as `substitution` replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "cancelled",
                "statusReasonCodeableConcept": {"text": "Patient did not collect"},
            }
        }
    }
