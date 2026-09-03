"""FHIR R4 conformance for `to_fhir_practitioner()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.
"""

import datetime as dt

import pytest

from app.fhir.mappers.practitioner import to_fhir_practitioner
from app.models.practitioner import (
    PractitionerAddress,
    PractitionerCommunication,
    PractitionerIdentifier,
    PractitionerModel,
    PractitionerName,
    PractitionerPhoto,
    PractitionerQualification,
    PractitionerQualificationIdentifier,
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
    "names", "identifiers", "telecoms", "addresses", "photos",
    "qualifications", "communications",
)


def _practitioner(**overrides) -> PractitionerModel:
    """A Practitioner carrying only the columns the model marks NOT NULL,
    plus empty sub-resource lists (nothing is lazy-loadable off a session
    here). active/gender/birth_date are all NOT NULL, so every shape under
    test must carry them."""
    fields = {
        "practitioner_id": 30001,
        "org_id": "org-test",
        "active": True,
        "gender": AdministrativeGender.female,
        "birth_date": dt.date(1975, 6, 15),
        "created_by": "u-test",
        "created_at": D,
    }
    fields.update(overrides)
    pr = PractitionerModel(**fields)
    for attr in _CHILD_ATTRS:
        if getattr(pr, attr, None) is None:
            setattr(pr, attr, [])
    return pr


def _with(attr, *rows) -> PractitionerModel:
    pr = _practitioner()
    setattr(pr, attr, list(rows))
    return pr


def _identifier(**kw) -> PractitionerIdentifier:
    return PractitionerIdentifier(
        **{
            "id": 1, "org_id": "org-test", "system": "http://ex.org/ids",
            "value": "PR-1", "created_by": "u-test", "created_at": D, **kw,
        }
    )


def _name(**kw) -> PractitionerName:
    return PractitionerName(
        **{
            "id": 1, "org_id": "org-test", "family": "Careful",
            "created_by": "u-test", "created_at": D, **kw,
        }
    )


def _telecom(**kw) -> PractitionerTelecom:
    return PractitionerTelecom(
        **{
            "id": 1, "org_id": "org-test", "system": "phone", "value": "555-1234",
            "created_by": "u-test", "created_at": D, **kw,
        }
    )


def _address(**kw) -> PractitionerAddress:
    return PractitionerAddress(
        **{
            "id": 1, "org_id": "org-test", "type": "both", "city": "Amsterdam",
            "state": "NH", "postal_code": "1000 AA", "country": "NLD",
            "created_by": "u-test", "created_at": D, **kw,
        }
    )


def _photo(**kw) -> PractitionerPhoto:
    return PractitionerPhoto(
        **{
            "id": 1, "org_id": "org-test", "url": "https://example.org/photo.png",
            "created_by": "u-test", "created_at": D, **kw,
        }
    )


def _communication(**kw) -> PractitionerCommunication:
    return PractitionerCommunication(
        **{
            "id": 1, "org_id": "org-test",
            "language_system": "urn:ietf:bcp:47", "language_code": "en",
            "language_display": "English",
            "created_by": "u-test", "created_at": D, **kw,
        }
    )


def _qualification_identifier(**kw) -> PractitionerQualificationIdentifier:
    return PractitionerQualificationIdentifier(
        **{
            "id": 1, "org_id": "org-test", "system": "http://ex.org/licenses",
            "value": "LIC-1", "created_by": "u-test", "created_at": D, **kw,
        }
    )


def _qualification(*, identifiers=None, **kw) -> PractitionerQualification:
    """A PractitionerQualification row with its `identifiers` grandchild
    list always set explicitly — nothing lazy-loads off a detached
    instance here."""
    q = PractitionerQualification(
        **{
            "id": 1, "org_id": "org-test",
            "code_system": "http://terminology.hl7.org/CodeSystem/v2-0360",
            "code_code": "MD", "code_display": "Doctor of Medicine",
            "created_by": "u-test", "created_at": D, **kw,
        }
    )
    q.identifiers = list(identifiers) if identifiers else []
    return q


