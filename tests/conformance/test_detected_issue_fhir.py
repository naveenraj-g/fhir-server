"""FHIR R4 conformance for `to_fhir_detected_issue()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.detected_issue import to_fhir_detected_issue
from app.models.detected_issue import (
    DetectedIssueAuthorReferenceType,
    DetectedIssueCodeCodingModel,
    DetectedIssueEvidenceCodeCodingModel,
    DetectedIssueEvidenceCodeModel,
    DetectedIssueEvidenceDetailModel,
    DetectedIssueEvidenceModel,
    DetectedIssueIdentifierModel,
    DetectedIssueIdentifierTypeCodingModel,
    DetectedIssueImplicatedModel,
    DetectedIssueMitigationActionCodingModel,
    DetectedIssueMitigationAuthorReferenceType,
    DetectedIssueMitigationModel,
    DetectedIssueModel,
    DetectedIssuePatientReferenceType,
    DetectedIssueSeverity,
    DetectedIssueStatus,
)
from app.models.enums import IdentifierUse

from .support import assert_valid

detected_issue_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.detected_issue_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 2, 1, 10, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "code_codings",
    "implicated_resources",
    "evidence_list",
    "mitigations",
)


def _detected_issue(**overrides) -> DetectedIssueModel:
    fields = {
        "id": 1,
        "detected_issue_id": 540001,
        "tenant_id": "org-test",
        "status": DetectedIssueStatus.final,
        "created_by": "u-test",
        "updated_at": D,
    }
    children = {attr: overrides.pop(attr, []) for attr in _CHILD_ATTRS}
    fields.update(overrides)
    m = DetectedIssueModel(**fields)

    for attr, val in children.items():
        setattr(m, attr, val)
    return m


def test_minimal_detected_issue_conforms():
    m = _detected_issue()
    resource = to_fhir_detected_issue(m)
    assert_valid(detected_issue_pb2.DetectedIssue, resource)


def test_full_detected_issue_conforms():
    ident = DetectedIssueIdentifierModel(
        use=IdentifierUse.official,
        system="http://example.org/issues",
        value="ISSUE-2026-001",
        period_start=D,
        period_end=D,
        assigner_reference="Organization/190001",
        assigner_display="Acme Clinic",
        type_text="Issue Tracker ID",
    )
    ident.type_codings = [
        DetectedIssueIdentifierTypeCodingModel(
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="FILL",
            display="Filler Identifier",
        )
    ]

    code_coding = DetectedIssueCodeCodingModel(
        system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
        code="DRG",
        display="Drug Interaction Alert",
        user_selected=True,
    )

    implicated = DetectedIssueImplicatedModel(
        implicated_reference="MedicationRequest/90001",
        implicated_type="MedicationRequest",
        implicated_id=90001,
        implicated_display="Warfarin Sodium 5mg",
    )

    ev_detail = DetectedIssueEvidenceDetailModel(
        detail_reference="Observation/160001",
        detail_type="Observation",
        detail_id=160001,
        detail_display="INR Lab Result",
    )

    ev_code = DetectedIssueEvidenceCodeModel(text="Bleeding risk")
    ev_code.codings = [
        DetectedIssueEvidenceCodeCodingModel(
            system="http://snomed.info/sct",
            code="89240000",
            display="Drug-induced hemorrhage",
        )
    ]

    ev = DetectedIssueEvidenceModel()
    ev.codes = [ev_code]
    ev.details = [ev_detail]

    mit_action_coding = DetectedIssueMitigationActionCodingModel(
        system="http://terminology.hl7.org/CodeSystem/v3-ActCode",
        code="13",
        display="Consulted Prescriber",
    )
    mit = DetectedIssueMitigationModel(
        action_text="Prescriber confirmed low dose",
        date=D,
        author_reference="Practitioner/30001",
        author_type=DetectedIssueMitigationAuthorReferenceType.Practitioner,
        author_id=30001,
        author_display="Dr. Alice Smith",
    )
    mit.action_codings = [mit_action_coding]

    m = _detected_issue(
        severity=DetectedIssueSeverity.high,
        patient_reference="Patient/10001",
        patient_type=DetectedIssuePatientReferenceType.Patient,
        patient_id=10001,
        patient_display="Jane Doe",
        identified_date_time=D,
        author_reference="Practitioner/30001",
        author_type=DetectedIssueAuthorReferenceType.Practitioner,
        author_id=30001,
        author_display="Dr. Alice Smith",
        detail="Concurrent use of warfarin and aspirin significantly increases risk of major gastrointestinal hemorrhage.",
        reference="http://example.org/alerts/interaction-war-asp",
        code_text="Potential drug-drug interaction between Warfarin and Aspirin",
        code_codings=[code_coding],
        identifiers=[ident],
        implicated_resources=[implicated],
        evidence_list=[ev],
        mitigations=[mit],
    )

    resource = to_fhir_detected_issue(m)
    assert_valid(detected_issue_pb2.DetectedIssue, resource)


def test_identified_period_conforms():
    m = _detected_issue(
        identified_period_start=D,
        identified_period_end=D,
    )
    resource = to_fhir_detected_issue(m)
    assert_valid(detected_issue_pb2.DetectedIssue, resource)
