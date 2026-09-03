"""FHIR R4 conformance for `to_fhir_patient()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.patient import to_fhir_patient
from app.models.patient import (
    PatientAddress,
    PatientCommunication,
    PatientContact,
    PatientContactRelationship,
    PatientContactTelecom,
    PatientGeneralPractitioner,
    PatientIdentifier,
    PatientLink,
    PatientModel,
    PatientName,
    PatientPhoto,
    PatientTelecom,
)
from app.models.patient.enums import PatientGender, PatientLinkType

from .support import assert_valid, fhir_json_text

patient_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.patient_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)

_CHILD_ATTRS = (
    "identifiers", "names", "telecoms", "addresses", "photos", "contacts",
    "communications", "general_practitioners", "links",
)


def _patient(**overrides) -> PatientModel:
    """A Patient carrying only the columns the model marks NOT NULL, plus
    empty sub-resource lists (nothing is lazy-loadable off a session here).
    active/gender/birth_date/deceased_boolean are all NOT NULL as of a recent
    fix, so every shape under test must carry them."""
    fields = {
        "patient_id": 10001,
        "org_id": "org-test",
        "active": True,
        "gender": PatientGender.female,
        "birth_date": dt.date(1990, 1, 1),
        "deceased_boolean": False,
        "created_by": "u-test",
        "created_at": D,
    }
    fields.update(overrides)
    pt = PatientModel(**fields)
    for attr in _CHILD_ATTRS:
        if getattr(pt, attr, None) is None:
            setattr(pt, attr, [])
    return pt


def _with(attr, *rows) -> PatientModel:
    pt = _patient()
    setattr(pt, attr, list(rows))
    return pt


def _identifier(**kw) -> PatientIdentifier:
    return PatientIdentifier(
        **{
            "id": 1, "org_id": "org-test", "system": "http://ex.org/ids",
            "value": "PT-1", "created_by": "u-test", "created_at": D, **kw,
        }
    )


def _name(**kw) -> PatientName:
    return PatientName(
        **{
            "id": 1, "org_id": "org-test", "family": "Chalmers",
            "created_by": "u-test", "created_at": D, **kw,
        }
    )


def _telecom(**kw) -> PatientTelecom:
    return PatientTelecom(
        **{
            "id": 1, "org_id": "org-test", "system": "phone", "value": "555-1234",
            "created_by": "u-test", "created_at": D, **kw,
        }
    )


def _address(**kw) -> PatientAddress:
    return PatientAddress(
        **{
            "id": 1, "org_id": "org-test", "type": "both", "city": "Amsterdam",
            "state": "NH", "postal_code": "1000 AA", "country": "NLD",
            "created_by": "u-test", "created_at": D, **kw,
        }
    )


def _photo(**kw) -> PatientPhoto:
    return PatientPhoto(
        **{
            "id": 1, "org_id": "org-test", "url": "https://example.org/photo.png",
            "created_by": "u-test", "created_at": D, **kw,
        }
    )


def _communication(**kw) -> PatientCommunication:
    return PatientCommunication(
        **{
            "id": 1, "org_id": "org-test",
            "language_system": "urn:ietf:bcp:47", "language_code": "en",
            "language_display": "English",
            "created_by": "u-test", "created_at": D, **kw,
        }
    )


def _contact(*, relationships=None, telecoms=None, **kw) -> PatientContact:
    """A PatientContact row with its two grandchild lists (relationships,
    telecoms) always set explicitly — nothing lazy-loads off a detached
    instance here."""
    c = PatientContact(
        **{
            "id": 1, "org_id": "org-test", "address_type": "both",
            "address_city": "Amsterdam", "address_state": "NH",
            "address_postal_code": "1000 AA", "address_country": "NLD",
            "created_by": "u-test", "created_at": D, **kw,
        }
    )
    c.relationships = list(relationships) if relationships else []
    c.telecoms = list(telecoms) if telecoms else []
    return c


def _general_practitioner(**kw) -> PatientGeneralPractitioner:
    return PatientGeneralPractitioner(
        **{
            "id": 1, "org_id": "org-test",
            "created_by": "u-test", "created_at": D, **kw,
        }
    )


def _link(**kw) -> PatientLink:
    return PatientLink(
        **{
            "id": 1, "org_id": "org-test", "type": PatientLinkType.seealso,
            "created_by": "u-test", "created_at": D, **kw,
        }
    )


# Each case is one distinct shape the mapper can emit. Anything with a
# conditional branch in app/fhir/mappers/patient/fhir.py should appear here.
CASES = {
    "minimal": _patient(),

    "active_false": _patient(active=False),
    "gender_male": _patient(gender=PatientGender.male),
    "gender_other": _patient(gender=PatientGender.other),
    "gender_unknown": _patient(gender=PatientGender.unknown),

    "deceased_boolean_true": _patient(deceased_boolean=True),
    "deceased_datetime": _patient(deceased_boolean=False, deceased_datetime=D),

    "marital_status_full_coding": _patient(
        marital_status_system="http://terminology.hl7.org/CodeSystem/v3-MaritalStatus",
        marital_status_version="2018-08-12",
        marital_status_code="M",
        marital_status_display="Married",
        marital_status_text="Married",
        marital_status_user_selected=True,
    ),

    "multiple_birth_boolean": _patient(multiple_birth_boolean=True),
    "multiple_birth_integer": _patient(multiple_birth_integer=2),

    "managing_organization_resolved": _patient(
        managing_organization_type="Organization",
        managing_organization_id=190001,
        managing_organization_display="Burgers UMC",
    ),
    "managing_organization_identifier_fallback": _patient(
        managing_organization_identifier_system="urn:org-registry",
        managing_organization_identifier_value="ORG-9",
        managing_organization_identifier_use="official",
    ),

    "identifier_with_type_and_period": _with(
        "identifiers",
        _identifier(
            use="official",
            type_system="http://terminology.hl7.org/CodeSystem/v2-0203",
            type_version="2.9",
            type_code="MR",
            type_display="Medical record number",
            type_text="Medical record number",
            type_user_selected=True,
            period_start=D,
            period_end=D,
        ),
    ),
    "identifier_assigner_resolved": _with(
        "identifiers",
        _identifier(
            assigner_type="Organization", assigner_id=190001, assigner_display="Acme"
        ),
    ),
    "identifier_assigner_fallback": _with(
        "identifiers",
        _identifier(
            assigner_identifier_system="urn:external-registry",
            assigner_identifier_value="EXTERNAL-1",
            assigner_identifier_use="official",
        ),
    ),

    "name_use_and_parts": _with(
        "names",
        _name(
            use="official", text="Peter James Chalmers", family="Chalmers",
            given="Peter,James", prefix="Mr.", suffix="Jr.",
            period_start=D, period_end=D,
        ),
    ),
    "name_multiple": _with(
        "names",
        _name(id=1, use="official", family="Chalmers"),
        _name(id=2, use="nickname", given="Jim"),
    ),

    "telecoms_with_rank_and_period": _with(
        "telecoms",
        _telecom(
            id=1, system="phone", value="555-1234", use="work", rank=1,
            period_start=D, period_end=D,
        ),
        _telecom(id=2, system="email", value="a@b.example"),
    ),

    "address_full": _with(
        "addresses",
        _address(
            use="home", type="both", text="534 Erewhon St",
            line="534 Erewhon St", district="Rainbow", period_start=D, period_end=D,
        ),
    ),

    "photo_full": _with(
        "photos",
        _photo(
            content_type="image/png", language="en", data="YWJjMTIz",
            url="https://example.org/photo.png", size=1024, hash="ZGVhZGJlZWY=",
            title="Patient photo", creation=D,
        ),
    ),

    "communication_with_preferred": _with(
        "communications",
        _communication(
            language_system="urn:ietf:bcp:47", language_version="R1",
            language_code="nl", language_display="Dutch", language_text="Dutch",
            language_user_selected=True, preferred=True,
        ),
    ),
    "communication_multiple": _with(
        "communications",
        _communication(id=1, language_code="en", language_display="English"),
        _communication(id=2, language_code="nl", language_display="Dutch"),
    ),

    "general_practitioner_organization": _with(
        "general_practitioners",
        _general_practitioner(
            reference_type="Organization", reference_id=190001, reference_display="Acme Clinic"
        ),
    ),
    "general_practitioner_practitioner": _with(
        "general_practitioners",
        _general_practitioner(
            reference_type="Practitioner", reference_id=30001, reference_display="Dr. Smith"
        ),
    ),
    "general_practitioner_practitioner_role": _with(
        "general_practitioners",
        _general_practitioner(
            reference_type="PractitionerRole", reference_id=140001, reference_display="Dr. Smith's role"
        ),
    ),
    "general_practitioner_identifier_fallback": _with(
        "general_practitioners",
        _general_practitioner(
            reference_identifier_system="urn:external-registry",
            reference_identifier_value="EXTERNAL-GP-1",
        ),
    ),
    "general_practitioner_multiple": _with(
        "general_practitioners",
        _general_practitioner(id=1, reference_type="Practitioner", reference_id=30001),
        _general_practitioner(id=2, reference_type="Organization", reference_id=190001),
    ),

    "link_replaces": _with(
        "links",
        _link(
            other_type="Patient", other_id=10002, other_display="Duplicate record",
            type=PatientLinkType.replaces,
        ),
    ),
    "link_replaced_by": _with(
        "links", _link(other_type="Patient", other_id=10003, type=PatientLinkType.replaced_by)
    ),
    "link_refer": _with(
        "links",
        _link(other_type="RelatedPerson", other_id=1, type=PatientLinkType.refer),
    ),
    "link_seealso_identifier_fallback": _with(
        "links",
        _link(
            other_identifier_system="urn:external-registry",
            other_identifier_value="EXTERNAL-PT-1",
            type=PatientLinkType.seealso,
        ),
    ),

    "contact_relationship_and_name": _with(
        "contacts",
        _contact(
            name_use="official", name_text="Bea Chalmers", name_family="Chalmers",
            name_given="Bea", gender="female", period_start=D, period_end=D,
            relationships=[
                PatientContactRelationship(
                    id=1, org_id="org-test",
                    coding_system="http://terminology.hl7.org/CodeSystem/v2-0131",
                    coding_code="C", coding_display="Emergency Contact",
                    text="Emergency Contact", created_by="u-test", created_at=D,
                ),
            ],
        ),
    ),
    "contact_telecom_and_organization": _with(
        "contacts",
        _contact(
            organization_type="Organization", organization_id=190001,
            organization_display="Acme Clinic",
            telecoms=[
                PatientContactTelecom(
                    id=1, org_id="org-test", system="phone", value="555-9999",
                    use="mobile", rank=1, created_by="u-test", created_at=D,
                ),
            ],
        ),
    ),
    "contact_organization_identifier_fallback": _with(
        "contacts",
        _contact(
            organization_identifier_system="urn:org-registry",
            organization_identifier_value="ORG-9",
        ),
    ),
    "contact_minimal": _with("contacts", _contact()),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_patient_mapper_emits_valid_fhir_r4(case):
    assert_valid(patient_pb2.Patient, to_fhir_patient(CASES[case]))


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.

@pytest.mark.parametrize(
    "label,broken",
    [
        ("bad gender code", {"gender": "bogus"}),
        ("misspelled element", {"activ3": True}),
        ("birthDate not a date", {"birthDate": "not-a-date"}),
        ("deceasedBoolean as string not boolean", {"deceasedBoolean": "yes"}),
        ("maritalStatus as string not CodeableConcept", {"maritalStatus": "married"}),
        ("identifier as string not object", {"identifier": ["PT-1"]}),
        ("link missing required other", {"link": [{"type": "seealso"}]}),
        ("link bad type code", {"link": [{"other": {"reference": "Patient/10002"}, "type": "bogus"}]}),
        ("generalPractitioner as string not Reference", {"generalPractitioner": ["Practitioner/30001"]}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {
        "resourceType": "Patient", "id": "10001", "active": True,
        "gender": "female", "birthDate": "1990-01-01", "deceasedBoolean": False,
        **broken,
    }
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), patient_pb2.Patient, validate=True
        )
