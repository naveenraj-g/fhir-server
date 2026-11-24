"""FHIR R4 search over Communication (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/communication.html#search).

One block per search parameter - `status`, the CodeableConcept tokens (`category`, `medium`),
`identifier`, the dates (`sent`, `received`), `instantiates-canonical` (canonical URLs) and
`instantiates-uri`, the Reference(Any) elements `based-on` and `part-of`, the multi-target
`subject`, `recipient` and `sender` with the narrowed `patient`, and the single-target `encounter`
- then chaining, `_include`/`_revinclude`, result parameters, combination rules, lenient vs strict
handling and POST _search. R4 defines no `priority`, `topic` or `reason-*` parameter.
"""

import pytest

from tests.integration.communication.support import (
    API,
    BASE,
    CATEGORY,
    COMM_IDS,
    MEDIUM,
    PLAN_DEFINITION,
    V2_0203,
    care_team_body,
    communication_body,
    concept,
    create_care_team,
    create_communication,
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
    service request, and five communications with distinct, searchable values. Returns
    {key: id}.

      a  completed; categories notification and alert; medium WRITTEN; id CM-A; for p1; in the
         encounter; sent by the practitioner to p1 and the organization; based on the service
         request and a Device; part of `e`; sent 2026-01-15T09:00, received 09:05; instantiates a
         PlanDefinition (1.0) and a protocol URI
      b  in-progress; for the group; sent by the organization to the group and the care team; sent
         in 2026-06
      c  not-done; for a logical subject; based on a Device; another protocol URI
      d  on-hold; for p2; a text-only medium
      e  preparation; nothing else (the parent of `a`)
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
    w["e"] = await create_communication(
        client, communication_body(status="preparation")
    )
    w["a"] = await create_communication(
        client,
        communication_body(
            status="completed",
            identifier=[
                {
                    "system": COMM_IDS,
                    "value": "CM-A",
                    "type": {
                        "coding": [{"system": V2_0203, "code": "FILL"}],
                        "text": "Comm id",
                    },
                }
            ],
            category=[
                concept(CATEGORY, "notification", "Notification"),
                concept(CATEGORY, "alert"),
            ],
            medium=[concept(MEDIUM, "WRITTEN", "written")],
            subject={"reference": f"Patient/{w['p1']}"},
            encounter={"reference": f"Encounter/{w['enc']}"},
            sender={"reference": f"Practitioner/{w['pr']}"},
            recipient=[
                {"reference": f"Patient/{w['p1']}"},
                {"reference": f"Organization/{w['org']}"},
            ],
            basedOn=[
                {"reference": f"ServiceRequest/{w['sr']}"},
                {"reference": "Device/7"},
            ],
            partOf=[{"reference": f"Communication/{w['e']}"}],
            sent="2026-01-15T09:00:00Z",
            received="2026-01-15T09:05:00Z",
            instantiatesCanonical=[f"{PLAN_DEFINITION}|1.0"],
            instantiatesUri=["http://example.org/protocols/notify"],
        ),
    )
    w["b"] = await create_communication(
        client,
        communication_body(
            status="in-progress",
            subject={"reference": f"Group/{w['grp']}"},
            sender={"reference": f"Organization/{w['org']}"},
            recipient=[
                {"reference": f"Group/{w['grp']}"},
                {"reference": f"CareTeam/{w['ct']}"},
            ],
            sent="2026-06",
        ),
    )
    w["c"] = await create_communication(
        client,
        communication_body(
            status="not-done",
            subject={
                "identifier": {"system": "urn:subj", "value": "S-9"},
                "display": "Someone",
            },
            basedOn=[{"reference": "Device/7"}],
            instantiatesUri=["http://example.org/protocols/other"],
        ),
    )
    w["d"] = await create_communication(
        client,
        communication_body(
            status="on-hold",
            subject={"reference": f"Patient/{w['p2']}"},
            medium=[{"text": "Carrier pigeon"}],
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


# -- _id / _lastUpdated / status -------------------------------------------------------------


async def test_id(client, world):
    assert await _keys(client, world, _id=str(world["a"])) == {"a"}
    assert await _keys(client, world, _id="999999") == set()
    assert await _keys(client, world, **{"_id:not": str(world["a"])}) == ALL - {"a"}


async def test_last_updated(client, world):
    assert await _keys(client, world, _lastUpdated="ge2020-01-01") == ALL
    assert await _keys(client, world, _lastUpdated="lt2020-01-01") == set()


async def test_status(client, world):
    assert await _keys(client, world, status="completed") == {"a"}
    assert await _keys(client, world, status="in-progress") == {
        "b"
    }  # the real FHIR code
    assert await _keys(client, world, status="not-done,on-hold") == {"c", "d"}
    assert await _keys(
        client, world, status="http://hl7.org/fhir/event-status|preparation"
    ) == {"e"}
    assert await _keys(client, world, status="http://wrong|completed") == set()
    assert await _keys(client, world, status="no-such-code") == set()
    assert await _keys(client, world, **{"status:not": "completed"}) == ALL - {"a"}
    assert await _keys(client, world, **{"status:missing": "true"}) == set()


# -- category / medium / identifier ----------------------------------------------------------


async def test_category_reads_every_entry(client, world):
    assert await _keys(client, world, category="notification") == {"a"}
    assert await _keys(client, world, category="alert") == {"a"}  # the second category
    assert await _keys(client, world, category=f"{CATEGORY}|alert") == {"a"}
    assert await _keys(client, world, category="http://wrong|alert") == set()
    assert await _keys(client, world, **{"category:text": "notif"}) == {"a"}  # display
    assert await _keys(client, world, **{"category:missing": "true"}) == ALL - {"a"}


async def test_medium(client, world):
    assert await _keys(client, world, medium="WRITTEN") == {"a"}
    assert await _keys(client, world, medium=f"{MEDIUM}|WRITTEN") == {"a"}
    assert await _keys(client, world, **{"medium:text": "carrier"}) == {
        "d"
    }  # text only
    assert await _keys(client, world, **{"medium:missing": "true"}) == {"b", "c", "e"}


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="CM-A") == {"a"}
    assert await _keys(client, world, identifier=f"{COMM_IDS}|CM-A") == {"a"}
    assert await _keys(client, world, identifier="urn:wrong|CM-A") == set()
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|FILL|CM-A"}
    ) == {"a"}
    assert await _keys(client, world, **{"identifier:text": "comm id"}) == {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == ALL - {"a"}


# -- sent / received -------------------------------------------------------------------------


async def test_sent(client, world):
    assert await _keys(client, world, sent="2026-01-15") == {"a"}
    assert await _keys(client, world, sent="2026-06") == {"b"}  # a partial date
    assert await _keys(client, world, sent="ge2026-01-01") == {"a", "b"}
    assert await _keys(client, world, sent="lt2026-02-01") == {"a"}
    assert await _keys(client, world, **{"sent:missing": "true"}) == {"c", "d", "e"}


async def test_received(client, world):
    assert await _keys(client, world, received="2026-01-15") == {"a"}
    assert await _keys(client, world, received="gt2026-01-16") == set()
    assert await _keys(client, world, **{"received:missing": "true"}) == ALL - {"a"}


# -- instantiates-canonical / instantiates-uri -----------------------------------------------


async def test_instantiates_canonical_matches_versions_of_an_unversioned_url(
    client, world
):
    assert await _keys(
        client, world, **{"instantiates-canonical": f"{PLAN_DEFINITION}|1.0"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"instantiates-canonical": PLAN_DEFINITION}
    ) == {"a"}
    assert (
        await _keys(
            client, world, **{"instantiates-canonical": f"{PLAN_DEFINITION}|2.0"}
        )
        == set()
    )
    assert await _keys(
        client, world, **{"instantiates-canonical:missing": "true"}
    ) == ALL - {"a"}


async def test_instantiates_uri_is_exact_with_below_and_above(client, world):
    assert await _keys(
        client, world, **{"instantiates-uri": "http://example.org/protocols/notify"}
    ) == {"a"}
    assert (
        await _keys(
            client, world, **{"instantiates-uri": "http://example.org/protocols/NOTIFY"}
        )
        == set()
    )  # case-sensitive
    assert await _keys(
        client, world, **{"instantiates-uri:below": "http://example.org/protocols"}
    ) == {"a", "c"}
    assert await _keys(
        client,
        world,
        **{"instantiates-uri:above": "http://example.org/protocols/notify/v2"},
    ) == {"a"}
    assert await _keys(client, world, **{"instantiates-uri:missing": "true"}) == {
        "b",
        "d",
        "e",
    }


# -- subject / patient / encounter ------------------------------------------------------------


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


# -- sender / recipient -----------------------------------------------------------------------


async def test_sender_and_recipient_are_multi_target(client, world):
    assert await _status(client, sender=str(world["pr"])) == 400
    assert await _keys(client, world, sender=f"Practitioner/{world['pr']}") == {"a"}
    assert await _keys(client, world, sender=f"Organization/{world['org']}") == {"b"}
    assert await _keys(client, world, **{"sender:missing": "true"}) == {"c", "d", "e"}
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


# -- based-on / part-of (Reference(Any)) ------------------------------------------------------


async def test_based_on_is_reference_any_and_reads_every_entry(client, world):
    assert await _status(client, **{"based-on": str(world["sr"])}) == 400
    assert await _keys(
        client, world, **{"based-on": f"ServiceRequest/{world['sr']}"}
    ) == {"a"}
    assert await _keys(client, world, **{"based-on": "Device/7"}) == {"a", "c"}
    assert await _keys(client, world, **{"based-on:missing": "true"}) == {"b", "d", "e"}


async def test_part_of_is_reference_any(client, world):
    assert await _status(client, **{"part-of": str(world["e"])}) == 400
    assert await _keys(client, world, **{"part-of": f"Communication/{world['e']}"}) == {
        "a"
    }
    assert await _keys(client, world, **{"part-of:Communication": str(world["e"])}) == {
        "a"
    }
    assert await _keys(client, world, **{"part-of:missing": "true"}) == ALL - {"a"}


# -- chaining --------------------------------------------------------------------------------


async def test_chains(client, world):
    assert await _keys(client, world, **{"patient.active": "true"}) == {"a", "d"}
    assert await _keys(client, world, **{"subject:Group.type": "person"}) == {"b"}
    assert await _keys(client, world, **{"sender:Organization.name": "Comm Org"}) == {
        "b"
    }
    assert await _keys(
        client, world, **{"recipient:Organization.name": "Comm Org"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"based-on:ServiceRequest.status": "active"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"part-of:Communication.status": "preparation"}
    ) == {"a"}
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
        await _status(client, **{"sender:Device.name": "x"}) == 400
    )  # Device is not a resource here
    assert (
        await _status(client, **{"status.x": "y"}) == 400
    )  # a token cannot be chained


# -- _sort / _count / _offset / _total -------------------------------------------------------


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "based-on",
        "category",
        "encounter",
        "identifier",
        "instantiates-canonical",
        "instantiates-uri",
        "medium",
        "part-of",
        "patient",
        "received",
        "recipient",
        "sender",
        "sent",
        "status",
        "subject",
        "_id",
    ):
        assert (await _search(client, _sort=key))["total"] == 5, key


