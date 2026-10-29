from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import DiagnosticReportStatus

from .codeable_concept import DiagnosticReportCodeableConceptInput
from .identifier import DiagnosticReportIdentifierInput
from .media import DiagnosticReportMediaInput
from .presented_form import DiagnosticReportPresentedFormInput
from .reference import (
    DiagnosticReportBasedOnInput,
    DiagnosticReportEncounterInput,
    DiagnosticReportImagingStudyInput,
    DiagnosticReportPerformerInput,
    DiagnosticReportResultInput,
    DiagnosticReportResultsInterpreterInput,
    DiagnosticReportSpecimenInput,
    DiagnosticReportSubjectInput,
)

_EXAMPLE = {
    "user_id": "user-001",
    "tenant_id": "org-001",
    "created_by": "user-001",
    "status": "final",
    "code": {"coding": [{"system": "http://loinc.org", "code": "58410-2", "display": "Complete blood count panel"}]},
    "subject": {"reference": "Patient/10001"},
    "conclusion": "No significant abnormalities detected.",
}


class DiagnosticReportCreateSchema(BaseModel):
    """Creates a DiagnosticReport and any combination of its sub-resource
    lists atomically in one request. Default (gateway-trusted) pattern —
    NOT part of the JWT auth rollout, same as Observation/
    QuestionnaireResponse/ServiceRequest/MedicationRequest: `tenant_id`/
    `created_by` are plain, gateway-forwarded request fields."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": _EXAMPLE})

    user_id: str | None = Field(None, description="Gateway-forwarded ID of the end-user this record is scoped to.")
    tenant_id: str = Field(..., description="Gateway-forwarded ID of the tenant/account this record is scoped to.")
    created_by: str = Field(..., description="Gateway-forwarded ID of the acting user who created this record.")

    extension: list[dict] | None = Field(None, description="Resource-level FHIR extensions.")

    identifier: list[DiagnosticReportIdentifierInput] | None = Field(None, description="Business identifiers assigned to the report.")
    based_on: list[DiagnosticReportBasedOnInput] | None = Field(None, description="The request that was fulfilled by this report.")
    status: DiagnosticReportStatus = Field(..., description="registered | partial | preliminary | final | amended | corrected | appended | cancelled | entered-in-error | unknown.")
    category: list[DiagnosticReportCodeableConceptInput] | None = Field(None, description="Clinical service/discipline that produced the report.")
    code: DiagnosticReportCodeableConceptInput = Field(..., description="Name/code for this diagnostic report.")
    subject: DiagnosticReportSubjectInput | None = Field(None, description="The subject of the report, usually a patient.")
    encounter: DiagnosticReportEncounterInput | None = Field(None, description="Healthcare event during which this report was created.")

    # effective[x]
    effective_date_time: datetime | None = Field(None, description="effective[x]: dateTime.")
    effective_period_start: datetime | None = Field(None, description="effective[x]: Period — start.")
    effective_period_end: datetime | None = Field(None, description="effective[x]: Period — end.")

    issued: datetime | None = Field(None, description="When this version of the report was made available to providers.")
    performer: list[DiagnosticReportPerformerInput] | None = Field(None, description="Diagnostic service responsible for issuing the report.")
    results_interpreter: list[DiagnosticReportResultsInterpreterInput] | None = Field(None, description="Party responsible for the report's conclusions/interpretations.")
    specimen: list[DiagnosticReportSpecimenInput] | None = Field(None, description="Specimens this report is based on.")
    result: list[DiagnosticReportResultInput] | None = Field(None, description="Observations that are part of this report.")
    imaging_study: list[DiagnosticReportImagingStudyInput] | None = Field(None, description="Full details of imaging performed during the investigation.")
    media: list[DiagnosticReportMediaInput] | None = Field(None, description="Key images associated with this report.")
    conclusion: str | None = Field(None, description="Concise clinical summary/interpretation of the results.")
    conclusion_code: list[DiagnosticReportCodeableConceptInput] | None = Field(None, description="Codes for the clinical conclusion of this test.")
    presented_form: list[DiagnosticReportPresentedFormInput] | None = Field(None, description="Full report as issued, e.g. a PDF.")


class DiagnosticReportPatchSchema(BaseModel):
    """Partial update — only supplied fields are written. Every supplied
    sub-resource list (even `[]`) replaces the corresponding rows
    wholesale; omitted lists are left untouched."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"updated_by": "user-001", "status": "amended"}})

    updated_by: str | None = Field(None, description="Gateway-forwarded ID of the acting user making this update.")

    extension: list[dict] | None = Field(None, description="Replaces the full list if supplied.")
    identifier: list[DiagnosticReportIdentifierInput] | None = Field(None, description="Replaces the full list if supplied.")
    based_on: list[DiagnosticReportBasedOnInput] | None = Field(None, description="Replaces the full list if supplied.")
    status: DiagnosticReportStatus | None = Field(None, description="registered | partial | preliminary | final | amended | corrected | appended | cancelled | entered-in-error | unknown.")
    category: list[DiagnosticReportCodeableConceptInput] | None = Field(None, description="Replaces the full list if supplied.")
    code: DiagnosticReportCodeableConceptInput | None = Field(None, description="Set to null to clear (not recommended — code is 1..1 in FHIR).")
    subject: DiagnosticReportSubjectInput | None = Field(None, description="Set to null to clear.")
    encounter: DiagnosticReportEncounterInput | None = Field(None, description="Set to null to clear.")

    effective_date_time: datetime | None = Field(None, description="effective[x]: dateTime.")
    effective_period_start: datetime | None = Field(None, description="effective[x]: Period — start.")
    effective_period_end: datetime | None = Field(None, description="effective[x]: Period — end.")

    issued: datetime | None = Field(None, description="When this version of the report was made available to providers.")
    performer: list[DiagnosticReportPerformerInput] | None = Field(None, description="Replaces the full list if supplied.")
    results_interpreter: list[DiagnosticReportResultsInterpreterInput] | None = Field(None, description="Replaces the full list if supplied.")
    specimen: list[DiagnosticReportSpecimenInput] | None = Field(None, description="Replaces the full list if supplied.")
    result: list[DiagnosticReportResultInput] | None = Field(None, description="Replaces the full list if supplied.")
    imaging_study: list[DiagnosticReportImagingStudyInput] | None = Field(None, description="Replaces the full list if supplied.")
    media: list[DiagnosticReportMediaInput] | None = Field(None, description="Replaces the full list if supplied.")
    conclusion: str | None = Field(None, description="Set to null to clear.")
    conclusion_code: list[DiagnosticReportCodeableConceptInput] | None = Field(None, description="Replaces the full list if supplied.")
    presented_form: list[DiagnosticReportPresentedFormInput] | None = Field(None, description="Replaces the full list if supplied.")
