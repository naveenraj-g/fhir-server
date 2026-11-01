from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.document_reference.input.codeable_concept import (
    DocumentReferenceCodeableConceptInput,
)
from app.schemas.document_reference.input.content import DocumentReferenceContentInput
from app.schemas.document_reference.input.context import DocumentReferenceContextInput
from app.schemas.document_reference.input.identifier import DocumentReferenceIdentifierInput
from app.schemas.document_reference.input.reference import (
    DocumentReferenceReferenceInput,
)
from app.schemas.document_reference.input.relates_to import DocumentReferenceRelatesToInput
from app.schemas.enums import (
    DocumentReferenceDocStatus,
    DocumentReferenceStatus,
    IdentifierUse,
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
                            "content_type": "application/pdf",
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
    subject_display: str | None = Field(
        None, description="Display text for the subject reference."
    )
    subject_identifier_use: IdentifierUse | None = Field(None)
    subject_identifier_type_system: str | None = Field(None)
    subject_identifier_type_version: str | None = Field(None)
    subject_identifier_type_code: str | None = Field(None)
    subject_identifier_type_display: str | None = Field(None)
    subject_identifier_type_user_selected: bool | None = Field(None)
    subject_identifier_type_text: str | None = Field(None)
    subject_identifier_system: str | None = Field(None)
    subject_identifier_value: str | None = Field(None)
    subject_identifier_period_start: datetime | None = Field(None)
    subject_identifier_period_end: datetime | None = Field(None)

    date: datetime | None = Field(
        None, description="When this document reference was created."
    )
    author: list[DocumentReferenceReferenceInput | str] | None = Field(
        None, description="Who and/or what authored the document."
    )
    authenticator: str | None = Field(
        None, description="Who/what authenticated the document."
    )
    authenticator_display: str | None = Field(
        None, description="Display text for authenticator."
    )
    authenticator_identifier_use: IdentifierUse | None = Field(None)
    authenticator_identifier_type_system: str | None = Field(None)
    authenticator_identifier_type_version: str | None = Field(None)
    authenticator_identifier_type_code: str | None = Field(None)
    authenticator_identifier_type_display: str | None = Field(None)
    authenticator_identifier_type_user_selected: bool | None = Field(None)
    authenticator_identifier_type_text: str | None = Field(None)
    authenticator_identifier_system: str | None = Field(None)
    authenticator_identifier_value: str | None = Field(None)
    authenticator_identifier_period_start: datetime | None = Field(None)
    authenticator_identifier_period_end: datetime | None = Field(None)

    custodian: str | None = Field(
        None, description="Organization which maintains the document."
    )
    custodian_display: str | None = Field(
        None, description="Display text for custodian."
    )
    custodian_identifier_use: IdentifierUse | None = Field(None)
    custodian_identifier_type_system: str | None = Field(None)
    custodian_identifier_type_version: str | None = Field(None)
    custodian_identifier_type_code: str | None = Field(None)
    custodian_identifier_type_display: str | None = Field(None)
    custodian_identifier_type_user_selected: bool | None = Field(None)
    custodian_identifier_type_text: str | None = Field(None)
    custodian_identifier_system: str | None = Field(None)
    custodian_identifier_value: str | None = Field(None)
    custodian_identifier_period_start: datetime | None = Field(None)
    custodian_identifier_period_end: datetime | None = Field(None)

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

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "status": "superseded",
                "doc_status": "final",
                "description": "Superseded consultation summary note",
            }
        },
    )

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
    subject_display: str | None = Field(
        None, description="Display text for the subject reference."
    )
    subject_identifier_use: IdentifierUse | None = None
    subject_identifier_type_system: str | None = None
    subject_identifier_type_version: str | None = None
    subject_identifier_type_code: str | None = None
    subject_identifier_type_display: str | None = None
    subject_identifier_type_user_selected: bool | None = None
    subject_identifier_type_text: str | None = None
    subject_identifier_system: str | None = None
    subject_identifier_value: str | None = None
    subject_identifier_period_start: datetime | None = None
    subject_identifier_period_end: datetime | None = None

    date: datetime | None = Field(
        None, description="When this document reference was created."
    )
    author: list[DocumentReferenceReferenceInput | str] | None = Field(
        None, description="Who and/or what authored the document."
    )
    authenticator: str | None = Field(
        None, description="Who/what authenticated the document."
    )
    authenticator_display: str | None = Field(
        None, description="Display text for authenticator."
    )
    authenticator_identifier_use: IdentifierUse | None = None
    authenticator_identifier_type_system: str | None = None
    authenticator_identifier_type_version: str | None = None
    authenticator_identifier_type_code: str | None = None
    authenticator_identifier_type_display: str | None = None
    authenticator_identifier_type_user_selected: bool | None = None
    authenticator_identifier_type_text: str | None = None
    authenticator_identifier_system: str | None = None
    authenticator_identifier_value: str | None = None
    authenticator_identifier_period_start: datetime | None = None
    authenticator_identifier_period_end: datetime | None = None

    custodian: str | None = Field(
        None, description="Organization which maintains the document."
    )
    custodian_display: str | None = Field(
        None, description="Display text for custodian."
    )
    custodian_identifier_use: IdentifierUse | None = None
    custodian_identifier_type_system: str | None = None
    custodian_identifier_type_version: str | None = None
    custodian_identifier_type_code: str | None = None
    custodian_identifier_type_display: str | None = None
    custodian_identifier_type_user_selected: bool | None = None
    custodian_identifier_type_text: str | None = None
    custodian_identifier_system: str | None = None
    custodian_identifier_value: str | None = None
    custodian_identifier_period_start: datetime | None = None
    custodian_identifier_period_end: datetime | None = None

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
