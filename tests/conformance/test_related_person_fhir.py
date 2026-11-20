"""FHIR R4 conformance for `to_fhir_related_person()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

RelatedPerson is stored Medplum-style (like Patient, Appointment, Encounter and the
other content-based resources): the resource lives whole in
RelatedPersonModel.content, and to_fhir_related_person() only stamps `id` and
`meta` onto it. So what can go wrong on the read side is that stamping (e.g. a
malformed meta extension) or a stored document the server returns that isn't
valid R4 — each case below is a `content` document as the write path would store
it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.related_person import to_fhir_related_person
from app.models.related_person import RelatedPersonModel

from .support import assert_valid, fhir_json_text

related_person_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.related_person_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)
PATIENT = {"reference": "Patient/10001"}
ROLE = "http://terminology.hl7.org/CodeSystem/v3-RoleCode"


def _related_person(content: dict, **overrides) -> RelatedPersonModel:
    fields = {
        "related_person_id": 300001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return RelatedPersonModel(**fields)


def _with(**elements) -> RelatedPersonModel:
    return _related_person({"patient": PATIENT, **elements})


CASES = {
    "minimal": _with(),
    "updated_by_and_updated_at": _related_person({"patient": PATIENT}, updated_by="u-other", updated_at=D),
    "identifier_with_type_and_assigner": _with(
        identifier=[
            {
                "use": "official",
                "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "PRN"}]},
                "system": "http://hospital.example.org/related-persons",
                "value": "RP-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    "active_true": _with(active=True),
    "active_false": _with(active=False),
    "patient_with_display": _with(patient={"reference": "Patient/10001", "display": "A. Patient"}),
    "patient_logical": _related_person({"patient": {"identifier": {"system": "urn:pts", "value": "P-9"}}}),
    "patient_absolute_url": _related_person({"patient": {"reference": "https://other.example.org/fhir/Patient/9"}}),
    "relationship": _with(
        relationship=[
            {"coding": [{"system": ROLE, "code": "MTH", "display": "mother"}], "text": "Mother"},
            {"text": "Emergency contact"},
        ]
    ),
    "name": _with(
        name=[
            {"use": "official", "family": "Windsor", "given": ["Mary", "Ann"], "prefix": ["Mrs"], "suffix": ["Jr"]},
            {"text": "Mary W."},
        ]
    ),
    "telecom": _with(
        telecom=[
            {"system": "phone", "value": "555-9988", "use": "mobile", "rank": 1, "period": {"start": "2020-01-01"}},
            {"system": "email", "value": "mary@example.org"},
        ]
    ),
    **{f"gender_{g}": _with(gender=g) for g in ("male", "female", "other", "unknown")},
    "birth_date_full": _with(birthDate="1965-04-12"),
    "birth_date_partial_month": _with(birthDate="1965-04"),
    "birth_date_partial_year": _with(birthDate="1965"),
    "address": _with(
        address=[
            {
                "use": "home",
                "type": "both",
                "text": "1 Main St, Boston",
                "line": ["1 Main St", "Apt 2"],
                "city": "Boston",
                "district": "Suffolk",
                "state": "MA",
                "postalCode": "02110",
                "country": "US",
                "period": {"start": "2020-01-01"},
            }
        ]
    ),
    "photo": _with(photo=[{"contentType": "image/png", "url": "https://example.org/mary.png", "title": "Mary"}]),
    "period": _with(period={"start": "2020-01-01", "end": "2026-01-01"}),
    "communication": _with(
        communication=[{"language": {"coding": [{"code": "en"}], "text": "English"}, "preferred": True}]
    ),
    "extension": _with(extension=[{"url": "https://fhir-server.dev/fhir/StructureDefinition/x", "valueString": "y"}]),
    "full": _with(
        identifier=[{"system": "urn:rp", "value": "RP-1"}],
        active=True,
        relationship=[{"coding": [{"system": ROLE, "code": "GUARD"}]}],
        name=[{"family": "Windsor", "given": ["Mary"]}],
        telecom=[{"system": "phone", "value": "555-9988"}],
        gender="female",
        birthDate="1965-04-12",
        address=[{"city": "Boston"}],
        period={"start": "2020-01-01"},
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_related_person_mapper_emits_valid_fhir_r4(case):
    assert_valid(related_person_pb2.RelatedPerson, to_fhir_related_person(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {"patient": PATIENT, "active": True, "gender": "female", "birthDate": "1965"}
    out = to_fhir_related_person(_related_person(content))
    assert out["resourceType"] == "RelatedPerson"
    assert out["id"] == "300001"
    assert {k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")} == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 — `patient` as a one-item list — and an unknown code
# for `gender`; the integration tests cover those.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"activee": True}),
        ("active as string", {"active": "yes"}),
        ("patient as string not a Reference", {"patient": "Patient/1"}),
        ("relationship as object not a list", {"relationship": {"text": "x"}}),
        ("name as object not a list", {"name": {"family": "x"}}),
        ("given as string not a list", {"name": [{"given": "Mary"}]}),
        ("telecom value as number", {"telecom": [{"value": 5}]}),
        ("birthDate not a date", {"birthDate": "tomorrow"}),
        ("gender as number", {"gender": 1}),
        ("address line as string not a list", {"address": [{"line": "1 Main St"}]}),
        ("period start not a dateTime", {"period": {"start": "tomorrow"}}),
        ("communication as object not a list", {"communication": {"preferred": True}}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "RelatedPerson", "id": "300001", "patient": PATIENT, **broken}
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), related_person_pb2.RelatedPerson, validate=True
        )
