from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.care_plan.input.activity import CarePlanActivityInput
from app.schemas.care_plan.input.codeable_concept import (
    CarePlanCodeableConceptInput,
)
from app.schemas.care_plan.input.identifier import CarePlanIdentifierInput
from app.schemas.care_plan.input.note import CarePlanNoteInput
from app.schemas.enums import CarePlanIntent, CarePlanStatus


class CarePlanCreateSchema(BaseModel):
    """Payload for POST /api/fhir/v1/care-plans.

    Tenant scoping (org_id) and created_by come from the verified JWT (actor.org_id / actor.sub).
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "status": "active",
                "intent": "plan",
                "title": "Diabetes Care Plan",
                "description": "Comprehensive diabetes management plan",
                "subject": "Patient/10001",
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "698360004",
                                "display": "Diabetes self management plan",
                            }
                        ],
                        "text": "Diabetes self management plan",
                    }
                ],
                "period_start": "2026-01-01T00:00:00Z",
                "period_end": "2026-12-31T23:59:59Z",
                "created": "2026-01-01T12:00:00Z",
                "author": "Practitioner/30001",
                "addresses": ["Condition/120001"],
                "activity": [
                    {
                        "detail": {
                            "kind": "CommunicationRequest",
                            "status": "in-progress",
                            "description": "Patient education on insulin self-administration",
                            "do_not_perform": False,
                        }
                    }
                ],
                "note": [
                    {
                        "text": "Initial plan established following diagnosis.",
                    }
                ],
            }
        },
    )

    instantiates_canonical: list[str] | None = Field(
        None, description="Instantiates FHIR protocol or definition."
    )
    instantiates_uri: list[str] | None = Field(
        None, description="Instantiates external protocol or definition."
    )
    based_on: list[str] | None = Field(
        None, description="Fulfills CarePlan, ServiceRequest, or NutritionOrder."
    )
    replaces: list[str] | None = Field(
        None, description="CarePlan replaced by this CarePlan."
    )
    part_of: list[str] | None = Field(
        None, description="Part of referenced CarePlan."
    )
    status: CarePlanStatus = Field(
        ..., description="draft | active | on-hold | revoked | completed | entered-in-error | unknown."
    )
    intent: CarePlanIntent = Field(
        ..., description="proposal | plan | order | option."
    )
    category: list[CarePlanCodeableConceptInput] | None = Field(
        None, description="Type of plan."
    )
    title: str | None = Field(
        None, description="Human-friendly name for the care plan."
    )
    description: str | None = Field(
        None, description="Summary of nature of plan."
    )
    subject: str = Field(
        ..., description="Who the care plan is for (Patient | Group) as a FHIR reference string (e.g. 'Patient/10001')."
    )
    subject_display: str | None = Field(
        None, description="Display name for subject reference."
    )
    encounter: str | None = Field(
        None, description="Encounter created as part of (Reference(Encounter))."
    )
    encounter_display: str | None = Field(
        None, description="Display name for encounter reference."
    )
    period_start: datetime | None = Field(
        None, description="Time period plan covers — start."
    )
    period_end: datetime | None = Field(
        None, description="Time period plan covers — end."
    )
    created: datetime | None = Field(
        None, description="Date record was first recorded."
    )
    author: str | None = Field(
        None, description="Who is the designated responsible party (Reference)."
    )
    author_display: str | None = Field(
        None, description="Display name for author reference."
    )
    contributor: list[str] | None = Field(
        None, description="Who provided the content of the care plan (References)."
    )
    care_team: list[str] | None = Field(
        None, description="Who's involved in plan (References)."
    )
    addresses: list[str] | None = Field(
        None, description="Health issues this plan addresses (Reference(Condition))."
    )
    goal: list[str] | None = Field(
        None, description="Desired outcome of plan (Reference(Goal))."
    )
    activity: list[CarePlanActivityInput] | None = Field(
        None, description="Action to occur as part of plan."
    )
    note: list[CarePlanNoteInput] | None = Field(
        None, description="Comments about the plan."
    )
    identifier: list[CarePlanIdentifierInput] | None = Field(
        None, description="External Ids for this plan."
    )


class CarePlanPatchSchema(BaseModel):
    """Payload for PATCH /api/fhir/v1/care-plans/{id}."""

    model_config = ConfigDict(extra="forbid")

    instantiates_canonical: list[str] | None = None
    instantiates_uri: list[str] | None = None
    based_on: list[str] | None = None
    replaces: list[str] | None = None
    part_of: list[str] | None = None
    status: CarePlanStatus | None = None
    intent: CarePlanIntent | None = None
    category: list[CarePlanCodeableConceptInput] | None = None
    title: str | None = None
    description: str | None = None
    subject: str | None = None
    subject_display: str | None = None
    encounter: str | None = None
    encounter_display: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    created: datetime | None = None
    author: str | None = None
    author_display: str | None = None
    contributor: list[str] | None = None
    care_team: list[str] | None = None
    addresses: list[str] | None = None
    goal: list[str] | None = None
    activity: list[CarePlanActivityInput] | None = None
    note: list[CarePlanNoteInput] | None = None
    identifier: list[CarePlanIdentifierInput] | None = None
