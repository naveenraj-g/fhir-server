"""FHIR R4 search over CommunicationRequest (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/communicationrequest.html#search).

One block per search parameter - `status` and `priority` (enums), the CodeableConcept tokens
(`category`, `medium`), `identifier` and `group-identifier`, the dates (`authored`, `occurrence`),
the Reference(Any) element `based-on`, the multi-target `subject`, `requester`, `recipient` and
`sender` with the narrowed `patient`, and the single-target `encounter` and `replaces` - then
chaining, `_include`/`_revinclude`, result parameters, combination rules, lenient vs strict
handling and POST _search. R4 defines no parameter for `about`, `payload`, `reasonCode`,
`reasonReference`, `statusReason`, `doNotPerform` or `note`.
"""

import pytest

from tests.integration.communication_request.support import (
    API,
    BASE,
    CATEGORY,
    CR_IDS,
    MEDIUM,
    V2_0203,
    care_team_body,
    communication_body,
    communication_request_body,
    concept,
    create_care_team,
    create_communication,
    create_communication_request,
    create_encounter,
    create_group,
    create_organization,
    create_patient,
    create_practitioner,
    create_service_request,
    encounter_body,
    group_body,
    service_request_body,
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
    """Two patients, a group, an organization, a practitioner, a care team, an encounter and a
    service request, and five communication requests with distinct, searchable values. Returns
    {key: id}.

      a  active, urgent; categories reminder and alert; medium WRITTEN; id CR-A; group G-1; for
         p1; in the encounter; requested and sent by the practitioner to p1 and the organization;
         based on the service request and a Device; replaces `e`; authored 2026-01-15T09:00,
         occurring 2026-02-01T09:00
      b  draft; for the group; requested and sent by the organization to the group and the care
         team; authored in 2026-06; occurring in 2026-07
      c  completed; for a logical subject; based on a Device; priority stat; a requester that is
         a Device
      d  on-hold; for p2; a text-only medium; occurrencePeriod only (not searched)
      e  revoked; nothing else (replaced by `a`)
    """
    w = {}
    w["p1"] = await create_patient(client)
    w["p2"] = await create_patient(client)
    w["grp"] = await create_group(client, group_body())
    w["org"] = await create_organization(client, name="Comm Org")
    w["pr"] = await create_practitioner(client)
    w["ct"] = await create_care_team(client, care_team_body())
    w["enc"] = await create_encounter(
        client, encounter_body(subject={"reference": f"Patient/{w['p1']}"})
    )
    w["sr"] = await create_service_request(client, service_request_body(w["p1"]))
    w["e"] = await create_communication_request(
        client, communication_request_body(status="revoked")
    )
    w["a"] = await create_communication_request(
        client,
        communication_request_body(
            status="active",
            priority="urgent",
            identifier=[
                {
                    "system": CR_IDS,
                    "value": "CR-A",
                    "type": {
                        "coding": [{"system": V2_0203, "code": "FILL"}],
                        "text": "Request id",
                    },
                }
            ],
            groupIdentifier={"system": "urn:groups", "value": "G-1"},
            category=[
                concept(CATEGORY, "reminder", "Reminder"),
                concept(CATEGORY, "alert"),
            ],
            medium=[concept(MEDIUM, "WRITTEN", "written")],
            subject={"reference": f"Patient/{w['p1']}"},
            encounter={"reference": f"Encounter/{w['enc']}"},
            requester={"reference": f"Practitioner/{w['pr']}"},
            sender={"reference": f"Practitioner/{w['pr']}"},
            recipient=[
                {"reference": f"Patient/{w['p1']}"},
                {"reference": f"Organization/{w['org']}"},
            ],
            basedOn=[
                {"reference": f"ServiceRequest/{w['sr']}"},
                {"reference": "Device/7"},
            ],
            replaces=[{"reference": f"CommunicationRequest/{w['e']}"}],
            authoredOn="2026-01-15T09:00:00Z",
            occurrenceDateTime="2026-02-01T09:00:00Z",
        ),
    )
    w["b"] = await create_communication_request(
        client,
        communication_request_body(
            status="draft",
            subject={"reference": f"Group/{w['grp']}"},
            requester={"reference": f"Organization/{w['org']}"},
            sender={"reference": f"Organization/{w['org']}"},
            recipient=[
                {"reference": f"Group/{w['grp']}"},
                {"reference": f"CareTeam/{w['ct']}"},
            ],
            authoredOn="2026-06",
            occurrenceDateTime="2026-07",
        ),
    )
    w["c"] = await create_communication_request(
        client,
        communication_request_body(
            status="completed",
            priority="stat",
            subject={
                "identifier": {"system": "urn:subj", "value": "S-9"},
                "display": "Someone",
            },
            requester={"reference": "Device/3"},
            basedOn=[{"reference": "Device/7"}],
        ),
    )
    w["d"] = await create_communication_request(
        client,
        communication_request_body(
            status="on-hold",
            subject={"reference": f"Patient/{w['p2']}"},
            medium=[{"text": "Carrier pigeon"}],
            occurrencePeriod={"start": "2026-03-01", "end": "2026-03-31"},
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


# -- _id / _lastUpdated / status / priority --------------------------------------------------


async def test_id(client, world):
    assert await _keys(client, world, _id=str(world["a"])) == {"a"}
    assert await _keys(client, world, _id="999999") == set()
    assert await _keys(client, world, **{"_id:not": str(world["a"])}) == ALL - {"a"}


async def test_last_updated(client, world):
    assert await _keys(client, world, _lastUpdated="ge2020-01-01") == ALL
    assert await _keys(client, world, _lastUpdated="lt2020-01-01") == set()


async def test_status(client, world):
    assert await _keys(client, world, status="active") == {"a"}
    assert await _keys(client, world, status="on-hold") == {"d"}  # the real FHIR code
    assert await _keys(client, world, status="draft,completed") == {"b", "c"}
    assert await _keys(
        client, world, status="http://hl7.org/fhir/request-status|revoked"
    ) == {"e"}
    assert await _keys(client, world, status="http://wrong|active") == set()
    assert await _keys(client, world, status="no-such-code") == set()
    assert await _keys(client, world, **{"status:not": "active"}) == ALL - {"a"}
    assert await _keys(client, world, **{"status:missing": "true"}) == set()


async def test_priority(client, world):
    assert await _keys(client, world, priority="urgent") == {"a"}
    assert await _keys(client, world, priority="urgent,stat") == {"a", "c"}
    assert await _keys(
        client, world, priority="http://hl7.org/fhir/request-priority|stat"
    ) == {"c"}
    assert await _keys(client, world, priority="http://wrong|stat") == set()
    assert await _keys(client, world, priority="no-such-code") == set()
    assert await _keys(client, world, **{"priority:missing": "true"}) == {"b", "d", "e"}
    assert await _keys(client, world, **{"priority:not": "urgent"}) == ALL - {"a"}


# -- category / medium / identifier / group-identifier ---------------------------------------


async def test_category_reads_every_entry(client, world):
    assert await _keys(client, world, category="reminder") == {"a"}
    assert await _keys(client, world, category="alert") == {"a"}  # the second category
    assert await _keys(client, world, category=f"{CATEGORY}|alert") == {"a"}
    assert await _keys(client, world, category="http://wrong|alert") == set()
    assert await _keys(client, world, **{"category:text": "remin"}) == {"a"}  # display
    assert await _keys(client, world, **{"category:missing": "true"}) == ALL - {"a"}


async def test_medium(client, world):
    assert await _keys(client, world, medium="WRITTEN") == {"a"}
    assert await _keys(client, world, medium=f"{MEDIUM}|WRITTEN") == {"a"}
    assert await _keys(client, world, **{"medium:text": "carrier"}) == {
        "d"
    }  # text only
    assert await _keys(client, world, **{"medium:missing": "true"}) == {"b", "c", "e"}


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="CR-A") == {"a"}
    assert await _keys(client, world, identifier=f"{CR_IDS}|CR-A") == {"a"}
    assert await _keys(client, world, identifier="urn:wrong|CR-A") == set()
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|FILL|CR-A"}
    ) == {"a"}
    assert await _keys(client, world, **{"identifier:text": "request id"}) == {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == ALL - {"a"}


async def test_group_identifier(client, world):
    assert await _keys(client, world, **{"group-identifier": "G-1"}) == {"a"}
    assert await _keys(client, world, **{"group-identifier": "urn:groups|G-1"}) == {"a"}
    assert await _keys(client, world, **{"group-identifier": "urn:other|G-1"}) == set()
    assert await _keys(client, world, **{"group-identifier": "|G-1"}) == set()
    assert await _keys(client, world, **{"group-identifier:not": "G-1"}) == ALL - {"a"}
    assert await _keys(client, world, **{"group-identifier:missing": "true"}) == ALL - {
        "a"
    }


# -- authored / occurrence -------------------------------------------------------------------


async def test_authored(client, world):
    assert await _keys(client, world, authored="2026-01-15") == {"a"}
    assert await _keys(client, world, authored="2026-06") == {"b"}  # a partial date
    assert await _keys(client, world, authored="ge2026-01-01") == {"a", "b"}
    assert await _keys(client, world, authored="lt2026-02-01") == {"a"}
    assert await _keys(client, world, **{"authored:missing": "true"}) == {"c", "d", "e"}


async def test_occurrence_reads_a_datetime_only(client, world):
    assert await _keys(client, world, occurrence="2026-02-01") == {"a"}
    assert await _keys(client, world, occurrence="2026-07") == {"b"}
    assert await _keys(client, world, occurrence="ge2026-02-01") == {"a", "b"}
    # `d` has only an occurrencePeriod: R4's expression is `(occurrence as dateTime)`
    assert await _keys(client, world, occurrence="2026-03-15") == set()
    assert await _keys(client, world, **{"occurrence:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


# -- subject / patient / encounter -----------------------------------------------------------


async def test_subject_is_multi_target(client, world):
    assert await _status(client, subject=str(world["p1"])) == 400  # bare id: ambiguous
    assert await _keys(client, world, subject=f"Patient/{world['p1']}") == {"a"}
    assert await _keys(client, world, **{"subject:Patient": str(world["p2"])}) == {"d"}
    assert await _keys(client, world, subject=f"Group/{world['grp']}") == {"b"}
    assert await _keys(client, world, subject=f"Group/{world['p1']}") == set()
    assert await _keys(client, world, **{"subject:identifier": "urn:subj|S-9"}) == {"c"}
    assert await _keys(client, world, **{"subject:missing": "true"}) == {"e"}


async def test_patient_is_subject_narrowed_to_patients(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {
        "a"
    }  # a bare id works
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"d"}
    assert await _keys(client, world, patient=str(world["grp"])) == set()
    assert await _keys(client, world, **{"patient:missing": "true"}) == {"b", "c", "e"}


async def test_encounter_has_one_target_so_a_bare_id_works(client, world):
    assert await _keys(client, world, encounter=str(world["enc"])) == {"a"}
    assert await _keys(client, world, **{"encounter:missing": "true"}) == ALL - {"a"}


# -- requester / sender / recipient ----------------------------------------------------------


async def test_requester_and_sender_are_multi_target(client, world):
    assert await _status(client, requester=str(world["pr"])) == 400
    assert await _keys(client, world, requester=f"Practitioner/{world['pr']}") == {"a"}
    assert await _keys(client, world, requester=f"Organization/{world['org']}") == {"b"}
    assert await _keys(client, world, requester="Device/3") == {"c"}  # stored as sent
    assert await _keys(client, world, **{"requester:missing": "true"}) == {"d", "e"}
    assert await _status(client, sender=str(world["pr"])) == 400
    assert await _keys(client, world, sender=f"Practitioner/{world['pr']}") == {"a"}
    assert await _keys(client, world, sender=f"Organization/{world['org']}") == {"b"}
    assert await _keys(client, world, **{"sender:missing": "true"}) == {"c", "d", "e"}


async def test_recipient_is_multi_target(client, world):
    assert await _status(client, recipient=str(world["p1"])) == 400
    assert await _keys(client, world, recipient=f"Patient/{world['p1']}") == {"a"}
    assert await _keys(client, world, recipient=f"Organization/{world['org']}") == {"a"}
    assert await _keys(client, world, recipient=f"Group/{world['grp']}") == {"b"}
    assert await _keys(client, world, **{"recipient:CareTeam": str(world["ct"])}) == {
        "b"
    }
    assert await _keys(client, world, **{"recipient:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


# -- based-on (Reference(Any)) / replaces ----------------------------------------------------


async def test_based_on_is_reference_any_and_reads_every_entry(client, world):
    assert await _status(client, **{"based-on": str(world["sr"])}) == 400
    assert await _keys(
        client, world, **{"based-on": f"ServiceRequest/{world['sr']}"}
    ) == {"a"}
    assert await _keys(client, world, **{"based-on": "Device/7"}) == {"a", "c"}
    assert await _keys(client, world, **{"based-on:missing": "true"}) == {"b", "d", "e"}


async def test_replaces_has_one_target_so_a_bare_id_works(client, world):
    assert await _keys(client, world, replaces=str(world["e"])) == {"a"}
    assert await _keys(
        client, world, replaces=f"CommunicationRequest/{world['e']}"
    ) == {"a"}
    assert await _keys(client, world, **{"replaces:missing": "true"}) == ALL - {"a"}


# -- chaining --------------------------------------------------------------------------------


async def test_chains(client, world):
    assert await _keys(client, world, **{"patient.active": "true"}) == {"a", "d"}
    assert await _keys(client, world, **{"subject:Group.type": "person"}) == {"b"}
    assert await _keys(
        client, world, **{"requester:Organization.name": "Comm Org"}
    ) == {"b"}
    assert await _keys(client, world, **{"sender:Organization.name": "Comm Org"}) == {
        "b"
    }
    assert await _keys(
        client, world, **{"recipient:Organization.name": "Comm Org"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"based-on:ServiceRequest.status": "active"}
    ) == {"a"}
    assert await _keys(client, world, **{"replaces.status": "revoked"}) == {"a"}
    assert await _keys(client, world, **{"encounter.status": "in-progress"}) == {"a"}


async def test_bad_chains_are_400(client, world):
    assert await _status(client, **{"patient.nonsense": "x"}) == 400
    assert (
        await _status(client, **{"subject.active": "x"}) == 400
    )  # untyped multi-target
    assert (
        await _status(client, **{"based-on.status": "x"}) == 400
    )  # untyped Reference(Any)
    assert (
        await _status(client, **{"recipient.name": "x"}) == 400
    )  # untyped multi-target
    assert (
        await _status(client, **{"requester:Device.name": "x"}) == 400
    )  # Device is not a resource here
    assert (
        await _status(client, **{"status.x": "y"}) == 400
    )  # a token cannot be chained


# -- _sort / _count / _offset / _total -------------------------------------------------------


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "authored",
        "based-on",
        "category",
        "encounter",
        "group-identifier",
        "identifier",
        "medium",
        "occurrence",
        "patient",
        "priority",
        "recipient",
        "replaces",
        "requester",
        "sender",
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
        world["a"],
        world["b"],
    ]
    assert await ids(**{"authored:missing": "false", "_sort": "-authored"}) == [
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
    assert resource["status"] == "active"
    assert "sender" not in resource and "category" not in resource


# -- _include / _revinclude ------------------------------------------------------------------


async def test_include_patient_subject_encounter_requester_sender_and_recipient(
    client, world
):
    ids = ",".join(str(world[k]) for k in KEYS)
    bundle = await _search(client, _id=ids, _include="CommunicationRequest:patient")
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }
    bundle = await _search(client, _id=ids, _include="CommunicationRequest:subject")
    assert _of_type(bundle, "Group", "include") == {str(world["grp"])}
    bundle = await _search(client, _id=ids, _include="CommunicationRequest:encounter")
    assert _of_type(bundle, "Encounter", "include") == {str(world["enc"])}
    bundle = await _search(client, _id=ids, _include="CommunicationRequest:requester")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "Organization", "include") == {str(world["org"])}
    bundle = await _search(client, _id=ids, _include="CommunicationRequest:sender")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    bundle = await _search(client, _id=ids, _include="CommunicationRequest:recipient")
    assert _of_type(bundle, "CareTeam", "include") == {str(world["ct"])}
    assert _of_type(bundle, "Group", "include") == {str(world["grp"])}
    bundle = await _search(
        client, _id=ids, _include="CommunicationRequest:recipient:CareTeam"
    )
    assert _of_type(bundle, "Group", "include") == set()


async def test_include_based_on_and_replaces(client, world):
    bundle = await _search(
        client, _id=str(world["a"]), _include="CommunicationRequest:based-on"
    )
    assert _of_type(bundle, "ServiceRequest", "include") == {str(world["sr"])}
    bundle = await _search(
        client, _id=str(world["a"]), _include="CommunicationRequest:replaces"
    )
    assert _of_type(bundle, "CommunicationRequest", "include") == {str(world["e"])}


async def test_revinclude_on_the_resources_a_request_points_at(client, world):
    bundle = await _other(
        client,
        "patients",
        _id=f"{world['p1']},{world['p2']}",
        _revinclude="CommunicationRequest:patient",
    )
    assert _of_type(bundle, "CommunicationRequest", "include") == {
        str(world["a"]),
        str(world["d"]),
    }
    bundle = await _other(
        client,
        "patients",
        _id=str(world["p1"]),
        _revinclude="CommunicationRequest:recipient",
    )
    assert _of_type(bundle, "CommunicationRequest", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "groups",
        _id=str(world["grp"]),
        _revinclude="CommunicationRequest:subject",
    )
    assert _of_type(bundle, "CommunicationRequest", "include") == {str(world["b"])}
    bundle = await _other(
        client,
        "groups",
        _id=str(world["grp"]),
        _revinclude="CommunicationRequest:recipient",
    )
    assert _of_type(bundle, "CommunicationRequest", "include") == {str(world["b"])}
    bundle = await _other(
        client,
        "encounters",
        _id=str(world["enc"]),
        _revinclude="CommunicationRequest:encounter",
    )
    assert _of_type(bundle, "CommunicationRequest", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "practitioners",
        _id=str(world["pr"]),
        _revinclude="CommunicationRequest:requester",
    )
    assert _of_type(bundle, "CommunicationRequest", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "practitioners",
        _id=str(world["pr"]),
        _revinclude="CommunicationRequest:sender",
    )
    assert _of_type(bundle, "CommunicationRequest", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "organizations",
        _id=str(world["org"]),
        _revinclude="CommunicationRequest:requester",
    )
    assert _of_type(bundle, "CommunicationRequest", "include") == {str(world["b"])}
    bundle = await _other(
        client,
        "organizations",
        _id=str(world["org"]),
        _revinclude="CommunicationRequest:recipient",
    )
    assert _of_type(bundle, "CommunicationRequest", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "care-teams",
        _id=str(world["ct"]),
        _revinclude="CommunicationRequest:recipient",
    )
    assert _of_type(bundle, "CommunicationRequest", "include") == {str(world["b"])}
    bundle = await _search(
        client, _id=str(world["e"]), _revinclude="CommunicationRequest:replaces"
    )
    assert _of_type(bundle, "CommunicationRequest", "include") == {str(world["a"])}


async def test_revinclude_communication_based_on(client, world):
    communication = await create_communication(
        client,
        communication_body(
            basedOn=[{"reference": f"CommunicationRequest/{world['a']}"}]
        ),
    )
    bundle = await _search(
        client, _id=str(world["a"]), _revinclude="Communication:based-on"
    )
    assert _of_type(bundle, "Communication", "include") == {str(communication)}
    # and the other way: a Communication follows its basedOn into CommunicationRequest
    resp = await client.get(
        "/api/fhir/v1/communications/",
        params={
            "based-on:CommunicationRequest.status": "active",
        },
    )
    assert resp.status_code == 200, resp.text
    assert communication in _ids(resp.json())


# -- combination rules / lenient vs strict ---------------------------------------------------


async def test_params_are_anded(client, world):
    assert await _keys(client, world, status="active", category="reminder") == {"a"}
    assert await _keys(client, world, status="draft", category="reminder") == set()
    assert await _keys(
        client, world, patient=str(world["p1"]), authored="ge2026-01-01"
    ) == {"a"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"subject:text": "x"}) == 400
    assert await _status(client, **{"authored:exact": "2020"}) == 400
    assert await _status(client, **{"identifier:below": "x"}) == 400
    assert await _status(client, **{"status:text": "x"}) == 400
    assert await _status(client, authored="banana") == 400
    assert await _status(client, occurrence="banana") == 400


async def test_unknown_param_lenient_vs_strict(client, world):
    lenient = await client.get(BASE + "/", params={"nonsense": "1"})
    assert lenient.status_code == 200
    assert any(e["search"]["mode"] == "outcome" for e in lenient.json()["entry"])
    strict = await client.get(
        BASE + "/", params={"nonsense": "1"}, headers={"Prefer": "handling=strict"}
    )
    assert strict.status_code == 400
    # R4 defines no `about` / `do-not-perform` parameter for CommunicationRequest
    for unknown in ("about", "do-not-perform", "sent", "received"):
        resp = await client.get(
            BASE + "/", params={unknown: "x"}, headers={"Prefer": "handling=strict"}
        )
        assert resp.status_code == 400, unknown


async def test_query_param_refused(client, world):
    assert await _status(client, _query="x") == 400


# -- POST _search / Bundle shape -------------------------------------------------------------


async def test_post_search_form_encoded(client, world):
    resp = await client.post(
        BASE + "/_search", data={"status": "completed", "based-on": "Device/7"}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["c"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, identifier="CR-A")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/communication-requests/{world['a']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "CommunicationRequest"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
