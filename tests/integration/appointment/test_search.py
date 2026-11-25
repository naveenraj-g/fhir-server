"""FHIR R4 search over Appointment (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/appointment.html#search).

One block per search parameter — `date` is an instant search, `status` a code
bound to the real FHIR codes, `actor`/`patient`/`practitioner`/`location` all
read the participant list (the first is multi-target, the others narrowed to
one type), `slot`/`based-on`/`reason-reference`/`supporting-info` are
references — then chaining, `_include`/`_revinclude`, result parameters,
combination rules, lenient vs strict handling and POST _search.
"""

import pytest

from tests.integration.appointment.support import (
    APPT,
    APPT_IDS,
    BASE,
    CAT,
    SCT,
    TYPE,
    appointment_body,
    create_appointment,
    create_condition,
    create_healthcare_service,
    create_location,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_schedule,
    create_slot,
    participant,
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


def _of_type(bundle: dict, rtype: str, mode: str) -> set[str]:
    return {
        e["resource"]["id"]
        for e in bundle.get("entry") or []
        if e["resource"]["resourceType"] == rtype and e["search"]["mode"] == mode
    }


@pytest.fixture
async def world(client):
    """Patients, practitioners, a location, two slots and four appointments with
    distinct, searchable values. Returns {key: public id}."""
    w = {}
    w["p1"] = await create_patient(
        client, {"active": True, "name": [{"family": "Windsor", "given": ["Anna"]}]}
    )
    w["p2"] = await create_patient(
        client, {"active": True, "name": [{"family": "Fairfax", "given": ["Ben"]}]}
    )
    w["prac1"] = await create_practitioner(client, "Careful", "Adam")
    w["prac2"] = await create_practitioner(client, "Other", "Olive")
    w["loc"] = await create_location(client, "North Wing", "Boston")
    w["hs"] = await create_healthcare_service(client)
    w["role"] = await create_practitioner_role(client)
    w["cond"] = await create_condition(client, w["p1"])
    w["s1"] = await create_slot(
        client, slot_body(await create_schedule(client), status="free")
    )
    w["s2"] = await create_slot(
        client, slot_body(await create_schedule(client), status="busy")
    )

    w["a"] = await create_appointment(
        client,
        appointment_body(
            w["p1"],
            status="booked",
            start="2026-06-01T09:00:00Z",
            end="2026-06-01T09:30:00Z",
            identifier=[
                {
                    "system": APPT_IDS,
                    "value": "AP-A",
                    "type": {"text": "Booking number"},
                }
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
            reasonCode=[
                {
                    "coding": [{"system": SCT, "code": "413153004"}],
                    "text": "Annual check-up",
                }
            ],
            slot=[{"reference": f"Slot/{w['s1']}"}],
            basedOn=[{"reference": "ServiceRequest/80001"}],
            reasonReference=[{"reference": f"Condition/{w['cond']}"}],
            supportingInformation=[{"reference": "Encounter/20001"}],
            participant=[
                participant(f"Patient/{w['p1']}"),
                participant(f"Practitioner/{w['prac1']}"),
                participant(f"Location/{w['loc']}", status="tentative"),
            ],
        ),
    )
    w["b"] = await create_appointment(
        client,
        appointment_body(
            w["p2"],
            status="pending",
            start="2026-06-02T09:00:00Z",
            identifier=[{"system": APPT_IDS, "value": "AP-B"}],
            specialty=[{"coding": [{"system": SCT, "code": "408443003"}]}],
            appointmentType={"coding": [{"system": APPT, "code": "WALKIN"}]},
            slot=[{"reference": f"Slot/{w['s2']}"}],
            reasonReference=[{"reference": "Observation/160001"}],
            supportingInformation=[
                {"reference": "https://other.example.org/fhir/DocumentReference/3"}
            ],
            participant=[
                participant(f"Patient/{w['p2']}", status="needs-action"),
                participant(f"Practitioner/{w['prac2']}"),
            ],
        ),
    )
    w["c"] = await create_appointment(
        client,
        appointment_body(
            w["p1"],
            status="cancelled",
            start="2026-07-15T14:00:00Z",
            participant=[
                participant(f"Patient/{w['p1']}", status="declined"),
                participant("Device/6"),
                participant(f"HealthcareService/{w['hs']}"),
                participant(f"PractitionerRole/{w['role']}"),
            ],
        ),
    )
    w["bare"] = await create_appointment(
        client, {"status": "noshow", "participant": [{"status": "accepted"}]}
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
    assert await _keys(client, world, _id="999999") == set()
    assert await _keys(client, world, **{"_id:not": str(world["a"])}) == {
        "b",
        "c",
        "bare",
    }


async def test_last_updated(client, world):
    assert await _keys(client, world, _lastUpdated="ge2020-01-01") == ALL
    assert await _keys(client, world, _lastUpdated="lt2020-01-01") == set()


# ── status ───────────────────────────────────────────────────────────────────


async def test_status(client, world):
    assert await _keys(client, world, status="booked") == {"a"}
    assert await _keys(client, world, status="noshow") == {"bare"}
    assert await _keys(client, world, status="booked,pending") == {"a", "b"}
    assert await _keys(
        client, world, status="http://hl7.org/fhir/appointmentstatus|cancelled"
    ) == {"c"}


async def test_status_wrong_system_or_unknown_code_matches_nothing(client, world):
    assert await _keys(client, world, status="http://wrong|booked") == set()
    assert await _keys(client, world, status="broken") == set()
    assert await _keys(client, world, status="entered_in_error") == set()


async def test_status_not_and_missing(client, world):
    assert await _keys(client, world, **{"status:not": "booked"}) == {"b", "c", "bare"}
    assert await _keys(client, world, **{"status:missing": "false"}) == ALL


# ── date (Appointment.start, an instant) ─────────────────────────────────────


async def test_date_prefixes(client, world):
    assert await _keys(client, world, date="2026-06-01") == {"a"}
    assert await _keys(client, world, date="ge2026-06-02") == {"b", "c"}
    assert await _keys(client, world, date="gt2026-06-02T09:00:00Z") == {"c"}
    assert await _keys(client, world, date="lt2026-06-02") == {"a"}
    assert await _keys(client, world, date="le2026-06-02T09:00:00Z") == {"a", "b"}
    assert await _keys(client, world, date="ne2026-06-01") == {"b", "c"} | set()


async def test_date_range_and_partial(client, world):
    assert await _keys(client, world, date=["ge2026-06-01", "lt2026-06-03"]) == {
        "a",
        "b",
    }
    assert await _keys(client, world, date="2026-06") == {"a", "b"}
    assert await _keys(client, world, date="2026") == {"a", "b", "c"}


async def test_date_missing_and_bad_value(client, world):
    assert await _keys(client, world, **{"date:missing": "true"}) == {"bare"}
    assert (
        await client.get(BASE + "/", params={"date": "not-a-date"})
    ).status_code == 400


# ── identifier ───────────────────────────────────────────────────────────────


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="AP-A") == {"a"}
    assert await _keys(client, world, identifier=f"{APPT_IDS}|AP-B") == {"b"}
    assert await _keys(client, world, identifier="urn:other|AP-A") == set()
    assert await _keys(client, world, identifier=f"{APPT_IDS}|") == {"a", "b"}


async def test_identifier_text_not_and_missing(client, world):
    assert await _keys(client, world, **{"identifier:text": "Booking"}) == {"a"}
    assert await _keys(client, world, **{"identifier:not": "AP-A"}) == {
        "b",
        "c",
        "bare",
    }
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {"c", "bare"}
    assert await _keys(client, world, **{"identifier:missing": "false"}) == {"a", "b"}


# ── the five CodeableConcept token parameters ────────────────────────────────


async def test_service_category_and_type(client, world):
    assert await _keys(client, world, **{"service-category": "17"}) == {"a"}
    assert await _keys(client, world, **{"service-category": f"{CAT}|17"}) == {"a"}
    assert await _keys(client, world, **{"service-category": "other|17"}) == set()
    assert await _keys(client, world, **{"service-category:text": "General"}) == {"a"}
    assert await _keys(client, world, **{"service-type": f"{TYPE}|124"}) == {"a"}


async def test_specialty(client, world):
    assert await _keys(client, world, specialty="394579002") == {"a"}
    assert await _keys(client, world, specialty="394579002,408443003") == {"a", "b"}
    assert await _keys(client, world, **{"specialty:not": "394579002"}) == {
        "b",
        "c",
        "bare",
    }


async def test_appointment_type(client, world):
    assert await _keys(client, world, **{"appointment-type": "ROUTINE"}) == {"a"}
    assert await _keys(client, world, **{"appointment-type": f"{APPT}|WALKIN"}) == {"b"}
    assert await _keys(client, world, **{"appointment-type:missing": "true"}) == {
        "c",
        "bare",
    }


async def test_reason_code(client, world):
    assert await _keys(client, world, **{"reason-code": "413153004"}) == {"a"}
    assert await _keys(client, world, **{"reason-code": f"{SCT}|413153004"}) == {"a"}
    assert await _keys(client, world, **{"reason-code:text": "Annual"}) == {"a"}
    assert await _keys(client, world, **{"reason-code:missing": "true"}) == {
        "b",
        "c",
        "bare",
    }


# ── actor / patient / practitioner / location ────────────────────────────────


async def test_actor_needs_a_type(client, world):
    assert (
        await client.get(BASE + "/", params={"actor": str(world["p1"])})
    ).status_code == 400


async def test_actor_by_type_and_id(client, world):
    assert await _keys(client, world, actor=f"Patient/{world['p1']}") == {"a", "c"}
    assert await _keys(client, world, actor=f"Practitioner/{world['prac2']}") == {"b"}
    assert await _keys(client, world, actor=f"Location/{world['loc']}") == {"a"}
    assert await _keys(client, world, actor=f"HealthcareService/{world['hs']}") == {"c"}
    assert await _keys(client, world, actor=f"PractitionerRole/{world['role']}") == {
        "c"
    }
    assert await _keys(client, world, actor="Device/6") == {"c"}


async def test_actor_type_modifier_and_type_is_part_of_the_match(client, world):
    assert await _keys(client, world, **{"actor:Patient": str(world["p1"])}) == {
        "a",
        "c",
    }
    # same number, other type: no match
    assert await _keys(client, world, actor=f"Practitioner/{world['p1']}") == set()
    assert (
        await client.get(BASE + "/", params={"actor:Condition": "1"})
    ).status_code == 400


async def test_actor_or_and_and(client, world):
    both = f"Patient/{world['p2']},Practitioner/{world['prac1']}"
    assert await _keys(client, world, actor=both) == {"a", "b"}
    assert await _keys(
        client,
        world,
        actor=[f"Patient/{world['p1']}", f"Practitioner/{world['prac1']}"],
    ) == {"a"}


async def test_actor_identifier_and_absolute(client, world):
    logical = await create_appointment(
        client,
        {
            "status": "booked",
            "participant": [
                {
                    "actor": {"identifier": {"system": "urn:pts", "value": "P-9"}},
                    "status": "accepted",
                }
            ],
        },
    )
    ext = await create_appointment(
        client,
        {
            "status": "booked",
            "participant": [participant("https://other.example.org/fhir/Patient/1")],
        },
    )
    assert logical in _ids(await _search(client, **{"actor:identifier": "urn:pts|P-9"}))
    assert ext in _ids(
        await _search(client, actor="https://other.example.org/fhir/Patient/1")
    )
    assert logical not in _ids(await _search(client, actor=f"Patient/{world['p1']}"))


async def test_actor_missing(client, world):
    assert await _keys(client, world, **{"actor:missing": "true"}) == {"bare"}
    assert await _keys(client, world, **{"actor:missing": "false"}) == {"a", "b", "c"}


async def test_patient_practitioner_location(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {"a", "c"}
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"b"}
    assert await _keys(client, world, practitioner=str(world["prac1"])) == {"a"}
    assert await _keys(client, world, location=str(world["loc"])) == {"a"}
    assert await _keys(client, world, patient=f"{world['p1']},{world['p2']}") == {
        "a",
        "b",
        "c",
    }


async def test_narrowed_params_only_match_their_type(client, world):
    assert await _keys(client, world, patient=f"Practitioner/{world['prac1']}") == set()
    assert await _keys(client, world, practitioner=f"Patient/{world['p1']}") == set()
    assert await _keys(client, world, **{"location:missing": "true"}) == {
        "b",
        "c",
        "bare",
    }
    assert await _keys(client, world, **{"patient:missing": "false"}) == {"a", "b", "c"}


async def test_patient_and_practitioner_are_anded(client, world):
    assert await _keys(
        client, world, patient=str(world["p1"]), practitioner=str(world["prac1"])
    ) == {"a"}
    assert (
        await _keys(
            client, world, patient=str(world["p2"]), practitioner=str(world["prac1"])
        )
        == set()
    )


# ── part-status ──────────────────────────────────────────────────────────────


async def test_part_status(client, world):
    assert await _keys(client, world, **{"part-status": "accepted"}) == ALL
    assert await _keys(client, world, **{"part-status": "declined"}) == {"c"}
    assert await _keys(client, world, **{"part-status": "needs-action"}) == {"b"}
    assert await _keys(client, world, **{"part-status": "tentative"}) == {"a"}
    assert await _keys(
        client,
        world,
        **{"part-status": "http://hl7.org/fhir/participationstatus|declined"},
    ) == {"c"}


async def test_part_status_wrong_system_or_unknown_matches_nothing(client, world):
    assert (
        await _keys(client, world, **{"part-status": "http://wrong|accepted"}) == set()
    )
    assert await _keys(client, world, **{"part-status": "needs_action"}) == set()


async def test_part_status_with_actor_in_one_search(client, world):
    assert await _keys(
        client, world, **{"part-status": "declined"}, patient=str(world["p1"])
    ) == {"c"}


# ── slot / based-on / reason-reference / supporting-info ─────────────────────


async def test_slot(client, world):
    assert await _keys(client, world, slot=str(world["s1"])) == {"a"}
    assert await _keys(client, world, slot=f"Slot/{world['s2']}") == {"b"}
    assert await _keys(client, world, **{"slot:missing": "true"}) == {"c", "bare"}


async def test_slot_chain(client, world):
    assert await _keys(client, world, **{"slot.status": "free"}) == {"a"}
    assert await _keys(client, world, **{"slot.status": "busy"}) == {"b"}
    assert (
        await client.get(BASE + "/", params={"slot.nonsense": "x"})
    ).status_code == 400


async def test_based_on(client, world):
    assert await _keys(client, world, **{"based-on": "80001"}) == {"a"}
    assert await _keys(client, world, **{"based-on": "ServiceRequest/80001"}) == {"a"}
    assert await _keys(client, world, **{"based-on": "80002"}) == set()


async def test_reason_reference_needs_a_type(client, world):
    cond = world["cond"]
    assert (
        await client.get(BASE + "/", params={"reason-reference": str(cond)})
    ).status_code == 400
    assert await _keys(client, world, **{"reason-reference": f"Condition/{cond}"}) == {
        "a"
    }
    assert await _keys(client, world, **{"reason-reference:Condition": str(cond)}) == {
        "a"
    }
    assert await _keys(client, world, **{"reason-reference:Observation": "160001"}) == {
        "b"
    }
    assert await _keys(
        client, world, **{"reason-reference": f"Condition/{cond},Observation/160001"}
    ) == {"a", "b"}
    assert (
        await _keys(
            client, world, **{"reason-reference:Condition.clinical-status": "active"}
        )
        == set()
    )  # the condition has none


async def test_supporting_info(client, world):
    assert (
        await client.get(BASE + "/", params={"supporting-info": "20001"})
    ).status_code == 400
    assert await _keys(client, world, **{"supporting-info": "Encounter/20001"}) == {"a"}
    assert await _keys(client, world, **{"supporting-info:Encounter": "20001"}) == {"a"}
    ext = "https://other.example.org/fhir/DocumentReference/3"
    assert await _keys(client, world, **{"supporting-info": ext}) == {"b"}


async def test_reference_identifier_modifier(client, world):
    logical = await create_appointment(
        client,
        appointment_body(
            basedOn=[{"identifier": {"system": "urn:orders", "value": "O-1"}}]
        ),
    )
    assert _ids(await _search(client, **{"based-on:identifier": "urn:orders|O-1"})) == {
        logical
    }


# ── chaining ─────────────────────────────────────────────────────────────────


async def test_patient_chain(client, world):
    assert await _keys(client, world, **{"patient.family": "Windsor"}) == {"a", "c"}
    assert await _keys(client, world, **{"patient.family": "Fairfax"}) == {"b"}
    assert await _keys(client, world, **{"patient.given": "Anna"}) == {"a", "c"}


async def test_practitioner_and_location_chain(client, world):
    assert await _keys(client, world, **{"practitioner.family": "Careful"}) == {"a"}
    assert await _keys(client, world, **{"location.address-city": "Boston"}) == {"a"}
    assert await _keys(client, world, **{"location.address-city": "Paris"}) == set()


async def test_actor_chain_through_a_typed_target(client, world):
    assert await _keys(client, world, **{"actor:Practitioner.family": "Other"}) == {"b"}
    assert await _keys(client, world, **{"actor:Patient.family": "Windsor"}) == {
        "a",
        "c",
    }
    assert await _keys(client, world, **{"actor:Location.address-city": "Boston"}) == {
        "a"
    }


async def test_bad_chains_are_400(client, world):
    assert (
        await client.get(BASE + "/", params={"actor.family": "x"})
    ).status_code == 400  # untyped
    assert (
        await client.get(BASE + "/", params={"actor:Device.name": "x"})
    ).status_code == 400  # not a resource here
    assert (
        await client.get(BASE + "/", params={"patient.nonsense": "x"})
    ).status_code == 400
    assert (await client.get(BASE + "/", params={"status.x": "y"})).status_code == 400


# ── _sort / _count / _offset / _total ────────────────────────────────────────


async def test_sort_by_date(client, world):
    asc = [
        int(e["resource"]["id"])
        for e in (
            await _search(
                client, _sort="date", _count=3, status="booked,pending,cancelled"
            )
        )["entry"]
    ]
    assert asc == [world["a"], world["b"], world["c"]]
    desc = [
        int(e["resource"]["id"])
        for e in (
            await _search(client, _sort="-date", status="booked,pending,cancelled")
        )["entry"]
    ]
    assert desc == [world["c"], world["b"], world["a"]]


async def test_sort_by_other_params(client, world):
    for key in ("status", "patient", "actor", "identifier", "part-status", "slot"):
        assert (await _search(client, _sort=key))["total"] == 4, key
    assert (
        await client.get(BASE + "/", params={"_sort": "comment"})
    ).status_code == 400


async def test_default_sort_is_newest_first(client, world):
    got = [int(e["resource"]["id"]) for e in (await _search(client))["entry"]]
    assert got == sorted(got, reverse=True)


async def test_paging_and_total(client, world):
    page = await _search(client, _count=2, _sort="status")
    assert page["total"] == 4 and len(page["entry"]) == 2
    assert any(link["relation"] == "next" for link in page["link"])
    nxt = await _search(client, _count=2, _offset=2, _sort="status")
    assert not (
        {e["resource"]["id"] for e in page["entry"]}
        & {e["resource"]["id"] for e in nxt["entry"]}
    )
    assert "entry" not in await _search(client, _count=0)
    assert "total" not in await _search(client, _total="none")


async def test_summary_count_and_elements(client, world):
    assert (await _search(client, _summary="count"))["total"] == 4
    elems = await _search(client, _elements="status", _id=str(world["a"]))
    resource = elems["entry"][0]["resource"]
    assert (
        resource["status"] == "booked"
        and "participant" in resource
        or "status" in resource
    )
    assert "comment" not in resource and "start" not in resource


# ── _include ─────────────────────────────────────────────────────────────────


async def test_include_actor_brings_every_modeled_type(client, world):
    bundle = await _search(client, _id=str(world["a"]), _include="Appointment:actor")
    assert _of_type(bundle, "Patient", "include") == {str(world["p1"])}
    assert _of_type(bundle, "Practitioner", "include") == {str(world["prac1"])}
    assert _of_type(bundle, "Location", "include") == {str(world["loc"])}


async def test_include_actor_with_type(client, world):
    bundle = await _search(
        client, _id=str(world["a"]), _include="Appointment:actor:Location"
    )
    assert {e["resource"]["resourceType"] for e in bundle["entry"]} == {
        "Appointment",
        "Location",
    }


async def test_include_actor_for_healthcare_service_and_role(client, world):
    bundle = await _search(client, _id=str(world["c"]), _include="Appointment:actor")
    assert _of_type(bundle, "HealthcareService", "include") == {str(world["hs"])}
    assert _of_type(bundle, "PractitionerRole", "include") == {str(world["role"])}
    assert _of_type(bundle, "Patient", "include") == {str(world["p1"])}


async def test_include_narrowed_params(client, world):
    bundle = await _search(
        client,
        _id=str(world["a"]),
        _include=["Appointment:patient", "Appointment:practitioner"],
    )
    assert _of_type(bundle, "Patient", "include") == {str(world["p1"])}
    assert _of_type(bundle, "Practitioner", "include") == {str(world["prac1"])}
    assert _of_type(bundle, "Location", "include") == set()


async def test_include_slot_and_dedup(client, world):
    bundle = await _search(client, _id=str(world["a"]), _include="Appointment:slot")
    assert _of_type(bundle, "Slot", "include") == {str(world["s1"])}
    both = await _search(
        client, patient=str(world["p1"]), _include="Appointment:patient"
    )
    assert (
        sum(1 for e in both["entry"] if e["resource"]["resourceType"] == "Patient") == 1
    )


async def test_include_nothing_for_actors_that_are_not_resources(client, world):
    bundle = await _search(client, _id=str(world["bare"]), _include="Appointment:actor")
    assert {e["resource"]["resourceType"] for e in bundle["entry"]} == {"Appointment"}


# ── _revinclude (declared on the other side) ─────────────────────────────────


async def _other(client, path, **params) -> dict:
    resp = await client.get(f"{API}/{path}/", params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_revinclude_appointment_patient_on_patients(client, world):
    bundle = await _other(
        client, "patients", _id=str(world["p1"]), _revinclude="Appointment:patient"
    )
    assert _of_type(bundle, "Appointment", "include") == {
        str(world["a"]),
        str(world["c"]),
    }


async def test_revinclude_appointment_actor_on_each_actor_type(client, world):
    for path, key in (
        ("patients", "p2"),
        ("practitioners", "prac1"),
        ("locations", "loc"),
        ("healthcare-services", "hs"),
        ("practitioner-roles", "role"),
    ):
        bundle = await _other(
            client, path, _id=str(world[key]), _revinclude="Appointment:actor"
        )
        got = _of_type(bundle, "Appointment", "include")
        assert got, path
    bundle = await _other(
        client,
        "practitioners",
        _id=str(world["prac2"]),
        _revinclude="Appointment:practitioner",
    )
    assert _of_type(bundle, "Appointment", "include") == {str(world["b"])}
    bundle = await _other(
        client, "locations", _id=str(world["loc"]), _revinclude="Appointment:location"
    )
    assert _of_type(bundle, "Appointment", "include") == {str(world["a"])}


async def test_revinclude_appointment_slot_on_slots(client, world):
    bundle = await _other(
        client, "slots", _id=str(world["s2"]), _revinclude="Appointment:slot"
    )
    assert _of_type(bundle, "Appointment", "include") == {str(world["b"])}


async def test_revinclude_is_tenant_scoped(client, other_client):
    from app.auth.dependencies import get_current_user
    from app.main import app
    from tests.conftest import make_test_user
    from tests.integration.appointment.conftest import APPOINTMENT_PERMS

    def as_user(**kw):
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=APPOINTMENT_PERMS, **kw
        )

    as_user()
    mine = await create_patient(client)
    await create_appointment(client, appointment_body(mine))
    as_user(sub="u-other", org_id="org-other")
    try:
        # The other org can't see the patient, so nothing reaches its appointments.
        bundle = await _other(
            other_client, "patients", _id=str(mine), _revinclude="Appointment:patient"
        )
        assert bundle["total"] == 0 and "entry" not in bundle
        theirs = await create_patient(other_client)
        bundle = await _other(
            other_client, "patients", _id=str(theirs), _revinclude="Appointment:patient"
        )
        assert _of_type(bundle, "Appointment", "include") == set()
    finally:
        as_user()


# ── combination rules / lenient vs strict ────────────────────────────────────


async def test_params_are_anded(client, world):
    assert await _keys(client, world, status="booked", specialty="394579002") == {"a"}
    assert await _keys(client, world, status="booked", specialty="408443003") == set()
    assert await _keys(
        client, world, patient=str(world["p1"]), date="ge2026-07-01"
    ) == {"c"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert (
        await client.get(BASE + "/", params={"status:above": "booked"})
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
        BASE + "/_search", data={"status": "pending", "date": "ge2026-06-01"}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, status="booked")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/appointments/{world['a']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "Appointment"


async def test_empty_result(client, world):
    bundle = await _search(client, status="waitlist")
    assert bundle["total"] == 0 and "entry" not in bundle
