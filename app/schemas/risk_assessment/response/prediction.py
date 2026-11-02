from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRPeriod,
    FHIRRange,
)
from app.schemas.risk_assessment.response.codeable_concept import (
    PlainRiskAssessmentCodeableConcept,
)


class FHIRRiskAssessmentPrediction(BaseModel):
    """FHIR R4 RiskAssessment.prediction element."""

    model_config = ConfigDict(extra="forbid")

    outcome: FHIRCodeableConcept | None = Field(None, description="Possible outcome targeted.")
    probabilityDecimal: float | None = Field(
        None, description="Likelihood of specified outcome as a decimal."
    )
    probabilityRange: FHIRRange | None = Field(
        None, description="Likelihood of specified outcome as a Range."
    )
    qualitativeRisk: FHIRCodeableConcept | None = Field(
        None, description="Likelihood of specified outcome as a qualitative rating."
    )
    relativeRisk: float | None = Field(None, description="Relative likelihood.")
    whenPeriod: FHIRPeriod | None = Field(None, description="Timeframe of prediction as a Period.")
    whenRange: FHIRRange | None = Field(None, description="Timeframe of prediction as a Range.")
    rationale: str | None = Field(None, description="Explanation of prediction.")


class PlainRiskAssessmentPrediction(BaseModel):
    """Plain snake_case RiskAssessment.prediction element."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Internal DB ID.")
    outcome: PlainRiskAssessmentCodeableConcept | None = Field(
        None, description="Possible outcome targeted."
    )
    probability_decimal: float | None = Field(
        None, description="Likelihood of specified outcome as a decimal."
    )
    probability_range: FHIRRange | None = Field(
        None, description="Likelihood of specified outcome as a Range."
    )
    qualitative_risk: PlainRiskAssessmentCodeableConcept | None = Field(
        None, description="Likelihood of specified outcome as a qualitative rating."
    )
    relative_risk: float | None = Field(None, description="Relative likelihood.")
    when_period_start: datetime | None = Field(None, description="Period start.")
    when_period_end: datetime | None = Field(None, description="Period end.")
    when_range: FHIRRange | None = Field(None, description="Timeframe of prediction as a Range.")
    rationale: str | None = Field(None, description="Explanation of prediction.")


class RiskAssessmentPredictionListItem(PlainRiskAssessmentPrediction):
    """Sub-resource list item for RiskAssessment prediction."""


class RiskAssessmentPredictionListResponse(BaseModel):
    """Sub-resource list response for RiskAssessment predictions."""

    model_config = ConfigDict(extra="forbid")

    data: list[RiskAssessmentPredictionListItem] = Field(..., description="List of predictions.")
    total: int = Field(..., description="Total count of predictions.")
