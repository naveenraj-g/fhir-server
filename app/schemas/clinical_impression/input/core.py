from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.clinical_impression.enums import ClinicalImpressionStatus
from app.schemas.clinical_impression.input.codeable_concept import (
    ClinicalImpressionCodeableConceptInput,
)
from app.schemas.clinical_impression.input.finding import (
    ClinicalImpressionFindingInput,
)
from app.schemas.clinical_impression.input.identifier import (
    ClinicalImpressionIdentifierInput,
)
from app.schemas.clinical_impression.input.investigation import (
    ClinicalImpressionInvestigationInput,
)
from app.schemas.clinical_impression.input.note import ClinicalImpressionNoteInput
from app.schemas.clinical_impression.input.reference import (
    ClinicalImpressionAssessorInput,
    ClinicalImpressionEncounterInput,
    ClinicalImpressionPreviousInput,
    ClinicalImpressionProblemInput,
    ClinicalImpressionPrognosisReferenceInput,
    ClinicalImpressionSubjectInput,
    ClinicalImpressionSupportingInfoInput,
)

_CREATE_EXAMPLE: dict[str, Any] = {
    "status": "completed",
    "description": "Initial clinical evaluation for acute chest pain.",
    "subject": {
        "reference": "Patient/10001",
        "reference_display": "Jane Doe",
    },
    "encounter": {
        "reference": "Encounter/20001",
        "reference_display": "Emergency encounter",
    },
    "effective_date_time": "2026-02-01T10:00:00Z",
    "date": "2026-02-01T11:00:00Z",
    "assessor": {
        "reference": "Practitioner/30001",
        "reference_display": "Dr. Alice Smith",
    },
    "summary": "Patient presented with acute non-cardiac chest pain, stable vitals.",
    "investigation": [
        {
            "code": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "271336007",
                        "display": "Examination / signs",
                    }
                ],
                "text": "Initial physical exam and ECG",
            },
            "item": [
                {
                    "reference": "Observation/160001",
                    "reference_display": "12-lead ECG",
                }
            ],
        }
    ],
    "problem": [
        {
            "reference": "Condition/120001",
            "reference_display": "Chest pain",
        }
    ],
    "finding": [
        {
            "item_codeable_concept": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "29857009",
                        "display": "Chest pain, unspecified",
                    }
                ],
                "text": "Musculoskeletal chest pain",
            },
            "basis": "Normal ECG and cardiac biomarkers",
        }
    ],
    "prognosis_codeable_concept": [
        {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "170968001",
                    "display": "Good prognosis",
                }
            ],
            "text": "Good prognosis with outpatient follow-up",
        }
    ],
}


class ClinicalImpressionCreateSchema(BaseModel):
    """Schema for creating a new ClinicalImpression resource.
    Multi-tenancy: org_id and created_by are extracted from the verified JWT.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": _CREATE_EXAMPLE},
    )

    extension: list[dict] | None = Field(
        None, description="Optional DomainResource extensions."
    )
    identifier: list[ClinicalImpressionIdentifierInput] | None = Field(
        None, description="Business identifier for impression."
    )
    status: ClinicalImpressionStatus = Field(
        ...,
        description="in-progress | completed | entered-in-error",
    )
    status_reason: ClinicalImpressionCodeableConceptInput | None = Field(
        None, description="Reason for current status."
    )
    code: ClinicalImpressionCodeableConceptInput | None = Field(
        None, description="Kind of impression performed."
    )
    description: str | None = Field(
        None, description="Why/how the assessment was performed."
    )
    subject: ClinicalImpressionSubjectInput = Field(
        ..., description="Patient or group impression is about (1..1 Reference(Patient | Group))."
    )
    encounter: ClinicalImpressionEncounterInput | None = Field(
        None, description="Encounter created as part of."
    )
    effective_date_time: datetime | None = Field(
        None, description="Time of assessment (dateTime)."
    )
    effective_period_start: datetime | None = Field(
        None, description="Time of assessment period (start)."
    )
    effective_period_end: datetime | None = Field(
        None, description="Time of assessment period (end)."
    )
    date: datetime | None = Field(
        None, description="When the assessment was documented."
    )
    assessor: ClinicalImpressionAssessorInput | None = Field(
        None, description="The clinician performing the assessment."
    )
    previous: ClinicalImpressionPreviousInput | None = Field(
        None, description="Reference to last assessment."
    )
    problem: list[ClinicalImpressionProblemInput] | None = Field(
        None, description="Relevant impressions of patient state."
    )
    investigation: list[ClinicalImpressionInvestigationInput] | None = Field(
        None, description="One or more sets of investigations (examinations, tests, reports)."
    )
    protocol: list[str] | None = Field(
        None, description="Clinical Protocol followed (URI)."
    )
    summary: str | None = Field(
        None, description="Summary of the assessment."
    )
    finding: list[ClinicalImpressionFindingInput] | None = Field(
        None, description="Possible or likely findings and diagnoses."
    )
    prognosis_codeable_concept: list[ClinicalImpressionCodeableConceptInput] | None = Field(
        None, description="Estimate of likely outcome (CodeableConcept)."
    )
    prognosis_reference: list[ClinicalImpressionPrognosisReferenceInput] | None = Field(
        None, description="RiskAssessment expressing likely outcome."
    )
    supporting_info: list[ClinicalImpressionSupportingInfoInput] | None = Field(
        None, description="Information supporting the clinical impression."
    )
    note: list[ClinicalImpressionNoteInput] | None = Field(
        None, description="Comments made about the ClinicalImpression."
    )


class ClinicalImpressionPatchSchema(BaseModel):
    """Schema for partially updating a ClinicalImpression resource."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"status": "completed", "summary": "Updated assessment summary"}},
    )

    extension: list[dict] | None = None
    identifier: list[ClinicalImpressionIdentifierInput] | None = None
    status: ClinicalImpressionStatus | None = None
    status_reason: ClinicalImpressionCodeableConceptInput | None = None
    code: ClinicalImpressionCodeableConceptInput | None = None
    description: str | None = None
    subject: ClinicalImpressionSubjectInput | None = None
    encounter: ClinicalImpressionEncounterInput | None = None
    effective_date_time: datetime | None = None
    effective_period_start: datetime | None = None
    effective_period_end: datetime | None = None
    date: datetime | None = None
    assessor: ClinicalImpressionAssessorInput | None = None
    previous: ClinicalImpressionPreviousInput | None = None
    problem: list[ClinicalImpressionProblemInput] | None = None
    investigation: list[ClinicalImpressionInvestigationInput] | None = None
    protocol: list[str] | None = None
    summary: str | None = None
    finding: list[ClinicalImpressionFindingInput] | None = None
    prognosis_codeable_concept: list[ClinicalImpressionCodeableConceptInput] | None = None
    prognosis_reference: list[ClinicalImpressionPrognosisReferenceInput] | None = None
    supporting_info: list[ClinicalImpressionSupportingInfoInput] | None = None
    note: list[ClinicalImpressionNoteInput] | None = None
