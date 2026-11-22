"""FHIR R4 search over Group (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/group.html#search).

One block per search parameter - `type` a code, `actual` and `exclude` booleans, `identifier`,
`code`, `characteristic` and `value` tokens, the `characteristic-value` composite (a
characteristic code and a value of the *same* characteristic), the multi-target `managing-entity`
and `member` references - then chaining, `_include`/`_revinclude`, result parameters,
combination rules, lenient vs strict handling and POST _search.
"""

import pytest

from tests.integration.group.support import (
    API,
    BASE,
    GROUP_IDS,
    LOINC,
    SCT,
    V2_0203,
    concept,
    create_group,
    create_medication,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_related_person,
    group_body,
    medication_body,
    related_person_body,
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
    """An organization, a practitioner, a role, two patients, a related person and a medication,
    plus five groups with distinct, searchable values. Returns {key: id}.

      a  actual person group managed by an organization, with two patients and a group member, two
         characteristics (a height range, an excluded male flag)
      b  actual practitioner group managed by a practitioner, with a practitioner member
      c  descriptive medication group, a coded characteristic
      d  an animal group with a logical manager and a Device member
      e  only what R4 requires
    """
    w = {}
    w["org"] = await create_organization(client, name="Pharma One")
    w["pr"] = await create_practitioner(client)  # family "Careful"
    w["role"] = await create_practitioner_role(client)
    w["p1"] = await create_patient(
        client, {"active": True, "name": [{"family": "Windsor", "given": ["Anna"]}]}
    )
    w["p2"] = await create_patient(
        client, {"active": True, "name": [{"family": "Fairfax", "given": ["Ben"]}]}
    )
    w["rel"] = await create_related_person(client, related_person_body(w["p1"]))
    w["med"] = await create_medication(client, medication_body(status="active"))
    w["e"] = await create_group(client, group_body())
    w["a"] = await create_group(
        client,
        group_body(
            type="person",
            actual=True,
            active=True,
            identifier=[
                {
                    "system": GROUP_IDS,
                    "value": "GRP-A",
                    "type": {
                        "coding": [{"system": V2_0203, "code": "FILL"}],
                        "text": "Group id",
                    },
                }
            ],
            code=concept(SCT, "385093006", "Community"),
            name="Diabetes cohort",
            quantity=3,
            managingEntity={"reference": f"Organization/{w['org']}"},
            characteristic=[
                {
                    "code": concept(LOINC, "8302-2", "Body height"),
                    "valueQuantity": {"value": 180, "unit": "cm"},
                    "exclude": False,
                },
                {
                    "code": concept(SCT, "248153007", "Male"),
                    "valueBoolean": True,
                    "exclude": True,
                },
            ],
            member=[
                {"entity": {"reference": f"Patient/{w['p1']}"}},
                {"entity": {"reference": f"Patient/{w['p2']}"}},
                {"entity": {"reference": f"Group/{w['e']}"}},
            ],
        ),
    )
    w["b"] = await create_group(
        client,
        group_body(
            type="practitioner",
            actual=True,
            identifier=[{"system": GROUP_IDS, "value": "GRP-B"}],
            code={"text": "Surgeons"},
            managingEntity={"reference": f"Practitioner/{w['pr']}"},
            member=[{"entity": {"reference": f"Practitioner/{w['pr']}"}}],
        ),
    )
    w["c"] = await create_group(
        client,
        group_body(
            type="medication",
            actual=False,
            characteristic=[
                {
                    "code": concept(LOINC, "8302-2", "Body height"),
                    "valueCodeableConcept": concept(SCT, "248153007", "Tall"),
                    "exclude": False,
                },
                {
                    "code": concept(SCT, "248153007", "Male"),
                    "valueCodeableConcept": concept(SCT, "1", "Other"),
                    "exclude": False,
                },
            ],
        ),
    )
    w["d"] = await create_group(
        client,
        group_body(
            type="animal",
            actual=True,
            managingEntity={
                "identifier": {"system": "urn:mgr", "value": "M-9"},
                "display": "External",
            },
            member=[{"entity": {"reference": "Device/5"}}],
        ),
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


# -- _id / _lastUpdated ---------------------------------------------------------------------


async def test_id(client, world):
    assert await _keys(client, world, _id=str(world["a"])) == {"a"}
    assert await _keys(client, world, _id="999999") == set()
    assert await _keys(client, world, **{"_id:not": str(world["a"])}) == ALL - {"a"}


async def test_last_updated(client, world):
    assert await _keys(client, world, _lastUpdated="ge2020-01-01") == ALL
    assert await _keys(client, world, _lastUpdated="lt2020-01-01") == set()


# -- type / actual / exclude ----------------------------------------------------------------


async def test_type(client, world):
    assert await _keys(client, world, type="practitioner") == {"b"}
    assert await _keys(client, world, type="medication") == {"c"}
    assert await _keys(client, world, type="animal") == {"d"}
    assert await _keys(client, world, type="person") == {"a", "e"}
    assert await _keys(client, world, type="animal,medication") == {"c", "d"}
    assert await _keys(client, world, type="http://hl7.org/fhir/group-type|animal") == {
        "d"
    }
    assert await _keys(client, world, type="http://wrong|animal") == set()
    assert await _keys(client, world, type="no-such-code") == set()
    assert await _keys(client, world, **{"type:not": "person"}) == {"b", "c", "d"}
    assert await _keys(client, world, **{"type:missing": "true"}) == set()


async def test_actual(client, world):
    assert await _keys(client, world, actual="true") == {"a", "b", "d", "e"}
    assert await _keys(client, world, actual="false") == {"c"}
    assert await _keys(client, world, actual="maybe") == set()
    assert await _keys(client, world, **{"actual:not": "true"}) == {"c"}
    assert await _keys(client, world, **{"actual:missing": "true"}) == set()


async def test_exclude_reads_every_characteristic(client, world):
    assert await _keys(client, world, exclude="true") == {
        "a"
    }  # a's second characteristic
    assert await _keys(client, world, exclude="false") == {"a", "c"}
    assert await _keys(client, world, **{"exclude:missing": "true"}) == {"b", "d", "e"}


# -- identifier / code / characteristic / value ---------------------------------------------


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="GRP-A") == {"a"}
    assert await _keys(client, world, identifier=f"{GROUP_IDS}|GRP-B") == {"b"}
    assert await _keys(client, world, identifier="GRP-A,GRP-B") == {"a", "b"}
    assert await _keys(client, world, identifier="urn:wrong|GRP-A") == set()
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|FILL|GRP-A"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|FILL|GRP-B"})
        == set()
    )
    assert await _keys(client, world, **{"identifier:text": "group id"}) == {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


async def test_code(client, world):
    assert await _keys(client, world, code="385093006") == {"a"}
    assert await _keys(client, world, code=f"{SCT}|385093006") == {"a"}
    assert await _keys(client, world, code="http://wrong|385093006") == set()
    assert await _keys(client, world, **{"code:text": "surgeons"}) == {
        "b"
    }  # a text-only concept
    assert await _keys(client, world, **{"code:text": "commun"}) == {
        "a"
    }  # Coding.display
    assert await _keys(client, world, **{"code:missing": "true"}) == {"c", "d", "e"}


async def test_characteristic_reads_every_characteristic(client, world):
    assert await _keys(client, world, characteristic="8302-2") == {"a", "c"}
    assert await _keys(client, world, characteristic=f"{SCT}|248153007") == {
        "a",
        "c",
    }  # each one's second
    assert await _keys(client, world, characteristic="http://wrong|8302-2") == set()
    assert await _keys(client, world, **{"characteristic:text": "body"}) == {"a", "c"}
    assert await _keys(client, world, **{"characteristic:missing": "true"}) == {
        "b",
        "d",
        "e",
    }


async def test_value_reads_a_codeable_concept_or_a_boolean(client, world):
    assert await _keys(client, world, value="248153007") == {"c"}  # c's Tall concept
    assert await _keys(client, world, value=f"{SCT}|1") == {"c"}
    assert await _keys(client, world, value="true") == {"a"}  # a's valueBoolean
    assert await _keys(client, world, **{"value:text": "tall"}) == {"c"}
    # a Quantity value (a's height) is not indexed for `value`
    assert await _keys(client, world, **{"value:missing": "true"}) == {"b", "d", "e"}


# -- the characteristic-value composite ------------------------------------------------------


async def test_characteristic_value_pairs_a_code_and_a_value_of_the_same_characteristic(
    client, world
):
    # c: height -> Tall; male -> Other
    assert await _keys(
        client, world, **{"characteristic-value": f"{LOINC}|8302-2${SCT}|248153007"}
    ) == {"c"}
    assert await _keys(
        client, world, **{"characteristic-value": f"{SCT}|248153007${SCT}|1"}
    ) == {"c"}
    # the code of one characteristic with the value of the *other* does not pair
    assert (
        await _keys(
            client, world, **{"characteristic-value": f"{LOINC}|8302-2${SCT}|1"}
        )
        == set()
    )
    # whereas the two single parameters would both match c
    assert await _keys(client, world, characteristic="8302-2", value="1") == {"c"}
    # a's boolean value pairs with its own characteristic
    assert await _keys(
        client, world, **{"characteristic-value": f"{SCT}|248153007$true"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"characteristic-value": f"{LOINC}|8302-2$true"})
        == set()
    )
    # OR across alternatives
    assert await _keys(
        client,
        world,
        **{"characteristic-value": f"{SCT}|248153007$true,{SCT}|248153007${SCT}|1"},
    ) == {"a", "c"}


