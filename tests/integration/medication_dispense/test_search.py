"""FHIR R4 search over MedicationDispense (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/medicationdispense.html#search).

One block per search parameter - `status` a code, `whenprepared` / `whenhandedover` dateTimes,
`identifier`, `code` and `type` tokens, the single-target `medication`, `destination` and
`prescription`, the multi-target `subject`, `context`, `performer`, `receiver` and
`responsibleparty`, `patient` (a subject narrowed to Patients) - then chaining,
`_include`/`_revinclude`, result parameters, combination rules, lenient vs strict handling and
POST _search.
"""

import pytest

from tests.integration.medication_dispense.support import (
    ACT_CODE,
    API,
    BASE,
    DISPENSE_IDS,
    RXNORM,
    STATUS_SYSTEM,
    V2_0203,
    concept,
    create_encounter,
    create_episode,
    create_group,
    create_location,
    create_medication,
    create_medication_dispense,
    create_medication_request,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_related_person,
    encounter_body,
    episode_body,
    group_body,
    medication_body,
    medication_dispense_body,
    medication_request_body,
    related_person_body,
)

KEYS = ("a", "b", "c", "d")
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
async def world(client) -> dict:
    """Four dispenses that differ on every searchable element.

    a - completed, RxNorm 197361, subject Patient p1, context Encounter, performer Practitioner,
        prescription MedicationRequest, destination Location, receiver Patient p1 and
        Practitioner, type FF, prepared 2026-02-03T08:30Z, handed over 2026-02-03T09:30Z, MD-A.
    b - cancelled, a Medication reference, subject Group, context EpisodeOfCare, performers
        Organization and RelatedPerson, a responsible party (a PractitionerRole), prepared
        2026-01-10.
    c - stopped, RxNorm 123456, subject Patient p2, a Device performer, prepared 2025-06-01.
    d - on-hold, nothing else (an external subject).
    """
    p1 = await create_patient(client)
    p2 = await create_patient(client)
    related = await create_related_person(client, related_person_body(p1))
    group = await create_group(client, group_body(type="person"))
    encounter = await create_encounter(client, encounter_body())
    episode = await create_episode(client, episode_body(p1))
    practitioner = await create_practitioner(client)
    organization = await create_organization(client)
    role = await create_practitioner_role(
        client, {"practitioner": {"reference": f"Practitioner/{practitioner}"}}
    )
    medication = await create_medication(client, medication_body(status="active"))
    request = await create_medication_request(client, medication_request_body(p1))
    location = await create_location(client)

    a = await create_medication_dispense(
        client,
        medication_dispense_body(
            p1,
            status="completed",
            identifier=[
                {
                    "system": DISPENSE_IDS,
                    "value": "MD-A",
                    "type": {
                        "coding": [
                            {"system": V2_0203, "code": "DSP", "display": "Dispense id"}
                        ],
                        "text": "Dispense number",
                    },
                }
            ],
            medicationCodeableConcept=concept(RXNORM, "197361", "Amlodipine 5 MG"),
            context={"reference": f"Encounter/{encounter}"},
            performer=[{"actor": {"reference": f"Practitioner/{practitioner}"}}],
            authorizingPrescription=[{"reference": f"MedicationRequest/{request}"}],
            destination={"reference": f"Location/{location}"},
            receiver=[
                {"reference": f"Patient/{p1}"},
                {"reference": f"Practitioner/{practitioner}"},
            ],
            type=concept(ACT_CODE, "FF", "First Fill"),
            whenPrepared="2026-02-03T08:30:00Z",
            whenHandedOver="2026-02-03T09:30:00Z",
        ),
    )
    b = await create_medication_dispense(
        client,
        {
            "status": "cancelled",
            "medicationReference": {"reference": f"Medication/{medication}"},
            "subject": {"reference": f"Group/{group}"},
            "context": {"reference": f"EpisodeOfCare/{episode}"},
            "performer": [
                {"actor": {"reference": f"Organization/{organization}"}},
                {"actor": {"reference": f"RelatedPerson/{related}"}},
            ],
            "substitution": {
                "wasSubstituted": True,
                "responsibleParty": [{"reference": f"PractitionerRole/{role}"}],
            },
            "whenPrepared": "2026-01-10",
        },
    )
    c = await create_medication_dispense(
        client,
        medication_dispense_body(
            p2,
            status="stopped",
            medicationCodeableConcept=concept(RXNORM, "123456", "Other drug"),
            performer=[{"actor": {"reference": "Device/77"}}],
            whenPrepared="2025-06-01T12:00:00Z",
        ),
    )
    d = await create_medication_dispense(
        client, medication_dispense_body(status="on-hold")
    )
    return {
        "a": a,
        "b": b,
        "c": c,
        "d": d,
        "p1": p1,
        "p2": p2,
        "related": related,
        "group": group,
        "encounter": encounter,
        "episode": episode,
        "practitioner": practitioner,
        "organization": organization,
        "role": role,
        "medication": medication,
        "request": request,
        "location": location,
    }


