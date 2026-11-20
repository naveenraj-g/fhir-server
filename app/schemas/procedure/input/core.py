from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

StatusCode = Literal[
    "preparation", "in-progress", "not-done", "on-hold", "stopped", "completed", "entered-in-error", "unknown"
]

_EXAMPLE = {
    "resourceType": "Procedure",
    "identifier": [{"system": "https://fhir-server.dev/fhir/identifier-system/procedure-id", "value": "PR-1001"}],
    "status": "completed",
    "category": {"coding": [{"system": "http://snomed.info/sct", "code": "387713003", "display": "Surgical procedure"}]},
    "code": {"coding": [{"system": "http://snomed.info/sct", "code": "80146002", "display": "Appendectomy"}]},
    "subject": {"reference": "Patient/10001"},
    "encounter": {"reference": "Encounter/20001"},
    "performedPeriod": {"start": "2023-01-15T09:30:00Z", "end": "2023-01-15T10:45:00Z"},
    "recorder": {"reference": "Practitioner/30001"},
    "asserter": {"reference": "Practitioner/30001"},
    "performer": [
        {
            "function": {"coding": [{"system": "http://snomed.info/sct", "code": "304292004", "display": "Surgeon"}]},
            "actor": {"reference": "Practitioner/30001"},
        }
    ],
    "location": {"reference": "Location/230001"},
    "reasonCode": [{"coding": [{"system": "http://snomed.info/sct", "code": "74400008", "display": "Appendicitis"}]}],
    "bodySite": [{"coding": [{"system": "http://snomed.info/sct", "code": "66754008", "display": "Appendix"}]}],
    "outcome": {"coding": [{"system": "http://snomed.info/sct", "code": "385669000", "display": "Successful"}]},
    "note": [{"text": "Uneventful.", "time": "2023-01-15T11:00:00Z"}],
}


class ProcedureAnnotationInput(FhirInputModel):
    """Annotation — a note with an author (a Reference or plain text) and a time."""

    authorReference: FhirReferenceInput | None = Field(
        None,
        description="Individual responsible for the annotation — Reference(Practitioner | Patient | RelatedPerson | Organization). A relative reference must exist in the caller's org (422 otherwise).",
    )
    authorString: str | None = Field(None, description="Individual responsible for the annotation, as plain text.")
    time: str | None = Field(None, description="When the annotation was made (a FHIR dateTime).")
    text: str | None = Field(None, description="The annotation text, as markdown (required by R4).")


class ProcedureQuantityInput(FhirInputModel):
    """Age (performedAge) — a Quantity with a time unit."""

    value: float | int | None = Field(None, description="Numerical value (with implicit precision).")
    comparator: Literal["<", "<=", ">=", ">"] | None = Field(None, description="< | <= | >= | > - how to understand the value.")
    unit: str | None = Field(None, description="Unit representation.")
    system: str | None = Field(None, description="System that defines coded unit form (usually http://unitsofmeasure.org).")
    code: str | None = Field(None, description="Coded form of the unit.")


class ProcedureRangeInput(FhirInputModel):
    """Range (performedRange) — a low and a high Quantity."""

    low: ProcedureQuantityInput | None = Field(None, description="Low limit.")
    high: ProcedureQuantityInput | None = Field(None, description="High limit.")


class ProcedurePerformerInput(FhirInputModel):
    """Procedure.performer — who performed the procedure and what they did."""

    function: FhirCodeableConceptInput | None = Field(None, description="Type of performance.")
    actor: FhirReferenceInput | None = Field(
        None,
        description="Who performed the procedure — Reference(Practitioner | PractitionerRole | Organization | Patient | RelatedPerson | Device) (required by R4). A relative reference to one of the first five must exist in the caller's org (422 otherwise).",
    )
    onBehalfOf: FhirReferenceInput | None = Field(None, description="Organization the device or practitioner was acting for — Reference(Organization).")


class ProcedureFocalDeviceInput(FhirInputModel):
    """Procedure.focalDevice — a device changed in the procedure."""

    action: FhirCodeableConceptInput | None = Field(None, description="Kind of change to device.")
    manipulated: FhirReferenceInput | None = Field(None, description="Device that was changed — Reference(Device) (required by R4).")


