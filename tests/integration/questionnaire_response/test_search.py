"""FHIR R4 search over QuestionnaireResponse (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/questionnaireresponse.html#search).

One block per search parameter - `status` a code, `authored` a dateTime, `identifier` a token, the
single-target `encounter`, the multi-target `subject` (Reference(Any)), `patient` (a subject
narrowed to Patients), `author`, `source`, `based-on` and `part-of`, and `questionnaire` (a
canonical URL) - then chaining, `_include`/`_revinclude`, result parameters, combination rules,
lenient vs strict handling and POST _search. R4 defines no search parameter for the answers.
"""

import pytest

from tests.integration.questionnaire_response.support import (
    API,
    BASE,
    QUESTIONNAIRE,
    RESPONSE_IDS,
    STATUS_SYSTEM,
    V2_0203,
    care_plan_body,
    create_care_plan,
    create_encounter,
    create_group,
    create_observation,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_procedure,
    create_questionnaire_response,
    create_related_person,
    create_service_request,
    encounter_body,
    group_body,
    observation_body,
    procedure_body,
    questionnaire_response_body,
    related_person_body,
    service_request_body,
)

KEYS = ("a", "b", "c", "d", "e")
ALL = set(KEYS)
GAD = "https://fhir-server.dev/fhir/Questionnaire/gad-7"


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
    """An organization, a practitioner, a role, two patients, a related person, a group, an
    encounter, a care plan, a service request, an observation and a procedure, plus five responses
    with distinct, searchable values. Returns {key: id}.

      a  completed, identifier QR-A (type MR), questionnaire phq-9|1.0, patient 1, an encounter,
         authored 2026-02-01, author the practitioner, source patient 1, basedOn the care plan,
         partOf the observation
      b  in-progress, subject the group, questionnaire gad-7, authored 2025-06, author the role,
         source the related person, basedOn the service request, partOf the procedure
      c  amended, patient 2, authored 2024, author the organization, no source, the relative
         questionnaire `Questionnaire/777`
      d  entered-in-error, subject an Observation, an absolute-URL author, a logical source
      e  stopped, only what makes it a response
    """
    w = {}
    w["org"] = await create_organization(client, name="Providing Org")
    w["pr"] = await create_practitioner(client)  # family "Careful"
    w["role"] = await create_practitioner_role(
        client, {"practitioner": {"reference": f"Practitioner/{w['pr']}"}}
    )
    w["p1"] = await create_patient(
        client, {"active": True, "name": [{"family": "Windsor", "given": ["Anna"]}]}
    )
    w["p2"] = await create_patient(
        client, {"active": True, "name": [{"family": "Fairfax", "given": ["Ben"]}]}
    )
    w["rel"] = await create_related_person(client, related_person_body(w["p1"]))
    w["grp"] = await create_group(client, group_body(type="person"))
    w["enc"] = await create_encounter(client, encounter_body())
    w["cp"] = await create_care_plan(client, care_plan_body(w["p1"]))
    w["sr"] = await create_service_request(client, service_request_body(w["p1"]))
    w["obs"] = await create_observation(client, observation_body(w["p1"]))
    w["proc"] = await create_procedure(client, procedure_body(w["p1"]))

    w["e"] = await create_questionnaire_response(
        client, questionnaire_response_body(status="stopped")
    )
    w["d"] = await create_questionnaire_response(
        client,
        questionnaire_response_body(
            status="entered-in-error",
            subject={"reference": f"Observation/{w['obs']}"},
            author={"reference": "https://other.example.org/fhir/Practitioner/9"},
            source={"identifier": {"system": "urn:pr", "value": "P-LOGICAL"}},
        ),
    )
    w["c"] = await create_questionnaire_response(
        client,
        questionnaire_response_body(
            status="amended",
            subject={"reference": f"Patient/{w['p2']}"},
            authored="2024-03-15T12:00:00Z",
            author={"reference": f"Organization/{w['org']}"},
            questionnaire="Questionnaire/777",
        ),
    )
    w["b"] = await create_questionnaire_response(
        client,
        questionnaire_response_body(
            status="in-progress",
            subject={"reference": f"Group/{w['grp']}"},
            authored="2025-06-01T09:00:00Z",
            author={"reference": f"PractitionerRole/{w['role']}"},
            source={"reference": f"RelatedPerson/{w['rel']}"},
            basedOn=[{"reference": f"ServiceRequest/{w['sr']}"}],
            partOf=[{"reference": f"Procedure/{w['proc']}"}],
            questionnaire=GAD,
        ),
    )
    w["a"] = await create_questionnaire_response(
        client,
        questionnaire_response_body(
            identifier={
                "system": RESPONSE_IDS,
                "value": "QR-A",
                "type": {
                    "coding": [{"system": V2_0203, "code": "MR"}],
                    "text": "Medical record number",
                },
            },
            questionnaire=f"{QUESTIONNAIRE}|1.0",
            subject={"reference": f"Patient/{w['p1']}"},
            encounter={"reference": f"Encounter/{w['enc']}"},
            authored="2026-02-01T10:00:00Z",
            author={"reference": f"Practitioner/{w['pr']}"},
            source={"reference": f"Patient/{w['p1']}"},
            basedOn=[{"reference": f"CarePlan/{w['cp']}"}],
            partOf=[{"reference": f"Observation/{w['obs']}"}],
            item=[{"linkId": "1", "answer": [{"valueString": "not searchable"}]}],
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


# -- _id / _lastUpdated ---------------------------------------------------------------------


async def test_id(client, world):
    assert await _keys(client, world, _id=str(world["a"])) == {"a"}
    both = f"{world['a']},{world['b']}"
    assert await _keys(client, world, _id=both) == {"a", "b"}
    assert await _keys(client, world, **{"_id:not": str(world["a"])}) == ALL - {"a"}
    assert await _keys(client, world, _id="999999") == set()


async def test_last_updated(client, world):
    assert await _keys(client, world, _lastUpdated="ge2000-01-01") == ALL
    assert await _keys(client, world, _lastUpdated="lt2000-01-01") == set()


# -- status ---------------------------------------------------------------------------------


async def test_status(client, world):
    assert await _keys(client, world, status="completed") == {"a"}
    assert await _keys(client, world, status="in-progress") == {"b"}
    assert await _keys(client, world, status="entered-in-error") == {"d"}
    assert await _keys(client, world, status="amended,stopped") == {"c", "e"}
    assert await _keys(client, world, status=f"{STATUS_SYSTEM}|completed") == {"a"}
    assert await _keys(client, world, status="http://wrong|completed") == set()
    assert await _keys(client, world, status="|completed") == set()
    assert await _keys(client, world, status="retired") == set()  # unknown code
    assert (
        await _keys(client, world, status="in_progress") == set()
    )  # not the FHIR code
    assert await _keys(client, world, **{"status:not": "completed"}) == ALL - {"a"}
    assert await _keys(client, world, **{"status:missing": "true"}) == set()


# -- authored (a dateTime, held as the range it covers) -------------------------------------


async def test_authored(client, world):
    assert await _keys(client, world, authored="2026-02-01") == {"a"}
    assert await _keys(client, world, authored="2026") == {"a"}
    assert await _keys(client, world, authored="2025-06") == {"b"}
    assert await _keys(client, world, authored="ge2025-01-01") == {"a", "b"}
    assert await _keys(client, world, authored="lt2025-01-01") == {"c"}
    assert await _keys(client, world, authored="gt2025-06-01T09:00:00Z") == {"a"}
    assert await _keys(client, world, authored="le2025-06-01T09:00:00Z") == {"b", "c"}
    assert await _keys(client, world, authored=["ge2024-01-01", "lt2026-01-01"]) == {
        "b",
        "c",
    }
    assert await _keys(client, world, **{"authored:missing": "true"}) == {"d", "e"}


# -- identifier -----------------------------------------------------------------------------


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="QR-A") == {"a"}
    assert await _keys(client, world, identifier=f"{RESPONSE_IDS}|QR-A") == {"a"}
    assert await _keys(client, world, identifier="http://wrong|QR-A") == set()
    assert await _keys(client, world, identifier=f"{RESPONSE_IDS}|") == {"a"}
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|MR|QR-A"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|ACSN|QR-A"})
        == set()
    )
    assert await _keys(client, world, **{"identifier:text": "Medical"}) == {"a"}
    assert await _keys(client, world, **{"identifier:not": "QR-A"}) == ALL - {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == ALL - {"a"}


# -- subject / patient / encounter ----------------------------------------------------------


async def test_subject_is_multi_target_and_may_be_any_resource(client, world):
    assert await _keys(client, world, subject=f"Patient/{world['p1']}") == {"a"}
    assert await _keys(client, world, subject=f"Group/{world['grp']}") == {"b"}
    assert await _keys(client, world, subject=f"Observation/{world['obs']}") == {"d"}
    assert await _keys(client, world, **{"subject:Group": str(world["grp"])}) == {"b"}
    assert await _keys(client, world, **{"subject:Patient": str(world["p2"])}) == {"c"}
    assert (
        await _status(client, subject=str(world["p1"])) == 400
    )  # a bare id is ambiguous
    assert await _keys(client, world, **{"subject:missing": "true"}) == {"e"}


async def test_patient_is_subject_narrowed_to_patients(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {"a"}
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"c"}
    # a Group or Observation subject counts as missing it
    assert await _keys(client, world, **{"patient:missing": "true"}) == {"b", "d", "e"}
    assert await _keys(client, world, **{"patient:missing": "false"}) == {"a", "c"}


async def test_encounter_has_one_target_so_a_bare_id_works(client, world):
    assert await _keys(client, world, encounter=str(world["enc"])) == {"a"}
    assert await _keys(client, world, encounter=f"Encounter/{world['enc']}") == {"a"}
    assert await _keys(client, world, **{"encounter:missing": "true"}) == ALL - {"a"}


# -- author / source ------------------------------------------------------------------------


async def test_author_is_multi_target(client, world):
    assert await _keys(client, world, author=f"Practitioner/{world['pr']}") == {"a"}
    assert await _keys(client, world, author=f"PractitionerRole/{world['role']}") == {
        "b"
    }
    assert await _keys(client, world, author=f"Organization/{world['org']}") == {"c"}
    assert await _keys(client, world, **{"author:Organization": str(world["org"])}) == {
        "c"
    }
    assert await _keys(
        client, world, author="https://other.example.org/fhir/Practitioner/9"
    ) == {"d"}
    assert await _status(client, author=str(world["pr"])) == 400
    assert await _keys(client, world, **{"author:missing": "true"}) == {"e"}


async def test_source_is_multi_target(client, world):
    assert await _keys(client, world, source=f"Patient/{world['p1']}") == {"a"}
    assert await _keys(client, world, source=f"RelatedPerson/{world['rel']}") == {"b"}
    assert await _keys(client, world, **{"source:identifier": "urn:pr|P-LOGICAL"}) == {
        "d"
    }
    assert await _status(client, source=str(world["p1"])) == 400
    assert await _keys(client, world, **{"source:missing": "true"}) == {"c", "e"}


# -- based-on / part-of ---------------------------------------------------------------------


async def test_based_on_and_part_of_are_multi_target(client, world):
    assert await _keys(client, world, **{"based-on": f"CarePlan/{world['cp']}"}) == {
        "a"
    }
    assert await _keys(
        client, world, **{"based-on": f"ServiceRequest/{world['sr']}"}
    ) == {"b"}
    assert await _keys(
        client, world, **{"based-on:ServiceRequest": str(world["sr"])}
    ) == {"b"}
    assert await _status(client, **{"based-on": str(world["cp"])}) == 400
    assert await _keys(client, world, **{"based-on:missing": "true"}) == {"c", "d", "e"}
    assert await _keys(client, world, **{"part-of": f"Observation/{world['obs']}"}) == {
        "a"
    }
    assert await _keys(client, world, **{"part-of": f"Procedure/{world['proc']}"}) == {
        "b"
    }
    assert await _keys(client, world, **{"part-of:missing": "false"}) == {"a", "b"}


# -- questionnaire (a canonical URL) --------------------------------------------------------


async def test_questionnaire_is_a_canonical_search(client, world):
    # exact, versioned
    assert await _keys(client, world, questionnaire=f"{QUESTIONNAIRE}|1.0") == {"a"}
    # an unversioned URL finds the stored versions of it
    assert await _keys(client, world, questionnaire=QUESTIONNAIRE) == {"a"}
    assert await _keys(client, world, questionnaire=GAD) == {"b"}
    # another version never matches
    assert await _keys(client, world, questionnaire=f"{QUESTIONNAIRE}|2.0") == set()
    # a relative reference matches by type and id
    assert await _keys(client, world, questionnaire="Questionnaire/777") == {"c"}
    assert await _keys(client, world, questionnaire="777") == {"c"}
    assert await _keys(client, world, questionnaire=f"{GAD},{QUESTIONNAIRE}") == {
        "a",
        "b",
    }
    assert await _keys(client, world, **{"questionnaire:missing": "true"}) == {"d", "e"}
    assert await _keys(client, world, **{"questionnaire:missing": "false"}) == {
        "a",
        "b",
        "c",
    }


# -- the answers are not searchable ---------------------------------------------------------


async def test_the_item_tree_has_no_search_parameter(client, world):
    for name in ("item", "answer", "link-id", "linkId", "value-string", "item-subject"):
        resp = await client.get(
            BASE + "/", params={name: "x"}, headers={"Prefer": "handling=strict"}
        )
        assert resp.status_code == 400, name


# -- chaining -------------------------------------------------------------------------------


async def test_chains(client, world):
    assert await _keys(client, world, **{"patient.family": "Windsor"}) == {"a"}
    assert await _keys(client, world, **{"subject:Patient.family": "Fairfax"}) == {"c"}
    assert await _keys(client, world, **{"subject:Group.type": "person"}) == {"b"}
    assert await _keys(client, world, **{"subject:Observation.status": "final"}) == {
        "d"
    }
    assert await _keys(client, world, **{"author:Practitioner.family": "Careful"}) == {
        "a"
    }
    assert await _keys(client, world, **{"author:Organization.name": "Providing"}) == {
        "c"
    }
    assert await _keys(client, world, **{"source:Patient.family": "Windsor"}) == {"a"}
    assert await _keys(client, world, **{"encounter.status": "in-progress"}) == {"a"}
    assert await _keys(client, world, **{"based-on:CarePlan.status": "active"}) == {"a"}
    assert await _keys(
        client, world, **{"based-on:ServiceRequest.status": "active"}
    ) == {"b"}
    assert await _keys(client, world, **{"part-of:Procedure.status": "completed"}) == {
        "b"
    }
    assert await _keys(client, world, **{"part-of:Observation.status": "final"}) == {
        "a"
    }


async def test_bad_chains_are_400(client, world):
    assert (
        await _status(client, **{"subject.family": "x"}) == 400
    )  # untyped multi-target
    assert await _status(client, **{"author.family": "x"}) == 400
    assert (
        await _status(client, **{"status.x": "y"}) == 400
    )  # a token cannot be chained
    assert await _status(client, **{"authored.x": "y"}) == 400
    assert (
        await _status(client, **{"questionnaire.title": "x"}) == 400
    )  # not a resource here


# -- _sort / _count / _offset / _total ------------------------------------------------------


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "author",
        "authored",
        "based-on",
        "encounter",
        "identifier",
        "part-of",
        "patient",
        "questionnaire",
        "source",
        "status",
        "subject",
        "_id",
    ):
        assert (await _search(client, _sort=key))["total"] == 5, key
        assert (await _search(client, _sort=f"-{key}"))["total"] == 5, key


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
    assert "item" not in resource and "subject" not in resource


