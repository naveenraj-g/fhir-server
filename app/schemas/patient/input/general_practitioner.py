from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.patient.enums import PatientGeneralPractitionerReferenceType
from app.schemas.enums import IdentifierUse


class PatientGeneralPractitionerInput(BaseModel):
    """Patient.generalPractitioner — nominated primary care provider (Reference(Organization | Practitioner | PractitionerRole))."""

    model_config = ConfigDict(extra="forbid")
    reference: str | None = Field(
        None,
        description="FHIR reference string (e.g. 'Practitioner/30001', 'Organization/190001', 'PractitionerRole/140001').",
    )
    reference_type: PatientGeneralPractitionerReferenceType | None = Field(
        None, description="Target resource type — Organization|Practitioner|PractitionerRole."
    )
    reference_id: int | None = Field(
        None, description="Public resource sequence ID of the target."
    )
    display: str | None = Field(
        None, description="Plain text display narrative for the reference."
    )
    reference_identifier_use: IdentifierUse | None = Field(
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
    reference_identifier_period_start: datetime | None = Field(
        None, description="Logical-reference fallback — identifier period start."
    )
    reference_identifier_period_end: datetime | None = Field(
        None, description="Logical-reference fallback — identifier period end."
    )