async def _search(client, **params) -> dict:
    resp = await client.get(BASE + "/", params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _keys(client, world, **params) -> set[str]:
    by_id = {world[k]: k for k in KEYS}
    return {by_id[i] for i in _ids(await _search(client, **params))}


async def _status(client, **params) -> int:
    return (await client.get(BASE + "/", params=params)).status_code


# -- _id / _lastUpdated ---------------------------------------------------------------------


async def test_id(client, world):
    assert await _keys(client, world, _id=str(world["a"])) == {"a"}
    assert await _keys(client, world, _id=f"{world['a']},{world['d']}") == {"a", "d"}
    assert await _keys(client, world, _id="999999") == set()
    assert await _keys(client, world, **{"_id:not": str(world["a"])}) == {"b", "c", "d"}


async def test_last_updated(client, world):
    assert await _keys(client, world, _lastUpdated="ge2000-01-01") == ALL
    assert await _keys(client, world, _lastUpdated="lt2000-01-01") == set()


# -- status ---------------------------------------------------------------------------------


async def test_status(client, world):
    assert await _keys(client, world, status="completed") == {"a"}
    assert await _keys(client, world, status="completed,cancelled") == {"a", "b"}
    assert await _keys(client, world, status="on-hold") == {"d"}
    assert await _keys(client, world, status=f"{STATUS_SYSTEM}|stopped") == {"c"}
    assert await _keys(client, world, status="http://wrong|completed") == set()
    assert await _keys(client, world, status="|completed") == set()
    assert await _keys(client, world, status="nonsense") == set()
    assert await _keys(client, world, **{"status:not": "completed"}) == {"b", "c", "d"}


# -- identifier / code / type ---------------------------------------------------------------


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="MD-A") == {"a"}
    assert await _keys(client, world, identifier=f"{DISPENSE_IDS}|MD-A") == {"a"}
    assert await _keys(client, world, identifier=f"{DISPENSE_IDS}|") == {"a"}
    assert await _keys(client, world, identifier="|MD-A") == set()
    assert await _keys(client, world, **{"identifier:text": "dispense number"}) == {"a"}
    assert await _keys(client, world, **{"identifier:text": "dispense id"}) == {"a"}
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|DSP|MD-A"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|DSP|nope"})
        == set()
    )
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {
        "b",
        "c",
        "d",
    }


async def test_code_reads_the_medication_codeable_concept(client, world):
    assert await _keys(client, world, code=f"{RXNORM}|197361") == {"a"}
    assert await _keys(client, world, code="123456") == {"c"}
    assert await _keys(client, world, code=f"{RXNORM}|") == {"a", "c"}
    assert await _keys(client, world, **{"code:text": "amlodipine"}) == {"a"}
    # d has a text-only concept (still a value for `code`); b names its medication by reference
    assert await _keys(client, world, **{"code:text": "aspirin"}) == {"d"}
    assert await _keys(client, world, **{"code:missing": "true"}) == {"b"}


async def test_type(client, world):
    assert await _keys(client, world, type="FF") == {"a"}
    assert await _keys(client, world, type=f"{ACT_CODE}|FF") == {"a"}
    assert await _keys(client, world, **{"type:text": "first"}) == {"a"}
    assert await _keys(client, world, type="http://wrong|FF") == set()
    assert await _keys(client, world, **{"type:missing": "true"}) == {"b", "c", "d"}


# -- whenprepared / whenhandedover ----------------------------------------------------------


