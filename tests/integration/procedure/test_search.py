"""FHIR R4 search over Procedure (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/procedure.html#search).

One block per search parameter — `category`, `code` and `reason-code` are tokens on
CodeableConcepts, `status` a token on a plain code, `identifier` a token on an
Identifier, `date` a dateTime-or-Period range, `instantiates-uri` the engine's first
`uri` search, `instantiates-canonical` a search over canonical URLs, the
single-target references (`encounter`, `location`, `patient`) and the multi-target
ones (`subject`, `performer`, `based-on`, `part-of`, `reason-reference`) — then
chaining, `_include`/`_revinclude` in both directions, result parameters,
combination rules, lenient vs strict handling and POST _search.
"""

import pytest

from tests.integration.procedure.support import (
    API,
    BASE,
    EVENT_STATUS,
    PROC_IDS,
    SCT,
    V2_0203,
    appointment_body,
    create_appointment,
    create_condition,
    create_encounter,
    create_location,
    create_organization,
    create_patient,
    create_practitioner,
    create_procedure,
    create_related_person,
    encounter_body,
    procedure_body,
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
    """Two patients, a practitioner, an organization, a related person, a location, a
    condition and two encounters, plus five procedures with distinct, searchable
    values. Returns {key: id}."""
    w = {}
    w["p1"] = await create_patient(
        client, {"active": True, "name": [{"family": "Windsor", "given": ["Anna"]}]}
    )
    w["p2"] = await create_patient(
        client, {"active": True, "name": [{"family": "Fairfax", "given": ["Ben"]}]}
    )
    w["pr"] = await create_practitioner(client)  # family "Careful"
    w["org"] = await create_organization(client)  # name "Providing Org"
    w["rp"] = await create_related_person(
        client,
        {
            **related_person_body(w["p1"]),
            "name": [{"family": "Gray", "given": ["Gail"]}],
        },
    )
    w["loc"] = await create_location(client)  # name "North Wing"
    w["cond"] = await create_condition(client, w["p1"])
    w["enc1"] = await create_encounter(client, encounter_body())
    w["enc2"] = await create_encounter(client, encounter_body())
    w["a"] = await create_procedure(
        client,
        procedure_body(
            w["p1"],
            "completed",
            identifier=[
                {
                    "system": PROC_IDS,
                    "value": "PR-A",
                    "type": {
                        "coding": [{"system": V2_0203, "code": "PRN"}],
                        "text": "Procedure id",
                    },
                }
            ],
            instantiatesCanonical=["http://example.org/PlanDefinition/pd1|1.0"],
            instantiatesUri=["http://example.org/protocols/appendectomy"],
            basedOn=[{"reference": "ServiceRequest/80001"}],
            category={
                "coding": [
                    {
                        "system": SCT,
                        "code": "387713003",
                        "display": "Surgical procedure",
                    }
                ]
            },
            code={
                "coding": [
                    {"system": SCT, "code": "80146002", "display": "Appendectomy"}
                ]
            },
            encounter={"reference": f"Encounter/{w['enc1']}"},
            performedPeriod={
                "start": "2023-01-15T09:30:00Z",
                "end": "2023-01-15T10:45:00Z",
            },
            performer=[
                {"actor": {"reference": f"Practitioner/{w['pr']}"}},
                {"actor": {"reference": f"Organization/{w['org']}"}},
            ],
            location={"reference": f"Location/{w['loc']}"},
            reasonCode=[
                {
                    "coding": [
                        {"system": SCT, "code": "74400008", "display": "Appendicitis"}
                    ]
                }
            ],
            reasonReference=[{"reference": f"Condition/{w['cond']}"}],
        ),
    )
    w["b"] = await create_procedure(
        client,
        procedure_body(
            w["p2"],
            "in-progress",
            identifier=[{"system": PROC_IDS, "value": "PR-B"}],
            instantiatesCanonical=["PlanDefinition/5"],
            instantiatesUri=[
                "http://example.org/protocols/mammo",
                "http://other.org/x",
            ],
            category={
                "coding": [
                    {
                        "system": SCT,
                        "code": "103693007",
                        "display": "Diagnostic procedure",
                    }
                ]
            },
            code={
                "coding": [
                    {"system": SCT, "code": "71651007", "display": "Mammography"}
                ]
            },
            encounter={"reference": f"Encounter/{w['enc2']}"},
            performedDateTime="2024-02",
            partOf=[{"reference": f"Procedure/{w['a']}"}],
            performer=[{"actor": {"reference": f"Patient/{w['p2']}"}}],
            reasonCode=[{"text": "Screening"}],
            reasonReference=[
                {"reference": f"Procedure/{w['a']}"},
                {"reference": "Observation/160001"},
            ],
        ),
    )
    w["c"] = await create_procedure(
        client,
        procedure_body(
            w["p1"],
            "not-done",
            code={"text": "Physio"},
            performedString="last spring",
            performer=[{"actor": {"reference": f"RelatedPerson/{w['rp']}"}}],
            reasonCode=[{"text": "Sports injury"}],
        ),
    )
    w["d"] = await create_procedure(
        client, {"status": "preparation", "subject": {"reference": "Group/5"}}
    )
    w["e"] = await create_procedure(
        client,
        {
            "status": "entered-in-error",
            "subject": {
                "identifier": {"system": "urn:pts", "value": "P-9"},
                "display": "External",
            },
            "instantiatesCanonical": ["http://example.org/PlanDefinition/pd1"],
            "performedPeriod": {"start": "2019-01-01"},
            "performer": [
                {"actor": {"identifier": {"system": "urn:who", "value": "W-1"}}}
            ],
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


# ── _id / _lastUpdated ───────────────────────────────────────────────────────


async def test_id(client, world):
    assert await _keys(client, world, _id=str(world["a"])) == {"a"}
    assert await _keys(client, world, _id="999999") == set()
    assert await _keys(client, world, **{"_id:not": str(world["a"])}) == ALL - {"a"}


async def test_last_updated(client, world):
    assert await _keys(client, world, _lastUpdated="ge2020-01-01") == ALL
    assert await _keys(client, world, _lastUpdated="lt2020-01-01") == set()


# ── status ───────────────────────────────────────────────────────────────────


async def test_status(client, world):
    assert await _keys(client, world, status="completed") == {"a"}
    assert await _keys(client, world, status="in-progress") == {
        "b"
    }  # the real FHIR code, not `in_progress`
    assert await _keys(client, world, status="not-done,preparation") == {"c", "d"}
    assert await _keys(client, world, status=f"{EVENT_STATUS}|entered-in-error") == {
        "e"
    }
    assert await _keys(client, world, status="http://wrong|completed") == set()
    assert (
        await _keys(client, world, status="|completed") == set()
    )  # a code with no system is not this one
    assert await _keys(client, world, status="nonsense") == set()
    assert await _keys(client, world, **{"status:not": "completed"}) == {
        "b",
        "c",
        "d",
        "e",
    }
    assert (
        await _status(client, **{"status:text": "completed"}) == 400
    )  # a plain code has no :text


# ── category / code / reason-code ────────────────────────────────────────────


async def test_category(client, world):
    assert await _keys(client, world, category="387713003") == {"a"}
    assert await _keys(client, world, category=f"{SCT}|103693007") == {"b"}
    assert await _keys(client, world, category="387713003,103693007") == {"a", "b"}
    assert await _keys(client, world, category="http://wrong|387713003") == set()
    assert await _keys(client, world, **{"category:text": "surgical"}) == {"a"}
    assert await _keys(client, world, **{"category:missing": "true"}) == {"c", "d", "e"}


async def test_code(client, world):
    assert await _keys(client, world, code="80146002") == {"a"}
    assert await _keys(client, world, code="71651007") == {"b"}
    assert await _keys(client, world, code=f"{SCT}|") == {"a", "b"}
    assert await _keys(client, world, **{"code:text": "physio"}) == {
        "c"
    }  # a text-only concept is found
    assert await _keys(client, world, **{"code:text": "mammo"}) == {
        "b"
    }  # Coding.display
    assert await _keys(client, world, **{"code:not": "80146002"}) == {
        "b",
        "c",
        "d",
        "e",
    }
    assert await _keys(client, world, **{"code:missing": "true"}) == {"d", "e"}


async def test_reason_code(client, world):
    assert await _keys(client, world, **{"reason-code": "74400008"}) == {"a"}
    assert await _keys(client, world, **{"reason-code:text": "screen"}) == {"b"}
    assert await _keys(client, world, **{"reason-code:text": "sports"}) == {"c"}
    assert await _keys(client, world, **{"reason-code:missing": "true"}) == {"d", "e"}


# ── identifier ───────────────────────────────────────────────────────────────


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="PR-A") == {"a"}
    assert await _keys(client, world, identifier=f"{PROC_IDS}|PR-B") == {"b"}
    assert await _keys(client, world, identifier="PR-A,PR-B") == {"a", "b"}
    assert await _keys(client, world, identifier="urn:other|PR-A") == set()


async def test_identifier_text_of_type_not_and_missing(client, world):
    assert await _keys(client, world, **{"identifier:text": "procedure"}) == {"a"}
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|PRN|PR-A"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|PRN|PR-B"})
        == set()
    )
    assert await _keys(client, world, **{"identifier:not": "PR-A"}) == ALL - {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


# ── date (performed[x] as a dateTime or a Period) ────────────────────────────


async def test_date_reads_a_period_or_a_datetime(client, world):
    assert await _keys(client, world, date="2023-01-15") == {
        "a"
    }  # the day holds the whole period
    assert (
        await _keys(client, world, date="2023-01-15T09:30") == set()
    )  # a minute does not
    assert await _keys(client, world, date="2024-02") == {"b"}  # the dateTime `2024-02`
    assert await _keys(client, world, date="2024") == {"b"}
    assert await _keys(client, world, date="ge2024") == {
        "b",
        "e",
    }  # e's period is open-ended
    assert await _keys(client, world, date="lt2020") == {"e"}
    assert await _keys(client, world, date="lt2019") == set()  # e starts on 2019-01-01
    assert await _keys(client, world, **{"date:missing": "true"}) == {
        "c",
        "d",
    }  # performedString is not a date
    assert await _status(client, date="banana") == 400


# ── patient / subject / encounter / location ─────────────────────────────────


async def test_subject_is_multi_target(client, world):
    assert (
        await _status(client, subject=str(world["p1"])) == 400
    )  # a bare id with two targets is ambiguous
    assert await _keys(client, world, subject=f"Patient/{world['p1']}") == {"a", "c"}
    assert await _keys(client, world, subject="Group/5") == {"d"}
    assert await _keys(client, world, **{"subject:Patient": str(world["p2"])}) == {"b"}
    assert (
        await _keys(client, world, subject=f"Group/{world['p1']}") == set()
    )  # the type is part of the match
    assert await _keys(client, world, **{"subject:identifier": "urn:pts|P-9"}) == {"e"}
    assert await _keys(client, world, **{"subject:missing": "false"}) == ALL


async def test_patient_is_subject_narrowed_to_patients(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {
        "a",
        "c",
    }  # a bare id works: one target
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"b"}
    assert await _keys(client, world, patient=f"{world['p1']},{world['p2']}") == {
        "a",
        "b",
        "c",
    }
    assert await _keys(client, world, patient="999999") == set()
    assert await _keys(client, world, **{"patient:missing": "true"}) == {
        "d",
        "e",
    }  # a Group / logical subject
    assert await _keys(client, world, **{"patient:missing": "false"}) == {"a", "b", "c"}


async def test_encounter_and_location(client, world):
    assert await _keys(client, world, encounter=str(world["enc1"])) == {"a"}
    assert await _keys(client, world, encounter=f"Encounter/{world['enc2']}") == {"b"}
    assert await _keys(client, world, **{"encounter:missing": "true"}) == {
        "c",
        "d",
        "e",
    }
    assert await _keys(client, world, location=str(world["loc"])) == {"a"}
    assert await _keys(client, world, location=f"Location/{world['loc']}") == {"a"}
    assert await _keys(client, world, **{"location:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }


# ── performer (multi-target child) ───────────────────────────────────────────


async def test_performer(client, world):
    assert await _status(client, performer=str(world["pr"])) == 400
    assert await _keys(client, world, performer=f"Practitioner/{world['pr']}") == {"a"}
    assert await _keys(client, world, performer=f"Organization/{world['org']}") == {
        "a"
    }  # a has two performers
    assert await _keys(client, world, performer=f"Patient/{world['p2']}") == {"b"}
    assert await _keys(
        client, world, **{"performer:RelatedPerson": str(world["rp"])}
    ) == {"c"}
    assert await _keys(client, world, **{"performer:identifier": "urn:who|W-1"}) == {
        "e"
    }
    assert (
        await _keys(client, world, performer=f"Practitioner/{world['p1']}") == set()
    )  # the type is part of the match
    assert await _keys(client, world, **{"performer:missing": "true"}) == {"d"}


# ── part-of / reason-reference / based-on ────────────────────────────────────


async def test_part_of(client, world):
    assert (
        await _status(client, **{"part-of": str(world["a"])}) == 400
    )  # three targets: needs a type
    assert await _keys(client, world, **{"part-of": f"Procedure/{world['a']}"}) == {"b"}
    assert await _keys(client, world, **{"part-of:Procedure": str(world["a"])}) == {"b"}
    assert (
        await _keys(client, world, **{"part-of": f"Observation/{world['a']}"}) == set()
    )
    assert await _keys(client, world, **{"part-of:missing": "true"}) == {
        "a",
        "c",
        "d",
        "e",
    }


async def test_reason_reference(client, world):
    cond = world["cond"]
    assert await _status(client, **{"reason-reference": str(cond)}) == 400
    assert await _keys(client, world, **{"reason-reference": f"Condition/{cond}"}) == {
        "a"
    }
    assert await _keys(
        client, world, **{"reason-reference": f"Procedure/{world['a']}"}
    ) == {"b"}
    assert await _keys(client, world, **{"reason-reference:Observation": "160001"}) == {
        "b"
    }
    assert await _keys(
        client, world, **{"reason-reference": f"Condition/{cond},Observation/160001"}
    ) == {"a", "b"}
    assert await _keys(client, world, **{"reason-reference:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


async def test_based_on(client, world):
    assert await _status(client, **{"based-on": "80001"}) == 400
    assert await _keys(client, world, **{"based-on": "ServiceRequest/80001"}) == {"a"}
    assert await _keys(client, world, **{"based-on:ServiceRequest": "80001"}) == {"a"}
    assert await _keys(client, world, **{"based-on:CarePlan": "80001"}) == set()
    assert await _keys(client, world, **{"based-on:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }


# ── instantiates-canonical / instantiates-uri ────────────────────────────────


async def test_instantiates_canonical(client, world):
    versioned = "http://example.org/PlanDefinition/pd1"
    assert await _keys(
        client, world, **{"instantiates-canonical": f"{versioned}|1.0"}
    ) == {"a"}
    assert await _keys(client, world, **{"instantiates-canonical": versioned}) == {
        "a",
        "e",
    }  # a versionless search finds versions
    assert (
        await _keys(client, world, **{"instantiates-canonical": f"{versioned}|2.0"})
        == set()
    )
    assert await _keys(
        client, world, **{"instantiates-canonical": "PlanDefinition/5"}
    ) == {"b"}  # a relative form
    assert await _keys(
        client, world, **{"instantiates-canonical:PlanDefinition": "5"}
    ) == {"b"}
    assert (
        await _keys(client, world, **{"instantiates-canonical": "Questionnaire/5"})
        == set()
    )
    assert await _keys(client, world, **{"instantiates-canonical:missing": "true"}) == {
        "c",
        "d",
    }


async def test_instantiates_uri(client, world):
    assert await _keys(
        client,
        world,
        **{"instantiates-uri": "http://example.org/protocols/appendectomy"},
    ) == {"a"}
    assert await _keys(client, world, **{"instantiates-uri": "http://other.org/x"}) == {
        "b"
    }  # b has two URIs
    assert (
        await _keys(
            client, world, **{"instantiates-uri": "http://example.org/protocols"}
        )
        == set()
    )  # exact, not a prefix
    assert (
        await _keys(
            client,
            world,
            **{"instantiates-uri": "http://example.org/Protocols/appendectomy"},
        )
        == set()
    )  # case-sensitive
    assert await _keys(
        client, world, **{"instantiates-uri:below": "http://example.org/protocols"}
    ) == {"a", "b"}
    assert await _keys(
        client, world, **{"instantiates-uri:below": "http://other.org"}
    ) == {"b"}
    assert await _keys(
        client,
        world,
        **{"instantiates-uri:above": "http://example.org/protocols/appendectomy/step1"},
    ) == {"a"}
    assert (
        await _keys(
            client, world, **{"instantiates-uri:above": "http://example.org/protocols"}
        )
        == set()
    )
    assert await _keys(
        client,
        world,
        **{
            "instantiates-uri": "http://example.org/protocols/appendectomy,http://other.org/x"
        },
    ) == {"a", "b"}
    assert await _keys(client, world, **{"instantiates-uri:missing": "true"}) == {
        "c",
        "d",
        "e",
    }
    assert await _status(client, **{"instantiates-uri:contains": "x"}) == 400


# ── chaining ─────────────────────────────────────────────────────────────────


async def test_chains(client, world):
    assert await _keys(client, world, **{"patient.family": "Windsor"}) == {"a", "c"}
    assert await _keys(client, world, **{"subject:Patient.name": "Ben"}) == {"b"}
    assert await _keys(client, world, **{"encounter.status": "in-progress"}) == {
        "a",
        "b",
    }
    assert await _keys(client, world, **{"location.name": "North"}) == {"a"}
    assert await _keys(
        client, world, **{"performer:Practitioner.family": "Careful"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"performer:Organization.name": "Providing"}
    ) == {"a"}
    assert await _keys(client, world, **{"performer:RelatedPerson.name": "Gray"}) == {
        "c"
    }
    assert await _keys(client, world, **{"part-of:Procedure.status": "completed"}) == {
        "b"
    }
    assert await _keys(
        client, world, **{"reason-reference:Procedure.code": "80146002"}
    ) == {"b"}
    assert await _keys(
        client, world, **{"reason-reference:Condition.patient": str(world["p1"])}
    ) == {"a"}


async def test_bad_chains_are_400(client, world):
    assert await _status(client, **{"patient.nonsense": "x"}) == 400
    assert (
        await _status(client, **{"subject.family": "x"}) == 400
    )  # an untyped multi-target cannot be chained
    assert (
        await _status(client, **{"subject:Group.name": "x"}) == 400
    )  # Group is not searchable here
    assert await _status(client, **{"performer:Device.x": "x"}) == 400
    assert (
        await _status(client, **{"based-on:CarePlan.code": "x"}) == 400
    )  # not a resource here
    assert (
        await _status(client, **{"code.x": "y"}) == 400
    )  # a token cannot be chained through


# ── _sort / _count / _offset / _total ────────────────────────────────────────


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "based-on",
        "category",
        "code",
        "date",
        "encounter",
        "identifier",
        "instantiates-canonical",
        "instantiates-uri",
        "location",
        "part-of",
        "patient",
        "performer",
        "reason-code",
        "reason-reference",
        "status",
        "subject",
        "_id",
    ):
        assert (await _search(client, _sort=key))["total"] == 5, key
    assert await _status(client, _sort="note") == 400


async def test_sort_by_date_and_status(client, world):
    async def ids(**params):
        return [
            int(e["resource"]["id"]) for e in (await _search(client, **params))["entry"]
        ]

    assert await ids(**{"date:missing": "false", "_sort": "date"}) == [
        world["e"],
        world["a"],
        world["b"],
    ]
    assert await ids(**{"date:missing": "false", "_sort": "-date"}) == [
        world["b"],
        world["a"],
        world["e"],
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
    assert resource["status"] == "completed"
    assert "performer" not in resource and "note" not in resource


# ── _include / _revinclude ───────────────────────────────────────────────────


async def test_include_subject_encounter_and_location(client, world):
    ids = f"{world['a']},{world['b']},{world['c']}"
    for param in ("patient", "subject"):
        bundle = await _search(client, _id=ids, _include=f"Procedure:{param}")
        assert _of_type(bundle, "Patient", "include") == {
            str(world["p1"]),
            str(world["p2"]),
        }
    bundle = await _search(client, _id=ids, _include="Procedure:encounter")
    assert _of_type(bundle, "Encounter", "include") == {
        str(world["enc1"]),
        str(world["enc2"]),
    }
    bundle = await _search(client, _id=ids, _include="Procedure:location")
    assert _of_type(bundle, "Location", "include") == {str(world["loc"])}


async def test_include_skips_non_resources(client, world):
    bundle = await _search(
        client, _id=f"{world['d']},{world['e']}", _include="Procedure:subject"
    )
    assert (
        _of_type(bundle, "Patient", "include") == set()
    )  # a Group and a logical subject add nothing


async def test_include_performer_brings_in_every_modeled_type(client, world):
    ids = f"{world['a']},{world['b']},{world['c']},{world['e']}"
    bundle = await _search(client, _id=ids, _include="Procedure:performer")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "Organization", "include") == {str(world["org"])}
    assert _of_type(bundle, "Patient", "include") == {str(world["p2"])}
    assert _of_type(bundle, "RelatedPerson", "include") == {str(world["rp"])}
    bundle = await _search(client, _id=ids, _include="Procedure:performer:Practitioner")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "Organization", "include") == set()


async def test_include_part_of_and_reason_reference(client, world):
    bundle = await _search(client, _id=str(world["b"]), _include="Procedure:part-of")
    assert _of_type(bundle, "Procedure", "include") == {str(world["a"])}
    bundle = await _search(
        client, _id=f"{world['a']},{world['b']}", _include="Procedure:reason-reference"
    )
    assert _of_type(bundle, "Condition", "include") == {str(world["cond"])}
    # `a` is already a match, so it is not repeated as an include.
    assert _of_type(bundle, "Procedure", "include") == set()
    bundle = await _search(
        client, _id=str(world["b"]), _include="Procedure:reason-reference"
    )
    assert _of_type(bundle, "Procedure", "include") == {
        str(world["a"])
    }  # Observation is not a resource here
    bundle = await _search(
        client, _id=str(world["b"]), _include="Procedure:reason-reference:Condition"
    )
    assert _of_type(bundle, "Procedure", "include") == set()


async def _other(client, path, **params) -> dict:
    resp = await client.get(f"{API}/{path}/", params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_revinclude_procedures_on_the_resources_they_point_at(client, world):
    for param in ("patient", "subject"):
        bundle = await _other(
            client, "patients", _id=str(world["p2"]), _revinclude=f"Procedure:{param}"
        )
        assert _of_type(bundle, "Procedure", "include") == {str(world["b"])}
    bundle = await _other(
        client, "patients", _id=str(world["p1"]), _revinclude="Procedure:patient"
    )
    assert _of_type(bundle, "Procedure", "include") == {
        str(world["a"]),
        str(world["c"]),
    }
    bundle = await _other(
        client, "patients", _id=str(world["p2"]), _revinclude="Procedure:performer"
    )
    assert _of_type(bundle, "Procedure", "include") == {str(world["b"])}
    bundle = await _other(
        client, "practitioners", _id=str(world["pr"]), _revinclude="Procedure:performer"
    )
    assert _of_type(bundle, "Procedure", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "related-persons",
        _id=str(world["rp"]),
        _revinclude="Procedure:performer",
    )
    assert _of_type(bundle, "Procedure", "include") == {str(world["c"])}
    bundle = await _other(
        client, "encounters", _id=str(world["enc1"]), _revinclude="Procedure:encounter"
    )
    assert _of_type(bundle, "Procedure", "include") == {str(world["a"])}
    bundle = await _other(
        client, "locations", _id=str(world["loc"]), _revinclude="Procedure:location"
    )
    assert _of_type(bundle, "Procedure", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "conditions",
        _id=str(world["cond"]),
        _revinclude="Procedure:reason-reference",
    )
    assert _of_type(bundle, "Procedure", "include") == {str(world["a"])}


async def test_revinclude_part_of_and_reason_reference_on_procedure(client, world):
    bundle = await _search(client, _id=str(world["a"]), _revinclude="Procedure:part-of")
    assert _of_type(bundle, "Procedure", "include") == {str(world["b"])}
    bundle = await _search(
        client, _id=str(world["a"]), _revinclude="Procedure:reason-reference"
    )
    assert _of_type(bundle, "Procedure", "include") == {str(world["b"])}


async def test_revinclude_what_points_at_a_procedure(client, world):
    ref = f"Procedure/{world['a']}"
    enc = (
        await client.post(
            f"{API}/encounters/",
            json={
                "status": "finished",
                "class": {"code": "AMB"},
                "diagnosis": [{"condition": {"reference": ref}}],
            },
        )
    ).json()["id"]
    appointment = await create_appointment(
        client, appointment_body(world["p1"], reasonReference=[{"reference": ref}])
    )

    def go(**params):
        return _search(client, _id=str(world["a"]), **params)

    assert _of_type(
        await go(_revinclude="Encounter:diagnosis"), "Encounter", "include"
    ) == {enc}
    assert (
        _of_type(
            await go(_revinclude="Encounter:reason-reference"), "Encounter", "include"
        )
        == set()
    )
    assert _of_type(
        await go(_revinclude="Appointment:reason-reference"), "Appointment", "include"
    ) == {str(appointment)}
    # ...and the other way round: _include the Procedures an Encounter / Appointment point at.
    bundle = await _other(client, "encounters", _id=enc, _include="Encounter:diagnosis")
    assert _of_type(bundle, "Procedure", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "appointments",
        _id=str(appointment),
        _include="Appointment:reason-reference",
    )
    assert _of_type(bundle, "Procedure", "include") == {str(world["a"])}
    # And a Procedure can be chained to from them.
    bundle = await _other(
        client, "encounters", **{"diagnosis:Procedure.status": "completed"}
    )
    assert _ids(bundle) == {int(enc)}
    bundle = await _other(
        client, "appointments", **{"reason-reference:Procedure.status": "completed"}
    )
    assert _ids(bundle) == {appointment}
    bundle = await _other(
        client, "appointments", **{"reason-reference:Procedure.status": "stopped"}
    )
    assert _ids(bundle) == set()


async def test_revinclude_is_tenant_scoped(client, other_client):
    from app.auth.dependencies import get_current_user
    from app.main import app
    from tests.conftest import make_test_user
    from tests.integration.procedure.conftest import PROCEDURE_PERMS

    def as_user(**kw):
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=PROCEDURE_PERMS, **kw
        )

    as_user()
    mine = await create_patient(client)
    await create_procedure(client, procedure_body(mine))
    as_user(sub="u-other", org_id="org-other")
    try:
        # The other org cannot see the patient, so nothing reaches its procedures.
        bundle = await _other(
            other_client, "patients", _id=str(mine), _revinclude="Procedure:patient"
        )
        assert bundle["total"] == 0 and "entry" not in bundle
        theirs = await create_patient(other_client)
        bundle = await _other(
            other_client, "patients", _id=str(theirs), _revinclude="Procedure:patient"
        )
        assert _of_type(bundle, "Procedure", "include") == set()
    finally:
        as_user()


# ── combination rules / lenient vs strict ────────────────────────────────────


async def test_params_are_anded(client, world):
    assert await _keys(client, world, status="completed", category="387713003") == {"a"}
    assert await _keys(client, world, status="completed", category="103693007") == set()
    assert await _keys(client, world, patient=str(world["p1"]), status="not-done") == {
        "c"
    }
    assert await _keys(client, world, code="80146002", date="ge2023") == {"a"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"status:above": "x"}) == 400
    assert await _status(client, **{"patient:text": "x"}) == 400
    assert await _status(client, **{"date:exact": "2020"}) == 400
    assert await _status(client, **{"instantiates-canonical:identifier": "x"}) == 400


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
        BASE + "/_search", data={"status": "in-progress", "patient": str(world["p2"])}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, status="in-progress")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/procedures/{world['b']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "Procedure"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
