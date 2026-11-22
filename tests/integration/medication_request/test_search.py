"""FHIR R4 search over MedicationRequest (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/medicationrequest.html#search).

One block per search parameter - `status`, `intent` and `priority` codes, `authoredon` and
`date` date ranges (`date` over every dosage instruction's timing events), `identifier`,
`category`, `code` and `intended-performertype` tokens, the single-target references
(`encounter`, `medication`, `intended-dispenser`, `patient`) and the multi-target ones
(`subject`, `requester`, `intended-performer`) - then chaining, `_include`/`_revinclude`, result
parameters, combination rules, lenient vs strict handling and POST _search.
"""

import pytest

from tests.integration.medication_request.support import (
    API,
    BASE,
    CATEGORY,
    RX_IDS,
    RXNORM,
    SCT,
    V2_0203,
    concept,
    create_encounter,
    create_medication,
    create_medication_request,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    encounter_body,
    medication_body,
    medication_request_body,
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
    """Two patients, a practitioner, a role, two organizations, an encounter and two
    medications, plus five medication requests with distinct, searchable values.
    Returns {key: id}.

      a  active order, urgent, of p1 in an encounter, requested by a practitioner, intended for
         an organization and dispensed by another, coded aspirin, with timing events
      b  completed plan, routine, of p2, requested by a role, for a Medication reference
      c  draft original-order of a Group, requested by an organization, a Device performer
      d  stopped proposal of a logical subject, requested by a Device
      e  only what R4 requires, with a logical subject
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
    w["o1"] = await create_organization(client, name="Pharma One")
    w["o2"] = await create_organization(client, name="Pharma Two")
    w["enc"] = await create_encounter(
        client, encounter_body(subject={"reference": f"Patient/{w['p1']}"})
    )
    w["m1"] = await create_medication(
        client, medication_body(status="active", code=concept(RXNORM, "1049502"))
    )
    w["m2"] = await create_medication(client, medication_body(status="inactive"))
    base = medication_request_body
    a = base(
        w["p1"],
        status="active",
        intent="order",
        priority="urgent",
        identifier=[
            {
                "system": RX_IDS,
                "value": "RX-A",
                "type": {
                    "coding": [{"system": V2_0203, "code": "PLAC"}],
                    "text": "Rx id",
                },
            }
        ],
        category=[concept(CATEGORY, "outpatient", "Outpatient")],
        medicationCodeableConcept=concept(RXNORM, "197696", "Aspirin"),
        encounter={"reference": f"Encounter/{w['enc']}"},
        authoredOn="2023-01-15T09:30:00Z",
        requester={"reference": f"Practitioner/{w['pr']}"},
        performer={"reference": f"Organization/{w['o1']}"},
        performerType=concept(SCT, "309343006", "Physician"),
        dispenseRequest={"performer": {"reference": f"Organization/{w['o2']}"}},
        dosageInstruction=[
            {"timing": {"event": ["2023-01-16T08:00:00Z", "2023-01-16T20:00:00Z"]}},
            {"timing": {"event": ["2023-02-01T08:00:00Z"]}},
        ],
    )
    w["a"] = await create_medication_request(client, a)
    b = base(
        w["p2"],
        status="completed",
        intent="plan",
        priority="routine",
        identifier=[{"system": RX_IDS, "value": "RX-B"}],
        category=[{"text": "Inpatient"}],
        requester={"reference": f"PractitionerRole/{w['role']}"},
        authoredOn="2024-02",
    )
    del b["medicationCodeableConcept"]
    b["medicationReference"] = {"reference": f"Medication/{w['m1']}"}
    w["b"] = await create_medication_request(client, b)
    c = {
        "status": "draft",
        "intent": "original-order",
        "medicationCodeableConcept": {"text": "Compounded cream"},
        "subject": {"reference": "Group/430001"},
        "requester": {"reference": f"Organization/{w['o1']}"},
        "performer": {"reference": "CareTeam/999999"},
        "authoredOn": "2019",
    }
    w["c"] = await create_medication_request(client, c)
    d = {
        "status": "stopped",
        "intent": "proposal",
        "medicationCodeableConcept": {"text": "x"},
        "subject": {
            "identifier": {"system": "urn:pts", "value": "P-9"},
            "display": "External",
        },
        "requester": {"reference": "Device/5"},
    }
    w["d"] = await create_medication_request(client, d)
    w["e"] = await create_medication_request(
        client,
        {
            "status": "unknown",
            "intent": "option",
            "medicationCodeableConcept": {"text": "y"},
            "subject": {"identifier": {"system": "urn:pts", "value": "P-8"}},
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


# -- status / intent / priority -------------------------------------------------------------


async def test_status(client, world):
    assert await _keys(client, world, status="active") == {"a"}
    assert await _keys(client, world, status="completed") == {"b"}
    assert await _keys(client, world, status="draft") == {"c"}
    assert await _keys(client, world, status="stopped") == {"d"}
    assert await _keys(client, world, status="active,draft") == {"a", "c"}
    assert await _keys(
        client,
        world,
        status="http://hl7.org/fhir/CodeSystem/medicationrequest-status|active",
    ) == {"a"}
    assert await _keys(client, world, status="http://wrong|active") == set()
    assert await _keys(client, world, status="no-such-code") == set()
    assert await _keys(client, world, **{"status:not": "active"}) == {
        "b",
        "c",
        "d",
        "e",
    }
    assert await _keys(client, world, **{"status:missing": "true"}) == set()


async def test_intent(client, world):
    assert await _keys(client, world, intent="order") == {"a"}
    assert await _keys(client, world, intent="plan") == {"b"}
    assert await _keys(client, world, intent="original-order") == {
        "c"
    }  # the real FHIR code
    assert await _keys(client, world, intent="proposal") == {"d"}
    assert await _keys(client, world, intent="order,plan") == {"a", "b"}
    assert await _keys(
        client,
        world,
        intent="http://hl7.org/fhir/CodeSystem/medicationrequest-intent|plan",
    ) == {"b"}
    assert await _keys(client, world, intent="http://wrong|plan") == set()
    assert await _keys(client, world, intent="option") == {"e"}
    assert await _keys(client, world, **{"intent:missing": "true"}) == set()


async def test_priority(client, world):
    assert await _keys(client, world, priority="urgent") == {"a"}
    assert await _keys(client, world, priority="routine") == {"b"}
    assert await _keys(client, world, priority="urgent,routine") == {"a", "b"}
    assert await _keys(
        client, world, priority="http://hl7.org/fhir/request-priority|urgent"
    ) == {"a"}
    assert await _keys(client, world, priority="stat") == set()
    assert await _keys(client, world, **{"priority:missing": "true"}) == {"c", "d", "e"}


# -- authoredon / date ----------------------------------------------------------------------


async def test_authoredon(client, world):
    assert await _keys(client, world, authoredon="2023-01-15") == {"a"}
    assert await _keys(client, world, authoredon="2023") == {"a"}
    assert await _keys(client, world, authoredon="2024-02") == {"b"}
    assert await _keys(client, world, authoredon="ge2023-06-01") == {"b"}
    assert await _keys(client, world, authoredon="lt2023-01-01") == {"c"}
    assert await _keys(client, world, authoredon="sa2023-02-01") == {"b"}
    assert await _keys(client, world, authoredon="eb2020-01-01") == {"c"}
    assert await _keys(client, world, **{"authoredon:missing": "true"}) == {"d", "e"}


async def test_date_reads_every_timing_event(client, world):
    assert await _keys(client, world, date="2023-01-16") == {"a"}
    assert await _keys(client, world, date="2023-02-01") == {
        "a"
    }  # the second dosage instruction
    assert await _keys(client, world, date="2023-03-01") == set()
    assert await _keys(client, world, date="ge2023-01-20") == {"a"}
    assert await _keys(client, world, date="lt2023-01-01") == set()
    assert await _keys(client, world, **{"date:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }
    assert await _keys(client, world, **{"date:missing": "false"}) == {"a"}


# -- identifier / category / code / intended-performertype ----------------------------------


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="RX-A") == {"a"}
    assert await _keys(client, world, identifier=f"{RX_IDS}|RX-B") == {"b"}
    assert await _keys(client, world, identifier="RX-A,RX-B") == {"a", "b"}
    assert await _keys(client, world, identifier="urn:wrong|RX-A") == set()
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|PLAC|RX-A"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|PLAC|RX-B"})
        == set()
    )
    assert await _keys(client, world, **{"identifier:text": "rx id"}) == {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


async def test_category(client, world):
    assert await _keys(client, world, category="outpatient") == {"a"}
    assert await _keys(client, world, category=f"{CATEGORY}|outpatient") == {"a"}
    assert await _keys(client, world, category="http://wrong|outpatient") == set()
    assert await _keys(client, world, **{"category:text": "inpatient"}) == {
        "b"
    }  # a text-only concept
    assert await _keys(client, world, **{"category:text": "outpat"}) == {
        "a"
    }  # Coding.display
    assert await _keys(client, world, **{"category:missing": "true"}) == {"c", "d", "e"}


async def test_code_reads_medication_codeable_concept(client, world):
    assert await _keys(client, world, code="197696") == {"a"}
    assert await _keys(client, world, code=f"{RXNORM}|197696") == {"a"}
    assert await _keys(client, world, code="http://wrong|197696") == set()
    assert await _keys(client, world, **{"code:text": "compounded"}) == {"c"}
    assert await _keys(client, world, **{"code:text": "aspirin"}) == {"a"}
    # a medicationReference carries no code
    assert await _keys(client, world, **{"code:missing": "true"}) == {"b"}


async def test_intended_performertype(client, world):
    assert await _keys(client, world, **{"intended-performertype": "309343006"}) == {
        "a"
    }
    assert await _keys(
        client, world, **{"intended-performertype": f"{SCT}|309343006"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"intended-performertype:text": "physician"}
    ) == {"a"}
    assert await _keys(client, world, **{"intended-performertype:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }


# -- patient / subject / encounter / medication ---------------------------------------------


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
    # a Group or a logical subject is not a Patient, so it counts as missing `patient`
    assert await _keys(client, world, **{"patient:missing": "true"}) == {"c", "d", "e"}


async def test_subject_is_multi_target(client, world):
    assert (
        await _status(client, subject=str(world["p1"])) == 400
    )  # a bare id is ambiguous
    assert await _keys(client, world, subject=f"Patient/{world['p1']}") == {"a"}
    assert await _keys(client, world, **{"subject:Patient": str(world["p2"])}) == {"b"}
    assert await _keys(client, world, subject="Group/430001") == {
        "c"
    }  # the type is part of the match
    assert await _keys(client, world, subject=f"Group/{world['p1']}") == set()
    assert await _keys(client, world, **{"subject:identifier": "urn:pts|P-9"}) == {"d"}


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


async def test_medication(client, world):
    assert await _keys(client, world, medication=str(world["m1"])) == {
        "b"
    }  # one target: a bare id works
    assert await _keys(client, world, medication=f"Medication/{world['m1']}") == {"b"}
    assert await _keys(client, world, medication=str(world["m2"])) == set()
    assert await _keys(client, world, **{"medication:missing": "true"}) == {
        "a",
        "c",
        "d",
        "e",
    }


# -- requester / intended-performer / intended-dispenser ------------------------------------


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
    assert await _keys(client, world, requester=f"Organization/{world['o1']}") == {"c"}
    assert await _keys(client, world, requester="Device/5") == {"d"}
    assert (
        await _keys(client, world, requester=f"Practitioner/{world['role']}") == set()
    )
    assert await _keys(client, world, **{"requester:missing": "true"}) == {"e"}


async def test_intended_performer_is_multi_target(client, world):
    assert await _status(client, **{"intended-performer": str(world["o1"])}) == 400
    assert await _keys(
        client, world, **{"intended-performer": f"Organization/{world['o1']}"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"intended-performer:Organization": str(world["o1"])}
    ) == {"a"}
    assert await _keys(client, world, **{"intended-performer": "CareTeam/999999"}) == {
        "c"
    }
    assert await _keys(client, world, **{"intended-performer:missing": "true"}) == {
        "b",
        "d",
        "e",
    }


async def test_intended_dispenser(client, world):
    assert await _keys(client, world, **{"intended-dispenser": str(world["o2"])}) == {
        "a"
    }  # one target
    assert await _keys(
        client, world, **{"intended-dispenser": f"Organization/{world['o2']}"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"intended-dispenser": str(world["o1"])}) == set()
    )
    assert await _keys(client, world, **{"intended-dispenser:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }


# -- chaining -------------------------------------------------------------------------------


async def test_chains(client, world):
    assert await _keys(client, world, **{"patient.family": "Windsor"}) == {"a"}
    assert await _keys(client, world, **{"subject:Patient.name": "Ben"}) == {"b"}
    assert await _keys(
        client, world, **{"requester:Practitioner.family": "Careful"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"requester:Organization.name": "Pharma One"}
    ) == {"c"}
    assert await _keys(
        client, world, **{"intended-performer:Organization.name": "Pharma One"}
    ) == {"a"}
    assert await _keys(client, world, **{"intended-dispenser.name": "Pharma Two"}) == {
        "a"
    }
    assert await _keys(client, world, **{"encounter.status": "in-progress"}) == {"a"}
    assert await _keys(client, world, **{"medication.status": "active"}) == {"b"}
    assert await _keys(client, world, **{"medication.code": "1049502"}) == {"b"}


async def test_bad_chains_are_400(client, world):
    assert await _status(client, **{"patient.nonsense": "x"}) == 400
    assert (
        await _status(client, **{"subject.family": "x"}) == 400
    )  # an untyped multi-target cannot be chained
    assert (
        await _status(client, **{"subject:Group.name": "x"}) == 400
    )  # Group is not searchable here
    assert await _status(client, **{"requester.family": "x"}) == 400
    assert await _status(client, **{"requester:Device.x": "x"}) == 400
    assert await _status(client, **{"intended-performer:CareTeam.name": "x"}) == 400
    assert (
        await _status(client, **{"code.x": "y"}) == 400
    )  # a token cannot be chained through
    assert await _status(client, **{"authoredon.x": "y"}) == 400


# -- _sort / _count / _offset / _total ------------------------------------------------------


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "authoredon",
        "category",
        "code",
        "date",
        "encounter",
        "identifier",
        "intended-dispenser",
        "intended-performer",
        "intended-performertype",
        "intent",
        "medication",
        "patient",
        "priority",
        "requester",
        "status",
        "subject",
        "_id",
    ):
        assert (await _search(client, _sort=key))["total"] == 5, key


async def test_sort_by_authoredon(client, world):
    async def ids(**params):
        return [
            int(e["resource"]["id"]) for e in (await _search(client, **params))["entry"]
        ]

    assert await ids(**{"authoredon:missing": "false", "_sort": "authoredon"}) == [
        world["c"],
        world["a"],
        world["b"],
    ]
    assert await ids(**{"authoredon:missing": "false", "_sort": "-authoredon"}) == [
        world["b"],
        world["a"],
        world["c"],
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
    assert "dosageInstruction" not in resource and "requester" not in resource


# -- _include / _revinclude -----------------------------------------------------------------


async def test_include_every_reference(client, world):
    ids = ",".join(str(world[k]) for k in KEYS)
    for param in ("patient", "subject"):
        bundle = await _search(client, _id=ids, _include=f"MedicationRequest:{param}")
        assert _of_type(bundle, "Patient", "include") == {
            str(world["p1"]),
            str(world["p2"]),
        }
    bundle = await _search(client, _id=ids, _include="MedicationRequest:encounter")
    assert _of_type(bundle, "Encounter", "include") == {str(world["enc"])}
    bundle = await _search(client, _id=ids, _include="MedicationRequest:requester")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "PractitionerRole", "include") == {str(world["role"])}
    assert _of_type(bundle, "Organization", "include") == {
        str(world["o1"])
    }  # a Device adds nothing
    bundle = await _search(
        client, _id=ids, _include="MedicationRequest:intended-performer"
    )
    assert _of_type(bundle, "Organization", "include") == {
        str(world["o1"])
    }  # a CareTeam adds nothing
    bundle = await _search(
        client, _id=ids, _include="MedicationRequest:intended-dispenser"
    )
    assert _of_type(bundle, "Organization", "include") == {str(world["o2"])}
    bundle = await _search(client, _id=ids, _include="MedicationRequest:medication")
    assert _of_type(bundle, "Medication", "include") == {str(world["m1"])}


async def test_revinclude_on_the_resources_a_request_points_at(client, world):
    for param in ("patient", "subject"):
        bundle = await _other(
            client,
            "patients",
            _id=str(world["p1"]),
            _revinclude=f"MedicationRequest:{param}",
        )
        assert _of_type(bundle, "MedicationRequest", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "encounters",
        _id=str(world["enc"]),
        _revinclude="MedicationRequest:encounter",
    )
    assert _of_type(bundle, "MedicationRequest", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "practitioners",
        _id=str(world["pr"]),
        _revinclude="MedicationRequest:requester",
    )
    assert _of_type(bundle, "MedicationRequest", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "practitioner-roles",
        _id=str(world["role"]),
        _revinclude="MedicationRequest:requester",
    )
    assert _of_type(bundle, "MedicationRequest", "include") == {str(world["b"])}
    bundle = await _other(
        client,
        "organizations",
        _id=str(world["o1"]),
        _revinclude="MedicationRequest:requester",
    )
    assert _of_type(bundle, "MedicationRequest", "include") == {str(world["c"])}
    bundle = await _other(
        client,
        "organizations",
        _id=str(world["o1"]),
        _revinclude="MedicationRequest:intended-performer",
    )
    assert _of_type(bundle, "MedicationRequest", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "organizations",
        _id=str(world["o2"]),
        _revinclude="MedicationRequest:intended-dispenser",
    )
    assert _of_type(bundle, "MedicationRequest", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "medications",
        _id=str(world["m1"]),
        _revinclude="MedicationRequest:medication",
    )
    assert _of_type(bundle, "MedicationRequest", "include") == {str(world["b"])}


# -- combination rules / lenient vs strict --------------------------------------------------


async def test_params_are_anded(client, world):
    assert await _keys(client, world, status="active", intent="order") == {"a"}
    assert await _keys(client, world, status="active", intent="plan") == set()
    assert await _keys(client, world, patient=str(world["p1"]), authoredon="2023") == {
        "a"
    }
    assert await _keys(client, world, code="197696", category="outpatient") == {"a"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"patient:text": "x"}) == 400
    assert await _status(client, **{"authoredon:exact": "2020"}) == 400
    assert await _status(client, **{"identifier:below": "x"}) == 400
    assert await _status(client, **{"status:text": "x"}) == 400
    assert await _status(client, **{"intent:text": "x"}) == 400
    assert await _status(client, date="banana") == 400


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
        BASE + "/_search", data={"intent": "plan", "status": "completed"}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, identifier="RX-B")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/medication-requests/{world['b']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "MedicationRequest"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle


async def test_service_request_observation_and_report_chain_to_a_medication_request(
    client, world
):
    ref = {"reference": f"MedicationRequest/{world['a']}"}
    service_request = (
        await client.post(
            f"{API}/service-requests/",
            json={
                "status": "active",
                "intent": "order",
                "subject": {"reference": f"Patient/{world['p1']}"},
                "basedOn": [ref],
            },
        )
    ).json()["id"]
    from tests.integration.medication_request.support import (
        create_observation,
        observation_body,
    )

    observation = await create_observation(
        client, observation_body(world["p1"], basedOn=[ref])
    )
    for path, found in (
        ("service-requests", service_request),
        ("observations", str(observation)),
    ):
        got = await _other(
            client, path, **{"based-on:MedicationRequest.status": "active"}
        )
        assert found in {e["resource"]["id"] for e in got["entry"]}, path
        got = await _other(
            client, path, **{"based-on:MedicationRequest.status": "completed"}
        )
        assert found not in {e["resource"]["id"] for e in got.get("entry") or []}, path
    got = await _other(
        client,
        "service-requests",
        _id=service_request,
        _include="ServiceRequest:based-on",
    )
    assert _of_type(got, "MedicationRequest", "include") == {str(world["a"])}
