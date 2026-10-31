from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.communication_request.enums import (
    CommunicationRequestPriority,
    CommunicationRequestStatus,
)
from app.models.enums import IdentifierUse
from app.schemas.datatypes import CodingInput

from .category import CommunicationRequestCategoryInput
from .identifier import CommunicationRequestIdentifierInput
from .note import CommunicationRequestNoteInput
from .payload import CommunicationRequestPayloadInput
from .reference import CommunicationRequestReferenceInput

_EXAMPLE = {
    "status": "active",
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
    "payload": [
        {
            "content_string": "Please provide update on recent lab results."
        }
    ],
    "authored_on": "2026-10-31T12:00:00Z",
    "requester": "Practitioner/30001",
    "requester_display": "Dr. Smith",
    "recipient": [
        {"reference": "Patient/10001", "display": "Jane Doe"}
    ],
}


class CommunicationRequestCreateSchema(BaseModel):
    """Request body for POST /api/fhir/v1/communication-requests.

    CommunicationRequest is an org-scoped clinical entity and has no user_id.
    status is required per FHIR R4.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": _EXAMPLE},
    )

    identifier: list[CommunicationRequestIdentifierInput] | None = Field(
        None, description="Unique identifier."
    )
    based_on: list[CommunicationRequestReferenceInput | str] | None = Field(
        None, description="Fulfills plan or proposal (Reference(Any))."
    )
    replaces: list[CommunicationRequestReferenceInput | str] | None = Field(
        None, description="Request(s) replaced by this request (Reference(CommunicationRequest))."
    )
    group_identifier_use: IdentifierUse | None = Field(
        None, description="Group identifier use."
    )
    group_identifier_system: str | None = Field(
        None, description="Group identifier system."
    )
    group_identifier_value: str | None = Field(
        None, description="Group identifier value."
    )
    group_identifier_period_start: datetime | None = Field(
        None, description="Group identifier validity start."
    )
    group_identifier_period_end: datetime | None = Field(
        None, description="Group identifier validity end."
    )
    group_identifier_assigner: str | None = Field(
        None, description="Group identifier assigner reference."
    )
    group_identifier_assigner_display: str | None = Field(
        None, description="Group identifier assigner display."
    )
    status: CommunicationRequestStatus = Field(
        ...,
        description="draft | active | on-hold | revoked | completed | entered-in-error | unknown.",
    )
    status_reason_coding: list[CodingInput] | None = Field(
        None, description="Reason for current status codings."
    )
    status_reason_text: str | None = Field(
        None, description="Reason for current status text."
    )
    category: list[CommunicationRequestCategoryInput] | None = Field(
        None, description="Message category (e.g. alert, notification, reminder)."
    )
    priority: CommunicationRequestPriority | None = Field(
        None, description="routine | urgent | asap | stat."
    )
    do_not_perform: bool | None = Field(
        None, description="True if request is prohibiting action rather than directing action."
    )
    medium: list[CommunicationRequestCategoryInput] | None = Field(
        None, description="A channel of communication."
    )
    subject: str | None = Field(
        None, description="Focus of message (Reference(Patient | Group))."
    )
    subject_display: str | None = Field(
        None, description="Plain text narrative for subject reference."
    )
    about: list[CommunicationRequestReferenceInput | str] | None = Field(
        None, description="Resources that pertain to this communication request."
    )
    encounter: str | None = Field(
        None, description="Encounter created as part of (Reference(Encounter))."
    )
    encounter_display: str | None = Field(
        None, description="Plain text narrative for encounter reference."
    )
    payload: list[CommunicationRequestPayloadInput] | None = Field(
        None, description="Message payload (string, Attachment, or Reference)."
    )
    occurrence_date_time: datetime | None = Field(
        None, description="When scheduled (dateTime)."
    )
    occurrence_period_start: datetime | None = Field(
        None, description="When scheduled (period start)."
    )
    occurrence_period_end: datetime | None = Field(
        None, description="When scheduled (period end)."
    )
    authored_on: datetime | None = Field(
        None, description="When request transitioned to being actionable."
    )
    requester: str | None = Field(
        None, description="Who asked for notification (Reference(Practitioner | PractitionerRole | Organization | Patient | RelatedPerson | Device))."
    )
    requester_display: str | None = Field(
        None, description="Plain text narrative for requester reference."
    )
    recipient: list[CommunicationRequestReferenceInput | str] | None = Field(
        None, description="Message recipient (Reference(Device | Organization | Patient | Practitioner | PractitionerRole | RelatedPerson | Group | CareTeam | HealthcareService))."
    )
    sender: str | None = Field(
        None, description="Message sender (Reference(Device | Organization | Patient | Practitioner | PractitionerRole | RelatedPerson | HealthcareService))."
    )
    sender_display: str | None = Field(
        None, description="Plain text narrative for sender reference."
    )
    reason_code: list[CommunicationRequestCategoryInput] | None = Field(
        None, description="Why is communication needed?"
    )
    reason_reference: list[CommunicationRequestReferenceInput | str] | None = Field(
        None, description="Why is communication needed (Reference(Condition | Observation | DiagnosticReport | DocumentReference))."
    )
    note: list[CommunicationRequestNoteInput] | None = Field(
        None, description="Comments made about communication request."
    )
    extension: list[dict[str, Any]] | None = Field(
        None, description="FHIR extensions."
    )


class CommunicationRequestPatchSchema(BaseModel):
    """Request body for PATCH /api/fhir/v1/communication-requests/{id}.

    All fields optional; set to None or omit to leave unchanged.
    """

    model_config = ConfigDict(extra="forbid")

    identifier: list[CommunicationRequestIdentifierInput] | None = None
    based_on: list[CommunicationRequestReferenceInput | str] | None = None
    replaces: list[CommunicationRequestReferenceInput | str] | None = None
    group_identifier_use: IdentifierUse | None = None
    group_identifier_system: str | None = None
    group_identifier_value: str | None = None
    group_identifier_period_start: datetime | None = None
    group_identifier_period_end: datetime | None = None
    group_identifier_assigner: str | None = None
    group_identifier_assigner_display: str | None = None
    status: CommunicationRequestStatus | None = None
    status_reason_coding: list[CodingInput] | None = None
    status_reason_text: str | None = None
    category: list[CommunicationRequestCategoryInput] | None = None
    priority: CommunicationRequestPriority | None = None
    do_not_perform: bool | None = None
    medium: list[CommunicationRequestCategoryInput] | None = None
    subject: str | None = None
    subject_display: str | None = None
    about: list[CommunicationRequestReferenceInput | str] | None = None
    encounter: str | None = None
    encounter_display: str | None = None
    payload: list[CommunicationRequestPayloadInput] | None = None
    occurrence_date_time: datetime | None = None
    occurrence_period_start: datetime | None = None
    occurrence_period_end: datetime | None = None
    authored_on: datetime | None = None
    requester: str | None = None
    requester_display: str | None = None
    recipient: list[CommunicationRequestReferenceInput | str] | None = None
    sender: str | None = None
    sender_display: str | None = None
    reason_code: list[CommunicationRequestCategoryInput] | None = None
    reason_reference: list[CommunicationRequestReferenceInput | str] | None = None
    note: list[CommunicationRequestNoteInput] | None = None
    extension: list[dict[str, Any]] | None = None
