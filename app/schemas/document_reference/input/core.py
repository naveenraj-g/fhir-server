from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirAttachmentInput,
    FhirCodeableConceptInput,
    FhirCodingInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

# document-reference-status (the required binding of DocumentReference.status).
StatusCode = Literal["current", "superseded", "entered-in-error"]
# composition-status (the required binding of DocumentReference.docStatus).
DocStatusCode = Literal["preliminary", "final", "amended", "entered-in-error"]
# document-relationship-type (the required binding of DocumentReference.relatesTo.code).
RelationCode = Literal["replaces", "transforms", "signs", "appends"]

_EXAMPLE = {
    "resourceType": "DocumentReference",
    "masterIdentifier": {
        "system": "urn:ietf:rfc:3986",
        "value": "urn:oid:1.2.840.113556.1.8000.2554.58783.21864",
    },
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/document-reference-id",
            "value": "DOC-1001",
        }
    ],
    "status": "current",
    "docStatus": "final",
    "type": {
        "coding": [
            {
                "system": "http://loinc.org",
                "code": "34133-9",
                "display": "Summarization of episode note",
            }
        ]
    },
    "category": [
        {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "LP173421-1",
                    "display": "Report",
                }
            ]
        }
    ],
    "subject": {"reference": "Patient/10001"},
    "date": "2026-02-01T10:00:00Z",
    "author": [{"reference": "Practitioner/30001"}],
    "custodian": {"reference": "Organization/190001"},
    "description": "Discharge summary",
    "content": [
        {
            "attachment": {
                "contentType": "application/pdf",
                "language": "en",
                "url": "https://documents.example.org/doc-1001.pdf",
                "title": "Discharge summary",
            },
            "format": {
                "system": "http://ihe.net/fhir/ValueSet/IHE.FormatCode.codesystem",
                "code": "urn:ihe:pcc:handp:2008",
            },
        }
    ],
    "context": {
        "encounter": [{"reference": "Encounter/20001"}],
        "period": {"start": "2026-01-30", "end": "2026-02-01"},
    },
}


class DocumentReferenceRelatesToInput(FhirInputModel):
    """DocumentReference.relatesTo - relationships to other documents."""

    code: RelationCode | None = Field(
        None,
        description="replaces | transforms | signs | appends (required by R4). Searched by `relation`.",
    )
    target: FhirReferenceInput | None = Field(
        None,
        description="Target of the relationship - Reference(DocumentReference), required by R4. A relative reference must exist in the caller's org (422 otherwise). Searched by `relatesto`; `relationship` pairs it with `code`.",
    )


class DocumentReferenceContentInput(FhirInputModel):
    """DocumentReference.content - the document and format."""

    attachment: FhirAttachmentInput | None = Field(
        None,
        description="Where to access the document (required by R4). `contentType` is searched by `contenttype`, `language` by `language` and `url` by `location`.",
    )
    format: FhirCodingInput | None = Field(
        None,
        description="Format/content rules for the document. Searched by `format`.",
    )


class DocumentReferenceContextInput(FhirInputModel):
    """DocumentReference.context - clinical context of the document."""

    encounter: list[FhirReferenceInput] | None = Field(
        None,
        description="Context of the document content - Reference(Encounter | EpisodeOfCare). A relative reference must exist in the caller's org (422 otherwise). Searched by `encounter`.",
    )
    event: list[FhirCodeableConceptInput] | None = Field(
        None, description="Main clinical acts documented. Searched by `event`."
    )
    period: FhirPeriodInput | None = Field(
        None,
        description="Time of service that is being documented. Searched by `period`.",
    )
    facilityType: FhirCodeableConceptInput | None = Field(
        None,
        description="Kind of facility where patient was seen. Searched by `facility`.",
    )
    practiceSetting: FhirCodeableConceptInput | None = Field(
        None,
        description="Additional details about where the content was created. Searched by `setting`.",
    )
    sourcePatientInfo: FhirReferenceInput | None = Field(
        None,
        description="Patient demographics from source - Reference(Patient). A relative reference must exist in the caller's org (422 otherwise).",
    )
    related: list[FhirReferenceInput] | None = Field(
        None,
        description="Related identifiers or resources - Reference(Any). A relative reference to a resource this server has must exist in the caller's org (422 otherwise). Searched by `related`.",
    )