async def test_characteristic_value_malformed_is_400(client, world):
    for bad in ("8302-2", "a$b$c", "$x", "x$"):
        assert await _status(client, **{"characteristic-value": bad}) == 400, bad
    assert (
        await _status(client, **{"characteristic-value:text": "x$y"}) == 400
    )  # no modifiers


# -- managing-entity / member ---------------------------------------------------------------


async def test_managing_entity_is_multi_target(client, world):
    assert await _status(client, **{"managing-entity": str(world["org"])}) == 400
    assert await _keys(
        client, world, **{"managing-entity": f"Organization/{world['org']}"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"managing-entity:Practitioner": str(world["pr"])}
    ) == {"b"}
    assert (
        await _keys(
            client, world, **{"managing-entity": f"Practitioner/{world['org']}"}
        )
        == set()
    )
    assert await _keys(
        client, world, **{"managing-entity:identifier": "urn:mgr|M-9"}
    ) == {"d"}
    assert await _keys(client, world, **{"managing-entity:missing": "true"}) == {
        "c",
        "e",
    }


async def test_member_is_multi_target(client, world):
    assert (
        await _status(client, member=str(world["p1"])) == 400
    )  # a bare id is ambiguous
    assert await _keys(client, world, member=f"Patient/{world['p1']}") == {"a"}
    assert await _keys(client, world, **{"member:Patient": str(world["p2"])}) == {"a"}
    assert await _keys(client, world, member=f"Practitioner/{world['pr']}") == {"b"}
    assert await _keys(client, world, member=f"Group/{world['e']}") == {"a"}
    assert await _keys(client, world, member="Device/5") == {"d"}
    assert (
        await _keys(client, world, member=f"Group/{world['p1']}") == set()
    )  # the type is part of the match
    assert await _keys(client, world, member=f"Patient/{world['p1']},Device/5") == {
        "a",
        "d",
    }
    assert await _keys(client, world, **{"member:missing": "true"}) == {"c", "e"}


