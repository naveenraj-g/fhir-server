from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

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
    subject: str = Field(
        ...,
        description="Who/What is the flag about, as a FHIR reference string (e.g. 'Patient/10001').",
    )
    subject_display: str | None = Field(
        None, description="Plain text narrative for the subject reference."
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
    author: str | None = Field(
        None,
        description="Flag creator, as a FHIR reference string (e.g. 'Practitioner/30001').",
    )
    author_display: str | None = Field(
        None, description="Plain text narrative for the author reference."
    )


class FlagPatchSchema(BaseModel):
    """Request body for PATCH /api/fhir/v1/flags/{flag_id}.

    All fields optional; excludes immutable fields.
    """

    model_config = ConfigDict(extra="forbid")

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
    author: str | None = Field(
        None,
        description="Flag creator, as a FHIR reference string (e.g. 'Practitioner/30001').",
    )
    author_display: str | None = Field(
        None, description="Plain text narrative for the author reference."
    )
