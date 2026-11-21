"""FHIR R4 search over AppointmentResponse (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/appointmentresponse.html#search).

One block per search parameter — `part-status` is a code bound to the real FHIR
codes, `appointment` a single-target reference, `actor`/`patient`/`practitioner`/
`location` all read the one `actor` element (the first is multi-target, the
others narrowed to one type) — then chaining, `_include`/`_revinclude`, result
parameters, combination rules, lenient vs strict handling and POST _search.
"""

import pytest

from tests.integration.appointment_response.support import (
    API,
    AR_IDS,
    BASE,
    appointment_body,
    create_appointment,
    create_healthcare_service,
    create_location,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_response,
    participant,
    response_body,
)

KEYS = ("a", "b", "c", "d", "dev", "hs", "role", "bare")
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
    """Two appointments, patients/practitioner/location/service/role and eight
    appointment responses with distinct, searchable values. Returns {key: id}."""
    w = {}
    w["p1"] = await create_patient(
        client, {"active": True, "name": [{"family": "Windsor", "given": ["Anna"]}]}
    )
    w["p2"] = await create_patient(
        client, {"active": True, "name": [{"family": "Fairfax", "given": ["Ben"]}]}
    )
    w["prac1"] = await create_practitioner(client, "Careful", "Adam")
    w["loc"] = await create_location(client, "North Wing", "Boston")
    w["hs_id"] = await create_healthcare_service(client)
    w["role_id"] = await create_practitioner_role(client)
    w["ap1"] = await create_appointment(
        client, appointment_body(w["p1"], status="booked")
    )
    w["ap2"] = await create_appointment(
        client,
        appointment_body(
            w["p2"],
            status="pending",
            participant=[
                participant(f"Patient/{w['p2']}"),
                participant(f"Location/{w['loc']}"),
            ],
        ),
    )

    def body(appointment, actor, status="accepted", **extra):
        return response_body(appointment, actor, status, **extra)

    w["a"] = await create_response(
        client,
        body(
            w["ap1"],
            f"Patient/{w['p1']}",
            identifier=[
                {"system": AR_IDS, "value": "AR-A", "type": {"text": "Visit number"}}
            ],
            participantType=[{"coding": [{"code": "ATND"}]}],
            comment="First",
        ),
    )
    w["b"] = await create_response(
        client,
        body(
            w["ap2"],
            f"Practitioner/{w['prac1']}",
            "declined",
            identifier=[{"system": AR_IDS, "value": "AR-B"}],
        ),
    )
    w["c"] = await create_response(
        client, body(w["ap1"], f"Location/{w['loc']}", "tentative")
    )
    w["d"] = await create_response(
        client, body(w["ap2"], f"Patient/{w['p2']}", "needs-action")
    )
    w["dev"] = await create_response(client, body(w["ap1"], "Device/6"))
    w["hs"] = await create_response(
        client, body(w["ap1"], f"HealthcareService/{w['hs_id']}")
    )
    w["role"] = await create_response(
        client, body(w["ap1"], f"PractitionerRole/{w['role_id']}")
    )
    w["bare"] = await create_response(client, body(w["ap2"], None))
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
    assert await _keys(client, world, **{"_id:not": str(world["a"])}) == ALL - {"a"}


async def test_last_updated(client, world):
    assert await _keys(client, world, _lastUpdated="ge2020-01-01") == ALL
    assert await _keys(client, world, _lastUpdated="lt2020-01-01") == set()


# ── part-status ──────────────────────────────────────────────────────────────


async def test_part_status(client, world):
    assert await _keys(client, world, **{"part-status": "declined"}) == {"b"}
    assert await _keys(client, world, **{"part-status": "tentative"}) == {"c"}
    assert await _keys(client, world, **{"part-status": "needs-action"}) == {"d"}
    assert await _keys(client, world, **{"part-status": "accepted"}) == {
        "a",
        "dev",
        "hs",
        "role",
        "bare",
    }
    assert await _keys(client, world, **{"part-status": "declined,tentative"}) == {
        "b",
        "c",
    }
    assert await _keys(
        client,
        world,
        **{"part-status": "http://hl7.org/fhir/participationstatus|declined"},
    ) == {"b"}