# -- chaining -------------------------------------------------------------------------------


async def test_chains(client, world):
    assert await _keys(
        client, world, **{"managing-entity:Organization.name": "Pharma"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"managing-entity:Practitioner.family": "Careful"}
    ) == {"b"}
    assert await _keys(client, world, **{"member:Patient.family": "Windsor"}) == {"a"}
    assert await _keys(client, world, **{"member:Practitioner.family": "Careful"}) == {
        "b"
    }
    assert await _keys(client, world, **{"member:Group.type": "person"}) == {
        "a"
    }  # a has the empty person group


async def test_bad_chains_are_400(client, world):
    assert (
        await _status(client, **{"managing-entity.name": "x"}) == 400
    )  # an untyped multi-target cannot be chained
    assert await _status(client, **{"member.family": "x"}) == 400
    assert (
        await _status(client, **{"member:Device.x": "x"}) == 400
    )  # Device is not searchable here
    assert await _status(client, **{"member:Substance.x": "x"}) == 400
    assert (
        await _status(client, **{"code.x": "y"}) == 400
    )  # a token cannot be chained through


# -- _sort / _count / _offset / _total ------------------------------------------------------


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "actual",
        "characteristic",
        "code",
        "exclude",
        "identifier",
        "managing-entity",
        "member",
        "type",
        "value",
        "_id",
    ):
        assert (await _search(client, _sort=key))["total"] == 5, key


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
    resource = (await _search(client, _elements="type", _id=str(world["a"])))["entry"][
        0
    ]["resource"]
    assert resource["type"] == "person"
    assert "member" not in resource and "characteristic" not in resource


