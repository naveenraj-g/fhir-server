from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import PlainCodingRow
from app.schemas.immunization_evaluation.response.identifier import (
    PlainImmunizationEvaluationIdentifier,
)


class PlainImmunizationEvaluationDoseStatusReason(BaseModel):
    """Plain snake_case dose status reason response element."""

    model_config = ConfigDict(extra="forbid")

    id: int | None = Field(None, description="Record ID.")
    text: str | None = Field(None, description="Plain text representation.")
    coding: list[PlainCodingRow] | None = Field(None, description="Reason codings.")


class ImmunizationEvaluationIdentifierListItem(PlainImmunizationEvaluationIdentifier):
    """Sub-resource list item for identifier."""


class ImmunizationEvaluationIdentifierListResponse(BaseModel):
    """Sub-resource list response for identifiers."""

    model_config = ConfigDict(extra="forbid")

    data: list[ImmunizationEvaluationIdentifierListItem] = Field(
        ..., description="List of identifiers."
    )
    total: int = Field(..., description="Total count.")


class ImmunizationEvaluationDoseStatusReasonListItem(
    PlainImmunizationEvaluationDoseStatusReason
):
    """Sub-resource list item for dose status reason."""


class ImmunizationEvaluationDoseStatusReasonListResponse(BaseModel):
    """Sub-resource list response for dose status reasons."""

    model_config = ConfigDict(extra="forbid")

    data: list[ImmunizationEvaluationDoseStatusReasonListItem] = Field(
        ..., description="List of dose status reasons."
    )
    total: int = Field(..., description="Total count.")
