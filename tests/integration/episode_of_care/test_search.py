"""FHIR R4 search over EpisodeOfCare (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/episodeofcare.html#search).

One block per search parameter - `status` a code, `date` a Period, `type` and `identifier` tokens,
the single-target `patient`, `organization`, `care-manager`, `condition` and `incoming-referral`
references - then chaining, `_include`/`_revinclude` (including Encounter's `episode-of-care`),
result parameters, combination rules, lenient vs strict handling and POST _search.
"""

import pytest

from tests.integration.episode_of_care.support import (
    API,
    BASE,
    DIAGNOSIS_ROLE,
    EPISODE_IDS,
    EPISODE_TYPE,
    EXTERNAL_PATIENT,
    STATUS_SYSTEM,
    V2_0203,
    concept,
    condition_body,
    create_condition,
    create_encounter,
    create_episode,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_service_request,
    encounter_body,
    episode_body,
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
    """Two organizations, a practitioner, a role, two patients, two conditions, two referrals and
    an encounter, plus five episodes of care with distinct, searchable values. Returns {key: id}.

      a  active, type cacp, identifier EOC-A, patient 1, organization 1, managed by a practitioner,
         covering 2026, diagnosis condition 1, referral 1
      b  planned, type hacc, patient 2, organization 2, managed by a practitioner *role*, open
         period from 2027, diagnosis condition 2
      c  finished, no type, identifier EOC-C of type MR, patient 1, period 2020, referral 2
      d  onhold, an absolute-URL patient, a logical organization, no period
      e  entered-in-error, only what makes it an episode
    """
    w = {}
    w["org1"] = await create_organization(client, name="Providing Org")
    w["org2"] = await create_organization(client, name="Other Hospital")
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
    w["cond1"] = await create_condition(client, condition_body(w["p1"]))
    w["cond2"] = await create_condition(client, condition_body(w["p2"]))
    w["sr1"] = await create_service_request(client, service_request_body(w["p1"]))
    w["sr2"] = await create_service_request(
        client, service_request_body(w["p1"], status="draft")
    )

    w["e"] = await create_episode(client, episode_body(status="entered-in-error"))
    w["d"] = await create_episode(
        client,
        episode_body(
            status="onhold",
            managingOrganization={
                "identifier": {"system": "urn:org", "value": "O-LOGICAL"}
            },
        ),
    )
    w["c"] = await create_episode(
        client,
        episode_body(
            w["p1"],
            status="finished",
            identifier=[
                {
                    "system": EPISODE_IDS,
                    "value": "EOC-C",
                    "type": {
                        "coding": [{"system": V2_0203, "code": "MR"}],
                        "text": "Medical record number",
                    },
                }
            ],
            period={"start": "2020-01-01", "end": "2020-12-31"},
            referralRequest=[{"reference": f"ServiceRequest/{w['sr2']}"}],
        ),
    )
    w["b"] = await create_episode(
        client,
        episode_body(
            w["p2"],
            status="planned",
            type=[concept(EPISODE_TYPE, "hacc", "Home and community care")],
            managingOrganization={"reference": f"Organization/{w['org2']}"},
            careManager={"reference": f"PractitionerRole/{w['role']}"},
            period={"start": "2027-01-01"},
            diagnosis=[{"condition": {"reference": f"Condition/{w['cond2']}"}}],
        ),
    )
    w["a"] = await create_episode(
        client,
        episode_body(
            w["p1"],
            identifier=[{"system": EPISODE_IDS, "value": "EOC-A"}],
            type=[concept(EPISODE_TYPE, "cacp", "Community-based aged care")],
            managingOrganization={"reference": f"Organization/{w['org1']}"},
            careManager={"reference": f"Practitioner/{w['pr']}"},
            period={"start": "2026-01-01", "end": "2026-12-31"},
            diagnosis=[
                {
                    "condition": {"reference": f"Condition/{w['cond1']}"},
                    "role": concept(DIAGNOSIS_ROLE, "AD"),
                }
            ],
            referralRequest=[{"reference": f"ServiceRequest/{w['sr1']}"}],
        ),
    )
    w["enc"] = await create_encounter(
        client, encounter_body(episodeOfCare=[{"reference": f"EpisodeOfCare/{w['a']}"}])
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
    assert await _keys(client, world, status="active") == {"a"}
    assert await _keys(client, world, status="entered-in-error") == {"e"}
    assert await _keys(client, world, status="planned,finished") == {"b", "c"}
    assert await _keys(client, world, status=f"{STATUS_SYSTEM}|onhold") == {"d"}
    assert await _keys(client, world, status="http://wrong|active") == set()
    assert await _keys(client, world, status="|active") == set()
    assert await _keys(client, world, status="retired") == set()  # unknown code
    assert await _keys(client, world, **{"status:not": "active"}) == ALL - {"a"}
    assert await _keys(client, world, **{"status:missing": "false"}) == ALL
    assert await _keys(client, world, **{"status:missing": "true"}) == set()


# -- date (a Period) ------------------------------------------------------------------------


async def test_date_is_a_period_search(client, world):
    # a covers 2026, b is open from 2027, c covers 2020; d and e have no period
    # the default `eq` means the search range wholly contains the period
    assert await _keys(client, world, date="2026") == {"a"}
    assert await _keys(client, world, date="2020") == {"c"}
    assert (
        await _keys(client, world, date="2026-03-01") == set()
    )  # a day cannot hold a year
    assert await _keys(client, world, date="ge2026-06-01") == {"a", "b"}
    assert await _keys(client, world, date="gt2027-06-01") == {"b"}
    assert await _keys(client, world, date="le2020-12-31") == {"c"}
    assert await _keys(client, world, date="lt2020-01-01") == set()
    assert await _keys(client, world, date="sa2025-01-01") == {"a", "b"}
    assert await _keys(client, world, date="eb2021-01-01") == {"c"}
    assert await _keys(client, world, **{"date:missing": "true"}) == {"d", "e"}
    assert await _keys(client, world, **{"date:missing": "false"}) == {"a", "b", "c"}
    # AND: overlaps above 2026-01-01 (a, b) and overlaps below 2026-12-31 (a, c)
    assert await _keys(client, world, date=["ge2026-01-01", "le2026-12-31"]) == {"a"}


# -- identifier / type ----------------------------------------------------------------------


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="EOC-A") == {"a"}
    assert await _keys(client, world, identifier=f"{EPISODE_IDS}|EOC-C") == {"c"}
    assert await _keys(client, world, identifier="http://wrong|EOC-A") == set()
    assert await _keys(client, world, identifier=f"{EPISODE_IDS}|") == {"a", "c"}
    assert await _keys(client, world, identifier="EOC-A,EOC-C") == {"a", "c"}
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|MR|EOC-C"}
    ) == {"c"}
    assert (
        await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|MR|EOC-A"})
        == set()
    )
    assert await _keys(client, world, **{"identifier:text": "Medical"}) == {"c"}
    assert await _keys(client, world, **{"identifier:not": "EOC-A"}) == ALL - {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {
        "b",
        "d",
        "e",
    }


async def test_type(client, world):
    assert await _keys(client, world, type="cacp") == {"a"}
    assert await _keys(client, world, type=f"{EPISODE_TYPE}|hacc") == {"b"}
    assert await _keys(client, world, type="cacp,hacc") == {"a", "b"}
    assert await _keys(client, world, type="http://wrong|cacp") == set()
    assert await _keys(client, world, type=f"{EPISODE_TYPE}|") == {"a", "b"}
    assert await _keys(client, world, **{"type:text": "Home"}) == {"b"}
    assert await _keys(client, world, **{"type:not": "cacp"}) == ALL - {"a"}
    assert await _keys(client, world, **{"type:missing": "true"}) == {"c", "d", "e"}


# -- patient / organization / care-manager --------------------------------------------------


async def test_patient_has_one_target_so_a_bare_id_works(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {"a", "c"}
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"b"}
    assert await _keys(client, world, **{"patient:Patient": str(world["p2"])}) == {"b"}
    assert await _keys(client, world, patient=f"{world['p1']},{world['p2']}") == {
        "a",
        "b",
        "c",
    }
    absolute = EXTERNAL_PATIENT["reference"]
    assert await _keys(client, world, patient=absolute) == {"d", "e"}
    assert await _keys(client, world, **{"patient:missing": "true"}) == set()
    assert await _keys(client, world, **{"patient:missing": "false"}) == ALL


async def test_organization(client, world):
    assert await _keys(client, world, organization=str(world["org1"])) == {"a"}
    assert await _keys(client, world, organization=f"Organization/{world['org2']}") == {
        "b"
    }
    assert await _keys(
        client, world, **{"organization:identifier": "urn:org|O-LOGICAL"}
    ) == {"d"}
    assert await _keys(client, world, **{"organization:missing": "true"}) == {"c", "e"}
    assert await _keys(client, world, **{"organization:missing": "false"}) == {
        "a",
        "b",
        "d",
    }


async def test_care_manager_is_careManager_resolved_to_a_practitioner(client, world):
    assert await _keys(client, world, **{"care-manager": str(world["pr"])}) == {"a"}
    assert await _keys(
        client, world, **{"care-manager": f"Practitioner/{world['pr']}"}
    ) == {"a"}
    # b is managed by a PractitionerRole: that is not this parameter's
    assert await _keys(client, world, **{"care-manager": str(world["role"])}) == set()
    assert await _keys(client, world, **{"care-manager:missing": "false"}) == {"a"}
    assert await _keys(client, world, **{"care-manager:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }


# -- condition / incoming-referral ----------------------------------------------------------


async def test_condition(client, world):
    assert await _keys(client, world, condition=str(world["cond1"])) == {"a"}
    assert await _keys(client, world, condition=f"Condition/{world['cond2']}") == {"b"}
    assert await _keys(
        client, world, condition=f"{world['cond1']},{world['cond2']}"
    ) == {"a", "b"}
    assert await _keys(client, world, **{"condition:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


async def test_condition_matches_any_diagnosis(client, world):
    both = await create_episode(
        client,
        episode_body(
            diagnosis=[
                {"condition": {"reference": f"Condition/{world['cond1']}"}},
                {"condition": {"reference": f"Condition/{world['cond2']}"}},
            ]
        ),
    )
    ids = _ids(await _search(client, condition=str(world["cond2"])))
    assert both in ids and world["b"] in ids and world["a"] not in ids


async def test_incoming_referral(client, world):
    assert await _keys(client, world, **{"incoming-referral": str(world["sr1"])}) == {
        "a"
    }
    assert await _keys(
        client, world, **{"incoming-referral": f"ServiceRequest/{world['sr2']}"}
    ) == {"c"}
    assert await _keys(client, world, **{"incoming-referral:missing": "true"}) == {
        "b",
        "d",
        "e",
    }


# -- chaining -------------------------------------------------------------------------------


async def test_chains(client, world):
    assert await _keys(client, world, **{"patient.family": "Windsor"}) == {"a", "c"}
    assert await _keys(client, world, **{"patient.family": "Fairfax"}) == {"b"}
    assert await _keys(client, world, **{"organization.name": "Providing"}) == {"a"}
    assert await _keys(client, world, **{"care-manager.family": "Careful"}) == {"a"}
    assert await _keys(client, world, **{"condition.patient": str(world["p2"])}) == {
        "b"
    }
    assert await _keys(client, world, **{"incoming-referral.status": "draft"}) == {"c"}
    assert await _keys(client, world, **{"incoming-referral.status": "active"}) == {"a"}


async def test_bad_chains_are_400(client, world):
    assert await _status(client, **{"type.x": "y"}) == 400  # a token cannot be chained
    assert await _status(client, **{"date.x": "y"}) == 400
    assert await _status(client, **{"patient:Organization.name": "x"}) == 400


# -- _sort / _count / _offset / _total ------------------------------------------------------


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "care-manager",
        "condition",
        "date",
        "identifier",
        "incoming-referral",
        "organization",
        "patient",
        "status",
        "type",
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
    assert resource["status"] == "active"
    assert "diagnosis" not in resource and "type" not in resource


# -- _include / _revinclude -----------------------------------------------------------------


async def test_include_every_reference(client, world):
    ids = ",".join(str(world[k]) for k in KEYS)
    bundle = await _search(client, _id=ids, _include="EpisodeOfCare:patient")
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }
    bundle = await _search(client, _id=ids, _include="EpisodeOfCare:organization")
    assert _of_type(bundle, "Organization", "include") == {
        str(world["org1"]),
        str(world["org2"]),
    }
    bundle = await _search(client, _id=ids, _include="EpisodeOfCare:care-manager")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    bundle = await _search(client, _id=ids, _include="EpisodeOfCare:condition")
    assert _of_type(bundle, "Condition", "include") == {
        str(world["cond1"]),
        str(world["cond2"]),
    }
    bundle = await _search(client, _id=ids, _include="EpisodeOfCare:incoming-referral")
    assert _of_type(bundle, "ServiceRequest", "include") == {
        str(world["sr1"]),
        str(world["sr2"]),
    }


async def test_revinclude_on_the_resources_an_episode_points_at(client, world):
    bundle = await _other(
        client, "patients", _id=str(world["p1"]), _revinclude="EpisodeOfCare:patient"
    )
    assert _of_type(bundle, "EpisodeOfCare", "include") == {
        str(world["a"]),
        str(world["c"]),
    }
    bundle = await _other(
        client,
        "organizations",
        _id=str(world["org2"]),
        _revinclude="EpisodeOfCare:organization",
    )
    assert _of_type(bundle, "EpisodeOfCare", "include") == {str(world["b"])}
    bundle = await _other(
        client,
        "practitioners",
        _id=str(world["pr"]),
        _revinclude="EpisodeOfCare:care-manager",
    )
    assert _of_type(bundle, "EpisodeOfCare", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "conditions",
        _id=str(world["cond2"]),
        _revinclude="EpisodeOfCare:condition",
    )
    assert _of_type(bundle, "EpisodeOfCare", "include") == {str(world["b"])}
    bundle = await _other(
        client,
        "service-requests",
        _id=str(world["sr2"]),
        _revinclude="EpisodeOfCare:incoming-referral",
    )
    assert _of_type(bundle, "EpisodeOfCare", "include") == {str(world["c"])}


# -- Encounter.episodeOfCare is followed in both directions ---------------------------------


async def test_encounter_chains_and_includes_its_episode(client, world):
    encounters = await _other(
        client, "encounters", **{"episode-of-care.status": "active"}
    )
    assert _ids(encounters) == {world["enc"]}
    assert (
        _ids(
            await _other(client, "encounters", **{"episode-of-care.status": "finished"})
        )
        == set()
    )
    bundle = await _other(
        client,
        "encounters",
        _id=str(world["enc"]),
        _include="Encounter:episode-of-care",
    )
    assert _of_type(bundle, "EpisodeOfCare", "include") == {str(world["a"])}


async def test_episode_revincludes_encounters(client, world):
    bundle = await _search(
        client, _id=str(world["a"]), _revinclude="Encounter:episode-of-care"
    )
    assert _of_type(bundle, "Encounter", "include") == {str(world["enc"])}
    bundle = await _search(
        client, _id=str(world["b"]), _revinclude="Encounter:episode-of-care"
    )
    assert _of_type(bundle, "Encounter", "include") == set()


# -- combination rules / lenient vs strict --------------------------------------------------


async def test_params_are_anded(client, world):
    assert await _keys(client, world, status="active", type="cacp") == {"a"}
    assert await _keys(client, world, status="active", type="hacc") == set()
    assert await _keys(client, world, patient=str(world["p1"]), status="finished") == {
        "c"
    }


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"identifier:below": "x"}) == 400
    assert await _status(client, date="notadate") == 400
    assert await _status(client, **{"patient:Group": "1"}) == 400
    assert await _status(client, **{"status:text": "x"}) == 400


async def test_unknown_param_lenient_vs_strict(client, world):
    lenient = await client.get(BASE + "/", params={"nonsense": "1"})
    assert lenient.status_code == 200
    assert any(e["search"]["mode"] == "outcome" for e in lenient.json()["entry"])
    strict = await client.get(
        BASE + "/", params={"nonsense": "1"}, headers={"Prefer": "handling=strict"}
    )
    assert strict.status_code == 400
    # R4 has no `team` or `account` search parameter on EpisodeOfCare
    for name in ("team", "account", "name"):
        assert (
            await client.get(
                BASE + "/", params={name: "x"}, headers={"Prefer": "handling=strict"}
            )
        ).status_code == 400, name


async def test_query_param_refused(client, world):
    assert await _status(client, _query="x") == 400


# -- POST _search / Bundle shape ------------------------------------------------------------


async def test_post_search_form_encoded(client, world):
    resp = await client.post(
        BASE + "/_search", data={"status": "planned", "type": "hacc"}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, identifier="EOC-A")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/episodes-of-care/{world['a']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "EpisodeOfCare"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
