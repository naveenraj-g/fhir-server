from pydantic import Field

from app.schemas.datatypes import AuditFields


class PlainPatientGeneralPractitioner(AuditFields):
    id: int = Field(..., description="Internal row ID.")
    reference: str | None = Field(
        None, description="Resolved FHIR reference (e.g. 'Practitioner/30001')."
    )
    reference_type: str | None = Field(
        None, description="Resource type of care provider."
    )
    reference_id: int | None = Field(
        None, description="Public resource sequence ID."
    )
    display: str | None = Field(
        None, description="Plain text display narrative."
    )
    reference_identifier_use: str | None = Field(
        None, description="Logical-reference fallback — identifier use."
    )
    reference_identifier_type_system: str | None = Field(
        None, description="Logical-reference fallback — identifier type system."
    )
    reference_identifier_type_version: str | None = Field(
        None, description="Logical-reference fallback — identifier type version."
    )
    reference_identifier_type_code: str | None = Field(
        None, description="Logical-reference fallback — identifier type code."
    )
    reference_identifier_type_display: str | None = Field(
        None, description="Logical-reference fallback — identifier type display."
    )
    reference_identifier_type_user_selected: bool | None = Field(
        None, description="Logical-reference fallback — identifier type user selected."
    )
    reference_identifier_type_text: str | None = Field(
        None, description="Logical-reference fallback — identifier type text."
    )
    reference_identifier_system: str | None = Field(
        None, description="Logical-reference fallback — identifier namespace URL."
    )
    reference_identifier_value: str | None = Field(
        None, description="Logical-reference fallback — identifier value."
    )
    reference_identifier_period_start: str | None = Field(
        None, description="Logical-reference fallback — identifier period start."
    )
    reference_identifier_period_end: str | None = Field(
        None, description="Logical-reference fallback — identifier period end."
    )
