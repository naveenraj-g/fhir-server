"""FHIR R4 conformance for `to_fhir_allergy_intolerance()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.allergy_intolerance import to_fhir_allergy_intolerance
from app.models.allergy_intolerance import (
    AllergyIntoleranceAsserterReferenceType,
    AllergyIntoleranceCategory,
    AllergyIntoleranceClinicalStatusCoding,
    AllergyIntoleranceCodeCoding,
    AllergyIntoleranceCriticality,
    AllergyIntoleranceEncounterReferenceType,
    AllergyIntoleranceIdentifier,
    AllergyIntoleranceIdentifierTypeCoding,
    AllergyIntoleranceModel,
    AllergyIntoleranceNote,
    AllergyIntoleranceNoteAuthorReferenceType,
    AllergyIntolerancePatientReferenceType,
    AllergyIntoleranceReaction,
    AllergyIntoleranceReactionExposureRouteCoding,
    AllergyIntoleranceReactionManifestation,
    AllergyIntoleranceReactionManifestationCoding,
    AllergyIntoleranceReactionNote,
    AllergyIntoleranceReactionSubstanceCoding,
    AllergyIntoleranceRecorderReferenceType,
    AllergyIntoleranceSeverity,
    AllergyIntoleranceType,
    AllergyIntoleranceVerificationStatusCoding,
)
from app.models.enums import IdentifierUse, OrganizationReferenceType

from .support import assert_valid

allergy_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.allergy_intolerance_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "clinical_status_codings",
    "verification_status_codings",
    "code_codings",
    "notes",
    "reactions",
)


def _allergy_intolerance(**overrides) -> AllergyIntoleranceModel:
    fields = {
        "id": 1,
        "allergy_intolerance_id": 260001,
        "tenant_id": "org-test",
        "patient_reference": "Patient/10001",
        "patient_type": AllergyIntolerancePatientReferenceType.Patient,
        "patient_id": 10001,
        "patient_display": "Jane Doe",
        "created_by": "u-test",
        "updated_at": D,
    }
    children = {attr: overrides.pop(attr, []) for attr in _CHILD_ATTRS}
    fields.update(overrides)
    m = AllergyIntoleranceModel(**fields)

    for attr, val in children.items():
        setattr(m, attr, val)
    return m


def test_allergy_intolerance_minimal_conformance():
    m = _allergy_intolerance()
    fhir = to_fhir_allergy_intolerance(m)
    assert_valid(allergy_pb2.AllergyIntolerance, fhir)


def test_allergy_intolerance_full_conformance():
    clin_coding = AllergyIntoleranceClinicalStatusCoding(
        allergy_intolerance_pk=1,
        tenant_id="org-test",
        system="http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
        code="active",
        display="Active",
        created_by="u-test",
    )
    ver_coding = AllergyIntoleranceVerificationStatusCoding(
        allergy_intolerance_pk=1,
        tenant_id="org-test",
        system="http://terminology.hl7.org/CodeSystem/allergyintolerance-verification",
        code="confirmed",
        display="Confirmed",
        created_by="u-test",
    )
    code_coding = AllergyIntoleranceCodeCoding(
        allergy_intolerance_pk=1,
        tenant_id="org-test",
        system="http://snomed.info/sct",
        code="227493005",
        display="Cashew nut allergy",
        created_by="u-test",
    )
    ident = AllergyIntoleranceIdentifier(
        allergy_intolerance_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        type_text="MRN",
        system="http://hospital.example.org",
        value="ALG-001",
        created_by="u-test",
    )
    ident.type_codings = [
        AllergyIntoleranceIdentifierTypeCoding(
            identifier_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="MR",
            display="Medical Record Number",
            created_by="u-test",
        )
    ]
    note = AllergyIntoleranceNote(
        allergy_intolerance_pk=1,
        tenant_id="org-test",
        text="Allergic to cashews and pistachios",
        time=D,
        author_string="Dr. Smith",
        created_by="u-test",
    )

    rx = AllergyIntoleranceReaction(
        allergy_intolerance_pk=1,
        tenant_id="org-test",
        description="Severe facial hives",
        onset=D,
        severity=AllergyIntoleranceSeverity.severe,
        substance_text="Cashew nut",
        exposure_route_text="Oral",
        created_by="u-test",
    )
    rx.substance_codings = [
        AllergyIntoleranceReactionSubstanceCoding(
            reaction_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="227493005",
            display="Cashew nut",
            created_by="u-test",
        )
    ]
    rx.exposure_route_codings = [
        AllergyIntoleranceReactionExposureRouteCoding(
            reaction_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="26643006",
            display="Oral route",
            created_by="u-test",
        )
    ]
    manif = AllergyIntoleranceReactionManifestation(
        reaction_id=1,
        tenant_id="org-test",
        text="Urticaria",
        created_by="u-test",
    )
    manif.codings = [
        AllergyIntoleranceReactionManifestationCoding(
            manifestation_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="64305001",
            display="Urticaria",
            created_by="u-test",
        )
    ]
    rx.manifestations = [manif]
    rx.notes = [
        AllergyIntoleranceReactionNote(
            reaction_id=1,
            tenant_id="org-test",
            text="EpiPen administered",
            time=D,
            created_by="u-test",
        )
    ]

    m = _allergy_intolerance(
        clinical_status_text="Active",
        verification_status_text="Confirmed",
        type=AllergyIntoleranceType.allergy,
        category=[AllergyIntoleranceCategory.food],
        criticality=AllergyIntoleranceCriticality.high,
        code_text="Cashew nut allergy",
        encounter_reference="Encounter/20001",
        encounter_type=AllergyIntoleranceEncounterReferenceType.Encounter,
        encounter_id=20001,
        encounter_display="ER visit",
        onset_date_time=D,
        recorded_date=D,
        recorder_reference="Practitioner/30001",
        recorder_type=AllergyIntoleranceRecorderReferenceType.Practitioner,
        recorder_id=30001,
        recorder_display="Dr. Smith",
        asserter_reference="Patient/10001",
        asserter_type=AllergyIntoleranceAsserterReferenceType.Patient,
        asserter_id=10001,
        asserter_display="Jane Doe",
        last_occurrence=D,
        clinical_status_codings=[clin_coding],
        verification_status_codings=[ver_coding],
        code_codings=[code_coding],
        identifiers=[ident],
        notes=[note],
        reactions=[rx],
    )

    fhir = to_fhir_allergy_intolerance(m)
    assert_valid(allergy_pb2.AllergyIntolerance, fhir)


def test_allergy_intolerance_onset_choices():
    # onsetAge
    m_age = _allergy_intolerance(
        onset_age={"value": 14, "unit": "a", "system": "http://unitsofmeasure.org", "code": "a"}
    )
    assert_valid(allergy_pb2.AllergyIntolerance, to_fhir_allergy_intolerance(m_age))

    # onsetPeriod
    m_period = _allergy_intolerance(
        onset_period_start=D,
        onset_period_end=D + dt.timedelta(days=30),
    )
    assert_valid(allergy_pb2.AllergyIntolerance, to_fhir_allergy_intolerance(m_period))

    # onsetRange
    m_range = _allergy_intolerance(
        onset_range={
            "low": {"value": 10, "unit": "a"},
            "high": {"value": 15, "unit": "a"},
        }
    )
    assert_valid(allergy_pb2.AllergyIntolerance, to_fhir_allergy_intolerance(m_range))

    # onsetString
    m_str = _allergy_intolerance(onset_string="childhood")
    assert_valid(allergy_pb2.AllergyIntolerance, to_fhir_allergy_intolerance(m_str))


def test_allergy_intolerance_categories_and_criticalities():
    for cat in AllergyIntoleranceCategory:
        m = _allergy_intolerance(category=[cat])
        assert_valid(allergy_pb2.AllergyIntolerance, to_fhir_allergy_intolerance(m))

    for crit in AllergyIntoleranceCriticality:
        m = _allergy_intolerance(criticality=crit)
        assert_valid(allergy_pb2.AllergyIntolerance, to_fhir_allergy_intolerance(m))
