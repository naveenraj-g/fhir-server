"""FHIR R4 conformance for `to_fhir_episode_of_care()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

EpisodeOfCare is stored Medplum-style (like CareTeam, CarePlan, Encounter and the other
content-based resources): the resource lives whole in EpisodeOfCareModel.content, and
to_fhir_episode_of_care() only stamps `id` and `meta` onto it. So what can go wrong on the read
side is that stamping (e.g. a malformed meta extension) or a stored document the server returns
that isn't valid R4 - each case below is a `content` document as the write path would store it,
run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.episode_of_care import to_fhir_episode_of_care
from app.models.episode_of_care import EpisodeOfCareModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.episode_of_care_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
EOC_TYPE = "http://terminology.hl7.org/CodeSystem/episodeofcare-type"
PATIENT = {"reference": "Patient/10001"}
TYPE = {
    "coding": [{"system": EOC_TYPE, "code": "cacp", "display": "Community aged care"}]
}
ROLE = {
    "coding": [
        {
            "system": "http://terminology.hl7.org/CodeSystem/diagnosis-role",
            "code": "AD",
        }
    ]
}


def _c(content: dict, **overrides) -> EpisodeOfCareModel:
    fields = {
        "episode_of_care_id": 350001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return EpisodeOfCareModel(**fields)


def _base(**extra) -> dict:
    return {"status": "active", "patient": PATIENT, **extra}


CASES = {
    "minimal": _c(_base()),
    "updated_by_and_updated_at": _c(_base(), updated_by="u-other", updated_at=D),
    "identifier_with_type_and_assigner": _c(
        _base(
            identifier=[
                {
                    "use": "official",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "MR",
                            }
                        ]
                    },
                    "system": "https://fhir-server.dev/fhir/identifier-system/episode-of-care-id",
                    "value": "EOC-1",
                    "period": {"start": "2020-01-01"},
                    "assigner": {"reference": "Organization/190001"},
                }
            ]
        )
    ),
    **{
        f"status_{s}": _c(_base(status=s))
        for s in (
            "planned",
            "waitlist",
            "active",
            "onhold",
            "finished",
            "cancelled",
            "entered-in-error",
        )
    },
    "status_history": _c(
        _base(
            statusHistory=[
                {
                    "status": "planned",
                    "period": {"start": "2025-12-01", "end": "2025-12-31"},
                },
                {"status": "active", "period": {"start": "2026-01-01"}},
            ]
        )
    ),
    "type": _c(_base(type=[TYPE, {"text": "Free text type"}])),
    "diagnosis_with_role_and_rank": _c(
        _base(
            diagnosis=[
                {
                    "condition": {"reference": "Condition/120001"},
                    "role": ROLE,
                    "rank": 1,
                },
                {"condition": {"reference": "Condition/120002"}},
            ]
        )
    ),
    "patient_absolute_url": _c(
        {
            "status": "active",
            "patient": {"reference": "https://other.example.org/fhir/Patient/1"},
        }
    ),
    "patient_logical_identifier": _c(
        {
            "status": "active",
            "patient": {"identifier": {"system": "urn:mrn", "value": "M-1"}},
        }
    ),
    "managing_organization": _c(
        _base(
            managingOrganization={
                "reference": "Organization/190001",
                "display": "Providing Org",
            }
        )
    ),
    "period_closed": _c(_base(period={"start": "2026-01-01", "end": "2026-06-30"})),
    "period_open": _c(_base(period={"start": "2026-01-01"})),
    "referral_requests": _c(
        _base(
            referralRequest=[
                {"reference": "ServiceRequest/80001"},
                {"reference": "https://other.example.org/fhir/ServiceRequest/9"},
            ]
        )
    ),
    "care_manager_practitioner": _c(
        _base(careManager={"reference": "Practitioner/30001"})
    ),
    "care_manager_role": _c(
        _base(careManager={"reference": "PractitionerRole/140001"})
    ),
    "team_and_account": _c(
        _base(
            team=[{"reference": "CareTeam/390001"}],
            account=[{"reference": "Account/7"}],
        )
    ),
    "extension": _c(
        _base(extension=[{"url": "http://example.org/ext", "valueString": "kept"}])
    ),
    "full": _c(
        _base(
            identifier=[{"system": "urn:eoc", "value": "EOC-1001"}],
            statusHistory=[
                {"status": "planned", "period": {"start": "2025-12-01"}},
            ],
            type=[TYPE],
            diagnosis=[
                {
                    "condition": {"reference": "Condition/120001"},
                    "role": ROLE,
                    "rank": 1,
                }
            ],
            managingOrganization={"reference": "Organization/190001"},
            period={"start": "2026-01-01"},
            referralRequest=[{"reference": "ServiceRequest/80001"}],
            careManager={"reference": "Practitioner/30001"},
            team=[{"reference": "CareTeam/390001"}],
            account=[{"reference": "Account/7"}],
        )
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_episode_of_care_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.EpisodeOfCare, to_fhir_episode_of_care(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = _base(type=[TYPE])
    out = to_fhir_episode_of_care(_c(content))
    assert out["resourceType"] == "EpisodeOfCare"
    assert out["id"] == "350001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# -- Guarding the oracle ---------------------------------------------------------------------
# If google-fhir-r4 ever stops validating - a version bump, a changed API, a
# silently-swallowed error - every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 - `patient` or `period` as a one-item list; the integration
# tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("status with an unknown code", {"status": "retired"}),
        ("status as number", {"status": 1}),
        ("type as object not a list", {"type": {"text": "x"}}),
        ("type entry as string", {"type": ["x"]}),
        ("patient as string", {"patient": "Patient/1"}),
        ("managingOrganization as string", {"managingOrganization": "Organization/1"}),
        ("careManager as string", {"careManager": "Practitioner/1"}),
        ("period as string", {"period": "2026"}),
        ("period start as number", {"period": {"start": 2026}}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("statusHistory as object not a list", {"statusHistory": {"status": "active"}}),
        (
            "statusHistory status with an unknown code",
            {"statusHistory": [{"status": "retired", "period": {"start": "2026"}}]},
        ),
        (
            "statusHistory period as string",
            {"statusHistory": [{"status": "active", "period": "2026"}]},
        ),
        ("diagnosis as object not a list", {"diagnosis": {"rank": 1}}),
        (
            "diagnosis condition as string",
            {"diagnosis": [{"condition": "Condition/1"}]},
        ),
        (
            "diagnosis rank as string",
            {
                "diagnosis": [
                    {"condition": {"reference": "Condition/1"}, "rank": "first"}
                ]
            },
        ),
        ("diagnosis role as object not a concept", {"diagnosis": [{"role": "x"}]}),
        (
            "referralRequest as object",
            {"referralRequest": {"reference": "ServiceRequest/1"}},
        ),
        ("team as object", {"team": {"reference": "CareTeam/1"}}),
        ("account as object", {"account": {"reference": "Account/1"}}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "EpisodeOfCare", "id": "350001", **broken}
    with pytest.raises(Exception):  # noqa: B017 - the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.EpisodeOfCare, validate=True
        )