# -- _include / _revinclude -----------------------------------------------------------------


async def test_include_every_reference(client, world):
    ids = ",".join(str(world[k]) for k in KEYS)
    bundle = await _search(client, _id=ids, _include="QuestionnaireResponse:patient")
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }
    bundle = await _search(client, _id=ids, _include="QuestionnaireResponse:subject")
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }
    assert _of_type(bundle, "Group", "include") == {str(world["grp"])}
    assert _of_type(bundle, "Observation", "include") == {str(world["obs"])}
    bundle = await _search(
        client, _id=ids, _include="QuestionnaireResponse:subject:Group"
    )
    assert _of_type(bundle, "Patient", "include") == set()
    assert _of_type(bundle, "Group", "include") == {str(world["grp"])}
    bundle = await _search(client, _id=ids, _include="QuestionnaireResponse:encounter")
    assert _of_type(bundle, "Encounter", "include") == {str(world["enc"])}
    bundle = await _search(client, _id=ids, _include="QuestionnaireResponse:author")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "PractitionerRole", "include") == {str(world["role"])}
    assert _of_type(bundle, "Organization", "include") == {str(world["org"])}
    bundle = await _search(client, _id=ids, _include="QuestionnaireResponse:source")
    assert _of_type(bundle, "Patient", "include") == {str(world["p1"])}
    assert _of_type(bundle, "RelatedPerson", "include") == {str(world["rel"])}
    bundle = await _search(client, _id=ids, _include="QuestionnaireResponse:based-on")
    assert _of_type(bundle, "CarePlan", "include") == {str(world["cp"])}
    assert _of_type(bundle, "ServiceRequest", "include") == {str(world["sr"])}
    bundle = await _search(client, _id=ids, _include="QuestionnaireResponse:part-of")
    assert _of_type(bundle, "Observation", "include") == {str(world["obs"])}
    assert _of_type(bundle, "Procedure", "include") == {str(world["proc"])}