async def test_sort_by_sent(client, world):
    async def ids(**params):
        return [
            int(e["resource"]["id"]) for e in (await _search(client, **params))["entry"]
        ]

    assert await ids(**{"sent:missing": "false", "_sort": "sent"}) == [
        world["a"],
        world["b"],
    ]
    assert await ids(**{"sent:missing": "false", "_sort": "-sent"}) == [
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
    assert resource["status"] == "completed"
    assert "sender" not in resource and "category" not in resource


# -- _include / _revinclude ------------------------------------------------------------------


async def test_include_patient_subject_encounter_sender_and_recipient(client, world):
    ids = ",".join(str(world[k]) for k in KEYS)
    bundle = await _search(client, _id=ids, _include="Communication:patient")
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }
    bundle = await _search(client, _id=ids, _include="Communication:subject")
    assert _of_type(bundle, "Group", "include") == {str(world["grp"])}
    bundle = await _search(client, _id=ids, _include="Communication:encounter")
    assert _of_type(bundle, "Encounter", "include") == {str(world["enc"])}
    bundle = await _search(client, _id=ids, _include="Communication:sender")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "Organization", "include") == {str(world["org"])}
    bundle = await _search(client, _id=ids, _include="Communication:recipient")
    assert _of_type(bundle, "CareTeam", "include") == {str(world["ct"])}
    assert _of_type(bundle, "Group", "include") == {str(world["grp"])}
    bundle = await _search(client, _id=ids, _include="Communication:recipient:CareTeam")
    assert _of_type(bundle, "Group", "include") == set()


