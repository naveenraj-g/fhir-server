"""FHIR R4 conformance for `to_fhir_practitioner()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

Practitioner is stored Medplum-style (like Organization): the resource lives
whole in PractitionerModel.content, and to_fhir_practitioner() only stamps
`id` and `meta` onto it. So what can go wrong on the read side is that
stamping (e.g. a malformed meta extension) or a stored document the server
returns that isn't valid R4 — each case below is a `content` document as the
write path would store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.practitioner import to_fhir_practitioner
from app.models.practitioner import PractitionerModel
from tests.integration.practitioner.support import FULL

from .support import assert_valid, fhir_json_text

practitioner_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.practitioner_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)


def _stored(document: dict) -> dict:
    """What the write path stores: everything but resourceType/id/meta."""
    return {
        k: v for k, v in document.items() if k not in ("resourceType", "id", "meta")
    }


def _practitioner(content: dict, **overrides) -> PractitionerModel:
    fields = {
        "practitioner_id": 30001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return PractitionerModel(**fields)


CASES = {
    "minimal": _practitioner({"name": [{"family": "Careful"}]}),
    "active_false": _practitioner({"active": False, "name": [{"family": "Careful"}]}),
    "gender_and_birthdate": _practitioner(
        {"gender": "female", "birthDate": "1980-05-15"}
    ),
    "partial_birthdate": _practitioner({"birthDate": "1980-05"}),
    "updated_by_and_updated_at": _practitioner(
        {"name": [{"family": "Careful"}]}, updated_by="u-other", updated_at=D
    ),
    "linked_user_is_not_in_the_resource": _practitioner(
        {"name": [{"family": "Careful"}]}, user_id="end-user-1"
    ),
    "extension": _practitioner(
        {
            "extension": [
                {
                    "url": "https://fhir-server.dev/fhir/StructureDefinition/x",
                    "valueString": "y",
                }
            ]
        }
    ),
    "several_names": _practitioner(
        {
            "name": [
                {
                    "use": "official",
                    "family": "Careful",
                    "given": ["Adam", "Quincy"],
                    "prefix": ["Dr"],
                    "suffix": ["Jr"],
                },
                {
                    "use": "maiden",
                    "text": "A. Hasty",
                    "period": {"start": "2000-01-01T00:00:00Z"},
                },
            ]
        }
    ),
    "identifier_with_type_and_assigner": _practitioner(
        {
            "identifier": [
                {
                    "use": "official",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "NPI",
                            }
                        ]
                    },
                    "system": "http://hl7.org/fhir/sid/us-npi",
                    "value": "9941339108",
                    "assigner": {
                        "reference": "Organization/190001",
                        "display": "NPI Registry",
                    },
                }
            ]
        }
    ),
    "telecom_address_photo": _practitioner(
        {
            "telecom": [
                {"system": "phone", "value": "555-9988", "use": "work", "rank": 1}
            ],
            "address": [
                {
                    "use": "work",
                    "line": ["534 Erewhon St"],
                    "city": "PleasantVille",
                    "postalCode": "3999",
                }
            ],
            "photo": [{"url": "https://fhir-server.dev/fhir/assets/photo.png"}],
        }
    ),
    "qualification_full": _practitioner(
        {
            "qualification": [
                {
                    "identifier": [{"system": "urn:license", "value": "L-1"}],
                    "code": {
                        "coding": [{"code": "BS", "display": "Bachelor of Science"}],
                        "text": "BS",
                    },
                    "period": {
                        "start": "2001-01-01T00:00:00Z",
                        "end": "2005-01-01T00:00:00Z",
                    },
                    "issuer": {
                        "reference": "Organization/190001",
                        "display": "State Board",
                    },
                }
            ]
        }
    ),
    "communication": _practitioner(
        {
            "communication": [
                {"coding": [{"code": "en", "display": "English"}], "text": "English"}
            ]
        }
    ),
    "full_payload": _practitioner(_stored(FULL)),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_practitioner_mapper_emits_valid_fhir_r4(case):
    assert_valid(practitioner_pb2.Practitioner, to_fhir_practitioner(CASES[case]))


def test_user_link_never_leaks_into_the_resource():
    out = to_fhir_practitioner(
        _practitioner({"name": [{"family": "Careful"}]}, user_id="end-user-1")
    )
    assert "end-user-1" not in str(out)


def test_mapper_serves_content_unchanged():
    content = _stored(FULL)
    out = to_fhir_practitioner(_practitioner(content))
    assert out["resourceType"] == "Practitioner"
    assert out["id"] == "30001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.


@pytest.mark.parametrize(
    "label,broken",
    [
        ("active as string not boolean", {"active": "yes"}),
        ("misspelled element", {"nam3": [{"family": "Careful"}]}),
        ("name as string not HumanName", {"name": ["Careful"]}),
        ("gender not in the required binding", {"gender": "robot"}),
        ("birthDate not a date", {"birthDate": "not-a-date"}),
        ("telecom as string not ContactPoint", {"telecom": ["555-9988"]}),
        (
            "qualification without its required code",
            {"qualification": [{"issuer": {"reference": "Organization/1"}}]},
        ),
        ("communication as strings not CodeableConcepts", {"communication": ["en"]}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "Practitioner", "id": "30001", "active": True, **broken}
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), practitioner_pb2.Practitioner, validate=True
        )
