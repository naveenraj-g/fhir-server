"""FHIR R4 conformance for `to_fhir_communication()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.communication import to_fhir_communication
from app.models.communication import (
    CommunicationAbout,
    CommunicationBasedOn,
    CommunicationCategory,
    CommunicationCategoryCoding,
    CommunicationEncounterReferenceType,
    CommunicationIdentifier,
    CommunicationIdentifierTypeCoding,
    CommunicationInResponseTo,
    CommunicationInResponseToReferenceType,
    CommunicationMedium,
    CommunicationMediumCoding,
    CommunicationModel,
    CommunicationNote,
    CommunicationPartOf,
    CommunicationPayload,
    CommunicationPriority,
    CommunicationReasonCode,
    CommunicationReasonCodeCoding,
    CommunicationReasonReference,
    CommunicationReasonReferenceType,
    CommunicationRecipient,
    CommunicationRecipientReferenceType,
    CommunicationSenderReferenceType,
    CommunicationStatus,
    CommunicationStatusReasonCoding,
    CommunicationSubjectReferenceType,
    CommunicationTopicCoding,
)
from app.models.enums import IdentifierUse, OrganizationReferenceType

from .support import assert_valid

communication_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.communication_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

T = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "based_on_list",
    "part_of_list",
    "in_response_to_list",
    "status_reason_codings",
    "categories",
    "medium_list",
    "topic_codings",
    "about_list",
    "payloads",
    "recipients",
    "reason_codes",
    "reason_references",
    "notes",
)


def _communication(**overrides) -> CommunicationModel:
    fields = {
        "id": 1,
        "communication_id": 480001,
        "tenant_id": "org-test",
        "status": CommunicationStatus.completed,
        "priority": CommunicationPriority.routine,
        "subject_reference": "Patient/10001",
        "subject_type": CommunicationSubjectReferenceType.Patient,
        "subject_id": 10001,
        "subject_display": "Jane Doe",
        "encounter_reference": "Encounter/20001",
        "encounter_type": CommunicationEncounterReferenceType.Encounter,
        "encounter_id": 20001,
        "encounter_display": "Office Visit",
        "sent": T,
        "received": T + dt.timedelta(minutes=1),
        "sender_reference": "Practitioner/30001",
        "sender_type": CommunicationSenderReferenceType.Practitioner,
        "sender_id": 30001,
        "sender_display": "Dr. Smith",
        "created_at": T,
        "updated_at": T,
        "created_by": "user-1",
        "updated_by": "user-1",
    }
    fields.update(overrides)
    m = CommunicationModel()
    for k, v in fields.items():
        setattr(m, k, v)
    for attr in _CHILD_ATTRS:
        if not hasattr(m, attr) or getattr(m, attr) is None:
            setattr(m, attr, [])
    return m


def test_communication_minimal_conformance():
    """Minimal Communication conforming to FHIR R4."""
    model = _communication()
    fhir_dict = to_fhir_communication(model)
    assert fhir_dict["resourceType"] == "Communication"
    assert fhir_dict["id"] == "480001"
    assert fhir_dict["status"] == "completed"
    assert_valid(communication_pb2.Communication, fhir_dict)


def test_communication_full_conformance():
    """Full Communication with all sub-elements populated conforming to FHIR R4."""
    model = _communication()

    # instantiatesCanonical & instantiatesUri
    model.instantiates_canonical = ["http://hl7.org/fhir/PlanDefinition/123"]
    model.instantiates_uri = ["http://example.org/protocols/comm"]

    # Identifier
    ident = CommunicationIdentifier(
        id=1,
        communication_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        type_text="Requisition ID",
        system="http://hospital.example.org",
        value="COMM-12345",
        period_start=T,
        period_end=T + dt.timedelta(days=365),
        assigner_reference="Organization/190001",
        assigner_type=OrganizationReferenceType.Organization,
        assigner_id=190001,
        assigner_display="Example Hospital",
    )
    ident.type_codings = [
        CommunicationIdentifierTypeCoding(
            id=1,
            communication_identifier_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="FILL",
            display="Filler Identifier",
        )
    ]
    model.identifiers = [ident]

    # basedOn
    model.based_on_list = [
        CommunicationBasedOn(
            id=1,
            communication_pk=1,
            tenant_id="org-test",
            reference_reference="CommunicationRequest/470001",
            reference_type="CommunicationRequest",
            reference_id=470001,
            reference_display="Communication Request",
        )
    ]

    # partOf
    model.part_of_list = [
        CommunicationPartOf(
            id=1,
            communication_pk=1,
            tenant_id="org-test",
            reference_reference="Task/280001",
            reference_type="Task",
            reference_id=280001,
            reference_display="Patient Check-in Task",
        )
    ]

    # inResponseTo
    model.in_response_to_list = [
        CommunicationInResponseTo(
            id=1,
            communication_pk=1,
            tenant_id="org-test",
            reference_reference="Communication/480000",
            reference_type=CommunicationInResponseToReferenceType.Communication,
            reference_id=480000,
            reference_display="Initial inquiry",
        )
    ]

    # statusReason
    model.status_reason_text = "Scheduled regular transmission"
    model.status_reason_codings = [
        CommunicationStatusReasonCoding(
            id=1,
            communication_pk=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/communication-category",
            code="routine",
            display="Routine",
        )
    ]

    # category
    cat = CommunicationCategory(
        id=1,
        communication_pk=1,
        tenant_id="org-test",
        text="Notification Message",
    )
    cat.codings = [
        CommunicationCategoryCoding(
            id=1,
            communication_category_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/communication-category",
            code="notification",
            display="Notification",
        )
    ]
    model.categories = [cat]

    # medium
    med = CommunicationMedium(
        id=1,
        communication_pk=1,
        tenant_id="org-test",
        text="Written letter",
    )
    med.codings = [
        CommunicationMediumCoding(
            id=1,
            communication_medium_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v3-ParticipationMode",
            code="WRITTEN",
            display="written",
        )
    ]
    model.medium_list = [med]

    # topic
    model.topic_text = "Followup instructions"
    model.topic_codings = [
        CommunicationTopicCoding(
            id=1,
            communication_pk=1,
            tenant_id="org-test",
            system="http://example.org/topics",
            code="followup",
            display="Followup Instructions",
        )
    ]

    # about
    model.about_list = [
        CommunicationAbout(
            id=1,
            communication_pk=1,
            tenant_id="org-test",
            reference_reference="Condition/120001",
            reference_type="Condition",
            reference_id=120001,
            reference_display="Type 2 Diabetes",
        )
    ]

    # recipient
    model.recipients = [
        CommunicationRecipient(
            id=1,
            communication_pk=1,
            tenant_id="org-test",
            reference_reference="Patient/10001",
            reference_type=CommunicationRecipientReferenceType.Patient,
            reference_id=10001,
            reference_display="Jane Doe",
        )
    ]

    # reasonCode
    rc = CommunicationReasonCode(
        id=1,
        communication_pk=1,
        tenant_id="org-test",
        text="Routine Care",
    )
    rc.codings = [
        CommunicationReasonCodeCoding(
            id=1,
            communication_reason_code_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v3-ActReason",
            code="ROUTINE",
            display="Routine",
        )
    ]
    model.reason_codes = [rc]

    # reasonReference
    model.reason_references = [
        CommunicationReasonReference(
            id=1,
            communication_pk=1,
            tenant_id="org-test",
            reference_reference="Observation/160001",
            reference_type=CommunicationReasonReferenceType.Observation,
            reference_id=160001,
            reference_display="Blood Pressure Observation",
        )
    ]

    # payloads (string, attachment, reference)
    p_str = CommunicationPayload(
        id=1,
        communication_pk=1,
        tenant_id="org-test",
        content_string="Please review the attached discharge instructions.",
    )
    p_att = CommunicationPayload(
        id=2,
        communication_pk=1,
        tenant_id="org-test",
        content_type="application/pdf",
        language="en",
        url="http://hospital.example.org/docs/instructions.pdf",
        title="Discharge Instructions",
    )
    p_ref = CommunicationPayload(
        id=3,
        communication_pk=1,
        tenant_id="org-test",
        content_reference_reference="DocumentReference/320001",
        content_reference_type="DocumentReference",
        content_reference_id=320001,
        content_reference_display="Discharge Summary Document",
    )
    model.payloads = [p_str, p_att, p_ref]

    # note
    model.notes = [
        CommunicationNote(
            id=1,
            communication_pk=1,
            tenant_id="org-test",
            author_string="Nurse Kelly",
            time=T,
            text="Patient verbally confirmed receipt of information.",
        )
    ]

    fhir_dict = to_fhir_communication(model)
    assert fhir_dict["resourceType"] == "Communication"
    assert fhir_dict["id"] == "480001"
    assert len(fhir_dict["payload"]) == 3
    assert fhir_dict["topic"]["text"] == "Followup instructions"
    assert len(fhir_dict["inResponseTo"]) == 1
    assert_valid(communication_pb2.Communication, fhir_dict)
