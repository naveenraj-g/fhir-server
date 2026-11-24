from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRReference,
)
from app.schemas.datatypes.annotation import FHIRAnnotation
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRCommunicationPayload(BaseModel):
    contentString: str | None = Field(None, description="content[x]: a string.")
    contentAttachment: dict | None = Field(
        None, description="content[x]: an Attachment."
    )
    contentReference: FHIRReference | None = Field(
        None, description="content[x]: a Reference(Any)."
    )


class FHIRCommunicationSchema(BaseModel):
    resourceType: str = Field("Communication", description="Always 'Communication'.")
    id: str = Field(..., description="Public communication_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
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
    partOf: list[FHIRReference] | None = Field(None, description="Part of this action.")
    inResponseTo: list[FHIRReference] | None = Field(None, description="Reply to.")
    status: str | None = Field(
        None,
        description="preparation | in-progress | not-done | on-hold | stopped | completed | entered-in-error | unknown.",
    )
    statusReason: FHIRCodeableConcept | None = Field(
        None, description="Reason for current status."
    )
    category: list[FHIRCodeableConcept] | None = Field(
        None, description="Message category."
    )
    priority: str | None = Field(None, description="routine | urgent | asap | stat.")
    medium: list[FHIRCodeableConcept] | None = Field(
        None, description="A channel of communication."
    )
    subject: FHIRReference | None = Field(None, description="Focus of message.")
    topic: FHIRCodeableConcept | None = Field(
        None, description="Description of the purpose/content."
    )
    about: list[FHIRReference] | None = Field(
        None, description="Resources that pertain to this communication."
    )
    encounter: FHIRReference | None = Field(
        None, description="Encounter created as part of."
    )
    sent: str | None = Field(None, description="When sent.")
    received: str | None = Field(None, description="When received.")
    recipient: list[FHIRReference] | None = Field(
        None, description="Message recipient."
    )
    sender: FHIRReference | None = Field(None, description="Message sender.")
    reasonCode: list[FHIRCodeableConcept] | None = Field(
        None, description="Indication for message."
    )
    reasonReference: list[FHIRReference] | None = Field(
        None, description="Why was communication done?"
    )
    payload: list[FHIRCommunicationPayload] | None = Field(
        None, description="Message payload."
    )
    note: list[FHIRAnnotation] | None = Field(
        None, description="Comments made about the communication."
    )


class FHIRCommunicationBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRCommunicationSchema | dict = Field(
        ...,
        description="A Communication (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included resource (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRCommunicationBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRCommunicationBundleEntry] | None = None
