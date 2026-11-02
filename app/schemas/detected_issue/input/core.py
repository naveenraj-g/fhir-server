from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.detected_issue.enums import DetectedIssueSeverity, DetectedIssueStatus

from .codeable_concept import DetectedIssueCodeableConceptInput
from .evidence import DetectedIssueEvidenceInput
from .identifier import DetectedIssueIdentifierInput
from .mitigation import DetectedIssueMitigationInput
from .reference import (
    DetectedIssueAuthorInput,
    DetectedIssueImplicatedInput,
    DetectedIssuePatientInput,
)


class DetectedIssueCreateSchema(BaseModel):
    """Payload to create a new DetectedIssue resource."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "status": "final",
                "code": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                            "code": "DRG",
                            "display": "Drug Interaction Alert",
                        }
                    ],
                    "text": "Potential drug-drug interaction between Warfarin and Aspirin",
                },
                "severity": "high",
                "patient": {
                    "reference": "Patient/10001",
                    "reference_display": "Jane Doe",
                },
                "identified_date_time": "2026-02-01T10:00:00Z",
                "author": {
                    "reference": "Practitioner/30001",
                    "reference_display": "Dr. Alice Smith",
                },
                "implicated": [
                    {
                        "reference": "MedicationRequest/90001",
                        "reference_display": "Warfarin Sodium 5mg",
                    },
                    {
                        "reference": "MedicationRequest/90002",
                        "reference_display": "Aspirin 81mg",
                    },
                ],
                "detail": "Concurrent use of warfarin and aspirin significantly increases risk of major gastrointestinal hemorrhage.",
                "reference": "http://example.org/alerts/interaction-war-asp",
                "evidence": [
                    {
                        "code": [
                            {
                                "coding": [
                                    {
                                        "system": "http://snomed.info/sct",
                                        "code": "89240000",
                                        "display": "Drug-induced hemorrhage",
                                    }
                                ],
                                "text": "Bleeding complication risk",
                            }
                        ],
                    }
                ],
                "mitigation": [
                    {
                        "action": {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
                                    "code": "13",
                                    "display": "Consulted Prescriber",
                                }
                            ],
                            "text": "Prescriber confirmed low-dose aspirin is indicated with close INR monitoring.",
                        },
                        "date": "2026-02-01T10:30:00Z",
                        "author": {
                            "reference": "Practitioner/30001",
                            "reference_display": "Dr. Alice Smith",
                        },
                    }
                ],
                "identifier": [
                    {
                        "use": "official",
                        "system": "http://example.org/issues",
                        "value": "ISSUE-2026-001",
                    }
                ],
            }
        },
    )

    status: DetectedIssueStatus = Field(
        ...,
        description="registered | preliminary | final | amended | corrected | cancelled | entered-in-error | unknown (1..1).",
    )
    code: DetectedIssueCodeableConceptInput | None = Field(
        None, description="Issue Category, e.g. drug-drug, contraindication."
    )
    severity: DetectedIssueSeverity | None = Field(
        None, description="high | moderate | low."
    )
    patient: DetectedIssuePatientInput | None = Field(
        None, description="Associated patient (0..1 Reference(Patient))."
    )
    identified_date_time: datetime | None = Field(
        None, description="When the issue was identified (dateTime variant)."
    )
    identified_period_start: datetime | None = Field(
        None, description="When the issue was identified (Period start)."
    )
    identified_period_end: datetime | None = Field(
        None, description="When the issue was identified (Period end)."
    )
    author: DetectedIssueAuthorInput | None = Field(
        None, description="Provider or device that identified the issue."
    )
    implicated: list[DetectedIssueImplicatedInput] | None = Field(
        None, description="Problem resource(s) involved in the issue."
    )
    evidence: list[DetectedIssueEvidenceInput] | None = Field(
        None, description="Supporting evidence / manifestation."
    )
    detail: str | None = Field(
        None, description="Description and context of the issue."
    )
    reference: str | None = Field(
        None, description="Authority for issue (guideline URL/URI)."
    )
    mitigation: list[DetectedIssueMitigationInput] | None = Field(
        None, description="Steps taken to address the issue."
    )
    identifier: list[DetectedIssueIdentifierInput] | None = Field(
        None, description="Business identifier for issue."
    )
    extension: dict[str, Any] | None = Field(
        None, description="FHIR DomainResource extensions."
    )


class DetectedIssuePatchSchema(BaseModel):
    """Payload to patch an existing DetectedIssue resource. All fields optional."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "status": "final",
                "severity": "moderate",
                "detail": "Updated clinical assessment: lower severity after dose adjustment.",
            }
        },
    )

    status: DetectedIssueStatus | None = Field(
        None, description="registered | preliminary | final | amended | corrected | cancelled | entered-in-error | unknown."
    )
    code: DetectedIssueCodeableConceptInput | None = Field(
        None, description="Issue Category."
    )
    severity: DetectedIssueSeverity | None = Field(
        None, description="high | moderate | low."
    )
    patient: DetectedIssuePatientInput | None = Field(
        None, description="Associated patient."
    )
    identified_date_time: datetime | None = Field(
        None, description="When the issue was identified (dateTime variant)."
    )
    identified_period_start: datetime | None = Field(
        None, description="When the issue was identified (Period start)."
    )
    identified_period_end: datetime | None = Field(
        None, description="When the issue was identified (Period end)."
    )
    author: DetectedIssueAuthorInput | None = Field(
        None, description="Provider or device that identified the issue."
    )
    implicated: list[DetectedIssueImplicatedInput] | None = Field(
        None, description="Problem resource(s) involved in the issue."
    )
    evidence: list[DetectedIssueEvidenceInput] | None = Field(
        None, description="Supporting evidence / manifestation."
    )
    detail: str | None = Field(
        None, description="Description and context."
    )
    reference: str | None = Field(
        None, description="Authority for issue."
    )
    mitigation: list[DetectedIssueMitigationInput] | None = Field(
        None, description="Steps taken to address the issue."
    )
    identifier: list[DetectedIssueIdentifierInput] | None = Field(
        None, description="Business identifier for issue."
    )
    extension: dict[str, Any] | None = Field(
        None, description="FHIR DomainResource extensions."
    )
