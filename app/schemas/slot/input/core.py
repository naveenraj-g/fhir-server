from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput
from app.schemas.enums import IdentifierUse, SlotStatus

from .identifier import SlotIdentifierInput
from .service_category import SlotServiceCategoryInput
from .service_type import SlotServiceTypeInput
from .specialty import SlotSpecialtyInput


class SlotCreateSchema(BaseModel):
    """Creates a Slot and any combination of its 4 sub-resource lists
    atomically in one request — same set-once-then-patch shape as
    Organization/HealthcareService/PractitionerRole/Schedule, no separate
    scalar-only vs. full create split. org_id and created_by both come
    from the verified JWT (actor.org_id / actor.sub) — neither is a
    request body field. Like Organization/Location/HealthcareService/
    PractitionerRole/Schedule, Slot has no user_id field at all — it's a
    shared tenant-level entity (a bookable time slot), not scoped to an
    individual end-user.

    `appointment_type` is a 0..1 CodeableConcept living directly on this
    schema (not a list sub-resource, since Slot.appointmentType itself is
    0..1) — `appointment_type_coding` is the real 0..* coding list,
    `appointment_type_text` is the CodeableConcept's own sibling field.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "schedule": "Schedule/200001",
                "schedule_display": "General Practice Schedule",
                "status": "free",
                "start": "2026-02-01T09:00:00Z",
                "end": "2026-02-01T09:30:00Z",
                "overbooked": False,
                "comment": "Standard consultation slot",
                "identifier": [],
                "service_category": [],
                "service_type": [{"coding": [{"code": "57", "display": "Immunization"}]}],
                "specialty": [],
                "appointment_type_coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0276",
                        "code": "ROUTINE",
                        "display": "Routine appointment",
                    }
                ],
                "appointment_type_text": "Routine",
            }
        },
    )

    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries. Not yet validated against registered extension definitions.",
    )

    # schedule (1..1) Reference(Schedule) — required
    schedule: str = Field(
        ...,
        description="The schedule resource that this slot defines an interval of status information, as a FHIR reference string (e.g. 'Schedule/200001'). Rejected with 422 if it doesn't exist in this org.",
    )
    schedule_display: str | None = Field(
        None,
        description="Plain text narrative that identifies the schedule in addition to the reference.",
    )
    schedule_identifier_use: IdentifierUse | None = Field(
        None,
        description="Logical-identifier fallback for schedule (used when it isn't a resource in this system) — identifies the purpose for that identifier, if known.",
    )
    schedule_identifier_type_system: str | None = Field(
        None,
        description="Fallback identifier — the code system that defines the meaning of its type code.",
    )
    schedule_identifier_type_version: str | None = Field(
        None,
        description="Fallback identifier — the version of the code system used for its type code.",
    )
    schedule_identifier_type_code: str | None = Field(
        None,
        description="Fallback identifier — a symbol in syntax defined by the code system.",
    )
    schedule_identifier_type_display: str | None = Field(
        None,
        description="Fallback identifier — a representation of the meaning of its type code.",
    )
    schedule_identifier_type_text: str | None = Field(
        None,
        description="Fallback identifier — a human language representation of its type.",
    )
    schedule_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was chosen by a user directly.",
    )
    schedule_identifier_system: str | None = Field(
        None, description="Fallback identifier — the namespace URL for the value."
    )
    schedule_identifier_value: str | None = Field(
        None,
        description="Fallback identifier — the portion typically relevant to the user, unique within the system.",
    )
    schedule_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — start of its validity period."
    )
    schedule_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — end of its validity period."
    )

    # status (1..1) — required
    status: SlotStatus = Field(
        ..., description="busy | free | busy-unavailable | busy-tentative | entered-in-error."
    )

    # start / end (1..1 each) — required
    start: datetime = Field(..., description="Date/Time that the slot is to begin.")
    end: datetime = Field(..., description="Date/Time that the slot is to conclude.")

    appointment_type_coding: list[CodingInput] | None = Field(
        None,
        description="Coding(s) for the style of appointment or patient that may be booked in this slot.",
    )
    appointment_type_text: str | None = Field(
        None,
        description="A human language representation of the appointment type.",
    )

    overbooked: bool | None = Field(
        None,
        description="This slot has already been overbooked, appointments are unlikely to be accepted for this time.",
    )
    comment: str | None = Field(
        None,
        description="Comments on the slot to describe any extended information, such as custom constraints on the slot.",
    )

    identifier: list[SlotIdentifierInput] | None = Field(
        None, description="External identifiers for this item."
    )
    service_category: list[SlotServiceCategoryInput] | None = Field(
        None, description="A broad categorization of the service for this slot."
    )
    service_type: list[SlotServiceTypeInput] | None = Field(
        None, description="The type of appointments that can be booked into this slot."
    )
    specialty: list[SlotSpecialtyInput] | None = Field(
        None,
        description="The specialty of a practitioner that would be required to perform the service requested in this slot.",
    )


class SlotPatchSchema(BaseModel):
    """Partial update — only supplied fields are written. Every supplied
    sub-resource list (even `[]`) replaces the corresponding rows wholesale;
    omitted lists are left untouched. updated_by comes from the verified
    JWT (actor.sub), not a request body field."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "status": "busy",
                "comment": "Reserved for walk-in",
            }
        },
    )

    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries — replaces the full list if supplied.",
    )
    schedule: str | None = Field(
        None,
        description="The schedule resource, as a FHIR reference string. Set to null to clear.",
    )
    schedule_display: str | None = Field(
        None,
        description="Plain text narrative that identifies the schedule in addition to the reference.",
    )
    schedule_identifier_use: IdentifierUse | None = Field(
        None,
        description="Logical-identifier fallback for schedule — identifies the purpose for that identifier, if known.",
    )
    schedule_identifier_type_system: str | None = Field(
        None,
        description="Fallback identifier — the code system that defines the meaning of its type code.",
    )
    schedule_identifier_type_version: str | None = Field(
        None,
        description="Fallback identifier — the version of the code system used for its type code.",
    )
    schedule_identifier_type_code: str | None = Field(
        None,
        description="Fallback identifier — a symbol in syntax defined by the code system.",
    )
    schedule_identifier_type_display: str | None = Field(
        None,
        description="Fallback identifier — a representation of the meaning of its type code.",
    )
    schedule_identifier_type_text: str | None = Field(
        None,
        description="Fallback identifier — a human language representation of its type.",
    )
    schedule_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was chosen by a user directly.",
    )
    schedule_identifier_system: str | None = Field(
        None, description="Fallback identifier — the namespace URL for the value."
    )
    schedule_identifier_value: str | None = Field(
        None,
        description="Fallback identifier — the portion typically relevant to the user, unique within the system.",
    )
    schedule_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — start of its validity period."
    )
    schedule_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — end of its validity period."
    )

    status: SlotStatus | None = Field(
        None, description="busy | free | busy-unavailable | busy-tentative | entered-in-error."
    )
    start: datetime | None = Field(
        None, description="Date/Time that the slot is to begin."
    )
    end: datetime | None = Field(
        None, description="Date/Time that the slot is to conclude."
    )

    appointment_type_coding: list[CodingInput] | None = Field(
        None,
        description="Coding(s) for the style of appointment — replaces the full list if supplied.",
    )
    appointment_type_text: str | None = Field(
        None, description="A human language representation of the appointment type."
    )

    overbooked: bool | None = Field(
        None, description="This slot has already been overbooked."
    )
    comment: str | None = Field(
        None, description="Comments on the slot."
    )

    identifier: list[SlotIdentifierInput] | None = Field(
        None, description="External identifiers — replaces the full list if supplied."
    )
    service_category: list[SlotServiceCategoryInput] | None = Field(
        None,
        description="Broad categorization of the service — replaces the full list if supplied.",
    )
    service_type: list[SlotServiceTypeInput] | None = Field(
        None, description="Appointment type(s) — replaces the full list if supplied."
    )
    specialty: list[SlotSpecialtyInput] | None = Field(
        None, description="Specialty(ies) — replaces the full list if supplied."
    )
