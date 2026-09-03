from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.slot.enums import SlotStatus
from app.schemas.enums import IdentifierUse

from .identifier import SlotIdentifierInput
from .service_category import SlotServiceCategoryInput
from .service_type import SlotServiceTypeInput
from .specialty import SlotSpecialtyInput


class SlotCreateSchema(BaseModel):
    """Creates a Slot and any combination of its sub-resource lists
    atomically in one request — same set-once-then-patch shape as
    Organization/Location/HealthcareService/PractitionerRole/Schedule, no
    separate scalar-only vs. full create split. org_id and created_by both
    come from the verified JWT (actor.org_id / actor.sub) — neither is a
    request body field. Like Organization, Location, HealthcareService, and
    Schedule, Slot has no user_id field at all — it's a shared tenant-level
    scheduling artifact, not scoped to an individual end-user.

    `schedule` is required — FHIR R4 Slot.schedule is 1..1, unlike
    HealthcareService.providedBy (0..1) or Schedule.actor (1..*). `status`,
    `start`, and `end` are likewise required (1..1)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "org_id": "org-456",
                "schedule": "Schedule/200001",
                "status": "free",
                "start": "2024-06-01T09:00:00Z",
                "end": "2024-06-01T09:30:00Z",
                "overbooked": False,
                "comment": "Morning slot — first appointment of the day",
                "appointment_type_system": "http://terminology.hl7.org/CodeSystem/v2-0276",
                "appointment_type_code": "ROUTINE",
                "appointment_type_display": "Routine appointment",
                "service_category": [
                    {
                        "coding_system": "http://example.org/service-category",
                        "coding_code": "17",
                        "coding_display": "General Practice",
                    }
                ],
                "service_type": [
                    {"coding_code": "57", "coding_display": "Immunization"}
                ],
                "specialty": [
                    {
                        "coding_system": "http://snomed.info/sct",
                        "coding_code": "394814009",
                        "coding_display": "General practice",
                    }
                ],
                "identifier": [],
            }
        },
    )

    schedule: str = Field(
        ...,
        description=(
            "Reference to the Schedule this slot belongs to, e.g. "
            "'Schedule/200001' (1..1, required) — rejected with 422 if it "
            "doesn't resolve to an existing Schedule in this org."
        ),
    )
    schedule_display: str | None = Field(
        None, description="Plain text narrative that identifies the schedule in addition to the reference."
    )
    schedule_identifier_use: IdentifierUse | None = Field(
        None,
        description="Logical-identifier fallback for the schedule (used when it isn't a resource in this system) — identifies the purpose for that identifier, if known.",
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

    status: SlotStatus = Field(
        ...,
        description="busy | free | busy-unavailable | busy-tentative | entered-in-error.",
    )
    start: datetime = Field(..., description="Date/Time the slot begins (1..1, required).")
    end: datetime = Field(..., description="Date/Time the slot concludes (1..1, required).")
    overbooked: bool | None = Field(
        None, description="This slot has already been overbooked."
    )
    comment: str | None = Field(
        None,
        description="Comments on the slot to describe any extended information.",
    )

    appointment_type_system: str | None = Field(
        None,
        description="The style of appointment or patient that has been booked in the slot (not service type) — code system.",
    )
    appointment_type_version: str | None = Field(
        None, description="The version of the code system used for appointmentType."
    )
    appointment_type_code: str | None = Field(
        None, description="A symbol in syntax defined by the code system."
    )
    appointment_type_display: str | None = Field(
        None, description="A representation of the meaning of the code in the system."
    )
    appointment_type_text: str | None = Field(
        None,
        description="A human language representation of the appointment type.",
    )
    appointment_type_user_selected: bool | None = Field(
        None, description="Indicates that this coding was chosen by a user directly."
    )

    identifier: list[SlotIdentifierInput] | None = Field(
        None, description="External identifiers for this item."
    )
    service_category: list[SlotServiceCategoryInput] | None = Field(
        None,
        description="A broad categorization of the service that is to be performed during this appointment.",
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
    sub-resource list replaces the corresponding rows wholesale; omitted
    lists are left untouched. updated_by comes from the verified JWT
    (actor.sub), not a request body field. The `schedule` reference cannot be
    changed via PATCH — delete and re-create the Slot to correct it."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "status": "busy",
                "comment": "Updated availability window",
            }
        },
    )

    status: SlotStatus | None = Field(
        None,
        description="busy | free | busy-unavailable | busy-tentative | entered-in-error.",
    )
    start: datetime | None = Field(None, description="Date/Time the slot begins.")
    end: datetime | None = Field(None, description="Date/Time the slot concludes.")
    overbooked: bool | None = Field(
        None, description="This slot has already been overbooked."
    )
    comment: str | None = Field(
        None,
        description="Comments on the slot to describe any extended information.",
    )

    appointment_type_system: str | None = Field(None, description="Code system for appointmentType.")
    appointment_type_version: str | None = Field(None, description="Version of the code system used for appointmentType.")
    appointment_type_code: str | None = Field(None, description="A symbol in syntax defined by the code system.")
    appointment_type_display: str | None = Field(None, description="A representation of the meaning of the code in the system.")
    appointment_type_text: str | None = Field(None, description="A human language representation of the appointment type.")
    appointment_type_user_selected: bool | None = Field(None, description="Indicates that this coding was chosen by a user directly.")

    identifier: list[SlotIdentifierInput] | None = Field(
        None, description="External identifiers — replaces the full list if supplied."
    )
    service_category: list[SlotServiceCategoryInput] | None = Field(
        None,
        description="High-level category of service — replaces the full list if supplied.",
    )
    service_type: list[SlotServiceTypeInput] | None = Field(
        None,
        description="Specific service type(s) — replaces the full list if supplied.",
    )
    specialty: list[SlotSpecialtyInput] | None = Field(
        None, description="Specialties needed — replaces the full list if supplied."
    )
