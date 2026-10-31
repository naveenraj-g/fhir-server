"""FHIR R4 conformance for `to_fhir_document_reference()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.document_reference import to_fhir_document_reference
from app.models.document_reference import (
    DocumentReferenceAuthor,
    DocumentReferenceAuthorReferenceType,
    DocumentReferenceCategory,
    DocumentReferenceCategoryCoding,
    DocumentReferenceContent,
    DocumentReferenceContextEncounter,
    DocumentReferenceContextEncounterReferenceType,
    DocumentReferenceContextEvent,
    DocumentReferenceContextEventCoding,
    DocumentReferenceContextFacilityTypeCoding,
    DocumentReferenceContextPracticeSettingCoding,
    DocumentReferenceContextRelated,
    DocumentReferenceDocStatus,
    DocumentReferenceIdentifier,
    DocumentReferenceIdentifierTypeCoding,
    DocumentReferenceMasterIdentifierTypeCoding,
    DocumentReferenceModel,
    DocumentReferencePatientReferenceType,
    DocumentReferenceRelatesTo,
    DocumentReferenceSecurityLabel,
    DocumentReferenceSecurityLabelCoding,
    DocumentReferenceStatus,
    DocumentReferenceSubjectReferenceType,
    DocumentReferenceTargetReferenceType,
    DocumentReferenceTypeCoding,
    DocumentRelationshipType,
)
from app.models.enums import (
    IdentifierUse,
    OrganizationReferenceType,
    PractitionerReferenceType,
)

from .support import assert_valid

document_reference_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.document_reference_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "master_identifier_type_codings",
    "identifiers",
    "type_codings",
    "categories",
    "authors",
    "relates_to",
    "security_labels",
    "contents",
    "context_encounters",
    "context_events",
    "context_facility_type_codings",
    "context_practice_setting_codings",
    "context_related",
)


def _document_reference(**overrides) -> DocumentReferenceModel:
    fields = {
        "id": 1,
        "document_reference_id": 320001,
        "tenant_id": "org-test",
        "status": DocumentReferenceStatus.current,
        "created_by": "u-test",
        "created_at": D,
        "updated_at": D,
        "extension": [],
    }
    fields.update(overrides)
    d = DocumentReferenceModel(**fields)
    for attr in _CHILD_ATTRS:
        if getattr(d, attr, None) is None:
            setattr(d, attr, [])
    # A valid DocumentReference in FHIR R4 requires at least one content
    if not d.contents:
        d.contents = [
            DocumentReferenceContent(
                id=1,
                document_reference_pk=1,
                tenant_id="org-test",
                content_type="text/plain",
                url="https://example.org/docs/1",
                title="Test Document",
                created_by="u-test",
                created_at=D,
            )
        ]
    return d


def test_minimal_document_reference_conforms():
    d = _document_reference()
    out = to_fhir_document_reference(d)
    assert out["resourceType"] == "DocumentReference"
    assert out["id"] == "320001"
    assert out["status"] == "current"
    assert len(out["content"]) == 1
    assert out["content"][0]["attachment"]["contentType"] == "text/plain"
    assert_valid(document_reference_pb2.DocumentReference, out)


def test_document_reference_status():
    for status_val in [
        DocumentReferenceStatus.current,
        DocumentReferenceStatus.superseded,
        DocumentReferenceStatus.entered_in_error,
    ]:
        d = _document_reference(status=status_val)
        out = to_fhir_document_reference(d)
        assert out["status"] == status_val.value
        assert_valid(document_reference_pb2.DocumentReference, out)


def test_document_reference_doc_status():
    for doc_status_val in [
        DocumentReferenceDocStatus.preliminary,
        DocumentReferenceDocStatus.final,
        DocumentReferenceDocStatus.amended,
        DocumentReferenceDocStatus.entered_in_error,
    ]:
        d = _document_reference(doc_status=doc_status_val)
        out = to_fhir_document_reference(d)
        assert out["docStatus"] == doc_status_val.value
        assert_valid(document_reference_pb2.DocumentReference, out)


def test_document_reference_type():
    d = _document_reference(type_text="Clinical summary")
    d.type_codings = [
        DocumentReferenceTypeCoding(
            id=1,
            document_reference_pk=1,
            tenant_id="org-test",
            system="http://loinc.org",
            code="34108-1",
            display="Outpatient Note",
            created_by="u-test",
            created_at=D,
        )
    ]
    out = to_fhir_document_reference(d)
    assert out["type"]["text"] == "Clinical summary"
    assert out["type"]["coding"][0]["code"] == "34108-1"
    assert_valid(document_reference_pb2.DocumentReference, out)


def test_document_reference_category():
    d = _document_reference()
    cat = DocumentReferenceCategory(
        id=1,
        document_reference_pk=1,
        tenant_id="org-test",
        text="Clinical",
        created_by="u-test",
        created_at=D,
    )
    cat.codings = [
        DocumentReferenceCategoryCoding(
            id=1,
            document_reference_category_id=1,
            tenant_id="org-test",
            system="http://hl7.org/fhir/us/core/CodeSystem/us-core-documentreference-category",
            code="clinical-note",
            display="Clinical Note",
            created_by="u-test",
            created_at=D,
        )
    ]
    d.categories = [cat]
    out = to_fhir_document_reference(d)
    assert len(out["category"]) == 1
    assert out["category"][0]["text"] == "Clinical"
    assert out["category"][0]["coding"][0]["code"] == "clinical-note"
    assert_valid(document_reference_pb2.DocumentReference, out)


def test_document_reference_subject():
    for ref_type, display in [
        (DocumentReferenceSubjectReferenceType.Patient, "Patient Doe"),
        (DocumentReferenceSubjectReferenceType.Practitioner, "Dr. Smith"),
        (DocumentReferenceSubjectReferenceType.Group, "Group Alpha"),
        (DocumentReferenceSubjectReferenceType.Device, "ECG Machine"),
    ]:
        d = _document_reference(
            subject_reference=f"{ref_type.value}/10001",
            subject_type=ref_type,
            subject_id=10001,
            subject_display=display,
        )
        out = to_fhir_document_reference(d)
        assert out["subject"]["reference"] == f"{ref_type.value}/10001"
        assert out["subject"]["display"] == display
        assert_valid(document_reference_pb2.DocumentReference, out)


def test_document_reference_date_and_description():
    d = _document_reference(
        date=D,
        description="Follow-up clinical discharge note",
    )
    out = to_fhir_document_reference(d)
    assert "2026-01-01" in out["date"]
    assert out["description"] == "Follow-up clinical discharge note"
    assert_valid(document_reference_pb2.DocumentReference, out)


def test_document_reference_author_and_authenticator_and_custodian():
    d = _document_reference(
        authenticator_reference="Practitioner/30001",
        authenticator_type=PractitionerReferenceType.Practitioner,
        authenticator_id=30001,
        authenticator_display="Dr. Smith",
        custodian_reference="Organization/190001",
        custodian_type=OrganizationReferenceType.Organization,
        custodian_id=190001,
        custodian_display="General Hospital",
    )
    d.authors = [
        DocumentReferenceAuthor(
            id=1,
            document_reference_pk=1,
            tenant_id="org-test",
            author_reference="Practitioner/30001",
            author_type=DocumentReferenceAuthorReferenceType.Practitioner,
            author_id=30001,
            author_display="Dr. Smith",
            created_by="u-test",
            created_at=D,
        )
    ]
    out = to_fhir_document_reference(d)
    assert out["author"][0]["reference"] == "Practitioner/30001"
    assert out["authenticator"]["reference"] == "Practitioner/30001"
    assert out["custodian"]["reference"] == "Organization/190001"
    assert_valid(document_reference_pb2.DocumentReference, out)


def test_document_reference_relates_to():
    d = _document_reference()
    d.relates_to = [
        DocumentReferenceRelatesTo(
            id=1,
            document_reference_pk=1,
            tenant_id="org-test",
            code=DocumentRelationshipType.replaces,
            target_reference="DocumentReference/320000",
            target_type=DocumentReferenceTargetReferenceType.DocumentReference,
            target_id=320000,
            target_display="Previous discharge summary",
            created_by="u-test",
            created_at=D,
        )
    ]
    out = to_fhir_document_reference(d)
    assert len(out["relatesTo"]) == 1
    assert out["relatesTo"][0]["code"] == "replaces"
    assert out["relatesTo"][0]["target"]["reference"] == "DocumentReference/320000"
    assert_valid(document_reference_pb2.DocumentReference, out)


def test_document_reference_security_label():
    d = _document_reference()
    sec = DocumentReferenceSecurityLabel(
        id=1,
        document_reference_pk=1,
        tenant_id="org-test",
        text="Confidential",
        created_by="u-test",
        created_at=D,
    )
    sec.codings = [
        DocumentReferenceSecurityLabelCoding(
            id=1,
            document_reference_security_label_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
            code="R",
            display="Restricted",
            created_by="u-test",
            created_at=D,
        )
    ]
    d.security_labels = [sec]
    out = to_fhir_document_reference(d)
    assert len(out["securityLabel"]) == 1
    assert out["securityLabel"][0]["text"] == "Confidential"
    assert out["securityLabel"][0]["coding"][0]["code"] == "R"
    assert_valid(document_reference_pb2.DocumentReference, out)


def test_document_reference_content_full():
    d = _document_reference()
    d.contents = [
        DocumentReferenceContent(
            id=1,
            document_reference_pk=1,
            tenant_id="org-test",
            content_type="application/pdf",
            language="en",
            data="SGVsbG8gV29ybGQ=",
            url="https://cdn.example.org/doc.pdf",
            size=1024,
            hash="2fd4e1c67a2d28fced849ee1bb76e7391b93eb12",
            title="Discharge PDF",
            creation=D,
            format_system="urn:oid:1.2.840.10008.2.1.1",
            format_version="1.0",
            format_code="urn:ihe:pcc:xphr:2007",
            format_display="Personal Health Record",
            format_user_selected=True,
            created_by="u-test",
            created_at=D,
        )
    ]
    out = to_fhir_document_reference(d)
    content = out["content"][0]
    assert content["attachment"]["contentType"] == "application/pdf"
    assert content["attachment"]["language"] == "en"
    assert content["attachment"]["size"] == 1024
    assert content["format"]["code"] == "urn:ihe:pcc:xphr:2007"
    assert_valid(document_reference_pb2.DocumentReference, out)


def test_document_reference_context():
    d = _document_reference(
        context_period_start=D,
        context_period_end=D,
        context_facility_type_text="Outpatient Clinic",
        context_practice_setting_text="General Medicine",
        context_source_patient_info_reference="Patient/10001",
        context_source_patient_info_type=DocumentReferencePatientReferenceType.Patient,
        context_source_patient_info_id=10001,
        context_source_patient_info_display="Jane Doe",
    )
    d.context_encounters = [
        DocumentReferenceContextEncounter(
            id=1,
            document_reference_pk=1,
            tenant_id="org-test",
            reference_reference="Encounter/20001",
            reference_type=DocumentReferenceContextEncounterReferenceType.Encounter,
            reference_id=20001,
            reference_display="Consultation Encounter",
            created_by="u-test",
            created_at=D,
        )
    ]
    evt = DocumentReferenceContextEvent(
        id=1,
        document_reference_pk=1,
        tenant_id="org-test",
        text="Clinical Consultation",
        created_by="u-test",
        created_at=D,
    )
    evt.codings = [
        DocumentReferenceContextEventCoding(
            id=1,
            document_reference_context_event_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
            code="AMB",
            display="Ambulatory",
            created_by="u-test",
            created_at=D,
        )
    ]
    d.context_events = [evt]
    d.context_facility_type_codings = [
        DocumentReferenceContextFacilityTypeCoding(
            id=1,
            document_reference_pk=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="225732001",
            display="Hospital",
            created_by="u-test",
            created_at=D,
        )
    ]
    d.context_practice_setting_codings = [
        DocumentReferenceContextPracticeSettingCoding(
            id=1,
            document_reference_pk=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="408443003",
            display="General medical practice",
            created_by="u-test",
            created_at=D,
        )
    ]
    d.context_related = [
        DocumentReferenceContextRelated(
            id=1,
            document_reference_pk=1,
            tenant_id="org-test",
            reference_reference="Patient/10001",
            reference_type="Patient",
            reference_id=10001,
            reference_display="Jane Doe Related",
            created_by="u-test",
            created_at=D,
        )
    ]
    out = to_fhir_document_reference(d)
    ctx = out["context"]
    assert ctx["encounter"][0]["reference"] == "Encounter/20001"
    assert ctx["event"][0]["coding"][0]["code"] == "AMB"
    assert ctx["facilityType"]["coding"][0]["code"] == "225732001"
    assert ctx["practiceSetting"]["coding"][0]["code"] == "408443003"
    assert ctx["sourcePatientInfo"]["reference"] == "Patient/10001"
    assert ctx["related"][0]["reference"] == "Patient/10001"
    assert_valid(document_reference_pb2.DocumentReference, out)


def test_document_reference_identifiers():
    d = _document_reference(
        master_identifier_use=IdentifierUse.official,
        master_identifier_system="urn:ietf:rfc:3986",
        master_identifier_value="urn:uuid:0c2873fc-94c6-11ec-b909-0242ac120002",
        master_identifier_type_text="Master ID",
    )
    d.master_identifier_type_codings = [
        DocumentReferenceMasterIdentifierTypeCoding(
            id=1,
            document_reference_pk=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="MR",
            display="Medical Record",
            created_by="u-test",
            created_at=D,
        )
    ]
    ident = DocumentReferenceIdentifier(
        id=1,
        document_reference_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.usual,
        system="http://hospital.example.org/documents",
        value="DOC-12345",
        type_text="Internal ID",
        created_by="u-test",
        created_at=D,
    )
    ident.type_codings = [
        DocumentReferenceIdentifierTypeCoding(
            id=1,
            document_reference_identifier_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="FILL",
            display="Filler Identifier",
            created_by="u-test",
            created_at=D,
        )
    ]
    d.identifiers = [ident]
    out = to_fhir_document_reference(d)
    assert out["masterIdentifier"]["value"] == "urn:uuid:0c2873fc-94c6-11ec-b909-0242ac120002"
    assert out["masterIdentifier"]["type"]["coding"][0]["code"] == "MR"
    assert out["identifier"][0]["value"] == "DOC-12345"
    assert out["identifier"][0]["type"]["coding"][0]["code"] == "FILL"
    assert_valid(document_reference_pb2.DocumentReference, out)
