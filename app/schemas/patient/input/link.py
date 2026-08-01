from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import IdentifierUse
from app.models.patient.enums import PatientLinkOtherType, PatientLinkType


class LinkCreate(BaseModel):
    """FHIR R4 Patient.link — a link to another Patient or RelatedPerson resource
    that concerns the same actual person."""

    model_config = ConfigDict(extra="forbid")
    other_type: PatientLinkOtherType | None = Field(
        None,
        description="Resource type of the linked resource. Patient|RelatedPerson. "
        "Required together with other_id unless other_identifier_system/_value is given instead.",
    )
    other_id: int | None = Field(
        None, description="Public id of the linked Patient/RelatedPerson resource."
    )
    other_display: str | None = Field(
        None, description="Display text for the linked resource."
    )
    other_identifier_use: IdentifierUse | None = Field(
        None,
        description="Fallback identifier (used when the linked resource isn't "
        "in this system) — usual|official|temp|secondary|old.",
    )
    other_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — coding system for its type."
    )
    other_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type coding system."
    )
    other_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type (e.g. MR, SS)."
    )
    other_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    other_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — plain-text rendering of its type."
    )
    other_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was user-selected.",
    )
    other_identifier_system: str | None = Field(
        None, description="Fallback identifier — URI namespace."
    )
    other_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    other_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — when it became valid."
    )
    other_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — when it stopped being valid."
    )
    type: PatientLinkType = Field(
        ...,
        description=(
            "The type of link between this patient resource and the other. "
            "replaced-by|replaces|refer|seealso."
        ),
    )

    @model_validator(mode="after")
    def _require_reference_or_identifier(self):
        has_reference = self.other_type is not None and self.other_id is not None
        has_identifier = (
            self.other_identifier_system is not None
            and self.other_identifier_value is not None
        )
        if not has_reference and not has_identifier:
            raise ValueError(
                "Provide either other_type+other_id or "
                "other_identifier_system+other_identifier_value."
            )
        return self


class LinkPatch(BaseModel):
    """Partial update to a patient link entry — only supplied fields are written."""

    model_config = ConfigDict(extra="forbid")
    other_type: PatientLinkOtherType | None = Field(
        None, description="Patient|RelatedPerson."
    )
    other_id: int | None = Field(None, description="Public id of the linked resource.")
    other_display: str | None = Field(
        None, description="Display text for the linked resource."
    )
    other_identifier_use: IdentifierUse | None = Field(
        None,
        description="Fallback identifier (used when the linked resource isn't "
        "in this system) — usual|official|temp|secondary|old.",
    )
    other_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — coding system for its type."
    )
    other_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type coding system."
    )
    other_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type (e.g. MR, SS)."
    )
    other_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    other_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — plain-text rendering of its type."
    )
    other_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was user-selected.",
    )
    other_identifier_system: str | None = Field(
        None, description="Fallback identifier — URI namespace."
    )
    other_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    other_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — when it became valid."
    )
    other_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — when it stopped being valid."
    )
    type: PatientLinkType | None = Field(
        None, description="replaced-by|replaces|refer|seealso."
    )
