from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.risk_assessment.input.codeable_concept import (
    RiskAssessmentCodeableConceptInput,
)


class QuantityInput(BaseModel):
    """FHIR Quantity input."""

    model_config = ConfigDict(extra="forbid")

    value: float | None = Field(None, description="Numerical value (with implicit precision).")
    comparator: str | None = Field(None, description="< | <= | >= | > - how to understand the value.")
    unit: str | None = Field(None, description="Unit representation.")
    system: str | None = Field(None, description="System that defines coded unit form.")
    code: str | None = Field(None, description="Coded form of the unit.")


class RangeInput(BaseModel):
    """FHIR Range input."""

    model_config = ConfigDict(extra="forbid")

    low: QuantityInput | None = Field(None, description="Low limit.")
    high: QuantityInput | None = Field(None, description="High limit.")


class PeriodInput(BaseModel):
    """FHIR Period input."""

    model_config = ConfigDict(extra="forbid")

    start: datetime | None = Field(None, description="Starting time with inclusive boundary.")
    end: datetime | None = Field(None, description="End time with inclusive boundary, if not ongoing.")


class RiskAssessmentPredictionInput(BaseModel):
    """FHIR R4 RiskAssessment.prediction input."""

    model_config = ConfigDict(extra="forbid")

    outcome: RiskAssessmentCodeableConceptInput | None = Field(
        None, description="Possible outcome targeted."
    )
    probability_decimal: float | None = Field(
        None, description="Likelihood of specified outcome as a decimal (between 0 and 1)."
    )
    probability_range: RangeInput | None = Field(
        None, description="Likelihood of specified outcome as a Range."
    )
    qualitative_risk: RiskAssessmentCodeableConceptInput | None = Field(
        None, description="Likelihood of specified outcome as a qualitative rating."
    )
    relative_risk: float | None = Field(
        None, description="Relative likelihood."
    )
    when_period: PeriodInput | None = Field(
        None, description="Timeframe of prediction as a Period."
    )
    when_range: RangeInput | None = Field(
        None, description="Timeframe of prediction as a Range."
    )
    rationale: str | None = Field(
        None, description="Explanation of prediction."
    )
