"""FHIR R4 conformance for `to_fhir_family_member_history()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.family_member_history import to_fhir_family_member_history
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.family_member_history import (
    FamilyMemberHistoryCondition,
    FamilyMemberHistoryConditionCodeCoding,
    FamilyMemberHistoryConditionNote,
    FamilyMemberHistoryConditionOutcomeCoding,
    FamilyMemberHistoryDataAbsentReasonCoding,
    FamilyMemberHistoryIdentifier,
    FamilyMemberHistoryIdentifierTypeCoding,
    FamilyMemberHistoryModel,
    FamilyMemberHistoryNote,
    FamilyMemberHistoryNoteAuthorReferenceType,
    FamilyMemberHistoryPatientReferenceType,
    FamilyMemberHistoryQuantityComparator,
    FamilyMemberHistoryReasonCode,
    FamilyMemberHistoryReasonCodeCoding,
    FamilyMemberHistoryReasonReference,
    FamilyMemberHistoryReasonReferenceType,
    FamilyMemberHistoryRelationshipCoding,
    FamilyMemberHistorySexCoding,
    FamilyMemberHistoryStatus,
)

from .support import assert_valid

family_history_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.family_member_history_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "data_absent_reason_codings",
    "relationship_codings",
    "sex_codings",
    "reason_codes",
    "reason_references",
    "notes",
    "conditions",
)


def _family_member_history(**overrides) -> FamilyMemberHistoryModel:
    fields = {
        "id": 1,
        "family_member_history_id": 490001,
        "tenant_id": "org-test",
        "status": FamilyMemberHistoryStatus.completed,
        "patient_reference": "Patient/10001",
        "patient_type": FamilyMemberHistoryPatientReferenceType.Patient,
        "patient_id": 10001,
        "patient_display": "Jane Doe",
        "relationship_text": "Father",
        "created_by": "u-test",
        "updated_at": D,
    }
    children = {attr: overrides.pop(attr, []) for attr in _CHILD_ATTRS}
    fields.update(overrides)
    m = FamilyMemberHistoryModel(**fields)

    for attr, val in children.items():
        setattr(m, attr, val)
    return m


def test_family_member_history_minimal_conformance():
    m = _family_member_history()
    m.relationship_codings = [
        FamilyMemberHistoryRelationshipCoding(
            family_member_history_pk=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v3-RoleCode",
            code="FTH",
            display="father",
            created_by="u-test",
        )
    ]
    fhir = to_fhir_family_member_history(m)
    assert_valid(family_history_pb2.FamilyMemberHistory, fhir)


def test_family_member_history_full_conformance():
    ident = FamilyMemberHistoryIdentifier(
        family_member_history_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        type_text="MRN",
        system="http://hospital.example.org",
        value="FMH-001",
        created_by="u-test",
    )
    ident.type_codings = [
        FamilyMemberHistoryIdentifierTypeCoding(
            family_member_history_identifier_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="MR",
            display="Medical Record Number",
            created_by="u-test",
        )
    ]

    rel_coding = FamilyMemberHistoryRelationshipCoding(
        family_member_history_pk=1,
        tenant_id="org-test",
        system="http://terminology.hl7.org/CodeSystem/v3-RoleCode",
        code="FTH",
        display="father",
        created_by="u-test",
    )

    sex_coding = FamilyMemberHistorySexCoding(
        family_member_history_pk=1,
        tenant_id="org-test",
        system="http://hl7.org/fhir/administrative-gender",
        code="male",
        display="Male",
        created_by="u-test",
    )

    reason_code = FamilyMemberHistoryReasonCode(
        family_member_history_pk=1,
        tenant_id="org-test",
        text="Family history of Type 2 Diabetes",
        created_by="u-test",
    )
    reason_code.codings = [
        FamilyMemberHistoryReasonCodeCoding(
            family_member_history_reason_code_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="44054006",
            display="Type 2 diabetes mellitus",
            created_by="u-test",
        )
    ]

    reason_ref = FamilyMemberHistoryReasonReference(
        family_member_history_pk=1,
        tenant_id="org-test",
        reference_reference="Condition/120001",
        reference_type=FamilyMemberHistoryReasonReferenceType.Condition,
        reference_id=120001,
        reference_display="Father diabetes condition",
        created_by="u-test",
    )

    note = FamilyMemberHistoryNote(
        family_member_history_pk=1,
        tenant_id="org-test",
        text="Father was diagnosed with diabetes in his early 50s.",
        time=D,
        author_string="Dr. Alice Smith",
        created_by="u-test",
    )

    cond = FamilyMemberHistoryCondition(
        family_member_history_pk=1,
        tenant_id="org-test",
        code_text="Type 2 Diabetes",
        outcome_text="Alive and well",
        contributed_to_death=False,
        onset_age_value=52.0,
        onset_age_unit="a",
        onset_age_system="http://unitsofmeasure.org",
        onset_age_code="a",
        created_by="u-test",
    )
    cond.code_codings = [
        FamilyMemberHistoryConditionCodeCoding(
            family_member_history_condition_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="44054006",
            display="Type 2 diabetes mellitus",
            created_by="u-test",
        )
    ]
    cond.outcome_codings = [
        FamilyMemberHistoryConditionOutcomeCoding(
            family_member_history_condition_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/condition-outcome",
            code="alive",
            display="Alive",
            created_by="u-test",
        )
    ]
    cond.notes = [
        FamilyMemberHistoryConditionNote(
            family_member_history_condition_id=1,
            tenant_id="org-test",
            text="Condition controlled with diet and oral medications.",
            time=D,
            created_by="u-test",
        )
    ]

    m = _family_member_history(
        date=D,
        name="John Doe",
        born_date=dt.date(1950, 5, 12),
        age_age_value=75.0,
        age_age_unit="a",
        age_age_system="http://unitsofmeasure.org",
        age_age_code="a",
        estimated_age=False,
        deceased_boolean=False,
        identifiers=[ident],
        relationship_codings=[rel_coding],
        sex_codings=[sex_coding],
        reason_codes=[reason_code],
        reason_references=[reason_ref],
        notes=[note],
        conditions=[cond],
    )

    fhir = to_fhir_family_member_history(m)
    assert_valid(family_history_pb2.FamilyMemberHistory, fhir)
