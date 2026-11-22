"""FHIR R4 search over CareTeam (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/careteam.html#search).

One block per search parameter - `status` a code, `date` a Period, `category` and `identifier`
tokens, the multi-target `subject` and `participant` references, `patient` (a subject narrowed
to Patients) and `encounter` - then chaining, `_include`/`_revinclude`, result parameters,
combination rules, lenient vs strict handling and POST _search.
"""

import pytest

from tests.integration.care_team.support import (
    API,
    BASE,
    CARE_TEAM_IDS,
    LOINC,
    SCT,
    V2_0203,
    care_team_body,
    concept,
    create_care_team,
    create_encounter,
    create_group,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_related_person,
    encounter_body,
    group_body,
    related_person_body,
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
    """An organization, a practitioner, a role, a related person, two patients, a group and an
    encounter, plus five care teams with distinct, searchable values. Returns {key: id}.

      a  active, category "Encounter-focused", for patient 1 at an encounter, covering 2026,
         participants: a practitioner, a related person and the organization
      b  proposed, for the group, open-ended period from 2027, participant: a practitioner role
         and patient 2
      c  inactive, for patient 2, period 2020, participant: another care team (e)
      d  suspended, a logical subject, an absolute-URL participant, no period
      e  only what makes it a care team
    """
    w = {}
    w["org"] = await create_organization(client, name="Providing Org")
    w["pr"] = await create_practitioner(client)  # family "Careful"
    w["role"] = await create_practitioner_role(client)
    w["p1"] = await create_patient(
        client, {"active": True, "name": [{"family": "Windsor", "given": ["Anna"]}]}
    )
    w["p2"] = await create_patient(
        client, {"active": True, "name": [{"family": "Fairfax", "given": ["Ben"]}]}
    )
    w["rel"] = await create_related_person(client, related_person_body(w["p1"]))
    w["grp"] = await create_group(client, group_body(type="person"))
    w["enc"] = await create_encounter(client, encounter_body())
    w["e"] = await create_care_team(client, care_team_body())
    w["a"] = await create_care_team(
        client,
        care_team_body(
            status="active",
            identifier=[
                {
                    "system": CARE_TEAM_IDS,
                    "value": "CT-A",
                    "type": {
                        "coding": [{"system": V2_0203, "code": "FILL"}],
                        "text": "Team id",
                    },
                }
            ],
            category=[concept(LOINC, "LA27976-2", "Encounter-focused care team")],
            name="Cardiology",
            subject={"reference": f"Patient/{w['p1']}"},
            encounter={"reference": f"Encounter/{w['enc']}"},
            period={"start": "2026-01-01", "end": "2026-12-31"},
            participant=[
                {"member": {"reference": f"Practitioner/{w['pr']}"}},
                {"member": {"reference": f"RelatedPerson/{w['rel']}"}},
                {"member": {"reference": f"Organization/{w['org']}"}},
            ],
        ),
    )
    w["b"] = await create_care_team(
        client,
        care_team_body(
            status="proposed",
            identifier=[{"system": CARE_TEAM_IDS, "value": "CT-B"}],
            category=[concept(SCT, "700232004", "Oncology team")],
            subject={"reference": f"Group/{w['grp']}"},
            period={"start": "2027-01-01"},
            participant=[
                {"member": {"reference": f"PractitionerRole/{w['role']}"}},
                {"member": {"reference": f"Patient/{w['p2']}"}},
            ],
        ),
    )
    w["c"] = await create_care_team(
        client,
        care_team_body(
            status="inactive",
            category=[{"text": "Home care"}],
            subject={"reference": f"Patient/{w['p2']}"},
            period={"start": "2020-01-01", "end": "2020-12-31"},
            participant=[{"member": {"reference": f"CareTeam/{w['e']}"}}],
        ),
    )
    w["d"] = await create_care_team(
        client,
        care_team_body(
            status="suspended",
            subject={
                "identifier": {"system": "urn:subj", "value": "S-9"},
                "display": "External",
            },
            participant=[
                {
                    "member": {
                        "reference": "https://other.example.org/fhir/Practitioner/9"
                    }
                },
                {"member": {"identifier": {"system": "urn:pr", "value": "P-9"}}},
            ],
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
    assert await _keys(client, world, _id="999999") == set()
    assert await _keys(client, world, **{"_id:not": str(world["a"])}) == ALL - {"a"}


async def test_last_updated(client, world):
    assert await _keys(client, world, _lastUpdated="ge2020-01-01") == ALL
    assert await _keys(client, world, _lastUpdated="lt2020-01-01") == set()


# -- status ---------------------------------------------------------------------------------


async def test_status(client, world):
    assert await _keys(client, world, status="active") == {"a"}
    assert await _keys(client, world, status="active,proposed") == {"a", "b"}
    assert await _keys(
        client, world, status="http://hl7.org/fhir/care-team-status|inactive"
    ) == {"c"}
    assert await _keys(client, world, status="urn:wrong|active") == set()
    assert await _keys(client, world, status="|active") == set()
    assert await _keys(client, world, status="retired") == set()
    # `:not` also matches a care team that has no status at all
    assert await _keys(client, world, **{"status:not": "active"}) == ALL - {"a"}
    assert await _keys(client, world, **{"status:missing": "true"}) == {"e"}


# -- date (the Period) ----------------------------------------------------------------------


async def test_date_is_a_period_search(client, world):
    # eq: the search range wholly contains the period
    assert await _keys(client, world, date="eq2026") == {"a"}
    assert await _keys(client, world, date="2020") == {"c"}
    # gt / ge / lt / le: the period overlaps the range above / below
    assert await _keys(client, world, date="ge2026-06-01") == {"a", "b"}
    assert await _keys(client, world, date="le2020-06-01") == {"c"}
    assert await _keys(client, world, date="gt2027-06-01") == {"b"}  # open-ended
    assert await _keys(client, world, date="lt2021-01-01") == {"c"}
    # sa / eb: entirely after / before
    assert await _keys(client, world, date="sa2026-12-31") == {"b"}
    assert await _keys(client, world, date="eb2021-01-01") == {"c"}
    # a care team with no period never matches a date search
    for prefix in ("ge", "le", "gt", "lt", "eq"):
        found = await _keys(client, world, date=f"{prefix}2026-06-01")
        assert "d" not in found and "e" not in found, prefix
    assert await _keys(client, world, **{"date:missing": "true"}) == {"d", "e"}


# -- identifier / category ------------------------------------------------------------------


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="CT-A") == {"a"}
    assert await _keys(client, world, identifier=f"{CARE_TEAM_IDS}|CT-B") == {"b"}
    assert await _keys(client, world, identifier="CT-A,CT-B") == {"a", "b"}
    assert await _keys(client, world, identifier="urn:wrong|CT-A") == set()
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|FILL|CT-A"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|FILL|CT-B"})
        == set()
    )
    assert await _keys(client, world, **{"identifier:text": "team id"}) == {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


async def test_category(client, world):
    assert await _keys(client, world, category="LA27976-2") == {"a"}
    assert await _keys(client, world, category=f"{LOINC}|LA27976-2") == {"a"}
    assert await _keys(client, world, category=f"{SCT}|700232004") == {"b"}
    assert await _keys(client, world, category="LA27976-2,700232004") == {"a", "b"}
    assert await _keys(client, world, category=f"{SCT}|LA27976-2") == set()
    assert await _keys(client, world, **{"category:text": "home"}) == {"c"}
    assert await _keys(client, world, **{"category:not": "LA27976-2"}) == ALL - {"a"}
    assert await _keys(client, world, **{"category:missing": "true"}) == {"d", "e"}


# -- subject / patient ----------------------------------------------------------------------


async def test_subject_is_multi_target(client, world):
    assert await _status(client, subject=str(world["p1"])) == 400  # bare id: ambiguous
    assert await _keys(client, world, subject=f"Patient/{world['p1']}") == {"a"}
    assert await _keys(client, world, **{"subject:Patient": str(world["p2"])}) == {"c"}
    assert await _keys(client, world, subject=f"Group/{world['grp']}") == {"b"}
    assert await _keys(client, world, **{"subject:Group": str(world["grp"])}) == {"b"}
    assert (
        await _keys(client, world, subject=f"Group/{world['p1']}") == set()
    )  # the type is part of the match
    assert await _keys(client, world, **{"subject:identifier": "urn:subj|S-9"}) == {"d"}
    assert await _keys(client, world, **{"subject:missing": "true"}) == {"e"}


async def test_patient_is_subject_narrowed_to_patients(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {
        "a"
    }  # a bare id works
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"c"}
    # the Group subject is not a patient, so it never matches (even by an equal id)
    assert await _keys(client, world, patient=str(world["grp"])) == set()
    assert await _keys(client, world, **{"patient:missing": "true"}) == {"b", "d", "e"}


# -- encounter ------------------------------------------------------------------------------


async def test_encounter_has_one_target_so_a_bare_id_works(client, world):
    assert await _keys(client, world, encounter=str(world["enc"])) == {"a"}
    assert await _keys(client, world, encounter=f"Encounter/{world['enc']}") == {"a"}
    assert await _keys(client, world, **{"encounter:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }


# -- participant ----------------------------------------------------------------------------


async def test_participant_is_multi_target(client, world):
    assert (
        await _status(client, participant=str(world["pr"])) == 400
    )  # a bare id is ambiguous
    assert await _keys(client, world, participant=f"Practitioner/{world['pr']}") == {
        "a"
    }
    assert await _keys(client, world, **{"participant:Patient": str(world["p2"])}) == {
        "b"
    }
    assert await _keys(
        client, world, participant=f"PractitionerRole/{world['role']}"
    ) == {"b"}
    assert await _keys(client, world, participant=f"RelatedPerson/{world['rel']}") == {
        "a"
    }
    assert await _keys(client, world, participant=f"Organization/{world['org']}") == {
        "a"
    }
    assert await _keys(client, world, participant=f"CareTeam/{world['e']}") == {"c"}
    assert (
        await _keys(client, world, participant=f"Patient/{world['pr']}") == set()
    )  # the type is part of the match
    assert await _keys(client, world, **{"participant:identifier": "urn:pr|P-9"}) == {
        "d"
    }
    assert await _keys(client, world, **{"participant:missing": "true"}) == {"e"}


async def test_participant_matches_any_of_several_members(client, world):
    both = await _keys(
        client,
        world,
        participant=f"Practitioner/{world['pr']},Patient/{world['p2']}",
    )
    assert both == {"a", "b"}


# -- chaining -------------------------------------------------------------------------------


async def test_chains(client, world):
    assert await _keys(client, world, **{"patient.family": "Windsor"}) == {"a"}
    assert await _keys(client, world, **{"subject:Patient.family": "Fairfax"}) == {"c"}
    assert await _keys(client, world, **{"subject:Group.type": "person"}) == {"b"}
    assert await _keys(
        client, world, **{"participant:Practitioner.family": "Careful"}
    ) == {"a"}
    assert await _keys(client, world, **{"participant:Patient.family": "Fairfax"}) == {
        "b"
    }
    assert await _keys(
        client, world, **{"participant:Organization.name": "Providing"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"participant:CareTeam.status": "active"}) == set()
    )
    assert await _keys(client, world, **{"encounter.status": "in-progress"}) == {"a"}


async def test_bad_chains_are_400(client, world):
    assert (
        await _status(client, **{"subject.family": "x"}) == 400
    )  # an untyped multi-target cannot be chained
    assert await _status(client, **{"participant.family": "x"}) == 400
    assert (
        await _status(client, **{"category.x": "y"}) == 400
    )  # a token cannot be chained through
    assert await _status(client, **{"date.x": "y"}) == 400


# -- _sort / _count / _offset / _total ------------------------------------------------------


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "category",
        "date",
        "encounter",
        "identifier",
        "participant",
        "patient",
        "status",
        "subject",
        "_id",
    ):
        assert (await _search(client, _sort=key))["total"] == 5, key


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
    assert "participant" not in resource and "category" not in resource


# -- _include / _revinclude -----------------------------------------------------------------


async def test_include_subject_encounter_and_participant(client, world):
    ids = ",".join(str(world[k]) for k in KEYS)
    bundle = await _search(client, _id=ids, _include="CareTeam:patient")
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }
    bundle = await _search(client, _id=ids, _include="CareTeam:subject")
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }
    assert _of_type(bundle, "Group", "include") == {str(world["grp"])}
    bundle = await _search(client, _id=ids, _include="CareTeam:subject:Group")
    assert _of_type(bundle, "Patient", "include") == set()
    assert _of_type(bundle, "Group", "include") == {str(world["grp"])}
    bundle = await _search(client, _id=ids, _include="CareTeam:encounter")
    assert _of_type(bundle, "Encounter", "include") == {str(world["enc"])}
    bundle = await _search(client, _id=ids, _include="CareTeam:participant")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "PractitionerRole", "include") == {str(world["role"])}
    assert _of_type(bundle, "RelatedPerson", "include") == {str(world["rel"])}
    assert _of_type(bundle, "Organization", "include") == {str(world["org"])}
    assert _of_type(bundle, "Patient", "include") == {str(world["p2"])}
    assert _of_type(bundle, "CareTeam", "include") == set()  # e is itself a match
    bundle = await _search(
        client, _id=str(world["c"]), _include="CareTeam:participant:CareTeam"
    )
    assert _of_type(bundle, "CareTeam", "include") == {str(world["e"])}


