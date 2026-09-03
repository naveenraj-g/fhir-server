from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .actor import ScheduleActorInput
from .identifier import ScheduleIdentifierInput
from .service_category import ScheduleServiceCategoryInput
from .service_type import ScheduleServiceTypeInput
from .specialty import ScheduleSpecialtyInput


class ScheduleCreateSchema(BaseModel):
    """Creates a Schedule and any combination of its sub-resource lists
    atomically in one request — same set-once-then-patch shape as
    Organization/Location/HealthcareService/PractitionerRole, no separate
    scalar-only vs. full create split. org_id and created_by both come from
    the verified JWT (actor.org_id / actor.sub) — neither is a request body
    field. Like Organization, Location, HealthcareService, and
    PractitionerRole, Schedule has no user_id field at all — it's a shared
    tenant-level scheduling artifact for an actor, not scoped to an
    individual end-user.

    `actor` is required with at least one entry — FHIR R4 Schedule.actor is
    1..*, unlike every other sub-resource list here (all 0..*)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "org_id": "org-456",
                "active": True,
                "comment": "Schedule for Dr. Smith — Mon/Wed/Fri mornings",
                "planning_horizon_start": "2024-01-01T08:00:00Z",
                "planning_horizon_end": "2024-12-31T12:00:00Z",
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
                "actor": [
                    {
                        "reference": "Practitioner/30001",
                        "reference_display": "Dr. Smith",
                    }
                ],
                "identifier": [],
            }
        },
    )

    active: bool | None = Field(False, description="Whether this schedule is in active use.")
    planning_horizon_start: datetime | None = Field(
        None, description="Start of the period for which slots should be provided."
    )
    planning_horizon_end: datetime | None = Field(
        None, description="End of the period for which slots should be provided."
    )
    comment: str | None = Field(
        None, description="Comments on the availability to describe any extended information."
    )

    identifier: list[ScheduleIdentifierInput] | None = Field(
        None, description="External identifiers for this item."
    )
    service_category: list[ScheduleServiceCategoryInput] | None = Field(
        None,
        description="High-level category of service being performed or considered.",
    )
    service_type: list[ScheduleServiceTypeInput] | None = Field(
        None, description="Specific service performed or considered."
    )
    specialty: list[ScheduleSpecialtyInput] | None = Field(
        None, description="Practitioner specialty needed for the appointment."
    )
    actor: list[ScheduleActorInput] = Field(
        ...,
        min_length=1,
        description="Resource(s) that this schedule is providing availability for (1..*, required).",
    )


class SchedulePatchSchema(BaseModel):
    """Partial update — only supplied fields are written. Every supplied
    sub-resource list (even `[]` for the 0..* lists) replaces the
    corresponding rows wholesale; omitted lists are left untouched.
    updated_by comes from the verified JWT (actor.sub), not a request body
    field. `actor` remains 1..* if supplied — an empty list is rejected."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "active": True,
                "comment": "Updated availability window",
            }
        },
    )

    active: bool | None = Field(None, description="Whether this schedule is in active use.")
    planning_horizon_start: datetime | None = Field(
        None, description="Start of the period for which slots should be provided."
    )
    planning_horizon_end: datetime | None = Field(
        None, description="End of the period for which slots should be provided."
    )
    comment: str | None = Field(
        None, description="Comments on the availability to describe any extended information."
    )

    identifier: list[ScheduleIdentifierInput] | None = Field(
        None, description="External identifiers — replaces the full list if supplied."
    )
    service_category: list[ScheduleServiceCategoryInput] | None = Field(
        None,
        description="High-level category of service — replaces the full list if supplied.",
    )
    service_type: list[ScheduleServiceTypeInput] | None = Field(
        None,
        description="Specific service type(s) — replaces the full list if supplied.",
    )
    specialty: list[ScheduleSpecialtyInput] | None = Field(
        None, description="Specialties needed — replaces the full list if supplied."
    )
    actor: list[ScheduleActorInput] | None = Field(
        None,
        description="Resource(s) this schedule provides availability for — replaces the full list if supplied. Must retain at least one entry (Schedule.actor is 1..*).",
    )

    @model_validator(mode="after")
    def _actor_not_emptied(self):
        if self.actor is not None and len(self.actor) < 1:
            raise ValueError(
                "actor must contain at least one entry when supplied — Schedule.actor is 1..* and cannot be emptied via PATCH"
            )
        return self
