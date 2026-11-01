from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    AuditFields,
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRReference,
    PlainCodingRow,
)

from .category import PlainCommunicationCategory
from .identifier import PlainCommunicationIdentifier
from .note import FHIRCommunicationAnnotation, PlainCommunicationNote
from .payload import FHIRCommunicationPayload, PlainCommunicationPayload
from .reference import PlainCommunicationReference


# ── FHIR JSON ─────────────────────────────────────────────────────────────────


class FHIRCommunicationSchema(BaseModel):
    """FHIR R4 Communication resource schema."""

    model_config = ConfigDict(populate_by_name=True)

    resourceType: Literal["Communication"] = "Communication"
    id: str = Field(..., description="Logical ID of this artifact.")
    meta: FHIRMeta | None = Field(None, description="Metadata about the resource.")
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Unique identifier."
    )
    instantiatesCanonical: list[str] | None = Field(
        None, description="Instantiates FHIR protocol or definition."
    )
    instantiatesUri: list[str] | None = Field(
        None, description="Instantiates external protocol or definition."
    )
    basedOn: list[FHIRReference] | None = Field(
        None, description="Request fulfilled by this communication."
    )
    partOf: list[FHIRReference] | None = Field(
        None, description="Part of this action."
    )
    inResponseTo: list[FHIRReference] | None = Field(
        None, description="Reply to previous communication."
    )
    status: str = Field(
        ...,
        description="preparation | in-progress | not-done | on-hold | stopped | completed | entered-in-error | unknown.",
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
    medium: list[FHIRCodeableConcept] | None = Field(
        None, description="A channel of communication."
    )
    subject: FHIRReference | None = Field(
        None, description="Focus of message."
    )
    topic: FHIRCodeableConcept | None = Field(
        None, description="Description of the purpose/content."
    )
    about: list[FHIRReference] | None = Field(
        None, description="Resources that pertain to this communication."
    )
    encounter: FHIRReference | None = Field(
        None, description="Encounter created as part of."
    )
    sent: str | None = Field(
        None, description="When sent."
    )
    received: str | None = Field(
        None, description="When received."
    )
    recipient: list[FHIRReference] | None = Field(
        None, description="Message recipient."
    )
    sender: FHIRReference | None = Field(
        None, description="Message sender."
    )
    reasonCode: list[FHIRCodeableConcept] | None = Field(
        None, description="Indication for communication."
    )
    reasonReference: list[FHIRReference] | None = Field(
        None, description="Why was communication done?."
    )
    payload: list[FHIRCommunicationPayload] | None = Field(
        None, description="Message payload."
    )
    note: list[FHIRCommunicationAnnotation] | None = Field(
        None, description="Comments made about the communication."
    )
    extension: list[dict[str, Any]] | None = Field(
        None, description="FHIR extensions."
    )


class FHIRCommunicationBundleEntry(BaseModel):
    resource: FHIRCommunicationSchema


class FHIRCommunicationBundle(FHIRBundle):
    entry: list[FHIRCommunicationBundleEntry] | None = None


# ── Plain (snake_case) ─────────────────────────────────────────────────────────


class PlainCommunicationResponse(AuditFields):
    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Public communication_id.")
    instantiates_canonical: list[str] | None = None
    instantiates_uri: list[str] | None = None
    status: str = Field(..., description="Current status of the communication.")
    status_reason_text: str | None = None
    status_reason_codings: list[PlainCodingRow] | None = None
    priority: str | None = None
    subject_reference: str | None = None
    subject: str | None = None
    subject_type: str | None = None
    subject_id: int | None = None
    subject_display: str | None = None
    topic_text: str | None = None
    topic_codings: list[PlainCodingRow] | None = None
    encounter_reference: str | None = None
    encounter: str | None = None
    encounter_type: str | None = None
    encounter_id: int | None = None
    encounter_display: str | None = None
    sent: str | None = None
    received: str | None = None
    sender_reference: str | None = None
    sender: str | None = None
    sender_type: str | None = None
    sender_id: int | None = None
    sender_display: str | None = None
    identifier: list[PlainCommunicationIdentifier] | None = None
    based_on: list[PlainCommunicationReference] | None = None
    part_of: list[PlainCommunicationReference] | None = None
    in_response_to: list[PlainCommunicationReference] | None = None
    category: list[PlainCommunicationCategory] | None = None
    medium: list[PlainCommunicationCategory] | None = None
    about: list[PlainCommunicationReference] | None = None
    recipient: list[PlainCommunicationReference] | None = None
    reason_code: list[PlainCommunicationCategory] | None = None
    reason_reference: list[PlainCommunicationReference] | None = None
    payload: list[PlainCommunicationPayload] | None = None
    note: list[PlainCommunicationNote] | None = None
    extension: list[dict[str, Any]] | None = None


class PaginatedCommunicationResponse(BaseModel):
    """Paginated plain snake_case response."""

    total: int
    limit: int
    offset: int
    data: list[PlainCommunicationResponse]
