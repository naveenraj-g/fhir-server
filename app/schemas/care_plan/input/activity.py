from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.care_plan.input.codeable_concept import (
    CarePlanCodeableConceptInput,
)
from app.schemas.care_plan.input.note import CarePlanNoteInput
from app.schemas.care_plan.input.quantity import CarePlanQuantityInput
from app.schemas.enums import CarePlanActivityKind, CarePlanActivityStatus


class CarePlanActivityDetailInput(BaseModel):
    """In-line definition of activity in CarePlan."""

    model_config = ConfigDict(extra="forbid")
    kind: CarePlanActivityKind | None = Field(
        None, description="Appointment | CommunicationRequest | DeviceRequest | MedicationRequest | NutritionOrder | Task | ServiceRequest | VisionPrescription"
    )
    instantiates_canonical: list[str] | None = Field(
        None, description="Instantiates FHIR protocol or definition."
    )
    instantiates_uri: list[str] | None = Field(
        None, description="Instantiates external protocol or definition."
    )
    code: CarePlanCodeableConceptInput | None = Field(
        None, description="Detail type of activity."
    )
    reason_code: list[CarePlanCodeableConceptInput] | None = Field(
        None, description="Why activity should be done or why activity was prohibited."
    )
    reason_reference: list[str] | None = Field(
        None, description="Why activity is needed (references)."
    )
    goal: list[str] | None = Field(
        None, description="Goals this activity will contribute towards."
    )
    status: CarePlanActivityStatus | None = Field(
        None, description="not-started | scheduled | in-progress | on-hold | completed | cancelled | stopped | unknown | entered-in-error."
    )
    status_reason: CarePlanCodeableConceptInput | None = Field(
        None, description="Reason for current status."
    )
    do_not_perform: bool | None = Field(
        None, description="If true, activity is to prohibit action."
    )
    scheduled_timing: dict[str, Any] | None = Field(
        None, description="When activity is to occur (Timing)."
    )
    scheduled_period_start: datetime | None = Field(
        None, description="When activity is to occur: Period start."
    )
    scheduled_period_end: datetime | None = Field(
        None, description="When activity is to occur: Period end."
    )
    scheduled_string: str | None = Field(
        None, description="When activity is to occur: text representation."
    )
    location: str | None = Field(
        None, description="Where it should happen (Reference(Location))."
    )
    location_display: str | None = Field(
        None, description="Display name for location reference."
    )
    performer: list[str] | None = Field(
        None, description="Who will be responsible (References)."
    )
    product_codeable_concept: CarePlanCodeableConceptInput | None = Field(
        None, description="What is to be administered/supplied (CodeableConcept)."
    )
    product_reference: str | None = Field(
        None, description="What is to be administered/supplied (Reference(Medication | Substance))."
    )
    product_display: str | None = Field(
        None, description="Display name for product reference."
    )
    daily_amount: CarePlanQuantityInput | None = Field(
        None, description="How to consume/day."
    )
    quantity: CarePlanQuantityInput | None = Field(
        None, description="How much to administer/supply/consume."
    )
    description: str | None = Field(
        None, description="Extra info describing activity to perform."
    )


class CarePlanActivityInput(BaseModel):
    """Action to occur as part of plan."""

    model_config = ConfigDict(extra="forbid")
    outcome_codeable_concept: list[CarePlanCodeableConceptInput] | None = Field(
        None, description="Results of the activity (e.g. met, partially met, not met)."
    )
    outcome_reference: list[str] | None = Field(
        None, description="Appointment, Encounter, Procedure, etc."
    )
    progress: list[CarePlanNoteInput] | None = Field(
        None, description="Comments about the activity status/progress."
    )
    reference: str | None = Field(
        None, description="Activity details defined in specific resource (Reference)."
    )
    reference_display: str | None = Field(
        None, description="Display name for reference."
    )
    detail: CarePlanActivityDetailInput | None = Field(
        None, description="In-line definition of activity."
    )
