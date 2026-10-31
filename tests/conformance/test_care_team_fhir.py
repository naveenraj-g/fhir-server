"""FHIR R4 conformance for `to_fhir_care_team()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.care_team import to_fhir_care_team
from app.models.care_team import (
    CareTeamAssignerReferenceType,
    CareTeamCategory,
    CareTeamCategoryCoding,
    CareTeamEncounterReferenceType,
    CareTeamIdentifier,
    CareTeamIdentifierTypeCoding,
    CareTeamManagingOrganization,
    CareTeamManagingOrganizationReferenceType,
    CareTeamModel,
    CareTeamNote,
    CareTeamNoteAuthorReferenceType,
    CareTeamParticipant,
    CareTeamParticipantMemberReferenceType,
    CareTeamParticipantOnBehalfOfReferenceType,
    CareTeamParticipantRole,
    CareTeamParticipantRoleCoding,
    CareTeamReasonCode,
    CareTeamReasonCodeCoding,
    CareTeamReasonReference,
    CareTeamReasonReferenceType,
    CareTeamStatus,
    CareTeamSubjectReferenceType,
    CareTeamTelecom,
)
from app.models.enums import IdentifierUse
from app.schemas.enums import ContactPointSystem, ContactPointUse

from .support import assert_valid

care_team_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.care_team_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "categories",
    "participants",
    "reason_codes",
    "reason_references",
    "managing_organizations",
    "telecoms",
    "notes",
)


def _care_team(**overrides) -> CareTeamModel:
    fields = {
        "id": 1,
        "care_team_id": 390001,
        "tenant_id": "org-test",
        "status": CareTeamStatus.active,
        "name": "Cardiology Care Team",
        "subject_reference": "Patient/10001",
        "subject_type": CareTeamSubjectReferenceType.Patient,
        "subject_id": 10001,
        "subject_display": "Test Patient",
        "created_by": "u-test",
        "created_at": D,
        "updated_at": D,
        "extension": [],
    }
    fields.update(overrides)
    ct = CareTeamModel(**fields)
    for attr in _CHILD_ATTRS:
        if getattr(ct, attr, None) is None:
            setattr(ct, attr, [])
    return ct


def test_minimal_care_team_conforms():
    ct = _care_team()
    out = to_fhir_care_team(ct)
    assert out["resourceType"] == "CareTeam"
    assert out["id"] == "390001"
    assert out["status"] == "active"
    assert out["name"] == "Cardiology Care Team"
    assert out["subject"]["reference"] == "Patient/10001"
    assert_valid(care_team_pb2.CareTeam, out)


def test_care_team_all_statuses():
    for status in CareTeamStatus:
        ct = _care_team(status=status)
        out = to_fhir_care_team(ct)
        assert out["status"] == status.value
        assert_valid(care_team_pb2.CareTeam, out)


def test_care_team_identifiers_conforms():
    ident = CareTeamIdentifier(
        id=1,
        care_team_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        type_text="CareTeam ID",
        system="http://example.org/careteams",
        value="CT-999",
        period_start=D,
        period_end=D,
        assigner_reference="Organization/190001",
        assigner_type=CareTeamAssignerReferenceType.Organization,
        assigner_id=190001,
        assigner_display="Acme Hospital",
        created_by="u-test",
    )
    ident.type_codings = [
        CareTeamIdentifierTypeCoding(
            id=1,
            identifier_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="PLAC",
            display="Placer Identifier",
            created_by="u-test",
        )
    ]
    ct = _care_team(identifiers=[ident])
    out = to_fhir_care_team(ct)
    assert len(out["identifier"]) == 1
    assert out["identifier"][0]["value"] == "CT-999"
    assert out["identifier"][0]["use"] == "official"
    assert out["identifier"][0]["assigner"]["reference"] == "Organization/190001"
    assert_valid(care_team_pb2.CareTeam, out)


def test_care_team_categories_conforms():
    cat = CareTeamCategory(
        id=1,
        care_team_pk=1,
        tenant_id="org-test",
        text="Longitudinal care-coordination",
        created_by="u-test",
    )
    cat.codings = [
        CareTeamCategoryCoding(
            id=1,
            category_id=1,
            tenant_id="org-test",
            system="http://loinc.org",
            code="LA27976-2",
            display="Longitudinal care-coordination",
            created_by="u-test",
        )
    ]
    ct = _care_team(categories=[cat])
    out = to_fhir_care_team(ct)
    assert len(out["category"]) == 1
    assert out["category"][0]["text"] == "Longitudinal care-coordination"
    assert out["category"][0]["coding"][0]["code"] == "LA27976-2"
    assert_valid(care_team_pb2.CareTeam, out)


def test_care_team_participants_conforms():
    part = CareTeamParticipant(
        id=1,
        care_team_pk=1,
        tenant_id="org-test",
        member_reference="Practitioner/30001",
        member_type=CareTeamParticipantMemberReferenceType.Practitioner,
        member_id=30001,
        member_display="Dr. Test",
        on_behalf_of_reference="Organization/190001",
        on_behalf_of_type=CareTeamParticipantOnBehalfOfReferenceType.Organization,
        on_behalf_of_id=190001,
        on_behalf_of_display="Acme Hospital",
        period_start=D,
        period_end=D,
        created_by="u-test",
    )
    role = CareTeamParticipantRole(
        id=1,
        participant_id=1,
        tenant_id="org-test",
        text="Lead Physician",
        created_by="u-test",
    )
    role.codings = [
        CareTeamParticipantRoleCoding(
            id=1,
            role_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="407542009",
            display="Cardiologist",
            created_by="u-test",
        )
    ]
    part.roles = [role]
    ct = _care_team(participants=[part])
    out = to_fhir_care_team(ct)
    assert len(out["participant"]) == 1
    p = out["participant"][0]
    assert p["member"]["reference"] == "Practitioner/30001"
    assert p["onBehalfOf"]["reference"] == "Organization/190001"
    assert len(p["role"]) == 1
    assert p["role"][0]["text"] == "Lead Physician"
    assert p["role"][0]["coding"][0]["code"] == "407542009"
    assert_valid(care_team_pb2.CareTeam, out)


def test_care_team_reason_code_and_reference_conforms():
    rc = CareTeamReasonCode(
        id=1,
        care_team_pk=1,
        tenant_id="org-test",
        text="Heart Failure Management",
        created_by="u-test",
    )
    rc.codings = [
        CareTeamReasonCodeCoding(
            id=1,
            reason_code_id=1,
            tenant_id="org-test",
            system="http://snomed.info/sct",
            code="84114007",
            display="Heart failure",
            created_by="u-test",
        )
    ]
    rr = CareTeamReasonReference(
        id=1,
        care_team_pk=1,
        tenant_id="org-test",
        reference_reference="Condition/120001",
        reference_type=CareTeamReasonReferenceType.Condition,
        reference_id=120001,
        reference_display="Chronic Congestive Heart Failure",
        created_by="u-test",
    )
    ct = _care_team(reason_codes=[rc], reason_references=[rr])
    out = to_fhir_care_team(ct)
    assert len(out["reasonCode"]) == 1
    assert out["reasonCode"][0]["coding"][0]["code"] == "84114007"
    assert len(out["reasonReference"]) == 1
    assert out["reasonReference"][0]["reference"] == "Condition/120001"
    assert_valid(care_team_pb2.CareTeam, out)


def test_care_team_managing_organization_conforms():
    mo = CareTeamManagingOrganization(
        id=1,
        care_team_pk=1,
        tenant_id="org-test",
        reference_reference="Organization/190001",
        reference_type=CareTeamManagingOrganizationReferenceType.Organization,
        reference_id=190001,
        reference_display="Acme Clinic",
        created_by="u-test",
    )
    ct = _care_team(managing_organizations=[mo])
    out = to_fhir_care_team(ct)
    assert len(out["managingOrganization"]) == 1
    assert out["managingOrganization"][0]["reference"] == "Organization/190001"
    assert_valid(care_team_pb2.CareTeam, out)


def test_care_team_telecom_conforms():
    tel = CareTeamTelecom(
        id=1,
        care_team_pk=1,
        tenant_id="org-test",
        system=ContactPointSystem.phone,
        value="+1-555-555-5555",
        use=ContactPointUse.work,
        rank=1,
        created_by="u-test",
    )
    ct = _care_team(telecoms=[tel])
    out = to_fhir_care_team(ct)
    assert len(out["telecom"]) == 1
    assert out["telecom"][0]["system"] == "phone"
    assert out["telecom"][0]["value"] == "+1-555-555-5555"
    assert out["telecom"][0]["use"] == "work"
    assert out["telecom"][0]["rank"] == 1
    assert_valid(care_team_pb2.CareTeam, out)


def test_care_team_notes_conforms():
    note = CareTeamNote(
        id=1,
        care_team_pk=1,
        tenant_id="org-test",
        author_reference_reference="Practitioner/30001",
        author_reference_type=CareTeamNoteAuthorReferenceType.Practitioner,
        author_reference_id=30001,
        author_reference_display="Dr. Test",
        time=D,
        text="Care plan review scheduled for next week.",
        created_by="u-test",
    )
    ct = _care_team(notes=[note])
    out = to_fhir_care_team(ct)
    assert len(out["note"]) == 1
    assert out["note"][0]["text"] == "Care plan review scheduled for next week."
    assert out["note"][0]["authorReference"]["reference"] == "Practitioner/30001"
    assert_valid(care_team_pb2.CareTeam, out)


def test_care_team_encounter_and_period_conforms():
    ct = _care_team(
        encounter_reference="Encounter/20001",
        encounter_type=CareTeamEncounterReferenceType.Encounter,
        encounter_id=20001,
        encounter_display="Initial Consultation",
        period_start=D,
        period_end=D,
    )
    out = to_fhir_care_team(ct)
    assert out["encounter"]["reference"] == "Encounter/20001"
    assert out["period"]["start"] == D.isoformat()
    assert out["period"]["end"] == D.isoformat()
    assert_valid(care_team_pb2.CareTeam, out)
