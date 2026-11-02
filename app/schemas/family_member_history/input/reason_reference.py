from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse


class FamilyMemberHistoryReasonReferenceInput(BaseModel):
    """FamilyMemberHistory.reasonReference (0..* Reference)."""

    model_config = ConfigDict(extra="forbid")

    reference: str | None = Field(
        None,
        description="Reference to resource justifying history. Reference(Condition|Observation|AllergyIntolerance|QuestionnaireResponse|DiagnosticReport|DocumentReference)",
    )
    display: str | None = Field(None, description="Plain text display for the reference.")
    identifier_use: IdentifierUse | None = Field(
        None, description="Fallback identifier — its purpose, if known."
    )
    identifier_type_system: str | None = Field(
        None, description="Fallback identifier — code system for its type."
    )
    identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type code system."
    )
    identifier_type_code: str | None = Field(
        None, description="Fallback identifier — a symbol for its type."
    )
    identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    identifier_type_user_selected: bool | None = Field(
        None, description="Fallback identifier — whether this type coding was chosen directly by the user."
    )
    identifier_type_text: str | None = Field(
        None, description="Fallback identifier — human language rendering of its type."
    )
    identifier_system: str | None = Field(
        None, description="Fallback identifier — namespace URL for the value."
    )
    identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — start of validity period."
    )
    identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — end of validity period."
    )