async def test_include_based_on_and_part_of(client, world):
    bundle = await _search(
        client, _id=str(world["a"]), _include="Communication:based-on"
    )
    assert _of_type(bundle, "ServiceRequest", "include") == {str(world["sr"])}
    bundle = await _search(
        client, _id=str(world["a"]), _include="Communication:part-of"
    )
    assert _of_type(bundle, "Communication", "include") == {str(world["e"])}


async def test_revinclude_on_the_resources_a_communication_points_at(client, world):
    bundle = await _other(
        client,
        "patients",
        _id=f"{world['p1']},{world['p2']}",
        _revinclude="Communication:patient",
    )
    assert _of_type(bundle, "Communication", "include") == {
        str(world["a"]),
        str(world["d"]),
    }
    bundle = await _other(
        client, "patients", _id=str(world["p1"]), _revinclude="Communication:recipient"
    )
    assert _of_type(bundle, "Communication", "include") == {str(world["a"])}
    bundle = await _other(
        client, "groups", _id=str(world["grp"]), _revinclude="Communication:subject"
    )
    assert _of_type(bundle, "Communication", "include") == {str(world["b"])}
    bundle = await _other(
        client, "groups", _id=str(world["grp"]), _revinclude="Communication:recipient"
    )
    assert _of_type(bundle, "Communication", "include") == {str(world["b"])}
    bundle = await _other(
        client,
        "encounters",
        _id=str(world["enc"]),
        _revinclude="Communication:encounter",
    )
    assert _of_type(bundle, "Communication", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "practitioners",
        _id=str(world["pr"]),
        _revinclude="Communication:sender",
    )
    assert _of_type(bundle, "Communication", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "organizations",
        _id=str(world["org"]),
        _revinclude="Communication:sender",
    )
    assert _of_type(bundle, "Communication", "include") == {str(world["b"])}
    bundle = await _other(
        client,
        "organizations",
        _id=str(world["org"]),
        _revinclude="Communication:recipient",
    )
    assert _of_type(bundle, "Communication", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "care-teams",
        _id=str(world["ct"]),
        _revinclude="Communication:recipient",
    )
    assert _of_type(bundle, "Communication", "include") == {str(world["b"])}
    bundle = await _search(
        client, _id=str(world["e"]), _revinclude="Communication:part-of"
    )
    assert _of_type(bundle, "Communication", "include") == {str(world["a"])}


