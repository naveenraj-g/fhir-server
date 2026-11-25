"""FHIR R4 search over Flag (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/flag.html#search).

One block per search parameter - `identifier`, `date` (a Period), the multi-target `subject` and
its narrowed `patient`, the single-target `encounter` and the multi-target `author` - then
chaining, `_include`/`_revinclude`, result parameters, combination rules, lenient vs strict
handling and POST _search. R4 defines no `status`, `category` or `code` parameter for Flag.
"""

import pytest

from tests.integration.flag.support import (
    API,
    BASE,
    FLAG_IDS,
    V2_0203,
    create_encounter,
    create_flag,
    create_group,
    create_location,
    create_medication,
    create_organization,
    create_patient,
    create_practitioner,
    encounter_body,
    flag_body,
    group_body,
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
    """Two patients, a group, an organization, a practitioner, a location, a medication and an
    encounter, and five flags with distinct, searchable values. Returns {key: id}.

      a  for p1; identifier F-A; active 2026-01-15 to 2026-12-31; in the encounter; by the
         practitioner
      b  for the group; from 2026-06-01 on (open ended); by the organization
      c  for the organization; no period
      d  for a logical subject (an identifier only); period 2025
      e  for p2; for the location's sibling medication; no period, no author
    """
    w = {}
    w["p1"] = await create_patient(client)
    w["p2"] = await create_patient(client)
    w["grp"] = await create_group(client, group_body())
    w["org"] = await create_organization(client, name="Flag Org")
    w["pr"] = await create_practitioner(client)
    w["loc"] = await create_location(client)
    w["med"] = await create_medication(client, medication_body())
    w["enc"] = await create_encounter(
        client, encounter_body(subject={"reference": f"Patient/{w['p1']}"})
    )
    w["a"] = await create_flag(
        client,
        flag_body(
            {"reference": f"Patient/{w['p1']}"},
            identifier=[
                {
                    "system": FLAG_IDS,
                    "value": "F-A",
                    "type": {
                        "coding": [{"system": V2_0203, "code": "FILL"}],
                        "text": "Flag id",
                    },
                }
            ],
            period={"start": "2026-01-15", "end": "2026-12-31"},
            encounter={"reference": f"Encounter/{w['enc']}"},
            author={"reference": f"Practitioner/{w['pr']}"},
        ),
    )
    w["b"] = await create_flag(
        client,
        flag_body(
            {"reference": f"Group/{w['grp']}"},
            period={"start": "2026-06-01"},
            author={"reference": f"Organization/{w['org']}"},
        ),
    )
    w["c"] = await create_flag(
        client, flag_body({"reference": f"Organization/{w['org']}"})
    )
    w["d"] = await create_flag(
        client,
        flag_body(
            {
                "identifier": {"system": "urn:subj", "value": "S-9"},
                "display": "Someone",
            },
            identifier=[{"system": FLAG_IDS, "value": "F-D"}],
            period={"start": "2025-01-01", "end": "2025-12-31"},
        ),
    )
    w["e"] = await create_flag(client, flag_body({"reference": f"Patient/{w['p2']}"}))
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


# -- _id / _lastUpdated -----------------------------------------------------------------------


async def test_id(client, world):
    assert await _keys(client, world, _id=str(world["a"])) == {"a"}
    assert await _keys(client, world, _id="999999") == set()
    assert await _keys(client, world, **{"_id:not": str(world["a"])}) == ALL - {"a"}


async def test_last_updated(client, world):
    assert await _keys(client, world, _lastUpdated="ge2020-01-01") == ALL
    assert await _keys(client, world, _lastUpdated="lt2020-01-01") == set()


# -- identifier / date ------------------------------------------------------------------------


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="F-A") == {"a"}
    assert await _keys(client, world, identifier=f"{FLAG_IDS}|F-D") == {"d"}
    assert await _keys(client, world, identifier="F-A,F-D") == {"a", "d"}
    assert await _keys(client, world, identifier="urn:wrong|F-A") == set()
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|FILL|F-A"}
    ) == {"a"}
    assert await _keys(client, world, **{"identifier:text": "flag id"}) == {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {
        "b",
        "c",
        "e",
    }


async def test_date_is_a_range_search(client, world):
    assert (
        await _keys(client, world, date="2026-03-01") == set()
    )  # eq: the period must fit
    assert await _keys(client, world, date="ge2026-03-01") == {
        "a",
        "b",
    }  # overlaps above
    assert await _keys(client, world, date="le2026-03-01") == {
        "a",
        "d",
    }  # overlaps below
    assert await _keys(client, world, date="sa2026-01-01") == {"a", "b"}
    assert await _keys(client, world, date="eb2026-01-01") == {"d"}
    assert await _keys(client, world, date="ge2030-01-01") == {"b"}  # open ended
    assert await _keys(client, world, **{"date:missing": "true"}) == {"c", "e"}


# -- subject / patient ------------------------------------------------------------------------


async def test_subject_is_multi_target(client, world):
    assert await _status(client, subject=str(world["p1"])) == 400  # bare id: ambiguous
    assert await _keys(client, world, subject=f"Patient/{world['p1']}") == {"a"}
    assert await _keys(client, world, **{"subject:Patient": str(world["p2"])}) == {"e"}
    assert await _keys(client, world, subject=f"Group/{world['grp']}") == {"b"}
    assert await _keys(client, world, subject=f"Organization/{world['org']}") == {"c"}
    assert await _keys(
        client, world, **{"subject:Organization": str(world["org"])}
    ) == {"c"}
    assert (
        await _keys(client, world, subject=f"Group/{world['p1']}") == set()
    )  # the type is part of the match
    assert await _keys(client, world, **{"subject:identifier": "urn:subj|S-9"}) == {"d"}
    assert await _keys(client, world, **{"subject:missing": "true"}) == set()


async def test_patient_is_subject_narrowed_to_patients(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {
        "a"
    }  # a bare id works
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"e"}
    # the Group and Organization subjects are not patients, so they never match
    assert await _keys(client, world, patient=str(world["grp"])) == set()
    assert await _keys(client, world, **{"patient:missing": "true"}) == {"b", "c", "d"}


# -- encounter / author -----------------------------------------------------------------------


async def test_encounter_has_one_target_so_a_bare_id_works(client, world):
    assert await _keys(client, world, encounter=str(world["enc"])) == {"a"}
    assert await _keys(client, world, encounter=f"Encounter/{world['enc']}") == {"a"}
    assert await _keys(client, world, **{"encounter:missing": "true"}) == ALL - {"a"}


async def test_author_is_multi_target(client, world):
    assert await _status(client, author=str(world["pr"])) == 400
    assert await _keys(client, world, author=f"Practitioner/{world['pr']}") == {"a"}
    assert await _keys(client, world, author=f"Organization/{world['org']}") == {"b"}
    assert await _keys(client, world, **{"author:Organization": str(world["org"])}) == {
        "b"
    }
    assert await _keys(client, world, author=f"Organization/{world['pr']}") == set()
    assert await _keys(client, world, **{"author:missing": "true"}) == {"c", "d", "e"}


# -- chaining --------------------------------------------------------------------------------


async def test_chains(client, world):
    assert await _keys(client, world, **{"patient.active": "true"}) == {"a", "e"}
    assert await _keys(client, world, **{"subject:Patient.active": "true"}) == {
        "a",
        "e",
    }
    assert await _keys(client, world, **{"subject:Group.type": "person"}) == {"b"}
    assert await _keys(client, world, **{"subject:Organization.name": "Flag Org"}) == {
        "c"
    }
    assert await _keys(client, world, **{"author:Organization.name": "Flag Org"}) == {
        "b"
    }
    assert await _keys(client, world, **{"author:Practitioner.active": "true"}) <= {"a"}
    assert await _keys(client, world, **{"encounter.status": "in-progress"}) == {"a"}


async def test_bad_chains_are_400(client, world):
    assert await _status(client, **{"patient.nonsense": "x"}) == 400
    assert (
        await _status(client, **{"subject.active": "x"}) == 400
    )  # untyped multi-target
    assert await _status(client, **{"author.name": "x"}) == 400  # untyped multi-target
    assert (
        await _status(client, **{"author:Device.name": "x"}) == 400
    )  # Device is not a resource here
    assert (
        await _status(client, **{"subject:PlanDefinition.name": "x"}) == 200
    )  # PlanDefinition is rebuilt, so it chains
    assert await _status(client, **{"date.x": "y"}) == 400
    assert await _status(client, status="active") == 200  # unknown parameter, ignored


# -- _sort / _count / _offset / _total -------------------------------------------------------


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "author",
        "date",
        "encounter",
        "identifier",
        "patient",
        "subject",
        "_id",
    ):
        assert (await _search(client, _sort=key))["total"] == 5, key


