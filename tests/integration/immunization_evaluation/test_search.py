"""FHIR R4 search over ImmunizationEvaluation (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/immunizationevaluation.html#search).

One block per search parameter — `status` is a token on a plain code, `dose-status` and
`target-disease` tokens on CodeableConcepts, `identifier` a token on an Identifier, `date` a
dateTime range, `patient` and `immunization-event` single-target references — then
chaining, `_include`/`_revinclude` in both directions, result parameters, combination
rules, lenient vs strict handling and POST _search.
"""

import pytest

from tests.integration.immunization_evaluation.support import (
    API,
    BASE,
    DOSE_STATUS,
    EVALUATION_IDS,
    SCT,
    STATUS_SYSTEM,
    TARGET,
    V2_0203,
    create_evaluation,
    create_immunization,
    create_patient,
    dose_status,
    evaluation_body,
    immunization_body,
)

KEYS = ("a", "b", "c", "d", "e")
ALL = set(KEYS)


def _ids(bundle: dict) -> set[int]:
    return {int(e["resource"]["id"]) for e in bundle.get("entry") or [] if e["search"]["mode"] == "match"}


def _of_type(bundle: dict, rtype: str, mode: str) -> set[str]:
    return {
        e["resource"]["id"]
        for e in bundle.get("entry") or []
        if e["resource"]["resourceType"] == rtype and e["search"]["mode"] == mode
    }


def _disease(code: str, display: str | None = None) -> dict:
    return {"coding": [{"system": SCT, "code": code, **({"display": display} if display else {})}]}