async def test_whenprepared_ranges_and_partial_precision(client, world):
    # a: 2026-02-03T08:30Z; b: 2026-01-10 (a day); c: 2025-06-01T12:00Z; d: none
    assert await _keys(client, world, whenprepared="2026") == {"a", "b"}
    assert await _keys(client, world, whenprepared="2026-01") == {"b"}
    assert await _keys(client, world, whenprepared="2026-02-03") == {"a"}
    assert await _keys(client, world, whenprepared="ge2026-01-01") == {"a", "b"}
    assert await _keys(client, world, whenprepared="lt2026-01-01") == {"c"}
    assert await _keys(client, world, whenprepared="gt2026-01-10") == {"a"}
    assert await _keys(client, world, **{"whenprepared:missing": "true"}) == {"d"}


async def test_whenhandedover(client, world):
    assert await _keys(client, world, whenhandedover="2026-02-03") == {"a"}
    assert await _keys(client, world, whenhandedover="ge2026-02-03T09:00:00Z") == {"a"}
    assert await _keys(client, world, whenhandedover="lt2026-02-03T09:00:00Z") == set()
    assert await _keys(client, world, **{"whenhandedover:missing": "true"}) == {
        "b",
        "c",
        "d",
    }


# -- subject / patient ----------------------------------------------------------------------


async def test_subject_has_several_targets_so_a_bare_id_is_ambiguous(client, world):
    assert await _status(client, subject=str(world["p1"])) == 400
    assert await _keys(client, world, subject=f"Patient/{world['p1']}") == {"a"}
    assert await _keys(client, world, **{"subject:Patient": str(world["p1"])}) == {"a"}
    assert await _keys(client, world, subject=f"Group/{world['group']}") == {"b"}
    assert await _status(client, **{"subject:Device": "1"}) == 400


async def test_patient_is_the_subject_narrowed_to_patients(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {"a"}
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"c"}
    # a Group (b) or an absolute-URL subject (d) counts as missing it
    assert await _keys(client, world, **{"patient:missing": "true"}) == {"b", "d"}
    assert await _keys(client, world, **{"patient:missing": "false"}) == {"a", "c"}


# -- context / medication / destination / prescription --------------------------------------


async def test_context_has_two_targets(client, world):
    assert await _status(client, context=str(world["encounter"])) == 400
    assert await _keys(client, world, context=f"Encounter/{world['encounter']}") == {
        "a"
    }
    assert await _keys(client, world, context=f"EpisodeOfCare/{world['episode']}") == {
        "b"
    }
    assert await _keys(client, world, **{"context:missing": "true"}) == {"c", "d"}


async def test_medication_has_one_target_so_a_bare_id_works(client, world):
    assert await _keys(client, world, medication=str(world["medication"])) == {"b"}
    assert await _keys(
        client, world, medication=f"Medication/{world['medication']}"
    ) == {"b"}
    assert await _keys(client, world, **{"medication:missing": "true"}) == {
        "a",
        "c",
        "d",
    }


async def test_destination_has_one_target_so_a_bare_id_works(client, world):
    assert await _keys(client, world, destination=str(world["location"])) == {"a"}
    assert await _keys(client, world, destination=f"Location/{world['location']}") == {
        "a"
    }
    assert await _keys(client, world, **{"destination:missing": "true"}) == {
        "b",
        "c",
        "d",
    }


async def test_prescription_has_one_target_so_a_bare_id_works(client, world):
    assert await _keys(client, world, prescription=str(world["request"])) == {"a"}
    assert await _keys(
        client, world, prescription=f"MedicationRequest/{world['request']}"
    ) == {"a"}
    assert await _keys(client, world, **{"prescription:missing": "true"}) == {
        "b",
        "c",
        "d",
    }


# -- performer / receiver / responsibleparty ------------------------------------------------


async def test_performer_has_several_targets(client, world):
    assert await _status(client, performer=str(world["practitioner"])) == 400
    assert await _keys(
        client, world, performer=f"Practitioner/{world['practitioner']}"
    ) == {"a"}
    assert await _keys(
        client, world, performer=f"Organization/{world['organization']}"
    ) == {"b"}
    assert await _keys(
        client, world, **{"performer:RelatedPerson": str(world["related"])}
    ) == {"b"}
    assert await _keys(client, world, performer="Device/77") == {"c"}
    assert await _keys(client, world, **{"performer:missing": "true"}) == {"d"}


async def test_receiver_has_two_targets(client, world):
    assert await _status(client, receiver=str(world["p1"])) == 400
    assert await _keys(client, world, receiver=f"Patient/{world['p1']}") == {"a"}
    assert await _keys(
        client, world, **{"receiver:Practitioner": str(world["practitioner"])}
    ) == {"a"}
    assert await _keys(client, world, **{"receiver:missing": "true"}) == {"b", "c", "d"}


