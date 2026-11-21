"""Observation as a *target*: the other rebuilt resources that point at an Observation.

A reference between resources has no foreign key, so the server checks that the target exists
when the referencing resource is written, and the search engine can follow it (chaining,
`_include`, `_revinclude`). This file covers the resources whose element can be an Observation:
`DiagnosticReport.result`, `Immunization.reaction.detail` / `reasonReference`, `Procedure` /
`Encounter` / `Appointment` / `RiskAssessment` / `FamilyMemberHistory` `reasonReference`,
`ClinicalImpression.investigation.item` / `finding.itemReference` / `supportingInfo`,
`Condition.stage.assessment` and `DetectedIssue.implicated` / `evidence.detail`.
"""

import pytest

from tests.integration.observation.support import (
    API,
    BASE,
    create_observation,
    create_patient,
    create_procedure,
    encounter_body,
    immunization_body,
    loinc,
    observation_body,
    procedure_body,
)


def _ref(observation) -> dict:
    return {"reference": f"Observation/{observation}"}


# resource path -> body that points at an Observation (given a patient id and the reference)
_PARTNERS = {
    "diagnostic-reports": lambda p, ref: {
        "status": "final",
        "code": {"text": "Report"},
        "subject": {"reference": f"Patient/{p}"},
        "result": [ref],
    },
    "immunizations": lambda p, ref: {
        **immunization_body(p),
        "reasonReference": [ref],
    },
    "immunizations#reaction": lambda p, ref: {
        **immunization_body(p),
        "reaction": [{"date": "2023-01-16", "detail": ref}],
    },
    "procedures": lambda p, ref: {**procedure_body(p), "reasonReference": [ref]},
    "encounters": lambda p, ref: {**encounter_body(), "reasonReference": [ref]},
    "appointments": lambda p, ref: {
        "status": "booked",
        "participant": [{"actor": {"reference": f"Patient/{p}"}, "status": "accepted"}],
        "reasonReference": [ref],
    },
    "risk-assessments": lambda p, ref: {
        "status": "final",
        "subject": {"reference": f"Patient/{p}"},
        "reasonReference": [ref],
    },
    "family-member-histories": lambda p, ref: {
        "status": "completed",
        "patient": {"reference": f"Patient/{p}"},
        "relationship": {"text": "Mother"},
        "reasonReference": [ref],
    },
    "clinical-impressions#investigation": lambda p, ref: {
        "status": "completed",
        "subject": {"reference": f"Patient/{p}"},
        "investigation": [{"code": {"text": "Labs"}, "item": [ref]}],
    },
    "clinical-impressions#finding": lambda p, ref: {
        "status": "completed",
        "subject": {"reference": f"Patient/{p}"},
        "finding": [{"itemReference": ref}],
    },
    "clinical-impressions#supporting": lambda p, ref: {
        "status": "completed",
        "subject": {"reference": f"Patient/{p}"},
        "supportingInfo": [ref],
    },
    "conditions": lambda p, ref: {
        "subject": {"reference": f"Patient/{p}"},
        "stage": [{"assessment": [ref]}],
    },
    "detected-issues#implicated": lambda p, ref: {
        "status": "final",
        "patient": {"reference": f"Patient/{p}"},
        "implicated": [ref],
    },
    "detected-issues#evidence": lambda p, ref: {
        "status": "final",
        "patient": {"reference": f"Patient/{p}"},
        "evidence": [{"detail": [ref]}],
    },
}


@pytest.fixture
async def patient(client) -> int:
    return await create_patient(client)


@pytest.fixture
async def observation(client, patient) -> int:
    return await create_observation(
        client,
        observation_body(patient, code=loinc("85354-9", "Blood pressure panel")),
    )


