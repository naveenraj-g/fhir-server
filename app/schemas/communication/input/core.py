from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.communication.enums import (
    CommunicationPriority,
    CommunicationStatus,
)
from app.schemas.datatypes import CodingInput

from .category import CommunicationCategoryInput
from .identifier import CommunicationIdentifierInput
from .note import CommunicationNoteInput
from .payload import CommunicationPayloadInput
from .reference import CommunicationReferenceInput

_EXAMPLE = {
    "status": "completed",
    "priority": "routine",
    "category": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/communication-category",
                    "code": "notification",
                    "display": "Notification",
                }
            ],
            "text": "Notification",
        }
    ],
    "medium": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationMode",
                    "code": "WRITTEN",
                    "display": "written",
                }
            ],
            "text": "written",
        }
    ],
    "subject": "Patient/10001",
    "subject_display": "Jane Doe",
    "topic_text": "Annual Wellness Visit Follow-up",
    "sent": "2026-11-01T08:00:00Z",
    "received": "2026-11-01T08:01:00Z",
    "sender": "Practitioner/30001",
    "sender_display": "Dr. Smith",
    "recipient": [
        {"reference": "Patient/10001", "display": "Jane Doe"}
    ],
    "payload": [
        {
            "content_string": "Your recent lab test results are normal."
        }
    ],
}


class CommunicationCreateSchema(BaseModel):
    """Request body for POST /api/fhir/v1/communications.

    Communication is an org-scoped clinical entity and has no user_id.
    status is required per FHIR R4.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": _EXAMPLE},
    )

    identifier: list[CommunicationIdentifierInput] | None = Field(
        None, description="Unique identifier."
    )
    instantiates_canonical: list[str] | None = Field(
        None, description="Instantiates FHIR protocol or definition."
    )
    instantiates_uri: list[str] | None = Field(
        None, description="Instantiates external protocol or definition."
    )
    based_on: list[CommunicationReferenceInput | str] | None = Field(
        None, description="Request fulfilled by this communication (Reference(Resource))."
    )
    part_of: list[CommunicationReferenceInput | str] | None = Field(
        None, description="Part of this action (Reference(Resource))."
    )
    in_response_to: list[CommunicationReferenceInput | str] | None = Field(
        None, description="Reply to previous communication (Reference(Communication))."
    )
    status: CommunicationStatus = Field(
        ...,
        description="preparation | in-progress | not-done | on-hold | stopped | completed | entered-in-error | unknown.",
    )
    status_reason_text: str | None = Field(
        None, description="Reason for current status (plain text)."
    )
    status_reason_coding: list[CodingInput] | None = Field(
        None, description="Reason for current status (codings)."
    )
    category: list[CommunicationCategoryInput] | None = Field(
        None, description="Message category."
    )
    priority: CommunicationPriority | None = Field(
        None, description="routine | urgent | asap | stat."
    )
    medium: list[CommunicationCategoryInput] | None = Field(
        None, description="A channel of communication."
    )
    subject: str | None = Field(
        None, description="Focus of message (Reference(Patient | Group))."
    )
    subject_display: str | None = Field(
        None, description="Display narrative for subject reference."
    )
    topic_text: str | None = Field(
        None, description="Description of the purpose/content (plain text)."
    )
    topic_coding: list[CodingInput] | None = Field(
        None, description="Description of the purpose/content (codings)."
    )
    about: list[CommunicationReferenceInput | str] | None = Field(
        None, description="Resources that pertain to this communication (Reference(Resource))."
    )
    encounter: str | None = Field(
        None, description="Encounter created as part of (Reference(Encounter))."
    )
    encounter_display: str | None = Field(
        None, description="Display narrative for encounter reference."
    )
    sent: datetime | None = Field(
        None, description="When sent."
    )
    received: datetime | None = Field(
        None, description="When received."
    )
    recipient: list[CommunicationReferenceInput | str] | None = Field(
        None, description="Message recipient (Reference(Device | Organization | Patient | Practitioner | PractitionerRole | RelatedPerson | Group | CareTeam | HealthcareService))."
    )
    sender: str | None = Field(
        None, description="Message sender (Reference(Device | Organization | Patient | Practitioner | PractitionerRole | RelatedPerson | HealthcareService))."
    )
    sender_display: str | None = Field(
        None, description="Display narrative for sender reference."
    )
    reason_code: list[CommunicationCategoryInput] | None = Field(
        None, description="Indication for communication."
    )
    reason_reference: list[CommunicationReferenceInput | str] | None = Field(
        None, description="Why was communication done? (Reference(Condition | Observation | DiagnosticReport | DocumentReference))."
    )
    payload: list[CommunicationPayloadInput] | None = Field(
        None, description="Message payload."
    )
    note: list[CommunicationNoteInput] | None = Field(
        None, description="Comments made about the communication."
    )
    extension: list[dict[str, Any]] | None = Field(
        None, description="FHIR extensions."
    )


class CommunicationPatchSchema(BaseModel):
    """Request body for PATCH /api/fhir/v1/communications/{id}.

    All fields are optional; exclude immutable fields.
    """

    model_config = ConfigDict(extra="forbid")

    identifier: list[CommunicationIdentifierInput] | None = None
    instantiates_canonical: list[str] | None = None
    instantiates_uri: list[str] | None = None
    based_on: list[CommunicationReferenceInput | str] | None = None
    part_of: list[CommunicationReferenceInput | str] | None = None
    in_response_to: list[CommunicationReferenceInput | str] | None = None
    status: CommunicationStatus | None = None
    status_reason_text: str | None = None
    status_reason_coding: list[CodingInput] | None = None
    category: list[CommunicationCategoryInput] | None = None
    priority: CommunicationPriority | None = None
    medium: list[CommunicationCategoryInput] | None = None
    subject: str | None = None
    subject_display: str | None = None
    topic_text: str | None = None
    topic_coding: list[CodingInput] | None = None
    about: list[CommunicationReferenceInput | str] | None = None
    encounter: str | None = None
    encounter_display: str | None = None
    sent: datetime | None = None
    received: datetime | None = None
    recipient: list[CommunicationReferenceInput | str] | None = None
    sender: str | None = None
    sender_display: str | None = None
    reason_code: list[CommunicationCategoryInput] | None = None
    reason_reference: list[CommunicationReferenceInput | str] | None = None
    payload: list[CommunicationPayloadInput] | None = None
    note: list[CommunicationNoteInput] | None = None
    extension: list[dict[str, Any]] | None = None
