from pydantic import BaseModel, Field

from app.schemas.datatypes import AuditFields, FHIRReference


class FHIRPatientLink(BaseModel):
    other: FHIRReference = Field(
        ..., description="The other patient or related person resource that the link refers to."
    )
    type: str = Field(
        ..., description="replaced-by | replaces | refer | seealso"
    )


class PlainPatientLink(AuditFields):
    id: int = Field(..., description="Internal row ID.")
    other: str | None = Field(
        None, description="Resolved FHIR reference (e.g. 'Patient/10001')."
    )
    other_type: str | None = Field(
        None, description="Resource type of other target."
    )
    other_id: int | None = Field(
        None, description="Public resource sequence ID."
    )
    other_display: str | None = Field(
        None, description="Plain text display narrative."
    )
    other_identifier_use: str | None = Field(
        None, description="Logical-reference fallback — identifier use."
    )
    other_identifier_type_system: str | None = Field(
        None, description="Logical-reference fallback — identifier type system."
    )
    other_identifier_type_version: str | None = Field(
        None, description="Logical-reference fallback — identifier type version."
    )
    other_identifier_type_code: str | None = Field(
        None, description="Logical-reference fallback — identifier type code."
    )
    other_identifier_type_display: str | None = Field(
        None, description="Logical-reference fallback — identifier type display."
    )
    other_identifier_type_user_selected: bool | None = Field(
        None, description="Logical-reference fallback — identifier type user selected."
    )
    other_identifier_type_text: str | None = Field(
        None, description="Logical-reference fallback — identifier type text."
    )
    other_identifier_system: str | None = Field(
        None, description="Logical-reference fallback — identifier namespace URL."
    )
    other_identifier_value: str | None = Field(
        None, description="Logical-reference fallback — identifier value."
    )
    other_identifier_period_start: str | None = Field(
        None, description="Logical-reference fallback — identifier period start."
    )
    other_identifier_period_end: str | None = Field(
        None, description="Logical-reference fallback — identifier period end."
    )
    type: str | None = Field(
        None, description="Type of link (replaced-by, replaces, refer, seealso)."
    )
