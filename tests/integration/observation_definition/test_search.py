"""FHIR R4 search over ObservationDefinition (https://www.hl7.org/fhir/R4/search.html).

R4 defines **no** resource-specific search parameter for ObservationDefinition (its resource page
has no Search Parameters section), so only the common `_id` and `_lastUpdated` exist, plus the
result parameters (`_sort`, `_count`, `_offset`, `_total`, `_summary`, `_elements`) and POST
_search. Every other name is an unknown parameter: ignored and reported by default, a 400 under
`Prefer: handling=strict`.
"""

import pytest

from tests.integration.observation_definition.support import (
    BASE,
    create_observation_definition,
    observation_definition_body,
)


def _ids(bundle: dict) -> set[int]:
    return {
        int(e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == "match"
    }


@pytest.fixture
async def world(client) -> dict:
    """Three observation definitions."""
    ids = {}
    for key, code, name in (
        ("a", "718-7", "Hemoglobin"),
        ("b", "4548-4", "HbA1c"),
        ("c", "2160-0", None),
    ):
        extra = {"preferredReportName": name} if name else {}
        ids[key] = await create_observation_definition(
            client, observation_definition_body(code, **extra)
        )
    return ids


async def _search(client, **params) -> dict:
    resp = await client.get(BASE + "/", params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _status(client, **params) -> int:
    return (await client.get(BASE + "/", params=params)).status_code


async def test_id(client, world):
    assert _ids(await _search(client, _id=str(world["a"]))) == {world["a"]}
    assert _ids(await _search(client, _id=f"{world['a']},{world['c']}")) == {
        world["a"],
        world["c"],
    }
    assert _ids(await _search(client, _id="999999")) == set()
    assert _ids(await _search(client, **{"_id:not": str(world["a"])})) == {
        world["b"],
        world["c"],
    }


async def test_last_updated(client, world):
    assert _ids(await _search(client, _lastUpdated="ge2000-01-01")) == set(
        world.values()
    )
    assert _ids(await _search(client, _lastUpdated="lt2000-01-01")) == set()


async def test_sort_by_id_and_last_updated(client, world):
    for key in ("_id", "-_id", "_lastUpdated", "-_lastUpdated"):
        assert (await _search(client, _sort=key))["total"] == 3, key
    got = [
        int(e["resource"]["id"]) for e in (await _search(client, _sort="_id"))["entry"]
    ]
    assert got == sorted(world.values())


async def test_default_sort_is_newest_first(client, world):
    got = [int(e["resource"]["id"]) for e in (await _search(client))["entry"]]
    assert got == sorted(got, reverse=True)


async def test_paging_and_total(client, world):
    page = await _search(client, _count=2, _sort="_id")
    assert page["total"] == 3 and len(page["entry"]) == 2
    assert any(link["relation"] == "next" for link in page["link"])
    nxt = await _search(client, _count=2, _offset=2, _sort="_id")
    assert len(nxt["entry"]) == 1
    assert "entry" not in await _search(client, _count=0)
    assert "total" not in await _search(client, _total="none")


async def test_summary_count_and_elements(client, world):
    assert (await _search(client, _summary="count"))["total"] == 3
    resource = (await _search(client, _elements="code", _id=str(world["a"])))["entry"][
        0
    ]["resource"]
    assert resource["code"]["coding"][0]["code"] == "718-7"
    assert "preferredReportName" not in resource


async def test_summary_true_keeps_only_the_summary_elements(client, world):
    resource = (await _search(client, _summary="true", _id=str(world["a"])))["entry"][
        0
    ]["resource"]
    assert "code" in resource and "preferredReportName" not in resource


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"_lastUpdated:exact": "2020"}) == 400


async def test_unknown_param_lenient_vs_strict(client, world):
    lenient = await client.get(BASE + "/", params={"nonsense": "1"})
    assert lenient.status_code == 200
    assert any(e["search"]["mode"] == "outcome" for e in lenient.json()["entry"])
    strict = await client.get(
        BASE + "/", params={"nonsense": "1"}, headers={"Prefer": "handling=strict"}
    )
    assert strict.status_code == 400


async def test_no_element_has_a_search_parameter(client, world):
    """R4 defines none, so even the elements a client might expect to filter on are unknown."""
    for name in (
        "code",
        "category",
        "identifier",
        "method",
        "permitted-data-type",
        "status",
        "name",
        "url",
    ):
        strict = await client.get(
            BASE + "/", params={name: "x"}, headers={"Prefer": "handling=strict"}
        )
        assert strict.status_code == 400, name


async def test_query_param_refused(client, world):
    assert await _status(client, _query="x") == 400


async def test_post_search_form_encoded(client, world):
    resp = await client.post(BASE + "/_search", data={"_id": str(world["b"])})
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, _id=str(world["a"]))
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/observation-definitions/{world['a']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "ObservationDefinition"
    assert entry["resource"]["preferredReportName"] == "Hemoglobin"


async def test_empty_result(client, world):
    bundle = await _search(client, _id="999999")
    assert bundle["total"] == 0 and "entry" not in bundle