async def test_revinclude_on_the_resources_a_care_team_points_at(client, world):
    bundle = await _other(
        client, "patients", _id=str(world["p1"]), _revinclude="CareTeam:patient"
    )
    assert _of_type(bundle, "CareTeam", "include") == {str(world["a"])}
    bundle = await _other(
        client, "patients", _id=str(world["p2"]), _revinclude="CareTeam:subject"
    )
    assert _of_type(bundle, "CareTeam", "include") == {str(world["c"])}
    bundle = await _other(
        client, "patients", _id=str(world["p2"]), _revinclude="CareTeam:participant"
    )
    assert _of_type(bundle, "CareTeam", "include") == {str(world["b"])}
    bundle = await _other(
        client, "groups", _id=str(world["grp"]), _revinclude="CareTeam:subject"
    )
    assert _of_type(bundle, "CareTeam", "include") == {str(world["b"])}
    bundle = await _other(
        client, "encounters", _id=str(world["enc"]), _revinclude="CareTeam:encounter"
    )
    assert _of_type(bundle, "CareTeam", "include") == {str(world["a"])}
    for path, key in (
        ("practitioners", "pr"),
        ("related-persons", "rel"),
        ("organizations", "org"),
    ):
        bundle = await _other(
            client, path, _id=str(world[key]), _revinclude="CareTeam:participant"
        )
        assert _of_type(bundle, "CareTeam", "include") == {str(world["a"])}, path
    bundle = await _other(
        client,
        "practitioner-roles",
        _id=str(world["role"]),
        _revinclude="CareTeam:participant",
    )
    assert _of_type(bundle, "CareTeam", "include") == {str(world["b"])}
    bundle = await _search(
        client, _id=str(world["e"]), _revinclude="CareTeam:participant"
    )
    assert _of_type(bundle, "CareTeam", "include") == {str(world["c"])}


