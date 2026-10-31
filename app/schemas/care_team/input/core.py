from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.care_team.input.codeable_concept import (
    CareTeamCodeableConceptInput,
)
from app.schemas.care_team.input.identifier import CareTeamIdentifierInput
from app.schemas.care_team.input.note import CareTeamNoteInput
from app.schemas.care_team.input.participant import CareTeamParticipantInput
from app.schemas.datatypes import ContactPointInput
from app.schemas.enums import CareTeamStatus


class CareTeamCreateSchema(BaseModel):
    """Request payload for POST /api/fhir/v1/care-teams/."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "status": "active",
                "name": "Diabetes Care Coordination Team",
                "subject": "Patient/10001",
                "subject_display": "Jane Doe",
                "period_start": "2026-01-01T00:00:00Z",
                "period_end": "2026-12-31T23:59:59Z",
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://loinc.org",
                                "code": "LA27976-2",
                                "display": "Longitudinal care-coordination",
                            }
                        ],
                        "text": "Longitudinal care-coordination",
                    }
                ],
                "participant": [
                    {
                        "role": [
                            {
                                "coding": [
                                    {
                                        "system": "http://snomed.info/sct",
                                        "code": "407543004",
                                        "display": "Primary care physician",
                                    }
                                ],
                                "text": "Primary care physician",
                            }
                        ],
                        "member": "Practitioner/30001",
                        "member_display": "Dr. Adam Careful",
                    }
                ],
                "reason_code": [
                    {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "44054006",
                                "display": "Diabetes mellitus type 2",
                            }
                        ],
                        "text": "Diabetes mellitus type 2",
                    }
                ],
                "reason_reference": ["Condition/120001"],
                "managing_organization": ["Organization/190001"],
                "telecom": [
                    {
                        "system": "phone",
                        "value": "555-555-5555",
                        "use": "work",
                    }
                ],
                "note": [
                    {
                        "text": "Initial care team established following diagnosis.",
                    }
                ],
            }
        },
    )

    status: CareTeamStatus | None = Field(
        None, description="proposed | active | suspended | inactive | entered-in-error."
    )
    category: list[CareTeamCodeableConceptInput] | None = Field(
        None, description="Type of team."
    )
    name: str | None = Field(
        None, description="Human-friendly name for the care team."
    )
    subject: str | None = Field(
        None, description="Who the care team is for (Patient | Group) as a FHIR reference string (e.g. 'Patient/10001')."
    )
    subject_display: str | None = Field(
        None, description="Display name for subject reference."
    )
    encounter: str | None = Field(
        None, description="Encounter created as part of (Reference(Encounter))."
    )
    encounter_display: str | None = Field(
        None, description="Display name for encounter reference."
    )
    period_start: datetime | None = Field(
        None, description="Time period team covers — start."
    )
    period_end: datetime | None = Field(
        None, description="Time period team covers — end."
    )
    participant: list[CareTeamParticipantInput] | None = Field(
        None, description="Members of the team."
    )
    reason_code: list[CareTeamCodeableConceptInput] | None = Field(
        None, description="Why the care team exists."
    )
    reason_reference: list[str] | None = Field(
        None, description="Why the care team exists (Reference(Condition))."
    )
    managing_organization: list[str] | None = Field(
        None, description="Organization responsible for the care team (Reference(Organization))."
    )
    telecom: list[ContactPointInput] | None = Field(
        None, description="A contact detail for the care team (that applies to all members)."
    )
    note: list[CareTeamNoteInput] | None = Field(
        None, description="Comments about the care team."
    )
    identifier: list[CareTeamIdentifierInput] | None = Field(
        None, description="External Ids for this team."
    )


class CareTeamPatchSchema(BaseModel):
    """Request payload for PATCH /api/fhir/v1/care-teams/{id}. All fields optional."""

    model_config = ConfigDict(extra="forbid")

    status: CareTeamStatus | None = Field(
        None, description="proposed | active | suspended | inactive | entered-in-error."
    )
    category: list[CareTeamCodeableConceptInput] | None = Field(
        None, description="Type of team."
    )
    name: str | None = Field(
        None, description="Human-friendly name for the care team."
    )
    subject: str | None = Field(
        None, description="Who the care team is for (Patient | Group) as a FHIR reference string (e.g. 'Patient/10001')."
    )
    subject_display: str | None = Field(
        None, description="Display name for subject reference."
    )
    encounter: str | None = Field(
        None, description="Encounter created as part of (Reference(Encounter))."
    )
    encounter_display: str | None = Field(
        None, description="Display name for encounter reference."
    )
    period_start: datetime | None = Field(
        None, description="Time period team covers — start."
    )
    period_end: datetime | None = Field(
        None, description="Time period team covers — end."
    )
    participant: list[CareTeamParticipantInput] | None = Field(
        None, description="Members of the team."
    )
    reason_code: list[CareTeamCodeableConceptInput] | None = Field(
        None, description="Why the care team exists."
    )
    reason_reference: list[str] | None = Field(
        None, description="Why the care team exists (Reference(Condition))."
    )
    managing_organization: list[str] | None = Field(
        None, description="Organization responsible for the care team (Reference(Organization))."
    )
    telecom: list[ContactPointInput] | None = Field(
        None, description="A contact detail for the care team (that applies to all members)."
    )
    note: list[CareTeamNoteInput] | None = Field(
        None, description="Comments about the care team."
    )
    identifier: list[CareTeamIdentifierInput] | None = Field(
        None, description="External Ids for this team."
    )
