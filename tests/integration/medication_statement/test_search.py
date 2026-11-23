"""FHIR R4 search over MedicationStatement (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/medicationstatement.html#search).

One block per search parameter - `status` a code, `effective` a dateTime-or-Period, `identifier`,
`category` and `code` tokens, the single-target `medication` and `context`/`source`/`subject`/
`part-of` with several targets, `patient` (a subject narrowed to Patients) - then chaining,
`_include`/`_revinclude`, result parameters, combination rules, lenient vs strict handling and
POST _search.
"""

import pytest

from tests.integration.medication_statement.support import (
    API,
    BASE,
    CATEGORY,
    RXNORM,
    STATEMENT_IDS,
    STATUS_SYSTEM,
    V2_0203,
    concept,
    create_encounter,
    create_episode,
    create_group,
    create_medication,
    create_medication_statement,
    create_observation,
    create_organization,
    create_patient,
    create_practitioner,
    create_procedure,
    encounter_body,
    episode_body,
    group_body,
    medication_body,
    medication_statement_body,
    observation_body,
    procedure_body,
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
    """Four statements that differ on every searchable element.

    a - active, community, RxNorm 197361, subject Patient p1, context Encounter, source
        Practitioner, partOf Observation, effective 2026-02-03T08:30Z (a dateTime), MS-A.
    b - completed, inpatient, a Medication reference, subject Group, context EpisodeOfCare,
        source Organization, partOf Procedure and MedicationStatement a, effective period
        2026-01-01..2026-03-01.
    c - stopped, RxNorm 123456, subject Patient p2, source Patient p2, an open-ended period from
        2025-01-01.
    d - not-taken, nothing else (an external subject).
    """
    p1 = await create_patient(client)
    p2 = await create_patient(client)
    group = await create_group(client, group_body(type="person"))
    encounter = await create_encounter(client, encounter_body())
    episode = await create_episode(client, episode_body(p1))
    practitioner = await create_practitioner(client)
    organization = await create_organization(client)
    medication = await create_medication(client, medication_body(status="active"))
    observation = await create_observation(client, observation_body(p1))
    procedure = await create_procedure(client, procedure_body(p1))

    a = await create_medication_statement(
        client,
        medication_statement_body(
            p1,
            status="active",
            identifier=[
                {
                    "system": STATEMENT_IDS,
                    "value": "MS-A",
                    "type": {
                        "coding": [
                            {"system": V2_0203, "code": "RXN", "display": "Rx number"}
                        ],
                        "text": "Prescription number",
                    },
                }
            ],
            category=concept(CATEGORY, "community"),
            medicationCodeableConcept=concept(RXNORM, "197361", "Amlodipine 5 MG"),
            context={"reference": f"Encounter/{encounter}"},
            informationSource={"reference": f"Practitioner/{practitioner}"},
            partOf=[{"reference": f"Observation/{observation}"}],
            effectiveDateTime="2026-02-03T08:30:00Z",
        ),
    )
    b = await create_medication_statement(
        client,
        {
            "status": "completed",
            "category": concept(CATEGORY, "inpatient"),
            "medicationReference": {"reference": f"Medication/{medication}"},
            "subject": {"reference": f"Group/{group}"},
            "context": {"reference": f"EpisodeOfCare/{episode}"},
            "informationSource": {"reference": f"Organization/{organization}"},
            "partOf": [
                {"reference": f"Procedure/{procedure}"},
                {"reference": f"MedicationStatement/{a}"},
            ],
            "effectivePeriod": {"start": "2026-01-01", "end": "2026-03-01"},
        },
    )
    c = await create_medication_statement(
        client,
        medication_statement_body(
            p2,
            status="stopped",
            medicationCodeableConcept=concept(RXNORM, "123456", "Other drug"),
            informationSource={"reference": f"Patient/{p2}"},
            effectivePeriod={"start": "2025-01-01"},
        ),
    )
    d = await create_medication_statement(
        client, medication_statement_body(status="not-taken")
    )
    return {
        "a": a,
        "b": b,
        "c": c,
        "d": d,
        "p1": p1,
        "p2": p2,
        "group": group,
        "encounter": encounter,
        "episode": episode,
        "practitioner": practitioner,
        "organization": organization,
        "medication": medication,
        "observation": observation,
        "procedure": procedure,
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
    assert await _keys(client, world, status="active") == {"a"}
    assert await _keys(client, world, status="active,completed") == {"a", "b"}
    assert await _keys(client, world, status="not-taken") == {"d"}
    assert await _keys(client, world, status=f"{STATUS_SYSTEM}|stopped") == {"c"}
    assert await _keys(client, world, status="http://wrong|active") == set()
    assert await _keys(client, world, status="|active") == set()
    assert await _keys(client, world, status="nonsense") == set()
    assert await _keys(client, world, **{"status:not": "active"}) == {"b", "c", "d"}


# -- identifier -----------------------------------------------------------------------------


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="MS-A") == {"a"}
    assert await _keys(client, world, identifier=f"{STATEMENT_IDS}|MS-A") == {"a"}
    assert await _keys(client, world, identifier=f"{STATEMENT_IDS}|") == {"a"}
    assert await _keys(client, world, identifier="|MS-A") == set()
    assert await _keys(client, world, **{"identifier:text": "prescription"}) == {"a"}
    assert await _keys(client, world, **{"identifier:text": "rx number"}) == {"a"}
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|RXN|MS-A"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|RXN|nope"})
        == set()
    )
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {
        "b",
        "c",
        "d",
    }