# -- combination rules / lenient vs strict --------------------------------------------------


async def test_params_are_anded(client, world):
    assert await _keys(client, world, status="active", category="LA27976-2") == {"a"}
    assert await _keys(client, world, status="active", category="700232004") == set()
    assert await _keys(client, world, patient=str(world["p1"]), status="active") == {
        "a"
    }


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"participant:text": "x"}) == 400
    assert await _status(client, **{"identifier:below": "x"}) == 400
    assert await _status(client, date="notadate") == 400
    assert await _status(client, **{"encounter:Patient": "1"}) == 400


async def test_unknown_param_lenient_vs_strict(client, world):
    lenient = await client.get(BASE + "/", params={"nonsense": "1"})
    assert lenient.status_code == 200
    assert any(e["search"]["mode"] == "outcome" for e in lenient.json()["entry"])
    strict = await client.get(
        BASE + "/", params={"nonsense": "1"}, headers={"Prefer": "handling=strict"}
    )
    assert strict.status_code == 400
    # R4 has no `name` search parameter on CareTeam
    assert (
        await client.get(
            BASE + "/", params={"name": "x"}, headers={"Prefer": "handling=strict"}
        )
    ).status_code == 400


async def test_query_param_refused(client, world):
    assert await _status(client, _query="x") == 400


# -- POST _search / Bundle shape ------------------------------------------------------------


async def test_post_search_form_encoded(client, world):
    resp = await client.post(
        BASE + "/_search", data={"status": "proposed", "category": "700232004"}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, identifier="CT-B")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/care-teams/{world['b']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "CareTeam"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
