from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import IdentifierUse
from app.models.flag.enums import FlagStatus
from app.schemas.datatypes import CodingInput

from .category import FlagCategoryInput
from .identifier import FlagIdentifierInput

_EXAMPLE = {
    "status": "active",
    "category": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/flag-category",
                    "code": "clinical",
                    "display": "Clinical",
                }
            ],
            "text": "Clinical",
        }
    ],
    "code_coding": [
        {
            "system": "http://snomed.info/sct",
            "code": "399166001",
            "display": "Infection control precaution",
        }
    ],
    "code_text": "Infection control precaution",
    "subject": "Patient/10001",
    "subject_display": "Jane Doe",
    "period_start": "2026-01-01T00:00:00Z",
    "period_end": "2026-12-31T23:59:59Z",
    "encounter": "Encounter/20001",
    "encounter_display": "Inpatient encounter",
    "author": "Practitioner/30001",
    "author_display": "Dr. Smith",
}


class FlagCreateSchema(BaseModel):
    """Request body for POST /api/fhir/v1/flags.

    Flag is an org-scoped entity and has no user_id.
    status, code (code_coding or code_text), and subject are required per FHIR R4.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": _EXAMPLE},
    )

    identifier: list[FlagIdentifierInput] | None = Field(
        None, description="Business identifier for each flag."
    )
    status: FlagStatus = Field(
        ..., description="active | inactive | entered-in-error."
    )
    category: list[FlagCategoryInput] | None = Field(
        None, description="Clinical, administrative, etc."
    )
    code_coding: list[CodingInput] | None = Field(
        None, description="Coded aspect of flag."
    )
    code_text: str | None = Field(
        None, description="Plain text representation of the flag code."
    )
    subject: str | None = Field(
        None,
        description="Who/What is the flag about, as a FHIR reference string (e.g. 'Patient/10001').",
    )
    subject_display: str | None = Field(
        None, description="Plain text narrative for the subject reference."
    )
    subject_identifier_use: IdentifierUse | None = Field(
        None, description="Subject identifier use."
    )
    subject_identifier_type_system: str | None = Field(
        None, description="Subject identifier type system."
    )
    subject_identifier_type_version: str | None = Field(
        None, description="Subject identifier type version."
    )
    subject_identifier_type_code: str | None = Field(
        None, description="Subject identifier type code."
    )
    subject_identifier_type_display: str | None = Field(
        None, description="Subject identifier type display."
    )
    subject_identifier_type_user_selected: bool | None = Field(
        None, description="Subject identifier type user selected."
    )
    subject_identifier_type_text: str | None = Field(
        None, description="Subject identifier type text."
    )
    subject_identifier_system: str | None = Field(
        None, description="Subject identifier system."
    )
    subject_identifier_value: str | None = Field(
        None, description="Subject identifier value."
    )
    subject_identifier_period_start: datetime | None = Field(
        None, description="Subject identifier period start."
    )
    subject_identifier_period_end: datetime | None = Field(
        None, description="Subject identifier period end."
    )
    period_start: datetime | None = Field(
        None, description="Start of time period when flag is active."
    )
    period_end: datetime | None = Field(
        None, description="End of time period when flag is active."
    )
    encounter: str | None = Field(
        None,
        description="Alert relevant to this encounter, as a FHIR reference string (e.g. 'Encounter/20001').",
    )
    encounter_display: str | None = Field(
        None, description="Plain text narrative for the encounter reference."
    )
    encounter_identifier_use: IdentifierUse | None = Field(
        None, description="Encounter identifier use."
    )
    encounter_identifier_type_system: str | None = Field(
        None, description="Encounter identifier type system."
    )
    encounter_identifier_type_version: str | None = Field(
        None, description="Encounter identifier type version."
    )
    encounter_identifier_type_code: str | None = Field(
        None, description="Encounter identifier type code."
    )
    encounter_identifier_type_display: str | None = Field(
        None, description="Encounter identifier type display."
    )
    encounter_identifier_type_user_selected: bool | None = Field(
        None, description="Encounter identifier type user selected."
    )
    encounter_identifier_type_text: str | None = Field(
        None, description="Encounter identifier type text."
    )
    encounter_identifier_system: str | None = Field(
        None, description="Encounter identifier system."
    )
    encounter_identifier_value: str | None = Field(
        None, description="Encounter identifier value."
    )
    encounter_identifier_period_start: datetime | None = Field(
        None, description="Encounter identifier period start."
    )
    encounter_identifier_period_end: datetime | None = Field(
        None, description="Encounter identifier period end."
    )
    author: str | None = Field(
        None,
        description="Flag creator, as a FHIR reference string (e.g. 'Practitioner/30001').",
    )
    author_display: str | None = Field(
        None, description="Plain text narrative for the author reference."
    )
    author_identifier_use: IdentifierUse | None = Field(
        None, description="Author identifier use."
    )
    author_identifier_type_system: str | None = Field(
        None, description="Author identifier type system."
    )
    author_identifier_type_version: str | None = Field(
        None, description="Author identifier type version."
    )
    author_identifier_type_code: str | None = Field(
        None, description="Author identifier type code."
    )
    author_identifier_type_display: str | None = Field(
        None, description="Author identifier type display."
    )
    author_identifier_type_user_selected: bool | None = Field(
        None, description="Author identifier type user selected."
    )
    author_identifier_type_text: str | None = Field(
        None, description="Author identifier type text."
    )
    author_identifier_system: str | None = Field(
        None, description="Author identifier system."
    )
    author_identifier_value: str | None = Field(
        None, description="Author identifier value."
    )
    author_identifier_period_start: datetime | None = Field(
        None, description="Author identifier period start."
    )
    author_identifier_period_end: datetime | None = Field(
        None, description="Author identifier period end."
    )

    @model_validator(mode="after")
    def validate_required_fields(self) -> "FlagCreateSchema":
        if not self.code_coding and not self.code_text:
            raise ValueError(
                "Flag.code is required (at least code_coding or code_text must be provided)"
            )
        if not self.subject and not self.subject_identifier_value and not self.subject_display:
            raise ValueError(
                "Flag.subject is required (at least subject reference, identifier, or display must be provided)"
            )
        return self


class FlagPatchSchema(BaseModel):
    """Request body for PATCH /api/fhir/v1/flags/{flag_id}.

    All fields optional; excludes immutable fields.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "status": "inactive",
                "period_end": "2026-12-31T23:59:59Z",
            }
        },
    )

    identifier: list[FlagIdentifierInput] | None = Field(
        None, description="Business identifier for each flag."
    )
    status: FlagStatus | None = Field(
        None, description="active | inactive | entered-in-error."
    )
    category: list[FlagCategoryInput] | None = Field(
        None, description="Clinical, administrative, etc."
    )
    code_coding: list[CodingInput] | None = Field(
        None, description="Coded aspect of flag."
    )
    code_text: str | None = Field(
        None, description="Plain text representation of the flag code."
    )
    subject: str | None = Field(
        None,
        description="Who/What is the flag about, as a FHIR reference string (e.g. 'Patient/10001').",
    )
    subject_display: str | None = Field(
        None, description="Plain text narrative for the subject reference."
    )
    subject_identifier_use: IdentifierUse | None = Field(
        None, description="Subject identifier use."
    )
    subject_identifier_type_system: str | None = Field(
        None, description="Subject identifier type system."
    )
    subject_identifier_type_version: str | None = Field(
        None, description="Subject identifier type version."
    )
    subject_identifier_type_code: str | None = Field(
        None, description="Subject identifier type code."
    )
    subject_identifier_type_display: str | None = Field(
        None, description="Subject identifier type display."
    )
    subject_identifier_type_user_selected: bool | None = Field(
        None, description="Subject identifier type user selected."
    )
    subject_identifier_type_text: str | None = Field(
        None, description="Subject identifier type text."
    )
    subject_identifier_system: str | None = Field(
        None, description="Subject identifier system."
    )
    subject_identifier_value: str | None = Field(
        None, description="Subject identifier value."
    )
    subject_identifier_period_start: datetime | None = Field(
        None, description="Subject identifier period start."
    )
    subject_identifier_period_end: datetime | None = Field(
        None, description="Subject identifier period end."
    )
    period_start: datetime | None = Field(
        None, description="Start of time period when flag is active."
    )
    period_end: datetime | None = Field(
        None, description="End of time period when flag is active."
    )
    encounter: str | None = Field(
        None,
        description="Alert relevant to this encounter, as a FHIR reference string (e.g. 'Encounter/20001').",
    )
    encounter_display: str | None = Field(
        None, description="Plain text narrative for the encounter reference."
    )
    encounter_identifier_use: IdentifierUse | None = Field(
        None, description="Encounter identifier use."
    )
    encounter_identifier_type_system: str | None = Field(
        None, description="Encounter identifier type system."
    )
    encounter_identifier_type_version: str | None = Field(
        None, description="Encounter identifier type version."
    )
    encounter_identifier_type_code: str | None = Field(
        None, description="Encounter identifier type code."
    )
    encounter_identifier_type_display: str | None = Field(
        None, description="Encounter identifier type display."
    )
    encounter_identifier_type_user_selected: bool | None = Field(
        None, description="Encounter identifier type user selected."
    )
    encounter_identifier_type_text: str | None = Field(
        None, description="Encounter identifier type text."
    )
    encounter_identifier_system: str | None = Field(
        None, description="Encounter identifier system."
    )
    encounter_identifier_value: str | None = Field(
        None, description="Encounter identifier value."
    )
    encounter_identifier_period_start: datetime | None = Field(
        None, description="Encounter identifier period start."
    )
    encounter_identifier_period_end: datetime | None = Field(
        None, description="Encounter identifier period end."
    )
    author: str | None = Field(
        None,
        description="Flag creator, as a FHIR reference string (e.g. 'Practitioner/30001').",
    )
    author_display: str | None = Field(
        None, description="Plain text narrative for the author reference."
    )
    author_identifier_use: IdentifierUse | None = Field(
        None, description="Author identifier use."
    )
    author_identifier_type_system: str | None = Field(
        None, description="Author identifier type system."
    )
    author_identifier_type_version: str | None = Field(
        None, description="Author identifier type version."
    )
    author_identifier_type_code: str | None = Field(
        None, description="Author identifier type code."
    )
    author_identifier_type_display: str | None = Field(
        None, description="Author identifier type display."
    )
    author_identifier_type_user_selected: bool | None = Field(
        None, description="Author identifier type user selected."
    )
    author_identifier_type_text: str | None = Field(
        None, description="Author identifier type text."
    )
    author_identifier_system: str | None = Field(
        None, description="Author identifier system."
    )
    author_identifier_value: str | None = Field(
        None, description="Author identifier value."
    )
    author_identifier_period_start: datetime | None = Field(
        None, description="Author identifier period start."
    )
    author_identifier_period_end: datetime | None = Field(
        None, description="Author identifier period end."
    )
