from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.care_plan.response.note import PlainCarePlanNote
from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRPeriod,
    FHIRReference,
    PlainCodingRow,
)
from app.schemas.questionnaire.response import FHIRQuantity
from app.schemas.service_request.response.core import FHIRAnnotation


class FHIRCarePlanActivityDetail(BaseModel):
    """FHIR R4 CarePlan.activity.detail."""

    model_config = ConfigDict(extra="forbid")
    kind: str | None = Field(None, description="Kind of resource.")
    instantiatesCanonical: list[str] | None = Field(None, description="Instantiates FHIR protocol.")
    instantiatesUri: list[str] | None = Field(None, description="Instantiates external protocol.")
    code: FHIRCodeableConcept | None = Field(None, description="Detail type of activity.")
    reasonCode: list[FHIRCodeableConcept] | None = Field(None, description="Why activity should be done.")
    reasonReference: list[FHIRReference] | None = Field(None, description="Why activity is needed.")
    goal: list[FHIRReference] | None = Field(None, description="Goals activity will contribute towards.")
    status: str = Field(..., description="Activity status code.")
    statusReason: FHIRCodeableConcept | None = Field(None, description="Reason for current status.")
    doNotPerform: bool | None = Field(None, description="If true, activity is to prohibit action.")
    scheduledTiming: dict[str, Any] | None = Field(None, description="When activity is to occur (Timing).")
    scheduledPeriod: FHIRPeriod | None = Field(None, description="When activity is to occur (Period).")
    scheduledString: str | None = Field(None, description="When activity is to occur (string).")
    location: FHIRReference | None = Field(None, description="Where it should happen.")
    performer: list[FHIRReference] | None = Field(None, description="Who will be responsible.")
    productCodeableConcept: FHIRCodeableConcept | None = Field(None, description="Product (CodeableConcept).")
    productReference: FHIRReference | None = Field(None, description="Product (Reference).")
    dailyAmount: FHIRQuantity | None = Field(None, description="Daily amount.")
    quantity: FHIRQuantity | None = Field(None, description="Quantity.")
    description: str | None = Field(None, description="Extra info describing activity.")


class FHIRCarePlanActivity(BaseModel):
    """FHIR R4 CarePlan.activity."""

    model_config = ConfigDict(extra="forbid")
    outcomeCodeableConcept: list[FHIRCodeableConcept] | None = Field(None, description="Results of the activity.")
    outcomeReference: list[FHIRReference] | None = Field(None, description="Appointment, Encounter, Procedure, etc.")
    progress: list[FHIRAnnotation] | None = Field(None, description="Comments about the activity status/progress.")
    reference: FHIRReference | None = Field(None, description="Activity details defined in specific resource.")
    detail: FHIRCarePlanActivityDetail | None = Field(None, description="In-line definition of activity.")


class PlainCarePlanActivityDetail(BaseModel):
    """Plain response shape for CarePlan.activity.detail."""

    model_config = ConfigDict(extra="allow")
    kind: str | None = None
    instantiates_canonical: list[str] | None = None
    instantiates_uri: list[str] | None = None
    code_text: str | None = None
    code_codings: list[PlainCodingRow] | None = None
    reason_codes: list[dict[str, Any]] | None = None
    reason_references: list[dict[str, Any]] | None = None
    goals: list[dict[str, Any]] | None = None
    status: str | None = None
    status_reason_text: str | None = None
    status_reason_codings: list[PlainCodingRow] | None = None
    do_not_perform: bool | None = None
    scheduled_timing: dict[str, Any] | None = None
    scheduled_period_start: str | None = None
    scheduled_period_end: str | None = None
    scheduled_string: str | None = None
    location_id: int | None = None
    location_type: str | None = None
    location_reference: str | None = None
    location_display: str | None = None
    performers: list[dict[str, Any]] | None = None
    product_codeable_concept_text: str | None = None
    product_codings: list[PlainCodingRow] | None = None
    product_id: int | None = None
    product_type: str | None = None
    product_reference: str | None = None
    product_display: str | None = None
    daily_amount_value: float | None = None
    daily_amount_comparator: str | None = None
    daily_amount_unit: str | None = None
    daily_amount_system: str | None = None
    daily_amount_code: str | None = None
    quantity_value: float | None = None
    quantity_comparator: str | None = None
    quantity_unit: str | None = None
    quantity_system: str | None = None
    quantity_code: str | None = None
    description: str | None = None


class PlainCarePlanActivity(BaseModel):
    """Plain response shape for CarePlan.activity."""

    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Internal DB ID.")
    reference_id: int | None = None
    reference_type: str | None = None
    reference_reference: str | None = None
    reference_display: str | None = None
    outcome_codeable_concepts: list[dict[str, Any]] | None = None
    outcome_references: list[dict[str, Any]] | None = None
    progress: list[PlainCarePlanNote] | None = None
    detail: PlainCarePlanActivityDetail | None = None
