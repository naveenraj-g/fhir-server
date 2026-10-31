"""FHIR R4 conformance for `to_fhir_episode_of_care()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.episode_of_care import to_fhir_episode_of_care
from app.models.episode_of_care import (
    EpisodeOfCareAccount,
    EpisodeOfCareAccountReferenceType,
    EpisodeOfCareAssignerReferenceType,
    EpisodeOfCareCareManagerReferenceType,
    EpisodeOfCareDiagnosis,
    EpisodeOfCareDiagnosisConditionReferenceType,
    EpisodeOfCareDiagnosisRoleCoding,
    EpisodeOfCareIdentifier,
    EpisodeOfCareIdentifierTypeCoding,
    EpisodeOfCareManagingOrganizationReferenceType,
    EpisodeOfCareModel,
    EpisodeOfCarePatientReferenceType,
    EpisodeOfCareReferralRequest,
    EpisodeOfCareReferralRequestReferenceType,
    EpisodeOfCareStatus,
    EpisodeOfCareStatusHistory,
    EpisodeOfCareTeam,
    EpisodeOfCareTeamReferenceType,
    EpisodeOfCareType,
    EpisodeOfCareTypeCoding,
)
from app.models.enums import IdentifierUse

from .support import assert_valid

episode_of_care_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.episode_of_care_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "status_history",
    "types",
    "diagnoses",
    "referral_requests",
    "teams",
    "accounts",
)


def _episode_of_care(**overrides) -> EpisodeOfCareModel:
    fields = {
        "id": 1,
        "episode_of_care_id": 350001,
        "tenant_id": "org-test",
        "status": EpisodeOfCareStatus.active,
        "patient_reference": "Patient/10001",
        "patient_type": EpisodeOfCarePatientReferenceType.Patient,
        "patient_id": 10001,
        "patient_display": "Test Patient",
        "managing_organization_reference": "Organization/190001",
        "managing_organization_type": EpisodeOfCareManagingOrganizationReferenceType.Organization,
        "managing_organization_id": 190001,
        "managing_organization_display": "Acme Hospital",
        "period_start": D,
        "period_end": D,
        "care_manager_reference": "Practitioner/30001",
        "care_manager_type": EpisodeOfCareCareManagerReferenceType.Practitioner,
        "care_manager_id": 30001,
        "care_manager_display": "Dr. House",
        "created_by": "u-test",
        "created_at": D,
        "updated_at": D,
        "extension": [],
    }
    fields.update(overrides)
    eoc = EpisodeOfCareModel(**fields)
    for attr in _CHILD_ATTRS:
        if getattr(eoc, attr, None) is None:
            setattr(eoc, attr, [])
    return eoc


def test_minimal_episode_of_care_conforms():
    eoc = _episode_of_care()
    out = to_fhir_episode_of_care(eoc)
    assert out["resourceType"] == "EpisodeOfCare"
    assert out["id"] == "350001"
    assert out["status"] == "active"
    assert out["patient"]["reference"] == "Patient/10001"
    assert out["managingOrganization"]["reference"] == "Organization/190001"
    assert out["careManager"]["reference"] == "Practitioner/30001"
    assert_valid(episode_of_care_pb2.EpisodeOfCare, out)


def test_episode_of_care_all_statuses():
    for status in EpisodeOfCareStatus:
        eoc = _episode_of_care(status=status)
        out = to_fhir_episode_of_care(eoc)
        assert out["status"] == status.value
        assert_valid(episode_of_care_pb2.EpisodeOfCare, out)


def test_episode_of_care_identifiers_conforms():
    ident = EpisodeOfCareIdentifier(
        id=1,
        episode_of_care_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        type_text="Episode ID",
        system="http://example.org/episodes",
        value="EOC-999",
        period_start=D,
        period_end=D,
        assigner_reference="Organization/190001",
        assigner_type=EpisodeOfCareAssignerReferenceType.Organization,
        assigner_id=190001,
        assigner_display="Acme Hospital",
        created_by="u-test",
    )
    ident.type_codings = [
        EpisodeOfCareIdentifierTypeCoding(
            id=1,
            identifier_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="PLAC",
            display="Placer Identifier",
            created_by="u-test",
        )
    ]
    eoc = _episode_of_care(identifiers=[ident])
    out = to_fhir_episode_of_care(eoc)
    assert len(out["identifier"]) == 1
    assert out["identifier"][0]["value"] == "EOC-999"
    assert out["identifier"][0]["use"] == "official"
    assert out["identifier"][0]["assigner"]["reference"] == "Organization/190001"
    assert_valid(episode_of_care_pb2.EpisodeOfCare, out)


def test_episode_of_care_status_history_conforms():
    sh = EpisodeOfCareStatusHistory(
        id=1,
        episode_of_care_pk=1,
        tenant_id="org-test",
        status=EpisodeOfCareStatus.planned,
        period_start=D,
        period_end=D,
        created_by="u-test",
    )
    eoc = _episode_of_care(status_history=[sh])
    out = to_fhir_episode_of_care(eoc)
    assert len(out["statusHistory"]) == 1
    assert out["statusHistory"][0]["status"] == "planned"
    assert "period" in out["statusHistory"][0]
    assert_valid(episode_of_care_pb2.EpisodeOfCare, out)


def test_episode_of_care_type_conforms():
    tp = EpisodeOfCareType(
        id=1,
        episode_of_care_pk=1,
        tenant_id="org-test",
        text="Home and Community Care",
        created_by="u-test",
    )
    tp.codings = [
        EpisodeOfCareTypeCoding(
            id=1,
            type_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/episodeofcare-type",
            code="hacc",
            display="Home and Community Care",
            created_by="u-test",
        )
    ]
    eoc = _episode_of_care(types=[tp])
    out = to_fhir_episode_of_care(eoc)
    assert len(out["type"]) == 1
    assert out["type"][0]["text"] == "Home and Community Care"
    assert out["type"][0]["coding"][0]["code"] == "hacc"
    assert_valid(episode_of_care_pb2.EpisodeOfCare, out)


def test_episode_of_care_diagnosis_conforms():
    diag = EpisodeOfCareDiagnosis(
        id=1,
        episode_of_care_pk=1,
        tenant_id="org-test",
        condition_reference="Condition/120001",
        condition_type=EpisodeOfCareDiagnosisConditionReferenceType.Condition,
        condition_id=120001,
        condition_display="Type 2 Diabetes",
        role_text="Primary Diagnosis",
        rank=1,
        created_by="u-test",
    )
    diag.role_codings = [
        EpisodeOfCareDiagnosisRoleCoding(
            id=1,
            diagnosis_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/diagnosis-role",
            code="CC",
            display="Chief complaint",
            created_by="u-test",
        )
    ]
    eoc = _episode_of_care(diagnoses=[diag])
    out = to_fhir_episode_of_care(eoc)
    assert len(out["diagnosis"]) == 1
    assert out["diagnosis"][0]["condition"]["reference"] == "Condition/120001"
    assert out["diagnosis"][0]["rank"] == 1
    assert out["diagnosis"][0]["role"]["text"] == "Primary Diagnosis"
    assert_valid(episode_of_care_pb2.EpisodeOfCare, out)


def test_episode_of_care_all_references_conforms():
    rr = EpisodeOfCareReferralRequest(
        id=1,
        episode_of_care_pk=1,
        tenant_id="org-test",
        reference_reference="ServiceRequest/80001",
        reference_type=EpisodeOfCareReferralRequestReferenceType.ServiceRequest,
        reference_id=80001,
        reference_display="Referral for Cardiology",
        created_by="u-test",
    )
    tm = EpisodeOfCareTeam(
        id=1,
        episode_of_care_pk=1,
        tenant_id="org-test",
        reference_reference="CareTeam/390001",
        reference_type=EpisodeOfCareTeamReferenceType.CareTeam,
        reference_id=390001,
        reference_display="Cardiology Care Team",
        created_by="u-test",
    )
    acc = EpisodeOfCareAccount(
        id=1,
        episode_of_care_pk=1,
        tenant_id="org-test",
        reference_reference="Account/1",
        reference_type=EpisodeOfCareAccountReferenceType.Account,
        reference_id=1,
        reference_display="Hospital Account",
        created_by="u-test",
    )
    eoc = _episode_of_care(
        referral_requests=[rr],
        teams=[tm],
        accounts=[acc],
    )
    out = to_fhir_episode_of_care(eoc)
    assert len(out["referralRequest"]) == 1
    assert out["referralRequest"][0]["reference"] == "ServiceRequest/80001"
    assert len(out["team"]) == 1
    assert out["team"][0]["reference"] == "CareTeam/390001"
    assert len(out["account"]) == 1
    assert out["account"][0]["reference"] == "Account/1"
    assert_valid(episode_of_care_pb2.EpisodeOfCare, out)


def test_episode_of_care_extension_conforms():
    ext = [
        {
            "url": "http://example.org/fhir/StructureDefinition/eoc-note",
            "valueString": "Patient enrolled via remote onboarding program",
        }
    ]
    eoc = _episode_of_care(extension=ext)
    out = to_fhir_episode_of_care(eoc)
    assert out["extension"] == ext
    assert_valid(episode_of_care_pb2.EpisodeOfCare, out)