async def test_sort_by_date(client, world):
    async def ids(**params):
        return [
            int(e["resource"]["id"]) for e in (await _search(client, **params))["entry"]
        ]

    assert await ids(**{"date:missing": "false", "_sort": "date"}) == [
        world["d"],
        world["a"],
        world["b"],
    ]
    assert await ids(**{"date:missing": "false", "_sort": "-date"}) == [
        world["b"],
        world["a"],
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
    resource = (await _search(client, _elements="status", _id=str(world["a"])))[
        "entry"
    ][0]["resource"]
    assert resource["status"] == "active"
    assert "period" not in resource and "author" not in resource


# -- _include / _revinclude ------------------------------------------------------------------


async def test_include_patient_subject_encounter_and_author(client, world):
    ids = ",".join(str(world[k]) for k in KEYS)
    bundle = await _search(client, _id=ids, _include="Flag:patient")
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }
    bundle = await _search(client, _id=ids, _include="Flag:subject")
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }
    assert _of_type(bundle, "Group", "include") == {str(world["grp"])}
    assert _of_type(bundle, "Organization", "include") == {str(world["org"])}
    bundle = await _search(client, _id=ids, _include="Flag:subject:Group")
    assert _of_type(bundle, "Patient", "include") == set()
    bundle = await _search(client, _id=ids, _include="Flag:encounter")
    assert _of_type(bundle, "Encounter", "include") == {str(world["enc"])}
    bundle = await _search(client, _id=ids, _include="Flag:author")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "Organization", "include") == {str(world["org"])}


