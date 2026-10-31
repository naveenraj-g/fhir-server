from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.document_reference.input.codeable_concept import (
    DocumentReferenceCodeableConceptInput,
)
from app.schemas.document_reference.input.content import DocumentReferenceContentInput
from app.schemas.document_reference.input.context import DocumentReferenceContextInput
from app.schemas.document_reference.input.identifier import DocumentReferenceIdentifierInput
from app.schemas.document_reference.input.relates_to import DocumentReferenceRelatesToInput
from app.schemas.enums import (
    DocumentReferenceDocStatus,
    DocumentReferenceStatus,
)


class DocumentReferenceCreateSchema(BaseModel):
    """Payload for POST /api/fhir/v1/document-references.

    Tenant scoping (org_id) and created_by come from the verified JWT (actor.org_id / actor.sub).
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "status": "current",
                "doc_status": "preliminary",
                "type": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "34108-1",
                            "display": "Outpatient Note",
                        }
                    ],
                    "text": "Outpatient Note",
                },
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://hl7.org/fhir/us/core/CodeSystem/us-core-documentreference-category",
                                "code": "clinical-note",
                                "display": "Clinical Note",
                            }
                        ],
                        "text": "Clinical Note",
                    }
                ],
                "subject": "Patient/10001",
                "date": "2026-10-30T10:00:00Z",
                "author": ["Practitioner/30001"],
                "authenticator": "Practitioner/30001",
                "custodian": "Organization/190001",
                "description": "Consultation summary note",
                "content": [
                    {
                        "attachment": {
                            "contentType": "application/pdf",
                            "language": "en",
                            "url": "http://example.org/documents/note-123.pdf",
                            "title": "Consultation Note PDF",
                        },
                        "format": {
                            "system": "http://ihe.net/fhir/ValueSet/IHE.FormatCode.codesystem",
                            "code": "urn:ihe:pcc:xphr:2007",
                            "display": "HL7 CDA Personal Health Monitoring Report",
                        },
                    }
                ],
            }
        },
    )

    master_identifier: DocumentReferenceIdentifierInput | None = Field(
        None, description="Master business identifier."
    )
    identifier: list[DocumentReferenceIdentifierInput] | None = Field(
        None, description="Other identifiers for the document."
    )
    status: DocumentReferenceStatus = Field(
        ..., description="current | superseded | entered-in-error."
    )
    doc_status: DocumentReferenceDocStatus | None = Field(
        None, description="preliminary | final | amended | entered-in-error."
    )
    type: DocumentReferenceCodeableConceptInput | None = Field(
        None, description="Kind of document (LOINC if possible)."
    )
    category: list[DocumentReferenceCodeableConceptInput] | None = Field(
        None, description="Categorization of document."
    )
    subject: str | None = Field(
        None, description="Who/what is the subject of the document (Patient/Practitioner/Group/Device)."
    )
    date: datetime | None = Field(
        None, description="When this document reference was created."
    )
    author: list[str] | None = Field(
        None, description="Who and/or what authored the document."
    )
    authenticator: str | None = Field(
        None, description="Who/what authenticated the document."
    )
    custodian: str | None = Field(
        None, description="Organization which maintains the document."
    )
    relates_to: list[DocumentReferenceRelatesToInput] | None = Field(
        None, description="Relationships to other documents."
    )
    description: str | None = Field(
        None, description="Human-readable description."
    )
    security_label: list[DocumentReferenceCodeableConceptInput] | None = Field(
        None, description="Document security-tags."
    )
    content: list[DocumentReferenceContentInput] = Field(
        ..., min_length=1, description="Document referenced (1..* in FHIR R4)."
    )
    context: DocumentReferenceContextInput | None = Field(
        None, description="Clinical context of document."
    )


class DocumentReferencePatchSchema(BaseModel):
    """Payload for PATCH /api/fhir/v1/document-references/{document_reference_id}.
    All fields are optional; omitted fields are left untouched.
    """

    model_config = ConfigDict(extra="forbid")

    master_identifier: DocumentReferenceIdentifierInput | None = Field(
        None, description="Master business identifier."
    )
    identifier: list[DocumentReferenceIdentifierInput] | None = Field(
        None, description="Other identifiers for the document."
    )
    status: DocumentReferenceStatus | None = Field(
        None, description="current | superseded | entered-in-error."
    )
    doc_status: DocumentReferenceDocStatus | None = Field(
        None, description="preliminary | final | amended | entered-in-error."
    )
    type: DocumentReferenceCodeableConceptInput | None = Field(
        None, description="Kind of document (LOINC if possible)."
    )
    category: list[DocumentReferenceCodeableConceptInput] | None = Field(
        None, description="Categorization of document."
    )
    subject: str | None = Field(
        None, description="Who/what is the subject of the document."
    )
    date: datetime | None = Field(
        None, description="When this document reference was created."
    )
    author: list[str] | None = Field(
        None, description="Who and/or what authored the document."
    )
    authenticator: str | None = Field(
        None, description="Who/what authenticated the document."
    )
    custodian: str | None = Field(
        None, description="Organization which maintains the document."
    )
    relates_to: list[DocumentReferenceRelatesToInput] | None = Field(
        None, description="Relationships to other documents."
    )
    description: str | None = Field(
        None, description="Human-readable description."
    )
    security_label: list[DocumentReferenceCodeableConceptInput] | None = Field(
        None, description="Document security-tags."
    )
    content: list[DocumentReferenceContentInput] | None = Field(
        None, min_length=1, description="Document referenced."
    )
    context: DocumentReferenceContextInput | None = Field(
        None, description="Clinical context of document."
    )
