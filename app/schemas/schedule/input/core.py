from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

_EXAMPLE = {
    "resourceType": "Schedule",
    "active": True,
    "identifier": [{"system": "https://fhir-server.dev/fhir/identifier-system/schedule-id", "value": "S-1"}],
    "serviceCategory": [{"coding": [{"code": "17", "display": "General Practice"}]}],
    "serviceType": [{"coding": [{"code": "124", "display": "General Practice"}]}],
    "specialty": [{"coding": [{"code": "394579002", "display": "Cardiology"}]}],
    "actor": [
        {"reference": "Practitioner/30001", "display": "Dr Adam Careful"},
        {"reference": "Location/230001", "display": "Consulting room 1"},
    ],
    "planningHorizon": {"start": "2026-01-01T00:00:00Z", "end": "2026-12-31T23:59:59Z"},
    "comment": "Weekday clinic",
}


class _ScheduleFields(FhirInputModel):
    """Every writable Schedule element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/schedule.html). Create and patch accept
    exactly the same fields. R4 requires at least one `actor`; that is enforced
    by base R4 validation of the stored document (the `java_validator`
    backend — the native structural check has no cardinality minimums), not by
    this model. A PATCH may omit it: it is merged onto the current resource
    before validating.

    The validated body is stored whole (ScheduleModel.content), so any valid R4
    element is kept — including ones this model doesn't declare.
    Server-managed elements are ignored if sent: `id` (assigned from the
    schedule_id sequence) and `meta` (audit/tenant data, stamped on at read
    time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["Schedule"] | None = Field(
        None, description="Optional; if supplied it must be 'Schedule'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="External Ids for this item."
    )
    active: bool | None = Field(
        None, description="Whether this schedule is in active use."
    )
    serviceCategory: list[FhirCodeableConceptInput] | None = Field(
        None, description="High-level category."
    )
    serviceType: list[FhirCodeableConceptInput] | None = Field(
        None, description="Specific service."
    )
    specialty: list[FhirCodeableConceptInput] | None = Field(
        None, description="Type of specialty needed."
    )
    actor: list[FhirReferenceInput] | None = Field(
        None,
        description="Resource(s) that availability information is being provided for — Reference(Patient | Practitioner | PractitionerRole | RelatedPerson | Device | HealthcareService | Location), at least one (required by R4). A relative 'Practitioner/<id>', 'PractitionerRole/<id>', 'HealthcareService/<id>' or 'Location/<id>' reference must exist in the caller's org (422 otherwise); Patient, RelatedPerson and Device aren't resources on this server and aren't checked.",
    )
    planningHorizon: FhirPeriodInput | None = Field(
        None, description="Period of time covered by schedule."
    )
    comment: str | None = Field(
        None, description="Comments on availability."
    )


class ScheduleCreateSchema(_ScheduleFields):
    """POST body — a FHIR R4 Schedule resource. Creates the schedule and every
    supplied nested element atomically in one transaction."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class SchedulePatchSchema(_ScheduleFields):
    """PATCH body — a partial FHIR R4 Schedule (merge-patch semantics on
    top-level elements). Only supplied elements are written; omitted ones are
    left untouched. A supplied element replaces the stored value wholesale — a
    list (even `[]`) replaces every existing entry, an object such as
    `planningHorizon` replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {"active": False, "planningHorizon": {"start": "2026-01-01T00:00:00Z", "end": "2026-06-30T23:59:59Z"}}
        }
    }
