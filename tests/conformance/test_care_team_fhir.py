"""FHIR R4 conformance for `to_fhir_care_team()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

CareTeam is stored Medplum-style (like Patient, Appointment, Encounter, Condition, Procedure,
Specimen, Group and the other content-based resources): the resource lives whole in
CareTeamModel.content, and to_fhir_care_team() only stamps `id` and `meta` onto it. So what can
go wrong on the read side is that stamping (e.g. a malformed meta extension) or a stored
document the server returns that isn't valid R4 - each case below is a `content` document as the
write path would store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.care_team import to_fhir_care_team
from app.models.care_team import CareTeamModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.care_team_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
SCT = "http://snomed.info/sct"
LOINC = "http://loinc.org"
CODE = {"coding": [{"system": SCT, "code": "17561000", "display": "Cardiologist"}]}


def _c(content: dict, **overrides) -> CareTeamModel:
    fields = {
        "care_team_id": 390001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return CareTeamModel(**fields)


CASES = {
    "empty": _c({}),
    "updated_by_and_updated_at": _c({}, updated_by="u-other", updated_at=D),
    "identifier_with_type_and_assigner": _c(
        {
            "identifier": [
                {
                    "use": "official",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "FILL",
                            }
                        ]
                    },
                    "system": "https://fhir-server.dev/fhir/identifier-system/care-team-id",
                    "value": "CT-1",
                    "period": {"start": "2020-01-01"},
                    "assigner": {"reference": "Organization/190001"},
                }
            ]
        }
    ),
    **{
        f"status_{s}": _c({"status": s})
        for s in ("proposed", "active", "suspended", "inactive", "entered-in-error")
    },
    "category_coded": _c(
        {
            "category": [
                {
                    "coding": [
                        {
                            "system": LOINC,
                            "code": "LA27976-2",
                            "display": "Encounter-focused care team",
                        }
                    ],
                    "text": "Encounter-focused",
                }
            ]
        }
    ),
    "category_text_only": _c({"category": [{"text": "Home care"}]}),
    "category_several": _c(
        {"category": [{"text": "Home care"}, {"text": "Palliative"}]}
    ),
    "name": _c({"name": "Cardiology care team"}),
    "subject_patient": _c({"subject": {"reference": "Patient/10001"}}),
    "subject_group": _c({"subject": {"reference": "Group/430001"}}),
    "subject_logical": _c(
        {"subject": {"identifier": {"system": "urn:s", "value": "S-9"}, "display": "X"}}
    ),
    "subject_absolute_url": _c(
        {"subject": {"reference": "https://other.example.org/fhir/Patient/1"}}
    ),
    "encounter": _c({"encounter": {"reference": "Encounter/20001"}}),
    "period_closed": _c({"period": {"start": "2026-01-01", "end": "2026-06-30"}}),
    "period_open_ended": _c({"period": {"start": "2026-01-01T09:00:00Z"}}),
    "period_end_only": _c({"period": {"end": "2026-06-30"}}),
    "participant_member_only": _c(
        {"participant": [{"member": {"reference": "Practitioner/30001"}}]}
    ),
    **{
        f"participant_member_{t}": _c(
            {"participant": [{"member": {"reference": f"{t}/1"}}]}
        )
        for t in (
            "Practitioner",
            "PractitionerRole",
            "RelatedPerson",
            "Patient",
            "Organization",
            "CareTeam",
        )
    },
    "participant_role_period": _c(
        {
            "participant": [
                {
                    "role": [CODE, {"text": "Lead"}],
                    "member": {"reference": "Practitioner/30001"},
                    "onBehalfOf": {"reference": "Organization/190001"},
                    "period": {"start": "2026-01-01", "end": "2026-06-30"},
                }
            ]
        }
    ),
    "participant_several": _c(
        {
            "participant": [
                {"member": {"reference": "Practitioner/30001"}},
                {"member": {"reference": "Patient/10001"}},
                {"role": [CODE]},
            ]
        }
    ),
    "participant_member_logical": _c(
        {
            "participant": [
                {"member": {"identifier": {"system": "urn:p", "value": "P-9"}}}
            ]
        }
    ),
    "reason_code": _c({"reasonCode": [CODE, {"text": "Heart failure"}]}),
    "reason_reference": _c({"reasonReference": [{"reference": "Condition/120001"}]}),
    "managing_organization": _c(
        {
            "managingOrganization": [
                {"reference": "Organization/190001"},
                {"reference": "https://other.example.org/fhir/Organization/7"},
            ]
        }
    ),
    "telecom": _c(
        {
            "telecom": [
                {"system": "phone", "value": "+1-555-0100", "use": "work", "rank": 1},
                {"system": "email", "value": "team@example.org"},
            ]
        }
    ),
    "note_author_reference": _c(
        {
            "note": [
                {
                    "authorReference": {"reference": "Practitioner/30001"},
                    "time": "2026-02-01T10:00:00Z",
                    "text": "Weekly review.",
                }
            ]
        }
    ),
    "note_author_string": _c({"note": [{"authorString": "Dr. A", "text": "x"}]}),
    "extension": _c({"extension": [{"url": "https://x/ext", "valueString": "y"}]}),
    "everything": _c(
        {
            "identifier": [{"system": "urn:ct", "value": "CT-1"}],
            "status": "active",
            "category": [{"text": "Home care"}],
            "name": "Cardiology care team",
            "subject": {"reference": "Patient/10001"},
            "encounter": {"reference": "Encounter/20001"},
            "period": {"start": "2026-01-01", "end": "2026-06-30"},
            "participant": [
                {
                    "role": [CODE],
                    "member": {"reference": "Practitioner/30001"},
                    "onBehalfOf": {"reference": "Organization/190001"},
                    "period": {"start": "2026-01-01"},
                }
            ],
            "reasonCode": [CODE],
            "reasonReference": [{"reference": "Condition/120001"}],
            "managingOrganization": [{"reference": "Organization/190001"}],
            "telecom": [{"system": "phone", "value": "+1-555-0100"}],
            "note": [{"text": "Weekly review."}],
        }
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_care_team_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.CareTeam, to_fhir_care_team(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {"status": "active", "name": "Cardiology care team"}
    out = to_fhir_care_team(_c(content))
    assert out["resourceType"] == "CareTeam"
    assert out["id"] == "390001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# -- Guarding the oracle ---------------------------------------------------------------------
# If google-fhir-r4 ever stops validating - a version bump, a changed API, a
# silently-swallowed error - every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 - `subject` or `period` as a one-item list; the integration
# tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("status with an unknown code", {"status": "retired"}),
        ("status as number", {"status": 1}),
        ("name as number", {"name": 5}),
        ("category as object not a list", {"category": {"text": "x"}}),
        ("category entry as string", {"category": ["x"]}),
        ("subject as string", {"subject": "Patient/1"}),
        ("encounter as string", {"encounter": "Encounter/1"}),
        ("period as string", {"period": "2026"}),
        ("period start as number", {"period": {"start": 2026}}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("participant as object not a list", {"participant": {"role": []}}),
        ("participant member as string", {"participant": [{"member": "Patient/1"}]}),
        ("participant role as object", {"participant": [{"role": {"text": "x"}}]}),
        (
            "participant onBehalfOf as string",
            {"participant": [{"onBehalfOf": "Organization/1"}]},
        ),
        ("participant period as string", {"participant": [{"period": "2026"}]}),
        ("reasonCode as object not a list", {"reasonCode": {"text": "x"}}),
        (
            "reasonReference as object",
            {"reasonReference": {"reference": "Condition/1"}},
        ),
        (
            "managingOrganization as object",
            {"managingOrganization": {"reference": "Organization/1"}},
        ),
        ("telecom as object not a list", {"telecom": {"value": "x"}}),
        ("telecom with an unknown system", {"telecom": [{"system": "pigeon"}]}),
        ("note as object not a list", {"note": {"text": "x"}}),
        ("note without text", {"note": [{"authorString": "x"}]}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "CareTeam", "id": "390001", **broken}
    with pytest.raises(Exception):  # noqa: B017 - the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.CareTeam, validate=True
        )
