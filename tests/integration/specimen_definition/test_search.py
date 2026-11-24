"""FHIR R4 search over SpecimenDefinition (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/specimendefinition.html#search).

R4 defines three parameters, all tokens: `identifier` (a single Identifier), `type`
(`typeCollected`) and `container` (`typeTested.container.type` of every typeTested entry). Plus
`_id` / `_lastUpdated`, the result parameters and POST _search. Every other name is unknown.
"""

import pytest

from tests.integration.specimen_definition.support import (
    BASE,
    SPECIMEN_DEFINITION_IDS,
    V2_0203,
    V2_0487,
    concept,
    create_specimen_definition,
    specimen_definition_body,
    type_tested,
)

KEYS = ("a", "b", "c")
ALL = set(KEYS)


def _ids(bundle: dict) -> set[int]:
    return {
        int(e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == "match"
    }


@pytest.fixture
async def world(client) -> dict:
    """Three specimen definitions.

    a - blood; identifier SD-A with a coded type and text; two typeTested entries whose container
        types are SPECIMEN and TUBE.
    b - urine; identifier urn:other|SD-B; one typeTested entry with container type CUP and one
        with no container.
    c - nothing indexed (an empty document).
    """
    a = specimen_definition_body(
        typeCollected={
            "coding": [{"system": V2_0487, "code": "BLD", "display": "Whole blood"}],
            "text": "Blood",
        },
        identifier={
            "system": SPECIMEN_DEFINITION_IDS,
            "value": "SD-A",
            "type": {
                "coding": [
                    {"system": V2_0203, "code": "ACSN", "display": "Accession ID"}
                ],
                "text": "Form number",
            },
        },
        typeTested=[
            type_tested("SPECIMEN"),
            {
                "preference": "preferred",
                "container": {"type": concept("TUBE", "Tube")},
            },
        ],
    )
    b = {
        "typeCollected": concept("URN", "Urine"),
        "identifier": {"system": "urn:other", "value": "SD-B"},
        "typeTested": [type_tested("CUP"), type_tested()],
    }
    ids = {}
    for key, body in (("a", a), ("b", b), ("c", {})):
        ids[key] = await create_specimen_definition(client, body)
    return ids


async def _search(client, **params) -> dict:
    resp = await client.get(BASE + "/", params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _keys(client, world, **params) -> set[str]:
    by_id = {world[k]: k for k in KEYS}
    return {by_id[i] for i in _ids(await _search(client, **params))}


async def _status(client, **params) -> int:
    return (await client.get(BASE + "/", params=params)).status_code


# -- _id / _lastUpdated ---------------------------------------------------------------------


async def test_id(client, world):
    assert await _keys(client, world, _id=str(world["a"])) == {"a"}
    assert await _keys(client, world, _id=f"{world['a']},{world['c']}") == {"a", "c"}
    assert await _keys(client, world, _id="999999") == set()
    assert await _keys(client, world, **{"_id:not": str(world["a"])}) == {"b", "c"}


async def test_last_updated(client, world):
    assert await _keys(client, world, _lastUpdated="ge2000-01-01") == ALL
    assert await _keys(client, world, _lastUpdated="lt2000-01-01") == set()


# -- type (typeCollected) -------------------------------------------------------------------


async def test_type(client, world):
    assert await _keys(client, world, type="BLD") == {"a"}
    assert await _keys(client, world, type=f"{V2_0487}|URN") == {"b"}
    assert await _keys(client, world, type="BLD,URN") == {"a", "b"}
    assert await _keys(client, world, type=f"{V2_0487}|") == {"a", "b"}
    assert await _keys(client, world, type="http://wrong|BLD") == set()
    assert await _keys(client, world, **{"type:not": "BLD"}) == {"b", "c"}
    assert await _keys(client, world, **{"type:text": "blood"}) == {
        "a"
    }  # CodeableConcept.text
    assert await _keys(client, world, **{"type:text": "urine"}) == {
        "b"
    }  # a coding's display
    assert await _keys(client, world, **{"type:missing": "true"}) == {"c"}
    assert await _keys(client, world, **{"type:missing": "false"}) == {"a", "b"}


# -- container (typeTested.container.type, every entry) -------------------------------------


async def test_container_reads_every_type_tested_entry(client, world):
    assert await _keys(client, world, container="SPECIMEN") == {"a"}
    assert await _keys(client, world, container="TUBE") == {"a"}  # the second entry
    assert await _keys(client, world, container="CUP") == {"b"}
    assert await _keys(client, world, container=f"{V2_0487}|CUP") == {"b"}
    assert await _keys(client, world, container="CUP,TUBE") == {"a", "b"}
    assert await _keys(client, world, container="http://wrong|CUP") == set()
    assert await _keys(client, world, **{"container:text": "tube"}) == {"a"}
    assert await _keys(client, world, **{"container:missing": "true"}) == {"c"}


# -- identifier -----------------------------------------------------------------------------


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="SD-A") == {"a"}
    assert await _keys(client, world, identifier=f"{SPECIMEN_DEFINITION_IDS}|SD-A") == {
        "a"
    }
    assert await _keys(client, world, identifier="urn:other|") == {"b"}
    assert await _keys(client, world, identifier="|SD-A") == set()
    assert await _keys(client, world, identifier="urn:wrong|SD-A") == set()
    assert await _keys(client, world, **{"identifier:text": "form number"}) == {"a"}
    assert await _keys(client, world, **{"identifier:text": "accession"}) == {"a"}
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|ACSN|SD-A"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|ACSN|SD-B"})
        == set()
    )
    assert await _keys(client, world, **{"identifier:not": "SD-A"}) == {"b", "c"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {"c"}


# -- the elements R4 gives no parameter ------------------------------------------------------


async def test_other_elements_have_no_search_parameter(client, world):
    for name in (
        "patient-preparation",
        "time-aspect",
        "collection",
        "is-derived",
        "preference",
    ):
        strict = await client.get(
            BASE + "/", params={name: "x"}, headers={"Prefer": "handling=strict"}
        )
        assert strict.status_code == 400, name


# -- _sort / _count / _offset / _total ------------------------------------------------------


async def test_sort_by_every_declared_param(client, world):
    for key in ("_id", "_lastUpdated", "container", "identifier", "type"):
        assert (await _search(client, _sort=key))["total"] == 3, key
        assert (await _search(client, _sort=f"-{key}"))["total"] == 3, key


async def test_sort_by_identifier_orders_the_resources(client, world):
    got = [
        e["resource"].get("identifier", {}).get("value")
        for e in (await _search(client, _sort="identifier"))["entry"]
    ]
    assert [v for v in got if v] == ["SD-A", "SD-B"]
    got = [
        e["resource"].get("identifier", {}).get("value")
        for e in (await _search(client, _sort="-identifier"))["entry"]
    ]
    assert [v for v in got if v] == ["SD-B", "SD-A"]


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
    resource = (await _search(client, _elements="typeCollected", _id=str(world["a"])))[
        "entry"
    ][0]["resource"]
    assert resource["typeCollected"]["coding"][0]["code"] == "BLD"
    assert "typeTested" not in resource and "identifier" not in resource


# -- combination, errors --------------------------------------------------------------------


async def test_and_or_combination(client, world):
    assert await _keys(client, world, type="BLD", container="TUBE") == {"a"}
    assert await _keys(client, world, type="URN", container="TUBE") == set()
    assert await _keys(client, world, container=["SPECIMEN", "TUBE"]) == {
        "a"
    }  # AND of two


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"type:exact": "x"}) == 400
    assert await _status(client, **{"identifier:below": "x"}) == 400
    assert await _status(client, **{"container:of-type": "x"}) == 400


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


# -- POST _search / Bundle shape ------------------------------------------------------------


async def test_post_search_form_encoded(client, world):
    resp = await client.post(
        BASE + "/_search", data={"type": "URN", "container": "CUP"}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, identifier="SD-A")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/specimen-definitions/{world['a']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "SpecimenDefinition"
    assert len(entry["resource"]["typeTested"]) == 2


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
