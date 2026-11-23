from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRCoding,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
)
from app.schemas.datatypes.attachment import FHIRAttachment
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRDocumentReferenceRelatesTo(BaseModel):
    code: str | None = Field(
        None, description="replaces | transforms | signs | appends."
    )
    target: FHIRReference | None = Field(
        None, description="Target of the relationship."
    )


class FHIRDocumentReferenceContent(BaseModel):
    attachment: FHIRAttachment | None = Field(
        None, description="Where to access the document."
    )
    format: FHIRCoding | None = Field(
        None, description="Format/content rules for the document."
    )


class FHIRDocumentReferenceContext(BaseModel):
    encounter: list[FHIRReference] | None = Field(
        None, description="Context of the document content."
    )
    event: list[FHIRCodeableConcept] | None = Field(
        None, description="Main clinical acts documented."
    )
    period: FHIRPeriod | None = Field(
        None, description="Time of service that is being documented."
    )
    facilityType: FHIRCodeableConcept | None = Field(
        None, description="Kind of facility where patient was seen."
    )
    practiceSetting: FHIRCodeableConcept | None = Field(
        None, description="Additional details about where the content was created."
    )
    sourcePatientInfo: FHIRReference | None = Field(
        None, description="Patient demographics from source."
    )
    related: list[FHIRReference] | None = Field(
        None, description="Related identifiers or resources."
    )


class FHIRDocumentReferenceSchema(BaseModel):
    resourceType: str = Field(
        "DocumentReference", description="Always 'DocumentReference'."
    )
    id: str = Field(..., description="Public document_reference_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    masterIdentifier: FHIRIdentifier | None = Field(
        None, description="Master Version Specific Identifier."
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Other identifiers for the document."
    )
    status: str | None = Field(
        None, description="current | superseded | entered-in-error."
    )
    docStatus: str | None = Field(
        None, description="preliminary | final | amended | entered-in-error."
    )
    type: FHIRCodeableConcept | None = Field(None, description="Kind of document.")
    category: list[FHIRCodeableConcept] | None = Field(
        None, description="Categorization of document."
    )
    subject: FHIRReference | None = Field(
        None, description="Who/what is the subject of the document."
    )
    date: str | None = Field(
        None, description="When this document reference was created."
    )
    author: list[FHIRReference] | None = Field(
        None, description="Who and/or what authored the document."
    )
    authenticator: FHIRReference | None = Field(
        None, description="Who/what authenticated the document."
    )
    custodian: FHIRReference | None = Field(
        None, description="Organization which maintains the document."
    )
    relatesTo: list[FHIRDocumentReferenceRelatesTo] | None = Field(
        None, description="Relationships to other documents."
    )
    description: str | None = Field(None, description="Human-readable description.")
    securityLabel: list[FHIRCodeableConcept] | None = Field(
        None, description="Document security-tags."
    )
    content: list[FHIRDocumentReferenceContent] | None = Field(
        None, description="Document referenced."
    )
    context: FHIRDocumentReferenceContext | None = Field(
        None, description="Clinical context of document."
    )


class FHIRDocumentReferenceBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRDocumentReferenceSchema | dict = Field(
        ...,
        description="A DocumentReference (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Patient / Group / Practitioner / PractitionerRole / RelatedPerson / Organization / Encounter / EpisodeOfCare / DocumentReference (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRDocumentReferenceBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRDocumentReferenceBundleEntry] | None = None
