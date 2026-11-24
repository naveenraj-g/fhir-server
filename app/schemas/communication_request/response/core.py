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


class FHIRCommunicationRequestPayload(BaseModel):
    contentString: str | None = Field(None, description="content[x]: a string.")
    contentAttachment: dict | None = Field(
        None, description="content[x]: an Attachment."
    )
    contentReference: FHIRReference | None = Field(
        None, description="content[x]: a Reference(Any)."
    )


class FHIRCommunicationRequestSchema(BaseModel):
    resourceType: str = Field(
        "CommunicationRequest", description="Always 'CommunicationRequest'."
    )
    id: str = Field(..., description="Public communication_request_id as a string.")
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
    basedOn: list[FHIRReference] | None = Field(
        None, description="Fulfills plan or proposal."
    )
    replaces: list[FHIRReference] | None = Field(
        None, description="Request(s) replaced by this request."
    )
    groupIdentifier: FHIRIdentifier | None = Field(
        None, description="Composite request this is part of."
    )
    status: str | None = Field(
        None,
        description="draft | active | on-hold | revoked | completed | entered-in-error | unknown.",
    )
    statusReason: FHIRCodeableConcept | None = Field(
        None, description="Reason for current status."
    )
    category: list[FHIRCodeableConcept] | None = Field(
        None, description="Message category."
    )
    priority: str | None = Field(None, description="routine | urgent | asap | stat.")
    doNotPerform: bool | None = Field(
        None,
        description="True if the request is asking for the communication NOT to occur.",
    )
    medium: list[FHIRCodeableConcept] | None = Field(
        None, description="A channel of communication."
    )
    subject: FHIRReference | None = Field(None, description="Focus of message.")
    about: list[FHIRReference] | None = Field(
        None, description="Resources that pertain to this communication."
    )
    encounter: FHIRReference | None = Field(
        None, description="Encounter created as part of."
    )
    payload: list[FHIRCommunicationRequestPayload] | None = Field(
        None, description="Message payload."
    )
    occurrenceDateTime: str | None = Field(
        None, description="occurrence[x]: when scheduled."
    )
    occurrencePeriod: dict | None = Field(
        None, description="occurrence[x]: when scheduled."
    )
    authoredOn: str | None = Field(
        None, description="When request transitioned to being actionable."
    )
    requester: FHIRReference | None = Field(
        None, description="Who/what is requesting service."
    )
    recipient: list[FHIRReference] | None = Field(
        None, description="Message recipient."
    )
    sender: FHIRReference | None = Field(None, description="Message sender.")
    reasonCode: list[FHIRCodeableConcept] | None = Field(
        None, description="Why is communication needed?"
    )
    reasonReference: list[FHIRReference] | None = Field(
        None, description="Why is communication needed?"
    )
    note: list[FHIRAnnotation] | None = Field(
        None, description="Comments made about the request."
    )


class FHIRCommunicationRequestBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRCommunicationRequestSchema | dict = Field(
        ...,
        description="A CommunicationRequest (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included resource (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRCommunicationRequestBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRCommunicationRequestBundleEntry] | None = None
