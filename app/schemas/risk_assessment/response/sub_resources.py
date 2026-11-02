from pydantic import BaseModel, ConfigDict, Field

from app.schemas.risk_assessment.response.codeable_concept import (
    PlainRiskAssessmentCodeableConcept,
)
from app.schemas.risk_assessment.response.reference import (
    PlainRiskAssessmentReference,
)


class RiskAssessmentReasonCodeListItem(BaseModel):
    """Sub-resource list item for RiskAssessment.reasonCode."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Internal DB ID.")
    reason_code: PlainRiskAssessmentCodeableConcept = Field(..., description="Reason code.")


class RiskAssessmentReasonCodeListResponse(BaseModel):
    """Sub-resource list response for RiskAssessment.reasonCode."""

    model_config = ConfigDict(extra="forbid")

    data: list[RiskAssessmentReasonCodeListItem] = Field(..., description="List of reason codes.")
    total: int = Field(..., description="Total count of reason codes.")


class RiskAssessmentReasonReferenceListItem(BaseModel):
    """Sub-resource list item for RiskAssessment.reasonReference."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Internal DB ID.")
    reason_reference: PlainRiskAssessmentReference = Field(..., description="Reason reference.")


class RiskAssessmentReasonReferenceListResponse(BaseModel):
    """Sub-resource list response for RiskAssessment.reasonReference."""

    model_config = ConfigDict(extra="forbid")

    data: list[RiskAssessmentReasonReferenceListItem] = Field(..., description="List of reason references.")
    total: int = Field(..., description="Total count of reason references.")


class RiskAssessmentBasisListItem(BaseModel):
    """Sub-resource list item for RiskAssessment.basis."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Internal DB ID.")
    basis: PlainRiskAssessmentReference = Field(..., description="Basis reference.")


class RiskAssessmentBasisListResponse(BaseModel):
    """Sub-resource list response for RiskAssessment.basis."""

    model_config = ConfigDict(extra="forbid")

    data: list[RiskAssessmentBasisListItem] = Field(..., description="List of basis references.")
    total: int = Field(..., description="Total count of basis references.")
