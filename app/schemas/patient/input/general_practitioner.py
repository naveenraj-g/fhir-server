from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import IdentifierUse
from app.models.patient.enums import PatientGeneralPractitionerType


class GeneralPractitionerCreate(BaseModel):
    """FHIR R4 Patient.generalPractitioner — a reference to the patient's nominated
    primary care provider."""

    model_config = ConfigDict(extra="forbid")
    reference_type: PatientGeneralPractitionerType | None = Field(
        None,
        description="Resource type of the referenced practitioner. Organization|Practitioner|PractitionerRole. "
        "Required together with reference_id unless reference_identifier_system/_value is given instead.",
    )
    reference_id: int | None = Field(
        None,
        description="Public id of the referenced Organization/Practitioner/PractitionerRole.",
    )
    reference_display: str | None = Field(
        None, description="Display text for the referenced resource."
    )
    reference_identifier_use: IdentifierUse | None = Field(
        None,
        description="Fallback identifier (used when the referenced resource isn't "
        "in this system) — usual|official|temp|secondary|old.",
    )
    reference_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — coding system for its type."
    )
    reference_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type coding system."
    )
    reference_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type (e.g. MR, SS)."
    )
    reference_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    reference_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — plain-text rendering of its type."
    )
    reference_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was user-selected.",
    )
    reference_identifier_system: str | None = Field(
        None, description="Fallback identifier — URI namespace."
    )
    reference_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    reference_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — when it became valid."
    )
    reference_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — when it stopped being valid."
    )

    @model_validator(mode="after")
    def _require_reference_or_identifier(self):
        has_reference = (
            self.reference_type is not None and self.reference_id is not None
        )
        has_identifier = (
            self.reference_identifier_system is not None
            and self.reference_identifier_value is not None
        )
        if not has_reference and not has_identifier:
            raise ValueError(
                "Provide either reference_type+reference_id or "
                "reference_identifier_system+reference_identifier_value."
            )
        return self


class GeneralPractitionerPatch(BaseModel):
    """Partial update to a general-practitioner reference — only supplied fields are written."""

    model_config = ConfigDict(extra="forbid")
    reference_type: PatientGeneralPractitionerType | None = Field(
        None, description="Organization|Practitioner|PractitionerRole."
    )
    reference_id: int | None = Field(
        None, description="Public id of the referenced resource."
    )
    reference_display: str | None = Field(
        None, description="Display text for the referenced resource."
    )
    reference_identifier_use: IdentifierUse | None = Field(
        None,
        description="Fallback identifier (used when the referenced resource isn't "
        "in this system) — usual|official|temp|secondary|old.",
    )
    reference_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — coding system for its type."
    )
    reference_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type coding system."
    )
    reference_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type (e.g. MR, SS)."
    )
    reference_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    reference_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — plain-text rendering of its type."
    )
    reference_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was user-selected.",
    )
    reference_identifier_system: str | None = Field(
        None, description="Fallback identifier — URI namespace."
    )
    reference_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    reference_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — when it became valid."
    )
    reference_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — when it stopped being valid."
    )