# -- category / code ------------------------------------------------------------------------


async def test_category(client, world):
    assert await _keys(client, world, category="community") == {"a"}
    assert await _keys(client, world, category=f"{CATEGORY}|inpatient") == {"b"}
    assert await _keys(client, world, category=f"{CATEGORY}|") == {"a", "b"}
    assert await _keys(client, world, category="community,inpatient") == {"a", "b"}
    assert await _keys(client, world, **{"category:missing": "true"}) == {"c", "d"}


async def test_code_reads_the_medication_codeable_concept(client, world):
    assert await _keys(client, world, code=f"{RXNORM}|197361") == {"a"}
    assert await _keys(client, world, code="123456") == {"c"}
    assert await _keys(client, world, code=f"{RXNORM}|") == {"a", "c"}
    assert await _keys(client, world, **{"code:text": "amlodipine"}) == {
        "a"
    }  # the display
    # d has a text-only concept (still a value for `code`); b names its medication by reference
    assert await _keys(client, world, **{"code:text": "aspirin"}) == {"d"}
    assert await _keys(client, world, **{"code:missing": "true"}) == {"b"}


# -- effective ------------------------------------------------------------------------------


async def test_effective_over_a_date_time_and_a_period(client, world):
    # a: 2026-02-03T08:30Z; b: [2026-01-01, 2026-03-01); c: [2025-01-01, open); d: none
    assert await _keys(client, world, effective="2026-02-03") == {"a"}
    assert await _keys(client, world, effective="ge2026-02-01") == {"a", "b", "c"}
    assert await _keys(client, world, effective="gt2026-03-01") == {
        "c"
    }  # only c has no end
    assert await _keys(client, world, effective="lt2025-06-01") == {"c"}
    assert await _keys(client, world, effective="eb2025-01-01") == set()
    assert await _keys(client, world, effective="sa2025-12-31") == {"a", "b"}
    assert await _keys(client, world, **{"effective:missing": "true"}) == {"d"}
    assert await _keys(client, world, **{"effective:missing": "false"}) == {
        "a",
        "b",
        "c",
    }


# -- subject / patient ----------------------------------------------------------------------


async def test_subject_has_several_targets_so_a_bare_id_is_ambiguous(client, world):
    assert await _status(client, subject=str(world["p1"])) == 400
    assert await _keys(client, world, subject=f"Patient/{world['p1']}") == {"a"}
    assert await _keys(client, world, **{"subject:Patient": str(world["p1"])}) == {"a"}
    assert await _keys(client, world, subject=f"Group/{world['group']}") == {"b"}
    assert await _keys(client, world, **{"subject:Group": str(world["group"])}) == {"b"}
    assert await _keys(
        client, world, subject=f"Patient/{world['p1']},Group/{world['group']}"
    ) == {
        "a",
        "b",
    }
    assert await _status(client, **{"subject:Device": "1"}) == 400


async def test_patient_is_the_subject_narrowed_to_patients(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {"a"}
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"c"}
    # a Group (b) or an absolute-URL / logical subject (d) counts as missing it
    assert await _keys(client, world, **{"patient:missing": "true"}) == {"b", "d"}
    assert await _keys(client, world, **{"patient:missing": "false"}) == {"a", "c"}


