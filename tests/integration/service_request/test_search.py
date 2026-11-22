"""FHIR R4 search over ServiceRequest (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/servicerequest.html#search).

One block per search parameter — `status`, `intent` and `priority` codes, `authored` and
`occurrence` date ranges (`occurrence` over a dateTime, a Period *or* a Timing), `identifier` and
`requisition` tokens, `category`, `code`, `body-site` and `performer-type` tokens on
CodeableConcepts, `instantiates-uri` and `instantiates-canonical`, the single-target references
(`encounter`, `replaces`, `specimen`, `patient`) and the multi-target ones (`subject`,
`requester`, `performer`, `based-on`) — then chaining, `_include`/`_revinclude`, result
parameters, combination rules, lenient vs strict handling and POST _search.
"""

import pytest

from tests.integration.service_request.support import (
    API,
    BASE,
    LOINC,
    ORDER_IDS,
    REQUISITIONS,
    SCT,
    V2_0203,
    concept,
    create_encounter,
    create_healthcare_service,
    create_location,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_service_request,
    create_specimen,
    encounter_body,
    service_request_body,
    specimen_body,
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
    """Two patients, a practitioner, a role, an organization, a healthcare service, a location,
    an encounter and two specimens, plus five service requests with distinct, searchable values.
    Returns {key: id}.

      a  active order, urgent, of p1 in an encounter, requested by a practitioner, performed by an
         organization and a role, with a specimen, instantiating a PlanDefinition
      b  completed plan, routine, of p2, based on and replacing a, requested by a role, over a period
      c  draft original-order of a location, a Timing, based on a CarePlan, with the other specimen
      d  entered-in-error proposal of a Group, requested by a Device
      e  nothing coded, a logical subject, based on b
    """
    w = {}
    w["p1"] = await create_patient(
        client, {"active": True, "name": [{"family": "Windsor", "given": ["Anna"]}]}
    )
    w["p2"] = await create_patient(
        client, {"active": True, "name": [{"family": "Fairfax", "given": ["Ben"]}]}
    )
    w["pr"] = await create_practitioner(client)  # family "Careful"
    w["role"] = await create_practitioner_role(client)
    w["org"] = await create_organization(client)  # name "Providing Org"
    w["hs"] = await create_healthcare_service(client)  # "Cardiology Clinic"
    w["loc"] = await create_location(client)  # name "North Wing"
    w["enc"] = await create_encounter(
        client, encounter_body(subject={"reference": f"Patient/{w['p1']}"})
    )
    w["s1"] = await create_specimen(
        client, specimen_body(w["p1"], type=concept(SCT, "119297000"))
    )
    w["s2"] = await create_specimen(client, specimen_body(w["p2"]))
    w["a"] = await create_service_request(
        client,
        service_request_body(
            w["p1"],
            status="active",
            intent="order",
            priority="urgent",
            identifier=[
                {
                    "system": ORDER_IDS,
                    "value": "SR-A",
                    "type": {
                        "coding": [{"system": V2_0203, "code": "PLAC"}],
                        "text": "Placer id",
                    },
                }
            ],
            requisition={"system": REQUISITIONS, "value": "RQ-A"},
            category=[concept(SCT, "108252007", "Laboratory procedure")],
            code=concept(LOINC, "58410-2", "CBC panel"),
            bodySite=[concept(SCT, "368208006", "Left upper arm structure")],
            performerType=concept(SCT, "309343006", "Physician"),
            encounter={"reference": f"Encounter/{w['enc']}"},
            requester={"reference": f"Practitioner/{w['pr']}"},
            performer=[
                {"reference": f"Organization/{w['org']}"},
                {"reference": f"PractitionerRole/{w['role']}"},
            ],
            specimen=[{"reference": f"Specimen/{w['s1']}"}],
            instantiatesCanonical=["http://example.org/fhir/PlanDefinition/cbc|1.0"],
            instantiatesUri=["http://example.org/protocols/cbc"],
            authoredOn="2023-01-15T09:30:00Z",
            occurrenceDateTime="2023-01-16T09:00:00Z",
        ),
    )
    w["b"] = await create_service_request(
        client,
        service_request_body(
            w["p2"],
            status="completed",
            intent="plan",
            priority="routine",
            identifier=[{"system": ORDER_IDS, "value": "SR-B"}],
            category=[{"text": "Imaging"}],
            code={"text": "Chest x-ray"},
            requester={"reference": f"PractitionerRole/{w['role']}"},
            performer=[{"reference": f"HealthcareService/{w['hs']}"}],
            basedOn=[{"reference": f"ServiceRequest/{w['a']}"}],
            replaces=[{"reference": f"ServiceRequest/{w['a']}"}],
            authoredOn="2024-02-01",
            occurrencePeriod={"start": "2024-01-01", "end": "2024-03-01"},
        ),
    )
    from tests.helpers.care_plans import create_minimal_care_plan

    w["cp"] = await create_minimal_care_plan(client)
    w["c"] = await create_service_request(
        client,
        {
            "status": "draft",
            "intent": "original-order",
            "subject": {"reference": f"Location/{w['loc']}"},
            "requester": {"reference": f"Organization/{w['org']}"},
            "performer": [{"reference": "CareTeam/999999"}],
            "specimen": [{"reference": f"Specimen/{w['s2']}"}],
            "basedOn": [{"reference": f"CarePlan/{w['cp']}"}],
            "occurrenceTiming": {
                "event": ["2022-06-01T08:00:00Z", "2022-08-01T08:00:00Z"]
            },
            "instantiatesCanonical": ["http://example.org/fhir/PlanDefinition/cbc|2.0"],
        },
    )
    w["d"] = await create_service_request(
        client,
        {
            "status": "entered-in-error",
            "intent": "proposal",
            "subject": {"reference": "Group/430001"},
            "requester": {"reference": "Device/5"},
            "authoredOn": "2019",
            "instantiatesUri": ["http://example.org/protocols/other"],
        },
    )
    w["e"] = await create_service_request(
        client,
        {
            "subject": {
                "identifier": {"system": "urn:pts", "value": "P-9"},
                "display": "External",
            },
            "requisition": {"system": REQUISITIONS, "value": "RQ-E"},
            "basedOn": [{"reference": f"ServiceRequest/{w['b']}"}],
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


# ── status / intent / priority ───────────────────────────────────────────────


async def test_status(client, world):
    assert await _keys(client, world, status="active") == {"a"}
    assert await _keys(client, world, status="completed") == {"b"}
    assert await _keys(client, world, status="draft") == {"c"}
    assert await _keys(client, world, status="entered-in-error") == {
        "d"
    }  # the real FHIR code
    assert await _keys(client, world, status="active,draft") == {"a", "c"}
    assert await _keys(
        client, world, status="http://hl7.org/fhir/request-status|active"
    ) == {"a"}
    assert await _keys(client, world, status="http://wrong|active") == set()
    assert await _keys(client, world, status="no-such-code") == set()
    assert await _keys(client, world, **{"status:not": "active"}) == {
        "b",
        "c",
        "d",
        "e",
    }  # `:not` also finds a request with no status
    assert await _keys(client, world, **{"status:missing": "true"}) == {"e"}
    assert await _keys(client, world, **{"status:missing": "false"}) == ALL - {"e"}


async def test_intent(client, world):
    assert await _keys(client, world, intent="order") == {"a"}
    assert await _keys(client, world, intent="plan") == {"b"}
    assert await _keys(client, world, intent="original-order") == {
        "c"
    }  # the real FHIR code
    assert await _keys(client, world, intent="proposal") == {"d"}
    assert await _keys(client, world, intent="order,plan") == {"a", "b"}
    assert await _keys(
        client, world, intent="http://hl7.org/fhir/request-intent|plan"
    ) == {"b"}
    assert await _keys(client, world, intent="http://wrong|plan") == set()
    assert await _keys(client, world, intent="reflex-order") == set()
    assert await _keys(client, world, **{"intent:missing": "true"}) == {"e"}


async def test_priority(client, world):
    assert await _keys(client, world, priority="urgent") == {"a"}
    assert await _keys(client, world, priority="routine") == {"b"}
    assert await _keys(client, world, priority="urgent,routine") == {"a", "b"}
    assert await _keys(
        client, world, priority="http://hl7.org/fhir/request-priority|urgent"
    ) == {"a"}
    assert await _keys(client, world, priority="stat") == set()
    assert await _keys(client, world, **{"priority:missing": "true"}) == {"c", "d", "e"}


# ── authored / occurrence ────────────────────────────────────────────────────


async def test_authored(client, world):
    assert await _keys(client, world, authored="2023-01-15") == {"a"}
    assert await _keys(client, world, authored="2023") == {"a"}
    assert await _keys(client, world, authored="2024-02") == {
        "b"
    }  # a date covers its precision
    assert await _keys(client, world, authored="ge2023-06-01") == {"b"}
    assert await _keys(client, world, authored="lt2023-01-01") == {"d"}
    assert await _keys(client, world, authored="sa2023-02-01") == {"b"}
    assert await _keys(client, world, authored="eb2020-01-01") == {"d"}
    assert await _keys(client, world, **{"authored:missing": "true"}) == {"c", "e"}


async def test_occurrence_reads_a_datetime_a_period_and_a_timing(client, world):
    assert await _keys(client, world, occurrence="2023-01-16") == {"a"}
    assert (
        await _keys(client, world, occurrence="2024-02-01") == set()
    )  # a period wholly contains it
    assert await _keys(client, world, occurrence="ge2024-01-01") == {"b"}
    assert (
        await _keys(client, world, occurrence="2022-06-01") == set()
    )  # the Timing spans two events
    assert await _keys(client, world, occurrence="lt2023-01-01") == {
        "c"
    }  # earliest event .. latest event
    assert await _keys(client, world, occurrence="ge2022-07-01") == {"a", "b", "c"}
    assert await _keys(client, world, occurrence="sa2023-02-01") == {"b"}
    assert await _keys(client, world, **{"occurrence:missing": "true"}) == {"d", "e"}
    assert await _keys(client, world, **{"occurrence:missing": "false"}) == {
        "a",
        "b",
        "c",
    }


# ── identifier / requisition ─────────────────────────────────────────────────


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="SR-A") == {"a"}
    assert await _keys(client, world, identifier=f"{ORDER_IDS}|SR-B") == {"b"}
    assert await _keys(client, world, identifier="SR-A,SR-B") == {"a", "b"}
    assert await _keys(client, world, identifier="urn:wrong|SR-A") == set()
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|PLAC|SR-A"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|PLAC|SR-B"})
        == set()
    )
    assert await _keys(client, world, **{"identifier:text": "placer"}) == {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


async def test_requisition(client, world):
    assert await _keys(client, world, requisition="RQ-A") == {"a"}
    assert await _keys(client, world, requisition=f"{REQUISITIONS}|RQ-E") == {"e"}
    assert await _keys(client, world, requisition="RQ-A,RQ-E") == {"a", "e"}
    assert await _keys(client, world, requisition="http://wrong|RQ-A") == set()
    assert await _keys(client, world, **{"requisition:missing": "true"}) == {
        "b",
        "c",
        "d",
    }


# ── category / code / body-site / performer-type ─────────────────────────────


async def test_category(client, world):
    assert await _keys(client, world, category="108252007") == {"a"}
    assert await _keys(client, world, category=f"{SCT}|108252007") == {"a"}
    assert await _keys(client, world, category="http://wrong|108252007") == set()
    assert await _keys(client, world, **{"category:text": "imaging"}) == {
        "b"
    }  # a text-only concept
    assert await _keys(client, world, **{"category:text": "laboratory"}) == {
        "a"
    }  # Coding.display
    assert await _keys(client, world, **{"category:missing": "true"}) == {"c", "d", "e"}


async def test_code(client, world):
    assert await _keys(client, world, code="58410-2") == {"a"}
    assert await _keys(client, world, code=f"{LOINC}|58410-2") == {"a"}
    assert await _keys(client, world, code="http://wrong|58410-2") == set()
    assert await _keys(client, world, **{"code:text": "chest"}) == {"b"}
    assert await _keys(client, world, **{"code:not": "58410-2"}) == {"b", "c", "d", "e"}
    assert await _keys(client, world, **{"code:missing": "true"}) == {"c", "d", "e"}


async def test_body_site_and_performer_type(client, world):
    assert await _keys(client, world, **{"body-site": "368208006"}) == {"a"}
    assert await _keys(client, world, **{"body-site:text": "left upper"}) == {"a"}
    assert await _keys(client, world, **{"body-site:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }
    assert await _keys(client, world, **{"performer-type": "309343006"}) == {"a"}
    assert await _keys(client, world, **{"performer-type": f"{SCT}|309343006"}) == {"a"}
    assert await _keys(client, world, **{"performer-type:text": "physician"}) == {"a"}
    assert await _keys(client, world, **{"performer-type:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }


# ── instantiates-uri / instantiates-canonical ────────────────────────────────


async def test_instantiates_uri(client, world):
    assert await _keys(
        client, world, **{"instantiates-uri": "http://example.org/protocols/cbc"}
    ) == {"a"}
    assert (
        await _keys(
            client, world, **{"instantiates-uri": "http://example.org/protocols/CBC"}
        )
        == set()
    )  # exact: case-sensitive
    assert await _keys(
        client, world, **{"instantiates-uri:below": "http://example.org/protocols"}
    ) == {"a", "d"}
    assert await _keys(
        client,
        world,
        **{"instantiates-uri:above": "http://example.org/protocols/cbc/v2"},
    ) == {"a"}
    assert await _keys(client, world, **{"instantiates-uri:missing": "true"}) == {
        "b",
        "c",
        "e",
    }


async def test_instantiates_canonical(client, world):
    assert await _keys(
        client,
        world,
        **{"instantiates-canonical": "http://example.org/fhir/PlanDefinition/cbc|1.0"},
    ) == {"a"}
    # an unversioned URL also finds every stored version of it
    assert await _keys(
        client,
        world,
        **{"instantiates-canonical": "http://example.org/fhir/PlanDefinition/cbc"},
    ) == {"a", "c"}
    assert (
        await _keys(
            client,
            world,
            **{
                "instantiates-canonical": "http://example.org/fhir/PlanDefinition/cbc|3.0"
            },
        )
        == set()
    )
    assert await _keys(client, world, **{"instantiates-canonical:missing": "true"}) == {
        "b",
        "d",
        "e",
    }


# ── patient / subject ────────────────────────────────────────────────────────


async def test_patient(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {
        "a"
    }  # one target: a bare id works
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"b"}
    assert await _keys(client, world, patient=f"{world['p1']},{world['p2']}") == {
        "a",
        "b",
    }
    assert await _keys(client, world, patient="999999") == set()
    # a Location, a Group or a logical subject is not a Patient, so it counts as missing `patient`
    assert await _keys(client, world, **{"patient:missing": "true"}) == {"c", "d", "e"}
    assert await _keys(client, world, **{"patient:missing": "false"}) == {"a", "b"}


async def test_subject_is_multi_target(client, world):
    assert (
        await _status(client, subject=str(world["p1"])) == 400
    )  # a bare id is ambiguous
    assert await _keys(client, world, subject=f"Patient/{world['p1']}") == {"a"}
    assert await _keys(client, world, **{"subject:Patient": str(world["p2"])}) == {"b"}
    assert await _keys(client, world, subject=f"Location/{world['loc']}") == {"c"}
    assert await _keys(client, world, subject="Group/430001") == {
        "d"
    }  # the type is part of the match
    assert await _keys(client, world, subject=f"Group/{world['p1']}") == set()
    assert await _keys(client, world, **{"subject:identifier": "urn:pts|P-9"}) == {"e"}


# ── encounter / requester / performer ────────────────────────────────────────


async def test_encounter(client, world):
    assert await _keys(client, world, encounter=str(world["enc"])) == {"a"}
    assert await _keys(client, world, encounter=f"Encounter/{world['enc']}") == {"a"}
    assert await _keys(client, world, encounter="999999") == set()
    assert await _keys(client, world, **{"encounter:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }


async def test_requester_is_multi_target(client, world):
    assert (
        await _status(client, requester=str(world["pr"])) == 400
    )  # a bare id is ambiguous
    assert await _keys(client, world, requester=f"Practitioner/{world['pr']}") == {"a"}
    assert await _keys(
        client, world, **{"requester:Practitioner": str(world["pr"])}
    ) == {"a"}
    assert await _keys(
        client, world, requester=f"PractitionerRole/{world['role']}"
    ) == {"b"}
    assert await _keys(client, world, requester=f"Organization/{world['org']}") == {"c"}
    assert await _keys(client, world, requester="Device/5") == {"d"}
    assert (
        await _keys(client, world, requester=f"Practitioner/{world['role']}") == set()
    )  # the type is part of the match
    assert await _keys(client, world, **{"requester:missing": "true"}) == {"e"}


async def test_performer_is_multi_target(client, world):
    assert (
        await _status(client, performer=str(world["org"])) == 400
    )  # a bare id is ambiguous
    assert await _keys(client, world, performer=f"Organization/{world['org']}") == {"a"}
    assert await _keys(
        client, world, performer=f"PractitionerRole/{world['role']}"
    ) == {"a"}  # the second performer
    assert await _keys(
        client, world, **{"performer:HealthcareService": str(world["hs"])}
    ) == {"b"}
    assert await _keys(client, world, performer="CareTeam/999999") == {"c"}
    assert (
        await _keys(client, world, performer=f"Organization/{world['role']}") == set()
    )
    assert await _keys(client, world, **{"performer:missing": "true"}) == {"d", "e"}


# ── based-on / replaces / specimen ───────────────────────────────────────────


async def test_based_on_is_multi_target(client, world):
    assert (
        await _status(client, **{"based-on": str(world["a"])}) == 400
    )  # a bare id is ambiguous
    assert await _keys(
        client, world, **{"based-on": f"ServiceRequest/{world['a']}"}
    ) == {"b"}
    assert await _keys(
        client, world, **{"based-on:ServiceRequest": str(world["b"])}
    ) == {"e"}
    assert await _keys(client, world, **{"based-on": f"CarePlan/{world['cp']}"}) == {
        "c"
    }
    assert await _keys(client, world, **{"based-on:CarePlan": str(world["cp"])}) == {
        "c"
    }
    assert await _keys(client, world, **{"based-on:CarePlan.status": "active"}) == {"c"}
    assert await _keys(client, world, **{"based-on:missing": "true"}) == {"a", "d"}


async def test_replaces(client, world):
    assert await _keys(client, world, replaces=str(world["a"])) == {
        "b"
    }  # one target: a bare id works
    assert await _keys(client, world, replaces=f"ServiceRequest/{world['a']}") == {"b"}
    assert await _keys(client, world, replaces="999999") == set()
    assert await _keys(client, world, **{"replaces:missing": "true"}) == {
        "a",
        "c",
        "d",
        "e",
    }


async def test_specimen(client, world):
    assert await _keys(client, world, specimen=str(world["s1"])) == {
        "a"
    }  # one target: a bare id works
    assert await _keys(client, world, specimen=f"Specimen/{world['s2']}") == {"c"}
    assert await _keys(client, world, specimen=f"{world['s1']},{world['s2']}") == {
        "a",
        "c",
    }
    assert await _keys(client, world, specimen="999999") == set()
    assert await _keys(client, world, **{"specimen:missing": "true"}) == {"b", "d", "e"}


# ── chaining ─────────────────────────────────────────────────────────────────


async def test_chains(client, world):
    assert await _keys(client, world, **{"patient.family": "Windsor"}) == {"a"}
    assert await _keys(client, world, **{"subject:Patient.name": "Ben"}) == {"b"}
    assert await _keys(client, world, **{"subject:Location.name": "North"}) == {"c"}
    assert await _keys(
        client, world, **{"requester:Practitioner.family": "Careful"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"requester:Organization.name": "Providing"}
    ) == {"c"}
    assert await _keys(
        client, world, **{"performer:Organization.name": "Providing"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"performer:HealthcareService.name": "Cardiology"}
    ) == {"b"}
    assert await _keys(client, world, **{"encounter.status": "in-progress"}) == {"a"}
    assert await _keys(
        client, world, **{"based-on:ServiceRequest.status": "active"}
    ) == {"b"}
    assert await _keys(client, world, **{"replaces.status": "active"}) == {"b"}
    assert await _keys(client, world, **{"specimen.type": "119297000"}) == {"a"}
    # chains recurse: e is based on b, which is based on a
    assert await _keys(
        client,
        world,
        **{"based-on:ServiceRequest.based-on:ServiceRequest.status": "active"},
    ) == {"e"}


async def test_bad_chains_are_400(client, world):
    assert await _status(client, **{"patient.nonsense": "x"}) == 400
    assert (
        await _status(client, **{"subject.family": "x"}) == 400
    )  # an untyped multi-target cannot be chained
    assert (
        await _status(client, **{"subject:Group.name": "x"}) == 400
    )  # Group is not searchable here
    assert await _status(client, **{"requester.family": "x"}) == 400
    assert (
        await _status(client, **{"performer:CareTeam.name": "x"}) == 400
    )  # CareTeam is not rebuilt
    assert (
        await _status(client, **{"based-on:DeviceRequest.status": "x"}) == 400
    )  # DeviceRequest is not a target of ServiceRequest.basedOn
    assert (
        await _status(client, **{"code.x": "y"}) == 400
    )  # a token cannot be chained through
    assert await _status(client, **{"authored.x": "y"}) == 400


# ── _sort / _count / _offset / _total ────────────────────────────────────────


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "authored",
        "based-on",
        "body-site",
        "category",
        "code",
        "encounter",
        "identifier",
        "instantiates-canonical",
        "instantiates-uri",
        "intent",
        "occurrence",
        "patient",
        "performer",
        "performer-type",
        "priority",
        "replaces",
        "requester",
        "requisition",
        "specimen",
        "status",
        "subject",
        "_id",
    ):
        assert (await _search(client, _sort=key))["total"] == 5, key


async def test_sort_by_authored(client, world):
    async def ids(**params):
        return [
            int(e["resource"]["id"]) for e in (await _search(client, **params))["entry"]
        ]

    assert await ids(**{"authored:missing": "false", "_sort": "authored"}) == [
        world["d"],
        world["a"],
        world["b"],
    ]
    assert await ids(**{"authored:missing": "false", "_sort": "-authored"}) == [
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
    assert "code" not in resource and "performer" not in resource


# ── _include / _revinclude ───────────────────────────────────────────────────


async def test_include_subject_encounter_requester_and_performer(client, world):
    ids = ",".join(str(world[k]) for k in KEYS)
    for param in ("patient", "subject"):
        bundle = await _search(client, _id=ids, _include=f"ServiceRequest:{param}")
        assert _of_type(bundle, "Patient", "include") == {
            str(world["p1"]),
            str(world["p2"]),
        }
    bundle = await _search(client, _id=ids, _include="ServiceRequest:subject")
    assert _of_type(bundle, "Location", "include") == {
        str(world["loc"])
    }  # a Group adds nothing
    bundle = await _search(client, _id=ids, _include="ServiceRequest:subject:Location")
    assert _of_type(bundle, "Patient", "include") == set()
    bundle = await _search(client, _id=ids, _include="ServiceRequest:encounter")
    assert _of_type(bundle, "Encounter", "include") == {str(world["enc"])}
    bundle = await _search(client, _id=ids, _include="ServiceRequest:requester")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "PractitionerRole", "include") == {str(world["role"])}
    assert _of_type(bundle, "Organization", "include") == {
        str(world["org"])
    }  # a Device adds nothing
    bundle = await _search(client, _id=ids, _include="ServiceRequest:performer")
    assert _of_type(bundle, "Organization", "include") == {str(world["org"])}
    assert _of_type(bundle, "PractitionerRole", "include") == {str(world["role"])}
    assert _of_type(bundle, "HealthcareService", "include") == {
        str(world["hs"])
    }  # a CareTeam adds nothing


async def test_include_based_on_replaces_and_specimen(client, world):
    bundle = await _search(
        client, _id=str(world["b"]), _include="ServiceRequest:based-on"
    )
    assert _of_type(bundle, "ServiceRequest", "include") == {str(world["a"])}
    bundle = await _search(
        client, _id=str(world["b"]), _include="ServiceRequest:replaces"
    )
    assert _of_type(bundle, "ServiceRequest", "include") == {str(world["a"])}
    bundle = await _search(
        client, _id=f"{world['a']},{world['c']}", _include="ServiceRequest:specimen"
    )
    assert _of_type(bundle, "Specimen", "include") == {
        str(world["s1"]),
        str(world["s2"]),
    }


async def test_revinclude_on_the_resources_a_request_points_at(client, world):
    for param in ("patient", "subject"):
        bundle = await _other(
            client,
            "patients",
            _id=str(world["p1"]),
            _revinclude=f"ServiceRequest:{param}",
        )
        assert _of_type(bundle, "ServiceRequest", "include") == {str(world["a"])}
    bundle = await _other(
        client, "locations", _id=str(world["loc"]), _revinclude="ServiceRequest:subject"
    )
    assert _of_type(bundle, "ServiceRequest", "include") == {str(world["c"])}
    bundle = await _other(
        client,
        "encounters",
        _id=str(world["enc"]),
        _revinclude="ServiceRequest:encounter",
    )
    assert _of_type(bundle, "ServiceRequest", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "practitioners",
        _id=str(world["pr"]),
        _revinclude="ServiceRequest:requester",
    )
    assert _of_type(bundle, "ServiceRequest", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "practitioner-roles",
        _id=str(world["role"]),
        _revinclude="ServiceRequest:requester",
    )
    assert _of_type(bundle, "ServiceRequest", "include") == {str(world["b"])}
    bundle = await _other(
        client,
        "practitioner-roles",
        _id=str(world["role"]),
        _revinclude="ServiceRequest:performer",
    )
    assert _of_type(bundle, "ServiceRequest", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "organizations",
        _id=str(world["org"]),
        _revinclude="ServiceRequest:requester",
    )
    assert _of_type(bundle, "ServiceRequest", "include") == {str(world["c"])}
    bundle = await _other(
        client,
        "organizations",
        _id=str(world["org"]),
        _revinclude="ServiceRequest:performer",
    )
    assert _of_type(bundle, "ServiceRequest", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "healthcare-services",
        _id=str(world["hs"]),
        _revinclude="ServiceRequest:performer",
    )
    assert _of_type(bundle, "ServiceRequest", "include") == {str(world["b"])}
    bundle = await _other(
        client, "specimens", _id=str(world["s1"]), _revinclude="ServiceRequest:specimen"
    )
    assert _of_type(bundle, "ServiceRequest", "include") == {str(world["a"])}


async def test_revinclude_on_itself(client, world):
    bundle = await _search(
        client, _id=str(world["a"]), _revinclude="ServiceRequest:based-on"
    )
    assert _of_type(bundle, "ServiceRequest", "include") == {str(world["b"])}
    bundle = await _search(
        client, _id=str(world["a"]), _revinclude="ServiceRequest:replaces"
    )
    assert _of_type(bundle, "ServiceRequest", "include") == {str(world["b"])}
    bundle = await _search(
        client, _id=str(world["b"]), _revinclude="ServiceRequest:based-on"
    )
    assert _of_type(bundle, "ServiceRequest", "include") == {str(world["e"])}


# ── combination rules / lenient vs strict ────────────────────────────────────


async def test_params_are_anded(client, world):
    assert await _keys(client, world, status="active", intent="order") == {"a"}
    assert await _keys(client, world, status="active", intent="plan") == set()
    assert await _keys(client, world, patient=str(world["p1"]), authored="2023") == {
        "a"
    }
    assert await _keys(client, world, code="58410-2", category="108252007") == {"a"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"patient:text": "x"}) == 400
    assert await _status(client, **{"authored:exact": "2020"}) == 400
    assert await _status(client, **{"identifier:below": "x"}) == 400
    assert await _status(client, **{"status:text": "x"}) == 400
    assert await _status(client, **{"intent:text": "x"}) == 400
    assert await _status(client, **{"requisition:text": "x"}) == 400
    assert await _status(client, **{"occurrence": "banana"}) == 400


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
        BASE + "/_search", data={"intent": "plan", "status": "completed"}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, identifier="SR-B")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/service-requests/{world['b']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "ServiceRequest"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle


async def test_partners_chain_to_include_and_revinclude_a_service_request(
    client, world
):
    from tests.integration.service_request.support import (
        appointment_body,
        create_appointment,
        create_observation,
        create_report,
        observation_body,
        report_body,
    )

    ref = {"reference": f"ServiceRequest/{world['a']}"}
    observation = await create_observation(
        client, observation_body(world["p1"], basedOn=[ref])
    )
    report = await create_report(client, report_body(world["p1"], basedOn=[ref]))
    encounter = (
        await client.post(
            f"{API}/encounters/",
            json={"status": "in-progress", "class": {"code": "AMB"}, "basedOn": [ref]},
        )
    ).json()["id"]
    procedure = (
        await client.post(
            f"{API}/procedures/",
            json={
                "status": "completed",
                "subject": {"reference": f"Patient/{world['p1']}"},
                "basedOn": [ref],
            },
        )
    ).json()["id"]
    appointment = await create_appointment(
        client, appointment_body(world["p1"], basedOn=[ref])
    )
    for path, found in (
        ("observations", str(observation)),
        ("diagnostic-reports", str(report)),
        ("encounters", encounter),
        ("procedures", procedure),
        ("appointments", str(appointment)),
    ):
        got = await _other(client, path, **{"based-on:ServiceRequest.status": "active"})
        assert found in {e["resource"]["id"] for e in got["entry"]}, path
        got = await _other(
            client, path, **{"based-on:ServiceRequest.status": "completed"}
        )
        assert found not in {e["resource"]["id"] for e in got.get("entry") or []}, path
    bundle = await _search(
        client,
        _id=str(world["a"]),
        _revinclude=[
            "Observation:based-on",
            "DiagnosticReport:based-on",
            "Encounter:based-on",
            "Procedure:based-on",
        ],
    )
    assert _of_type(bundle, "Observation", "include") == {str(observation)}
    assert _of_type(bundle, "DiagnosticReport", "include") == {str(report)}
    assert _of_type(bundle, "Encounter", "include") == {encounter}
    assert _of_type(bundle, "Procedure", "include") == {procedure}
    got = await _other(
        client, "observations", _id=str(observation), _include="Observation:based-on"
    )
    assert _of_type(got, "ServiceRequest", "include") == {str(world["a"])}
    got = await _other(
        client, "appointments", _id=str(appointment), _include="Appointment:based-on"
    )
    assert _of_type(got, "ServiceRequest", "include") == {str(world["a"])}
