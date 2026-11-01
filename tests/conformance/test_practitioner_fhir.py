"""FHIR R4 conformance for `to_fhir_practitioner()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.practitioner import to_fhir_practitioner
from app.models.practitioner import (
    PractitionerAddress,
    PractitionerCommunication,
    PractitionerCommunicationCoding,
    PractitionerIdentifier,
    PractitionerIdentifierTypeCoding,
    PractitionerModel,
    PractitionerName,
    PractitionerPhoto,
    PractitionerQualification,
    PractitionerQualificationCodeCoding,
    PractitionerQualificationIdentifier,
    PractitionerQualificationIdentifierTypeCoding,
    PractitionerTelecom,
)
from app.schemas.enums import AdministrativeGender

from .support import assert_valid, fhir_json_text

practitioner_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.practitioner_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers",
    "names",
    "telecoms",
    "addresses",
    "photos",
    "qualifications",
    "communications",
)


def _practitioner(**overrides) -> PractitionerModel:
    """A Practitioner carrying only the columns the model marks NOT NULL,
    plus empty sub-resource lists."""
    fields = {
        "practitioner_id": 30001,
        "tenant_id": "org-test",
        "user_id": "u-doc-1",
        "created_by": "u-test",
        "created_at": D,
        "extension": [],
    }
    fields.update(overrides)
    p = PractitionerModel(**fields)
    for attr in _CHILD_ATTRS:
        if getattr(p, attr, None) is None:
            setattr(p, attr, [])
    return p


def _with(attr, *rows) -> PractitionerModel:
    p = _practitioner()
    setattr(p, attr, list(rows))
    return p


CASES = {
    "minimal": _practitioner(),
    "active_true": _practitioner(active=True),
    "active_false": _practitioner(active=False),
    "gender_male": _practitioner(gender=AdministrativeGender.male),
    "gender_female": _practitioner(gender=AdministrativeGender.female),
    "birth_date": _practitioner(birth_date=dt.date(1980, 5, 12)),
    "identifier_simple": _with(
        "identifiers",
        PractitionerIdentifier(
            id=1,
            tenant_id="org-test",
            system="http://hl7.org/fhir/sid/us-npi",
            value="9941339108",
            created_by="u-test",
            created_at=D,
            type_codings=[],
        ),
    ),
    "identifier_with_type_coding": _with(
        "identifiers",
        PractitionerIdentifier(
            id=1,
            tenant_id="org-test",
            system="http://hl7.org/fhir/sid/us-npi",
            value="9941339108",
            type_text="National Provider Identifier",
            created_by="u-test",
            created_at=D,
            type_codings=[
                PractitionerIdentifierTypeCoding(
                    id=1,
                    system="http://terminology.hl7.org/CodeSystem/v2-0203",
                    code="PRN",
                    display="Provider number",
                    created_by="u-test",
                    created_at=D,
                )
            ],
        ),
    ),
    "identifier_with_assigner_resolved": _with(
        "identifiers",
        PractitionerIdentifier(
            id=1,
            tenant_id="org-test",
            system="http://example.org/staff",
            value="DOC-42",
            assigner_type="Organization",
            assigner_id=190001,
            assigner_display="Acme Hospital",
            created_by="u-test",
            created_at=D,
            type_codings=[],
        ),
    ),
    "identifier_with_assigner_fallback_15col": _with(
        "identifiers",
        PractitionerIdentifier(
            id=1,
            tenant_id="org-test",
            system="http://example.org/staff",
            value="DOC-42",
            assigner_display="State Medical Board",
            assigner_identifier_use="official",
            assigner_identifier_type_system="http://terminology.hl7.org/CodeSystem/v2-0203",
            assigner_identifier_type_version="2.9",
            assigner_identifier_type_code="XX",
            assigner_identifier_type_display="Organization identifier",
            assigner_identifier_type_user_selected=True,
            assigner_identifier_type_text="State Org ID",
            assigner_identifier_system="http://state.example.gov/orgs",
            assigner_identifier_value="SMB-99",
            assigner_identifier_period_start=D,
            assigner_identifier_period_end=D,
            created_by="u-test",
            created_at=D,
            type_codings=[],
        ),
    ),
    "name_full": _with(
        "names",
        PractitionerName(
            id=1,
            tenant_id="org-test",
            use="official",
            family="Smith",
            given=["John", "Adam"],
            prefix=["Dr."],
            suffix=["MD"],
            text="Dr. John Adam Smith, MD",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "telecom_phone_email": _with(
        "telecoms",
        PractitionerTelecom(
            id=1,
            tenant_id="org-test",
            system="phone",
            value="555-123-4567",
            use="work",
            rank=1,
            created_by="u-test",
            created_at=D,
        ),
        PractitionerTelecom(
            id=2,
            tenant_id="org-test",
            system="email",
            value="dr.smith@example.com",
            use="work",
            rank=2,
            created_by="u-test",
            created_at=D,
        ),
    ),
    "address_work": _with(
        "addresses",
        PractitionerAddress(
            id=1,
            tenant_id="org-test",
            use="work",
            line=["100 Medical Center Blvd", "Suite 400"],
            city="Metropolis",
            state="NY",
            postal_code="10001",
            country="USA",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "photo_attachment": _with(
        "photos",
        PractitionerPhoto(
            id=1,
            tenant_id="org-test",
            content_type="image/jpeg",
            url="http://example.org/photos/drsmith.jpg",
            title="Profile Photo",
            created_by="u-test",
            created_at=D,
        ),
    ),
    "communication_language": _with(
        "communications",
        PractitionerCommunication(
            id=1,
            tenant_id="org-test",
            text="English",
            created_by="u-test",
            created_at=D,
            codings=[
                PractitionerCommunicationCoding(
                    id=1,
                    system="urn:ietf:bcp:47",
                    code="en",
                    display="English",
                    created_by="u-test",
                    created_at=D,
                )
            ],
        ),
    ),
    "qualification_full_with_fallback": _with(
        "qualifications",
        PractitionerQualification(
            id=1,
            tenant_id="org-test",
            code_text="Board Certified in Cardiology",
            period_start=D,
            issuer_display="American Board of Internal Medicine",
            issuer_identifier_use="official",
            issuer_identifier_type_system="http://terminology.hl7.org/CodeSystem/v2-0203",
            issuer_identifier_type_version="2.9",
            issuer_identifier_type_code="XX",
            issuer_identifier_type_display="Organization identifier",
            issuer_identifier_type_user_selected=True,
            issuer_identifier_type_text="Board Org ID",
            issuer_identifier_system="http://abim.example.org",
            issuer_identifier_value="ABIM-12345",
            issuer_identifier_period_start=D,
            issuer_identifier_period_end=D,
            created_by="u-test",
            created_at=D,
            code_codings=[
                PractitionerQualificationCodeCoding(
                    id=1,
                    system="http://terminology.hl7.org/CodeSystem/v2-0360|2.7",
                    code="MD",
                    display="Doctor of Medicine",
                    created_by="u-test",
                    created_at=D,
                )
            ],
            identifiers=[
                PractitionerQualificationIdentifier(
                    id=1,
                    tenant_id="org-test",
                    system="http://example.org/cert-numbers",
                    value="CERT-9876",
                    assigner_display="State Licensing Bureau",
                    assigner_identifier_system="http://licensing.state.gov",
                    assigner_identifier_value="SLB-44",
                    created_by="u-test",
                    created_at=D,
                    type_codings=[],
                )
            ],
        ),
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_practitioner_mapper_emits_valid_fhir_r4(case):
    assert_valid(practitioner_pb2.Practitioner, to_fhir_practitioner(CASES[case]))


def test_practitioner_reference_fallback_identifiers():
    """Verify that logical fallback identifier fields are mapped accurately into FHIR camelCase."""
    p = CASES["qualification_full_with_fallback"]
    data = to_fhir_practitioner(p)

    # Check qualification issuer fallback
    q = data["qualification"][0]
    issuer = q["issuer"]
    assert issuer["display"] == "American Board of Internal Medicine"
    assert "reference" not in issuer
    ident = issuer["identifier"]
    assert ident["use"] == "official"
    assert ident["system"] == "http://abim.example.org"
    assert ident["value"] == "ABIM-12345"
    assert ident["period"] == {"start": "2026-01-01T00:00:00+00:00", "end": "2026-01-01T00:00:00+00:00"}
    assert ident["type"]["text"] == "Board Org ID"
    assert ident["type"]["coding"][0] == {
        "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
        "version": "2.9",
        "code": "XX",
        "display": "Organization identifier",
        "userSelected": True,
    }

    # Check qualification identifier assigner fallback
    q_ident = q["identifier"][0]
    assigner = q_ident["assigner"]
    assert assigner["display"] == "State Licensing Bureau"
    assert assigner["identifier"]["system"] == "http://licensing.state.gov"
    assert assigner["identifier"]["value"] == "SLB-44"


@pytest.mark.parametrize(
    "label,broken",
    [
        ("bad gender code", {"gender": "unknown_gender"}),
        ("birthDate not a date", {"birthDate": "invalid-date"}),
        ("telecom not a list", {"telecom": {"system": "phone"}}),
        ("active not a bool", {"active": "yes"}),
        ("bad qualification structure", {"qualification": [{"code": 123}]}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {
        "resourceType": "Practitioner",
        "id": "30001",
        **broken,
    }
    with pytest.raises(Exception):  # noqa: B017
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), practitioner_pb2.Practitioner, validate=True
        )