# Each case is one distinct shape the mapper can emit. Anything with a
# conditional branch in app/fhir/mappers/practitioner/fhir.py should appear here.
CASES = {
    "minimal": _practitioner(),

    "active_false": _practitioner(active=False),
    "gender_male": _practitioner(gender=AdministrativeGender.male),
    "gender_other": _practitioner(gender=AdministrativeGender.other),
    "gender_unknown": _practitioner(gender=AdministrativeGender.unknown),

    "identifier_with_type_and_period": _with(
        "identifiers",
        _identifier(
            use="official",
            type_system="http://terminology.hl7.org/CodeSystem/v2-0203",
            type_version="2.9",
            type_code="NPI",
            type_display="National provider identifier",
            type_text="National provider identifier",
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
            use="official", text="Adam Careful", family="Careful",
            given="Adam", prefix="Dr.", suffix="MD",
            period_start=D, period_end=D,
        ),
    ),
    "name_multiple": _with(
        "names",
        _name(id=1, use="official", family="Careful"),
        _name(id=2, use="nickname", given="Ad"),
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
            use="work", type="both", text="534 Erewhon St",
            line="534 Erewhon St", district="Rainbow", period_start=D, period_end=D,
        ),
    ),

    "photo_full": _with(
        "photos",
        _photo(
            content_type="image/png", language="en", data="YWJjMTIz",
            url="https://example.org/photo.png", size=1024, hash="ZGVhZGJlZWY=",
            title="Practitioner photo", creation=D,
        ),
    ),

    "communication_with_text": _with(
        "communications",
        _communication(
            language_system="urn:ietf:bcp:47", language_version="R1",
            language_code="nl", language_display="Dutch", language_text="Dutch",
            language_user_selected=True,
        ),
    ),
    "communication_multiple": _with(
        "communications",
        _communication(id=1, language_code="en", language_display="English"),
        _communication(id=2, language_code="nl", language_display="Dutch"),
    ),

    "qualification_code_with_text": _with(
        "qualifications",
        _qualification(
            code_system="http://terminology.hl7.org/CodeSystem/v2-0360",
            code_code="MD", code_display="Doctor of Medicine",
            code_text="Doctor of Medicine",
        ),
    ),
    "qualification_period": _with(
        "qualifications", _qualification(period_start=D, period_end=D)
    ),
    "qualification_issuer_resolved": _with(
        "qualifications",
        _qualification(
            issuer_type="Organization", issuer_id=190001,
            issuer_display="Board of Medicine",
        ),
    ),
    "qualification_issuer_identifier_fallback": _with(
        "qualifications",
        _qualification(
            issuer_identifier_system="urn:org-registry",
            issuer_identifier_value="ORG-9",
            issuer_identifier_use="official",
        ),
    ),
    "qualification_identifier_with_type_and_period": _with(
        "qualifications",
        _qualification(
            identifiers=[
                _qualification_identifier(
                    use="official",
                    type_system="http://terminology.hl7.org/CodeSystem/v2-0203",
                    type_code="PRN",
                    type_display="Provider number",
                    type_text="Provider number",
                    period_start=D,
                    period_end=D,
                ),
            ],
        ),
    ),
    "qualification_identifier_assigner_resolved": _with(
        "qualifications",
        _qualification(
            identifiers=[
                _qualification_identifier(
                    assigner_type="Organization", assigner_id=190001,
                    assigner_display="Acme",
                ),
            ],
        ),
    ),
    "qualification_identifier_assigner_fallback": _with(
        "qualifications",
        _qualification(
            identifiers=[
                _qualification_identifier(
                    assigner_identifier_system="urn:external-registry",
                    assigner_identifier_value="EXTERNAL-1",
                ),
            ],
        ),
    ),
    "qualification_multiple": _with(
        "qualifications",
        _qualification(id=1, code_code="MD", code_display="Doctor of Medicine"),
        _qualification(id=2, code_code="RN", code_display="Registered Nurse"),
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_practitioner_mapper_emits_valid_fhir_r4(case):
    assert_valid(practitioner_pb2.Practitioner, to_fhir_practitioner(CASES[case]))


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
        ("active as string not boolean", {"active": "yes"}),
        ("identifier as string not object", {"identifier": ["PR-1"]}),
        ("qualification.code as string not CodeableConcept", {"qualification": [{"code": "MD"}]}),
        ("name as strings not HumanNames", {"name": ["Adam Careful"]}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {
        "resourceType": "Practitioner", "id": "30001", "active": True,
        "gender": "female", "birthDate": "1975-06-15",
        **broken,
    }
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), practitioner_pb2.Practitioner, validate=True
        )
