"""FHIR R4 conformance for `to_fhir_medication_request()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.medication_request import to_fhir_medication_request
from app.models.medication_request import (
    MedicationRequestBasedOn,
    MedicationRequestDetectedIssue,
    MedicationRequestEventHistory,
    MedicationRequestInsurance,
    MedicationRequestModel,
    MedicationRequestNote,
    MedicationRequestReasonReference,
    MedicationRequestSupportingInformation,
)
from app.models.medication_request.enums import (
    MedicationRequestIntent,
    MedicationRequestPriority,
    MedicationRequestStatus,
)

from .support import assert_valid

mr_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.medication_request_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 9, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "status_reason_codings",
    "medication_codings",
    "performer_type_codings",
    "group_identifier_type_codings",
    "course_of_therapy_type_codings",
    "substitution_allowed_codings",
    "substitution_reason_codings",
    "identifiers",
    "categories",
    "reason_codes",
    "reason_references",
    "based_ons",
    "insurances",
    "supporting_informations",
    "notes",
    "dosage_instructions",
    "detected_issues",
    "event_histories",
)


def _mr(**overrides) -> MedicationRequestModel:
    fields = {
        "medication_request_id": 90001,
        "tenant_id": "org-test",
        "status": MedicationRequestStatus.active,
        "intent": MedicationRequestIntent.order,
        "priority": MedicationRequestPriority.routine,
        "authored_on": D,
        "subject_type": "Patient",
        "subject_id": 10001,
        "subject_display": "Alice Doe",
        "created_by": "u-test",
        "created_at": D,
        "extension": [],
        "medication_codeable_concept_text": "Amoxicillin 500mg",
    }
    fields.update(overrides)
    model = MedicationRequestModel(**fields)
    for attr in _CHILD_ATTRS:
        if getattr(model, attr, None) is None:
            setattr(model, attr, [])
    return model


def _with(attr, *rows) -> MedicationRequestModel:
    model = _mr()
    setattr(model, attr, list(rows))
    return model


CASES = {
    "minimal": _mr(),
    "subject_resolved": _mr(
        subject_type="Patient",
        subject_id=10001,
        subject_display="Alice Doe",
    ),
    "subject_fallback": _mr(
        subject_type=None,
        subject_id=None,
        subject_display="External Subject",
        subject_identifier_system="http://external-patients.example.org",
        subject_identifier_value="EXT-PAT-88",
        subject_identifier_use="official",
    ),
    "encounter_fallback": _mr(
        encounter_display="External Encounter",
        encounter_identifier_system="http://encounters.example.org",
        encounter_identifier_value="ENC-88",
        encounter_identifier_use="official",
    ),
    "requester_fallback": _mr(
        requester_display="External Requester",
        requester_identifier_system="http://practitioners.example.org",
        requester_identifier_value="PRAC-88",
        requester_identifier_use="official",
    ),
    "performer_fallback": _mr(
        performer_display="External Pharmacy",
        performer_identifier_system="http://pharmacies.example.org",
        performer_identifier_value="PHARM-01",
        performer_identifier_use="official",
    ),
    "recorder_fallback": _mr(
        recorder_display="External Nurse",
        recorder_identifier_system="http://nurses.example.org",
        recorder_identifier_value="NURSE-02",
        recorder_identifier_use="official",
    ),
    "reported_reference_fallback": _mr(
        reported_reference_display="External Informant",
        reported_reference_identifier_system="http://reporters.example.org",
        reported_reference_identifier_value="REP-03",
        reported_reference_identifier_use="official",
    ),
    "medication_reference_fallback": _mr(
        medication_codeable_concept_text=None,
        medication_reference_display="Custom Compounded Drug",
        medication_reference_identifier_system="http://medications.example.org",
        medication_reference_identifier_value="MED-99",
        medication_reference_identifier_use="official",
    ),
    "dispense_request_performer_fallback": _mr(
        dispense_request_performer_display="Specialty Dispenser",
        dispense_request_performer_identifier_system="http://dispensers.example.org",
        dispense_request_performer_identifier_value="DISP-11",
        dispense_request_performer_identifier_use="official",
    ),
    "prior_prescription_fallback": _mr(
        prior_prescription_display="Old Prescription",
        prior_prescription_identifier_system="http://prescriptions.example.org",
        prior_prescription_identifier_value="RX-44",
        prior_prescription_identifier_use="official",
    ),
    "based_on_fallback": _with(
        "based_ons",
        MedicationRequestBasedOn(
            id=1,
            tenant_id="org-test",
            reference_display="Care Plan Item",
            reference_identifier_system="http://careplans.example.org",
            reference_identifier_value="CP-01",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "reason_reference_fallback": _with(
        "reason_references",
        MedicationRequestReasonReference(
            id=1,
            tenant_id="org-test",
            reference_display="Bacterial Infection",
            reference_identifier_system="http://conditions.example.org",
            reference_identifier_value="COND-55",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "insurance_fallback": _with(
        "insurances",
        MedicationRequestInsurance(
            id=1,
            tenant_id="org-test",
            reference_display="Drug Coverage Plan",
            reference_identifier_system="http://insurance.example.org",
            reference_identifier_value="INS-88",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "supporting_info_fallback": _with(
        "supporting_informations",
        MedicationRequestSupportingInformation(
            id=1,
            tenant_id="org-test",
            reference_display="Lab Culture Results",
            reference_identifier_system="http://labs.example.org",
            reference_identifier_value="LAB-12",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "detected_issue_fallback": _with(
        "detected_issues",
        MedicationRequestDetectedIssue(
            id=1,
            tenant_id="org-test",
            reference_display="Drug Interaction Alert",
            reference_identifier_system="http://alerts.example.org",
            reference_identifier_value="ALT-77",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "event_history_fallback": _with(
        "event_histories",
        MedicationRequestEventHistory(
            id=1,
            tenant_id="org-test",
            reference_display="Order Audit Event",
            reference_identifier_system="http://audit.example.org",
            reference_identifier_value="AUD-01",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "note_author_fallback": _with(
        "notes",
        MedicationRequestNote(
            id=1,
            tenant_id="org-test",
            text="Take with food.",
            time=D,
            author_display="Pharmacist John",
            author_identifier_system="http://practitioners.example.org",
            author_identifier_value="PHARM-99",
            author_identifier_use="official",
            created_by="u-test",
            created_at=D,
        ),
    ),
}


@pytest.mark.parametrize("case_name", list(CASES.keys()))
def test_medication_request_fhir_conformance(case_name: str):
    model = CASES[case_name]
    output = to_fhir_medication_request(model)
    assert_valid(mr_pb2.MedicationRequest, output)
