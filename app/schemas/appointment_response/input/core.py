from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirReferenceInput,
)

ParticipationStatusCode = Literal["accepted", "declined", "tentative", "needs-action"]

_EXAMPLE = {
    "resourceType": "AppointmentResponse",
    "identifier": [{"system": "https://fhir-server.dev/fhir/identifier-system/appointment-response-id", "value": "AR-1001"}],
    "appointment": {"reference": "Appointment/40001"},
    "start": "2026-06-01T09:00:00Z",
    "end": "2026-06-01T09:30:00Z",
    "participantType": [{"coding": [{"code": "ATND", "display": "attender"}]}],
    "actor": {"reference": "Patient/10001"},
    "participantStatus": "accepted",
    "comment": "See you there",
}


class _AppointmentResponseFields(FhirInputModel):
    """Every writable AppointmentResponse element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/appointmentresponse.html). Create and patch
    accept exactly the same fields. R4 requires `appointment` and
    `participantStatus`, and (rule apr-1) at least one of `participantType` or
    `actor`; that is enforced by base R4 validation of the stored document (the
    `java_validator` backend — the native structural check has no cardinality
    minimums), not by this model. A PATCH may omit them: it is merged onto the
    current resource before validating.

    The validated body is stored whole (AppointmentResponseModel.content), so
    any valid R4 element is kept — including ones this model does not declare.
    Server-managed elements are ignored if sent: `id` (assigned from the
    appointment_response_id sequence) and `meta` (audit/tenant data, stamped on
    at read time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["AppointmentResponse"] | None = Field(
        None, description="Optional; if supplied it must be 'AppointmentResponse'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(None, description="External Ids for this item.")
    appointment: FhirReferenceInput | None = Field(
        None,
        description="Appointment this response is replying to — Reference(Appointment) (required by R4). A relative 'Appointment/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    start: str | None = Field(None, description="Time from appointment, or requested new start time (a FHIR instant, with a timezone offset).")
    end: str | None = Field(None, description="Time from appointment, or requested new end time (a FHIR instant, with a timezone offset).")
    participantType: list[FhirCodeableConceptInput] | None = Field(
        None, description="Role of participant in the appointment."
    )
    actor: FhirReferenceInput | None = Field(
        None,
        description="Person, Location, HealthcareService, or Device — Reference(Patient | Practitioner | PractitionerRole | RelatedPerson | Device | HealthcareService | Location). A relative reference to a Patient, Practitioner, PractitionerRole, HealthcareService or Location must exist in the caller's org (422 otherwise).",
    )
    participantStatus: ParticipationStatusCode | None = Field(
        None, description="accepted | declined | tentative | needs-action (required by R4)."
    )
    comment: str | None = Field(None, description="Additional comments.")


class AppointmentResponseCreateSchema(_AppointmentResponseFields):
    """POST body — a FHIR R4 AppointmentResponse resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class AppointmentResponsePatchSchema(_AppointmentResponseFields):
    """PATCH body — a partial FHIR R4 AppointmentResponse (merge-patch
    semantics on top-level elements). Only supplied elements are written;
    omitted ones are left untouched. A supplied element replaces the stored
    value wholesale — a list (even `[]`) replaces every existing entry, an
    object such as `actor` replaces the whole value, and `null` clears it."""

    model_config = {"json_schema_extra": {"example": {"participantStatus": "declined", "comment": "Cannot attend"}}}