async def test_subject_identifier_modifier_and_missing(client, world):
    await create_medication_statement(
        client,
        medication_statement_body(
            subject={"identifier": {"system": "urn:mrn", "value": "M-9"}}
        ),
    )
    assert (
        len(_ids(await _search(client, **{"subject:identifier": "urn:mrn|M-9"}))) == 1
    )
    assert await _keys(client, world, **{"subject:missing": "true"}) == set()


# -- context / source / medication ----------------------------------------------------------


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
    assert await _keys(
        client, world, **{"context:EpisodeOfCare": str(world["episode"])}
    ) == {"b"}
    assert await _keys(client, world, **{"context:missing": "true"}) == {"c", "d"}


async def test_source_has_several_targets(client, world):
    assert await _status(client, source=str(world["practitioner"])) == 400
    assert await _keys(
        client, world, source=f"Practitioner/{world['practitioner']}"
    ) == {"a"}
    assert await _keys(
        client, world, source=f"Organization/{world['organization']}"
    ) == {"b"}
    assert await _keys(client, world, **{"source:Patient": str(world["p2"])}) == {"c"}
    assert await _keys(client, world, **{"source:missing": "true"}) == {"d"}


async def test_medication_has_one_target_so_a_bare_id_works(client, world):
    assert await _keys(client, world, medication=str(world["medication"])) == {"b"}
    assert await _keys(
        client, world, medication=f"Medication/{world['medication']}"
    ) == {"b"}
    assert await _keys(
        client, world, **{"medication:Medication": str(world["medication"])}
    ) == {"b"}
    assert await _keys(client, world, **{"medication:missing": "true"}) == {
        "a",
        "c",
        "d",
    }


# -- part-of --------------------------------------------------------------------------------


async def test_part_of_has_several_targets(client, world):
    assert await _status(client, **{"part-of": str(world["observation"])}) == 400
    assert await _keys(
        client, world, **{"part-of": f"Observation/{world['observation']}"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"part-of": f"Procedure/{world['procedure']}"}
    ) == {"b"}
    assert await _keys(
        client, world, **{"part-of:MedicationStatement": str(world["a"])}
    ) == {"b"}
    assert await _keys(client, world, **{"part-of:missing": "true"}) == {"c", "d"}


# -- chaining -------------------------------------------------------------------------------


async def test_chain_through_each_resource_target(client, world):
    assert await _keys(client, world, **{"patient.active": "true"}) == {"a", "c"}
    assert await _keys(client, world, **{"subject:Patient.active": "true"}) == {
        "a",
        "c",
    }
    assert await _keys(client, world, **{"subject:Group.type": "person"}) == {"b"}
    assert await _keys(
        client, world, **{"context:Encounter.status": "in-progress"}
    ) <= {"a"}
    assert await _keys(client, world, **{"context:EpisodeOfCare.status": "active"}) == {
        "b"
    }
    assert await _keys(client, world, **{"source:Practitioner.active": "true"}) <= {"a"}
    assert await _keys(client, world, **{"source:Organization.active": "true"}) <= {"b"}
    assert await _keys(client, world, **{"medication.status": "active"}) == {"b"}
    assert await _keys(client, world, **{"part-of:Observation.status": "final"}) == {
        "a"
    }
    assert await _keys(
        client, world, **{"part-of:MedicationStatement.status": "active"}
    ) == {"b"}


async def test_bad_chains_are_400(client, world):
    assert (
        await _status(client, **{"subject.active": "x"}) == 400
    )  # untyped multi-target
    assert await _status(client, **{"part-of.status": "x"}) == 400
    assert (
        await _status(client, **{"status.x": "y"}) == 400
    )  # a token cannot be chained
    assert await _status(client, **{"effective.x": "y"}) == 400
    assert await _status(client, **{"subject:Device.x": "y"}) == 400


# -- _sort / _count / _offset / _total ------------------------------------------------------


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "_id",
        "_lastUpdated",
        "category",
        "code",
        "context",
        "effective",
        "identifier",
        "medication",
        "part-of",
        "patient",
        "source",
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
    assert resource["status"] == "active"
    # R4 keeps the mandatory elements (status, medication[x], subject), drops the rest
    assert "category" not in resource and "effectiveDateTime" not in resource


# -- _include / _revinclude -----------------------------------------------------------------


