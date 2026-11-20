"""FHIR R4 search over Encounter (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/encounter.html#search).

One block per search parameter — `status`/`class` are codes, `date` and
`location-period` are Period searches, `length` is the engine's first
`quantity` search, `subject`/`participant`/`diagnosis`/`reason-reference` are
multi-target references (a bare id is ambiguous), `patient`/`practitioner` are
the same elements narrowed to one type — then chaining, `_include`/
`_revinclude` in both directions, result parameters, combination rules,
lenient vs strict handling and POST _search.
"""

import pytest

from tests.integration.encounter.support import (
    ACT,
    API,
    BASE,
    ENC_IDS,
    PART,
    SCT,
    SPECIAL,
    UCUM,
    appointment_body,
    create_appointment,
    create_condition,
    create_encounter,
    create_location,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    encounter_body,
)

KEYS = ("a", "b", "c", "d", "e")
ALL = set(KEYS)


def _ids(bundle: dict) -> set[int]:
    return {int(e["resource"]["id"]) for e in bundle.get("entry") or [] if e["search"]["mode"] == "match"}


def _of_type(bundle: dict, rtype: str, mode: str) -> set[str]:
    return {
        e["resource"]["id"]
        for e in bundle.get("entry") or []
        if e["resource"]["resourceType"] == rtype and e["search"]["mode"] == mode
    }


