"""FHIR R4 search over MedicationAdministration (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/medicationadministration.html#search).

One block per search parameter - `status` a code, `effective-time` a dateTime-or-Period,
`identifier`, `code`, `reason-given` and `reason-not-given` tokens, the single-target `medication`,
`request`, `device` and `context`, the multi-target `subject` and `performer`, `patient` (a subject
narrowed to Patients) - then chaining, `_include`/`_revinclude`, result parameters, combination
rules, lenient vs strict handling and POST _search.
"""

import pytest

from tests.integration.medication_administration.support import (
    ADMIN_IDS,
    API,
    BASE,
    RXNORM,
    SCT,
    STATUS_SYSTEM,
    V2_0203,
    concept,
    create_encounter,
    create_episode,
    create_group,
    create_medication,
    create_medication_administration,
    create_medication_request,
    create_organization,
    create_patient,
    create_practitioner,
    create_related_person,
    encounter_body,
    episode_body,
    group_body,
    medication_administration_body,
    medication_body,
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
    """Four administrations that differ on every searchable element.

    a - completed, RxNorm 197361, subject Patient p1, context Encounter, performer Practitioner,
        request MedicationRequest, device Device/12, effective 2026-02-03T08:30Z (a dateTime),
        reasonCode SCT 38341003, MA-A.
    b - not-done, a Medication reference, subject Group, context EpisodeOfCare, performers
        Patient p2 and RelatedPerson, effective period 2026-01-01..2026-03-01, statusReason
        SCT 182856006.
    c - stopped, RxNorm 123456, subject Patient p2, an open-ended period from 2025-01-01, a
        Device performer.
    d - on-hold, nothing else (an external subject).
    """
    p1 = await create_patient(client)
    p2 = await create_patient(client)
    related = await create_related_person(client, related_person_body(p1))
    group = await create_group(client, group_body(type="person"))
    encounter = await create_encounter(client, encounter_body())
    episode = await create_episode(client, episode_body(p1))
    practitioner = await create_practitioner(client)
    medication = await create_medication(client, medication_body(status="active"))
    request = await create_medication_request(client, medication_request_body(p1))
    await create_organization(client)

    a = await create_medication_administration(
        client,
        medication_administration_body(
            p1,
            status="completed",
            identifier=[
                {
                    "system": ADMIN_IDS,
                    "value": "MA-A",
                    "type": {
                        "coding": [
                            {"system": V2_0203, "code": "ADM", "display": "Admin id"}
                        ],
                        "text": "Administration number",
                    },
                }
            ],
            medicationCodeableConcept=concept(RXNORM, "197361", "Amlodipine 5 MG"),
            context={"reference": f"Encounter/{encounter}"},
            performer=[{"actor": {"reference": f"Practitioner/{practitioner}"}}],
            request={"reference": f"MedicationRequest/{request}"},
            device=[{"reference": "Device/12"}],
            reasonCode=[concept(SCT, "38341003", "Hypertension")],
        ),
    )
    b_body = {
        "status": "not-done",
        "medicationReference": {"reference": f"Medication/{medication}"},
        "subject": {"reference": f"Group/{group}"},
        "context": {"reference": f"EpisodeOfCare/{episode}"},
        "performer": [
            {"actor": {"reference": f"Patient/{p2}"}},
            {"actor": {"reference": f"RelatedPerson/{related}"}},
        ],
        "effectivePeriod": {"start": "2026-01-01", "end": "2026-03-01"},
        "statusReason": [concept(SCT, "182856006", "Drug not available")],
    }
    b = await create_medication_administration(client, b_body)
    c_body = medication_administration_body(
        p2,
        status="stopped",
        medicationCodeableConcept=concept(RXNORM, "123456", "Other drug"),
        performer=[{"actor": {"reference": "Device/77"}}],
    )
    del c_body["effectiveDateTime"]
    c_body["effectivePeriod"] = {"start": "2025-01-01"}
    c = await create_medication_administration(client, c_body)
    d = await create_medication_administration(
        client, medication_administration_body(status="on-hold")
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
        "medication": medication,
        "request": request,
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
    assert await _keys(client, world, status="completed,not-done") == {"a", "b"}
    assert await _keys(client, world, status="on-hold") == {"d"}
    assert await _keys(client, world, status=f"{STATUS_SYSTEM}|stopped") == {"c"}
    assert await _keys(client, world, status="http://wrong|completed") == set()
    assert await _keys(client, world, status="|completed") == set()
    assert await _keys(client, world, status="nonsense") == set()
    assert await _keys(client, world, **{"status:not": "completed"}) == {"b", "c", "d"}


# -- identifier -----------------------------------------------------------------------------


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="MA-A") == {"a"}
    assert await _keys(client, world, identifier=f"{ADMIN_IDS}|MA-A") == {"a"}
    assert await _keys(client, world, identifier=f"{ADMIN_IDS}|") == {"a"}
    assert await _keys(client, world, identifier="|MA-A") == set()
    assert await _keys(
        client, world, **{"identifier:text": "administration number"}
    ) == {"a"}
    assert await _keys(client, world, **{"identifier:text": "admin id"}) == {"a"}
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|ADM|MA-A"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|ADM|nope"})
        == set()
    )
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {
        "b",
        "c",
        "d",
    }


