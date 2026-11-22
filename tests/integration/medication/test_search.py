"""FHIR R4 search over Medication (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/medication.html#search).

One block per search parameter — `status` a code, `expiration-date` a date range over a
dateTime, `lot-number` a token over a string, `identifier`, `code`, `form` and `ingredient-code`
tokens, the single-target `manufacturer` and the multi-target `ingredient` references — then
chaining, `_include`/`_revinclude`, result parameters, combination rules, lenient vs strict
handling and POST _search.
"""

import pytest

from tests.integration.medication.support import (
    API,
    BASE,
    MED_IDS,
    RXNORM,
    SCT,
    V2_0203,
    concept,
    create_medication,
    create_organization,
    medication_body,
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
    """Two organizations and five medications with distinct, searchable values.
    Returns {key: id}.

      a  active tablet from org1, two ingredients (one coded, one a Substance), in a batch
      b  inactive capsule from org2, with `a` as an ingredient
      c  entered-in-error, coded only by text, an open batch
      d  a Substance ingredient and a logical manufacturer
      e  nothing coded
    """
    w = {}
    w["o1"] = await create_organization(client, name="Pharma One")
    w["o2"] = await create_organization(client, name="Pharma Two")
    w["a"] = await create_medication(
        client,
        medication_body(
            status="active",
            identifier=[
                {
                    "system": MED_IDS,
                    "value": "MED-A",
                    "type": {
                        "coding": [{"system": V2_0203, "code": "FILL"}],
                        "text": "Med id",
                    },
                }
            ],
            code=concept(RXNORM, "1049502", "Oxycodone 10 MG ER tablet"),
            form=concept(SCT, "385057009", "Film-coated tablet"),
            manufacturer={"reference": f"Organization/{w['o1']}"},
            ingredient=[
                {"itemCodeableConcept": concept(RXNORM, "7804", "Oxycodone")},
                {"itemReference": {"reference": "Substance/12345"}},
            ],
            batch={"lotNumber": "LOT-A", "expirationDate": "2027-06-30T00:00:00Z"},
        ),
    )
    w["b"] = await create_medication(
        client,
        medication_body(
            status="inactive",
            identifier=[{"system": MED_IDS, "value": "MED-B"}],
            code=concept(RXNORM, "197696", "Ibuprofen"),
            form=concept(SCT, "385049006", "Capsule"),
            manufacturer={"reference": f"Organization/{w['o2']}"},
            ingredient=[{"itemReference": {"reference": f"Medication/{w['a']}"}}],
            batch={"lotNumber": "LOT-B", "expirationDate": "2028-01"},
        ),
    )
    w["c"] = await create_medication(
        client,
        {
            "status": "entered-in-error",
            "code": {"text": "Compounded cream"},
            "batch": {"expirationDate": "2026-12-31"},
        },
    )
    w["d"] = await create_medication(
        client,
        {
            "manufacturer": {
                "identifier": {"system": "urn:mfr", "value": "M-9"},
                "display": "External",
            },
            "ingredient": [{"itemReference": {"reference": "Substance/12345"}}],
        },
    )
    w["e"] = await create_medication(client, {})
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


# -- _id / _lastUpdated / status -------------------------------------------------------------


async def test_id(client, world):
    assert await _keys(client, world, _id=str(world["a"])) == {"a"}
    assert await _keys(client, world, _id="999999") == set()
    assert await _keys(client, world, **{"_id:not": str(world["a"])}) == ALL - {"a"}


async def test_last_updated(client, world):
    assert await _keys(client, world, _lastUpdated="ge2020-01-01") == ALL
    assert await _keys(client, world, _lastUpdated="lt2020-01-01") == set()


async def test_status(client, world):
    assert await _keys(client, world, status="active") == {"a"}
    assert await _keys(client, world, status="inactive") == {"b"}
    assert await _keys(client, world, status="entered-in-error") == {
        "c"
    }  # the real FHIR code
    assert await _keys(client, world, status="active,inactive") == {"a", "b"}
    assert await _keys(
        client, world, status="http://hl7.org/fhir/CodeSystem/medication-status|active"
    ) == {"a"}
    assert await _keys(client, world, status="http://wrong|active") == set()
    assert await _keys(client, world, status="no-such-code") == set()
    assert await _keys(client, world, **{"status:missing": "true"}) == {"d", "e"}
    assert await _keys(client, world, **{"status:missing": "false"}) == {"a", "b", "c"}


# -- expiration-date / lot-number ------------------------------------------------------------


async def test_expiration_date(client, world):
    assert await _keys(client, world, **{"expiration-date": "2027-06-30"}) == {"a"}
    assert await _keys(client, world, **{"expiration-date": "2027"}) == {"a"}
    assert await _keys(client, world, **{"expiration-date": "2028"}) == {
        "b"
    }  # a partial date covers its precision
    assert await _keys(client, world, **{"expiration-date": "ge2027-01-01"}) == {
        "a",
        "b",
    }
    assert await _keys(client, world, **{"expiration-date": "lt2027-01-01"}) == {"c"}
    assert await _keys(client, world, **{"expiration-date": "sa2027-07-01"}) == {"b"}
    assert await _keys(client, world, **{"expiration-date": "eb2027-01-01"}) == {"c"}
    assert await _keys(client, world, **{"expiration-date:missing": "true"}) == {
        "d",
        "e",
    }


async def test_lot_number(client, world):
    assert await _keys(client, world, **{"lot-number": "LOT-A"}) == {"a"}
    assert await _keys(client, world, **{"lot-number": "LOT-A,LOT-B"}) == {"a", "b"}
    assert (
        await _keys(client, world, **{"lot-number": "lot-a"}) == set()
    )  # an exact, case-sensitive code
    assert (
        await _keys(client, world, **{"lot-number": "urn:x|LOT-A"}) == set()
    )  # a string has no system
    assert await _keys(client, world, **{"lot-number:not": "LOT-A"}) == {
        "b",
        "c",
        "d",
        "e",
    }
    assert await _keys(client, world, **{"lot-number:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


# -- identifier / code / form / ingredient-code ----------------------------------------------


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="MED-A") == {"a"}
    assert await _keys(client, world, identifier=f"{MED_IDS}|MED-B") == {"b"}
    assert await _keys(client, world, identifier="MED-A,MED-B") == {"a", "b"}
    assert await _keys(client, world, identifier="urn:wrong|MED-A") == set()
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|FILL|MED-A"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|FILL|MED-B"})
        == set()
    )
    assert await _keys(client, world, **{"identifier:text": "med id"}) == {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


async def test_code(client, world):
    assert await _keys(client, world, code="1049502") == {"a"}
    assert await _keys(client, world, code=f"{RXNORM}|197696") == {"b"}
    assert await _keys(client, world, code="http://wrong|197696") == set()
    assert await _keys(client, world, code="1049502,197696") == {"a", "b"}
    assert await _keys(client, world, **{"code:text": "compounded"}) == {
        "c"
    }  # a text-only concept is found
    assert await _keys(client, world, **{"code:text": "ibuprofen"}) == {
        "b"
    }  # Coding.display
    assert await _keys(client, world, **{"code:missing": "true"}) == {"d", "e"}


async def test_form(client, world):
    assert await _keys(client, world, form="385057009") == {"a"}
    assert await _keys(client, world, form=f"{SCT}|385049006") == {"b"}
    assert await _keys(client, world, **{"form:text": "capsule"}) == {"b"}
    assert await _keys(client, world, **{"form:missing": "true"}) == {"c", "d", "e"}


async def test_ingredient_code_reads_every_ingredient(client, world):
    assert await _keys(client, world, **{"ingredient-code": "7804"}) == {"a"}
    assert await _keys(client, world, **{"ingredient-code": f"{RXNORM}|7804"}) == {"a"}
    assert await _keys(client, world, **{"ingredient-code:text": "oxy"}) == {"a"}
    # an ingredient that is a reference carries no code
    assert await _keys(client, world, **{"ingredient-code:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }


# -- manufacturer / ingredient ---------------------------------------------------------------


async def test_manufacturer(client, world):
    assert await _keys(client, world, manufacturer=str(world["o1"])) == {
        "a"
    }  # one target: a bare id works
    assert await _keys(client, world, manufacturer=f"Organization/{world['o2']}") == {
        "b"
    }
    assert await _keys(client, world, manufacturer=f"{world['o1']},{world['o2']}") == {
        "a",
        "b",
    }
    assert await _keys(client, world, manufacturer="999999") == set()
    assert await _keys(client, world, **{"manufacturer:identifier": "urn:mfr|M-9"}) == {
        "d"
    }
    assert await _keys(client, world, **{"manufacturer:missing": "true"}) == {"c", "e"}


async def test_ingredient_is_multi_target(client, world):
    assert (
        await _status(client, ingredient=str(world["a"])) == 400
    )  # a bare id is ambiguous
    assert await _keys(client, world, ingredient=f"Medication/{world['a']}") == {"b"}
    assert await _keys(client, world, **{"ingredient:Medication": str(world["a"])}) == {
        "b"
    }
    assert await _keys(client, world, ingredient="Substance/12345") == {
        "a",
        "d",
    }  # the type is part of the match
    assert await _keys(client, world, ingredient=f"Substance/{world['a']}") == set()
    assert await _keys(client, world, **{"ingredient:missing": "true"}) == {"c", "e"}


# -- chaining --------------------------------------------------------------------------------


async def test_chains(client, world):
    assert await _keys(client, world, **{"manufacturer.name": "Pharma One"}) == {"a"}
    assert await _keys(client, world, **{"manufacturer.name": "Pharma"}) == {"a", "b"}
    assert await _keys(client, world, **{"ingredient:Medication.status": "active"}) == {
        "b"
    }
    assert await _keys(client, world, **{"ingredient:Medication.code": "1049502"}) == {
        "b"
    }


async def test_bad_chains_are_400(client, world):
    assert await _status(client, **{"manufacturer.nonsense": "x"}) == 400
    assert (
        await _status(client, **{"ingredient.status": "x"}) == 400
    )  # an untyped multi-target cannot be chained
    assert (
        await _status(client, **{"ingredient:Substance.name": "x"}) == 400
    )  # Substance is not a resource here
    assert (
        await _status(client, **{"code.x": "y"}) == 400
    )  # a token cannot be chained through
    assert await _status(client, **{"expiration-date.x": "y"}) == 400


# -- _sort / _count / _offset / _total -------------------------------------------------------


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "code",
        "expiration-date",
        "form",
        "identifier",
        "ingredient",
        "ingredient-code",
        "lot-number",
        "manufacturer",
        "status",
        "_id",
    ):
        assert (await _search(client, _sort=key))["total"] == 5, key


async def test_sort_by_expiration_date(client, world):
    async def ids(**params):
        return [
            int(e["resource"]["id"]) for e in (await _search(client, **params))["entry"]
        ]

    assert await ids(
        **{"expiration-date:missing": "false", "_sort": "expiration-date"}
    ) == [world["c"], world["a"], world["b"]]
    assert await ids(
        **{"expiration-date:missing": "false", "_sort": "-expiration-date"}
    ) == [world["b"], world["a"], world["c"]]


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
    assert resource["status"] == "active"
    assert "batch" not in resource and "ingredient" not in resource


# -- _include / _revinclude ------------------------------------------------------------------


async def test_include_manufacturer_and_ingredient(client, world):
    ids = ",".join(str(world[k]) for k in KEYS)
    bundle = await _search(client, _id=ids, _include="Medication:manufacturer")
    assert _of_type(bundle, "Organization", "include") == {
        str(world["o1"]),
        str(world["o2"]),
    }
    bundle = await _search(
        client, _id=str(world["b"]), _include="Medication:ingredient"
    )
    assert _of_type(bundle, "Medication", "include") == {
        str(world["a"])
    }  # a Substance adds nothing


async def test_revinclude_on_the_organizations_and_on_itself(client, world):
    bundle = await _other(
        client,
        "organizations",
        _id=str(world["o1"]),
        _revinclude="Medication:manufacturer",
    )
    assert _of_type(bundle, "Medication", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "organizations",
        _id=f"{world['o1']},{world['o2']}",
        _revinclude="Medication:manufacturer",
    )
    assert _of_type(bundle, "Medication", "include") == {
        str(world["a"]),
        str(world["b"]),
    }
    bundle = await _search(
        client, _id=str(world["a"]), _revinclude="Medication:ingredient"
    )
    assert _of_type(bundle, "Medication", "include") == {str(world["b"])}


# -- combination rules / lenient vs strict ---------------------------------------------------


async def test_params_are_anded(client, world):
    assert await _keys(client, world, status="active", form="385057009") == {"a"}
    assert await _keys(client, world, status="inactive", form="385057009") == set()
    assert await _keys(client, world, code="1049502", **{"lot-number": "LOT-A"}) == {
        "a"
    }


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"manufacturer:text": "x"}) == 400
    assert await _status(client, **{"expiration-date:exact": "2020"}) == 400
    assert await _status(client, **{"identifier:below": "x"}) == 400
    assert await _status(client, **{"status:text": "x"}) == 400
    assert await _status(client, **{"expiration-date": "banana"}) == 400


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


# -- POST _search / Bundle shape -------------------------------------------------------------


async def test_post_search_form_encoded(client, world):
    resp = await client.post(
        BASE + "/_search", data={"form": "385049006", "status": "inactive"}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, identifier="MED-B")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/medications/{world['b']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "Medication"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