@pytest.mark.parametrize("partner", sorted(_PARTNERS))
async def test_a_reference_to_an_observation_is_existence_checked(
    client, patient, observation, partner
):
    path = partner.split("#")[0]
    url = f"{API}/{path}/"
    resp = await client.post(url, json=_PARTNERS[partner](patient, _ref(observation)))
    assert resp.status_code == 201, (partner, resp.text)
    missing = await client.post(url, json=_PARTNERS[partner](patient, _ref(999999)))
    assert missing.status_code == 422, (partner, missing.text)
    # an absolute URL or a logical reference is stored as sent
    absolute = {"reference": "https://other.example.org/fhir/Observation/9"}
    resp = await client.post(url, json=_PARTNERS[partner](patient, absolute))
    assert resp.status_code == 201, (partner, resp.text)


async def test_an_observation_in_another_org_is_rejected(client, other_client, patient):
    from app.auth.dependencies import get_current_user
    from app.main import app
    from tests.conftest import make_test_user
    from tests.integration.observation.conftest import OBSERVATION_PERMS

    def as_user(**kw):
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=OBSERVATION_PERMS, **kw
        )

    as_user(sub="u-other", org_id="org-other")
    try:
        other_patient = await create_patient(other_client)
        theirs = await create_observation(other_client, observation_body(other_patient))
    finally:
        as_user()
    resp = await client.post(
        f"{API}/diagnostic-reports/",
        json=_PARTNERS["diagnostic-reports"](patient, _ref(theirs)),
    )
    assert resp.status_code == 422


# ── DiagnosticReport.result: chaining, _include, _revinclude ─────────────────


async def test_diagnostic_report_result_chains_includes_and_revincludes(
    client, patient
):
    bp = await create_observation(
        client,
        observation_body(patient, code=loinc("85354-9", "Blood pressure panel")),
    )
    weight = await create_observation(
        client, observation_body(patient, code=loinc("29463-7", "Body weight"))
    )
    report = (
        await client.post(
            f"{API}/diagnostic-reports/",
            json=_PARTNERS["diagnostic-reports"](patient, _ref(bp)),
        )
    ).json()["id"]
    other_report = (
        await client.post(
            f"{API}/diagnostic-reports/",
            json=_PARTNERS["diagnostic-reports"](patient, _ref(weight)),
        )
    ).json()["id"]

    def ids(bundle, rtype, mode):
        return {
            e["resource"]["id"]
            for e in bundle.get("entry") or []
            if e["resource"]["resourceType"] == rtype and e["search"]["mode"] == mode
        }

    found = (
        await client.get(
            f"{API}/diagnostic-reports/", params={"result.code": "85354-9"}
        )
    ).json()
    assert ids(found, "DiagnosticReport", "match") == {report}
    found = (
        await client.get(f"{API}/diagnostic-reports/", params={"result": str(weight)})
    ).json()
    assert ids(found, "DiagnosticReport", "match") == {other_report}
    included = (
        await client.get(
            f"{API}/diagnostic-reports/",
            params={"_id": report, "_include": "DiagnosticReport:result"},
        )
    ).json()
    assert ids(included, "Observation", "include") == {str(bp)}
    reverse = (
        await client.get(
            f"{BASE}/",
            params={"_id": str(bp), "_revinclude": "DiagnosticReport:result"},
        )
    ).json()
    assert ids(reverse, "DiagnosticReport", "include") == {report}


# ── Immunization / Procedure / Encounter / ClinicalImpression ────────────────


