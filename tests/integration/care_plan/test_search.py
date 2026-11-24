"""FHIR R4 search over CarePlan (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/careplan.html#search).

One block per search parameter - `status` and `intent` codes, `date` and `activity-date` Period /
Timing searches, `category`, `activity-code` and `identifier` tokens, `instantiates-canonical` /
`instantiates-uri`, the single-target `based-on` / `replaces` / `part-of` / `care-team` /
`condition` / `goal` / `encounter` references, the multi-target `subject`, `performer` and
`activity-reference` references and `patient` (a subject narrowed to Patients) - then chaining,
`_include`/`_revinclude`, result parameters, combination rules, lenient vs strict handling and
POST _search.
"""

import pytest

from tests.integration.goal.support import create_goal, goal_body
from tests.integration.care_plan.support import (
    API,
    BASE,
    CARE_PLAN_IDS,
    CATEGORY,
    SCT,
    V2_0203,
    appointment_body,
    care_plan_body,
    care_team_body,
    concept,
    condition_body,
    create_appointment,
    create_care_plan,
    create_care_team,
    create_condition,
    create_encounter,
    create_group,
    create_healthcare_service,
    create_medication_request,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_related_person,
    create_service_request,
    encounter_body,
    group_body,
    medication_request_body,
    related_person_body,
    service_request_body,
)

KEYS = ("a", "b", "c", "d", "e")
ALL = set(KEYS)
PLAN_DEFINITION = "http://example.org/fhir/PlanDefinition/diabetes"


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


def _detail(**detail) -> dict:
    return {"detail": {"status": "scheduled", **detail}}


