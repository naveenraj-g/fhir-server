"""FHIR R4 conformance for `to_fhir_observation()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.observation import to_fhir_observation
from app.models.enums import IdentifierUse, OrganizationReferenceType
from app.models.observation import (
    ObservationCodeCoding,
    ObservationComponent,
    ObservationComponentCodeCoding,
    ObservationIdentifier,
    ObservationIdentifierTypeCoding,
    ObservationModel,
    ObservationNote,
    ObservationPerformer,
    ObservationPerformerReferenceType,
    ObservationStatus,
    ObservationSubjectReferenceType,
)

from .support import assert_valid

observation_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.observation_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "categories",
    "code_codings",
    "based_on",
    "part_of",
    "performers",
    "value_codeable_concept_codings",
    "interpretations",
    "notes",
    "body_site_codings",
    "method_codings",
    "specimens",
    "devices",
    "reference_ranges",
    "has_members",
    "derived_from",
    "components",
    "focuses",
)


def _observation(**overrides) -> ObservationModel:
    fields = {
        "id": 1,
        "observation_id": 160001,
        "tenant_id": "org-test",
        "status": ObservationStatus.final,
        "code_text": "Vital signs",
        "subject_reference": "Patient/10001",
        "subject_type": ObservationSubjectReferenceType.Patient,
        "subject_id": 10001,
        "subject_display": "Jane Doe",
        "created_by": "u-test",
        "updated_at": D,
    }
    children = {attr: overrides.pop(attr, []) for attr in _CHILD_ATTRS}
    fields.update(overrides)
    m = ObservationModel(**fields)

    for attr, val in children.items():
        setattr(m, attr, val)
    return m


def test_observation_minimal_conformance():
    code_coding = ObservationCodeCoding(
        id=1,
        observation_pk=1,
        tenant_id="org-test",
        system="http://loinc.org",
        code="85354-9",
        display="Blood pressure panel",
        created_by="u-test",
        created_at=D,
    )
    m = _observation(code_codings=[code_coding])
    fhir = to_fhir_observation(m)
    assert_valid(observation_pb2.Observation, fhir)


def test_observation_full_conformance():
    code_coding = ObservationCodeCoding(
        id=1,
        observation_pk=1,
        tenant_id="org-test",
        system="http://loinc.org",
        code="883-9",
        display="ABO group",
        created_by="u-test",
        created_at=D,
    )
    ident = ObservationIdentifier(
        id=1,
        observation_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        system="http://hospital.example.org",
        value="OBS-001",
        created_by="u-test",
        created_at=D,
    )
    ident.type_codings = [
        ObservationIdentifierTypeCoding(
            id=1,
            observation_identifier_id=1,
            tenant_id="org-test",
            system="http://terminology.hl7.org/CodeSystem/v2-0203",
            code="FILL",
            display="Filler Identifier",
            created_by="u-test",
            created_at=D,
        )
    ]
    performer = ObservationPerformer(
        id=1,
        observation_pk=1,
        tenant_id="org-test",
        reference_reference="Practitioner/30001",
        reference_type=ObservationPerformerReferenceType.Practitioner,
        reference_id=30001,
        reference_display="Dr. Smith",
        created_by="u-test",
        created_at=D,
    )
    note = ObservationNote(
        id=1,
        observation_pk=1,
        tenant_id="org-test",
        text="Normal reading",
        time=D,
        author_string="Dr. Smith",
        created_by="u-test",
        created_at=D,
    )
    comp = ObservationComponent(
        id=1,
        observation_pk=1,
        tenant_id="org-test",
        code_text="Systolic blood pressure",
        value_quantity_value=120,
        value_quantity_unit="mmHg",
        value_quantity_system="http://unitsofmeasure.org",
        value_quantity_code="mm[Hg]",
        created_by="u-test",
        created_at=D,
    )
    comp.code_codings = [
        ObservationComponentCodeCoding(
            id=1,
            observation_component_id=1,
            tenant_id="org-test",
            system="http://loinc.org",
            code="8480-6",
            display="Systolic blood pressure",
            created_by="u-test",
            created_at=D,
        )
    ]
    m = _observation(
        effective_date_time=D,
        value_string="Type A+",
        code_codings=[code_coding],
        identifiers=[ident],
        performers=[performer],
        notes=[note],
        components=[comp],
    )
    fhir = to_fhir_observation(m)
    assert_valid(observation_pb2.Observation, fhir)


def test_observation_reference_fallback_identifiers():
    code_coding = ObservationCodeCoding(
        id=1,
        observation_pk=1,
        tenant_id="org-test",
        system="http://loinc.org",
        code="85354-9",
        display="Blood pressure panel",
        created_by="u-test",
        created_at=D,
    )
    ident = ObservationIdentifier(
        id=1,
        observation_pk=1,
        tenant_id="org-test",
        use=IdentifierUse.official,
        system="http://hospital.example.org",
        value="OBS-001",
        assigner_reference=None,
        assigner_type=None,
        assigner_id=None,
        assigner_identifier_system="http://hospital.example.org/orgs",
        assigner_identifier_value="ORG-1111",
        created_by="u-test",
        created_at=D,
    )
    performer = ObservationPerformer(
        id=1,
        observation_pk=1,
        tenant_id="org-test",
        reference_reference=None,
        reference_type=None,
        reference_id=None,
        reference_identifier_system="http://hospital.example.org/practitioners",
        reference_identifier_value="PRAC-7777",
        created_by="u-test",
        created_at=D,
    )
    note = ObservationNote(
        id=1,
        observation_pk=1,
        tenant_id="org-test",
        text="Normal reading",
        time=D,
        author_reference=None,
        author_type=None,
        author_id=None,
        author_identifier_system="http://hospital.example.org/practitioners",
        author_identifier_value="PRAC-5555",
        created_by="u-test",
        created_at=D,
    )
    m = _observation(
        code_codings=[code_coding],
        subject_reference=None,
        subject_type=None,
        subject_id=None,
        subject_identifier_system="http://hospital.example.org/patients",
        subject_identifier_value="PAT-9999",
        subject_identifier_use=IdentifierUse.official,
        encounter_reference=None,
        encounter_type=None,
        encounter_id=None,
        encounter_identifier_system="http://hospital.example.org/encounters",
        encounter_identifier_value="ENC-8888",
        identifiers=[ident],
        performers=[performer],
        notes=[note],
    )
    out = to_fhir_observation(m)
    assert out["subject"]["identifier"]["value"] == "PAT-9999"
    assert out["encounter"]["identifier"]["value"] == "ENC-8888"
    assert out["identifier"][0]["assigner"]["identifier"]["value"] == "ORG-1111"
    assert out["performer"][0]["identifier"]["value"] == "PRAC-7777"
    assert out["note"][0]["authorReference"]["identifier"]["value"] == "PRAC-5555"
    assert_valid(observation_pb2.Observation, out)