async def test_immunization_reaction_and_reason_chain_include_and_revinclude(
    client, patient, observation
):
    reaction = (
        await client.post(
            f"{API}/immunizations/",
            json=_PARTNERS["immunizations#reaction"](patient, _ref(observation)),
        )
    ).json()["id"]
    reason = (
        await client.post(
            f"{API}/immunizations/",
            json=_PARTNERS["immunizations"](patient, _ref(observation)),
        )
    ).json()["id"]

    def match(bundle):
        return {
            e["resource"]["id"]
            for e in bundle["entry"]
            if e["search"]["mode"] == "match"
        }

    def inc(bundle):
        return {
            e["resource"]["id"]
            for e in bundle.get("entry") or []
            if e["search"]["mode"] == "include"
        }

    got = (
        await client.get(f"{API}/immunizations/", params={"reaction.code": "85354-9"})
    ).json()
    assert match(got) == {reaction}
    got = (
        await client.get(
            f"{API}/immunizations/",
            params={"reason-reference:Observation.code": "85354-9"},
        )
    ).json()
    assert match(got) == {reason}
    got = (
        await client.get(
            f"{API}/immunizations/",
            params={"_id": reaction, "_include": "Immunization:reaction"},
        )
    ).json()
    assert inc(got) == {str(observation)}
    got = (
        await client.get(
            f"{BASE}/",
            params={"_id": str(observation), "_revinclude": "Immunization:reaction"},
        )
    ).json()
    assert inc(got) == {reaction}
    got = (
        await client.get(
            f"{BASE}/",
            params={
                "_id": str(observation),
                "_revinclude": "Immunization:reason-reference",
            },
        )
    ).json()
    assert inc(got) == {reason}


@pytest.mark.parametrize(
    "path,partner,param",
    [
        ("procedures", "procedures", "reason-reference"),
        ("encounters", "encounters", "reason-reference"),
        ("appointments", "appointments", "reason-reference"),
        ("clinical-impressions", "clinical-impressions#investigation", "investigation"),
        ("clinical-impressions", "clinical-impressions#finding", "finding-ref"),
        ("clinical-impressions", "clinical-impressions#supporting", "supporting-info"),
        ("detected-issues", "detected-issues#implicated", "implicated"),
    ],
)
async def test_a_reference_parameter_chains_to_an_observation_and_includes_it(
    client, patient, observation, path, partner, param
):
    created = (
        await client.post(
            f"{API}/{path}/", json=_PARTNERS[partner](patient, _ref(observation))
        )
    ).json()["id"]
    chained = (
        await client.get(
            f"{API}/{path}/", params={f"{param}:Observation.code": "85354-9"}
        )
    ).json()
    assert {e["resource"]["id"] for e in chained["entry"]} == {created}
    nothing = (
        await client.get(
            f"{API}/{path}/", params={f"{param}:Observation.code": "29463-7"}
        )
    ).json()
    assert nothing["total"] == 0
    included = (
        await client.get(
            f"{API}/{path}/",
            params={"_id": created, "_include": f"{_RESOURCE[path]}:{param}"},
        )
    ).json()
    assert {
        e["resource"]["id"]
        for e in included["entry"]
        if e["search"]["mode"] == "include"
    } == {str(observation)}


_RESOURCE = {
    "procedures": "Procedure",
    "encounters": "Encounter",
    "appointments": "Appointment",
    "clinical-impressions": "ClinicalImpression",
    "detected-issues": "DetectedIssue",
}


async def test_the_observation_can_be_found_from_what_points_at_it(
    client, patient, observation
):
    procedure = await create_procedure(client, procedure_body(patient))
    # nothing points at it yet
    bundle = (
        await client.get(
            f"{BASE}/",
            params={
                "_id": str(observation),
                "_revinclude": "Procedure:reason-reference",
            },
        )
    ).json()
    assert [e for e in bundle["entry"] if e["search"]["mode"] == "include"] == []
    created = (
        await client.post(
            f"{API}/procedures/",
            json={**procedure_body(patient), "reasonReference": [_ref(observation)]},
        )
    ).json()["id"]
    bundle = (
        await client.get(
            f"{BASE}/",
            params={
                "_id": str(observation),
                "_revinclude": "Procedure:reason-reference",
            },
        )
    ).json()
    assert {
        e["resource"]["id"] for e in bundle["entry"] if e["search"]["mode"] == "include"
    } == {created}
    assert procedure != created
