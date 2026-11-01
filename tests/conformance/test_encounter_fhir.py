"""FHIR R4 conformance for `to_fhir_encounter()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.encounter import to_fhir_encounter
from app.models.encounter import (
    EncounterAccount,
    EncounterAppointment,
    EncounterBasedOn,
    EncounterClassHistory,
    EncounterDiagnosis,
    EncounterDiagnosisUseCoding,
    EncounterEpisodeOfCare,
    EncounterHospitalization,
    EncounterIdentifier,
    EncounterIdentifierTypeCoding,
    EncounterLocationPhysicalTypeCoding,
    EncounterLocationRow,
    EncounterModel,
    EncounterParticipant,
    EncounterParticipantType,
    EncounterParticipantTypeCoding,
    EncounterReasonCode,
    EncounterReasonCodeCoding,
    EncounterReasonReference,
    EncounterServiceTypeCoding,
    EncounterStatus,
    EncounterStatusHistory,
    EncounterType,
    EncounterTypeCoding,
)

from .support import assert_valid, fhir_json_text

encounter_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.encounter_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 9, 0, tzinfo=dt.timezone.utc)
D2 = dt.datetime(2026, 1, 1, 10, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "status_history",
    "class_history",
    "types",
    "service_type_codings",
    "priority_codings",
    "episodes_of_care",
    "based_ons",
    "participants",
    "appointments",
    "reason_codes",
    "reason_references",
    "diagnoses",
    "accounts",
    "locations",
)


def _enc(**overrides) -> EncounterModel:
    """An Encounter carrying NOT NULL columns + class coding."""
    fields = {
        "encounter_id": 20001,
        "tenant_id": "org-test",
        "status": EncounterStatus.in_progress,
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
        "code": "AMB",
        "display": "ambulatory",
        "period_start": D,
        "period_end": D2,
        "created_by": "u-test",
        "created_at": D,
    }
    fields.update(overrides)
    enc = EncounterModel(**fields)
    for attr in _CHILD_ATTRS:
        if getattr(enc, attr, None) is None:
            setattr(enc, attr, [])
    return enc


def _with(attr, *rows) -> EncounterModel:
    enc = _enc()
    setattr(enc, attr, list(rows))
    return enc


def _identifier(**kw) -> EncounterIdentifier:
    defaults = {
        "id": 1,
        "tenant_id": "org-test",
        "system": "http://example.org/encounters",
        "value": "ENC-001",
        "created_by": "u-test",
        "created_at": D,
    }
    defaults.update(kw)
    type_codings = defaults.pop("type_codings", [])
    ident = EncounterIdentifier(**defaults)
    ident.type_codings = type_codings
    return ident


CASES = {
    "minimal": _enc(),
    "status_finished": _enc(status=EncounterStatus.finished),
    "subject_resolved": _enc(
        subject_type="Patient",
        subject_id=10001,
        subject_display="Alice Doe",
    ),
    "subject_fallback": _enc(
        subject_display="External Patient",
        subject_identifier_system="http://external-patients.example.org",
        subject_identifier_value="EXT-PAT-88",
        subject_identifier_use="official",
    ),
    "service_provider_fallback": _enc(
        service_provider_display="External Hospital",
        service_provider_identifier_system="http://hospitals.example.org",
        service_provider_identifier_value="HOSP-44",
        service_provider_identifier_use="official",
    ),
    "part_of_fallback": _enc(
        part_of_display="Parent Encounter",
        part_of_identifier_system="http://encounters.example.org",
        part_of_identifier_value="PARENT-ENC-1",
        part_of_identifier_use="official",
    ),
    "identifier_with_assigner_fallback": _with(
        "identifiers",
        _identifier(
            assigner_identifier_system="http://agencies.example.org",
            assigner_identifier_value="AGENCY-1",
            assigner_identifier_use="official",
        ),
    ),
    "participant_with_individual_fallback": _with(
        "participants",
        EncounterParticipant(
            id=1,
            tenant_id="org-test",
            individual_display="Dr. Consultant",
            individual_identifier_system="http://npi.example.org",
            individual_identifier_value="NPI-9988",
            individual_identifier_use="official",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "diagnosis_with_condition_fallback": _with(
        "diagnoses",
        EncounterDiagnosis(
            id=1,
            tenant_id="org-test",
            condition_display="Suspected Bronchitis",
            condition_identifier_system="http://conditions.example.org",
            condition_identifier_value="COND-555",
            rank=1,
            created_by="u-test",
            created_at=D,
        ),
    ),
    "location_with_fallback": _with(
        "locations",
        EncounterLocationRow(
            id=1,
            tenant_id="org-test",
            location_display="External Clinic Room 3",
            location_identifier_system="http://locations.example.org",
            location_identifier_value="LOC-ROOM-3",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "based_on_with_fallback": _with(
        "based_ons",
        EncounterBasedOn(
            id=1,
            tenant_id="org-test",
            reference_display="External Referral",
            reference_identifier_system="http://referrals.example.org",
            reference_identifier_value="REF-22",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "episode_of_care_with_fallback": _with(
        "episodes_of_care",
        EncounterEpisodeOfCare(
            id=1,
            tenant_id="org-test",
            reference_display="External Episode",
            reference_identifier_system="http://episodes.example.org",
            reference_identifier_value="EP-33",
            created_by="u-test",
            created_at=D,
        ),
    ),
}


@pytest.mark.parametrize("case_name", list(CASES.keys()))
def test_encounter_fhir_conformance(case_name: str):
    model = CASES[case_name]
    output = to_fhir_encounter(model)
    assert_valid(encounter_pb2.Encounter, output)
