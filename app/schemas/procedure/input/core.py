from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.procedure.enums import ProcedureStatus
from app.schemas.procedure.input.codeable_concept import (
    ProcedureCodeableConceptInput,
)
from app.schemas.procedure.input.focal_device import ProcedureFocalDeviceInput
from app.schemas.procedure.input.identifier import ProcedureIdentifierInput
from app.schemas.procedure.input.note import ProcedureNoteInput
from app.schemas.procedure.input.performer import ProcedurePerformerInput


class ProcedureCreateSchema(BaseModel):
    """Schema for creating a Procedure resource (POST /api/fhir/v1/procedures)."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "status": "completed",
                "code": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "80146002",
                            "display": "Appendectomy",
                        }
                    ],
                    "text": "Appendectomy",
                },
                "subject": "Patient/10001",
                "subject_display": "John Doe",
                "encounter": "Encounter/20001",
                "performed_date_time": "2026-10-15T14:30:00Z",
                "performer": [
                    {
                        "actor": "Practitioner/30001",
                        "actor_display": "Dr. Sarah Surgeon",
                        "function": {
                            "coding": [
                                {
                                    "system": "http://snomed.info/sct",
                                    "code": "304292004",
                                    "display": "Surgeon",
                                }
                            ],
                            "text": "Surgeon",
                        },
                    }
                ],
                "location": "Location/230001",
                "reason_code": [
                    {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "74400008",
                                "display": "Appendicitis",
                            }
                        ],
                        "text": "Acute Appendicitis",
                    }
                ],
                "outcome": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "385669000",
                            "display": "Successful",
                        }
                    ],
                    "text": "Successful",
                },
            }
        },
    )

    instantiates_canonical: list[str] | None = Field(
        None, description="Instantiates FHIR protocol or definition."
    )
    instantiates_uri: list[str] | None = Field(
        None, description="Instantiates external protocol or definition."
    )
    based_on: list[str] | None = Field(
        None, description="A request for this procedure (CarePlan | ServiceRequest)."
    )
    part_of: list[str] | None = Field(
        None, description="Part of referenced event (Procedure | Observation | MedicationAdministration)."
    )
    status: ProcedureStatus = Field(
        ...,
        description="preparation | in-progress | not-done | on-hold | stopped | completed | entered-in-error | unknown.",
    )
    status_reason: ProcedureCodeableConceptInput | None = Field(
        None, description="Reason for current status."
    )
    category: ProcedureCodeableConceptInput | None = Field(
        None, description="Classification of the procedure."
    )
    code: ProcedureCodeableConceptInput | None = Field(
        None, description="Identification of the procedure."
    )
    subject: str = Field(
        ...,
        description="Who the procedure was performed on (Patient | Group), e.g. Patient/10001.",
    )
    subject_display: str | None = Field(
        None, description="Plain text display for the subject."
    )
    encounter: str | None = Field(
        None, description="Encounter created as part of (e.g. Encounter/20001)."
    )
    encounter_display: str | None = Field(
        None, description="Plain text display for the encounter."
    )
    performed_date_time: datetime | None = Field(
        None, description="When the procedure was performed (dateTime)."
    )
    performed_period_start: datetime | None = Field(
        None, description="Start of period when procedure was performed."
    )
    performed_period_end: datetime | None = Field(
        None, description="End of period when procedure was performed."
    )
    performed_string: str | None = Field(
        None, description="When procedure was performed as human language."
    )
    performed_age: dict[str, Any] | None = Field(
        None, description="Age when procedure was performed."
    )
    performed_range: dict[str, Any] | None = Field(
        None, description="Range of ages or periods when procedure was performed."
    )
    recorder: str | None = Field(
        None, description="Who recorded the procedure (Patient | RelatedPerson | Practitioner | PractitionerRole)."
    )
    recorder_display: str | None = Field(
        None, description="Plain text display for recorder."
    )
    asserter: str | None = Field(
        None, description="Person who asserts this procedure (Patient | RelatedPerson | Practitioner | PractitionerRole)."
    )
    asserter_display: str | None = Field(
        None, description="Plain text display for asserter."
    )
    performer: list[ProcedurePerformerInput] | None = Field(
        None, description="The people/organizations/devices who performed the procedure."
    )
    location: str | None = Field(
        None, description="Where the procedure happened (e.g. Location/230001)."
    )
    location_display: str | None = Field(
        None, description="Plain text display for location."
    )
    reason_code: list[ProcedureCodeableConceptInput] | None = Field(
        None, description="Coded reason procedure performed."
    )
    reason_reference: list[str] | None = Field(
        None, description="The justification that the procedure was performed (Condition | Observation | Procedure | DiagnosticReport | DocumentReference)."
    )
    body_site: list[ProcedureCodeableConceptInput] | None = Field(
        None, description="Target body sites."
    )
    outcome: ProcedureCodeableConceptInput | None = Field(
        None, description="The result of procedure."
    )
    report: list[str] | None = Field(
        None, description="Any report resulting from the procedure (DiagnosticReport | DocumentReference | Composition)."
    )
    complication: list[ProcedureCodeableConceptInput] | None = Field(
        None, description="Complication following the procedure."
    )
    complication_detail: list[str] | None = Field(
        None, description="A condition that is a result of the procedure (Condition)."
    )
    follow_up: list[ProcedureCodeableConceptInput] | None = Field(
        None, description="Instructions for follow up."
    )
    note: list[ProcedureNoteInput] | None = Field(
        None, description="Additional information about the procedure."
    )
    focal_device: list[ProcedureFocalDeviceInput] | None = Field(
        None, description="Manipulated, implanted, or removed device."
    )
    used_reference: list[str] | None = Field(
        None, description="Items used during procedure (Device | Medication | Substance)."
    )
    used_code: list[ProcedureCodeableConceptInput] | None = Field(
        None, description="Coded items used during the procedure."
    )
    identifier: list[ProcedureIdentifierInput] | None = Field(
        None, description="External identifiers for this procedure."
    )
    extension: list[dict[str, Any]] | None = Field(
        None, description="May be used to represent additional information not part of the basic definition."
    )


class ProcedurePatchSchema(BaseModel):
    """Schema for updating a Procedure resource (PATCH /api/fhir/v1/procedures/{id})."""

    model_config = ConfigDict(extra="forbid")

    instantiates_canonical: list[str] | None = Field(None, description="Instantiates FHIR protocol or definition.")
    instantiates_uri: list[str] | None = Field(None, description="Instantiates external protocol or definition.")
    based_on: list[str] | None = Field(None, description="A request for this procedure.")
    part_of: list[str] | None = Field(None, description="Part of referenced event.")
    status: ProcedureStatus | None = Field(None, description="preparation | in-progress | not-done | on-hold | stopped | completed | entered-in-error | unknown.")
    status_reason: ProcedureCodeableConceptInput | None = Field(None, description="Reason for current status.")
    category: ProcedureCodeableConceptInput | None = Field(None, description="Classification of the procedure.")
    code: ProcedureCodeableConceptInput | None = Field(None, description="Identification of the procedure.")
    subject: str | None = Field(None, description="Who the procedure was performed on.")
    subject_display: str | None = Field(None, description="Plain text display for subject.")
    encounter: str | None = Field(None, description="Encounter created as part of.")
    encounter_display: str | None = Field(None, description="Plain text display for encounter.")
    performed_date_time: datetime | None = Field(None, description="When the procedure was performed.")
    performed_period_start: datetime | None = Field(None, description="Start of period.")
    performed_period_end: datetime | None = Field(None, description="End of period.")
    performed_string: str | None = Field(None, description="When procedure was performed.")
    performed_age: dict[str, Any] | None = Field(None, description="Age when performed.")
    performed_range: dict[str, Any] | None = Field(None, description="Range when performed.")
    recorder: str | None = Field(None, description="Who recorded the procedure.")
    recorder_display: str | None = Field(None, description="Plain text display for recorder.")
    asserter: str | None = Field(None, description="Person who asserts this procedure.")
    asserter_display: str | None = Field(None, description="Plain text display for asserter.")
    performer: list[ProcedurePerformerInput] | None = Field(None, description="The people who performed the procedure.")
    location: str | None = Field(None, description="Where the procedure happened.")
    location_display: str | None = Field(None, description="Plain text display for location.")
    reason_code: list[ProcedureCodeableConceptInput] | None = Field(None, description="Coded reason procedure performed.")
    reason_reference: list[str] | None = Field(None, description="The justification that the procedure was performed.")
    body_site: list[ProcedureCodeableConceptInput] | None = Field(None, description="Target body sites.")
    outcome: ProcedureCodeableConceptInput | None = Field(None, description="The result of procedure.")
    report: list[str] | None = Field(None, description="Any report resulting from the procedure.")
    complication: list[ProcedureCodeableConceptInput] | None = Field(None, description="Complication following the procedure.")
    complication_detail: list[str] | None = Field(None, description="A condition resulting from the procedure.")
    follow_up: list[ProcedureCodeableConceptInput] | None = Field(None, description="Instructions for follow up.")
    note: list[ProcedureNoteInput] | None = Field(None, description="Additional information about the procedure.")
    focal_device: list[ProcedureFocalDeviceInput] | None = Field(None, description="Manipulated device.")
    used_reference: list[str] | None = Field(None, description="Items used during procedure.")
    used_code: list[ProcedureCodeableConceptInput] | None = Field(None, description="Coded items used during the procedure.")
    identifier: list[ProcedureIdentifierInput] | None = Field(None, description="External identifiers for this procedure.")
    extension: list[dict[str, Any]] | None = Field(None, description="Extensions.")
