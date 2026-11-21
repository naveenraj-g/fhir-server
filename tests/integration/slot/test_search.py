"""FHIR R4 search over Slot (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/slot.html#search).

One block per search parameter — `start` is an instant search, `status` a code
bound to the real FHIR codes, `schedule` a reference chaining into Schedule
(and through it to the actor) — then `_include`/`_revinclude`, result
parameters, combination rules, lenient vs strict handling and POST _search.
"""

import pytest

from tests.integration.slot.support import (
    APPT,
    BASE,
    CAT,
    SCT,
    SLOT_IDS,
    TYPE,
    create_practitioner,
    create_schedule,
    create_slot,
    slot_body,
)

API = "/api/fhir/v1"
KEYS = ("a", "b", "c", "bare")
ALL = set(KEYS)


def _ids(bundle: dict) -> set[int]:
    return {
        int(e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == "match"
    }


@pytest.fixture
async def world(client):
    """Two schedules (one for a practitioner) and four slots with distinct,
    searchable values. Returns {key: public id}."""
    w = {}
    w["prac"] = await create_practitioner(client, "Careful", "Adam")
    w["sched1"] = await create_schedule(
        client, {"active": True, "actor": [{"reference": f"Practitioner/{w['prac']}"}]}
    )
    w["sched2"] = await create_schedule(client)

    w["a"] = await create_slot(
        client,
        slot_body(
            w["sched1"],
            status="free",
            start="2026-06-01T09:00:00Z",
            end="2026-06-01T09:30:00Z",
            identifier=[
                {"system": SLOT_IDS, "value": "SL-A", "type": {"text": "Slot number"}}
            ],
            serviceCategory=[
                {
                    "coding": [
                        {"system": CAT, "code": "17", "display": "General Practice"}
                    ]
                }
            ],
            serviceType=[{"coding": [{"system": TYPE, "code": "124"}]}],
            specialty=[
                {
                    "coding": [
                        {"system": SCT, "code": "394579002", "display": "Cardiology"}
                    ]
                }
            ],
            appointmentType={"coding": [{"system": APPT, "code": "ROUTINE"}]},
        ),
    )
    w["b"] = await create_slot(
        client,
        slot_body(
            w["sched1"],
            status="busy",
            start="2026-06-02T09:00:00Z",
            end="2026-06-02T09:30:00Z",
            identifier=[{"system": SLOT_IDS, "value": "SL-B"}],
            specialty=[{"coding": [{"system": SCT, "code": "408443003"}]}],
            appointmentType={"coding": [{"system": APPT, "code": "WALKIN"}]},
        ),
    )
    w["c"] = await create_slot(
        client,
        slot_body(
            w["sched2"],
            status="busy-unavailable",
            start="2026-07-15T14:00:00Z",
            end="2026-07-15T14:30:00Z",
        ),
    )
    w["bare"] = await create_slot(
        client,
        slot_body(
            w["sched2"],
            status="entered-in-error",
            start="2027-01-05T08:00:00Z",
            end="2027-01-05T08:30:00Z",
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


# ── _id / _lastUpdated ───────────────────────────────────────────────────────


async def test_id(client, world):
    assert await _keys(client, world, _id=str(world["a"])) == {"a"}
    assert await _keys(client, world, _id=f"{world['a']},{world['b']}") == {"a", "b"}
    assert await _keys(client, world, **{"_id:not": str(world["a"])}) == ALL - {"a"}


async def test_last_updated(client, world):
    assert await _keys(client, world, _lastUpdated="ge2000-01-01") == ALL
    assert await _keys(client, world, _lastUpdated="lt2000-01-01") == set()


# ── status ───────────────────────────────────────────────────────────────────


async def test_status_uses_real_fhir_codes(client, world):
    assert await _keys(client, world, status="free") == {"a"}
    assert await _keys(client, world, status="busy-unavailable") == {"c"}
    assert await _keys(client, world, status="entered-in-error") == {"bare"}
    assert await _keys(client, world, status="busy,free") == {"a", "b"}


async def test_status_system_and_not(client, world):
    assert await _keys(client, world, status="http://hl7.org/fhir/slotstatus|free") == {
        "a"
    }
    assert await _keys(client, world, status="http://wrong.example.org|free") == set()
    assert await _keys(client, world, **{"status:not": "free"}) == ALL - {"a"}


async def test_status_unknown_code_matches_nothing(client, world):
    assert await _keys(client, world, status="busy_unavailable") == set()
    assert await _keys(client, world, status="nonsense") == set()


# ── start ────────────────────────────────────────────────────────────────────


async def test_start_prefixes(client, world):
    assert await _keys(client, world, start="ge2026-06-02") == {"b", "c", "bare"}
    assert await _keys(client, world, start="lt2026-06-02") == {"a"}
    assert await _keys(client, world, start="gt2026-06-02T09:00:00Z") == {"c", "bare"}
    assert await _keys(client, world, start="le2026-06-02T09:00:00Z") == {"a", "b"}
    assert await _keys(client, world, start="ne2026-06-01") == ALL - {"a"}


async def test_start_eq_day_and_instant(client, world):
    assert await _keys(client, world, start="2026-06-01") == {"a"}
    assert await _keys(client, world, start="2026-06") == {"a", "b"}
    assert await _keys(client, world, start="2026-06-01T09:00:00Z") == {"a"}
    assert await _keys(client, world, start="2026-06-01T10:00:00Z") == set()


async def test_start_range_and_repeat_is_and(client, world):
    assert await _keys(client, world, start=["ge2026-06-02", "lt2026-07-01"]) == {"b"}
    assert await _keys(client, world, start="2026-06-01,2026-07-15") == {"a", "c"}


async def test_start_bad_value_is_400(client, world):
    assert (
        await client.get(BASE + "/", params={"start": "not-a-date"})
    ).status_code == 400


# ── identifier ───────────────────────────────────────────────────────────────


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="SL-A") == {"a"}
    assert await _keys(client, world, identifier=f"{SLOT_IDS}|SL-B") == {"b"}
    assert await _keys(client, world, identifier="urn:other|SL-A") == set()
    assert await _keys(client, world, identifier=f"{SLOT_IDS}|") == {"a", "b"}


async def test_identifier_text_not_and_missing(client, world):
    assert await _keys(client, world, **{"identifier:text": "Slot"}) == {"a"}
    assert await _keys(client, world, **{"identifier:not": "SL-A"}) == ALL - {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {"c", "bare"}
    assert await _keys(client, world, **{"identifier:missing": "false"}) == {"a", "b"}


# ── the CodeableConcept tokens ───────────────────────────────────────────────


async def test_service_category_and_type(client, world):
    assert await _keys(client, world, **{"service-category": "17"}) == {"a"}
    assert await _keys(client, world, **{"service-category": f"{CAT}|17"}) == {"a"}
    assert await _keys(client, world, **{"service-category": "other|17"}) == set()
    assert await _keys(client, world, **{"service-type": f"{TYPE}|124"}) == {"a"}
    assert await _keys(client, world, **{"service-category:text": "General"}) == {"a"}


async def test_specialty(client, world):
    assert await _keys(client, world, specialty="394579002") == {"a"}
    assert await _keys(client, world, specialty=f"{SCT}|408443003") == {"b"}
    assert await _keys(client, world, specialty="394579002,408443003") == {"a", "b"}
    assert await _keys(client, world, **{"specialty:not": "394579002"}) == ALL - {"a"}


async def test_appointment_type_is_a_single_concept(client, world):
    assert await _keys(client, world, **{"appointment-type": "ROUTINE"}) == {"a"}
    assert await _keys(client, world, **{"appointment-type": f"{APPT}|WALKIN"}) == {"b"}
    assert await _keys(client, world, **{"appointment-type:missing": "true"}) == {
        "c",
        "bare",
    }


async def test_token_params_do_not_cross_over(client, world):
    # Same table, told apart by the param: a specialty code is not an appointment type.
    assert await _keys(client, world, **{"appointment-type": "394579002"}) == set()
    assert await _keys(client, world, specialty="ROUTINE") == set()


# ── schedule ─────────────────────────────────────────────────────────────────


async def test_schedule_by_id_and_typed_reference(client, world):
    s1, s2 = world["sched1"], world["sched2"]
    assert await _keys(client, world, schedule=str(s1)) == {"a", "b"}
    assert await _keys(client, world, schedule=f"Schedule/{s2}") == {"c", "bare"}
    assert await _keys(client, world, **{"schedule:Schedule": str(s1)}) == {"a", "b"}
    assert await _keys(client, world, schedule=f"{s1},{s2}") == ALL


async def test_schedule_unsupported_modifier_is_400(client, world):
    assert (
        await client.get(BASE + "/", params={"schedule:Practitioner": "1"})
    ).status_code == 400


async def test_schedule_missing(client, world):
    assert await _keys(client, world, **{"schedule:missing": "false"}) == ALL
    assert await _keys(client, world, **{"schedule:missing": "true"}) == set()


async def test_schedule_chain_through_typed_actor(client, world):
    assert await _keys(
        client, world, **{"schedule.actor:Practitioner.family": "Careful"}
    ) == {"a", "b"}
    assert (
        await _keys(client, world, **{"schedule.actor:Practitioner.family": "Nobody"})
        == set()
    )


async def test_schedule_chain_on_schedule_params(client, world):
    assert await _keys(client, world, **{"schedule.active": "true"}) == ALL
    assert await _keys(
        client, world, **{"schedule.actor": f"Practitioner/{world['prac']}"}
    ) == {"a", "b"}


async def test_schedule_chain_unknown_param_is_400(client, world):
    assert (
        await client.get(BASE + "/", params={"schedule.nonsense": "x"})
    ).status_code == 400


async def test_schedule_absolute_url_and_logical_reference(client, world):
    external = "https://other.example.org/fhir/Schedule/9"
    ext = await create_slot(client, slot_body(1, schedule={"reference": external}))
    logical = await create_slot(
        client,
        slot_body(
            1, schedule={"identifier": {"system": "urn:schedules", "value": "EXT-1"}}
        ),
    )
    assert ext in _ids(await _search(client, schedule=external))
    assert logical in _ids(
        await _search(client, **{"schedule:identifier": "urn:schedules|EXT-1"})
    )
    assert logical not in _ids(await _search(client, schedule=str(world["sched1"])))


# ── _sort / _count / _offset / _total ────────────────────────────────────────


async def test_sort_by_start(client, world):
    asc = (await _search(client, _sort="start"))["entry"]
    assert [int(e["resource"]["id"]) for e in asc] == [
        world[k] for k in ("a", "b", "c", "bare")
    ]
    desc = (await _search(client, _sort="-start"))["entry"]
    assert [int(e["resource"]["id"]) for e in desc] == [
        world[k] for k in ("bare", "c", "b", "a")
    ]


async def test_sort_by_status_and_schedule(client, world):
    assert (await _search(client, _sort="status"))["total"] == 4
    assert (await _search(client, _sort="-schedule"))["total"] == 4
    assert (
        await client.get(BASE + "/", params={"_sort": "comment"})
    ).status_code == 400


async def test_default_sort_is_newest_first(client, world):
    got = [int(e["resource"]["id"]) for e in (await _search(client))["entry"]]
    assert got == sorted(got, reverse=True)


async def test_paging_and_total(client, world):
    page = await _search(client, _count=2, _sort="start")
    assert page["total"] == 4 and len(page["entry"]) == 2
    assert {link["relation"] for link in page["link"]} >= {"self", "next"}
    nxt = await _search(client, _count=2, _offset=2, _sort="start")
    assert [int(e["resource"]["id"]) for e in nxt["entry"]] == [
        world["c"],
        world["bare"],
    ]
    assert "entry" not in await _search(client, _count=0)
    assert "total" not in await _search(client, _total="none")


# ── _summary / _elements ─────────────────────────────────────────────────────


async def test_summary_count_and_elements(client, world):
    summary = await _search(client, _summary="count")
    assert summary["total"] == 4 and "entry" not in summary
    elems = await _search(client, _elements="status", _id=str(world["a"]))
    res = elems["entry"][0]["resource"]
    assert (
        res["status"] == "free"
        and "comment" not in res
        and "serviceCategory" not in res
    )
    assert res["meta"]["tag"][0]["code"] == "SUBSETTED"


# ── _include / _revinclude ───────────────────────────────────────────────────


async def test_include_schedule(client, world):
    bundle = await _search(client, _id=str(world["a"]), _include="Slot:schedule")
    modes = {
        (e["resource"]["resourceType"], e["search"]["mode"]) for e in bundle["entry"]
    }
    assert modes == {("Slot", "match"), ("Schedule", "include")}
    included = [
        e["resource"] for e in bundle["entry"] if e["search"]["mode"] == "include"
    ]
    assert [r["id"] for r in included] == [str(world["sched1"])]


async def test_include_schedule_is_deduplicated(client, world):
    bundle = await _search(
        client, schedule=str(world["sched1"]), _include="Slot:schedule"
    )
    assert (
        sum(1 for e in bundle["entry"] if e["resource"]["resourceType"] == "Schedule")
        == 1
    )


async def test_include_nothing_for_external_schedule(client, world):
    ext = await create_slot(
        client,
        slot_body(
            1, schedule={"reference": "https://other.example.org/fhir/Schedule/9"}
        ),
    )
    bundle = await _search(client, _id=str(ext), _include="Slot:schedule")
    assert {e["resource"]["resourceType"] for e in bundle["entry"]} == {"Slot"}


async def test_revinclude_slots_on_schedule(client, world):
    resp = await client.get(
        f"{API}/schedules/",
        params={"_id": str(world["sched1"]), "_revinclude": "Slot:schedule"},
    )
    assert resp.status_code == 200, resp.text
    entries = resp.json()["entry"]
    slots = {
        int(e["resource"]["id"])
        for e in entries
        if e["resource"]["resourceType"] == "Slot"
    }
    assert slots == {world["a"], world["b"]}
    assert all(
        e["search"]["mode"] == "include"
        for e in entries
        if e["resource"]["resourceType"] == "Slot"
    )


async def test_include_on_unsupported_target_is_ignored_or_400(client, world):
    resp = await client.get(BASE + "/", params={"_include": "Slot:nonsense"})
    assert resp.status_code in (200, 400)


# ── combination rules / lenient vs strict ────────────────────────────────────


async def test_params_are_anded(client, world):
    assert await _keys(client, world, status="free", specialty="394579002") == {"a"}
    assert await _keys(client, world, status="free", specialty="408443003") == set()
    assert await _keys(
        client, world, schedule=str(world["sched1"]), start="ge2026-06-02"
    ) == {"b"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert (
        await client.get(BASE + "/", params={"status:above": "free"})
    ).status_code == 400


async def test_unknown_param_lenient_vs_strict(client, world):
    lenient = await client.get(BASE + "/", params={"nonsense": "1"})
    assert lenient.status_code == 200
    assert any(e["search"]["mode"] == "outcome" for e in lenient.json()["entry"])
    strict = await client.get(
        BASE + "/", params={"nonsense": "1"}, headers={"Prefer": "handling=strict"}
    )
    assert strict.status_code == 400


async def test_query_param_refused(client, world):
    assert (await client.get(BASE + "/", params={"_query": "x"})).status_code == 400


# ── POST _search / Bundle shape ──────────────────────────────────────────────


async def test_post_search_form_encoded(client, world):
    resp = await client.post(
        BASE + "/_search", data={"status": "busy", "start": "ge2026-06-01"}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, status="free")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/slots/{world['a']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "Slot"


async def test_empty_result(client, world):
    bundle = await _search(client, status="busy-tentative")
    assert bundle["total"] == 0 and "entry" not in bundle