async def test_revinclude_on_the_resources_a_flag_points_at(client, world):
    bundle = await _other(
        client,
        "patients",
        _id=f"{world['p1']},{world['p2']}",
        _revinclude="Flag:patient",
    )
    assert _of_type(bundle, "Flag", "include") == {str(world["a"]), str(world["e"])}
    bundle = await _other(
        client, "groups", _id=str(world["grp"]), _revinclude="Flag:subject"
    )
    assert _of_type(bundle, "Flag", "include") == {str(world["b"])}
    bundle = await _other(
        client, "organizations", _id=str(world["org"]), _revinclude="Flag:subject"
    )
    assert _of_type(bundle, "Flag", "include") == {str(world["c"])}
    bundle = await _other(
        client, "organizations", _id=str(world["org"]), _revinclude="Flag:author"
    )
    assert _of_type(bundle, "Flag", "include") == {str(world["b"])}
    bundle = await _other(
        client, "practitioners", _id=str(world["pr"]), _revinclude="Flag:author"
    )
    assert _of_type(bundle, "Flag", "include") == {str(world["a"])}
    bundle = await _other(
        client, "encounters", _id=str(world["enc"]), _revinclude="Flag:encounter"
    )
    assert _of_type(bundle, "Flag", "include") == {str(world["a"])}


# -- combination rules / lenient vs strict ---------------------------------------------------


async def test_params_are_anded(client, world):
    assert await _keys(
        client, world, patient=str(world["p1"]), date="ge2026-01-01"
    ) == {"a"}
    assert (
        await _keys(client, world, patient=str(world["p2"]), date="ge2026-01-01")
        == set()
    )
    assert await _keys(
        client, world, author=f"Practitioner/{world['pr']}", encounter=str(world["enc"])
    ) == {"a"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"subject:text": "x"}) == 400
    assert await _status(client, **{"date:exact": "2020"}) == 400
    assert await _status(client, **{"identifier:below": "x"}) == 400
    assert await _status(client, date="banana") == 400


async def test_unknown_param_lenient_vs_strict(client, world):
    lenient = await client.get(BASE + "/", params={"nonsense": "1"})
    assert lenient.status_code == 200
    assert any(e["search"]["mode"] == "outcome" for e in lenient.json()["entry"])
    strict = await client.get(
        BASE + "/", params={"nonsense": "1"}, headers={"Prefer": "handling=strict"}
    )
    assert strict.status_code == 400
    # R4 defines no status / category / code parameter for Flag
    strict_status = await client.get(
        BASE + "/", params={"status": "active"}, headers={"Prefer": "handling=strict"}
    )
    assert strict_status.status_code == 400


async def test_query_param_refused(client, world):
    assert await _status(client, _query="x") == 400


# -- POST _search / Bundle shape -------------------------------------------------------------


async def test_post_search_form_encoded(client, world):
    resp = await client.post(
        BASE + "/_search", data={"identifier": "F-D", "date": "le2025-12-31"}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["d"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, identifier="F-D")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/flags/{world['d']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "Flag"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