@pytest.fixture
async def world(client):
    """A patient, practitioner, role, location, organization and appointment,
    and five encounters with distinct, searchable values. Returns {key: id}."""
    w = {}
    w["p1"] = await create_patient(client, {"active": True, "name": [{"family": "Windsor", "given": ["Anna"]}]})
    w["p2"] = await create_patient(client, {"active": True, "name": [{"family": "Fairfax", "given": ["Ben"]}]})
    w["prac"] = await create_practitioner(client, "Careful", "Adam")
    w["role"] = await create_practitioner_role(client)
    w["loc"] = await create_location(client, "North Wing", "Boston")
    w["org"] = await create_organization(client, "Providing Org")
    w["ap"] = await create_appointment(client, appointment_body(w["p1"], status="booked"))
    w["cond"] = await create_condition(client, w["p1"])
    rp = await client.post(
        API + "/related-persons/",
        json={"patient": {"reference": f"Patient/{w['p1']}"}, "name": [{"family": "Relative"}]},
    )
    assert rp.status_code == 201, rp.text
    w["rp"] = int(rp.json()["id"])

    w["a"] = await create_encounter(
        client,
        encounter_body(
            "in-progress",
            **{
                "class": {"system": ACT, "code": "AMB", "display": "Ambulatory"},
                "identifier": [{"system": ENC_IDS, "value": "E-A", "type": {"text": "Visit number"}}],
                "type": [{"coding": [{"system": SCT, "code": "270427003"}], "text": "Initial"}],
                "subject": {"reference": f"Patient/{w['p1']}"},
                "participant": [
                    {"type": [{"coding": [{"system": PART, "code": "ATND"}]}],
                     "individual": {"reference": f"Practitioner/{w['prac']}"}}
                ],
                "appointment": [{"reference": f"Appointment/{w['ap']}"}],
                "period": {"start": "2026-06-01T09:00:00Z", "end": "2026-06-01T10:00:00Z"},
                "length": {"value": 2, "unit": "d", "system": UCUM, "code": "d"},
                "reasonCode": [{"coding": [{"system": SCT, "code": "185347001"}]}],
                "location": [
                    {"location": {"reference": f"Location/{w['loc']}"},
                     "period": {"start": "2026-06-01T09:00:00Z", "end": "2026-06-01T09:30:00Z"}}
                ],
                "serviceProvider": {"reference": f"Organization/{w['org']}"},
                "hospitalization": {"specialArrangement": [{"coding": [{"system": SPECIAL, "code": "wheel"}]}]},
                "diagnosis": [{"condition": {"reference": f"Condition/{w['cond']}"}}],
                "reasonReference": [{"reference": "Observation/5"}],
                "basedOn": [{"reference": "ServiceRequest/80001"}],
                "episodeOfCare": [{"reference": "EpisodeOfCare/350001"}],
                "account": [{"reference": "Account/7"}],
            },
        ),
    )
    w["b"] = await create_encounter(
        client,
        encounter_body(
            "finished", "IMP",
            identifier=[{"system": ENC_IDS, "value": "E-B"}],
            type=[{"coding": [{"system": SCT, "code": "11429006"}], "text": "Consultation"}],
            subject={"reference": f"Patient/{w['p2']}"},
            partOf={"reference": f"Encounter/{w['a']}"},
            participant=[{"individual": {"reference": f"PractitionerRole/{w['role']}"}}],
            period={"start": "2026-05-01T00:00:00Z", "end": "2026-05-02T00:00:00Z"},
            length={"value": 5, "unit": "days", "system": UCUM, "code": "d"},
            reasonReference=[{"reference": f"Condition/{w['cond']}"}],
        ),
    )
    w["c"] = await create_encounter(
        client,
        encounter_body(
            "planned", "EMER",
            subject={"reference": "Group/9"},
            period={"start": "2026-07-01T00:00:00Z"},
            length={"value": 90, "unit": "min", "system": UCUM, "code": "min"},
        ),
    )
    w["d"] = await create_encounter(
        client,
        encounter_body("cancelled", "AMB", participant=[{"individual": {"reference": f"RelatedPerson/{w['rp']}"}}]),
    )
    w["e"] = await create_encounter(
        client,
        encounter_body(
            "entered-in-error", "VR", subject={"identifier": {"system": "urn:pts", "value": "P-9"}}
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
    assert await _keys(client, world, status="in-progress") == {"a"}
    assert await _keys(client, world, status="entered-in-error") == {"e"}
    assert await _keys(client, world, status="finished,cancelled") == {"b", "d"}
    assert await _keys(client, world, status="http://hl7.org/fhir/encounter-status|planned") == {"c"}


async def test_status_wrong_system_or_unknown_code_matches_nothing(client, world):
    assert await _keys(client, world, status="http://wrong|planned") == set()
    assert await _keys(client, world, status="broken") == set()
    assert await _keys(client, world, status="in_progress") == set()


async def test_status_not_and_missing(client, world):
    assert await _keys(client, world, **{"status:not": "finished"}) == ALL - {"b"}
    assert await _keys(client, world, **{"status:missing": "true"}) == set()
    assert await _keys(client, world, **{"status:missing": "false"}) == ALL


# ── class (a bare Coding) ────────────────────────────────────────────────────


async def test_class(client, world):
    assert await _keys(client, world, **{"class": "AMB"}) == {"a", "d"}
    assert await _keys(client, world, **{"class": f"{ACT}|IMP"}) == {"b"}
    assert await _keys(client, world, **{"class": f"{ACT}|"}) == ALL
    assert await _keys(client, world, **{"class": "http://wrong|AMB"}) == set()
    assert await _keys(client, world, **{"class": "EMER,VR"}) == {"c", "e"}


async def test_class_text_not_and_missing(client, world):
    assert await _keys(client, world, **{"class:text": "ambul"}) == {"a"}
    assert await _keys(client, world, **{"class:not": "AMB"}) == {"b", "c", "e"}
    assert await _keys(client, world, **{"class:missing": "true"}) == set()


# ── date (Period) ────────────────────────────────────────────────────────────


async def test_date_default_is_contained_in_the_range(client, world):
    assert await _keys(client, world, date="2026-06-01") == {"a"}
    assert await _keys(client, world, date="2026-05") == {"b"}
    assert await _keys(client, world, date="2026-06-01T09:00:00Z") == set()  # no period lies within one instant


async def test_date_prefixes(client, world):
    assert await _keys(client, world, date="ge2026-06-01") == {"a", "c"}  # the period overlaps the range above
    assert await _keys(client, world, date="lt2026-06-01") == {"b"}
    assert await _keys(client, world, date="gt2026-07-01") == {"c"}  # an open-ended period reaches beyond
    assert await _keys(client, world, date="sa2026-06-02") == {"c"}
    assert await _keys(client, world, date="eb2026-05-15") == {"b"}


async def test_date_and_and_missing(client, world):
    assert await _keys(client, world, date=["ge2026-05-01", "lt2026-06-01"]) == {"b"}
    assert await _keys(client, world, **{"date:missing": "true"}) == {"d", "e"}
    assert await _keys(client, world, **{"date:missing": "false"}) == {"a", "b", "c"}


# ── location-period ──────────────────────────────────────────────────────────


async def test_location_period(client, world):
    assert await _keys(client, world, **{"location-period": "2026-06-01"}) == {"a"}
    assert await _keys(client, world, **{"location-period": "ge2026-06-01"}) == {"a"}
    assert await _keys(client, world, **{"location-period": "lt2026-06-01"}) == set()
    assert await _keys(client, world, **{"location-period:missing": "true"}) == {"b", "c", "d", "e"}


# ── length (quantity) ────────────────────────────────────────────────────────


async def test_length_number_precision(client, world):
    assert await _keys(client, world, length="2") == {"a"}  # the range [1.5, 2.5)
    assert await _keys(client, world, length="5") == {"b"}
    assert await _keys(client, world, length="2.0") == {"a"}  # [1.95, 2.05)
    assert await _keys(client, world, length="3") == set()
    assert await _keys(client, world, length="ne2") == {"b", "c"}  # a row with no length never matches
    assert await _keys(client, world, length="ap5") == {"b"}


async def test_length_comparison_prefixes(client, world):
    assert await _keys(client, world, length="gt2") == {"b", "c"}
    assert await _keys(client, world, length="ge2") == {"a", "b", "c"}
    assert await _keys(client, world, length="lt5") == {"a"}
    assert await _keys(client, world, length="le5") == {"a", "b"}
    assert await _keys(client, world, length=["gt1", "lt6"]) == {"a", "b"}
    assert await _keys(client, world, length="gt2,lt1") == {"b", "c"}


async def test_length_units(client, world):
    assert await _keys(client, world, length=f"2|{UCUM}|d") == {"a"}
    assert await _keys(client, world, length=f"gt2|{UCUM}|d") == {"b"}  # c is 90 `min`, not days
    assert await _keys(client, world, length=f"ge90|{UCUM}|min") == {"c"}
    assert await _keys(client, world, length=f"2|{UCUM}|") == {"a"}  # system only
    assert await _keys(client, world, length="2|http://wrong|d") == set()
    assert await _keys(client, world, length=f"2|{UCUM}|min") == set()


async def test_length_code_without_system_also_matches_the_unit_text(client, world):
    assert await _keys(client, world, length="5||d") == {"b"}  # the code
    assert await _keys(client, world, length="5||days") == {"b"}  # the human unit
    assert await _keys(client, world, length="gt1||min") == {"c"}


async def test_length_missing_and_bad_values(client, world):
    assert await _keys(client, world, **{"length:missing": "true"}) == {"d", "e"}
    for bad in ("abc", "gt", "1|2|3|4", "5e"):
        assert await _status(client, length=bad) == 400, bad
    assert await _status(client, **{"length:exact": "5"}) == 400  # a quantity takes no :exact


# ── identifier / type / reason-code / special-arrangement / participant-type ──


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="E-A") == {"a"}
    assert await _keys(client, world, identifier=f"{ENC_IDS}|E-B") == {"b"}
    assert await _keys(client, world, identifier="E-A,E-B") == {"a", "b"}
    assert await _keys(client, world, identifier="urn:other|E-A") == set()


async def test_identifier_text_not_and_missing(client, world):
    assert await _keys(client, world, **{"identifier:text": "visit"}) == {"a"}
    assert await _keys(client, world, **{"identifier:not": "E-A"}) == ALL - {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {"c", "d", "e"}


async def test_type(client, world):
    assert await _keys(client, world, type="270427003") == {"a"}
    assert await _keys(client, world, type=f"{SCT}|11429006") == {"b"}
    assert await _keys(client, world, **{"type:text": "consult"}) == {"b"}
    assert await _keys(client, world, **{"type:missing": "true"}) == {"c", "d", "e"}


async def test_reason_code_special_arrangement_and_participant_type(client, world):
    assert await _keys(client, world, **{"reason-code": "185347001"}) == {"a"}
    assert await _keys(client, world, **{"special-arrangement": f"{SPECIAL}|wheel"}) == {"a"}
    assert await _keys(client, world, **{"special-arrangement": "walker"}) == set()
    assert await _keys(client, world, **{"participant-type": "ATND"}) == {"a"}
    assert await _keys(client, world, **{"participant-type:missing": "true"}) == {"b", "c", "d", "e"}


# ── subject / patient ────────────────────────────────────────────────────────


async def test_subject_needs_a_type(client, world):
    assert await _status(client, subject=str(world["p1"])) == 400  # Patient | Group is ambiguous


async def test_subject_by_type_and_id(client, world):
    assert await _keys(client, world, subject=f"Patient/{world['p1']}") == {"a"}
    assert await _keys(client, world, **{"subject:Patient": str(world["p2"])}) == {"b"}
    assert await _keys(client, world, subject="Group/9") == {"c"}
    assert await _keys(client, world, **{"subject:Group": "9"}) == {"c"}
    assert await _keys(client, world, subject=f"Patient/{world['p1']},Group/9") == {"a", "c"}


async def test_subject_type_is_part_of_the_match(client, world):
    assert await _keys(client, world, subject=f"Group/{world['p1']}") == set()
    assert await _keys(client, world, **{"subject:Group": str(world["p1"])}) == set()


async def test_subject_identifier_absolute_and_missing(client, world):
    assert await _keys(client, world, **{"subject:identifier": "urn:pts|P-9"}) == {"e"}
    assert await _keys(client, world, **{"subject:missing": "true"}) == {"d"}
    assert await _keys(client, world, **{"subject:missing": "false"}) == {"a", "b", "c", "e"}


async def test_patient_is_subject_narrowed_to_patients(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {"a"}  # a bare id works: one target
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"b"}
    assert await _keys(client, world, patient="9") == set()  # Group/9 is not a Patient
    assert await _keys(client, world, **{"patient:missing": "true"}) == {"c", "d", "e"}


# ── participant / practitioner ───────────────────────────────────────────────


async def test_participant_needs_a_type(client, world):
    assert await _status(client, participant=str(world["prac"])) == 400


async def test_participant_by_type_and_id(client, world):
    assert await _keys(client, world, participant=f"Practitioner/{world['prac']}") == {"a"}
    assert await _keys(client, world, participant=f"PractitionerRole/{world['role']}") == {"b"}
    assert await _keys(client, world, participant=f"RelatedPerson/{world['rp']}") == {"d"}
    assert await _keys(client, world, participant="RelatedPerson/5") == set()
    assert await _keys(client, world, **{"participant:Practitioner": str(world["prac"])}) == {"a"}
    assert await _keys(client, world, participant=f"Practitioner/{world['role']}") == set()  # the type is part of the match
    assert await _keys(client, world, **{"participant:missing": "true"}) == {"c", "e"}


async def test_practitioner_is_participant_narrowed_to_practitioners(client, world):
    assert await _keys(client, world, practitioner=str(world["prac"])) == {"a"}
    assert await _keys(client, world, practitioner=str(world["role"])) == set()
    assert await _keys(client, world, **{"practitioner:missing": "true"}) == {"b", "c", "d", "e"}


# ── location / service-provider / part-of / appointment ──────────────────────


async def test_location(client, world):
    assert await _keys(client, world, location=str(world["loc"])) == {"a"}
    assert await _keys(client, world, location=f"Location/{world['loc']}") == {"a"}
    assert await _keys(client, world, location="999999") == set()
    assert await _keys(client, world, **{"location:missing": "true"}) == {"b", "c", "d", "e"}


async def test_service_provider(client, world):
    assert await _keys(client, world, **{"service-provider": str(world["org"])}) == {"a"}
    assert await _keys(client, world, **{"service-provider": f"Organization/{world['org']}"}) == {"a"}
    assert await _keys(client, world, **{"service-provider:missing": "true"}) == {"b", "c", "d", "e"}


async def test_part_of(client, world):
    assert await _keys(client, world, **{"part-of": str(world["a"])}) == {"b"}
    assert await _keys(client, world, **{"part-of": f"Encounter/{world['a']}"}) == {"b"}
    assert await _keys(client, world, **{"part-of:missing": "true"}) == {"a", "c", "d", "e"}


async def test_appointment(client, world):
    assert await _keys(client, world, appointment=str(world["ap"])) == {"a"}
    assert await _keys(client, world, appointment=f"Appointment/{world['ap']}") == {"a"}
    assert await _keys(client, world, **{"appointment:missing": "true"}) == {"b", "c", "d", "e"}


# ── references to resources not on this server ───────────────────────────────


async def test_account_based_on_episode_of_care(client, world):
    assert await _keys(client, world, account="7") == {"a"}
    assert await _keys(client, world, account="Account/7") == {"a"}
    assert await _keys(client, world, **{"based-on": "80001"}) == {"a"}
    assert await _keys(client, world, **{"episode-of-care": "EpisodeOfCare/350001"}) == {"a"}
    assert await _keys(client, world, account="Account/8") == set()
    assert await _keys(client, world, **{"based-on:missing": "true"}) == {"b", "c", "d", "e"}


async def test_diagnosis_and_reason_reference_need_a_type(client, world):
    assert await _status(client, diagnosis=str(world["cond"])) == 400
    assert await _status(client, **{"reason-reference": str(world["cond"])}) == 400


async def test_diagnosis_and_reason_reference(client, world):
    cond = world["cond"]
    assert await _keys(client, world, diagnosis=f"Condition/{cond}") == {"a"}
    assert await _keys(client, world, **{"diagnosis:Condition": str(cond)}) == {"a"}
    assert await _keys(client, world, diagnosis=f"Procedure/{cond}") == set()  # the type is part of the match
    assert await _keys(client, world, **{"reason-reference": "Observation/5"}) == {"a"}
    assert await _keys(client, world, **{"reason-reference": f"Condition/{cond}"}) == {"b"}
    assert await _keys(client, world, **{"reason-reference": f"Observation/5,Condition/{cond}"}) == {"a", "b"}


# ── chaining ─────────────────────────────────────────────────────────────────


async def test_patient_and_subject_chain(client, world):
    assert await _keys(client, world, **{"patient.family": "Windsor"}) == {"a"}
    assert await _keys(client, world, **{"subject:Patient.family": "Fairfax"}) == {"b"}
    assert await _keys(client, world, **{"patient.family": "Nobody"}) == set()


async def test_participant_and_practitioner_chain(client, world):
    assert await _keys(client, world, **{"practitioner.family": "Careful"}) == {"a"}
    assert await _keys(client, world, **{"participant:Practitioner.family": "Careful"}) == {"a"}
    assert await _keys(client, world, **{"participant:PractitionerRole.active": "true"}) <= {"b"}
    assert await _keys(client, world, **{"participant:RelatedPerson.name": "Relative"}) == {"d"}
    assert await _keys(client, world, **{"participant:RelatedPerson.name": "Nobody"}) == set()


async def test_location_service_provider_part_of_and_appointment_chain(client, world):
    assert await _keys(client, world, **{"location.address-city": "Boston"}) == {"a"}
    assert await _keys(client, world, **{"service-provider.name": "Providing"}) == {"a"}
    assert await _keys(client, world, **{"part-of.status": "in-progress"}) == {"b"}
    assert await _keys(client, world, **{"part-of.class": "IMP"}) == set()
    assert await _keys(client, world, **{"appointment.status": "booked"}) == {"a"}
    assert await _keys(client, world, **{"appointment.status": "pending"}) == set()


async def test_bad_chains_are_400(client, world):
    assert await _status(client, **{"subject.family": "x"}) == 400  # untyped, two targets
    assert await _status(client, **{"subject:Group.name": "x"}) == 400  # Group is not a resource here
    assert await _status(client, **{"participant:Device.name": "x"}) == 400  # Device is not a resource here
    assert await _status(client, **{"patient.nonsense": "x"}) == 400
    assert await _status(client, **{"account.name": "x"}) == 400  # Account is not a resource here
    assert await _status(client, **{"status.x": "y"}) == 400


# ── _sort / _count / _offset / _total ────────────────────────────────────────


async def test_sort_by_other_params(client, world):
    for key in ("status", "class", "date", "length", "subject", "patient", "participant", "location", "identifier",
                "type", "part-of", "service-provider", "appointment", "_id"):
        assert (await _search(client, _sort=key))["total"] == 5, key
    assert await _status(client, _sort="serviceType") == 400


async def test_sort_by_length_and_date(client, world):
    async def ids(**params):
        return [int(e["resource"]["id"]) for e in (await _search(client, **params))["entry"]]

    assert await ids(**{"length:missing": "false", "_sort": "length"}) == [world["a"], world["b"], world["c"]]
    assert await ids(**{"length:missing": "false", "_sort": "-length"}) == [world["c"], world["b"], world["a"]]
    assert await ids(**{"date:missing": "false", "_sort": "date"}) == [world["b"], world["a"], world["c"]]
    assert await ids(**{"date:missing": "false", "_sort": "-date"}) == [world["c"], world["a"], world["b"]]


async def test_default_sort_is_newest_first(client, world):
    got = [int(e["resource"]["id"]) for e in (await _search(client))["entry"]]
    assert got == sorted(got, reverse=True)


async def test_paging_and_total(client, world):
    page = await _search(client, _count=2, _sort="_id")
    assert page["total"] == 5 and len(page["entry"]) == 2
    assert any(link["relation"] == "next" for link in page["link"])
    nxt = await _search(client, _count=2, _offset=2, _sort="_id")
    assert not ({e["resource"]["id"] for e in page["entry"]} & {e["resource"]["id"] for e in nxt["entry"]})
    assert "entry" not in await _search(client, _count=0)
    assert "total" not in await _search(client, _total="none")


async def test_summary_count_and_elements(client, world):
    assert (await _search(client, _summary="count"))["total"] == 5
    resource = (await _search(client, _elements="status", _id=str(world["a"])))["entry"][0]["resource"]
    assert resource["status"] == "in-progress"
    assert "period" not in resource and "identifier" not in resource


# ── _include ─────────────────────────────────────────────────────────────────


async def test_include_patient_and_subject(client, world):
    for param in ("patient", "subject"):
        bundle = await _search(client, _id=str(world["a"]), _include=f"Encounter:{param}")
        assert _of_type(bundle, "Patient", "include") == {str(world["p1"])}, param


async def test_include_nothing_for_subjects_that_are_not_resources(client, world):
    bundle = await _search(client, _id=str(world["c"]), _include="Encounter:subject")
    assert _of_type(bundle, "Patient", "include") == set()


async def test_include_appointment_location_and_service_provider(client, world):
    bundle = await _search(
        client, _id=str(world["a"]),
        _include=["Encounter:appointment", "Encounter:location", "Encounter:service-provider"],
    )
    assert _of_type(bundle, "Appointment", "include") == {str(world["ap"])}
    assert _of_type(bundle, "Location", "include") == {str(world["loc"])}
    assert _of_type(bundle, "Organization", "include") == {str(world["org"])}


async def test_include_participant_brings_every_modeled_type(client, world):
    bundle = await _search(client, _id=f"{world['a']},{world['b']},{world['d']}", _include="Encounter:participant")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["prac"])}
    assert _of_type(bundle, "PractitionerRole", "include") == {str(world["role"])}
    assert _of_type(bundle, "RelatedPerson", "include") == {str(world["rp"])}


