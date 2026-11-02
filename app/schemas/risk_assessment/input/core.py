from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.risk_assessment.enums import RiskAssessmentStatus
from app.schemas.risk_assessment.input.codeable_concept import (
    RiskAssessmentCodeableConceptInput,
)
from app.schemas.risk_assessment.input.identifier import (
    RiskAssessmentIdentifierInput,
)
from app.schemas.risk_assessment.input.note import RiskAssessmentNoteInput
from app.schemas.risk_assessment.input.prediction import (
    RiskAssessmentPredictionInput,
)
from app.schemas.risk_assessment.input.reference import (
    RiskAssessmentBasedOnInput,
    RiskAssessmentBasisInput,
    RiskAssessmentConditionInput,
    RiskAssessmentEncounterInput,
    RiskAssessmentParentInput,
    RiskAssessmentPerformerInput,
    RiskAssessmentReasonReferenceInput,
    RiskAssessmentSubjectInput,
)

_CREATE_EXAMPLE: dict[str, Any] = {
    "status": "final",
    "subject": {
        "reference": "Patient/10001",
        "reference_display": "Jane Doe",
    },
    "occurrence_date_time": "2026-02-01T10:00:00Z",
    "condition": {
        "reference": "Condition/120001",
        "reference_display": "Hypertension",
    },
    "performer": {
        "reference": "Practitioner/30001",
        "reference_display": "Dr. Alice Smith",
    },
    "method": {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "709510001",
                "display": "Framingham risk score",
            }
        ],
        "text": "Framingham 10-year cardiovascular risk",
    },
    "code": {
        "coding": [
            {
                "system": "http://loinc.org",
                "code": "89243-0",
                "display": "Cardiovascular disease 10Y risk [Likelihood]",
            }
        ],
        "text": "10-year CVD risk assessment",
    },
    "prediction": [
        {
            "outcome": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "49436004",
                        "display": "Atrial fibrillation",
                    }
                ],
                "text": "Atrial fibrillation",
            },
            "probability_decimal": 0.12,
            "qualitative_risk": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/risk-probability",
                        "code": "moderate",
                        "display": "Moderate likelihood",
                    }
                ],
                "text": "Moderate risk",
            },
            "relative_risk": 1.5,
            "rationale": "Elevated systolic BP and family history.",
        }
    ],
    "mitigation": "Initiate lifestyle modifications and low-dose antihypertensive therapy.",
    "note": [
        {
            "text": "Re-evaluate in 12 months.",
        }
    ],
}


