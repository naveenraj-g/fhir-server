"""FHIR R4 conformance for `to_fhir_healthcare_service()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

HealthcareService is stored Medplum-style (like Organization/Practitioner):
the resource lives whole in HealthcareServiceModel.content, and
to_fhir_healthcare_service() only stamps `id` and `meta` onto it. So what can
go wrong on the read side is that stamping (e.g. a malformed meta extension)
or a stored document the server returns that isn't valid R4 — each case below
is a `content` document as the write path would store it, run through the
real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.healthcare_service import to_fhir_healthcare_service
from app.models.healthcare_service import HealthcareServiceModel
from tests.integration.healthcare_service.support import FULL

from .support import assert_valid, fhir_json_text

healthcare_service_pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.healthcare_service_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc)


def _stored(document: dict) -> dict:
    """What the write path stores: everything but resourceType/id/meta."""
    return {
        k: v for k, v in document.items() if k not in ("resourceType", "id", "meta")
    }


def _service(content: dict, **overrides) -> HealthcareServiceModel:
    fields = {
        "healthcare_service_id": 150001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return HealthcareServiceModel(**fields)


CASES = {
    "minimal": _service({"name": "Cardiology"}),
    "active_false": _service({"active": False, "name": "Cardiology"}),
    "updated_by_and_updated_at": _service(
        {"name": "Cardiology"}, updated_by="u-other", updated_at=D
    ),
    "provided_by": _service(
        {
            "providedBy": {
                "reference": "Organization/190001",
                "type": "Organization",
                "display": "General Hospital",
                "identifier": {"system": "urn:org-registry", "value": "ORG-9"},
            }
        }
    ),
    "category_type_specialty": _service(
        {
            "category": [
                {
                    "coding": [{"code": "35", "display": "Specialist Medical"}],
                    "text": "Specialist",
                }
            ],
            "type": [{"coding": [{"code": "124"}]}],
            "specialty": [{"coding": [{"code": "394579002", "display": "Cardiology"}]}],
        }
    ),
    "locations_and_coverage_area": _service(
        {
            "location": [{"reference": "Location/230001", "display": "North Wing"}],
            "coverageArea": [{"reference": "Location/230002"}],
        }
    ),
    "identifier_with_type_and_assigner": _service(
        {
            "identifier": [
                {
                    "use": "official",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "SVC",
                            }
                        ]
                    },
                    "system": "https://fhir-server.dev/fhir/identifier-system/hs-ids",
                    "value": "HS-1",
                    "assigner": {"reference": "Organization/190001"},
                }
            ]
        }
    ),
    "telecom_and_photo": _service(
        {
            "telecom": [
                {"system": "phone", "value": "555-0100", "use": "work", "rank": 1}
            ],
            "photo": {
                "url": "https://fhir-server.dev/fhir/assets/photo.png",
                "title": "Front desk",
            },
        }
    ),
    "eligibility": _service(
        {"eligibility": [{"code": {"text": "Over 18"}, "comment": "Adults only"}]}
    ),
    "available_time": _service(
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
    "not_available": _service(
        {
            "notAvailable": [
                {
                    "description": "Closed",
                    "during": {
                        "start": "2026-12-24T00:00:00Z",
                        "end": "2026-12-26T00:00:00Z",
                    },
                }
            ]
        }
    ),
    "program_characteristic_communication_referral": _service(
        {
            "serviceProvisionCode": [{"coding": [{"code": "free"}]}],
            "program": [{"coding": [{"code": "diabetes"}]}],
            "characteristic": [{"coding": [{"code": "wheelchair"}]}],
            "communication": [{"coding": [{"code": "en"}], "text": "English"}],
            "referralMethod": [{"coding": [{"code": "phone"}]}],
        }
    ),
    "scalars": _service(
        {
            "comment": "Heart care",
            "extraDetails": "More details",
            "appointmentRequired": True,
            "availabilityExceptions": "Closed on public holidays",
        }
    ),
    "endpoint": _service(
        {"endpoint": [{"identifier": {"system": "urn:ep", "value": "EP-1"}}]}
    ),
    "extension": _service(
        {
            "extension": [
                {
                    "url": "https://fhir-server.dev/fhir/StructureDefinition/x",
                    "valueString": "y",
                }
            ]
        }
    ),
    "full_payload": _service(_stored(FULL)),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_healthcare_service_mapper_emits_valid_fhir_r4(case):
    assert_valid(
        healthcare_service_pb2.HealthcareService,
        to_fhir_healthcare_service(CASES[case]),
    )


def test_mapper_serves_content_unchanged():
    content = _stored(FULL)
    out = to_fhir_healthcare_service(_service(content))
    assert out["resourceType"] == "HealthcareService"
    assert out["id"] == "150001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# ── Guarding the oracle ────────────────────────────────────────────────────────
# If google-fhir-r4 ever stops validating — a version bump, a changed API, a
# silently-swallowed error — every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array where
# the spec says 0..1, e.g. `photo: [{...}]`.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("active as string not boolean", {"active": "yes"}),
        ("misspelled element", {"nam3": "Cardiology"}),
        ("name as object not string", {"name": {"text": "Cardiology"}}),
        ("category as strings not CodeableConcepts", {"category": ["35"]}),
        ("providedBy as string not Reference", {"providedBy": "Organization/190001"}),
        ("location as string not Reference", {"location": ["Location/230001"]}),
        (
            "day of week outside the required binding",
            {"availableTime": [{"daysOfWeek": ["funday"]}]},
        ),
        (
            "notAvailable without its required description",
            {"notAvailable": [{"during": {"start": "2026-01-01T00:00:00Z"}}]},
        ),
        ("appointmentRequired as string", {"appointmentRequired": "yes"}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {
        "resourceType": "HealthcareService",
        "id": "150001",
        "active": True,
        "name": "Cardiology",
        **broken,
    }
    with pytest.raises(Exception):  # noqa: B017 — the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload),
            healthcare_service_pb2.HealthcareService,
            validate=True,
        )
