"""FHIR R4 search over RiskAssessment (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/riskassessment.html#search).

One block per search parameter — `method` and `risk` are tokens on CodeableConcepts, `identifier`
a token on an Identifier, `date` a dateTime range (an `occurrencePeriod` is not searched),
`probability` the engine's first `number` search (over a decimal or a Range), the single-target
references (`patient`, `encounter`, `condition`) and the multi-target ones (`subject`,
`performer`) — then chaining, `_include`/`_revinclude`, result parameters, combination rules,
lenient vs strict handling and POST _search. There is deliberately no `status` search: R4 defines
none for this resource.
"""

import pytest

from tests.integration.risk_assessment.support import (
    API,
    ASSESSMENT_IDS,
    BASE,
    RISK,
    SCT,
    V2_0203,
    assessment_body,
    condition_body,
    create_assessment,
    create_condition,
    create_encounter,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    encounter_body,
    percent,
    risk,
)

KEYS = ("a", "b", "c", "d", "e")
ALL = set(KEYS)


def _ids(bundle: dict) -> set[int]:
    return {
        int(e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == "match"
    }


def _of_type(bundle: dict, rtype: str, mode: str) -> set[str]:
    return {
        e["resource"]["id"]
        for e in bundle.get("entry") or []
        if e["resource"]["resourceType"] == rtype and e["search"]["mode"] == mode
    }


@pytest.fixture
async def world(client):
    """Two patients, a practitioner, a practitioner role, an encounter and a condition, plus five
    assessments with distinct, searchable values. Returns {key: id}."""
    w = {}
    w["p1"] = await create_patient(
        client, {"active": True, "name": [{"family": "Windsor", "given": ["Anna"]}]}
    )
    w["p2"] = await create_patient(
        client, {"active": True, "name": [{"family": "Fairfax", "given": ["Ben"]}]}
    )
    w["pr"] = await create_practitioner(client)  # family "Careful"
    w["role"] = await create_practitioner_role(client)
    w["enc"] = await create_encounter(client, encounter_body())
    w["cond"] = await create_condition(client, condition_body(w["p1"]))
    w["a"] = await create_assessment(
        client,
        assessment_body(
            w["p1"],
            "final",
            identifier=[
                {
                    "system": ASSESSMENT_IDS,
                    "value": "RA-A",
                    "type": {
                        "coding": [{"system": V2_0203, "code": "FILL"}],
                        "text": "Risk id",
                    },
                }
            ],
            method={
                "coding": [
                    {"system": SCT, "code": "225338004", "display": "Risk assessment"}
                ]
            },
            occurrenceDateTime="2023-01-15T09:30:00Z",
            encounter={"reference": f"Encounter/{w['enc']}"},
            condition={"reference": f"Condition/{w['cond']}"},
            performer={"reference": f"Practitioner/{w['pr']}"},
            prediction=[
                {
                    "probabilityDecimal": 12.5,
                    "qualitativeRisk": risk("moderate", "moderate likelihood"),
                },
                {
                    "probabilityRange": {"low": percent(5), "high": percent(10)},
                    "qualitativeRisk": risk("low"),
                },
            ],
        ),
    )
    w["b"] = await create_assessment(
        client,
        assessment_body(
            w["p2"],
            "preliminary",
            identifier=[{"system": ASSESSMENT_IDS, "value": "RA-B"}],
            method={"text": "Clinical judgement"},
            occurrenceDateTime="2024-02",
            performer={"reference": f"PractitionerRole/{w['role']}"},
            prediction=[
                {"probabilityDecimal": 80, "qualitativeRisk": {"text": "Very high"}}
            ],
        ),
    )
    w["c"] = await create_assessment(
        client,
        assessment_body(
            w["p1"],
            "amended",
            occurrencePeriod={"start": "2022-01-01", "end": "2022-02-01"},
            performer={"reference": "Device/5"},
            prediction=[
                {
                    "probabilityRange": {"low": percent(50)},
                    "qualitativeRisk": risk("high"),
                }
            ],
        ),
    )
    w["d"] = await create_assessment(
        client,
        {
            "status": "cancelled",
            "subject": {"reference": "Group/430001"},
            "occurrenceDateTime": "2019",
        },
    )
    w["e"] = await create_assessment(
        client,
        {
            "status": "final",
            "subject": {
                "identifier": {"system": "urn:pts", "value": "P-9"},
                "display": "External",
            },
            "occurrenceDateTime": "2024-03-01T00:00:00Z",
            "prediction": [{"probabilityDecimal": 0.5}],
        },
    )
    return w


async def _search(client, **params) -> dict:
    resp = await client.get(BASE + "/", params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _keys(client, world, **params) -> set[str]:
    ids = _ids(await _search(client, **params))
    by_id = {world[k]: k for k in KEYS}
    return {by_id[i] for i in ids}


async def _status(client, **params) -> int:
    return (await client.get(BASE + "/", params=params)).status_code


async def _other(client, path: str, **params) -> dict:
    resp = await client.get(f"{API}/{path}/", params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


# ── _id / _lastUpdated ───────────────────────────────────────────────────────


async def test_id(client, world):
    assert await _keys(client, world, _id=str(world["a"])) == {"a"}
    assert await _keys(client, world, _id="999999") == set()
    assert await _keys(client, world, **{"_id:not": str(world["a"])}) == ALL - {"a"}


async def test_last_updated(client, world):
    assert await _keys(client, world, _lastUpdated="ge2020-01-01") == ALL
    assert await _keys(client, world, _lastUpdated="lt2020-01-01") == set()


async def test_there_is_no_status_search(client, world):
    """R4 defines no `status` search parameter for RiskAssessment: it is an unknown parameter."""
    lenient = await client.get(BASE + "/", params={"status": "final"})
    assert lenient.status_code == 200
    assert any(e["search"]["mode"] == "outcome" for e in lenient.json()["entry"])
    strict = await client.get(
        BASE + "/", params={"status": "final"}, headers={"Prefer": "handling=strict"}
    )
    assert strict.status_code == 400


# ── date ─────────────────────────────────────────────────────────────────────


async def test_date(client, world):
    assert await _keys(client, world, date="2023-01-15") == {"a"}
    assert await _keys(client, world, date="2023") == {"a"}
    assert await _keys(client, world, date="2024") == {
        "b",
        "e",
    }  # 2024-02 and 2024-03-01 lie inside 2024
    assert await _keys(client, world, date="ge2024-01-01") == {"b", "e"}
    assert await _keys(client, world, date="lt2023-01-01") == {"d"}
    assert await _keys(client, world, date="sa2023-02-01") == {"b", "e"}
    assert await _keys(client, world, date="eb2020-01-01") == {"d"}
    # an occurrencePeriod is not `(occurrence as dateTime)`: it is not searched and counts as missing
    assert await _keys(client, world, **{"date:missing": "true"}) == {"c"}
    assert await _keys(client, world, **{"date:missing": "false"}) == {
        "a",
        "b",
        "d",
        "e",
    }


# ── identifier ───────────────────────────────────────────────────────────────


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="RA-A") == {"a"}
    assert await _keys(client, world, identifier=f"{ASSESSMENT_IDS}|RA-B") == {"b"}
    assert await _keys(client, world, identifier="RA-A,RA-B") == {"a", "b"}
    assert await _keys(client, world, identifier="urn:wrong|RA-A") == set()
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|FILL|RA-A"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|FILL|RA-B"})
        == set()
    )
    assert await _keys(client, world, **{"identifier:text": "risk"}) == {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


# ── method / risk ────────────────────────────────────────────────────────────


async def test_method(client, world):
    assert await _keys(client, world, method="225338004") == {"a"}
    assert await _keys(client, world, method=f"{SCT}|225338004") == {"a"}
    assert await _keys(client, world, method="http://wrong|225338004") == set()
    assert await _keys(client, world, **{"method:text": "clinical"}) == {
        "b"
    }  # a text-only concept is found
    assert await _keys(client, world, **{"method:text": "risk"}) == {
        "a"
    }  # Coding.display
    assert await _keys(client, world, **{"method:missing": "true"}) == {"c", "d", "e"}


async def test_risk_reads_every_prediction(client, world):
    assert await _keys(client, world, risk="moderate") == {"a"}
    assert await _keys(client, world, risk="low") == {
        "a"
    }  # the second prediction of `a`
    assert await _keys(client, world, risk=f"{RISK}|high") == {"c"}
    assert await _keys(client, world, risk="low,high") == {"a", "c"}
    assert await _keys(client, world, **{"risk:text": "very high"}) == {"b"}
    assert await _keys(client, world, **{"risk:text": "moderate likelihood"}) == {"a"}
    assert await _keys(client, world, **{"risk:missing": "true"}) == {"d", "e"}


# ── probability (number) ─────────────────────────────────────────────────────


async def test_probability_number(client, world):
    assert await _keys(client, world, probability="12.5") == {"a"}
    assert await _keys(client, world, probability="80") == {"b"}
    assert await _keys(client, world, probability="0.5") == {"e"}
    assert await _keys(client, world, probability="gt50") == {
        "b",
        "c",
    }  # 80, and 50-open-above
    assert await _keys(client, world, probability="lt6") == {
        "a",
        "e",
    }  # the 5-10% range, and 0.5
    assert await _keys(client, world, probability="ge80") == {"b", "c"}
    assert await _keys(client, world, probability="le0.5") == {"e"}
    assert await _keys(client, world, probability="sa10") == {"a", "b", "c"}
    assert await _keys(client, world, probability="ap12") == {"a"}
    assert await _keys(client, world, probability="ne12.5") == {
        "a",
        "b",
        "c",
        "e",
    }  # a: the other prediction is not 12.5
    assert await _keys(client, world, probability="12.5,80") == {"a", "b"}
    assert await _keys(client, world, **{"probability:missing": "true"}) == {"d"}
    assert await _keys(client, world, **{"probability:missing": "false"}) == {
        "a",
        "b",
        "c",
        "e",
    }


async def test_probability_rejects_bad_values(client, world):
    assert await _status(client, probability="abc") == 400
    assert (
        await _status(client, probability="1|http://unitsofmeasure.org|%") == 400
    )  # a number takes no unit
    assert await _status(client, **{"probability:exact": "1"}) == 400
    assert await _status(client, **{"probability:contains": "1"}) == 400


# ── patient / subject ────────────────────────────────────────────────────────


async def test_patient(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {
        "a",
        "c",
    }  # one target: a bare id works
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"b"}
    assert await _keys(client, world, patient=f"{world['p1']},{world['p2']}") == {
        "a",
        "b",
        "c",
    }
    assert await _keys(client, world, patient="999999") == set()
    assert await _keys(client, world, **{"patient:Patient": str(world["p1"])}) == {
        "a",
        "c",
    }
    assert (
        await _keys(client, world, **{"patient:identifier": "urn:pts|P-9"}) == set()
    )  # not a Patient reference
    # a Group or a logical subject is not a Patient, so it counts as missing `patient`
    assert await _keys(client, world, **{"patient:missing": "true"}) == {"d", "e"}
    assert await _keys(client, world, **{"patient:missing": "false"}) == {"a", "b", "c"}


async def test_subject_is_multi_target(client, world):
    assert (
        await _status(client, subject=str(world["p1"])) == 400
    )  # a bare id is ambiguous
    assert await _keys(client, world, subject=f"Patient/{world['p1']}") == {"a", "c"}
    assert await _keys(client, world, **{"subject:Patient": str(world["p2"])}) == {"b"}
    assert await _keys(client, world, subject="Group/430001") == {
        "d"
    }  # the type is part of the match
    assert await _keys(client, world, subject=f"Group/{world['p1']}") == set()
    assert await _keys(client, world, **{"subject:identifier": "urn:pts|P-9"}) == {"e"}
    assert await _keys(client, world, **{"subject:missing": "true"}) == set()


# ── encounter / condition / performer ────────────────────────────────────────


async def test_encounter_and_condition(client, world):
    assert await _keys(client, world, encounter=str(world["enc"])) == {"a"}
    assert await _keys(client, world, encounter=f"Encounter/{world['enc']}") == {"a"}
    assert await _keys(client, world, **{"encounter:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }
    assert await _keys(client, world, condition=str(world["cond"])) == {"a"}
    assert await _keys(client, world, condition=f"Condition/{world['cond']}") == {"a"}
    assert await _keys(client, world, **{"condition:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }
    assert await _keys(client, world, condition="999999") == set()


async def test_performer_is_multi_target(client, world):
    assert (
        await _status(client, performer=str(world["pr"])) == 400
    )  # a bare id is ambiguous
    assert await _keys(client, world, performer=f"Practitioner/{world['pr']}") == {"a"}
    assert await _keys(
        client, world, **{"performer:Practitioner": str(world["pr"])}
    ) == {"a"}
    assert await _keys(
        client, world, performer=f"PractitionerRole/{world['role']}"
    ) == {"b"}
    assert await _keys(client, world, performer="Device/5") == {
        "c"
    }  # a Device is searchable by reference
    assert (
        await _keys(client, world, performer=f"Practitioner/{world['role']}") == set()
    )  # the type is part of the match
    assert await _keys(client, world, **{"performer:missing": "true"}) == {"d", "e"}


# ── chaining ─────────────────────────────────────────────────────────────────


async def test_chains(client, world):
    assert await _keys(client, world, **{"patient.family": "Windsor"}) == {"a", "c"}
    assert await _keys(client, world, **{"subject:Patient.name": "Ben"}) == {"b"}
    assert await _keys(client, world, **{"condition.patient": str(world["p1"])}) == {
        "a"
    }
    assert await _keys(
        client, world, **{"performer:Practitioner.family": "Careful"}
    ) == {"a"}


async def test_bad_chains_are_400(client, world):
    assert await _status(client, **{"patient.nonsense": "x"}) == 400
    assert (
        await _status(client, **{"subject.family": "x"}) == 400
    )  # an untyped multi-target cannot be chained
    assert (
        await _status(client, **{"subject:Group.name": "x"}) == 400
    )  # Group is not searchable here
    assert (
        await _status(client, **{"performer:Device.model": "x"}) == 400
    )  # likewise Device
    assert (
        await _status(client, **{"risk.x": "y"}) == 400
    )  # a token cannot be chained through
    assert await _status(client, **{"probability.x": "y"}) == 400  # nor a number


# ── _sort / _count / _offset / _total ────────────────────────────────────────


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "condition",
        "date",
        "encounter",
        "identifier",
        "method",
        "patient",
        "performer",
        "probability",
        "risk",
        "subject",
        "_id",
    ):
        assert (await _search(client, _sort=key))["total"] == 5, key
    assert await _status(client, _sort="status") == 400


async def test_sort_by_date_and_probability(client, world):
    async def ids(**params):
        return [
            int(e["resource"]["id"]) for e in (await _search(client, **params))["entry"]
        ]

    assert await ids(**{"date:missing": "false", "_sort": "date"}) == [
        world["d"],
        world["a"],
        world["b"],
        world["e"],
    ]
    assert await ids(**{"date:missing": "false", "_sort": "-date"}) == [
        world["e"],
        world["b"],
        world["a"],
        world["d"],
    ]
    assert await ids(**{"probability:missing": "false", "_sort": "probability"}) == [
        world["e"],
        world["a"],
        world["c"],
        world["b"],
    ]


async def test_default_sort_is_newest_first(client, world):
    got = [int(e["resource"]["id"]) for e in (await _search(client))["entry"]]
    assert got == sorted(got, reverse=True)


async def test_paging_and_total(client, world):
    page = await _search(client, _count=2, _sort="_id")
    assert page["total"] == 5 and len(page["entry"]) == 2
    assert any(link["relation"] == "next" for link in page["link"])
    nxt = await _search(client, _count=2, _offset=2, _sort="_id")
    assert not (
        {e["resource"]["id"] for e in page["entry"]}
        & {e["resource"]["id"] for e in nxt["entry"]}
    )
    assert "entry" not in await _search(client, _count=0)
    assert "total" not in await _search(client, _total="none")


async def test_summary_count_and_elements(client, world):
    assert (await _search(client, _summary="count"))["total"] == 5
    resource = (await _search(client, _elements="status", _id=str(world["a"])))[
        "entry"
    ][0]["resource"]
    assert resource["status"] == "final"
    assert "prediction" not in resource and "mitigation" not in resource


# ── _include / _revinclude ───────────────────────────────────────────────────


async def test_include_subject_encounter_and_condition(client, world):
    ids = f"{world['a']},{world['b']},{world['d']},{world['e']}"
    for param in ("patient", "subject"):
        bundle = await _search(client, _id=ids, _include=f"RiskAssessment:{param}")
        assert _of_type(bundle, "Patient", "include") == {
            str(world["p1"]),
            str(world["p2"]),
        }  # a Group adds nothing
    bundle = await _search(client, _id=ids, _include="RiskAssessment:encounter")
    assert _of_type(bundle, "Encounter", "include") == {str(world["enc"])}
    bundle = await _search(client, _id=ids, _include="RiskAssessment:condition")
    assert _of_type(bundle, "Condition", "include") == {str(world["cond"])}


async def test_include_performer_brings_in_every_modeled_type(client, world):
    ids = f"{world['a']},{world['b']},{world['c']}"
    bundle = await _search(client, _id=ids, _include="RiskAssessment:performer")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "PractitionerRole", "include") == {
        str(world["role"])
    }  # a Device adds nothing
    bundle = await _search(
        client, _id=ids, _include="RiskAssessment:performer:Practitioner"
    )
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "PractitionerRole", "include") == set()


async def test_revinclude_assessments_on_the_resources_they_point_at(client, world):
    for param in ("patient", "subject"):
        bundle = await _other(
            client,
            "patients",
            _id=str(world["p1"]),
            _revinclude=f"RiskAssessment:{param}",
        )
        assert _of_type(bundle, "RiskAssessment", "include") == {
            str(world["a"]),
            str(world["c"]),
        }
    bundle = await _other(
        client,
        "conditions",
        _id=str(world["cond"]),
        _revinclude="RiskAssessment:condition",
    )
    assert _of_type(bundle, "RiskAssessment", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "encounters",
        _id=str(world["enc"]),
        _revinclude="RiskAssessment:encounter",
    )
    assert _of_type(bundle, "RiskAssessment", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "practitioners",
        _id=str(world["pr"]),
        _revinclude="RiskAssessment:performer",
    )
    assert _of_type(bundle, "RiskAssessment", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "practitioner-roles",
        _id=str(world["role"]),
        _revinclude="RiskAssessment:performer",
    )
    assert _of_type(bundle, "RiskAssessment", "include") == {str(world["b"])}


async def test_revinclude_is_tenant_scoped(client, other_client):
    from app.auth.dependencies import get_current_user
    from app.main import app
    from tests.conftest import make_test_user
    from tests.integration.risk_assessment.conftest import ASSESSMENT_PERMS

    def as_user(**kw):
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=ASSESSMENT_PERMS, **kw
        )

    as_user()
    mine = await create_patient(client)
    await create_assessment(client, assessment_body(mine))
    as_user(sub="u-other", org_id="org-other")
    try:
        # The other org cannot see the patient, so nothing reaches its assessments.
        bundle = await _other(
            other_client,
            "patients",
            _id=str(mine),
            _revinclude="RiskAssessment:patient",
        )
        assert bundle["total"] == 0 and "entry" not in bundle
        theirs = await create_patient(other_client)
        bundle = await _other(
            other_client,
            "patients",
            _id=str(theirs),
            _revinclude="RiskAssessment:patient",
        )
        assert _of_type(bundle, "RiskAssessment", "include") == set()
    finally:
        as_user()


# ── combination rules / lenient vs strict ────────────────────────────────────


async def test_params_are_anded(client, world):
    assert await _keys(client, world, risk="moderate", probability="12.5") == {"a"}
    assert await _keys(client, world, risk="high", probability="12.5") == set()
    assert await _keys(client, world, patient=str(world["p1"]), probability="gt50") == {
        "c"
    }
    assert await _keys(client, world, method="225338004", date="ge2023") == {"a"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"patient:text": "x"}) == 400
    assert await _status(client, **{"date:exact": "2020"}) == 400
    assert await _status(client, **{"identifier:below": "x"}) == 400
    assert await _status(client, **{"risk:nonsense": "x"}) == 400


async def test_unknown_param_lenient_vs_strict(client, world):
    lenient = await client.get(BASE + "/", params={"nonsense": "1"})
    assert lenient.status_code == 200
    assert any(e["search"]["mode"] == "outcome" for e in lenient.json()["entry"])
    strict = await client.get(
        BASE + "/", params={"nonsense": "1"}, headers={"Prefer": "handling=strict"}
    )
    assert strict.status_code == 400


async def test_query_param_refused(client, world):
    assert await _status(client, _query="x") == 400


# ── POST _search / Bundle shape ──────────────────────────────────────────────


async def test_post_search_form_encoded(client, world):
    resp = await client.post(
        BASE + "/_search", data={"risk": "very high", "patient": str(world["p2"])}
    )
    # `risk=very high` is a token value (a code), not :text, so it finds nothing; the point is the form parses
    assert resp.status_code == 200, resp.text
    resp = await client.post(
        BASE + "/_search", data={"probability": "gt50", "patient": str(world["p1"])}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["c"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, probability="80")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/risk-assessments/{world['b']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "RiskAssessment"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