# -- combination rules / lenient vs strict ---------------------------------------------------


async def test_params_are_anded(client, world):
    assert await _keys(client, world, status="completed", category="notification") == {
        "a"
    }
    assert (
        await _keys(client, world, status="in-progress", category="notification")
        == set()
    )
    assert await _keys(
        client, world, patient=str(world["p1"]), sent="ge2026-01-01"
    ) == {"a"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"subject:text": "x"}) == 400
    assert await _status(client, **{"sent:exact": "2020"}) == 400
    assert await _status(client, **{"identifier:below": "x"}) == 400
    assert await _status(client, **{"status:text": "x"}) == 400
    assert await _status(client, sent="banana") == 400
    assert await _status(client, **{"instantiates-uri:text": "x"}) == 400


async def test_unknown_param_lenient_vs_strict(client, world):
    lenient = await client.get(BASE + "/", params={"nonsense": "1"})
    assert lenient.status_code == 200
    assert any(e["search"]["mode"] == "outcome" for e in lenient.json()["entry"])
    strict = await client.get(
        BASE + "/", params={"nonsense": "1"}, headers={"Prefer": "handling=strict"}
    )
    assert strict.status_code == 400
    # R4 defines no priority parameter for Communication
    strict_priority = await client.get(
        BASE + "/", params={"priority": "stat"}, headers={"Prefer": "handling=strict"}
    )
    assert strict_priority.status_code == 400


async def test_query_param_refused(client, world):
    assert await _status(client, _query="x") == 400


# -- POST _search / Bundle shape -------------------------------------------------------------


async def test_post_search_form_encoded(client, world):
    resp = await client.post(
        BASE + "/_search", data={"status": "not-done", "based-on": "Device/7"}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["c"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, identifier="CM-A")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/communications/{world['a']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "Communication"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