async def test_part_status_wrong_system_or_unknown_code_matches_nothing(client, world):
    assert (
        await _keys(client, world, **{"part-status": "http://wrong|accepted"}) == set()
    )
    assert await _keys(client, world, **{"part-status": "broken"}) == set()
    assert await _keys(client, world, **{"part-status": "needs_action"}) == set()


async def test_part_status_not_and_missing(client, world):
    assert await _keys(client, world, **{"part-status:not": "accepted"}) == {
        "b",
        "c",
        "d",
    }
    assert await _keys(client, world, **{"part-status:missing": "false"}) == ALL
    assert await _keys(client, world, **{"part-status:missing": "true"}) == set()


# ── identifier ───────────────────────────────────────────────────────────────


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="AR-A") == {"a"}
    assert await _keys(client, world, identifier=f"{AR_IDS}|AR-B") == {"b"}
    assert await _keys(client, world, identifier="urn:other|AR-A") == set()
    assert await _keys(client, world, identifier=f"{AR_IDS}|") == {"a", "b"}


async def test_identifier_text_not_and_missing(client, world):
    assert await _keys(client, world, **{"identifier:text": "Visit"}) == {"a"}
    assert await _keys(client, world, **{"identifier:not": "AR-A"}) == ALL - {"a"}
    assert await _keys(client, world, **{"identifier:missing": "false"}) == {"a", "b"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == ALL - {
        "a",
        "b",
    }


# ── appointment ──────────────────────────────────────────────────────────────


async def test_appointment(client, world):
    assert await _keys(client, world, appointment=str(world["ap2"])) == {
        "b",
        "d",
        "bare",
    }
    assert await _keys(client, world, appointment=f"Appointment/{world['ap1']}") == {
        "a",
        "c",
        "dev",
        "hs",
        "role",
    }
    assert await _keys(client, world, appointment="999999") == set()
    assert await _keys(
        client, world, **{"appointment:Appointment": str(world["ap2"])}
    ) == {"b", "d", "bare"}


async def test_appointment_absolute_and_identifier(client, world):
    ext = "https://other.example.org/fhir/Appointment/1"
    logical = await create_response(
        client, response_body(actor="Device/1")
    )  # absolute appointment
    body = response_body(actor="Device/2")
    body["appointment"] = {"identifier": {"system": "urn:appts", "value": "A-9"}}
    by_identifier = await create_response(client, body)
    assert _ids(await _search(client, appointment=ext)) == {logical}
    assert _ids(
        await _search(client, **{"appointment:identifier": "urn:appts|A-9"})
    ) == {by_identifier}


async def test_appointment_missing(client, world):
    assert await _keys(client, world, **{"appointment:missing": "false"}) == ALL
    assert await _keys(client, world, **{"appointment:missing": "true"}) == set()


async def test_appointment_chain(client, world):
    assert await _keys(client, world, **{"appointment.status": "booked"}) == {
        "a",
        "c",
        "dev",
        "hs",
        "role",
    }
    assert await _keys(client, world, **{"appointment.status": "pending"}) == {
        "b",
        "d",
        "bare",
    }
    assert await _keys(client, world, **{"appointment.patient": str(world["p2"])}) == {
        "b",
        "d",
        "bare",
    }
    assert (
        await client.get(BASE + "/", params={"appointment.nonsense": "x"})
    ).status_code == 400


# ── actor / patient / practitioner / location ────────────────────────────────


async def test_actor_needs_a_type(client, world):
    assert (
        await client.get(BASE + "/", params={"actor": str(world["p1"])})
    ).status_code == 400


async def test_actor_by_type_and_id(client, world):
    assert await _keys(client, world, actor=f"Patient/{world['p1']}") == {"a"}
    assert await _keys(client, world, actor=f"Patient/{world['p2']}") == {"d"}
    assert await _keys(client, world, actor=f"Practitioner/{world['prac1']}") == {"b"}
    assert await _keys(client, world, actor=f"Location/{world['loc']}") == {"c"}
    assert await _keys(client, world, actor=f"HealthcareService/{world['hs_id']}") == {
        "hs"
    }
    assert await _keys(client, world, actor=f"PractitionerRole/{world['role_id']}") == {
        "role"
    }
    assert await _keys(client, world, actor="Device/6") == {"dev"}


async def test_actor_type_modifier_and_type_is_part_of_the_match(client, world):
    assert await _keys(client, world, **{"actor:Patient": str(world["p1"])}) == {"a"}
    # same number, other type: no match
    assert await _keys(client, world, actor=f"Practitioner/{world['p1']}") == set()
    assert (
        await client.get(BASE + "/", params={"actor:Condition": "1"})
    ).status_code == 400


async def test_actor_or_and_and(client, world):
    both = f"Patient/{world['p2']},Practitioner/{world['prac1']}"
    assert await _keys(client, world, actor=both) == {"b", "d"}
    assert (
        await _keys(
            client,
            world,
            actor=[f"Patient/{world['p1']}", f"Practitioner/{world['prac1']}"],
        )
        == set()
    )


async def test_actor_identifier_and_absolute(client, world):
    body = response_body()
    body["actor"] = {"identifier": {"system": "urn:pts", "value": "P-9"}}
    logical = await create_response(client, body)
    ext = await create_response(
        client, response_body(actor="https://other.example.org/fhir/Patient/1")
    )
    assert _ids(await _search(client, **{"actor:identifier": "urn:pts|P-9"})) == {
        logical
    }
    assert _ids(
        await _search(client, actor="https://other.example.org/fhir/Patient/1")
    ) == {ext}
    assert logical not in _ids(await _search(client, actor=f"Patient/{world['p1']}"))
    # A logical actor has no resolved type, so it is *missing* for every narrowed parameter.
    for param in ("patient", "practitioner", "location"):
        assert logical in _ids(await _search(client, **{f"{param}:missing": "true"})), (
            param
        )
        assert logical not in _ids(
            await _search(client, **{f"{param}:missing": "false"})
        ), param


async def test_actor_missing(client, world):
    assert await _keys(client, world, **{"actor:missing": "true"}) == {"bare"}
    assert await _keys(client, world, **{"actor:missing": "false"}) == ALL - {"bare"}


async def test_patient_practitioner_location(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {"a"}
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"d"}
    assert await _keys(client, world, practitioner=str(world["prac1"])) == {"b"}
    assert await _keys(client, world, location=str(world["loc"])) == {"c"}
    assert await _keys(client, world, patient=f"{world['p1']},{world['p2']}") == {
        "a",
        "d",
    }


async def test_narrowed_params_only_match_their_type(client, world):
    assert await _keys(client, world, patient=f"Practitioner/{world['prac1']}") == set()
    assert await _keys(client, world, practitioner=f"Patient/{world['p1']}") == set()
    assert await _keys(client, world, **{"location:missing": "true"}) == ALL - {"c"}
    assert await _keys(client, world, **{"patient:missing": "false"}) == {"a", "d"}


async def test_patient_and_part_status_are_anded(client, world):
    assert await _keys(
        client, world, patient=str(world["p2"]), **{"part-status": "needs-action"}
    ) == {"d"}
    assert (
        await _keys(
            client, world, patient=str(world["p1"]), **{"part-status": "needs-action"}
        )
        == set()
    )


# ── chaining ─────────────────────────────────────────────────────────────────


async def test_patient_chain(client, world):
    assert await _keys(client, world, **{"patient.family": "Windsor"}) == {"a"}
    assert await _keys(client, world, **{"patient.family": "Fairfax"}) == {"d"}
    assert await _keys(client, world, **{"patient.given": "Anna"}) == {"a"}


async def test_practitioner_and_location_chain(client, world):
    assert await _keys(client, world, **{"practitioner.family": "Careful"}) == {"b"}
    assert await _keys(client, world, **{"location.address-city": "Boston"}) == {"c"}
    assert await _keys(client, world, **{"location.address-city": "Paris"}) == set()


async def test_actor_chain_through_a_typed_target(client, world):
    assert await _keys(client, world, **{"actor:Practitioner.family": "Careful"}) == {
        "b"
    }
    assert await _keys(client, world, **{"actor:Patient.family": "Windsor"}) == {"a"}
    assert await _keys(client, world, **{"actor:Location.address-city": "Boston"}) == {
        "c"
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
    assert (
        await client.get(BASE + "/", params={"part-status.x": "y"})
    ).status_code == 400


# ── _sort / _count / _offset / _total ────────────────────────────────────────


async def test_sort_by_other_params(client, world):
    for key in ("part-status", "patient", "actor", "identifier", "appointment", "_id"):
        assert (await _search(client, _sort=key))["total"] == 8, key
    assert (
        await client.get(BASE + "/", params={"_sort": "comment"})
    ).status_code == 400


async def test_sort_by_part_status_groups_rows_and_descending_reverses_it(
    client, world
):
    """The order of the codes themselves is the database's (alphabetical on the
    SQLite test DB, enum order on Postgres), so only the grouping is asserted."""

    async def statuses(sort):
        return [
            e["resource"]["participantStatus"]
            for e in (await _search(client, _sort=sort))["entry"]
        ]

    def groups(values):
        return [v for i, v in enumerate(values) if i == 0 or values[i - 1] != v]

    asc, desc = await statuses("part-status"), await statuses("-part-status")
    assert len(groups(asc)) == len(set(asc)) == 4  # each status is one contiguous run
    assert groups(desc) == list(reversed(groups(asc)))


async def test_default_sort_is_newest_first(client, world):
    got = [int(e["resource"]["id"]) for e in (await _search(client))["entry"]]
    assert got == sorted(got, reverse=True)


async def test_paging_and_total(client, world):
    page = await _search(client, _count=3, _sort="_id")
    assert page["total"] == 8 and len(page["entry"]) == 3
    assert any(link["relation"] == "next" for link in page["link"])
    nxt = await _search(client, _count=3, _offset=3, _sort="_id")
    assert not (
        {e["resource"]["id"] for e in page["entry"]}
        & {e["resource"]["id"] for e in nxt["entry"]}
    )
    assert "entry" not in await _search(client, _count=0)
    assert "total" not in await _search(client, _total="none")


async def test_summary_count_and_elements(client, world):
    assert (await _search(client, _summary="count"))["total"] == 8
    resource = (
        await _search(client, _elements="participantStatus", _id=str(world["a"]))
    )["entry"][0]["resource"]
    assert resource["participantStatus"] == "accepted"
    assert "comment" not in resource and "identifier" not in resource


# ── _include ─────────────────────────────────────────────────────────────────


async def test_include_appointment(client, world):
    bundle = await _search(
        client, _id=str(world["a"]), _include="AppointmentResponse:appointment"
    )
    assert _of_type(bundle, "Appointment", "include") == {str(world["ap1"])}


async def test_include_appointment_is_deduplicated(client, world):
    bundle = await _search(
        client,
        appointment=str(world["ap1"]),
        _include="AppointmentResponse:appointment",
    )
    assert (
        sum(
            1 for e in bundle["entry"] if e["resource"]["resourceType"] == "Appointment"
        )
        == 1
    )


async def test_include_actor_brings_every_modeled_type(client, world):
    for key, rtype, actor_id in (
        ("a", "Patient", world["p1"]),
        ("b", "Practitioner", world["prac1"]),
        ("c", "Location", world["loc"]),
        ("hs", "HealthcareService", world["hs_id"]),
        ("role", "PractitionerRole", world["role_id"]),
    ):
        bundle = await _search(
            client, _id=str(world[key]), _include="AppointmentResponse:actor"
        )
        assert _of_type(bundle, rtype, "include") == {str(actor_id)}, rtype


async def test_include_actor_with_type(client, world):
    bundle = await _search(
        client, _id=str(world["c"]), _include="AppointmentResponse:actor:Location"
    )
    assert {e["resource"]["resourceType"] for e in bundle["entry"]} == {
        "AppointmentResponse",
        "Location",
    }
    other = await _search(
        client, _id=str(world["c"]), _include="AppointmentResponse:actor:Patient"
    )
    assert {e["resource"]["resourceType"] for e in other["entry"]} == {
        "AppointmentResponse"
    }


async def test_include_narrowed_params(client, world):
    bundle = await _search(
        client,
        _id=str(world["a"]),
        _include=["AppointmentResponse:patient", "AppointmentResponse:practitioner"],
    )
    assert _of_type(bundle, "Patient", "include") == {str(world["p1"])}
    assert _of_type(bundle, "Practitioner", "include") == set()


async def test_include_nothing_for_actors_that_are_not_resources(client, world):
    bundle = await _search(
        client, _id=str(world["dev"]), _include="AppointmentResponse:actor"
    )
    assert {e["resource"]["resourceType"] for e in bundle["entry"]} == {
        "AppointmentResponse"
    }
    bare = await _search(
        client, _id=str(world["bare"]), _include="AppointmentResponse:actor"
    )
    assert {e["resource"]["resourceType"] for e in bare["entry"]} == {
        "AppointmentResponse"
    }


# ── _revinclude (declared on the other side) ─────────────────────────────────


async def _other(client, path, **params) -> dict:
    resp = await client.get(f"{API}/{path}/", params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_revinclude_appointment_response_on_appointments(client, world):
    bundle = await _other(
        client,
        "appointments",
        _id=str(world["ap2"]),
        _revinclude="AppointmentResponse:appointment",
    )
    assert _of_type(bundle, "AppointmentResponse", "include") == {
        str(world[k]) for k in ("b", "d", "bare")
    }


async def test_revinclude_appointment_response_patient_on_patients(client, world):
    bundle = await _other(
        client,
        "patients",
        _id=str(world["p1"]),
        _revinclude="AppointmentResponse:patient",
    )
    assert _of_type(bundle, "AppointmentResponse", "include") == {str(world["a"])}


async def test_revinclude_appointment_response_actor_on_each_actor_type(client, world):
    for path, actor_id, key in (
        ("patients", world["p2"], "d"),
        ("practitioners", world["prac1"], "b"),
        ("locations", world["loc"], "c"),
        ("healthcare-services", world["hs_id"], "hs"),
        ("practitioner-roles", world["role_id"], "role"),
    ):
        bundle = await _other(
            client, path, _id=str(actor_id), _revinclude="AppointmentResponse:actor"
        )
        assert _of_type(bundle, "AppointmentResponse", "include") == {
            str(world[key])
        }, path
    bundle = await _other(
        client,
        "practitioners",
        _id=str(world["prac1"]),
        _revinclude="AppointmentResponse:practitioner",
    )
    assert _of_type(bundle, "AppointmentResponse", "include") == {str(world["b"])}
    bundle = await _other(
        client,
        "locations",
        _id=str(world["loc"]),
        _revinclude="AppointmentResponse:location",
    )
    assert _of_type(bundle, "AppointmentResponse", "include") == {str(world["c"])}


async def test_revinclude_is_tenant_scoped(client, other_client):
    from app.auth.dependencies import get_current_user
    from app.main import app
    from tests.conftest import make_test_user
    from tests.integration.appointment_response.conftest import (
        APPOINTMENT_RESPONSE_PERMS,
    )

    def as_user(**kw):
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=APPOINTMENT_RESPONSE_PERMS, **kw
        )

    as_user()
    mine = await create_patient(client)
    appointment = await create_appointment(client, appointment_body(mine))
    await create_response(client, response_body(appointment, f"Patient/{mine}"))
    as_user(sub="u-other", org_id="org-other")
    try:
        # The other org cannot see the patient, so nothing reaches its responses.
        bundle = await _other(
            other_client,
            "patients",
            _id=str(mine),
            _revinclude="AppointmentResponse:patient",
        )
        assert bundle["total"] == 0 and "entry" not in bundle
        theirs = await create_patient(other_client)
        bundle = await _other(
            other_client,
            "patients",
            _id=str(theirs),
            _revinclude="AppointmentResponse:patient",
        )
        assert _of_type(bundle, "AppointmentResponse", "include") == set()
    finally:
        as_user()


# ── combination rules / lenient vs strict ────────────────────────────────────


async def test_params_are_anded(client, world):
    assert await _keys(
        client, world, **{"part-status": "accepted"}, appointment=str(world["ap2"])
    ) == {"bare"}
    assert (
        await _keys(
            client, world, **{"part-status": "declined"}, appointment=str(world["ap1"])
        )
        == set()
    )


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert (
        await client.get(BASE + "/", params={"part-status:above": "accepted"})
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
        BASE + "/_search",
        data={"part-status": "declined", "appointment": str(world["ap2"])},
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, **{"part-status": "declined"})
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/appointment-responses/{world['b']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "AppointmentResponse"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