# -- code / reason-given / reason-not-given -------------------------------------------------


async def test_code_reads_the_medication_codeable_concept(client, world):
    assert await _keys(client, world, code=f"{RXNORM}|197361") == {"a"}
    assert await _keys(client, world, code="123456") == {"c"}
    assert await _keys(client, world, code=f"{RXNORM}|") == {"a", "c"}
    assert await _keys(client, world, **{"code:text": "amlodipine"}) == {"a"}
    # d has a text-only concept (still a value for `code`); b names its medication by reference
    assert await _keys(client, world, **{"code:text": "aspirin"}) == {"d"}
    assert await _keys(client, world, **{"code:missing": "true"}) == {"b"}


async def test_reason_given_reads_reason_code(client, world):
    assert await _keys(client, world, **{"reason-given": "38341003"}) == {"a"}
    assert await _keys(client, world, **{"reason-given": f"{SCT}|"}) == {"a"}
    assert await _keys(client, world, **{"reason-given:text": "hypertension"}) == {"a"}
    assert await _keys(client, world, **{"reason-given:missing": "true"}) == {
        "b",
        "c",
        "d",
    }


async def test_reason_not_given_reads_status_reason(client, world):
    assert await _keys(client, world, **{"reason-not-given": "182856006"}) == {"b"}
    assert await _keys(client, world, **{"reason-not-given:text": "drug not"}) == {"b"}
    assert await _keys(client, world, **{"reason-not-given:missing": "false"}) == {"b"}
    assert await _keys(client, world, **{"reason-not-given": "38341003"}) == set()


# -- effective-time -------------------------------------------------------------------------


async def test_effective_time_over_a_date_time_and_a_period(client, world):
    # a: 2026-02-03T08:30Z; b: [2026-01-01, 2026-03-02); c: [2025-01-01, open); d: dateTime
    assert await _keys(client, world, **{"effective-time": "2026-02-03"}) == {"a", "d"}
    assert await _keys(client, world, **{"effective-time": "ge2026-02-01"}) == {
        "a",
        "b",
        "c",
        "d",
    }
    assert await _keys(client, world, **{"effective-time": "gt2026-03-01"}) == {"c"}
    assert await _keys(client, world, **{"effective-time": "lt2025-06-01"}) == {"c"}
    assert await _keys(client, world, **{"effective-time": "eb2025-01-01"}) == set()
    assert await _keys(client, world, **{"effective-time": "sa2025-12-31"}) == {
        "a",
        "b",
        "d",
    }
    assert await _keys(client, world, **{"effective-time:missing": "true"}) == set()


# -- subject / patient ----------------------------------------------------------------------


async def test_subject_has_several_targets_so_a_bare_id_is_ambiguous(client, world):
    assert await _status(client, subject=str(world["p1"])) == 400
    assert await _keys(client, world, subject=f"Patient/{world['p1']}") == {"a"}
    assert await _keys(client, world, **{"subject:Patient": str(world["p1"])}) == {"a"}
    assert await _keys(client, world, subject=f"Group/{world['group']}") == {"b"}
    assert await _keys(client, world, **{"subject:Group": str(world["group"])}) == {"b"}
    assert await _status(client, **{"subject:Device": "1"}) == 400


async def test_patient_is_the_subject_narrowed_to_patients(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {"a"}
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"c"}
    # a Group (b) or an absolute-URL subject (d) counts as missing it
    assert await _keys(client, world, **{"patient:missing": "true"}) == {"b", "d"}
    assert await _keys(client, world, **{"patient:missing": "false"}) == {"a", "c"}


# -- context / medication / request / device ------------------------------------------------


async def test_context_has_two_targets(client, world):
    assert await _status(client, context=str(world["encounter"])) == 400
    assert await _keys(client, world, context=f"Encounter/{world['encounter']}") == {
        "a"
    }
    assert await _keys(client, world, context=f"EpisodeOfCare/{world['episode']}") == {
        "b"
    }
    assert await _keys(
        client, world, **{"context:Encounter": str(world["encounter"])}
    ) == {"a"}
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


async def test_request_has_one_target_so_a_bare_id_works(client, world):
    assert await _keys(client, world, request=str(world["request"])) == {"a"}
    assert await _keys(
        client, world, request=f"MedicationRequest/{world['request']}"
    ) == {"a"}
    assert await _keys(client, world, **{"request:missing": "true"}) == {"b", "c", "d"}


async def test_device_has_one_target_so_a_bare_id_works(client, world):
    assert await _keys(client, world, device="12") == {"a"}
    assert await _keys(client, world, device="Device/12") == {"a"}
    assert await _keys(client, world, **{"device:missing": "true"}) == {"b", "c", "d"}


# -- performer ------------------------------------------------------------------------------