async def test_responsibleparty_reads_substitution(client, world):
    assert await _status(client, responsibleparty=str(world["role"])) == 400
    assert await _keys(
        client, world, responsibleparty=f"PractitionerRole/{world['role']}"
    ) == {"b"}
    assert await _keys(
        client, world, **{"responsibleparty:PractitionerRole": str(world["role"])}
    ) == {"b"}
    assert await _keys(client, world, **{"responsibleparty:missing": "true"}) == {
        "a",
        "c",
        "d",
    }


# -- chaining -------------------------------------------------------------------------------


async def test_chain_through_each_resource_target(client, world):
    assert await _keys(client, world, **{"patient.active": "true"}) == {"a", "c"}
    assert await _keys(client, world, **{"subject:Group.type": "person"}) == {"b"}
    assert await _keys(client, world, **{"context:EpisodeOfCare.status": "active"}) == {
        "b"
    }
    assert await _keys(client, world, **{"medication.status": "active"}) == {"b"}
    assert await _keys(client, world, **{"prescription.status": "active"}) == {"a"}
    assert await _keys(client, world, **{"destination.status": "active"}) <= {"a"}
    assert await _keys(client, world, **{"performer:Organization.active": "true"}) == {
        "b"
    }
    assert await _keys(client, world, **{"receiver:Patient.active": "true"}) == {"a"}


async def test_bad_chains_are_400(client, world):
    assert (
        await _status(client, **{"subject.active": "x"}) == 400
    )  # untyped multi-target
    assert await _status(client, **{"performer.active": "x"}) == 400
    assert (
        await _status(client, **{"status.x": "y"}) == 400
    )  # a token cannot be chained
    assert await _status(client, **{"whenprepared.x": "y"}) == 400
    assert (
        await _status(client, **{"performer:Device.x": "y"}) == 400
    )  # Device is not a resource here


# -- _sort / _count / _offset / _total ------------------------------------------------------


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "_id",
        "_lastUpdated",
        "code",
        "context",
        "destination",
        "identifier",
        "medication",
        "patient",
        "performer",
        "prescription",
        "receiver",
        "responsibleparty",
        "status",
        "subject",
        "type",
        "whenhandedover",
        "whenprepared",
    ):
        assert (await _search(client, _sort=key))["total"] == 4, key
        assert (await _search(client, _sort=f"-{key}"))["total"] == 4, key


async def test_default_sort_is_newest_first(client, world):
    got = [int(e["resource"]["id"]) for e in (await _search(client))["entry"]]
    assert got == sorted(got, reverse=True)


async def test_paging_and_total(client, world):
    page = await _search(client, _count=2, _sort="_id")
    assert page["total"] == 4 and len(page["entry"]) == 2
    assert any(link["relation"] == "next" for link in page["link"])
    nxt = await _search(client, _count=2, _offset=2, _sort="_id")
    assert not (
        {e["resource"]["id"] for e in page["entry"]}
        & {e["resource"]["id"] for e in nxt["entry"]}
    )
    assert "entry" not in await _search(client, _count=0)
    assert "total" not in await _search(client, _total="none")


async def test_summary_count_and_elements(client, world):
    assert (await _search(client, _summary="count"))["total"] == 4
    resource = (await _search(client, _elements="status", _id=str(world["a"])))[
        "entry"
    ][0]["resource"]
    assert resource["status"] == "completed"
    # R4 keeps the mandatory elements (status, medication[x]), drops the rest
    assert "performer" not in resource and "whenPrepared" not in resource


# -- _include / _revinclude -----------------------------------------------------------------


async def test_include_every_reference(client, world):
    ids = ",".join(str(world[k]) for k in KEYS)

    async def inc(param: str) -> dict:
        return await _search(client, _id=ids, _include=f"MedicationDispense:{param}")

    bundle = await inc("patient")
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }
    bundle = await inc("subject")
    assert _of_type(bundle, "Group", "include") == {str(world["group"])}
    bundle = await inc("context")
    assert _of_type(bundle, "Encounter", "include") == {str(world["encounter"])}
    assert _of_type(bundle, "EpisodeOfCare", "include") == {str(world["episode"])}
    bundle = await inc("medication")
    assert _of_type(bundle, "Medication", "include") == {str(world["medication"])}
    bundle = await inc("destination")
    assert _of_type(bundle, "Location", "include") == {str(world["location"])}
    bundle = await inc("prescription")
    assert _of_type(bundle, "MedicationRequest", "include") == {str(world["request"])}
    bundle = await inc("performer")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["practitioner"])}
    assert _of_type(bundle, "Organization", "include") == {str(world["organization"])}
    assert _of_type(bundle, "RelatedPerson", "include") == {str(world["related"])}
    bundle = await inc("receiver")
    assert _of_type(bundle, "Patient", "include") == {str(world["p1"])}
    bundle = await inc("responsibleparty")
    assert _of_type(bundle, "PractitionerRole", "include") == {str(world["role"])}