async def test_revinclude_on_the_resources_a_response_points_at(client, world):
    for path, key, param, expected in (
        ("patients", "p1", "QuestionnaireResponse:patient", {"a"}),
        ("patients", "p1", "QuestionnaireResponse:subject", {"a"}),
        ("patients", "p1", "QuestionnaireResponse:source", {"a"}),
        ("patients", "p2", "QuestionnaireResponse:subject", {"c"}),
        ("practitioners", "pr", "QuestionnaireResponse:author", {"a"}),
        ("practitioner-roles", "role", "QuestionnaireResponse:author", {"b"}),
        ("organizations", "org", "QuestionnaireResponse:author", {"c"}),
        ("related-persons", "rel", "QuestionnaireResponse:source", {"b"}),
        ("encounters", "enc", "QuestionnaireResponse:encounter", {"a"}),
        ("care-plans", "cp", "QuestionnaireResponse:based-on", {"a"}),
        ("service-requests", "sr", "QuestionnaireResponse:based-on", {"b"}),
        ("observations", "obs", "QuestionnaireResponse:part-of", {"a"}),
        ("procedures", "proc", "QuestionnaireResponse:part-of", {"b"}),
    ):
        bundle = await _other(client, path, _id=str(world[key]), _revinclude=param)
        got = _of_type(bundle, "QuestionnaireResponse", "include")
        assert got == {str(world[k]) for k in expected}, (path, param)


# -- combination rules / lenient vs strict --------------------------------------------------


async def test_params_are_anded(client, world):
    assert await _keys(client, world, status="completed", patient=str(world["p1"])) == {
        "a"
    }
    assert (
        await _keys(client, world, status="amended", patient=str(world["p1"])) == set()
    )
    assert await _keys(
        client, world, authored="ge2025-01-01", status="in-progress"
    ) == {"b"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"identifier:below": "x"}) == 400
    assert await _status(client, authored="notadate") == 400
    assert await _status(client, **{"patient:Group": "1"}) == 400
    assert await _status(client, **{"status:text": "x"}) == 400
    assert await _status(client, **{"questionnaire:Patient": "1"}) == 400


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


# -- POST _search / Bundle shape ------------------------------------------------------------


async def test_post_search_form_encoded(client, world):
    resp = await client.post(
        BASE + "/_search", data={"status": "in-progress", "questionnaire": GAD}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, identifier="QR-A")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/questionnaire-responses/{world['a']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "QuestionnaireResponse"
    assert entry["resource"]["item"][0]["answer"][0]["valueString"] == "not searchable"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