async def test_include_participant_with_type_and_practitioner(client, world):
    bundle = await _search(client, _id=f"{world['a']},{world['b']}", _include="Encounter:participant:Practitioner")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["prac"])}
    assert _of_type(bundle, "PractitionerRole", "include") == set()
    bundle = await _search(client, _id=f"{world['a']},{world['b']}", _include="Encounter:practitioner")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["prac"])}


async def test_include_part_of(client, world):
    bundle = await _search(client, _id=str(world["b"]), _include="Encounter:part-of")
    assert _of_type(bundle, "Encounter", "include") == {str(world["a"])}


async def test_include_is_deduplicated(client, world):
    bundle = await _search(client, patient=str(world["p1"]), _include="Encounter:patient")
    assert sum(1 for e in bundle["entry"] if e["resource"]["resourceType"] == "Patient") == 1


# ── _revinclude ──────────────────────────────────────────────────────────────


async def _other(client, path, **params) -> dict:
    resp = await client.get(f"{API}/{path}/", params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_revinclude_on_patients(client, world):
    for param in ("patient", "subject"):
        bundle = await _other(client, "patients", _id=str(world["p2"]), _revinclude=f"Encounter:{param}")
        assert _of_type(bundle, "Encounter", "include") == {str(world["b"])}, param


async def test_revinclude_on_practitioners_and_roles(client, world):
    for param in ("participant", "practitioner"):
        bundle = await _other(client, "practitioners", _id=str(world["prac"]), _revinclude=f"Encounter:{param}")
        assert _of_type(bundle, "Encounter", "include") == {str(world["a"])}, param
    bundle = await _other(client, "practitioner-roles", _id=str(world["role"]), _revinclude="Encounter:participant")
    assert _of_type(bundle, "Encounter", "include") == {str(world["b"])}
    bundle = await _other(client, "related-persons", _id=str(world["rp"]), _revinclude="Encounter:participant")
    assert _of_type(bundle, "Encounter", "include") == {str(world["d"])}


async def test_revinclude_on_locations_appointments_and_organizations(client, world):
    bundle = await _other(client, "locations", _id=str(world["loc"]), _revinclude="Encounter:location")
    assert _of_type(bundle, "Encounter", "include") == {str(world["a"])}
    bundle = await _other(client, "appointments", _id=str(world["ap"]), _revinclude="Encounter:appointment")
    assert _of_type(bundle, "Encounter", "include") == {str(world["a"])}
    bundle = await _other(client, "organizations", _id=str(world["org"]), _revinclude="Encounter:service-provider")
    assert _of_type(bundle, "Encounter", "include") == {str(world["a"])}


async def test_revinclude_part_of_on_encounters(client, world):
    bundle = await _search(client, _id=str(world["a"]), _revinclude="Encounter:part-of")
    assert _of_type(bundle, "Encounter", "include") == {str(world["b"])}


async def test_revinclude_is_tenant_scoped(client, other_client):
    from app.auth.dependencies import get_current_user
    from app.main import app
    from tests.conftest import make_test_user
    from tests.integration.encounter.conftest import ENCOUNTER_PERMS

    def as_user(**kw):
        app.dependency_overrides[get_current_user] = make_test_user(permissions=ENCOUNTER_PERMS, **kw)

    as_user()
    mine = await create_patient(client)
    await create_encounter(client, encounter_body(subject={"reference": f"Patient/{mine}"}))
    as_user(sub="u-other", org_id="org-other")
    try:
        # The other org cannot see the patient, so nothing reaches its encounters.
        bundle = await _other(other_client, "patients", _id=str(mine), _revinclude="Encounter:patient")
        assert bundle["total"] == 0 and "entry" not in bundle
        theirs = await create_patient(other_client)
        bundle = await _other(other_client, "patients", _id=str(theirs), _revinclude="Encounter:patient")
        assert _of_type(bundle, "Encounter", "include") == set()
    finally:
        as_user()


# ── combination rules / lenient vs strict ────────────────────────────────────


async def test_params_are_anded(client, world):
    assert await _keys(client, world, status="in-progress", **{"class": "AMB"}) == {"a"}
    assert await _keys(client, world, status="cancelled", **{"class": "AMB"}) == {"d"}
    assert await _keys(client, world, status="in-progress", **{"class": "IMP"}) == set()
    assert await _keys(client, world, patient=str(world["p1"]), length="gt1") == {"a"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, date="banana") == 400
    assert await _status(client, status="in-progress", **{"status:above": "x"}) == 400
    assert await _status(client, **{"class:of-type": "x"}) == 400


async def test_unknown_param_lenient_vs_strict(client, world):
    lenient = await client.get(BASE + "/", params={"nonsense": "1"})
    assert lenient.status_code == 200
    assert any(e["search"]["mode"] == "outcome" for e in lenient.json()["entry"])
    strict = await client.get(BASE + "/", params={"nonsense": "1"}, headers={"Prefer": "handling=strict"})
    assert strict.status_code == 400


async def test_query_param_refused(client, world):
    assert await _status(client, _query="x") == 400


# ── POST _search / Bundle shape ──────────────────────────────────────────────


async def test_post_search_form_encoded(client, world):
    resp = await client.post(BASE + "/_search", data={"status": "finished", "length": "gt1"})
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, status="finished")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/encounters/{world['b']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "Encounter"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
