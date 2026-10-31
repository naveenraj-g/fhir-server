"""FHIR R4 conformance for `to_fhir_communication_request()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.communication_request import to_fhir_communication_request
from app.models.communication_request import (
    CommunicationRequestAbout,
    CommunicationRequestBasedOn,
    CommunicationRequestCategory,
    CommunicationRequestCategoryCoding,
    CommunicationRequestEncounterReferenceType,
    CommunicationRequestIdentifier,
    CommunicationRequestIdentifierTypeCoding,
    CommunicationRequestMedium,
    CommunicationRequestMediumCoding,
    CommunicationRequestModel,
    CommunicationRequestNote,
    CommunicationRequestPayload,
    CommunicationRequestPriority,
    CommunicationRequestReasonCode,
    CommunicationRequestReasonCodeCoding,
    CommunicationRequestReasonReference,
    CommunicationRequestReasonReferenceType,
    CommunicationRequestRecipient,
    CommunicationRequestRecipientReferenceType,
    CommunicationRequestReplaces,
    CommunicationRequestRequesterReferenceType,
    CommunicationRequestSenderReferenceType,
    CommunicationRequestStatus,
    CommunicationRequestStatusReasonCoding,
    CommunicationRequestSubjectReferenceType,
)
from app.models.enums import IdentifierUse, OrganizationReferenceType

from .support import assert_valid

communication_request_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.communication_request_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

T = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "based_on_list",
    "replaces_list",
    "status_reason_codings",
    "categories",
    "medium_list",
    "about_list",
    "payloads",
    "recipients",
    "reason_codes",
    "reason_references",
    "notes",
)


def _communication_request(**overrides) -> CommunicationRequestModel:
    fields = {
        "id": 1,
        "communication_request_id": 470001,
        "tenant_id": "org-test",
        "status": CommunicationRequestStatus.active,
        "priority": CommunicationRequestPriority.routine,
        "do_not_perform": False,
        "subject_reference": "Patient/10001",
        "subject_type": CommunicationRequestSubjectReferenceType.Patient,
        "subject_id": 10001,
        "subject_display": "Jane Doe",
        "encounter_reference": "Encounter/20001",
        "encounter_type": CommunicationRequestEncounterReferenceType.Encounter,
        "encounter_id": 20001,
        "encounter_display": "Office Visit",
        "authored_on": T,
        "occurrence_date_time": T,
        "requester_reference": "Practitioner/30001",
        "requester_type": CommunicationRequestRequesterReferenceType.Practitioner,
        "requester_id": 30001,
        "requester_display": "Dr. Smith",
        "sender_reference": "Practitioner/30001",
        "sender_type": CommunicationRequestSenderReferenceType.Practitioner,
        "sender_id": 30001,
        "sender_display": "Dr. Smith",
        "created_at": T,
        "updated_at": T,
        "created_by": "user-1",
        "updated_by": "user-1",
    }
    fields.update(overrides)
    m = CommunicationRequestModel()
    for k, v in fields.items():
        setattr(m, k, v)
    for attr in _CHILD_ATTRS:
        if not hasattr(m, attr) or getattr(m, attr) is None:
            setattr(m, attr, [])
    return m


def test_communication_request_minimal_conformance():
    """Minimal CommunicationRequest conforming to FHIR R4."""
    model = _communication_request()
    fhir_dict = to_fhir_communication_request(model)
    assert fhir_dict["resourceType"] == "CommunicationRequest"
    assert fhir_dict["id"] == "470001"
    assert fhir_dict["status"] == "active"
    assert_valid(communication_request_pb2.CommunicationRequest, fhir_dict)


def test_communication_request_full_conformance():
    """Full CommunicationRequest with all sub-elements populated conforming to FHIR R4."""
    model = _communication_request()

    # Group identifier
    model.group_identifier_use = IdentifierUse.official
    model.group_identifier_system = "http://hospital.example.org/groups"
    model.group_identifier_value = "GRP-999"
    model.group_identifier_period_start = T
    model.group_identifier_period_end = T + dt.timedelta(days=30)
    model.group_identifier_assigner_reference = "Organization/190001"
    model.group_identifier_assigner_type = OrganizationReferenceType.Organization
    model.group_identifier_assigner_id = 190001
    model.group_identifier_assigner_display = "Example Hospital"

    # Identifier
    ident = CommunicationRequestIdentifier(
        id=1,
        communication_request_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        type_text="Requisition ID",
        system="http://hospital.example.org",
        value="CR-12345",
        period_start=T,
        period_end=T + dt.timedelta(days=365),
        assigner_reference="Organization/190001",
        assigner_type=OrganizationReferenceType.Organization,
        assigner_id=190001,
        assigner_display="Example Hospital",
    )
    ident.type_codings = [
        CommunicationRequestIdentifierTypeCoding(
            id=1,
            communication_request_identifier_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="FILL",
            display="Filler Identifier",
        )
    ]
    model.identifiers = [ident]

    # basedOn
    model.based_on_list = [
        CommunicationRequestBasedOn(
            id=1,
            communication_request_pk=1,
            tenant_id="org-test",
            reference_reference="CarePlan/290001",
            reference_type="CarePlan",
            reference_id=290001,
            reference_display="Diabetes Care Plan",
        )
    ]

    # replaces
    model.replaces_list = [
        CommunicationRequestReplaces(
            id=1,
            communication_request_pk=1,
            tenant_id="org-test",
            reference_reference="CommunicationRequest/470000",
            reference_type="CommunicationRequest",
            reference_id=470000,
            reference_display="Prior Communication Request",
        )
    ]

    # statusReason
    model.status_reason_text = "Scheduled regular follow-up"
    model.status_reason_codings = [
        CommunicationRequestStatusReasonCoding(
            id=1,
            communication_request_pk=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/communication-request-status-reason",
            code="routine",
            display="Routine",
        )
    ]

    # category
    cat = CommunicationRequestCategory(
        id=1,
        communication_request_pk=1,
        tenant_id="org-test",
        text="Notification",
    )
    cat.codings = [
        CommunicationRequestCategoryCoding(
            id=1,
            communication_request_category_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/communication-category",
            code="notification",
            display="Notification",
        )
    ]
    model.categories = [cat]

    # medium
    med = CommunicationRequestMedium(
        id=1,
        communication_request_pk=1,
        tenant_id="org-test",
        text="written",
    )
    med.codings = [
        CommunicationRequestMediumCoding(
            id=1,
            communication_request_medium_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v3-ParticipationMode",
            code="WRITTEN",
            display="written",
        )
    ]
    model.medium_list = [med]

    # about
    model.about_list = [
        CommunicationRequestAbout(
            id=1,
            communication_request_pk=1,
            tenant_id="org-test",
            reference_reference="Observation/160001",
            reference_type="Observation",
            reference_id=160001,
            reference_display="Lab result",
        )
    ]

    # payload
    p_string = CommunicationRequestPayload(
        id=1,
        communication_request_pk=1,
        tenant_id="org-test",
        content_string="Please review lab results and call patient.",
    )
    p_attachment = CommunicationRequestPayload(
        id=2,
        communication_request_pk=1,
        tenant_id="org-test",
        content_type="text/plain",
        data="SGVsbG8gV29ybGQ=",
        title="Lab summary",
    )
    p_ref = CommunicationRequestPayload(
        id=3,
        communication_request_pk=1,
        tenant_id="org-test",
        content_reference_reference="DocumentReference/320001",
        content_reference_type="DocumentReference",
        content_reference_id=320001,
        content_reference_display="Lab report document",
    )
    model.payloads = [p_string, p_attachment, p_ref]

    # recipient
    model.recipients = [
        CommunicationRequestRecipient(
            id=1,
            communication_request_pk=1,
            tenant_id="org-test",
            reference_reference="Patient/10001",
            reference_type=CommunicationRequestRecipientReferenceType.Patient,
            reference_id=10001,
            reference_display="Jane Doe",
        )
    ]

    # reasonCode
    rc = CommunicationRequestReasonCode(
        id=1,
        communication_request_pk=1,
        tenant_id="org-test",
        text="Abnormal lab",
    )
    rc.codings = [
        CommunicationRequestReasonCodeCoding(
            id=1,
            communication_request_reason_code_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="439401001",
            display="Abnormal lab result",
        )
    ]
    model.reason_codes = [rc]

    # reasonReference
    model.reason_references = [
        CommunicationRequestReasonReference(
            id=1,
            communication_request_pk=1,
            tenant_id="org-test",
            reference_reference="Condition/120001",
            reference_type=CommunicationRequestReasonReferenceType.Condition,
            reference_id=120001,
            reference_display="Diabetes mellitus",
        )
    ]

    # notes
    model.notes = [
        CommunicationRequestNote(
            id=1,
            communication_request_pk=1,
            tenant_id="org-test",
            author_reference="Practitioner/30001",
            author_type="Practitioner",
            author_id=30001,
            author_display="Dr. Smith",
            time=T,
            text="Priority notification sent.",
        )
    ]

    fhir_dict = to_fhir_communication_request(model)
    assert_valid(communication_request_pb2.CommunicationRequest, fhir_dict)
