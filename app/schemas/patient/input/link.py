from pydantic import BaseModel, ConfigDict, Field

from app.models.patient.enums import PatientLinkOtherType, PatientLinkType
from app.schemas.enums import IdentifierUse


class PatientLinkInput(BaseModel):
    """Patient.link — link to a Patient or RelatedPerson resource that concerns the same actual individual (BackboneElement)."""

    model_config = ConfigDict(extra="forbid")
    other: str | None = Field(
        None,
        description="Reference to the other patient or related person (e.g. 'Patient/10001', 'RelatedPerson/300001').",
    )
    other_type: PatientLinkOtherType | None = Field(
        None, description="Resource type of other target — Patient|RelatedPerson."
    )
    other_id: int | None = Field(
        None, description="Public sequence ID of the other resource."
    )
    other_display: str | None = Field(
        None, description="Plain text display narrative for other resource."
    )
    other_identifier_system: str | None = Field(
        None, description="Logical-reference fallback — identifier namespace URL."
    )
    other_identifier_value: str | None = Field(
        None, description="Logical-reference fallback — identifier value."
    )
    other_identifier_use: IdentifierUse | None = Field(
        None, description="Logical-reference fallback — identifier use."
    )
    other_identifier_type_text: str | None = Field(
        None, description="Logical-reference fallback — identifier type text."
    )
    type: PatientLinkType | None = Field(
        None, description="Type of link — replaced_by|replaces|refer|seealso."
    )