async def test_performer_has_several_targets(client, world):
    assert await _status(client, performer=str(world["practitioner"])) == 400
    assert await _keys(
        client, world, performer=f"Practitioner/{world['practitioner']}"
    ) == {"a"}
    assert await _keys(client, world, performer=f"Patient/{world['p2']}") == {"b"}
    assert await _keys(
        client, world, **{"performer:RelatedPerson": str(world["related"])}
    ) == {"b"}
    assert await _keys(client, world, performer="Device/77") == {"c"}
    assert await _keys(client, world, **{"performer:missing": "true"}) == {"d"}


# -- chaining -------------------------------------------------------------------------------


async def test_chain_through_each_resource_target(client, world):
    assert await _keys(client, world, **{"patient.active": "true"}) == {"a", "c"}
    assert await _keys(client, world, **{"subject:Patient.active": "true"}) == {
        "a",
        "c",
    }
    assert await _keys(client, world, **{"subject:Group.type": "person"}) == {"b"}
    assert await _keys(client, world, **{"context:EpisodeOfCare.status": "active"}) == {
        "b"
    }
    assert await _keys(client, world, **{"medication.status": "active"}) == {"b"}
    assert await _keys(client, world, **{"request.status": "active"}) == {"a"}
    assert await _keys(client, world, **{"performer:Patient.active": "true"}) == {"b"}


async def test_bad_chains_are_400(client, world):
    assert (
        await _status(client, **{"subject.active": "x"}) == 400
    )  # untyped multi-target
    assert await _status(client, **{"performer.active": "x"}) == 400
    assert (
        await _status(client, **{"status.x": "y"}) == 400
    )  # a token cannot be chained
    assert await _status(client, **{"effective-time.x": "y"}) == 400
    assert await _status(client, **{"subject:Device.x": "y"}) == 400


# -- _sort / _count / _offset / _total ------------------------------------------------------


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "_id",
        "_lastUpdated",
        "code",
        "context",
        "device",
        "effective-time",
        "identifier",
        "medication",
        "patient",
        "performer",
        "reason-given",
        "reason-not-given",
        "request",
        "status",
        "subject",
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
    # R4 keeps the mandatory elements (status, medication[x], subject, effective[x]), drops the rest
    assert "performer" not in resource and "reasonCode" not in resource


# -- _include / _revinclude -----------------------------------------------------------------


async def test_include_every_reference(client, world):
    ids = ",".join(str(world[k]) for k in KEYS)
    bundle = await _search(client, _id=ids, _include="MedicationAdministration:patient")
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }
    bundle = await _search(client, _id=ids, _include="MedicationAdministration:subject")
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }
    assert _of_type(bundle, "Group", "include") == {str(world["group"])}
    bundle = await _search(client, _id=ids, _include="MedicationAdministration:context")
    assert _of_type(bundle, "Encounter", "include") == {str(world["encounter"])}
    assert _of_type(bundle, "EpisodeOfCare", "include") == {str(world["episode"])}
    bundle = await _search(
        client, _id=ids, _include="MedicationAdministration:medication"
    )
    assert _of_type(bundle, "Medication", "include") == {str(world["medication"])}
    bundle = await _search(client, _id=ids, _include="MedicationAdministration:request")
    assert _of_type(bundle, "MedicationRequest", "include") == {str(world["request"])}
    bundle = await _search(
        client, _id=ids, _include="MedicationAdministration:performer"
    )
    assert _of_type(bundle, "Practitioner", "include") == {str(world["practitioner"])}
    assert _of_type(bundle, "RelatedPerson", "include") == {str(world["related"])}
    assert _of_type(bundle, "Patient", "include") == {str(world["p2"])}


async def test_revinclude_from_the_resources_an_administration_points_at(client, world):
    async def rev(path: str, ids, param: str) -> dict:
        resp = await client.get(
            f"{API}/{path}/",
            params={
                "_id": ",".join(str(i) for i in ids),
                "_revinclude": f"MedicationAdministration:{param}",
            },
        )
        assert resp.status_code == 200, resp.text
        return resp.json()

    def included(bundle):
        return _of_type(bundle, "MedicationAdministration", "include")

    assert included(await rev("patients", [world["p1"], world["p2"]], "patient")) == {
        str(world["a"]),
        str(world["c"]),
    }
    assert included(await rev("patients", [world["p1"], world["p2"]], "subject")) == {
        str(world["a"]),
        str(world["c"]),
    }
    assert included(await rev("patients", [world["p2"]], "performer")) == {
        str(world["b"])
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
    assert included(await rev("related-persons", [world["related"]], "performer")) == {
        str(world["b"])
    }
    assert included(await rev("medications", [world["medication"]], "medication")) == {
        str(world["b"])
    }
    assert included(
        await rev("medication-requests", [world["request"]], "request")
    ) == {str(world["a"])}


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
    assert await _status(client, **{"effective-time": "notadate"}) == 400
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
        "dosage",
        "note",
        "category",
        "part-of",
        "supporting-information",
        "effective",
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
        BASE + "/_search", data={"status": "not-done", "reason-not-given": "182856006"}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, identifier="MA-A")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/medication-administrations/{world['a']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "MedicationAdministration"
    assert entry["resource"]["status"] == "completed"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
