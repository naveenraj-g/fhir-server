from pydantic import BaseModel, ConfigDict, Field

from .codeable_concept import PlainClinicalImpressionCodeableConcept
from .reference import PlainClinicalImpressionReference


class ClinicalImpressionProblemListItem(PlainClinicalImpressionReference):
    """Sub-resource list item for problem."""


class ClinicalImpressionProblemListResponse(BaseModel):
    """Sub-resource list response for problems."""

    model_config = ConfigDict(extra="forbid")

    data: list[ClinicalImpressionProblemListItem] = Field(..., description="List of problems.")
    total: int = Field(..., description="Total count.")


class ClinicalImpressionProtocolListItem(BaseModel):
    """Sub-resource list item for protocol."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Internal DB ID.")
    uri: str = Field(..., description="Protocol URI.")


class ClinicalImpressionProtocolListResponse(BaseModel):
    """Sub-resource list response for protocols."""

    model_config = ConfigDict(extra="forbid")

    data: list[ClinicalImpressionProtocolListItem] = Field(..., description="List of protocols.")
    total: int = Field(..., description="Total count.")


class ClinicalImpressionPrognosisCodeableConceptListItem(PlainClinicalImpressionCodeableConcept):
    """Sub-resource list item for prognosisCodeableConcept."""

    id: int = Field(..., description="Internal DB ID.")


class ClinicalImpressionPrognosisCodeableConceptListResponse(BaseModel):
    """Sub-resource list response for prognosisCodeableConcepts."""

    model_config = ConfigDict(extra="forbid")

    data: list[ClinicalImpressionPrognosisCodeableConceptListItem] = Field(
        ..., description="List of prognosis codeable concepts."
    )
    total: int = Field(..., description="Total count.")


class ClinicalImpressionPrognosisReferenceListItem(PlainClinicalImpressionReference):
    """Sub-resource list item for prognosisReference."""


class ClinicalImpressionPrognosisReferenceListResponse(BaseModel):
    """Sub-resource list response for prognosisReferences."""

    model_config = ConfigDict(extra="forbid")

    data: list[ClinicalImpressionPrognosisReferenceListItem] = Field(
        ..., description="List of prognosis references."
    )
    total: int = Field(..., description="Total count.")


class ClinicalImpressionSupportingInfoListItem(PlainClinicalImpressionReference):
    """Sub-resource list item for supportingInfo."""


class ClinicalImpressionSupportingInfoListResponse(BaseModel):
    """Sub-resource list response for supportingInfo."""

    model_config = ConfigDict(extra="forbid")

    data: list[ClinicalImpressionSupportingInfoListItem] = Field(
        ..., description="List of supportingInfo references."
    )
    total: int = Field(..., description="Total count.")
