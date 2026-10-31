"""FHIR R4 conformance for `to_fhir_condition()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.condition import to_fhir_condition
from app.models.condition import (
    ConditionAsserterReferenceType,
    ConditionBodySite,
    ConditionBodySiteCoding,
    ConditionCategory,
    ConditionCategoryCoding,
    ConditionClinicalStatusCoding,
    ConditionCodeCoding,
    ConditionEvidence,
    ConditionEvidenceCode,
    ConditionEvidenceCodeCoding,
    ConditionEvidenceDetail,
    ConditionIdentifier,
    ConditionIdentifierTypeCoding,
    ConditionModel,
    ConditionNote,
    ConditionNoteAuthorReferenceType,
    ConditionQuantityComparator as ConditionQuantityComparatorModel,
    ConditionRecorderReferenceType,
    ConditionSeverityCoding,
    ConditionStage,
    ConditionStageAssessment,
    ConditionStageAssessmentReferenceType,
    ConditionStageSummaryCoding,
    ConditionStageTypeCoding,
    ConditionVerificationStatusCoding,
)
from app.models.enums import (
    EncounterReferenceType,
    IdentifierUse,
    OrganizationReferenceType,
    SubjectReferenceType,
)

from .support import assert_valid

condition_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.condition_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "clinical_status_codings",
    "verification_status_codings",
    "categories",
    "severity_codings",
    "code_codings",
    "body_sites",
    "stages",
    "evidence",
    "notes",
)


def _condition(**overrides) -> ConditionModel:
    fields = {
        "id": 1,
        "condition_id": 120001,
        "tenant_id": "org-test",
        "subject_reference": "Patient/10001",
        "subject_type": SubjectReferenceType.Patient,
        "subject_id": 10001,
        "subject_display": "Jane Doe",
        "created_by": "u-test",
        "created_at": D,
        "updated_at": D,
        "extension": [],
    }
    fields.update(overrides)
    c = ConditionModel(**fields)
    for attr in _CHILD_ATTRS:
        if getattr(c, attr, None) is None:
            setattr(c, attr, [])
    return c


def test_minimal_condition_conforms():
    c = _condition()
    out = to_fhir_condition(c)
    assert out["resourceType"] == "Condition"
    assert out["id"] == "120001"
    assert out["subject"]["reference"] == "Patient/10001"
    assert_valid(condition_pb2.Condition, out)


def test_clinical_and_verification_status():
    c = _condition(
        clinical_status_text="Active",
        verification_status_text="Confirmed",
    )
    c.clinical_status_codings = [
        ConditionClinicalStatusCoding(
            id=1,
            condition_pk=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/condition-clinical",
            code="active",
            display="Active",
            created_by="u-test",
            created_at=D,
        )
    ]
    c.verification_status_codings = [
        ConditionVerificationStatusCoding(
            id=1,
            condition_pk=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/condition-ver-status",
            code="confirmed",
            display="Confirmed",
            created_by="u-test",
            created_at=D,
        )
    ]
    out = to_fhir_condition(c)
    assert out["clinicalStatus"]["coding"][0]["code"] == "active"
    assert out["verificationStatus"]["coding"][0]["code"] == "confirmed"
    assert_valid(condition_pb2.Condition, out)


def test_category_and_severity_and_code():
    c = _condition(
        severity_text="Severe",
        code_text="Hypertension",
    )
    cat = ConditionCategory(
        id=1,
        condition_pk=1,
        tenant_id="org-test",
        text="Problem List Item",
        created_by="u-test",
        created_at=D,
    )
    cat.codings = [
        ConditionCategoryCoding(
            id=1,
            condition_category_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/condition-category",
            code="problem-list-item",
            display="Problem List Item",
            created_by="u-test",
            created_at=D,
        )
    ]
    c.categories = [cat]

    c.severity_codings = [
        ConditionSeverityCoding(
            id=1,
            condition_pk=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="24484000",
            display="Severe",
            created_by="u-test",
            created_at=D,
        )
    ]
    c.code_codings = [
        ConditionCodeCoding(
            id=1,
            condition_pk=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="38341003",
            display="Hypertension",
            created_by="u-test",
            created_at=D,
        )
    ]
    out = to_fhir_condition(c)
    assert len(out["category"]) == 1
    assert out["severity"]["text"] == "Severe"
    assert out["code"]["coding"][0]["code"] == "38341003"
    assert_valid(condition_pb2.Condition, out)


def test_body_site():
    c = _condition()
    bs = ConditionBodySite(
        id=1,
        condition_pk=1,
        tenant_id="org-test",
        text="Left arm",
        created_by="u-test",
        created_at=D,
    )
    bs.codings = [
        ConditionBodySiteCoding(
            id=1,
            condition_body_site_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="368209003",
            display="Right arm structure",
            created_by="u-test",
            created_at=D,
        )
    ]
    c.body_sites = [bs]
    out = to_fhir_condition(c)
    assert out["bodySite"][0]["coding"][0]["code"] == "368209003"
    assert_valid(condition_pb2.Condition, out)


def test_encounter_reference():
    c = _condition(
        encounter_reference="Encounter/20001",
        encounter_type=EncounterReferenceType.Encounter,
        encounter_id=20001,
        encounter_display="Annual physical",
    )
    out = to_fhir_condition(c)
    assert out["encounter"]["reference"] == "Encounter/20001"
    assert out["encounter"]["display"] == "Annual physical"
    assert_valid(condition_pb2.Condition, out)


def test_onset_choice_variants():
    # DateTime
    c_dt = _condition(onset_date_time=D)
    assert_valid(condition_pb2.Condition, to_fhir_condition(c_dt))

    # Age (Quantity)
    c_age = _condition(
        onset_age_value=45.0,
        onset_age_comparator=ConditionQuantityComparatorModel.ge,
        onset_age_unit="a",
        onset_age_system="http://unitsofmeasure.org",
        onset_age_code="a",
    )
    out_age = to_fhir_condition(c_age)
    assert out_age["onsetAge"]["value"] == 45.0
    assert out_age["onsetAge"]["comparator"] == ">="
    assert_valid(condition_pb2.Condition, out_age)

    # Period
    c_per = _condition(onset_period_start=D, onset_period_end=D)
    out_per = to_fhir_condition(c_per)
    assert "onsetPeriod" in out_per
    assert_valid(condition_pb2.Condition, out_per)

    # Range
    c_rng = _condition(
        onset_range_low_value=20.0,
        onset_range_low_unit="a",
        onset_range_high_value=30.0,
        onset_range_high_unit="a",
    )
    out_rng = to_fhir_condition(c_rng)
    assert "onsetRange" in out_rng
    assert_valid(condition_pb2.Condition, out_rng)

    # String
    c_str = _condition(onset_string="approx. 2 years ago")
    out_str = to_fhir_condition(c_str)
    assert out_str["onsetString"] == "approx. 2 years ago"
    assert_valid(condition_pb2.Condition, out_str)


def test_abatement_choice_variants():
    # DateTime
    c_dt = _condition(abatement_date_time=D)
    assert_valid(condition_pb2.Condition, to_fhir_condition(c_dt))

    # Age (Quantity)
    c_age = _condition(
        abatement_age_value=50.0,
        abatement_age_unit="a",
        abatement_age_system="http://unitsofmeasure.org",
        abatement_age_code="a",
    )
    out_age = to_fhir_condition(c_age)
    assert out_age["abatementAge"]["value"] == 50.0
    assert_valid(condition_pb2.Condition, out_age)

    # Period
    c_per = _condition(abatement_period_start=D, abatement_period_end=D)
    assert_valid(condition_pb2.Condition, to_fhir_condition(c_per))

    # Range
    c_rng = _condition(
        abatement_range_low_value=40.0,
        abatement_range_high_value=50.0,
    )
    assert_valid(condition_pb2.Condition, to_fhir_condition(c_rng))

    # String
    c_str = _condition(abatement_string="around retirement")
    out_str = to_fhir_condition(c_str)
    assert out_str["abatementString"] == "around retirement"
    assert_valid(condition_pb2.Condition, out_str)


def test_recorder_and_asserter():
    c = _condition(
        recorder_reference="Practitioner/30001",
        recorder_type=ConditionRecorderReferenceType.Practitioner,
        recorder_id=30001,
        recorder_display="Dr. Smith",
        asserter_reference="Patient/10001",
        asserter_type=ConditionAsserterReferenceType.Patient,
        asserter_id=10001,
        asserter_display="Self",
        recorded_date=D,
    )
    out = to_fhir_condition(c)
    assert out["recorder"]["reference"] == "Practitioner/30001"
    assert out["asserter"]["reference"] == "Patient/10001"
    assert out["recordedDate"] == D.isoformat()
    assert_valid(condition_pb2.Condition, out)


def test_stage_with_assessments_and_type():
    c = _condition()
    stage = ConditionStage(
        id=1,
        condition_pk=1,
        tenant_id="org-test",
        summary_text="Stage II",
        type_text="Clinical staging",
        created_by="u-test",
        created_at=D,
    )
    stage.summary_codings = [
        ConditionStageSummaryCoding(
            id=1,
            condition_stage_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="261614003",
            display="Stage II",
            created_by="u-test",
            created_at=D,
        )
    ]
    stage.type_codings = [
        ConditionStageTypeCoding(
            id=1,
            condition_stage_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="260998006",
            display="Clinical staging",
            created_by="u-test",
            created_at=D,
        )
    ]
    stage.assessments = [
        ConditionStageAssessment(
            id=1,
            condition_stage_id=1,
            tenant_id="org-test",
            reference_reference="Observation/160001",
            reference_type=ConditionStageAssessmentReferenceType.Observation,
            reference_id=160001,
            reference_display="Biopsy assessment",
            created_by="u-test",
            created_at=D,
        )
    ]
    c.stages = [stage]
    out = to_fhir_condition(c)
    assert len(out["stage"]) == 1
    assert out["stage"][0]["summary"]["text"] == "Stage II"
    assert out["stage"][0]["assessment"][0]["reference"] == "Observation/160001"
    assert_valid(condition_pb2.Condition, out)


def test_evidence_with_codes_and_details():
    c = _condition()
    ev = ConditionEvidence(
        id=1,
        condition_pk=1,
        tenant_id="org-test",
        created_by="u-test",
        created_at=D,
    )
    code = ConditionEvidenceCode(
        id=1,
        condition_evidence_id=1,
        tenant_id="org-test",
        text="Headache",
        created_by="u-test",
        created_at=D,
    )
    code.codings = [
        ConditionEvidenceCodeCoding(
            id=1,
            condition_evidence_code_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="25064002",
            display="Headache",
            created_by="u-test",
            created_at=D,
        )
    ]
    ev.codes = [code]
    ev.details = [
        ConditionEvidenceDetail(
            id=1,
            condition_evidence_id=1,
            tenant_id="org-test",
            reference_reference="Observation/160002",
            reference_type="Observation",
            reference_id=160002,
            reference_display="BP reading",
            created_by="u-test",
            created_at=D,
        )
    ]
    c.evidence = [ev]
    out = to_fhir_condition(c)
    assert len(out["evidence"]) == 1
    assert out["evidence"][0]["code"][0]["text"] == "Headache"
    assert out["evidence"][0]["detail"][0]["reference"] == "Observation/160002"
    assert_valid(condition_pb2.Condition, out)


def test_note_annotation():
    c = _condition()
    c.notes = [
        ConditionNote(
            id=1,
            condition_pk=1,
            tenant_id="org-test",
            author_reference="Practitioner/30001",
            author_type=ConditionNoteAuthorReferenceType.Practitioner,
            author_id=30001,
            author_display="Dr. Smith",
            time=D,
            text="Patient responding well to treatment",
            created_by="u-test",
            created_at=D,
        ),
        ConditionNote(
            id=2,
            condition_pk=1,
            tenant_id="org-test",
            author_string="Nurse Jane",
            time=D,
            text="Follow-up scheduled in 2 weeks",
            created_by="u-test",
            created_at=D,
        ),
    ]
    out = to_fhir_condition(c)
    assert len(out["note"]) == 2
    assert out["note"][0]["authorReference"]["reference"] == "Practitioner/30001"
    assert out["note"][1]["authorString"] == "Nurse Jane"
    assert_valid(condition_pb2.Condition, out)


def test_identifier_with_type_and_assigner():
    c = _condition()
    ident = ConditionIdentifier(
        id=1,
        condition_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        system="http://hospital.example.org/conditions",
        value="COND-12345",
        period_start=D,
        period_end=D,
        assigner_reference="Organization/190001",
        assigner_type=OrganizationReferenceType.Organization,
        assigner_id=190001,
        assigner_display="City Hospital",
        created_by="u-test",
        created_at=D,
    )
    ident.type_codings = [
        ConditionIdentifierTypeCoding(
            id=1,
            condition_identifier_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="MR",
            display="Medical record number",
            created_by="u-test",
            created_at=D,
        )
    ]
    c.identifiers = [ident]
    out = to_fhir_condition(c)
    assert len(out["identifier"]) == 1
    assert out["identifier"][0]["value"] == "COND-12345"
    assert out["identifier"][0]["assigner"]["reference"] == "Organization/190001"
    assert_valid(condition_pb2.Condition, out)


def test_full_condition_conforms():
    c = _condition(
        clinical_status_text="Active",
        verification_status_text="Confirmed",
        severity_text="Mild",
        code_text="Essential hypertension",
        encounter_reference="Encounter/20001",
        encounter_type=EncounterReferenceType.Encounter,
        encounter_id=20001,
        encounter_display="Checkup",
        onset_date_time=D,
        recorded_date=D,
        recorder_reference="Practitioner/30001",
        recorder_type=ConditionRecorderReferenceType.Practitioner,
        recorder_id=30001,
    )
    c.clinical_status_codings = [
        ConditionClinicalStatusCoding(
            id=1,
            condition_pk=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/condition-clinical",
            code="active",
            display="Active",
            created_by="u-test",
            created_at=D,
        )
    ]
    c.code_codings = [
        ConditionCodeCoding(
            id=1,
            condition_pk=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="59621000",
            display="Essential hypertension",
            created_by="u-test",
            created_at=D,
        )
    ]
    out = to_fhir_condition(c)
    assert_valid(condition_pb2.Condition, out)