class _ProcedureFields(FhirInputModel):
    """Every writable Procedure element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/procedure.html). Create and patch accept exactly
    the same fields. R4 requires `status` and `subject`; that is enforced by base
    R4 validation of the stored document (the `java_validator` backend — the
    native structural check has no cardinality minimums), not by this model. A
    PATCH may omit them: it is merged onto the current resource before validating.

    The validated body is stored whole (ProcedureModel.content), so any valid R4
    element is kept — including ones this model does not declare. Server-managed
    elements are ignored if sent: `id` (assigned from the procedure_id sequence)
    and `meta` (audit/tenant data, stamped on at read time). org_id and
    created_by/updated_by come from the verified JWT (actor.org_id / actor.sub),
    never the body. There is no user_id."""

    resourceType: Literal["Procedure"] | None = Field(None, description="Optional; if supplied it must be 'Procedure'.")
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(None, description="External Identifiers for this procedure.")
    instantiatesCanonical: list[str] | None = Field(None, description="Instantiates FHIR protocol or definition (canonical URLs).")
    instantiatesUri: list[str] | None = Field(None, description="Instantiates external protocol or definition (URIs).")
    basedOn: list[FhirReferenceInput] | None = Field(None, description="A request for this procedure — Reference(CarePlan | ServiceRequest).")
    partOf: list[FhirReferenceInput] | None = Field(None, description="Part of referenced event — Reference(Procedure | Observation | MedicationAdministration). A relative `Procedure/<id>` must exist in the caller's org (422 otherwise).")
    status: StatusCode | None = Field(None, description="preparation | in-progress | not-done | on-hold | stopped | completed | entered-in-error | unknown (required by R4).")
    statusReason: FhirCodeableConceptInput | None = Field(None, description="Reason for current status.")
    category: FhirCodeableConceptInput | None = Field(None, description="Classification of the procedure.")
    code: FhirCodeableConceptInput | None = Field(None, description="Identification of the procedure.")
    subject: FhirReferenceInput | None = Field(
        None,
        description="Who the procedure was performed on — Reference(Patient | Group) (required by R4). A relative 'Patient/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    encounter: FhirReferenceInput | None = Field(None, description="Encounter created as part of — Reference(Encounter). A relative reference must exist in the caller's org (422 otherwise).")
    performedDateTime: str | None = Field(None, description="When the procedure was performed (a FHIR dateTime). One of the performed[x] choices.")
    performedPeriod: FhirPeriodInput | None = Field(None, description="When the procedure was performed (a Period). One of the performed[x] choices.")
    performedString: str | None = Field(None, description="When the procedure was performed, as text. One of the performed[x] choices.")
    performedAge: ProcedureQuantityInput | None = Field(None, description="When the procedure was performed (an Age). One of the performed[x] choices.")
    performedRange: ProcedureRangeInput | None = Field(None, description="When the procedure was performed (a Range). One of the performed[x] choices.")
    recorder: FhirReferenceInput | None = Field(None, description="Who recorded the procedure — Reference(Patient | RelatedPerson | Practitioner | PractitionerRole). A relative reference must exist in the caller's org (422 otherwise).")
    asserter: FhirReferenceInput | None = Field(None, description="Person who asserts this procedure — Reference(Patient | RelatedPerson | Practitioner | PractitionerRole). A relative reference must exist in the caller's org (422 otherwise).")
    performer: list[ProcedurePerformerInput] | None = Field(None, description="The people who performed the procedure.")
    location: FhirReferenceInput | None = Field(None, description="Where the procedure happened — Reference(Location). A relative reference must exist in the caller's org (422 otherwise).")
    reasonCode: list[FhirCodeableConceptInput] | None = Field(None, description="Coded reason procedure performed.")
    reasonReference: list[FhirReferenceInput] | None = Field(None, description="The justification that the procedure was performed — Reference(Condition | Observation | Procedure | DiagnosticReport | DocumentReference). A relative Condition or Procedure must exist in the caller's org (422 otherwise).")
    bodySite: list[FhirCodeableConceptInput] | None = Field(None, description="Target body sites.")
    outcome: FhirCodeableConceptInput | None = Field(None, description="The result of procedure.")
    report: list[FhirReferenceInput] | None = Field(None, description="Any report resulting from the procedure — Reference(DiagnosticReport | DocumentReference | Composition).")
    complication: list[FhirCodeableConceptInput] | None = Field(None, description="Complication following the procedure.")
    complicationDetail: list[FhirReferenceInput] | None = Field(None, description="A condition that is a result of the procedure — Reference(Condition). A relative reference must exist in the caller's org (422 otherwise).")
    followUp: list[FhirCodeableConceptInput] | None = Field(None, description="Instructions for follow up.")
    note: list[ProcedureAnnotationInput] | None = Field(None, description="Additional information about the procedure.")
    focalDevice: list[ProcedureFocalDeviceInput] | None = Field(None, description="Manipulated, implanted, or removed device.")
    usedReference: list[FhirReferenceInput] | None = Field(None, description="Items used during procedure — Reference(Device | Medication | Substance).")
    usedCode: list[FhirCodeableConceptInput] | None = Field(None, description="Coded items used during the procedure.")


class ProcedureCreateSchema(_ProcedureFields):
    """POST body — a FHIR R4 Procedure resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class ProcedurePatchSchema(_ProcedureFields):
    """PATCH body — a partial FHIR R4 Procedure (merge-patch semantics on
    top-level elements). Only supplied elements are written; omitted ones are left
    untouched. A supplied element replaces the stored value wholesale — a list
    (even `[]`) replaces every existing entry, an object such as `code` replaces
    the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "completed",
                "outcome": {"coding": [{"system": "http://snomed.info/sct", "code": "385669000", "display": "Successful"}]},
            }
        }
    }
