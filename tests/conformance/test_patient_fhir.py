"""FHIR R4 conformance for `to_fhir_patient()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

Patient is stored Medplum-style (like Practitioner and the other content-based
resources): the resource lives whole in PatientModel.content, and
to_fhir_patient() only stamps `id` and `meta` onto it. So what can go wrong on
the read side is that stamping (e.g. a malformed meta extension) or a stored
document the server returns that isn't valid R4 — each case below is a
`content` document as the write path would store it, run through the real read
mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.patient import to_fhir_patient
from app.models.patient import PatientModel
from tests.integration.patient.support import FULL, MINIMAL

from .support import assert_valid, fhir_json_text

patient_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.patient_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)


def _stored(document: dict) -> dict:
    """What the write path stores: everything but resourceType/id/meta."""
    return {k: v for k, v in document.items() if k not in ("resourceType", "id", "meta")}


def _patient(content: dict, **overrides) -> PatientModel:
    fields = {"patient_id": 10001, "tenant_id": "org-test", "created_by": "u-test", "created_at": D, "content": content}
    fields.update(overrides)
    return PatientModel(**fields)


CASES = {
    "empty": _patient({}),
    "minimal": _patient(_stored(MINIMAL)),
    "active_false": _patient({"active": False}),
    "updated_by_and_updated_at": _patient({"active": True}, updated_by="u-other", updated_at=D),
    **{f"gender_{g}": _patient({"gender": g}) for g in ("male", "female", "other", "unknown")},
    "birth_date_full": _patient({"birthDate": "1974-12-25"}),
    "birth_date_year_month": _patient({"birthDate": "1990-05"}),
    "birth_date_year": _patient({"birthDate": "1990"}),
    "deceased_boolean_true": _patient({"deceasedBoolean": True}),
    "deceased_boolean_false": _patient({"deceasedBoolean": False}),
    "deceased_date_time": _patient({"deceasedDateTime": "2020-03-01T10:00:00Z"}),
    "multiple_birth_boolean": _patient({"multipleBirthBoolean": True}),
    "multiple_birth_integer": _patient({"multipleBirthInteger": 2}),
    "identifier_with_type_and_assigner": _patient(
        {
            "identifier": [
                {
                    "use": "official",
                    "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR"}]},
                    "system": "http://hospital.example.org/mrn",
                    "value": "MRN-1",
                    "period": {"start": "2020-01-01"},
                    "assigner": {"reference": "Organization/190001"},
                }
            ]
        }
    ),
    "names": _patient(
        {
            "name": [
                {"use": "official", "family": "Chalmers", "given": ["Peter", "James"], "prefix": ["Mr"], "suffix": ["Jr"]},
                {"use": "maiden", "text": "Peter C", "period": {"start": "1990-01-01", "end": "2000-01-01"}},
            ]
        }
    ),
    "telecoms": _patient(
        {
            "telecom": [
                {"system": "phone", "value": "555-1234", "use": "home", "rank": 1},
                {"system": "email", "value": "peter@example.org"},
            ]
        }
    ),
    "address": _patient(
        {
            "address": [
                {
                    "use": "home",
                    "type": "both",
                    "line": ["534 Erewhon St", "Unit 2"],
                    "city": "PleasantVille",
                    "district": "Rainbow",
                    "state": "Vic",
                    "postalCode": "3999",
                    "country": "AU",
                }
            ]
        }
    ),
    "marital_status": _patient({"maritalStatus": {"coding": [{"code": "M", "display": "Married"}], "text": "Married"}}),
    "photo": _patient({"photo": [{"url": "https://fhir-server.dev/fhir/assets/patient.png"}]}),
    "contact_with_every_part": _patient(
        {
            "contact": [
                {
                    "relationship": [{"coding": [{"code": "N", "display": "Next-of-Kin"}]}],
                    "name": {"family": "Chalmers", "given": ["Sarah"]},
                    "telecom": [{"system": "phone", "value": "555-9876", "use": "mobile"}],
                    "address": {"city": "Springfield", "line": ["1 Main St"]},
                    "gender": "female",
                    "organization": {"reference": "Organization/190001"},
                    "period": {"start": "2020-01-01"},
                }
            ]
        }
    ),
    "contact_with_only_an_organization": _patient({"contact": [{"organization": {"display": "Employer"}}]}),
    "communication": _patient(
        {
            "communication": [
                {"language": {"coding": [{"code": "en", "display": "English"}]}, "preferred": True},
                {"language": {"text": "Francais"}},
            ]
        }
    ),
    "general_practitioners_of_every_type": _patient(
        {
            "generalPractitioner": [
                {"reference": "Practitioner/30001", "display": "Dr Careful"},
                {"reference": "PractitionerRole/140001"},
                {"reference": "Organization/190001"},
            ]
        }
    ),
    "logical_and_absolute_general_practitioners": _patient(
        {
            "generalPractitioner": [
                {"reference": "https://other.example.org/fhir/Practitioner/9"},
                {"identifier": {"system": "urn:gps", "value": "GP-7"}, "display": "External GP"},
            ]
        }
    ),
    "managing_organization": _patient({"managingOrganization": {"reference": "Organization/190001", "display": "Hospital"}}),
    "links": _patient(
        {
            "link": [
                {"other": {"reference": "Patient/10002"}, "type": "replaced-by"},
                {"other": {"reference": "RelatedPerson/5"}, "type": "seealso"},
                {"other": {"reference": "Patient/10003"}, "type": "replaces"},
                {"other": {"reference": "Patient/10004"}, "type": "refer"},
            ]
        }
    ),
    "extension": _patient({"extension": [{"url": "https://fhir-server.dev/fhir/StructureDefinition/x", "valueString": "y"}]}),
    "full_payload": _patient(_stored(FULL)),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_patient_mapper_emits_valid_fhir_r4(case):
    assert_valid(patient_pb2.Patient, to_fhir_patient(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = _stored(FULL)
    out = to_fhir_patient(_patient(content))
    assert out["resourceType"] == "Patient"
    assert out["id"] == "10001"
    assert {k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")} == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1, and an unknown `gender` code here.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("active as string not boolean", {"active": "yes"}),
        ("misspelled element", {"birthDat": "1974-12-25"}),
        ("birthDate not a date", {"birthDate": "last tuesday"}),
        ("deceasedBoolean as string", {"deceasedBoolean": "no"}),
        ("deceasedDateTime not a dateTime", {"deceasedDateTime": "tomorrow"}),
        ("name as strings not HumanNames", {"name": ["Peter Chalmers"]}),
        ("telecom value as number", {"telecom": [{"system": "phone", "value": 5551234}]}),
        ("maritalStatus as string not CodeableConcept", {"maritalStatus": "M"}),
        ("multipleBirthInteger as string", {"multipleBirthInteger": "two"}),
        ("generalPractitioner as strings not References", {"generalPractitioner": ["Practitioner/30001"]}),
        ("managingOrganization as string not Reference", {"managingOrganization": "Organization/190001"}),
        ("communication as strings not backbone elements", {"communication": ["en"]}),
        ("link type not a link type", {"link": [{"other": {"reference": "Patient/1"}, "type": "friend"}]}),
        ("contact as an object not a list", {"contact": {"gender": "female"}}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "Patient", "id": "10001", **broken}
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(fhir_json_text(payload), patient_pb2.Patient, validate=True)
