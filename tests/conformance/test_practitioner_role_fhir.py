"""FHIR R4 conformance for `to_fhir_practitioner_role()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

PractitionerRole is stored Medplum-style (like Organization/Practitioner/
HealthcareService/Endpoint): the resource lives whole in
PractitionerRoleModel.content, and to_fhir_practitioner_role() only stamps `id`
and `meta` onto it. So what can go wrong on the read side is that stamping
(e.g. a malformed meta extension) or a stored document the server returns that
isn't valid R4 — each case below is a `content` document as the write path
would store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.practitioner_role import to_fhir_practitioner_role
from app.models.practitioner_role import PractitionerRoleModel
from tests.integration.practitioner_role.support import FULL

from .support import assert_valid, fhir_json_text

practitioner_role_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.practitioner_role_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)


def _stored(document: dict) -> dict:
    """What the write path stores: everything but resourceType/id/meta."""
    return {
        k: v for k, v in document.items() if k not in ("resourceType", "id", "meta")
    }


def _role(content: dict, **overrides) -> PractitionerRoleModel:
    fields = {
        "practitioner_role_id": 140001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return PractitionerRoleModel(**fields)


CASES = {
    "minimal": _role({"active": True}),
    "active_false": _role({"active": False}),
    "updated_by_and_updated_at": _role(
        {"active": True}, updated_by="u-other", updated_at=D
    ),
    "period": _role(
        {"period": {"start": "2026-01-01T00:00:00Z", "end": "2026-12-31T23:59:59Z"}}
    ),
    "open_ended_period": _role({"period": {"start": "2026-01-01"}}),
    "practitioner_and_organization": _role(
        {
            "practitioner": {
                "reference": "Practitioner/30001",
                "type": "Practitioner",
                "display": "Dr Careful",
            },
            "organization": {
                "reference": "Organization/190001",
                "identifier": {"system": "urn:org-registry", "value": "ORG-9"},
            },
        }
    ),
    "identifier_with_type_and_assigner": _role(
        {
            "identifier": [
                {
                    "use": "official",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "ROLE",
                            }
                        ]
                    },
                    "system": "https://fhir-server.dev/fhir/identifier-system/role-id",
                    "value": "R-1",
                    "assigner": {"reference": "Organization/190001"},
                }
            ]
        }
    ),
    "code_and_specialty": _role(
        {
            "code": [
                {
                    "coding": [{"code": "doctor", "display": "Doctor"}],
                    "text": "Medical doctor",
                },
                {"text": "Locum"},
            ],
            "specialty": [{"coding": [{"code": "394579002", "display": "Cardiology"}]}],
        }
    ),
    "locations_services_endpoints": _role(
        {
            "location": [{"reference": "Location/230001", "display": "North Wing"}],
            "healthcareService": [{"reference": "HealthcareService/150001"}],
            "endpoint": [{"reference": "Endpoint/620001"}],
        }
    ),
    "telecom": _role(
        {
            "telecom": [
                {"system": "phone", "value": "555-0100", "use": "work", "rank": 1}
            ]
        }
    ),
    "available_time": _role(
        {
            "availableTime": [
                {
                    "daysOfWeek": ["mon", "tue"],
                    "availableStartTime": "08:00:00",
                    "availableEndTime": "17:00:00",
                },
                {"daysOfWeek": ["sat"], "allDay": True},
            ]
        }
    ),
    "not_available": _role(
        {
            "notAvailable": [
                {
                    "description": "Away",
                    "during": {
                        "start": "2026-09-01T00:00:00Z",
                        "end": "2026-09-08T00:00:00Z",
                    },
                }
            ]
        }
    ),
    "availability_exceptions": _role(
        {"availabilityExceptions": "Not on public holidays"}
    ),
    "extension": _role(
        {
            "extension": [
                {
                    "url": "https://fhir-server.dev/fhir/StructureDefinition/x",
                    "valueString": "y",
                }
            ]
        }
    ),
    "full_payload": _role(_stored(FULL)),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_practitioner_role_mapper_emits_valid_fhir_r4(case):
    assert_valid(
        practitioner_role_pb2.PractitionerRole, to_fhir_practitioner_role(CASES[case])
    )


def test_mapper_serves_content_unchanged():
    content = _stored(FULL)
    out = to_fhir_practitioner_role(_role(content))
    assert out["resourceType"] == "PractitionerRole"
    assert out["id"] == "140001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("active as string not boolean", {"active": "yes"}),
        ("misspelled element", {"practitoner": {"reference": "Practitioner/1"}}),
        ("period as string", {"period": "2026"}),
        (
            "practitioner as string not Reference",
            {"practitioner": "Practitioner/30001"},
        ),
        (
            "organization as string not Reference",
            {"organization": "Organization/190001"},
        ),
        ("code as strings not CodeableConcepts", {"code": ["doctor"]}),
        ("location as string not Reference", {"location": ["Location/230001"]}),
        ("telecom as string not ContactPoint", {"telecom": ["555-0100"]}),
        (
            "day of week outside the required binding",
            {"availableTime": [{"daysOfWeek": ["funday"]}]},
        ),
        (
            "notAvailable without its required description",
            {"notAvailable": [{"during": {"start": "2026-01-01T00:00:00Z"}}]},
        ),
        ("availabilityExceptions as list", {"availabilityExceptions": ["x"]}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {
        "resourceType": "PractitionerRole",
        "id": "140001",
        "active": True,
        **broken,
    }
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload),
            practitioner_role_pb2.PractitionerRole,
            validate=True,
        )