@pytest.fixture
async def world(client):
    """The resources a care plan points at, plus five care plans with distinct, searchable values.
    Returns {key: id}.

      a  active plan for patient 1 at an encounter, covering 2026, with a care team, a condition,
         a goal, based on `e`, instantiating a versioned PlanDefinition and a URI; activities: a
         ServiceRequest reference and a detail (coded, in-progress, scheduled Feb 2026, performed
         by a practitioner and a related person)
      b  on-hold order for a group, open-ended period from 2027, part of `a`, replacing `e`;
         activities: an Appointment reference and a detail (text-coded, scheduled by a Timing in
         2027, performed by a role and a healthcare service)
      c  completed option for patient 2, covering 2020; activities: a MedicationRequest reference
         and a detail performed by patient 2
      d  entered-in-error plan with a logical subject; activities: a Task reference (not a
         resource here) and a detail scheduled by a string, performed by an external device
      e  only what R4 requires
    """
    w = {}
    w["org"] = await create_organization(client, name="Providing Org")
    w["pr"] = await create_practitioner(client)  # family "Careful"
    w["role"] = await create_practitioner_role(client)
    w["p1"] = await create_patient(
        client, {"active": True, "name": [{"family": "Windsor", "given": ["Anna"]}]}
    )
    w["p2"] = await create_patient(
        client, {"active": True, "name": [{"family": "Fairfax", "given": ["Ben"]}]}
    )
    w["rel"] = await create_related_person(client, related_person_body(w["p1"]))
    w["hs"] = await create_healthcare_service(client)
    w["grp"] = await create_group(client, group_body(type="person"))
    w["enc"] = await create_encounter(client, encounter_body())
    w["team"] = await create_care_team(client, care_team_body(status="active"))
    w["cond"] = await create_condition(client, condition_body(w["p1"]))
    w["goal"] = await create_goal(
        client, goal_body({"reference": f"Patient/{w['p1']}"}, lifecycleStatus="active")
    )
    w["sr"] = await create_service_request(client, service_request_body(w["p1"]))
    w["appt"] = await create_appointment(client, appointment_body(w["p1"]))
    w["mr"] = await create_medication_request(client, medication_request_body(w["p1"]))
    w["e"] = await create_care_plan(
        client, care_plan_body(status="draft", intent="proposal")
    )
    w["a"] = await create_care_plan(
        client,
        care_plan_body(
            w["p1"],
            status="active",
            intent="plan",
            identifier=[
                {
                    "system": CARE_PLAN_IDS,
                    "value": "CP-A",
                    "type": {
                        "coding": [{"system": V2_0203, "code": "FILL"}],
                        "text": "Plan id",
                    },
                }
            ],
            category=[concept(CATEGORY, "assess-plan", "Assessment and plan")],
            title="Diabetes",
            encounter={"reference": f"Encounter/{w['enc']}"},
            period={"start": "2026-01-01", "end": "2026-12-31"},
            basedOn=[{"reference": f"CarePlan/{w['e']}"}],
            careTeam=[{"reference": f"CareTeam/{w['team']}"}],
            addresses=[{"reference": f"Condition/{w['cond']}"}],
            goal=[{"reference": f"Goal/{w['goal']}"}],
            instantiatesCanonical=[f"{PLAN_DEFINITION}|1.0"],
            instantiatesUri=["http://example.org/protocols/diabetes"],
            activity=[
                {"reference": {"reference": f"ServiceRequest/{w['sr']}"}},
                _detail(
                    kind="ServiceRequest",
                    status="in-progress",
                    code=concept(SCT, "386053000", "Evaluation procedure"),
                    scheduledPeriod={"start": "2026-02-01", "end": "2026-02-28"},
                    performer=[
                        {"reference": f"Practitioner/{w['pr']}"},
                        {"reference": f"RelatedPerson/{w['rel']}"},
                    ],
                ),
            ],
        ),
    )
    w["b"] = await create_care_plan(
        client,
        {
            **care_plan_body(
                status="on-hold",
                intent="order",
                identifier=[{"system": CARE_PLAN_IDS, "value": "CP-B"}],
                period={"start": "2027-01-01"},
                partOf=[{"reference": f"CarePlan/{w['a']}"}],
                replaces=[{"reference": f"CarePlan/{w['e']}"}],
                instantiatesUri=["http://example.org/protocols/other"],
                activity=[
                    {"reference": {"reference": f"Appointment/{w['appt']}"}},
                    _detail(
                        code={"text": "Counselling"},
                        scheduledTiming={
                            "event": ["2027-03-01T08:00:00Z", "2027-03-15T08:00:00Z"]
                        },
                        performer=[
                            {"reference": f"PractitionerRole/{w['role']}"},
                            {"reference": f"HealthcareService/{w['hs']}"},
                        ],
                    ),
                ],
            ),
            "subject": {"reference": f"Group/{w['grp']}"},
        },
    )
    w["c"] = await create_care_plan(
        client,
        care_plan_body(
            w["p2"],
            status="completed",
            intent="option",
            category=[{"text": "Home care"}],
            period={"start": "2020-01-01", "end": "2020-12-31"},
            activity=[
                {"reference": {"reference": f"MedicationRequest/{w['mr']}"}},
                _detail(
                    status="completed",
                    performer=[{"reference": f"Patient/{w['p2']}"}],
                ),
            ],
        ),
    )
    w["d"] = await create_care_plan(
        client,
        {
            **care_plan_body(
                status="entered-in-error",
                intent="plan",
                activity=[
                    {"reference": {"reference": "Task/5"}},
                    _detail(
                        status="unknown",
                        scheduledString="next week",
                        performer=[
                            {"reference": "https://other.example.org/fhir/Device/5"}
                        ],
                    ),
                ],
            ),
            "subject": {
                "identifier": {"system": "urn:subj", "value": "S-9"},
                "display": "External",
            },
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


# -- _id / _lastUpdated ---------------------------------------------------------------------


async def test_id(client, world):
    assert await _keys(client, world, _id=str(world["a"])) == {"a"}
    assert await _keys(client, world, _id="999999") == set()
    assert await _keys(client, world, **{"_id:not": str(world["a"])}) == ALL - {"a"}


async def test_last_updated(client, world):
    assert await _keys(client, world, _lastUpdated="ge2020-01-01") == ALL
    assert await _keys(client, world, _lastUpdated="lt2020-01-01") == set()


# -- status / intent ------------------------------------------------------------------------


async def test_status(client, world):
    assert await _keys(client, world, status="active") == {"a"}
    assert await _keys(client, world, status="active,on-hold") == {"a", "b"}
    assert await _keys(
        client, world, status="http://hl7.org/fhir/request-status|completed"
    ) == {"c"}
    assert await _keys(client, world, status="urn:wrong|active") == set()
    assert await _keys(client, world, status="|active") == set()
    assert await _keys(client, world, status="retired") == set()
    assert await _keys(client, world, **{"status:not": "active"}) == ALL - {"a"}
    assert await _keys(client, world, **{"status:missing": "true"}) == set()
    assert await _keys(client, world, **{"status:missing": "false"}) == ALL


async def test_intent(client, world):
    assert await _keys(client, world, intent="plan") == {"a", "d"}
    assert await _keys(client, world, intent="order") == {"b"}
    assert await _keys(client, world, intent="proposal,option") == {"c", "e"}
    assert await _keys(
        client, world, intent="http://hl7.org/fhir/request-intent|plan"
    ) == {"a", "d"}
    assert await _keys(client, world, intent="directive") == set()
    assert await _keys(client, world, **{"intent:not": "plan"}) == ALL - {"a", "d"}


# -- date / activity-date (Period and Timing searches) --------------------------------------


async def test_date_is_a_period_search(client, world):
    assert await _keys(client, world, date="eq2026") == {"a"}
    assert await _keys(client, world, date="2020") == {"c"}
    assert await _keys(client, world, date="ge2026-06-01") == {"a", "b"}
    assert await _keys(client, world, date="le2020-06-01") == {"c"}
    assert await _keys(client, world, date="gt2027-06-01") == {"b"}  # open-ended
    assert await _keys(client, world, date="sa2026-12-31") == {"b"}
    assert await _keys(client, world, date="eb2021-01-01") == {"c"}
    for prefix in ("ge", "le", "gt", "lt", "eq"):
        found = await _keys(client, world, date=f"{prefix}2026-06-01")
        assert not found & {"d", "e"}, prefix  # no period never matches
    assert await _keys(client, world, **{"date:missing": "true"}) == {"d", "e"}


async def test_activity_date_reads_periods_and_timings(client, world):
    assert await _keys(client, world, **{"activity-date": "eq2026-02"}) == {"a"}
    assert await _keys(client, world, **{"activity-date": "ge2026-02-15"}) == {"a", "b"}
    # a Timing is the range from its earliest to its latest event
    assert await _keys(client, world, **{"activity-date": "eq2027-03"}) == {"b"}
    assert await _keys(client, world, **{"activity-date": "ge2027-01-01"}) == {"b"}
    assert await _keys(client, world, **{"activity-date": "lt2026-01-01"}) == set()
    # a `scheduledString` is not a date
    assert await _keys(client, world, **{"activity-date:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


# -- identifier / category / activity-code --------------------------------------------------


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="CP-A") == {"a"}
    assert await _keys(client, world, identifier=f"{CARE_PLAN_IDS}|CP-B") == {"b"}
    assert await _keys(client, world, identifier="CP-A,CP-B") == {"a", "b"}
    assert await _keys(client, world, identifier="urn:wrong|CP-A") == set()
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|FILL|CP-A"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|FILL|CP-B"})
        == set()
    )
    assert await _keys(client, world, **{"identifier:text": "plan id"}) == {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


async def test_category(client, world):
    assert await _keys(client, world, category="assess-plan") == {"a"}
    assert await _keys(client, world, category=f"{CATEGORY}|assess-plan") == {"a"}
    assert await _keys(client, world, category=f"{SCT}|assess-plan") == set()
    assert await _keys(client, world, **{"category:text": "home"}) == {"c"}
    assert await _keys(client, world, **{"category:not": "assess-plan"}) == ALL - {"a"}
    assert await _keys(client, world, **{"category:missing": "true"}) == {"b", "d", "e"}


async def test_activity_code_reads_every_activity(client, world):
    assert await _keys(client, world, **{"activity-code": "386053000"}) == {"a"}
    assert await _keys(client, world, **{"activity-code": f"{SCT}|386053000"}) == {"a"}
    assert await _keys(client, world, **{"activity-code:text": "counsel"}) == {"b"}
    assert await _keys(client, world, **{"activity-code": "nope"}) == set()
    assert await _keys(client, world, **{"activity-code:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


# -- instantiates-canonical / instantiates-uri ----------------------------------------------


async def test_instantiates_canonical(client, world):
    assert await _keys(
        client, world, **{"instantiates-canonical": f"{PLAN_DEFINITION}|1.0"}
    ) == {"a"}
    # an unversioned canonical matches the stored versions of that URL
    assert await _keys(
        client, world, **{"instantiates-canonical": PLAN_DEFINITION}
    ) == {"a"}
    assert (
        await _keys(
            client, world, **{"instantiates-canonical": f"{PLAN_DEFINITION}|2.0"}
        )
        == set()
    )
    assert await _keys(client, world, **{"instantiates-canonical:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }


async def test_instantiates_uri(client, world):
    assert await _keys(
        client, world, **{"instantiates-uri": "http://example.org/protocols/diabetes"}
    ) == {"a"}
    assert (
        await _keys(
            client,
            world,
            **{"instantiates-uri": "HTTP://EXAMPLE.ORG/protocols/diabetes"},
        )
        == set()
    )  # case-sensitive
    assert await _keys(
        client, world, **{"instantiates-uri:below": "http://example.org/protocols"}
    ) == {"a", "b"}
    assert await _keys(
        client,
        world,
        **{"instantiates-uri:above": "http://example.org/protocols/other/x"},
    ) == {"b"}
    assert await _keys(client, world, **{"instantiates-uri:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


# -- based-on / replaces / part-of / care-team / condition / goal / encounter ----------------


async def test_care_plan_references_have_one_target_so_a_bare_id_works(client, world):
    assert await _keys(client, world, **{"based-on": str(world["e"])}) == {"a"}
    assert await _keys(client, world, **{"based-on": f"CarePlan/{world['e']}"}) == {"a"}
    assert await _keys(client, world, replaces=str(world["e"])) == {"b"}
    assert await _keys(client, world, **{"part-of": str(world["a"])}) == {"b"}
    assert await _keys(client, world, **{"part-of": str(world["e"])}) == set()
    assert await _keys(client, world, **{"based-on:missing": "true"}) == ALL - {"a"}


async def test_care_team_condition_and_goal(client, world):
    assert await _keys(client, world, **{"care-team": str(world["team"])}) == {"a"}
    assert await _keys(client, world, condition=str(world["cond"])) == {"a"}
    assert await _keys(client, world, condition=f"Condition/{world['cond']}") == {"a"}
    assert await _keys(client, world, goal=str(world["goal"])) == {"a"}
    assert await _keys(client, world, goal=f"Goal/{world['goal']}") == {"a"}
    # Goal is a rebuilt resource: the reference chains
    assert await _keys(client, world, **{"goal.lifecycle-status": "active"}) == {"a"}
    assert await _keys(client, world, **{"goal.lifecycle-status": "completed"}) == set()
    assert await _keys(client, world, **{"goal:missing": "true"}) == ALL - {"a"}
    assert await _keys(client, world, **{"care-team:missing": "true"}) == ALL - {"a"}
    assert await _keys(client, world, **{"condition:missing": "true"}) == ALL - {"a"}


async def test_encounter_has_one_target_so_a_bare_id_works(client, world):
    assert await _keys(client, world, encounter=str(world["enc"])) == {"a"}
    assert await _keys(client, world, encounter=f"Encounter/{world['enc']}") == {"a"}
    assert await _keys(client, world, **{"encounter:missing": "true"}) == ALL - {"a"}


# -- subject / patient ----------------------------------------------------------------------


async def test_subject_is_multi_target(client, world):
    assert await _status(client, subject=str(world["p1"])) == 400  # bare id: ambiguous
    assert await _keys(client, world, subject=f"Patient/{world['p1']}") == {"a"}
    assert await _keys(client, world, **{"subject:Patient": str(world["p2"])}) == {"c"}
    assert await _keys(client, world, subject=f"Group/{world['grp']}") == {"b"}
    assert await _keys(client, world, subject=f"Group/{world['p1']}") == set()
    assert await _keys(client, world, **{"subject:identifier": "urn:subj|S-9"}) == {"d"}


async def test_patient_is_subject_narrowed_to_patients(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {
        "a"
    }  # a bare id works
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"c"}
    assert await _keys(client, world, patient=str(world["grp"])) == set()
    assert await _keys(client, world, **{"patient:missing": "true"}) == {"b", "d", "e"}


# -- performer / activity-reference ---------------------------------------------------------


async def test_performer_is_multi_target(client, world):
    assert await _status(client, performer=str(world["pr"])) == 400
    assert await _keys(client, world, performer=f"Practitioner/{world['pr']}") == {"a"}
    assert await _keys(client, world, performer=f"RelatedPerson/{world['rel']}") == {
        "a"
    }
    assert await _keys(
        client, world, performer=f"PractitionerRole/{world['role']}"
    ) == {"b"}
    assert await _keys(client, world, performer=f"HealthcareService/{world['hs']}") == {
        "b"
    }
    assert await _keys(client, world, **{"performer:Patient": str(world["p2"])}) == {
        "c"
    }
    assert await _keys(client, world, performer=f"Patient/{world['pr']}") == set()
    assert (
        await _keys(client, world, performer="Device/5") == set()
    )  # absolute URL, not Device/5
    assert await _keys(client, world, **{"performer:missing": "true"}) == {"e"}


async def test_activity_reference_is_multi_target(client, world):
    assert await _status(client, **{"activity-reference": str(world["sr"])}) == 400
    assert await _keys(
        client, world, **{"activity-reference": f"ServiceRequest/{world['sr']}"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"activity-reference:Appointment": str(world["appt"])}
    ) == {"b"}
    assert await _keys(
        client, world, **{"activity-reference": f"MedicationRequest/{world['mr']}"}
    ) == {"c"}
    # a Task is not a resource here, but the reference is still searchable by type and id
    assert await _keys(client, world, **{"activity-reference": "Task/5"}) == {"d"}
    assert (
        await _keys(
            client, world, **{"activity-reference": f"Appointment/{world['sr']}"}
        )
        == set()
    )
    assert await _keys(client, world, **{"activity-reference:missing": "true"}) == {"e"}


# -- chaining -------------------------------------------------------------------------------


async def test_chains(client, world):
    assert await _keys(client, world, **{"patient.family": "Windsor"}) == {"a"}
    assert await _keys(client, world, **{"subject:Patient.family": "Fairfax"}) == {"c"}
    assert await _keys(client, world, **{"subject:Group.type": "person"}) == {"b"}
    assert await _keys(client, world, **{"encounter.status": "in-progress"}) == {"a"}
    assert await _keys(client, world, **{"care-team.status": "active"}) == {"a"}
    assert await _keys(client, world, **{"condition.patient": str(world["p1"])}) == {
        "a"
    }
    assert await _keys(client, world, **{"based-on.status": "draft"}) == {"a"}
    assert await _keys(client, world, **{"part-of.status": "active"}) == {"b"}
    assert await _keys(client, world, **{"replaces.intent": "proposal"}) == {"b"}
    assert await _keys(
        client, world, **{"performer:Practitioner.family": "Careful"}
    ) == {"a"}
    assert await _keys(client, world, **{"performer:Patient.family": "Fairfax"}) == {
        "c"
    }
    assert await _keys(
        client, world, **{"activity-reference:ServiceRequest.status": "active"}
    ) == {"a"}


async def test_bad_chains_are_400(client, world):
    assert (
        await _status(client, **{"subject.family": "x"}) == 400
    )  # untyped multi-target
    assert await _status(client, **{"performer.family": "x"}) == 400
    assert await _status(client, **{"activity-reference.status": "x"}) == 400
    assert (
        await _status(client, **{"performer:Device.x": "x"}) == 400
    )  # not searchable here
    assert await _status(client, **{"activity-reference:Task.x": "x"}) == 400
    assert (
        await _status(client, **{"goal.nonsense": "x"}) == 400
    )  # unknown Goal parameter
    assert (
        await _status(client, **{"category.x": "y"}) == 400
    )  # a token cannot be chained


# -- _sort / _count / _offset / _total ------------------------------------------------------


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "activity-code",
        "activity-date",
        "activity-reference",
        "based-on",
        "care-team",
        "category",
        "condition",
        "date",
        "encounter",
        "goal",
        "identifier",
        "instantiates-canonical",
        "instantiates-uri",
        "intent",
        "part-of",
        "patient",
        "performer",
        "replaces",
        "status",
        "subject",
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
    resource = (await _search(client, _elements="title", _id=str(world["a"])))["entry"][
        0
    ]["resource"]
    assert resource["title"] == "Diabetes"
    assert "activity" not in resource and "category" not in resource


# -- _include / _revinclude -----------------------------------------------------------------


async def test_include_subject_encounter_and_references(client, world):
    ids = ",".join(str(world[k]) for k in KEYS)
    bundle = await _search(client, _id=ids, _include="CarePlan:patient")
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }
    bundle = await _search(client, _id=ids, _include="CarePlan:subject")
    assert _of_type(bundle, "Group", "include") == {str(world["grp"])}
    bundle = await _search(client, _id=ids, _include="CarePlan:subject:Group")
    assert _of_type(bundle, "Patient", "include") == set()
    bundle = await _search(
        client,
        _id=ids,
        _include="CarePlan:encounter",
    )
    assert _of_type(bundle, "Encounter", "include") == {str(world["enc"])}
    bundle = await _search(client, _id=ids, _include="CarePlan:care-team")
    assert _of_type(bundle, "CareTeam", "include") == {str(world["team"])}
    bundle = await _search(client, _id=ids, _include="CarePlan:condition")
    assert _of_type(bundle, "Condition", "include") == {str(world["cond"])}
    bundle = await _search(
        client, _id=f"{world['a']},{world['b']}", _include="CarePlan:based-on"
    )
    assert _of_type(bundle, "CarePlan", "include") == {str(world["e"])}
    bundle = await _search(client, _id=str(world["b"]), _include="CarePlan:part-of")
    assert _of_type(bundle, "CarePlan", "include") == {str(world["a"])}


async def test_include_performer_and_activity_reference(client, world):
    ids = ",".join(str(world[k]) for k in KEYS)
    bundle = await _search(client, _id=ids, _include="CarePlan:performer")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "RelatedPerson", "include") == {str(world["rel"])}
    assert _of_type(bundle, "PractitionerRole", "include") == {str(world["role"])}
    assert _of_type(bundle, "HealthcareService", "include") == {str(world["hs"])}
    assert str(world["p2"]) in _of_type(bundle, "Patient", "include")
    bundle = await _search(client, _id=ids, _include="CarePlan:performer:Practitioner")
    assert _of_type(bundle, "RelatedPerson", "include") == set()
    bundle = await _search(client, _id=ids, _include="CarePlan:activity-reference")
    assert _of_type(bundle, "ServiceRequest", "include") == {str(world["sr"])}
    assert _of_type(bundle, "Appointment", "include") == {str(world["appt"])}
    assert _of_type(bundle, "MedicationRequest", "include") == {str(world["mr"])}


async def test_revinclude_on_the_resources_a_care_plan_points_at(client, world):
    def includes(bundle):
        return _of_type(bundle, "CarePlan", "include")

    p1 = str(world["p1"])
    assert includes(
        await _other(client, "patients", _id=p1, _revinclude="CarePlan:patient")
    ) == {str(world["a"])}
    assert includes(
        await _other(
            client, "patients", _id=str(world["p2"]), _revinclude="CarePlan:subject"
        )
    ) == {str(world["c"])}
    assert includes(
        await _other(
            client, "patients", _id=str(world["p2"]), _revinclude="CarePlan:performer"
        )
    ) == {str(world["c"])}
    assert includes(
        await _other(
            client, "groups", _id=str(world["grp"]), _revinclude="CarePlan:subject"
        )
    ) == {str(world["b"])}
    assert includes(
        await _other(
            client,
            "encounters",
            _id=str(world["enc"]),
            _revinclude="CarePlan:encounter",
        )
    ) == {str(world["a"])}
    assert includes(
        await _other(
            client,
            "care-teams",
            _id=str(world["team"]),
            _revinclude="CarePlan:care-team",
        )
    ) == {str(world["a"])}
    assert includes(
        await _other(
            client,
            "conditions",
            _id=str(world["cond"]),
            _revinclude="CarePlan:condition",
        )
    ) == {str(world["a"])}
    for path, key, expected in (
        ("practitioners", "pr", "a"),
        ("related-persons", "rel", "a"),
        ("practitioner-roles", "role", "b"),
        ("healthcare-services", "hs", "b"),
    ):
        assert includes(
            await _other(
                client, path, _id=str(world[key]), _revinclude="CarePlan:performer"
            )
        ) == {str(world[expected])}, path
    for path, key, expected in (
        ("service-requests", "sr", "a"),
        ("appointments", "appt", "b"),
        ("medication-requests", "mr", "c"),
    ):
        assert includes(
            await _other(
                client,
                path,
                _id=str(world[key]),
                _revinclude="CarePlan:activity-reference",
            )
        ) == {str(world[expected])}, path
    # and a care plan that is based on / replaced by / part of another points back at it
    assert includes(
        await _search(client, _id=str(world["e"]), _revinclude="CarePlan:based-on")
    ) == {str(world["a"])}
    assert includes(
        await _search(client, _id=str(world["e"]), _revinclude="CarePlan:replaces")
    ) == {str(world["b"])}
    assert includes(
        await _search(client, _id=str(world["a"]), _revinclude="CarePlan:part-of")
    ) == {str(world["b"])}


# -- combination rules / lenient vs strict --------------------------------------------------


async def test_params_are_anded(client, world):
    assert await _keys(client, world, status="active", intent="plan") == {"a"}
    assert await _keys(client, world, status="active", intent="order") == set()
    assert await _keys(client, world, patient=str(world["p1"]), status="active") == {
        "a"
    }
    # the activity parameters are independent: any activity may match each
    assert await _keys(
        client,
        world,
        **{
            "activity-code": "386053000",
            "activity-reference": f"ServiceRequest/{world['sr']}",
        },
    ) == {"a"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"performer:text": "x"}) == 400
    assert await _status(client, **{"identifier:below": "x"}) == 400
    assert await _status(client, date="notadate") == 400
    assert await _status(client, **{"activity-date": "notadate"}) == 400
    assert await _status(client, **{"encounter:Patient": "1"}) == 400


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
        BASE + "/_search", data={"status": "on-hold", "intent": "order"}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, identifier="CP-B")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/care-plans/{world['b']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "CarePlan"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
