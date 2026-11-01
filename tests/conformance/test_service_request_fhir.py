"""FHIR R4 conformance for `to_fhir_service_request()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.service_request import to_fhir_service_request
from app.models.service_request import (
    ServiceRequestBasedOn,
    ServiceRequestInsurance,
    ServiceRequestLocationReference,
    ServiceRequestModel,
    ServiceRequestNote,
    ServiceRequestPerformer,
    ServiceRequestReasonReference,
    ServiceRequestRelevantHistory,
    ServiceRequestReplaces,
    ServiceRequestSpecimen,
    ServiceRequestSupportingInfo,
)
from app.models.service_request.enums import (
    ServiceRequestIntent,
    ServiceRequestPriority,
    ServiceRequestStatus,
)

from .support import assert_valid

sr_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.service_request_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 9, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "requisition_type_codings",
    "code_codings",
    "as_needed_codings",
    "performer_type_codings",
    "identifiers",
    "based_ons",
    "replaces",
    "categories",
    "order_details",
    "location_codes",
    "location_references",
    "reason_codes",
    "reason_references",
    "insurances",
    "supporting_infos",
    "specimens",
    "relevant_histories",
    "notes",
    "performers",
    "body_sites",
)


def _sr(**overrides) -> ServiceRequestModel:
    fields = {
        "service_request_id": 80001,
        "tenant_id": "org-test",
        "status": ServiceRequestStatus.active,
        "intent": ServiceRequestIntent.order,
        "priority": ServiceRequestPriority.routine,
        "authored_on": D,
        "subject_type": "Patient",
        "subject_id": 10001,
        "subject_display": "Alice Doe",
        "created_by": "u-test",
        "created_at": D,
        "extension": [],
    }
    fields.update(overrides)
    model = ServiceRequestModel(**fields)
    for attr in _CHILD_ATTRS:
        if getattr(model, attr, None) is None:
            setattr(model, attr, [])
    return model


def _with(attr, *rows) -> ServiceRequestModel:
    model = _sr()
    setattr(model, attr, list(rows))
    return model


CASES = {
    "minimal": _sr(),
    "subject_resolved": _sr(
        subject_type="Patient",
        subject_id=10001,
        subject_display="Alice Doe",
    ),
    "subject_fallback": _sr(
        subject_type=None,
        subject_id=None,
        subject_display="External Subject",
        subject_identifier_system="http://external-patients.example.org",
        subject_identifier_value="EXT-PAT-88",
        subject_identifier_use="official",
    ),
    "encounter_fallback": _sr(
        encounter_display="External Encounter",
        encounter_identifier_system="http://encounters.example.org",
        encounter_identifier_value="ENC-88",
        encounter_identifier_use="official",
    ),
    "requester_fallback": _sr(
        requester_display="External Requester",
        requester_identifier_system="http://practitioners.example.org",
        requester_identifier_value="PRAC-88",
        requester_identifier_use="official",
    ),
    "based_on_fallback": _with(
        "based_ons",
        ServiceRequestBasedOn(
            id=1,
            tenant_id="org-test",
            reference_display="External Referral",
            reference_identifier_system="http://referrals.example.org",
            reference_identifier_value="REF-22",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "replaces_fallback": _with(
        "replaces",
        ServiceRequestReplaces(
            id=1,
            tenant_id="org-test",
            reference_display="Old Service Request",
            reference_identifier_system="http://requests.example.org",
            reference_identifier_value="SR-11",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "performer_fallback": _with(
        "performers",
        ServiceRequestPerformer(
            id=1,
            tenant_id="org-test",
            reference_display="External Lab",
            reference_identifier_system="http://labs.example.org",
            reference_identifier_value="LAB-44",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "location_reference_fallback": _with(
        "location_references",
        ServiceRequestLocationReference(
            id=1,
            tenant_id="org-test",
            reference_display="Radiology Suite 3",
            reference_identifier_system="http://locations.example.org",
            reference_identifier_value="LOC-RAD-3",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "reason_reference_fallback": _with(
        "reason_references",
        ServiceRequestReasonReference(
            id=1,
            tenant_id="org-test",
            reference_display="Suspected Fracture",
            reference_identifier_system="http://conditions.example.org",
            reference_identifier_value="COND-99",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "insurance_fallback": _with(
        "insurances",
        ServiceRequestInsurance(
            id=1,
            tenant_id="org-test",
            reference_display="Medicare Coverage",
            reference_identifier_system="http://insurance.example.org",
            reference_identifier_value="INS-55",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "supporting_info_fallback": _with(
        "supporting_infos",
        ServiceRequestSupportingInfo(
            id=1,
            tenant_id="org-test",
            reference_display="Prior X-Ray",
            reference_identifier_system="http://imaging.example.org",
            reference_identifier_value="IMG-77",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "specimen_fallback": _with(
        "specimens",
        ServiceRequestSpecimen(
            id=1,
            tenant_id="org-test",
            reference_display="Blood Sample",
            reference_identifier_system="http://specimens.example.org",
            reference_identifier_value="SPEC-12",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "relevant_history_fallback": _with(
        "relevant_histories",
        ServiceRequestRelevantHistory(
            id=1,
            tenant_id="org-test",
            reference_display="Initial Triage",
            reference_identifier_system="http://provenance.example.org",
            reference_identifier_value="PROV-01",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "note_author_fallback": _with(
        "notes",
        ServiceRequestNote(
            id=1,
            tenant_id="org-test",
            text="Routine fasting required.",
            time=D,
            author_display="Dr. Clinician",
            author_identifier_system="http://practitioners.example.org",
            author_identifier_value="PRAC-99",
            author_identifier_use="official",
            created_by="u-test",
            created_at=D,
        ),
    ),
}


@pytest.mark.parametrize("case_name", list(CASES.keys()))
def test_service_request_fhir_conformance(case_name: str):
    model = CASES[case_name]
    output = to_fhir_service_request(model)
    assert_valid(sr_pb2.ServiceRequest, output)