async def test_revinclude_from_the_resources_a_dispense_points_at(client, world):
    async def rev(path: str, ids, param: str) -> dict:
        resp = await client.get(
            f"{API}/{path}/",
            params={
                "_id": ",".join(str(i) for i in ids),
                "_revinclude": f"MedicationDispense:{param}",
            },
        )
        assert resp.status_code == 200, resp.text
        return resp.json()

    def included(bundle):
        return _of_type(bundle, "MedicationDispense", "include")

    both = {str(world["a"]), str(world["c"])}
    assert (
        included(await rev("patients", [world["p1"], world["p2"]], "patient")) == both
    )
    assert included(await rev("patients", [world["p1"]], "receiver")) == {
        str(world["a"])
    }
    assert included(await rev("groups", [world["group"]], "subject")) == {
        str(world["b"])
    }
    assert included(await rev("encounters", [world["encounter"]], "context")) == {
        str(world["a"])
    }
    assert included(await rev("episodes-of-care", [world["episode"]], "context")) == {
        str(world["b"])
    }
    assert included(
        await rev("practitioners", [world["practitioner"]], "performer")
    ) == {str(world["a"])}
    assert included(
        await rev("practitioners", [world["practitioner"]], "receiver")
    ) == {str(world["a"])}
    assert included(
        await rev("practitioner-roles", [world["role"]], "responsibleparty")
    ) == {str(world["b"])}
    assert included(
        await rev("organizations", [world["organization"]], "performer")
    ) == {str(world["b"])}
    assert included(await rev("related-persons", [world["related"]], "performer")) == {
        str(world["b"])
    }
    assert included(await rev("medications", [world["medication"]], "medication")) == {
        str(world["b"])
    }
    assert included(
        await rev("medication-requests", [world["request"]], "prescription")
    ) == {str(world["a"])}
    assert included(await rev("locations", [world["location"]], "destination")) == {
        str(world["a"])
    }


# -- combination, errors --------------------------------------------------------------------


async def test_and_or_combination(client, world):
    assert await _keys(client, world, status="completed", patient=str(world["p1"])) == {
        "a"
    }
    assert (
        await _keys(client, world, status="completed", patient=str(world["p2"]))
        == set()
    )
    assert await _keys(client, world, status="completed,stopped") == {"a", "c"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, whenprepared="notadate") == 400
    assert await _status(client, **{"status:text": "x"}) == 400
    assert await _status(client, **{"identifier:below": "x"}) == 400
    assert await _status(client, **{"medication:Patient": "1"}) == 400


async def test_unknown_param_lenient_vs_strict(client, world):
    lenient = await client.get(BASE + "/", params={"nonsense": "1"})
    assert lenient.status_code == 200
    assert any(e["search"]["mode"] == "outcome" for e in lenient.json()["entry"])
    strict = await client.get(
        BASE + "/", params={"nonsense": "1"}, headers={"Prefer": "handling=strict"}
    )
    assert strict.status_code == 400


async def test_unindexed_elements_have_no_search_parameter(client, world):
    for name in (
        "dosageinstruction",
        "note",
        "category",
        "part-of",
        "quantity",
        "location",
    ):
        strict = await client.get(
            BASE + "/", params={name: "x"}, headers={"Prefer": "handling=strict"}
        )
        assert strict.status_code == 400, name


async def test_query_param_refused(client, world):
    assert await _status(client, _query="x") == 400


# -- POST _search / Bundle shape ------------------------------------------------------------


async def test_post_search_form_encoded(client, world):
    resp = await client.post(
        BASE + "/_search",
        data={"status": "cancelled", "context:EpisodeOfCare": str(world["episode"])},
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, identifier="MD-A")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/medication-dispenses/{world['a']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "MedicationDispense"
    assert entry["resource"]["status"] == "completed"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
