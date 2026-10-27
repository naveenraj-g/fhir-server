from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from .actor import ScheduleActorInput
from .identifier import ScheduleIdentifierInput
from .service_category import ScheduleServiceCategoryInput
from .service_type import ScheduleServiceTypeInput
from .specialty import ScheduleSpecialtyInput


class ScheduleCreateSchema(BaseModel):
    """Creates a Schedule and any combination of its 5 sub-resource lists
    atomically in one request — same set-once-then-patch shape as
    Organization/HealthcareService/PractitionerRole, no separate scalar-only
    vs. full create split. org_id and created_by both come from the
    verified JWT (actor.org_id / actor.sub) — neither is a request body
    field. Like Organization/Location/HealthcareService/PractitionerRole,
    Schedule has no user_id field at all — it's a shared tenant-level
    entity (a container of bookable time), not scoped to an individual
    end-user."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "active": True,
                "planning_horizon_start": "2026-01-01T00:00:00Z",
                "planning_horizon_end": "2026-12-31T23:59:59Z",
                "comment": "General practice bookings only",
                "identifier": [],
                "service_category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/service-category",
                                "code": "17",
                                "display": "General Practice",
                            }
                        ]
                    }
                ],
                "service_type": [{"coding": [{"code": "57", "display": "Immunization"}]}],
                "specialty": [
                    {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "394814009",
                                "display": "General practice",
                            }
                        ]
                    }
                ],
                "actor": [
                    {
                        "reference": "Practitioner/30001",
                        "reference_display": "Dr. Jane Smith",
                    }
                ],
            }
        },
    )

    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries. Not yet validated against registered extension definitions.",
    )
    active: bool | None = Field(
        None, description="Whether this schedule record is in active use."
    )

    planning_horizon_start: datetime | None = Field(
        None,
        description="Start of the period of time covered by this schedule's slots.",
    )
    planning_horizon_end: datetime | None = Field(
        None,
        description="End of the period of time covered by this schedule's slots.",
    )

    comment: str | None = Field(
        None,
        description="Comments on the availability to describe any extended information, such as custom constraints.",
    )

    identifier: list[ScheduleIdentifierInput] | None = Field(
        None, description="External identifiers for this item."
    )
    service_category: list[ScheduleServiceCategoryInput] | None = Field(
        None,
        description="A high-level category of service(s) that could be provided using this schedule.",
    )
    service_type: list[ScheduleServiceTypeInput] | None = Field(
        None,
        description="The specific service(s) that could be provided using this schedule.",
    )
    specialty: list[ScheduleSpecialtyInput] | None = Field(
        None,
        description="The specialty of a practitioner that would be required to perform the service requested in this schedule.",
    )
    actor: list[ScheduleActorInput] | None = Field(
        None,
        description="The resource(s) this schedule resource is for (Patient, Practitioner, PractitionerRole, RelatedPerson, Device, HealthcareService, or Location).",
    )


class SchedulePatchSchema(BaseModel):
    """Partial update — only supplied fields are written. Every supplied
    sub-resource list (even `[]`) replaces the corresponding rows wholesale;
    omitted lists are left untouched. updated_by comes from the verified
    JWT (actor.sub), not a request body field."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "active": False,
                "comment": "Temporarily closed for renovations",
            }
        },
    )

    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries — replaces the full list if supplied.",
    )
    active: bool | None = Field(
        None, description="Whether this schedule record is in active use."
    )

    planning_horizon_start: datetime | None = Field(
        None,
        description="Start of the period of time covered by this schedule's slots.",
    )
    planning_horizon_end: datetime | None = Field(
        None,
        description="End of the period of time covered by this schedule's slots.",
    )

    comment: str | None = Field(
        None, description="Comments on the availability."
    )

    identifier: list[ScheduleIdentifierInput] | None = Field(
        None, description="External identifiers — replaces the full list if supplied."
    )
    service_category: list[ScheduleServiceCategoryInput] | None = Field(
        None,
        description="High-level service category(ies) — replaces the full list if supplied.",
    )
    service_type: list[ScheduleServiceTypeInput] | None = Field(
        None, description="Specific service type(s) — replaces the full list if supplied."
    )
    specialty: list[ScheduleSpecialtyInput] | None = Field(
        None, description="Specialty(ies) — replaces the full list if supplied."
    )
    actor: list[ScheduleActorInput] | None = Field(
        None, description="Actor(s) — replaces the full list if supplied."
    )