class _DocumentReferenceFields(FhirInputModel):
    """Every writable DocumentReference element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/documentreference.html). Create and patch accept exactly the same
    fields. R4 requires `status` and at least one `content` (with its `attachment`), but only the
    java_validator backend enforces cardinality minimums.

    The validated body is stored whole (DocumentReferenceModel.content), so any valid R4 element
    is kept - including ones this model does not declare. Server-managed elements are ignored if
    sent: `id` (assigned from the document_reference_id sequence) and `meta` (audit/tenant data,
    stamped on at read time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["DocumentReference"] | None = Field(
        None, description="Optional; if supplied it must be 'DocumentReference'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries - validated by the profile pipeline, not here.",
    )
    masterIdentifier: FhirIdentifierInput | None = Field(
        None,
        description="Master Version Specific Identifier. Searched by `identifier` (together with `identifier`).",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None,
        description="Other identifiers for the document. Searched by `identifier`.",
    )
    status: StatusCode | None = Field(
        None,
        description="current | superseded | entered-in-error (required by R4). Searched by `status`.",
    )
    docStatus: DocStatusCode | None = Field(
        None, description="preliminary | final | amended | entered-in-error."
    )
    type: FhirCodeableConceptInput | None = Field(
        None, description="Kind of document (LOINC if possible). Searched by `type`."
    )
    category: list[FhirCodeableConceptInput] | None = Field(
        None, description="Categorization of document. Searched by `category`."
    )
    subject: FhirReferenceInput | None = Field(
        None,
        description="Who/what is the subject of the document - Reference(Patient | Practitioner | Group | Device). A relative reference must exist in the caller's org (422 otherwise). Searched by `subject` / `patient`.",
    )
    date: str | None = Field(
        None,
        description="When this document reference was created (a FHIR instant). Searched by `date`.",
    )
    author: list[FhirReferenceInput] | None = Field(
        None,
        description="Who and/or what authored the document - Reference(Practitioner | PractitionerRole | Organization | Device | Patient | RelatedPerson). A relative reference must exist in the caller's org (422 otherwise). Searched by `author`.",
    )
    authenticator: FhirReferenceInput | None = Field(
        None,
        description="Who/what authenticated the document - Reference(Practitioner | PractitionerRole | Organization). A relative reference must exist in the caller's org (422 otherwise). Searched by `authenticator`.",
    )
    custodian: FhirReferenceInput | None = Field(
        None,
        description="Organization which maintains the document - Reference(Organization). A relative reference must exist in the caller's org (422 otherwise). Searched by `custodian`.",
    )
    relatesTo: list[DocumentReferenceRelatesToInput] | None = Field(
        None, description="Relationships to other documents."
    )
    description: str | None = Field(
        None, description="Human-readable description. Searched by `description`."
    )
    securityLabel: list[FhirCodeableConceptInput] | None = Field(
        None, description="Document security-tags. Searched by `security-label`."
    )
    content: list[DocumentReferenceContentInput] | None = Field(
        None, description="Document referenced (required by R4, at least one)."
    )
    context: DocumentReferenceContextInput | None = Field(
        None, description="Clinical context of document."
    )


class DocumentReferenceCreateSchema(_DocumentReferenceFields):
    """POST body - a FHIR R4 DocumentReference resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class DocumentReferencePatchSchema(_DocumentReferenceFields):
    """PATCH body - a partial FHIR R4 DocumentReference (merge-patch semantics on top-level
    elements). Only supplied elements are written; omitted ones are left untouched. A supplied
    element replaces the stored value wholesale - a list (even `[]`) replaces every existing
    entry, an object such as `context` replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "superseded",
                "description": "Superseded discharge summary",
            }
        }
    }