@pytest.fixture
async def world(client):
    """Two patients with an immunization each, plus five evaluations with distinct, searchable
    values. Returns {key: id}."""
    w = {}
    w["p1"] = await create_patient(client, {"active": True, "name": [{"family": "Windsor", "given": ["Anna"]}]})
    w["p2"] = await create_patient(client, {"active": True, "name": [{"family": "Fairfax", "given": ["Ben"]}]})
    w["i1"] = await create_immunization(client, immunization_body(w["p1"], status="completed"))
    w["i2"] = await create_immunization(client, immunization_body(w["p2"], status="not-done"))
    w["a"] = await create_evaluation(
        client,
        evaluation_body(
            w["p1"],
            w["i1"],
            "completed",
            identifier=[
                {
                    "system": EVALUATION_IDS,
                    "value": "IE-A",
                    "type": {"coding": [{"system": V2_0203, "code": "FILL"}], "text": "Evaluation id"},
                }
            ],
            date="2023-01-15T09:30:00Z",
            targetDisease=_disease("6142004", "Influenza"),
            doseStatus=dose_status("valid", display="Valid dose"),
        ),
    )
    w["b"] = await create_evaluation(
        client,
        evaluation_body(
            w["p2"],
            w["i2"],
            "entered-in-error",
            identifier=[{"system": EVALUATION_IDS, "value": "IE-B"}],
            date="2024-02",
            targetDisease=_disease("14189004", "Measles"),
            doseStatus=dose_status("notvalid"),
        ),
    )
    w["c"] = await create_evaluation(
        client,
        evaluation_body(
            w["p1"],
            w["i1"],
            "completed",
            date="2022-06-10T00:00:00Z",
            targetDisease={"text": "Tetanus"},
            doseStatus={"text": "Too early"},
        ),
    )
    w["d"] = await create_evaluation(
        client,
        evaluation_body(
            w["p2"],
            w["i2"],
            "completed",
            date="2019",
            targetDisease=_disease("6142004"),
            doseStatus=dose_status("valid"),
        ),
    )
    w["e"] = await create_evaluation(
        client,
        {
            "status": "completed",
            "patient": {"identifier": {"system": "urn:pts", "value": "P-9"}, "display": "External"},
            "targetDisease": TARGET,
            "immunizationEvent": {"identifier": {"system": "urn:imm", "value": "I-9"}},
            "doseStatus": dose_status("valid"),
            "date": "2024-03-01T00:00:00Z",
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


# ── status ───────────────────────────────────────────────────────────────────


async def test_status(client, world):
    assert await _keys(client, world, status="completed") == {"a", "c", "d", "e"}
    assert await _keys(client, world, status="entered-in-error") == {"b"}  # the real FHIR code
    assert await _keys(client, world, status=f"{STATUS_SYSTEM}|entered-in-error") == {"b"}
    assert await _keys(client, world, status="completed,entered-in-error") == ALL
    assert await _keys(client, world, status="http://wrong|completed") == set()
    assert await _keys(client, world, status="|completed") == set()  # a code with no system is not this one
    assert await _keys(client, world, status="nonsense") == set()
    assert await _keys(client, world, **{"status:not": "completed"}) == {"b"}
    assert await _status(client, **{"status:text": "completed"}) == 400  # a plain code has no :text


# ── date ─────────────────────────────────────────────────────────────────────


async def test_date(client, world):
    assert await _keys(client, world, date="2023-01-15") == {"a"}
    assert await _keys(client, world, date="2023") == {"a"}
    assert await _keys(client, world, date="2024") == {"b", "e"}  # 2024-02 and 2024-03-01 lie inside 2024
    assert await _keys(client, world, date="ge2024-01-01") == {"b", "e"}
    assert await _keys(client, world, date="lt2023-01-01") == {"c", "d"}
    assert await _keys(client, world, date="lt2020-01-01,ge2024-03-01") == {"d", "e"}
    assert await _keys(client, world, date="sa2023-02-01") == {"b", "e"}
    assert await _keys(client, world, date="eb2020-01-01") == {"d"}
    assert await _keys(client, world, **{"date:missing": "true"}) == set()
    assert await _keys(client, world, **{"date:missing": "false"}) == ALL


# ── identifier ───────────────────────────────────────────────────────────────


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="IE-A") == {"a"}
    assert await _keys(client, world, identifier=f"{EVALUATION_IDS}|IE-B") == {"b"}
    assert await _keys(client, world, identifier="IE-A,IE-B") == {"a", "b"}
    assert await _keys(client, world, identifier="urn:wrong|IE-A") == set()
    assert await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|FILL|IE-A"}) == {"a"}
    assert await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|FILL|IE-B"}) == set()
    assert await _keys(client, world, **{"identifier:text": "evaluation"}) == {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {"c", "d", "e"}


# ── dose-status / target-disease ─────────────────────────────────────────────


async def test_dose_status(client, world):
    assert await _keys(client, world, **{"dose-status": "valid"}) == {"a", "d", "e"}
    assert await _keys(client, world, **{"dose-status": f"{DOSE_STATUS}|notvalid"}) == {"b"}
    assert await _keys(client, world, **{"dose-status": f"{DOSE_STATUS}|"}) == {"a", "b", "d", "e"}
    assert await _keys(client, world, **{"dose-status": "valid,notvalid"}) == {"a", "b", "d", "e"}
    assert await _keys(client, world, **{"dose-status": "http://wrong|valid"}) == set()
    assert await _keys(client, world, **{"dose-status:text": "too early"}) == {"c"}  # a text-only concept is found
    assert await _keys(client, world, **{"dose-status:text": "valid dose"}) == {"a"}  # Coding.display
    assert await _keys(client, world, **{"dose-status:not": "valid"}) == {"b", "c"}
    assert await _keys(client, world, **{"dose-status:missing": "true"}) == set()


async def test_target_disease(client, world):
    assert await _keys(client, world, **{"target-disease": "6142004"}) == {"a", "d", "e"}
    assert await _keys(client, world, **{"target-disease": f"{SCT}|14189004"}) == {"b"}
    assert await _keys(client, world, **{"target-disease": "6142004,14189004"}) == {"a", "b", "d", "e"}
    assert await _keys(client, world, **{"target-disease:text": "measles"}) == {"b"}
    assert await _keys(client, world, **{"target-disease:text": "tetanus"}) == {"c"}
    assert await _keys(client, world, **{"target-disease:missing": "true"}) == set()


# ── patient / immunization-event ─────────────────────────────────────────────


async def test_patient(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {"a", "c"}  # one target: a bare id works
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"b", "d"}
    assert await _keys(client, world, patient=f"{world['p1']},{world['p2']}") == {"a", "b", "c", "d"}
    assert await _keys(client, world, patient="999999") == set()
    assert await _keys(client, world, **{"patient:Patient": str(world["p1"])}) == {"a", "c"}
    assert await _keys(client, world, **{"patient:identifier": "urn:pts|P-9"}) == {"e"}
    assert await _keys(client, world, **{"patient:missing": "false"}) == ALL


async def test_immunization_event(client, world):
    assert await _keys(client, world, **{"immunization-event": str(world["i1"])}) == {"a", "c"}
    assert await _keys(client, world, **{"immunization-event": f"Immunization/{world['i2']}"}) == {"b", "d"}
    assert await _keys(client, world, **{"immunization-event:identifier": "urn:imm|I-9"}) == {"e"}
    assert await _keys(client, world, **{"immunization-event": "999999"}) == set()
    assert await _keys(client, world, **{"immunization-event:missing": "false"}) == ALL


# ── chaining ─────────────────────────────────────────────────────────────────


async def test_chains(client, world):
    assert await _keys(client, world, **{"patient.family": "Windsor"}) == {"a", "c"}
    assert await _keys(client, world, **{"patient.name": "Ben"}) == {"b", "d"}
    assert await _keys(client, world, **{"immunization-event.status": "completed"}) == {"a", "c"}
    assert await _keys(client, world, **{"immunization-event.status": "not-done"}) == {"b", "d"}
    assert await _keys(client, world, **{"immunization-event.patient": str(world["p1"])}) == {"a", "c"}


async def test_bad_chains_are_400(client, world):
    assert await _status(client, **{"patient.nonsense": "x"}) == 400
    assert await _status(client, **{"immunization-event.nonsense": "x"}) == 400
    assert await _status(client, **{"dose-status.x": "y"}) == 400  # a token cannot be chained through
    assert await _status(client, **{"status.x": "y"}) == 400


# ── _sort / _count / _offset / _total ────────────────────────────────────────


async def test_sort_by_every_declared_param(client, world):
    for key in ("date", "dose-status", "identifier", "immunization-event", "patient", "status", "target-disease",
                "_id"):
        assert (await _search(client, _sort=key))["total"] == 5, key
    assert await _status(client, _sort="series") == 400


async def test_sort_by_date(client, world):
    async def ids(**params):
        return [int(e["resource"]["id"]) for e in (await _search(client, **params))["entry"]]

    assert await ids(_sort="date") == [world["d"], world["c"], world["a"], world["b"], world["e"]]
    assert await ids(_sort="-date") == [world["e"], world["b"], world["a"], world["c"], world["d"]]


async def test_default_sort_is_newest_first(client, world):
    got = [int(e["resource"]["id"]) for e in (await _search(client))["entry"]]
    assert got == sorted(got, reverse=True)


async def test_paging_and_total(client, world):
    page = await _search(client, _count=2, _sort="_id")
    assert page["total"] == 5 and len(page["entry"]) == 2
    assert any(link["relation"] == "next" for link in page["link"])
    nxt = await _search(client, _count=2, _offset=2, _sort="_id")
    assert not ({e["resource"]["id"] for e in page["entry"]} & {e["resource"]["id"] for e in nxt["entry"]})
    assert "entry" not in await _search(client, _count=0)
    assert "total" not in await _search(client, _total="none")


async def test_summary_count_and_elements(client, world):
    assert (await _search(client, _summary="count"))["total"] == 5
    resource = (await _search(client, _elements="status", _id=str(world["a"])))["entry"][0]["resource"]
    assert resource["status"] == "completed"
    assert "date" not in resource and "identifier" not in resource


# ── _include / _revinclude ───────────────────────────────────────────────────


async def test_include_patient_and_immunization_event(client, world):
    ids = f"{world['a']},{world['b']},{world['e']}"
    bundle = await _search(client, _id=ids, _include="ImmunizationEvaluation:patient")
    assert _of_type(bundle, "Patient", "include") == {str(world["p1"]), str(world["p2"])}  # a logical patient adds nothing
    bundle = await _search(client, _id=ids, _include="ImmunizationEvaluation:immunization-event")
    assert _of_type(bundle, "Immunization", "include") == {str(world["i1"]), str(world["i2"])}


async def test_revinclude_evaluations_on_the_resources_they_point_at(client, world):
    bundle = await _other(client, "patients", _id=str(world["p1"]), _revinclude="ImmunizationEvaluation:patient")
    assert _of_type(bundle, "ImmunizationEvaluation", "include") == {str(world["a"]), str(world["c"])}
    bundle = await _other(
        client, "immunizations", _id=str(world["i2"]), _revinclude="ImmunizationEvaluation:immunization-event"
    )
    assert _of_type(bundle, "ImmunizationEvaluation", "include") == {str(world["b"]), str(world["d"])}


async def test_revinclude_what_points_at_an_evaluation(client, world):
    """An ImmunizationRecommendation's `supportingImmunization` can name an evaluation."""
    body = {
        "patient": {"reference": f"Patient/{world['p1']}"},
        "date": "2023-02-01",
        "recommendation": [
            {
                "vaccineCode": [{"text": "Flu"}],
                "forecastStatus": {"text": "Due"},
                "supportingImmunization": [{"reference": f"ImmunizationEvaluation/{world['a']}"}],
            }
        ],
    }
    created = await client.post(f"{API}/immunization-recommendations/", json=body)
    assert created.status_code == 201, created.text
    recommendation = created.json()["id"]
    bundle = await _search(client, _id=str(world["a"]), _revinclude="ImmunizationRecommendation:support")
    assert _of_type(bundle, "ImmunizationRecommendation", "include") == {recommendation}
    # ...and the other way round: _include the evaluation a recommendation points at.
    bundle = await _other(
        client, "immunization-recommendations", _id=recommendation, _include="ImmunizationRecommendation:support"
    )
    assert _of_type(bundle, "ImmunizationEvaluation", "include") == {str(world["a"])}
    bundle = await _other(
        client, "immunization-recommendations", **{"support:ImmunizationEvaluation.status": "completed"}
    )
    assert _ids(bundle) == {int(recommendation)}


async def test_revinclude_is_tenant_scoped(client, other_client):
    from app.auth.dependencies import get_current_user
    from app.main import app
    from tests.conftest import make_test_user
    from tests.integration.immunization_evaluation.conftest import EVALUATION_PERMS

    def as_user(**kw):
        app.dependency_overrides[get_current_user] = make_test_user(permissions=EVALUATION_PERMS, **kw)

    as_user()
    mine = await create_patient(client)
    await create_evaluation(client, evaluation_body(mine))
    as_user(sub="u-other", org_id="org-other")
    try:
        # The other org cannot see the patient, so nothing reaches its evaluations.
        bundle = await _other(other_client, "patients", _id=str(mine), _revinclude="ImmunizationEvaluation:patient")
        assert bundle["total"] == 0 and "entry" not in bundle
        theirs = await create_patient(other_client)
        bundle = await _other(other_client, "patients", _id=str(theirs), _revinclude="ImmunizationEvaluation:patient")
        assert _of_type(bundle, "ImmunizationEvaluation", "include") == set()
    finally:
        as_user()


# ── combination rules / lenient vs strict ────────────────────────────────────


async def test_params_are_anded(client, world):
    assert await _keys(client, world, status="completed", **{"dose-status": "valid"}) == {"a", "d", "e"}
    assert await _keys(client, world, status="entered-in-error", **{"dose-status": "valid"}) == set()
    assert await _keys(client, world, patient=str(world["p1"]), **{"target-disease": "6142004"}) == {"a"}
    assert await _keys(client, world, **{"dose-status": "valid"}, date="ge2024") == {"e"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"status:above": "x"}) == 400
    assert await _status(client, **{"patient:text": "x"}) == 400
    assert await _status(client, **{"date:exact": "2020"}) == 400
    assert await _status(client, **{"identifier:below": "x"}) == 400


async def test_unknown_param_lenient_vs_strict(client, world):
    lenient = await client.get(BASE + "/", params={"nonsense": "1"})
    assert lenient.status_code == 200
    assert any(e["search"]["mode"] == "outcome" for e in lenient.json()["entry"])
    strict = await client.get(BASE + "/", params={"nonsense": "1"}, headers={"Prefer": "handling=strict"})
    assert strict.status_code == 400


async def test_query_param_refused(client, world):
    assert await _status(client, _query="x") == 400


# ── POST _search / Bundle shape ──────────────────────────────────────────────


async def test_post_search_form_encoded(client, world):
    resp = await client.post(BASE + "/_search", data={"status": "entered-in-error", "patient": str(world["p2"])})
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, status="entered-in-error")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/immunization-evaluations/{world['b']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "ImmunizationEvaluation"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
