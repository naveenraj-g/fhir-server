from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    AuditFields,
    FHIRAttachment,
    FHIRBundle,
    FHIRBundleEntry,
    FHIRCoding,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
    PlainAttachmentRow,
    PlainCodingRow,
)


class FHIRDocumentReferenceRelatesTo(BaseModel):
    """FHIR R4 DocumentReference.relatesTo."""

    code: str = Field(..., description="replaces | transforms | signs | appends.")
    target: FHIRReference = Field(..., description="Target of the relationship.")


class FHIRDocumentReferenceContent(BaseModel):
    """FHIR R4 DocumentReference.content."""

    attachment: FHIRAttachment = Field(..., description="Where to access the document.")
    format: FHIRCoding | None = Field(None, description="Format/content rules for the document.")


class FHIRDocumentReferenceContext(BaseModel):
    """FHIR R4 DocumentReference.context."""

    encounter: list[FHIRReference] | None = Field(None, description="Context of the document content.")
    event: list[FHIRCodeableConcept] | None = Field(None, description="Main clinical acts being documented.")
    period: FHIRPeriod | None = Field(None, description="Time of service that is being documented.")
    facilityType: FHIRCodeableConcept | None = Field(None, description="Kind of organization where admission occurred.")
    practiceSetting: FHIRCodeableConcept | None = Field(None, description="Additional details about where the content was created.")
    sourcePatientInfo: FHIRReference | None = Field(None, description="Patient demographics from source.")
    related: list[FHIRReference] | None = Field(None, description="Related identifiers or resources.")


class FHIRDocumentReferenceSchema(BaseModel):
    """FHIR R4 DocumentReference resource representation."""

    resourceType: Literal["DocumentReference"] = Field("DocumentReference", description="Always 'DocumentReference'.")
    id: str = Field(..., description="Public document_reference_id as a string.")
    meta: FHIRMeta | None = Field(None, description="Resource metadata.")
    extension: list[dict] | None = Field(None, description="Resource extensions.")
    masterIdentifier: FHIRIdentifier | None = Field(None, description="Master business identifier.")
    identifier: list[FHIRIdentifier] | None = Field(None, description="Other identifiers for the document.")
    status: str = Field(..., description="current | superseded | entered-in-error.")
    docStatus: str | None = Field(None, description="preliminary | final | amended | entered-in-error.")
    type: FHIRCodeableConcept | None = Field(None, description="Kind of document.")
    category: list[FHIRCodeableConcept] | None = Field(None, description="Categorization of document.")
    subject: FHIRReference | None = Field(None, description="Who/what is the subject of the document.")
    date: str | None = Field(None, description="When this document reference was created.")
    author: list[FHIRReference] | None = Field(None, description="Who and/or what authored the document.")
    authenticator: FHIRReference | None = Field(None, description="Who/what authenticated the document.")
    custodian: FHIRReference | None = Field(None, description="Organization which maintains the document.")
    relatesTo: list[FHIRDocumentReferenceRelatesTo] | None = Field(None, description="Relationships to other documents.")
    description: str | None = Field(None, description="Human-readable description.")
    securityLabel: list[FHIRCodeableConcept] | None = Field(None, description="Document security-tags.")
    content: list[FHIRDocumentReferenceContent] = Field(..., description="Document referenced (1..*).")
    context: FHIRDocumentReferenceContext | None = Field(None, description="Clinical context of document.")


class FHIRDocumentReferenceBundleEntry(FHIRBundleEntry):
    resource: FHIRDocumentReferenceSchema = Field(..., description="DocumentReference resource.")


class FHIRDocumentReferenceBundle(FHIRBundle):
    entry: list[FHIRDocumentReferenceBundleEntry] | None = Field(None, description="Bundle entries.")


# ── Plain Response Schemas (snake_case) ──────────────────────────────────────────


class PlainCodeableConcept(BaseModel):
    text: str | None = None
    coding: list[PlainCodingRow] | None = None


class PlainReference(BaseModel):
    reference: str | None = None
    type: str | None = None
    id: int | None = None
    display: str | None = None


class PlainDocumentReferenceIdentifier(BaseModel):
    id: int | None = None
    use: str | None = None
    system: str | None = None
    value: str | None = None
    type_text: str | None = None
    type_coding: list[PlainCodingRow] | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    assigner_reference: str | None = None
    assigner_type: str | None = None
    assigner_id: int | None = None
    assigner_display: str | None = None
    assigner_identifier_use: str | None = None
    assigner_identifier_system: str | None = None
    assigner_identifier_value: str | None = None
    assigner_identifier_type_text: str | None = None


class PlainDocumentReferenceRelatesTo(BaseModel):
    id: int | None = None
    code: str
    target_reference: str | None = None
    target_type: str | None = None
    target_id: int | None = None
    target_display: str | None = None


class PlainDocumentReferenceContent(BaseModel):
    id: int | None = None
    attachment: PlainAttachmentRow | None = None
    format: PlainCodingRow | None = None


class PlainDocumentReferenceContext(BaseModel):
    encounter: list[PlainReference] | None = None
    event: list[PlainCodeableConcept] | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    facility_type: PlainCodeableConcept | None = None
    practice_setting: PlainCodeableConcept | None = None
    source_patient_info: PlainReference | None = None
    related: list[PlainReference] | None = None


class PlainDocumentReferenceResponse(AuditFields):
    """Plain snake_case response for DocumentReference."""

    id: int = Field(..., description="Public document_reference_id.")
    master_identifier: PlainDocumentReferenceIdentifier | None = None
    identifier: list[PlainDocumentReferenceIdentifier] | None = None
    status: str
    doc_status: str | None = None
    type: PlainCodeableConcept | None = None
    category: list[PlainCodeableConcept] | None = None
    subject: PlainReference | None = None
    date: datetime | None = None
    author: list[PlainReference] | None = None
    authenticator: PlainReference | None = None
    custodian: PlainReference | None = None
    relates_to: list[PlainDocumentReferenceRelatesTo] | None = None
    description: str | None = None
    security_label: list[PlainCodeableConcept] | None = None
    content: list[PlainDocumentReferenceContent]
    context: PlainDocumentReferenceContext | None = None


class PaginatedDocumentReferenceResponse(BaseModel):
    """Paginated plain snake_case response."""

    total: int | None = None
    limit: int
    offset: int
    data: list[PlainDocumentReferenceResponse]