# -- _include / _revinclude -----------------------------------------------------------------


async def test_include_managing_entity_and_member(client, world):
    ids = ",".join(str(world[k]) for k in KEYS)
    ids_without_e = ",".join(str(world[k]) for k in KEYS if k != "e")
    bundle = await _search(client, _id=ids, _include="Group:managing-entity")
    assert _of_type(bundle, "Organization", "include") == {str(world["org"])}
    assert _of_type(bundle, "Practitioner", "include") == {
        str(world["pr"])
    }  # a logical manager adds nothing
    bundle = await _search(
        client, _id=ids, _include="Group:managing-entity:Organization"
    )
    assert _of_type(bundle, "Practitioner", "include") == set()
    bundle = await _search(client, _id=ids_without_e, _include="Group:member")
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "Group", "include") == {
        str(world["e"])
    }  # a Device adds nothing


async def test_revinclude_on_the_resources_a_group_points_at(client, world):
    bundle = await _other(
        client, "patients", _id=str(world["p1"]), _revinclude="Group:member"
    )
    assert _of_type(bundle, "Group", "include") == {str(world["a"])}
    bundle = await _other(
        client, "practitioners", _id=str(world["pr"]), _revinclude="Group:member"
    )
    assert _of_type(bundle, "Group", "include") == {str(world["b"])}
    bundle = await _other(
        client,
        "practitioners",
        _id=str(world["pr"]),
        _revinclude="Group:managing-entity",
    )
    assert _of_type(bundle, "Group", "include") == {str(world["b"])}
    bundle = await _other(
        client,
        "organizations",
        _id=str(world["org"]),
        _revinclude="Group:managing-entity",
    )
    assert _of_type(bundle, "Group", "include") == {str(world["a"])}
    bundle = await _search(client, _id=str(world["e"]), _revinclude="Group:member")
    assert _of_type(bundle, "Group", "include") == {str(world["a"])}


# -- combination rules / lenient vs strict --------------------------------------------------


async def test_params_are_anded(client, world):
    assert await _keys(client, world, type="person", actual="true") == {"a", "e"}
    assert await _keys(client, world, type="person", code="385093006") == {"a"}
    assert await _keys(client, world, type="animal", code="385093006") == set()


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"member:text": "x"}) == 400
    assert await _status(client, **{"identifier:below": "x"}) == 400
    assert await _status(client, **{"type:text": "x"}) == 400
    assert await _status(client, **{"actual:text": "x"}) == 400


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
        BASE + "/_search", data={"type": "practitioner", "actual": "true"}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, identifier="GRP-B")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/groups/{world['b']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "Group"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
