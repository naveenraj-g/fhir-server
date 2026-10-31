from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import IdentifierUse
from app.schemas.datatypes import (
    AuditFields,
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
    PlainCodingRow,
)

from .category import PlainCommunicationRequestCategory
from .identifier import PlainCommunicationRequestIdentifier
from .note import FHIRCommunicationRequestAnnotation, PlainCommunicationRequestNote
from .payload import FHIRCommunicationRequestPayload, PlainCommunicationRequestPayload
from .reference import PlainCommunicationRequestReference


# ── FHIR JSON ─────────────────────────────────────────────────────────────────


class FHIRCommunicationRequestSchema(BaseModel):
    """FHIR R4 CommunicationRequest resource schema."""

    model_config = ConfigDict(populate_by_name=True)

    resourceType: Literal["CommunicationRequest"] = "CommunicationRequest"
    id: str = Field(..., description="Logical ID of this artifact.")
    meta: FHIRMeta | None = Field(None, description="Metadata about the resource.")
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Unique identifier."
    )
    basedOn: list[FHIRReference] | None = Field(
        None, description="Fulfills plan or proposal."
    )
    replaces: list[FHIRReference] | None = Field(
        None, description="Request(s) replaced by this request."
    )
    groupIdentifier: FHIRIdentifier | None = Field(
        None, description="Composite request this is part of."
    )
    status: str = Field(
        ...,
        description="draft | active | on-hold | revoked | completed | entered-in-error | unknown.",
    )
    statusReason: FHIRCodeableConcept | None = Field(
        None, description="Reason for current status."
    )
    category: list[FHIRCodeableConcept] | None = Field(
        None, description="Message category."
    )
    priority: str | None = Field(
        None, description="routine | urgent | asap | stat."
    )
    doNotPerform: bool | None = Field(
        None, description="True if request is prohibiting action rather than directing action."
    )
    medium: list[FHIRCodeableConcept] | None = Field(
        None, description="A channel of communication."
    )
    subject: FHIRReference | None = Field(
        None, description="Focus of message."
    )
    about: list[FHIRReference] | None = Field(
        None, description="Resources that pertain to this communication request."
    )
    encounter: FHIRReference | None = Field(
        None, description="Encounter created as part of."
    )
    payload: list[FHIRCommunicationRequestPayload] | None = Field(
        None, description="Message payload."
    )
    occurrenceDateTime: str | None = Field(
        None, description="When scheduled (dateTime)."
    )
    occurrencePeriod: FHIRPeriod | None = Field(
        None, description="When scheduled (period)."
    )
    authoredOn: str | None = Field(
        None, description="When request transitioned to being actionable."
    )
    requester: FHIRReference | None = Field(
        None, description="Who asked for notification."
    )
    recipient: list[FHIRReference] | None = Field(
        None, description="Message recipient."
    )
    sender: FHIRReference | None = Field(
        None, description="Message sender."
    )
    reasonCode: list[FHIRCodeableConcept] | None = Field(
        None, description="Why is communication needed?"
    )
    reasonReference: list[FHIRReference] | None = Field(
        None, description="Why is communication needed (Reference)."
    )
    note: list[FHIRCommunicationRequestAnnotation] | None = Field(
        None, description="Comments made about communication request."
    )
    extension: list[dict[str, Any]] | None = Field(
        None, description="FHIR extensions."
    )


class FHIRCommunicationRequestBundleEntry(BaseModel):
    resource: FHIRCommunicationRequestSchema


class FHIRCommunicationRequestBundle(FHIRBundle):
    entry: list[FHIRCommunicationRequestBundleEntry] | None = None


# ── Plain (snake_case) ─────────────────────────────────────────────────────────


class PlainCommunicationRequestResponse(AuditFields):
    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Public communication_request_id.")
    group_identifier_use: IdentifierUse | None = None
    group_identifier_system: str | None = None
    group_identifier_value: str | None = None
    group_identifier_period_start: str | None = None
    group_identifier_period_end: str | None = None
    group_identifier_assigner_reference: str | None = None
    group_identifier_assigner: str | None = None
    group_identifier_assigner_type: str | None = None
    group_identifier_assigner_id: int | None = None
    group_identifier_assigner_display: str | None = None
    status: str = Field(..., description="Current status of the communication request.")
    status_reason_text: str | None = None
    status_reason_codings: list[PlainCodingRow] | None = None
    priority: str | None = None
    do_not_perform: bool | None = None
    subject_reference: str | None = None
    subject: str | None = None
    subject_type: str | None = None
    subject_id: int | None = None
    subject_display: str | None = None
    encounter_reference: str | None = None
    encounter: str | None = None
    encounter_type: str | None = None
    encounter_id: int | None = None
    encounter_display: str | None = None
    occurrence_date_time: str | None = None
    occurrence_period_start: str | None = None
    occurrence_period_end: str | None = None
    authored_on: str | None = None
    requester_reference: str | None = None
    requester: str | None = None
    requester_type: str | None = None
    requester_id: int | None = None
    requester_display: str | None = None
    sender_reference: str | None = None
    sender: str | None = None
    sender_type: str | None = None
    sender_id: int | None = None
    sender_display: str | None = None
    identifier: list[PlainCommunicationRequestIdentifier] | None = None
    based_on: list[PlainCommunicationRequestReference] | None = None
    replaces: list[PlainCommunicationRequestReference] | None = None
    category: list[PlainCommunicationRequestCategory] | None = None
    medium: list[PlainCommunicationRequestCategory] | None = None
    about: list[PlainCommunicationRequestReference] | None = None
    payload: list[PlainCommunicationRequestPayload] | None = None
    recipient: list[PlainCommunicationRequestReference] | None = None
    reason_code: list[PlainCommunicationRequestCategory] | None = None
    reason_reference: list[PlainCommunicationRequestReference] | None = None
    note: list[PlainCommunicationRequestNote] | None = None
    extension: list[dict[str, Any]] | None = None


class PaginatedCommunicationRequestResponse(BaseModel):
    """Paginated plain snake_case response."""

    total: int
    limit: int
    offset: int
    data: list[PlainCommunicationRequestResponse]
