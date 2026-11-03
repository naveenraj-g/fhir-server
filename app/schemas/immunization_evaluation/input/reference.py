from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.enums import IdentifierUse


class _SingleReferenceInput(BaseModel):
    """Shared Reference input shape for ImmunizationEvaluation references."""

    model_config = ConfigDict(extra="forbid")

    reference: str | None = Field(
        None, description="FHIR reference string, e.g. 'Patient/10001'."
    )
    reference_display: str | None = Field(
        None, description="Plain text narrative identifying the target."
    )
    reference_identifier_use: IdentifierUse | None = Field(
        None, description="Fallback identifier — its purpose, if known."
    )
    reference_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — code system for its type."
    )
    reference_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type code system."
    )
    reference_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — a symbol for its type."
    )
    reference_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    reference_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — human language rendering of its type."
    )
    reference_identifier_type_user_selected: bool | None = Field(
        None, description="Fallback identifier — whether its type was user-selected."
    )
    reference_identifier_system: str | None = Field(
        None, description="Fallback identifier — namespace URL for the value."
    )
    reference_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    reference_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — start of validity period."
    )
    reference_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — end of validity period."
    )

    @model_validator(mode="before")
    @classmethod
    def _coerce_from_str(cls, data: Any) -> Any:
        if isinstance(data, str):
            return {"reference": data}
        return data


class ImmunizationEvaluationPatientInput(_SingleReferenceInput):
    """patient — Reference(Patient)."""


class ImmunizationEvaluationAuthorityInput(_SingleReferenceInput):
    """authority — Reference(Organization)."""


class ImmunizationEvaluationImmunizationEventInput(_SingleReferenceInput):
    """immunizationEvent — Reference(Immunization)."""
