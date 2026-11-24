"""FHIR R4 search over Goal (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/goal.html#search).

One block per search parameter - `lifecycle-status` a code, `achievement-status` and `category`
CodeableConcept tokens, `identifier`, `start-date` and `target-date` dates (the second over every
target), the multi-target `subject` and its narrowed `patient` - then chaining,
`_include`/`_revinclude` (including the CarePlan that names a goal), result parameters,
combination rules, lenient vs strict handling and POST _search.
"""

import pytest

from tests.integration.goal.support import (
    ACHIEVEMENT,
    API,
    BASE,
    GOAL_CATEGORY,
    GOAL_IDS,
    V2_0203,
    concept,
    create_goal,
    create_group,
    create_organization,
    create_patient,
    goal_body,
    group_body,
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
    """Two patients, a group and an organization, and five goals with distinct, searchable
    values. Returns {key: id}.

      a  active, for p1; in progress; dietary; starts 2026-01-15; targets due 2026-12-31 and
         2027-06-30; identifier G-A
      b  completed, for the group; achieved; behavioral; starts in 2026-06; target due 2026-03-01
      c  proposed, for the organization; starts as a concept; a target with only a duration
      d  on-hold, for a logical subject (an identifier only); a text-only achievement status;
         identifier G-D
      e  entered-in-error, for p2; a text-only category; no start, no target
    """
    w = {}
    w["p1"] = await create_patient(client)
    w["p2"] = await create_patient(client)
    w["grp"] = await create_group(client, group_body())
    w["org"] = await create_organization(client, name="Wellness Org")
    w["a"] = await create_goal(
        client,
        goal_body(
            {"reference": f"Patient/{w['p1']}"},
            lifecycleStatus="active",
            identifier=[
                {
                    "system": GOAL_IDS,
                    "value": "G-A",
                    "type": {
                        "coding": [{"system": V2_0203, "code": "FILL"}],
                        "text": "Goal id",
                    },
                }
            ],
            achievementStatus=concept(ACHIEVEMENT, "in-progress", "In Progress"),
            category=[
                concept(GOAL_CATEGORY, "dietary", "Dietary"),
                concept(GOAL_CATEGORY, "nursing"),
            ],
            startDate="2026-01-15",
            target=[{"dueDate": "2026-12-31"}, {"dueDate": "2027-06-30"}],
        ),
    )
    w["b"] = await create_goal(
        client,
        goal_body(
            {"reference": f"Group/{w['grp']}"},
            lifecycleStatus="completed",
            achievementStatus=concept(ACHIEVEMENT, "achieved"),
            category=[concept(GOAL_CATEGORY, "behavioral")],
            startDate="2026-06",
            target=[{"dueDate": "2026-03-01"}],
        ),
    )
    w["c"] = await create_goal(
        client,
        goal_body(
            {"reference": f"Organization/{w['org']}"},
            lifecycleStatus="proposed",
            startCodeableConcept=concept("http://snomed.info/sct", "32485007"),
            target=[{"dueDuration": {"value": 6, "unit": "mo"}}],
        ),
    )
    w["d"] = await create_goal(
        client,
        goal_body(
            {
                "identifier": {"system": "urn:subj", "value": "S-9"},
                "display": "Someone",
            },
            lifecycleStatus="on-hold",
            identifier=[{"system": GOAL_IDS, "value": "G-D"}],
            achievementStatus={"text": "Stalled"},
        ),
    )
    w["e"] = await create_goal(
        client,
        goal_body(
            {"reference": f"Patient/{w['p2']}"},
            lifecycleStatus="entered-in-error",
            category=[{"text": "Lifestyle"}],
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


# -- _id / _lastUpdated / lifecycle-status ----------------------------------------------------


async def test_id(client, world):
    assert await _keys(client, world, _id=str(world["a"])) == {"a"}
    assert await _keys(client, world, _id="999999") == set()
    assert await _keys(client, world, **{"_id:not": str(world["a"])}) == ALL - {"a"}


async def test_last_updated(client, world):
    assert await _keys(client, world, _lastUpdated="ge2020-01-01") == ALL
    assert await _keys(client, world, _lastUpdated="lt2020-01-01") == set()


async def test_lifecycle_status(client, world):
    assert await _keys(client, world, **{"lifecycle-status": "active"}) == {"a"}
    assert await _keys(client, world, **{"lifecycle-status": "on-hold"}) == {
        "d"
    }  # the real FHIR code
    assert await _keys(client, world, **{"lifecycle-status": "entered-in-error"}) == {
        "e"
    }
    assert await _keys(client, world, **{"lifecycle-status": "active,completed"}) == {
        "a",
        "b",
    }
    assert await _keys(
        client,
        world,
        **{"lifecycle-status": "http://hl7.org/fhir/goal-status|proposed"},
    ) == {"c"}
    assert (
        await _keys(client, world, **{"lifecycle-status": "http://wrong|active"})
        == set()
    )
    assert await _keys(client, world, **{"lifecycle-status": "no-such-code"}) == set()
    assert await _keys(client, world, **{"lifecycle-status:not": "active"}) == ALL - {
        "a"
    }
    assert await _keys(client, world, **{"lifecycle-status:missing": "true"}) == set()


# -- achievement-status / category / identifier ----------------------------------------------


async def test_achievement_status(client, world):
    assert await _keys(client, world, **{"achievement-status": "in-progress"}) == {"a"}
    assert await _keys(
        client, world, **{"achievement-status": f"{ACHIEVEMENT}|achieved"}
    ) == {"b"}
    assert (
        await _keys(client, world, **{"achievement-status": "http://wrong|achieved"})
        == set()
    )
    assert await _keys(client, world, **{"achievement-status:text": "stalled"}) == {
        "d"
    }  # a text-only concept is found
    assert await _keys(client, world, **{"achievement-status:text": "in progress"}) == {
        "a"
    }  # Coding.display
    assert await _keys(client, world, **{"achievement-status:missing": "true"}) == {
        "c",
        "e",
    }


async def test_category_reads_every_entry(client, world):
    assert await _keys(client, world, category="dietary") == {"a"}
    assert await _keys(client, world, category="nursing") == {
        "a"
    }  # the second category of the same goal
    assert await _keys(client, world, category=f"{GOAL_CATEGORY}|behavioral") == {"b"}
    assert await _keys(client, world, **{"category:text": "lifestyle"}) == {"e"}
    assert await _keys(client, world, **{"category:missing": "true"}) == {"c", "d"}


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="G-A") == {"a"}
    assert await _keys(client, world, identifier=f"{GOAL_IDS}|G-D") == {"d"}
    assert await _keys(client, world, identifier="G-A,G-D") == {"a", "d"}
    assert await _keys(client, world, identifier="urn:wrong|G-A") == set()
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|FILL|G-A"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|FILL|G-D"})
        == set()
    )
    assert await _keys(client, world, **{"identifier:text": "goal id"}) == {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {
        "b",
        "c",
        "e",
    }


# -- start-date / target-date ----------------------------------------------------------------


async def test_start_date(client, world):
    assert await _keys(client, world, **{"start-date": "2026-01-15"}) == {"a"}
    assert await _keys(client, world, **{"start-date": "2026-01"}) == {"a"}
    assert await _keys(client, world, **{"start-date": "2026-06"}) == {
        "b"
    }  # a partial date covers its precision
    assert await _keys(client, world, **{"start-date": "ge2026-01-01"}) == {"a", "b"}
    assert await _keys(client, world, **{"start-date": "lt2026-02-01"}) == {"a"}
    assert await _keys(client, world, **{"start-date": "sa2026-02-01"}) == {"b"}
    assert await _keys(client, world, **{"start-date": "eb2026-02-01"}) == {"a"}
    # a startCodeableConcept is not a date, so it counts as missing
    assert await _keys(client, world, **{"start-date:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


async def test_target_date_reads_every_target(client, world):
    assert await _keys(client, world, **{"target-date": "2026-12-31"}) == {"a"}
    assert await _keys(client, world, **{"target-date": "2027-06-30"}) == {
        "a"
    }  # the second target of the same goal
    assert await _keys(client, world, **{"target-date": "le2026-12-31"}) == {"a", "b"}
    assert await _keys(client, world, **{"target-date": "lt2026-06-01"}) == {"b"}
    assert await _keys(client, world, **{"target-date": "gt2027-01-01"}) == {"a"}
    # a dueDuration is not a date, so it counts as missing
    assert await _keys(client, world, **{"target-date:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


# -- subject / patient -----------------------------------------------------------------------


async def test_subject_is_multi_target(client, world):
    assert (
        await _status(client, subject=str(world["p1"])) == 400
    )  # a bare id is ambiguous
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


# -- chaining --------------------------------------------------------------------------------


async def test_chains(client, world):
    assert await _keys(client, world, **{"patient.active": "true"}) == {"a", "e"}
    assert await _keys(client, world, **{"subject:Patient.active": "true"}) == {
        "a",
        "e",
    }
    assert await _keys(client, world, **{"subject:Group.type": "person"}) == {"b"}
    assert await _keys(client, world, **{"subject:Organization.name": "Wellness"}) == {
        "c"
    }
    assert await _keys(client, world, **{"subject:Organization.name": "Nope"}) == set()


async def test_bad_chains_are_400(client, world):
    assert await _status(client, **{"patient.nonsense": "x"}) == 400
    assert (
        await _status(client, **{"subject.active": "x"}) == 400
    )  # an untyped multi-target cannot be chained
    assert (
        await _status(client, **{"subject:Device.name": "x"}) == 400
    )  # Device is not a target of subject
    assert await _status(client, **{"lifecycle-status.x": "y"}) == 400
    assert await _status(client, **{"start-date.x": "y"}) == 400


# -- _sort / _count / _offset / _total -------------------------------------------------------


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "achievement-status",
        "category",
        "identifier",
        "lifecycle-status",
        "patient",
        "start-date",
        "subject",
        "target-date",
        "_id",
    ):
        assert (await _search(client, _sort=key))["total"] == 5, key


async def test_sort_by_start_date(client, world):
    async def ids(**params):
        return [
            int(e["resource"]["id"]) for e in (await _search(client, **params))["entry"]
        ]

    assert await ids(**{"start-date:missing": "false", "_sort": "start-date"}) == [
        world["a"],
        world["b"],
    ]
    assert await ids(**{"start-date:missing": "false", "_sort": "-start-date"}) == [
        world["b"],
        world["a"],
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
    resource = (
        await _search(client, _elements="lifecycleStatus", _id=str(world["a"]))
    )["entry"][0]["resource"]
    assert resource["lifecycleStatus"] == "active"
    assert "target" not in resource and "category" not in resource


async def test_summary_true_drops_non_summary_elements(client, world):
    resource = (await _search(client, _summary="true", _id=str(world["a"])))["entry"][
        0
    ]["resource"]
    assert resource["lifecycleStatus"] == "active" and "subject" in resource
    assert "note" not in resource and "addresses" not in resource


# -- _include / _revinclude ------------------------------------------------------------------


async def test_include_patient_and_subject(client, world):
    ids = ",".join(str(world[k]) for k in KEYS)
    bundle = await _search(client, _id=ids, _include="Goal:patient")
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }
    bundle = await _search(client, _id=ids, _include="Goal:subject")
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }
    assert _of_type(bundle, "Group", "include") == {str(world["grp"])}
    assert _of_type(bundle, "Organization", "include") == {str(world["org"])}
    bundle = await _search(client, _id=ids, _include="Goal:subject:Group")
    assert _of_type(bundle, "Patient", "include") == set()
    assert _of_type(bundle, "Group", "include") == {str(world["grp"])}


async def test_revinclude_on_the_resources_a_goal_points_at(client, world):
    bundle = await _other(
        client,
        "patients",
        _id=f"{world['p1']},{world['p2']}",
        _revinclude="Goal:patient",
    )
    assert _of_type(bundle, "Goal", "include") == {str(world["a"]), str(world["e"])}
    bundle = await _other(
        client, "patients", _id=str(world["p1"]), _revinclude="Goal:subject"
    )
    assert _of_type(bundle, "Goal", "include") == {str(world["a"])}
    bundle = await _other(
        client, "groups", _id=str(world["grp"]), _revinclude="Goal:subject"
    )
    assert _of_type(bundle, "Goal", "include") == {str(world["b"])}
    bundle = await _other(
        client, "organizations", _id=str(world["org"]), _revinclude="Goal:subject"
    )
    assert _of_type(bundle, "Goal", "include") == {str(world["c"])}


async def test_care_plan_names_a_goal(client, world):
    """CarePlan.goal is Reference(Goal): searchable, chained, `_include`d, and the reverse
    `_revinclude=CarePlan:goal` is declared on Goal."""
    plans = f"{API}/care-plans/"
    plan = (
        await client.post(
            plans,
            json={
                "status": "active",
                "intent": "plan",
                "subject": {"reference": f"Patient/{world['p1']}"},
                "goal": [{"reference": f"Goal/{world['a']}"}],
            },
        )
    ).json()["id"]
    chained = await _other(client, "care-plans", **{"goal.lifecycle-status": "active"})
    assert {e["resource"]["id"] for e in chained["entry"]} == {plan}
    assert (
        await _other(client, "care-plans", **{"goal.lifecycle-status": "completed"})
    ).get("entry") is None
    bundle = await _other(client, "care-plans", _id=plan, _include="CarePlan:goal")
    assert _of_type(bundle, "Goal", "include") == {str(world["a"])}
    bundle = await _search(client, _id=str(world["a"]), _revinclude="CarePlan:goal")
    assert _of_type(bundle, "CarePlan", "include") == {plan}


# -- combination rules / lenient vs strict ---------------------------------------------------


async def test_params_are_anded(client, world):
    assert await _keys(
        client, world, **{"lifecycle-status": "active", "category": "dietary"}
    ) == {"a"}
    assert (
        await _keys(
            client, world, **{"lifecycle-status": "completed", "category": "dietary"}
        )
        == set()
    )
    assert await _keys(
        client, world, patient=str(world["p1"]), **{"start-date": "ge2026-01-01"}
    ) == {"a"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"subject:text": "x"}) == 400
    assert await _status(client, **{"start-date:exact": "2020"}) == 400
    assert await _status(client, **{"identifier:below": "x"}) == 400
    assert await _status(client, **{"lifecycle-status:text": "x"}) == 400
    assert await _status(client, **{"start-date": "banana"}) == 400
    assert await _status(client, **{"target-date": "banana"}) == 400


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
        BASE + "/_search",
        data={"lifecycle-status": "completed", "category": "behavioral"},
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, identifier="G-D")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/goals/{world['d']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "Goal"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
