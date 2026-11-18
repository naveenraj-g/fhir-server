from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirReferenceInput,
)

SlotStatusCode = Literal["busy", "free", "busy-unavailable", "busy-tentative", "entered-in-error"]

_EXAMPLE = {
    "resourceType": "Slot",
    "status": "free",
    "schedule": {"reference": "Schedule/200001"},
    "start": "2026-06-01T09:00:00Z",
    "end": "2026-06-01T09:30:00Z",
    "identifier": [{"system": "https://fhir-server.dev/fhir/identifier-system/slot-id", "value": "SL-1"}],
    "serviceCategory": [{"coding": [{"code": "17", "display": "General Practice"}]}],
    "serviceType": [{"coding": [{"code": "124", "display": "General Practice"}]}],
    "specialty": [{"coding": [{"code": "394579002", "display": "Cardiology"}]}],
    "appointmentType": {"coding": [{"code": "ROUTINE", "display": "Routine appointment"}]},
    "overbooked": False,
    "comment": "Bring previous reports",
}


class _SlotFields(FhirInputModel):
    """Every writable Slot element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/slot.html). Create and patch accept exactly
    the same fields. R4 requires `schedule`, `status`, `start` and `end`; that
    is enforced by base R4 validation of the stored document (the
    `java_validator` backend — the native structural check has no cardinality
    minimums), not by this model. A PATCH may omit them: it is merged onto the
    current resource before validating.

    The validated body is stored whole (SlotModel.content), so any valid R4
    element is kept — including ones this model doesn't declare.
    Server-managed elements are ignored if sent: `id` (assigned from the
    slot_id sequence) and `meta` (audit/tenant data, stamped on at read time).
    org_id and created_by/updated_by come from the verified JWT (actor.org_id /
    actor.sub), never the body. There is no user_id."""

    resourceType: Literal["Slot"] | None = Field(
        None, description="Optional; if supplied it must be 'Slot'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="External Ids for this item."
    )
    serviceCategory: list[FhirCodeableConceptInput] | None = Field(
        None, description="A broad categorization of the service that is to be performed during this appointment."
    )
    serviceType: list[FhirCodeableConceptInput] | None = Field(
        None, description="The type of appointments that can be booked into this slot."
    )
    specialty: list[FhirCodeableConceptInput] | None = Field(
        None, description="The specialty of a practitioner that would be required to perform the service requested in this appointment."
    )
    appointmentType: FhirCodeableConceptInput | None = Field(
        None, description="The style of appointment or patient that may be booked in the slot (not service type)."
    )
    schedule: FhirReferenceInput | None = Field(
        None,
        description="The schedule resource that this slot defines an interval of status information — Reference(Schedule), required by R4. A relative 'Schedule/<id>' reference must exist in the caller's org (422 otherwise).",
    )
    status: SlotStatusCode | None = Field(
        None, description="busy | free | busy-unavailable | busy-tentative | entered-in-error (required by R4)."
    )
    start: str | None = Field(
        None, description="Date/Time that the slot is to begin (a FHIR instant, with a timezone offset; required by R4)."
    )
    end: str | None = Field(
        None, description="Date/Time that the slot is to conclude (a FHIR instant, with a timezone offset; required by R4)."
    )
    overbooked: bool | None = Field(
        None, description="This slot has already been overbooked, appointments are unlikely to be accepted for this time."
    )
    comment: str | None = Field(
        None, description="Comments on the slot to describe any extended information."
    )


class SlotCreateSchema(_SlotFields):
    """POST body — a FHIR R4 Slot resource. Creates the slot and every
    supplied nested element atomically in one transaction."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class SlotPatchSchema(_SlotFields):
    """PATCH body — a partial FHIR R4 Slot (merge-patch semantics on top-level
    elements). Only supplied elements are written; omitted ones are left
    untouched. A supplied element replaces the stored value wholesale — a list
    (even `[]`) replaces every existing entry, an object such as `schedule` or
    `appointmentType` replaces the whole value, and `null` clears it."""

    model_config = {"json_schema_extra": {"example": {"status": "busy", "overbooked": True}}}
