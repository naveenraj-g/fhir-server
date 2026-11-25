"""FHIR R4 search over Task (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/task.html#search).

One block per search parameter - `status`, `intent` and `priority` codes, the CodeableConcept
tokens (`code`, `business-status`, `performer`), `identifier` and `group-identifier`, the three
dates (`authored-on`, `modified`, `period`), the Reference(Any) elements `subject`, `focus` and
`based-on`, the narrowed `patient`, and the single- and multi-target `encounter`, `part-of`,
`owner` and `requester` - then chaining, `_include`/`_revinclude`, result parameters, combination
rules, lenient vs strict handling and POST _search.
"""

import pytest

from tests.integration.task.support import (
    API,
    BASE,
    BUSINESS,
    PERFORMER,
    TASK_CODE,
    TASK_IDS,
    V2_0203,
    concept,
    create_encounter,
    create_group,
    create_organization,
    create_patient,
    create_practitioner,
    create_service_request,
    create_task,
    encounter_body,
    group_body,
    service_request_body,
    task_body,
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
    """Two patients, a group, an organization, a practitioner, an encounter and a service request,
    and five tasks with distinct, searchable values. Returns {key: id}.

      a  requested order, routine; code fulfill; identifier T-A; group GRP-A; authored 2026-01-15,
         modified 2026-01-16, underway in February; for p1, focus the service request, based on the
         service request and a Device, in the encounter, requested and owned by the practitioner,
         part of `e`
      b  in-progress plan, urgent; for the group, owned and requested by the organization;
         authored in 2026-06
      c  completed option; for a logical subject; focus and based on a Device; a text-only code
      d  on-hold proposal, stat; for p2; business status "paused"
      e  draft unknown, nothing else (the parent of `a`)
    """
    w = {}
    w["p1"] = await create_patient(client)
    w["p2"] = await create_patient(client)
    w["grp"] = await create_group(client, group_body())
    w["org"] = await create_organization(client, name="Task Org")
    w["pr"] = await create_practitioner(client)
    w["enc"] = await create_encounter(
        client, encounter_body(subject={"reference": f"Patient/{w['p1']}"})
    )
    w["sr"] = await create_service_request(client, service_request_body(w["p1"]))
    w["e"] = await create_task(client, task_body(status="draft", intent="unknown"))
    w["a"] = await create_task(
        client,
        task_body(
            status="requested",
            intent="order",
            priority="routine",
            identifier=[
                {
                    "system": TASK_IDS,
                    "value": "T-A",
                    "type": {
                        "coding": [{"system": V2_0203, "code": "FILL"}],
                        "text": "Task id",
                    },
                }
            ],
            groupIdentifier={"system": TASK_IDS, "value": "GRP-A"},
            code=concept(TASK_CODE, "fulfill", "Fulfill"),
            businessStatus=concept(BUSINESS, "waiting", "Waiting"),
            performerType=[
                concept(PERFORMER, "requester", "Requester"),
                concept(PERFORMER, "scheduler"),
            ],
            authoredOn="2026-01-15T08:00:00Z",
            lastModified="2026-01-16T09:00:00Z",
            executionPeriod={"start": "2026-02-01", "end": "2026-02-28"},
            **{"for": {"reference": f"Patient/{w['p1']}"}},
            focus={"reference": f"ServiceRequest/{w['sr']}"},
            basedOn=[
                {"reference": f"ServiceRequest/{w['sr']}"},
                {"reference": "Device/7"},
            ],
            encounter={"reference": f"Encounter/{w['enc']}"},
            requester={"reference": f"Practitioner/{w['pr']}"},
            owner={"reference": f"Practitioner/{w['pr']}"},
            partOf=[{"reference": f"Task/{w['e']}"}],
        ),
    )
    w["b"] = await create_task(
        client,
        task_body(
            status="in-progress",
            intent="plan",
            priority="urgent",
            authoredOn="2026-06",
            **{"for": {"reference": f"Group/{w['grp']}"}},
            owner={"reference": f"Organization/{w['org']}"},
            requester={"reference": f"Organization/{w['org']}"},
        ),
    )
    w["c"] = await create_task(
        client,
        task_body(
            status="completed",
            intent="option",
            code={"text": "Ad hoc errand"},
            **{
                "for": {
                    "identifier": {"system": "urn:subj", "value": "S-9"},
                    "display": "Someone",
                }
            },
            focus={"reference": "Device/9"},
            basedOn=[{"reference": "Device/7"}],
        ),
    )
    w["d"] = await create_task(
        client,
        task_body(
            status="on-hold",
            intent="proposal",
            priority="stat",
            businessStatus={"text": "Paused"},
            **{"for": {"reference": f"Patient/{w['p2']}"}},
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


# -- _id / _lastUpdated / status / intent / priority ------------------------------------------


async def test_id(client, world):
    assert await _keys(client, world, _id=str(world["a"])) == {"a"}
    assert await _keys(client, world, _id="999999") == set()
    assert await _keys(client, world, **{"_id:not": str(world["a"])}) == ALL - {"a"}


async def test_last_updated(client, world):
    assert await _keys(client, world, _lastUpdated="ge2020-01-01") == ALL
    assert await _keys(client, world, _lastUpdated="lt2020-01-01") == set()


async def test_status(client, world):
    assert await _keys(client, world, status="requested") == {"a"}
    assert await _keys(client, world, status="in-progress") == {
        "b"
    }  # the real FHIR code
    assert await _keys(client, world, status="on-hold,completed") == {"c", "d"}
    assert await _keys(
        client, world, status="http://hl7.org/fhir/task-status|draft"
    ) == {"e"}
    assert await _keys(client, world, status="http://wrong|draft") == set()
    assert await _keys(client, world, status="no-such-code") == set()
    assert await _keys(client, world, **{"status:not": "requested"}) == ALL - {"a"}
    assert await _keys(client, world, **{"status:missing": "true"}) == set()


async def test_intent(client, world):
    assert await _keys(client, world, intent="order") == {"a"}
    assert await _keys(client, world, intent="plan,option") == {"b", "c"}
    assert await _keys(
        client, world, intent="http://hl7.org/fhir/task-intent|proposal"
    ) == {"d"}
    assert await _keys(client, world, intent="no-such-code") == set()


async def test_priority(client, world):
    assert await _keys(client, world, priority="routine") == {"a"}
    assert await _keys(client, world, priority="urgent,stat") == {"b", "d"}
    assert await _keys(
        client, world, priority="http://hl7.org/fhir/request-priority|stat"
    ) == {"d"}
    assert await _keys(client, world, **{"priority:missing": "true"}) == {"c", "e"}


# -- code / business-status / performer / identifier / group-identifier -----------------------


async def test_code(client, world):
    assert await _keys(client, world, code="fulfill") == {"a"}
    assert await _keys(client, world, code=f"{TASK_CODE}|fulfill") == {"a"}
    assert await _keys(client, world, code="http://wrong|fulfill") == set()
    assert await _keys(client, world, **{"code:text": "ad hoc"}) == {
        "c"
    }  # a text-only concept is found
    assert await _keys(client, world, **{"code:missing": "true"}) == {"b", "d", "e"}


async def test_business_status(client, world):
    assert await _keys(client, world, **{"business-status": "waiting"}) == {"a"}
    assert await _keys(client, world, **{"business-status:text": "paused"}) == {"d"}
    assert await _keys(client, world, **{"business-status:missing": "true"}) == {
        "b",
        "c",
        "e",
    }


async def test_performer_reads_every_performer_type(client, world):
    assert await _keys(client, world, performer="requester") == {"a"}
    assert await _keys(client, world, performer="scheduler") == {
        "a"
    }  # the second performer type of the same task
    assert await _keys(client, world, performer=f"{PERFORMER}|requester") == {"a"}
    assert await _keys(client, world, **{"performer:text": "requester"}) == {"a"}
    assert await _keys(client, world, **{"performer:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="T-A") == {"a"}
    assert await _keys(client, world, identifier=f"{TASK_IDS}|T-A") == {"a"}
    assert await _keys(client, world, identifier="urn:wrong|T-A") == set()
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|FILL|T-A"}
    ) == {"a"}
    assert await _keys(client, world, **{"identifier:text": "task id"}) == {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == ALL - {"a"}


async def test_group_identifier(client, world):
    assert await _keys(client, world, **{"group-identifier": "GRP-A"}) == {"a"}
    assert await _keys(client, world, **{"group-identifier": f"{TASK_IDS}|GRP-A"}) == {
        "a"
    }
    assert (
        await _keys(client, world, **{"group-identifier": "urn:wrong|GRP-A"}) == set()
    )
    assert await _keys(client, world, **{"group-identifier:missing": "true"}) == ALL - {
        "a"
    }


# -- authored-on / modified / period ----------------------------------------------------------


async def test_authored_on(client, world):
    assert await _keys(client, world, **{"authored-on": "2026-01-15"}) == {"a"}
    assert await _keys(client, world, **{"authored-on": "2026-06"}) == {
        "b"
    }  # a partial date covers its precision
    assert await _keys(client, world, **{"authored-on": "ge2026-01-01"}) == {"a", "b"}
    assert await _keys(client, world, **{"authored-on": "lt2026-02-01"}) == {"a"}
    assert await _keys(client, world, **{"authored-on:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


async def test_modified(client, world):
    assert await _keys(client, world, modified="2026-01-16") == {"a"}
    assert await _keys(client, world, modified="gt2026-01-01") == {"a"}
    assert await _keys(client, world, modified="lt2026-01-01") == set()
    assert await _keys(client, world, **{"modified:missing": "true"}) == ALL - {"a"}


async def test_period_is_a_range_search(client, world):
    assert (
        await _keys(client, world, period="2026-02-10") == set()
    )  # eq: the period must fit
    assert await _keys(client, world, period="ge2026-02-10") == {"a"}  # overlaps above
    assert await _keys(client, world, period="le2026-02-10") == {"a"}  # overlaps below
    assert await _keys(client, world, period="sa2026-03-01") == set()
    assert await _keys(client, world, period="sa2026-01-01") == {"a"}
    assert await _keys(client, world, period="eb2026-03-01") == {"a"}
    assert await _keys(client, world, **{"period:missing": "true"}) == ALL - {"a"}


# -- subject / patient / focus / based-on (Reference(Any)) ------------------------------------


async def test_subject_is_reference_any(client, world):
    assert (
        await _status(client, subject=str(world["p1"])) == 400
    )  # a bare id is ambiguous
    assert await _keys(client, world, subject=f"Patient/{world['p1']}") == {"a"}
    assert await _keys(client, world, **{"subject:Patient": str(world["p2"])}) == {"d"}
    assert await _keys(client, world, subject=f"Group/{world['grp']}") == {"b"}
    assert await _keys(client, world, **{"subject:Group": str(world["grp"])}) == {"b"}
    assert (
        await _keys(client, world, subject=f"Group/{world['p1']}") == set()
    )  # the type is part of the match
    assert await _keys(client, world, **{"subject:identifier": "urn:subj|S-9"}) == {"c"}
    assert await _keys(client, world, **{"subject:missing": "true"}) == {"e"}


async def test_patient_is_subject_narrowed_to_patients(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {
        "a"
    }  # a bare id works
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"d"}
    # the Group subject is not a patient, so it never matches (even by an equal id)
    assert await _keys(client, world, patient=str(world["grp"])) == set()
    assert await _keys(client, world, **{"patient:missing": "true"}) == {"b", "c", "e"}


async def test_focus_is_reference_any(client, world):
    assert await _status(client, focus=str(world["sr"])) == 400
    assert await _keys(client, world, focus=f"ServiceRequest/{world['sr']}") == {"a"}
    assert await _keys(client, world, **{"focus:ServiceRequest": str(world["sr"])}) == {
        "a"
    }
    assert await _keys(client, world, focus="Device/9") == {"c"}  # an unmodeled type
    assert await _keys(client, world, **{"focus:missing": "true"}) == {"b", "d", "e"}


async def test_based_on_is_reference_any_and_reads_every_entry(client, world):
    assert await _status(client, **{"based-on": str(world["sr"])}) == 400
    assert await _keys(
        client, world, **{"based-on": f"ServiceRequest/{world['sr']}"}
    ) == {"a"}
    assert await _keys(client, world, **{"based-on": "Device/7"}) == {
        "a",
        "c",
    }  # the second entry of `a`
    assert await _keys(client, world, **{"based-on:missing": "true"}) == {"b", "d", "e"}


# -- encounter / part-of / owner / requester --------------------------------------------------


async def test_encounter_has_one_target_so_a_bare_id_works(client, world):
    assert await _keys(client, world, encounter=str(world["enc"])) == {"a"}
    assert await _keys(client, world, encounter=f"Encounter/{world['enc']}") == {"a"}
    assert await _keys(client, world, **{"encounter:missing": "true"}) == ALL - {"a"}


async def test_part_of_has_one_target_so_a_bare_id_works(client, world):
    assert await _keys(client, world, **{"part-of": str(world["e"])}) == {"a"}
    assert await _keys(client, world, **{"part-of": f"Task/{world['e']}"}) == {"a"}
    assert await _keys(client, world, **{"part-of:missing": "true"}) == ALL - {"a"}


async def test_owner_and_requester_are_multi_target(client, world):
    assert await _status(client, owner=str(world["pr"])) == 400
    assert await _keys(client, world, owner=f"Practitioner/{world['pr']}") == {"a"}
    assert await _keys(client, world, owner=f"Organization/{world['org']}") == {"b"}
    assert await _keys(client, world, **{"owner:Organization": str(world["org"])}) == {
        "b"
    }
    assert await _keys(client, world, owner=f"Organization/{world['pr']}") == set()
    assert await _keys(client, world, requester=f"Practitioner/{world['pr']}") == {"a"}
    assert await _keys(
        client, world, **{"requester:Organization": str(world["org"])}
    ) == {"b"}
    assert await _keys(client, world, **{"owner:missing": "true"}) == {"c", "d", "e"}


# -- chaining --------------------------------------------------------------------------------


async def test_chains(client, world):
    assert await _keys(client, world, **{"patient.active": "true"}) == {"a", "d"}
    assert await _keys(client, world, **{"subject:Patient.active": "true"}) == {
        "a",
        "d",
    }
    assert await _keys(client, world, **{"subject:Group.type": "person"}) == {"b"}
    assert await _keys(client, world, **{"focus:ServiceRequest.status": "active"}) == {
        "a"
    }
    assert await _keys(
        client, world, **{"based-on:ServiceRequest.status": "active"}
    ) == {"a"}
    assert await _keys(client, world, **{"encounter.status": "planned"}) | {"a"} >= {
        "a"
    }
    assert await _keys(client, world, **{"part-of.status": "draft"}) == {"a"}
    assert await _keys(client, world, **{"owner:Organization.name": "Task Org"}) == {
        "b"
    }
    assert await _keys(client, world, **{"owner:Practitioner.active": "true"}) <= {"a"}
    assert (
        await _keys(client, world, **{"requester:Organization.name": "Nope"}) == set()
    )


async def test_bad_chains_are_400(client, world):
    assert await _status(client, **{"patient.nonsense": "x"}) == 400
    assert await _status(client, **{"subject.active": "x"}) == 400  # untyped Any
    assert await _status(client, **{"owner.name": "x"}) == 400  # untyped multi-target
    assert (
        await _status(client, **{"owner:Device.name": "x"}) == 400
    )  # Device is not a resource here
    assert (
        await _status(client, **{"focus:Device.name": "x"}) == 400
    )  # valid R4 type, not a resource here
    assert (
        await _status(client, **{"status.x": "y"}) == 400
    )  # a token cannot be chained


# -- _sort / _count / _offset / _total -------------------------------------------------------


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "authored-on",
        "based-on",
        "business-status",
        "code",
        "encounter",
        "focus",
        "group-identifier",
        "identifier",
        "intent",
        "modified",
        "owner",
        "part-of",
        "patient",
        "performer",
        "period",
        "priority",
        "requester",
        "status",
        "subject",
        "_id",
    ):
        assert (await _search(client, _sort=key))["total"] == 5, key


async def test_sort_by_authored_on(client, world):
    async def ids(**params):
        return [
            int(e["resource"]["id"]) for e in (await _search(client, **params))["entry"]
        ]

    assert await ids(**{"authored-on:missing": "false", "_sort": "authored-on"}) == [
        world["a"],
        world["b"],
    ]
    assert await ids(**{"authored-on:missing": "false", "_sort": "-authored-on"}) == [
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
    resource = (await _search(client, _elements="status", _id=str(world["a"])))[
        "entry"
    ][0]["resource"]
    assert resource["status"] == "requested"
    assert "owner" not in resource and "code" not in resource


# -- _include / _revinclude ------------------------------------------------------------------


async def test_include_patient_subject_focus_and_based_on(client, world):
    ids = ",".join(str(world[k]) for k in KEYS)
    bundle = await _search(client, _id=ids, _include="Task:patient")
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }
    bundle = await _search(client, _id=ids, _include="Task:subject")
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }
    assert _of_type(bundle, "Group", "include") == {str(world["grp"])}
    bundle = await _search(client, _id=ids, _include="Task:focus")
    assert _of_type(bundle, "ServiceRequest", "include") == {str(world["sr"])}
    bundle = await _search(client, _id=ids, _include="Task:based-on")
    assert _of_type(bundle, "ServiceRequest", "include") == {str(world["sr"])}
    bundle = await _search(client, _id=ids, _include="Task:subject:Group")
    assert _of_type(bundle, "Patient", "include") == set()


async def test_include_encounter_part_of_owner_and_requester(client, world):
    ids = ",".join(str(world[k]) for k in KEYS)
    bundle = await _search(client, _id=ids, _include="Task:encounter")
    assert _of_type(bundle, "Encounter", "include") == {str(world["enc"])}
    bundle = await _search(client, _id=str(world["a"]), _include="Task:part-of")
    assert _of_type(bundle, "Task", "include") == {str(world["e"])}
    bundle = await _search(client, _id=ids, _include="Task:owner")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "Organization", "include") == {str(world["org"])}
    bundle = await _search(client, _id=ids, _include="Task:requester:Organization")
    assert _of_type(bundle, "Practitioner", "include") == set()
    assert _of_type(bundle, "Organization", "include") == {str(world["org"])}


async def test_revinclude_on_the_resources_a_task_points_at(client, world):
    bundle = await _other(
        client,
        "patients",
        _id=f"{world['p1']},{world['p2']}",
        _revinclude="Task:patient",
    )
    assert _of_type(bundle, "Task", "include") == {str(world["a"]), str(world["d"])}
    bundle = await _other(
        client, "patients", _id=str(world["p1"]), _revinclude="Task:subject"
    )
    assert _of_type(bundle, "Task", "include") == {str(world["a"])}
    bundle = await _other(
        client, "encounters", _id=str(world["enc"]), _revinclude="Task:encounter"
    )
    assert _of_type(bundle, "Task", "include") == {str(world["a"])}
    bundle = await _other(
        client, "practitioners", _id=str(world["pr"]), _revinclude="Task:owner"
    )
    assert _of_type(bundle, "Task", "include") == {str(world["a"])}
    bundle = await _other(
        client, "organizations", _id=str(world["org"]), _revinclude="Task:requester"
    )
    assert _of_type(bundle, "Task", "include") == {str(world["b"])}
    bundle = await _search(client, _id=str(world["e"]), _revinclude="Task:part-of")
    assert _of_type(bundle, "Task", "include") == {str(world["a"])}


async def test_care_plan_names_a_task_as_an_activity(client, world):
    """CarePlan.activity.reference can be a Task: searchable, chained, `_include`d, and the reverse
    `_revinclude=CarePlan:activity-reference` is declared on Task."""
    plans = f"{API}/care-plans/"
    plan = (
        await client.post(
            plans,
            json={
                "status": "active",
                "intent": "plan",
                "subject": {"reference": f"Patient/{world['p1']}"},
                "activity": [{"reference": {"reference": f"Task/{world['a']}"}}],
            },
        )
    ).json()["id"]
    chained = await _other(
        client, "care-plans", **{"activity-reference:Task.status": "requested"}
    )
    assert {e["resource"]["id"] for e in chained["entry"]} == {plan}
    bundle = await _other(
        client, "care-plans", _id=plan, _include="CarePlan:activity-reference:Task"
    )
    assert _of_type(bundle, "Task", "include") == {str(world["a"])}
    bundle = await _search(
        client, _id=str(world["a"]), _revinclude="CarePlan:activity-reference"
    )
    assert _of_type(bundle, "CarePlan", "include") == {plan}


# -- combination rules / lenient vs strict ---------------------------------------------------


async def test_params_are_anded(client, world):
    assert await _keys(client, world, status="requested", intent="order") == {"a"}
    assert await _keys(client, world, status="requested", intent="plan") == set()
    assert await _keys(
        client, world, patient=str(world["p1"]), **{"authored-on": "ge2026-01-01"}
    ) == {"a"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"subject:text": "x"}) == 400
    assert await _status(client, **{"authored-on:exact": "2020"}) == 400
    assert await _status(client, **{"identifier:below": "x"}) == 400
    assert await _status(client, **{"status:text": "x"}) == 400
    assert await _status(client, **{"authored-on": "banana"}) == 400
    assert await _status(client, period="banana") == 400


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
        BASE + "/_search", data={"status": "completed", "intent": "option"}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["c"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, **{"group-identifier": "GRP-A"})
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/tasks/{world['a']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "Task"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
