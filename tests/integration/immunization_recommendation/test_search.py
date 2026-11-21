"""FHIR R4 search over ImmunizationRecommendation (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/immunizationrecommendation.html#search).

One block per search parameter — `status`, `target-disease` and `vaccine-type` are tokens on
CodeableConcepts inside the `recommendation` backbone, `identifier` a token on an Identifier,
`date` a dateTime range, `patient` a single-target reference and `support` / `information`
the multi-target ones — then chaining, `_include`/`_revinclude` in both directions, result
parameters, combination rules, lenient vs strict handling and POST _search.
"""

import pytest

from tests.integration.immunization_recommendation.support import (
    API,
    BASE,
    CVX,
    RECOMMENDATION_IDS,
    SCT,
    STATUS,
    V2_0203,
    condition_body,
    create_condition,
    create_evaluation,
    create_immunization,
    create_patient,
    create_recommendation,
    entry,
    evaluation_body,
    immunization_body,
    recommendation_body,
    status,
    vaccine,
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
    """Two patients, an immunization and a condition, plus five recommendations with
    distinct, searchable values. Returns {key: id}."""
    w = {}
    w["p1"] = await create_patient(
        client, {"active": True, "name": [{"family": "Windsor", "given": ["Anna"]}]}
    )
    w["p2"] = await create_patient(
        client, {"active": True, "name": [{"family": "Fairfax", "given": ["Ben"]}]}
    )
    w["imm"] = await create_immunization(
        client, immunization_body(w["p1"], vaccineCode=vaccine("140"))
    )
    w["cond"] = await create_condition(client, condition_body(w["p1"]))
    w["ev"] = await create_evaluation(client, evaluation_body(w["p1"], w["imm"]))
    w["a"] = await create_recommendation(
        client,
        recommendation_body(
            w["p1"],
            identifier=[
                {
                    "system": RECOMMENDATION_IDS,
                    "value": "IR-A",
                    "type": {
                        "coding": [{"system": V2_0203, "code": "FILL"}],
                        "text": "Recommendation id",
                    },
                }
            ],
            date="2023-01-15T09:30:00Z",
            recommendation=[
                entry(
                    vaccineCode=[vaccine("140", "Influenza vaccine")],
                    targetDisease={
                        "coding": [
                            {"system": SCT, "code": "6142004", "display": "Influenza"}
                        ]
                    },
                    forecastStatus=status("due"),
                    supportingImmunization=[
                        {"reference": f"Immunization/{w['imm']}"},
                        {"reference": f"ImmunizationEvaluation/{w['ev']}"},
                    ],
                    supportingPatientInformation=[
                        {"reference": f"Condition/{w['cond']}"},
                        {"reference": "Observation/160001"},
                    ],
                ),
                entry(
                    vaccineCode=[vaccine("03", "MMR vaccine")],
                    targetDisease={
                        "coding": [
                            {"system": SCT, "code": "14189004", "display": "Measles"}
                        ]
                    },
                    forecastStatus=status("contraindicated"),
                ),
            ],
        ),
    )
    w["b"] = await create_recommendation(
        client,
        recommendation_body(
            w["p2"],
            identifier=[{"system": RECOMMENDATION_IDS, "value": "IR-B"}],
            date="2024-02",
            recommendation=[
                {
                    "vaccineCode": [{"text": "Tetanus shot"}],
                    "forecastStatus": status("overdue"),
                    "supportingPatientInformation": [
                        {"reference": "Observation/160002"}
                    ],
                }
            ],
        ),
    )
    w["c"] = await create_recommendation(
        client,
        recommendation_body(
            w["p1"],
            date="2022-06-10T00:00:00Z",
            recommendation=[
                {
                    "targetDisease": {"coding": [{"system": SCT, "code": "6142004"}]},
                    "forecastStatus": status("due"),
                    "supportingImmunization": [
                        {"identifier": {"system": "urn:imm", "value": "I-9"}}
                    ],
                }
            ],
        ),
    )
    w["d"] = await create_recommendation(
        client,
        recommendation_body(
            w["p2"],
            date="2019",
            recommendation=[
                {
                    "vaccineCode": [vaccine("21", "Varicella")],
                    "forecastStatus": {"text": "Complete"},
                }
            ],
        ),
    )
    w["e"] = await create_recommendation(
        client,
        {
            "patient": {
                "identifier": {"system": "urn:pts", "value": "P-9"},
                "display": "External",
            },
            "date": "2024-03-01T00:00:00Z",
            "recommendation": [
                entry(vaccineCode=[vaccine("140")], forecastStatus=status("due"))
            ],
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


# ── date ─────────────────────────────────────────────────────────────────────


async def test_date(client, world):
    assert await _keys(client, world, date="2023-01-15") == {"a"}
    assert await _keys(client, world, date="2023") == {"a"}
    assert await _keys(client, world, date="2024") == {
        "b",
        "e",
    }  # 2024-02 and 2024-03-01 lie inside 2024
    assert await _keys(client, world, date="ge2024-01-01") == {"b", "e"}
    assert await _keys(client, world, date="lt2023-01-01") == {"c", "d"}
    assert await _keys(client, world, date="lt2020-01-01,ge2024-03-01") == {"d", "e"}
    assert await _keys(client, world, date="sa2023-02-01") == {"b", "e"}
    assert await _keys(client, world, date="eb2020-01-01") == {"d"}
    assert await _keys(client, world, **{"date:missing": "true"}) == set()
    assert await _keys(client, world, **{"date:missing": "false"}) == ALL


# ── identifier ───────────────────────────────────────────────────────────────


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="IR-A") == {"a"}
    assert await _keys(client, world, identifier=f"{RECOMMENDATION_IDS}|IR-B") == {"b"}
    assert await _keys(client, world, identifier="IR-A,IR-B") == {"a", "b"}
    assert await _keys(client, world, identifier="urn:wrong|IR-A") == set()
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|FILL|IR-A"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|FILL|IR-B"})
        == set()
    )
    assert await _keys(client, world, **{"identifier:text": "recommendation"}) == {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


# ── status / target-disease / vaccine-type (tokens inside `recommendation`) ──


async def test_status(client, world):
    assert await _keys(client, world, status="due") == {"a", "c", "e"}
    assert await _keys(client, world, status=f"{STATUS}|contraindicated") == {
        "a"
    }  # any recommendation entry matches
    assert await _keys(client, world, status="overdue,contraindicated") == {"a", "b"}
    assert await _keys(client, world, status="http://wrong|due") == set()
    assert await _keys(client, world, **{"status:text": "complete"}) == {
        "d"
    }  # a text-only concept is found
    assert await _keys(client, world, **{"status:not": "due"}) == {"b", "d"}
    assert await _keys(client, world, **{"status:missing": "false"}) == ALL


async def test_target_disease(client, world):
    assert await _keys(client, world, **{"target-disease": "6142004"}) == {"a", "c"}
    assert await _keys(client, world, **{"target-disease": f"{SCT}|14189004"}) == {"a"}
    assert await _keys(client, world, **{"target-disease": "6142004,14189004"}) == {
        "a",
        "c",
    }
    assert await _keys(client, world, **{"target-disease:text": "measles"}) == {
        "a"
    }  # Coding.display
    assert await _keys(client, world, **{"target-disease:missing": "true"}) == {
        "b",
        "d",
        "e",
    }


async def test_vaccine_type(client, world):
    assert await _keys(client, world, **{"vaccine-type": "140"}) == {"a", "e"}
    assert await _keys(client, world, **{"vaccine-type": f"{CVX}|03"}) == {"a"}
    assert await _keys(client, world, **{"vaccine-type": f"{CVX}|"}) == {"a", "d", "e"}
    assert await _keys(client, world, **{"vaccine-type": "140,21"}) == {"a", "d", "e"}
    assert await _keys(client, world, **{"vaccine-type": "http://wrong|140"}) == set()
    assert await _keys(client, world, **{"vaccine-type:text": "tetanus"}) == {"b"}
    assert await _keys(client, world, **{"vaccine-type:text": "influenza"}) == {"a"}
    assert await _keys(client, world, **{"vaccine-type:missing": "true"}) == {"c"}


# ── patient ──────────────────────────────────────────────────────────────────


async def test_patient(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {
        "a",
        "c",
    }  # one target: a bare id works
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"b", "d"}
    assert await _keys(client, world, patient=f"{world['p1']},{world['p2']}") == {
        "a",
        "b",
        "c",
        "d",
    }
    assert await _keys(client, world, patient="999999") == set()
    assert await _keys(client, world, **{"patient:Patient": str(world["p1"])}) == {
        "a",
        "c",
    }
    assert await _keys(client, world, **{"patient:identifier": "urn:pts|P-9"}) == {"e"}
    assert await _keys(client, world, **{"patient:missing": "false"}) == ALL


# ── support / information ────────────────────────────────────────────────────


async def test_support_is_multi_target(client, world):
    assert (
        await _status(client, support=str(world["imm"])) == 400
    )  # a bare id is ambiguous
    assert await _keys(client, world, support=f"Immunization/{world['imm']}") == {"a"}
    assert await _keys(
        client, world, **{"support:Immunization": str(world["imm"])}
    ) == {"a"}
    assert await _keys(
        client, world, support=f"ImmunizationEvaluation/{world['ev']}"
    ) == {"a"}
    assert (
        await _keys(client, world, support=f"Immunization/{world['ev']}") == set()
    )  # the type is part of the match
    assert await _keys(client, world, **{"support:identifier": "urn:imm|I-9"}) == {"c"}
    assert await _keys(client, world, **{"support:missing": "true"}) == {"b", "d", "e"}


async def test_information_is_reference_any(client, world):
    assert (
        await _status(client, information=str(world["cond"])) == 400
    )  # a bare id is ambiguous
    assert await _keys(client, world, information=f"Condition/{world['cond']}") == {"a"}
    assert await _keys(
        client, world, **{"information:Condition": str(world["cond"])}
    ) == {"a"}
    assert await _keys(client, world, information="Observation/160001") == {"a"}
    assert await _keys(client, world, information="Observation/160002") == {"b"}
    assert await _keys(
        client, world, **{"information:Observation": "160001,160002"}
    ) == {"a", "b"}
    assert await _keys(client, world, **{"information:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


# ── chaining ─────────────────────────────────────────────────────────────────


async def test_chains(client, world):
    assert await _keys(client, world, **{"patient.family": "Windsor"}) == {"a", "c"}
    assert await _keys(client, world, **{"patient.name": "Ben"}) == {"b", "d"}
    assert await _keys(
        client, world, **{"support:Immunization.status": "completed"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"support:Immunization.vaccine-code": "140"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"support:Immunization.status": "not-done"})
        == set()
    )
    assert await _keys(
        client, world, **{"support:ImmunizationEvaluation.status": "completed"}
    ) == {"a"}
    assert (
        await _keys(
            client,
            world,
            **{"support:ImmunizationEvaluation.status": "entered-in-error"},
        )
        == set()
    )
    assert await _keys(
        client, world, **{"support:ImmunizationEvaluation.patient": str(world["p1"])}
    ) == {"a"}
    assert await _keys(
        client, world, **{"information:Condition.patient": str(world["p1"])}
    ) == {"a"}


async def test_bad_chains_are_400(client, world):
    assert await _status(client, **{"patient.nonsense": "x"}) == 400
    assert (
        await _status(client, **{"support.status": "x"}) == 400
    )  # an untyped multi-target cannot be chained
    assert (
        await _status(client, **{"information:MedicationRequest.status": "x"}) == 400
    )  # likewise
    assert (
        await _status(client, **{"status.x": "y"}) == 400
    )  # a token cannot be chained through


# ── _sort / _count / _offset / _total ────────────────────────────────────────


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "date",
        "identifier",
        "information",
        "patient",
        "status",
        "support",
        "target-disease",
        "vaccine-type",
        "_id",
    ):
        assert (await _search(client, _sort=key))["total"] == 5, key
    assert await _status(client, _sort="series") == 400


async def test_sort_by_date(client, world):
    async def ids(**params):
        return [
            int(e["resource"]["id"]) for e in (await _search(client, **params))["entry"]
        ]

    assert await ids(_sort="date") == [
        world["d"],
        world["c"],
        world["a"],
        world["b"],
        world["e"],
    ]
    assert await ids(_sort="-date") == [
        world["e"],
        world["b"],
        world["a"],
        world["c"],
        world["d"],
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
    resource = (await _search(client, _elements="date", _id=str(world["a"])))["entry"][
        0
    ]["resource"]
    assert resource["date"] == "2023-01-15T09:30:00Z"
    assert "authority" not in resource and "identifier" not in resource


# ── _include / _revinclude ───────────────────────────────────────────────────


async def test_include_patient(client, world):
    ids = f"{world['a']},{world['b']},{world['e']}"
    bundle = await _search(
        client, _id=ids, _include="ImmunizationRecommendation:patient"
    )
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }  # a logical patient adds nothing


async def test_include_support_and_information(client, world):
    ids = f"{world['a']},{world['c']}"
    bundle = await _search(
        client, _id=ids, _include="ImmunizationRecommendation:support"
    )
    assert _of_type(bundle, "Immunization", "include") == {
        str(world["imm"])
    }  # a logical one adds nothing
    assert _of_type(bundle, "ImmunizationEvaluation", "include") == {str(world["ev"])}
    bundle = await _search(
        client, _id=ids, _include="ImmunizationRecommendation:information"
    )
    assert _of_type(bundle, "Condition", "include") == {
        str(world["cond"])
    }  # an Observation adds nothing
    bundle = await _search(
        client, _id=ids, _include="ImmunizationRecommendation:information:Patient"
    )
    assert _of_type(bundle, "Condition", "include") == set()


async def test_revinclude_recommendations_on_the_resources_they_point_at(client, world):
    bundle = await _other(
        client,
        "patients",
        _id=str(world["p1"]),
        _revinclude="ImmunizationRecommendation:patient",
    )
    assert _of_type(bundle, "ImmunizationRecommendation", "include") == {
        str(world["a"]),
        str(world["c"]),
    }
    bundle = await _other(
        client,
        "patients",
        _id=str(world["p2"]),
        _revinclude="ImmunizationRecommendation:patient",
    )
    assert _of_type(bundle, "ImmunizationRecommendation", "include") == {
        str(world["b"]),
        str(world["d"]),
    }
    bundle = await _other(
        client,
        "immunizations",
        _id=str(world["imm"]),
        _revinclude="ImmunizationRecommendation:support",
    )
    assert _of_type(bundle, "ImmunizationRecommendation", "include") == {
        str(world["a"])
    }
    bundle = await _other(
        client,
        "immunization-evaluations",
        _id=str(world["ev"]),
        _revinclude="ImmunizationRecommendation:support",
    )
    assert _of_type(bundle, "ImmunizationRecommendation", "include") == {
        str(world["a"])
    }


async def test_revinclude_is_tenant_scoped(client, other_client):
    from app.auth.dependencies import get_current_user
    from app.main import app
    from tests.conftest import make_test_user
    from tests.integration.immunization_recommendation.conftest import (
        RECOMMENDATION_PERMS,
    )

    def as_user(**kw):
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=RECOMMENDATION_PERMS, **kw
        )

    as_user()
    mine = await create_patient(client)
    await create_recommendation(client, recommendation_body(mine))
    as_user(sub="u-other", org_id="org-other")
    try:
        # The other org cannot see the patient, so nothing reaches its recommendations.
        bundle = await _other(
            other_client,
            "patients",
            _id=str(mine),
            _revinclude="ImmunizationRecommendation:patient",
        )
        assert bundle["total"] == 0 and "entry" not in bundle
        theirs = await create_patient(other_client)
        bundle = await _other(
            other_client,
            "patients",
            _id=str(theirs),
            _revinclude="ImmunizationRecommendation:patient",
        )
        assert _of_type(bundle, "ImmunizationRecommendation", "include") == set()
    finally:
        as_user()


# ── combination rules / lenient vs strict ────────────────────────────────────


async def test_params_are_anded(client, world):
    assert await _keys(client, world, status="due", **{"vaccine-type": "140"}) == {
        "a",
        "e",
    }
    assert (
        await _keys(client, world, status="overdue", **{"vaccine-type": "140"}) == set()
    )
    assert await _keys(client, world, patient=str(world["p1"]), status="due") == {
        "a",
        "c",
    }
    assert await _keys(client, world, **{"vaccine-type": "140"}, date="ge2024") == {"e"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"status:nonsense": "x"}) == 400
    assert await _status(client, **{"patient:text": "x"}) == 400
    assert await _status(client, **{"date:exact": "2020"}) == 400
    assert await _status(client, **{"identifier:below": "x"}) == 400


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
        BASE + "/_search", data={"status": "overdue", "patient": str(world["p2"])}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, status="overdue")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry_ = bundle["entry"][0]
    assert entry_["fullUrl"].endswith(f"/immunization-recommendations/{world['b']}")
    assert entry_["search"]["mode"] == "match"
    assert entry_["resource"]["resourceType"] == "ImmunizationRecommendation"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