async def test_include_every_reference(client, world):
    ids = ",".join(str(world[k]) for k in KEYS)
    bundle = await _search(client, _id=ids, _include="MedicationStatement:patient")
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }
    bundle = await _search(client, _id=ids, _include="MedicationStatement:subject")
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }
    assert _of_type(bundle, "Group", "include") == {str(world["group"])}
    bundle = await _search(
        client, _id=ids, _include="MedicationStatement:subject:Group"
    )
    assert _of_type(bundle, "Patient", "include") == set()
    bundle = await _search(client, _id=ids, _include="MedicationStatement:context")
    assert _of_type(bundle, "Encounter", "include") == {str(world["encounter"])}
    assert _of_type(bundle, "EpisodeOfCare", "include") == {str(world["episode"])}
    bundle = await _search(client, _id=ids, _include="MedicationStatement:source")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["practitioner"])}
    assert _of_type(bundle, "Organization", "include") == {str(world["organization"])}
    assert _of_type(bundle, "Patient", "include") == {str(world["p2"])}
    bundle = await _search(client, _id=ids, _include="MedicationStatement:medication")
    assert _of_type(bundle, "Medication", "include") == {str(world["medication"])}
    bundle = await _search(client, _id=ids, _include="MedicationStatement:part-of")
    assert _of_type(bundle, "Observation", "include") == {str(world["observation"])}
    assert _of_type(bundle, "Procedure", "include") == {str(world["procedure"])}
    # a is itself a match here, so it is not repeated as an include; ask for b alone
    bundle = await _search(
        client, _id=str(world["b"]), _include="MedicationStatement:part-of"
    )
    assert _of_type(bundle, "MedicationStatement", "include") == {str(world["a"])}


async def test_revinclude_from_the_resources_a_statement_points_at(client, world):
    async def rev(path: str, ids, param: str) -> dict:
        resp = await client.get(
            f"{API}/{path}/",
            params={
                "_id": ",".join(str(i) for i in ids),
                "_revinclude": f"MedicationStatement:{param}",
            },
        )
        assert resp.status_code == 200, resp.text
        return resp.json()

    bundle = await rev("patients", [world["p1"], world["p2"]], "patient")
    assert _of_type(bundle, "MedicationStatement", "include") == {
        str(world["a"]),
        str(world["c"]),
    }
    bundle = await rev("patients", [world["p1"], world["p2"]], "subject")
    assert _of_type(bundle, "MedicationStatement", "include") == {
        str(world["a"]),
        str(world["c"]),
    }
    bundle = await rev("patients", [world["p2"]], "source")
    assert _of_type(bundle, "MedicationStatement", "include") == {str(world["c"])}
    bundle = await rev("groups", [world["group"]], "subject")
    assert _of_type(bundle, "MedicationStatement", "include") == {str(world["b"])}
    bundle = await rev("encounters", [world["encounter"]], "context")
    assert _of_type(bundle, "MedicationStatement", "include") == {str(world["a"])}
    bundle = await rev("episodes-of-care", [world["episode"]], "context")
    assert _of_type(bundle, "MedicationStatement", "include") == {str(world["b"])}
    bundle = await rev("practitioners", [world["practitioner"]], "source")
    assert _of_type(bundle, "MedicationStatement", "include") == {str(world["a"])}
    bundle = await rev("organizations", [world["organization"]], "source")
    assert _of_type(bundle, "MedicationStatement", "include") == {str(world["b"])}
    bundle = await rev("medications", [world["medication"]], "medication")
    assert _of_type(bundle, "MedicationStatement", "include") == {str(world["b"])}
    bundle = await rev("observations", [world["observation"]], "part-of")
    assert _of_type(bundle, "MedicationStatement", "include") == {str(world["a"])}
    bundle = await rev("procedures", [world["procedure"]], "part-of")
    assert _of_type(bundle, "MedicationStatement", "include") == {str(world["b"])}
    bundle = await rev("medication-statements", [world["a"]], "part-of")
    assert _of_type(bundle, "MedicationStatement", "include") == {str(world["b"])}


# -- combination, errors --------------------------------------------------------------------


async def test_and_or_combination(client, world):
    assert await _keys(client, world, status="active", patient=str(world["p1"])) == {
        "a"
    }
    assert (
        await _keys(client, world, status="active", patient=str(world["p2"])) == set()
    )
    assert await _keys(client, world, status="active,stopped") == {"a", "c"}
    assert (
        await _keys(client, world, category=["community", "inpatient"]) == set()
    )  # AND


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, effective="notadate") == 400
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
        "reason-code",
        "derived-from",
        "based-on",
        "status-reason",
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
        BASE + "/_search", data={"status": "completed", "category": "inpatient"}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, identifier="MS-A")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/medication-statements/{world['a']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "MedicationStatement"
    assert entry["resource"]["status"] == "active"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