class RiskAssessmentCreateSchema(BaseModel):
    """Request payload for POST /risk-assessments/."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": _CREATE_EXAMPLE},
    )

    status: RiskAssessmentStatus = Field(
        ...,
        description="registered | preliminary | final | amended | corrected | cancelled | entered-in-error | unknown.",
    )
    subject: RiskAssessmentSubjectInput | str = Field(
        ...,
        description="Who/what does assessment apply to? Reference(Patient | Group), e.g. 'Patient/10001'.",
    )
    based_on: RiskAssessmentBasedOnInput | str | None = Field(
        None,
        description="Request fulfilled by this assessment. Reference(Any), e.g. 'ServiceRequest/80001'.",
    )
    parent: RiskAssessmentParentInput | str | None = Field(
        None,
        description="Part of this occurrence. Reference(Any).",
    )
    encounter: RiskAssessmentEncounterInput | str | None = Field(
        None,
        description="Where was assessment performed? Reference(Encounter), e.g. 'Encounter/20001'.",
    )
    occurrence_date_time: datetime | None = Field(
        None,
        description="When was assessment made? (dateTime).",
    )
    occurrence_period_start: datetime | None = Field(
        None,
        description="When was assessment made? (Period start).",
    )
    occurrence_period_end: datetime | None = Field(
        None,
        description="When was assessment made? (Period end).",
    )
    condition: RiskAssessmentConditionInput | str | None = Field(
        None,
        description="Condition assessed. Reference(Condition), e.g. 'Condition/120001'.",
    )
    performer: RiskAssessmentPerformerInput | str | None = Field(
        None,
        description="Who did assessment? Reference(Practitioner | PractitionerRole | Device), e.g. 'Practitioner/30001'.",
    )
    method: RiskAssessmentCodeableConceptInput | None = Field(
        None,
        description="Evaluation mechanism used (e.g. algorithm, risk calculation tool).",
    )
    code: RiskAssessmentCodeableConceptInput | None = Field(
        None,
        description="Type of assessment (e.g. scoring tool, prognosis statement).",
    )
    reason_code: list[RiskAssessmentCodeableConceptInput] | None = Field(
        None,
        description="Why the assessment was necessary (concept).",
    )
    reason_reference: list[RiskAssessmentReasonReferenceInput | str] | None = Field(
        None,
        description="Why the assessment was necessary (Reference to Condition | Observation | DiagnosticReport | DocumentReference).",
    )
    basis: list[RiskAssessmentBasisInput | str] | None = Field(
        None,
        description="Information used in assessment. Reference(Any).",
    )
    prediction: list[RiskAssessmentPredictionInput] | None = Field(
        None,
        description="Outcome predicted (0..*).",
    )
    mitigation: str | None = Field(
        None,
        description="How to reduce risk.",
    )
    note: list[RiskAssessmentNoteInput] | None = Field(
        None,
        description="Comments made about the risk assessment.",
    )
    identifier: list[RiskAssessmentIdentifierInput] | None = Field(
        None,
        description="Business identifier for the assessment.",
    )
    extension: list[dict[str, Any]] | None = Field(
        None,
        description="Additional content defined by implementations.",
    )


class RiskAssessmentPatchSchema(BaseModel):
    """Request payload for PATCH /risk-assessments/{id}."""

    model_config = ConfigDict(extra="forbid")

    status: RiskAssessmentStatus | None = Field(
        None,
        description="registered | preliminary | final | amended | corrected | cancelled | entered-in-error | unknown.",
    )
    subject: RiskAssessmentSubjectInput | str | None = Field(
        None,
        description="Who/what does assessment apply to? Reference(Patient | Group).",
    )
    based_on: RiskAssessmentBasedOnInput | str | None = Field(
        None,
        description="Request fulfilled by this assessment. Reference(Any).",
    )
    parent: RiskAssessmentParentInput | str | None = Field(
        None,
        description="Part of this occurrence. Reference(Any).",
    )
    encounter: RiskAssessmentEncounterInput | str | None = Field(
        None,
        description="Where was assessment performed? Reference(Encounter).",
    )
    occurrence_date_time: datetime | None = Field(
        None,
        description="When was assessment made? (dateTime).",
    )
    occurrence_period_start: datetime | None = Field(
        None,
        description="When was assessment made? (Period start).",
    )
    occurrence_period_end: datetime | None = Field(
        None,
        description="When was assessment made? (Period end).",
    )
    condition: RiskAssessmentConditionInput | str | None = Field(
        None,
        description="Condition assessed. Reference(Condition).",
    )
    performer: RiskAssessmentPerformerInput | str | None = Field(
        None,
        description="Who did assessment? Reference(Practitioner | PractitionerRole | Device).",
    )
    method: RiskAssessmentCodeableConceptInput | None = Field(
        None,
        description="Evaluation mechanism used.",
    )
    code: RiskAssessmentCodeableConceptInput | None = Field(
        None,
        description="Type of assessment.",
    )
    reason_code: list[RiskAssessmentCodeableConceptInput] | None = Field(
        None,
        description="Why the assessment was necessary (concept).",
    )
    reason_reference: list[RiskAssessmentReasonReferenceInput | str] | None = Field(
        None,
        description="Why the assessment was necessary (reference).",
    )
    basis: list[RiskAssessmentBasisInput | str] | None = Field(
        None,
        description="Information used in assessment.",
    )
    prediction: list[RiskAssessmentPredictionInput] | None = Field(
        None,
        description="Outcome predicted.",
    )
    mitigation: str | None = Field(
        None,
        description="How to reduce risk.",
    )
    note: list[RiskAssessmentNoteInput] | None = Field(
        None,
        description="Comments made about the risk assessment.",
    )
    identifier: list[RiskAssessmentIdentifierInput] | None = Field(
        None,
        description="Business identifier for the assessment.",
    )
    extension: list[dict[str, Any]] | None = Field(
        None,
        description="Additional content defined by implementations.",
    )
