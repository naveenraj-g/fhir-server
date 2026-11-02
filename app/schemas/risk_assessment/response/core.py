from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
)
from app.schemas.risk_assessment.response.codeable_concept import (
    PlainRiskAssessmentCodeableConcept,
)
from app.schemas.risk_assessment.response.identifier import (
    PlainRiskAssessmentIdentifier,
)
from app.schemas.risk_assessment.response.note import (
    PlainRiskAssessmentNote,
)
from app.schemas.risk_assessment.response.prediction import (
    FHIRRiskAssessmentPrediction,
    PlainRiskAssessmentPrediction,
)
from app.schemas.risk_assessment.response.reference import (
    PlainRiskAssessmentReference,
)


class FHIRAnnotation(BaseModel):
    """FHIR R4 Annotation datatype."""

    model_config = ConfigDict(extra="forbid")

    authorString: str | None = Field(None, description="Individual responsible for the annotation.")
    authorReference: FHIRReference | None = Field(None, description="Individual responsible for the annotation.")
    time: str | None = Field(None, description="When the annotation was made.")
    text: str = Field(..., description="The annotation  — text content (as markdown).")


class FHIRRiskAssessmentSchema(BaseModel):
    """FHIR R4 RiskAssessment resource schema."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["RiskAssessment"] = "RiskAssessment"
    id: str = Field(..., description="Logical id of this artifact.")
    meta: FHIRMeta | None = Field(None, description="Metadata about the resource.")
    extension: list[dict[str, Any]] | None = Field(
        None, description="Additional content defined by implementations."
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Unique identifier for the assessment."
    )
    basedOn: FHIRReference | None = Field(
        None, description="Request fulfilled by this assessment."
    )
    parent: FHIRReference | None = Field(
        None, description="Part of this occurrence."
    )
    status: str = Field(
        ...,
        description="registered | preliminary | final | amended | corrected | cancelled | entered-in-error | unknown.",
    )
    method: FHIRCodeableConcept | None = Field(
        None, description="Evaluation mechanism."
    )
    code: FHIRCodeableConcept | None = Field(
        None, description="Type of assessment."
    )
    subject: FHIRReference = Field(
        ..., description="Who/what does assessment apply to?"
    )
    encounter: FHIRReference | None = Field(
        None, description="Where was assessment performed?"
    )
    occurrenceDateTime: str | None = Field(
        None, description="When was assessment made?"
    )
    occurrencePeriod: FHIRPeriod | None = Field(
        None, description="When was assessment made?"
    )
    condition: FHIRReference | None = Field(
        None, description="Condition assessed."
    )
    performer: FHIRReference | None = Field(
        None, description="Who did assessment?"
    )
    reasonCode: list[FHIRCodeableConcept] | None = Field(
        None, description="Why the assessment was necessary (concept)."
    )
    reasonReference: list[FHIRReference] | None = Field(
        None, description="Why the assessment was necessary (reference)."
    )
    basis: list[FHIRReference] | None = Field(
        None, description="Information used in assessment."
    )
    prediction: list[FHIRRiskAssessmentPrediction] | None = Field(
        None, description="Outcome predicted."
    )
    mitigation: str | None = Field(
        None, description="How to reduce risk."
    )
    note: list[FHIRAnnotation] | None = Field(
        None, description="Comments made about the risk assessment."
    )


class PlainRiskAssessmentResponse(BaseModel):
    """Plain snake_case RiskAssessment response schema."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Public sequence identifier.")
    status: str = Field(..., description="Risk assessment status.")
    method: PlainRiskAssessmentCodeableConcept | None = Field(
        None, description="Evaluation mechanism."
    )
    code: PlainRiskAssessmentCodeableConcept | None = Field(
        None, description="Type of assessment."
    )
    subject: PlainRiskAssessmentReference = Field(
        ..., description="Subject of the risk assessment."
    )
    based_on: PlainRiskAssessmentReference | None = Field(
        None, description="Request fulfilled by this assessment."
    )
    parent: PlainRiskAssessmentReference | None = Field(
        None, description="Part of this occurrence."
    )
    encounter: PlainRiskAssessmentReference | None = Field(
        None, description="Encounter where assessment was made."
    )
    occurrence_date_time: datetime | None = Field(
        None, description="When was assessment made? (dateTime)."
    )
    occurrence_period_start: datetime | None = Field(
        None, description="When was assessment made? (Period start)."
    )
    occurrence_period_end: datetime | None = Field(
        None, description="When was assessment made? (Period end)."
    )
    condition: PlainRiskAssessmentReference | None = Field(
        None, description="Condition assessed."
    )
    performer: PlainRiskAssessmentReference | None = Field(
        None, description="Who did assessment?"
    )
    reason_code: list[PlainRiskAssessmentCodeableConcept] | None = Field(
        None, description="Reason code."
    )
    reason_reference: list[PlainRiskAssessmentReference] | None = Field(
        None, description="Reason reference."
    )
    basis: list[PlainRiskAssessmentReference] | None = Field(
        None, description="Information used in assessment."
    )
    prediction: list[PlainRiskAssessmentPrediction] | None = Field(
        None, description="Predictions."
    )
    mitigation: str | None = Field(
        None, description="How to reduce risk."
    )
    note: list[PlainRiskAssessmentNote] | None = Field(
        None, description="Notes."
    )
    identifier: list[PlainRiskAssessmentIdentifier] | None = Field(
        None, description="Identifiers."
    )
    extension: list[dict[str, Any]] | None = Field(
        None, description="Extensions."
    )
    created_at: datetime | None = Field(None, description="Creation timestamp.")
    updated_at: datetime | None = Field(None, description="Last update timestamp.")
    created_by: str | None = Field(None, description="Created by actor sub.")
    updated_by: str | None = Field(None, description="Updated by actor sub.")


class PaginatedRiskAssessmentResponse(BaseModel):
    """Paginated plain snake_case RiskAssessment list response."""

    model_config = ConfigDict(extra="forbid")

    total: int = Field(..., description="Total matching items.")
    limit: int = Field(..., description="Requested page size.")
    offset: int = Field(..., description="Requested page offset.")
    data: list[PlainRiskAssessmentResponse] = Field(..., description="Page of resources.")


class FHIRRiskAssessmentBundleEntry(BaseModel):
    """Entry in a FHIR RiskAssessment searchset Bundle."""

    model_config = ConfigDict(extra="forbid")

    fullUrl: str | None = Field(None, description="Absolute URL for the resource.")
    resource: FHIRRiskAssessmentSchema = Field(..., description="RiskAssessment resource.")


class FHIRRiskAssessmentBundle(BaseModel):
    """FHIR R4 searchset Bundle of RiskAssessment resources."""

    model_config = ConfigDict(extra="forbid")

    resourceType: Literal["Bundle"] = "Bundle"
    type: str = Field("searchset", description="Bundle type.")
    total: int = Field(..., description="Total matching items.")
    entry: list[FHIRRiskAssessmentBundleEntry] = Field(
        default_factory=list, description="Page of entries."
    )
