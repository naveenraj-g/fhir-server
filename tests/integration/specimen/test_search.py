"""FHIR R4 search over Specimen (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/specimen.html#search).

One block per search parameter — `status` a code, `collected` a date range over a dateTime *or* a
Period, `accession` and `identifier` / `container-id` tokens on Identifiers, `type`, `bodysite` and
`container` tokens on CodeableConcepts, the single-target references (`patient`, `parent`) and the
multi-target ones (`subject`, `collector`) — then chaining, `_include`/`_revinclude` (including the
Observations and DiagnosticReports that point at a specimen), result parameters, combination
rules, lenient vs strict handling and POST _search.
"""

import pytest

from tests.integration.specimen.support import (
    ACCESSIONS,
    API,
    BASE,
    SCT,
    SPECIMEN_IDS,
    V2_0203,
    V2_0487,
    concept,
    create_location,
    create_observation,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_specimen,
    observation_body,
    specimen_body,
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
    """Two patients, a practitioner, a practitioner role and a location, plus five specimens with
    distinct, searchable values. Returns {key: id}.

      a  whole blood of p1, in two containers, collected by a practitioner
      b  urine of p2, collected over a period by a role, derived from a
      c  serum from a location, collected from an open-ended period
      d  entered in error, with a Group subject
      e  no status, a logical subject, derived from b
    """
    w = {}
    w["p1"] = await create_patient(
        client, {"active": True, "name": [{"family": "Windsor", "given": ["Anna"]}]}
    )
    w["p2"] = await create_patient(
        client, {"active": True, "name": [{"family": "Fairfax", "given": ["Ben"]}]}
    )
    w["pr"] = await create_practitioner(client)  # family "Careful"
    w["role"] = await create_practitioner_role(client)
    w["loc"] = await create_location(client)  # name "North Wing"
    w["a"] = await create_specimen(
        client,
        specimen_body(
            w["p1"],
            status="available",
            identifier=[
                {
                    "system": SPECIMEN_IDS,
                    "value": "SP-A",
                    "type": {
                        "coding": [{"system": V2_0203, "code": "FILL"}],
                        "text": "Specimen id",
                    },
                }
            ],
            accessionIdentifier={"system": ACCESSIONS, "value": "ACC-A"},
            type=concept(V2_0487, "BLD", "Whole blood"),
            collection={
                "collector": {"reference": f"Practitioner/{w['pr']}"},
                "collectedDateTime": "2023-01-15T09:30:00Z",
                "bodySite": concept(SCT, "368208006", "Left upper arm structure"),
            },
            container=[
                {
                    "identifier": [{"system": "urn:containers", "value": "C-A"}],
                    "type": concept(SCT, "434746001", "Specimen vial"),
                },
                {
                    "identifier": [{"system": "urn:containers", "value": "C-A2"}],
                    "type": concept(SCT, "119339001", "Stool container"),
                },
            ],
        ),
    )
    w["b"] = await create_specimen(
        client,
        specimen_body(
            w["p2"],
            status="unavailable",
            identifier=[{"system": SPECIMEN_IDS, "value": "SP-B"}],
            type={"text": "Urine"},
            parent=[{"reference": f"Specimen/{w['a']}"}],
            collection={
                "collector": {"reference": f"PractitionerRole/{w['role']}"},
                "collectedPeriod": {"start": "2024-01-01", "end": "2024-03-01"},
            },
            container=[{"type": {"text": "Cup"}}],
        ),
    )
    w["c"] = await create_specimen(
        client,
        {
            "status": "unsatisfactory",
            "subject": {"reference": f"Location/{w['loc']}"},
            "type": concept(V2_0487, "SER", "Serum"),
            "collection": {
                "collectedPeriod": {"start": "2022-06-01"},
                "bodySite": concept(SCT, "999"),
            },
        },
    )
    w["d"] = await create_specimen(
        client,
        {
            "status": "entered-in-error",
            "subject": {"reference": "Group/430001"},
            "collection": {"collectedDateTime": "2019"},
        },
    )
    w["e"] = await create_specimen(
        client,
        {
            "subject": {
                "identifier": {"system": "urn:pts", "value": "P-9"},
                "display": "External",
            },
            "accessionIdentifier": {"system": ACCESSIONS, "value": "ACC-E"},
            "parent": [{"reference": f"Specimen/{w['b']}"}],
        },
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


# ── _id / _lastUpdated / status ──────────────────────────────────────────────


async def test_id(client, world):
    assert await _keys(client, world, _id=str(world["a"])) == {"a"}
    assert await _keys(client, world, _id="999999") == set()
    assert await _keys(client, world, **{"_id:not": str(world["a"])}) == ALL - {"a"}


async def test_last_updated(client, world):
    assert await _keys(client, world, _lastUpdated="ge2020-01-01") == ALL
    assert await _keys(client, world, _lastUpdated="lt2020-01-01") == set()


async def test_status(client, world):
    assert await _keys(client, world, status="available") == {"a"}
    assert await _keys(client, world, status="unavailable") == {"b"}
    assert await _keys(client, world, status="unsatisfactory") == {"c"}
    assert await _keys(client, world, status="entered-in-error") == {
        "d"
    }  # the real FHIR code
    assert await _keys(client, world, status="available,unsatisfactory") == {"a", "c"}
    assert await _keys(
        client, world, status="http://hl7.org/fhir/specimen-status|available"
    ) == {"a"}
    assert await _keys(client, world, status="http://wrong|available") == set()
    assert await _keys(client, world, status="no-such-code") == set()
    assert await _keys(client, world, **{"status:missing": "true"}) == {"e"}
    assert await _keys(client, world, **{"status:missing": "false"}) == ALL - {"e"}


# ── collected ────────────────────────────────────────────────────────────────


async def test_collected_reads_a_datetime_and_a_period(client, world):
    assert await _keys(client, world, collected="2023-01-15") == {"a"}
    assert await _keys(client, world, collected="2023") == {"a"}
    assert await _keys(client, world, collected="2024") == {"b"}
    assert await _keys(client, world, collected="ge2024-01-01") == {
        "b",
        "c",
    }  # c's open-ended period reaches it
    assert await _keys(client, world, collected="lt2023-01-01") == {"c", "d"}
    assert await _keys(client, world, collected="sa2023-02-01") == {"b"}
    assert await _keys(client, world, collected="eb2020-01-01") == {"d"}
    assert await _keys(client, world, **{"collected:missing": "true"}) == {"e"}
    assert await _keys(client, world, **{"collected:missing": "false"}) == ALL - {"e"}


# ── identifier / container-id / accession ────────────────────────────────────


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="SP-A") == {"a"}
    assert await _keys(client, world, identifier=f"{SPECIMEN_IDS}|SP-B") == {"b"}
    assert await _keys(client, world, identifier="SP-A,SP-B") == {"a", "b"}
    assert await _keys(client, world, identifier="urn:wrong|SP-A") == set()
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|FILL|SP-A"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|FILL|SP-B"})
        == set()
    )
    assert await _keys(client, world, **{"identifier:text": "specimen id"}) == {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


async def test_container_id_reads_every_container(client, world):
    assert await _keys(client, world, **{"container-id": "C-A"}) == {"a"}
    assert await _keys(client, world, **{"container-id": "urn:containers|C-A2"}) == {
        "a"
    }  # the second container
    assert await _keys(client, world, **{"container-id": "C-A,C-X"}) == {"a"}
    assert await _keys(client, world, **{"container-id": "urn:wrong|C-A"}) == set()
    assert await _keys(client, world, **{"container-id:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }


async def test_accession(client, world):
    assert await _keys(client, world, accession="ACC-A") == {"a"}
    assert await _keys(client, world, accession=f"{ACCESSIONS}|ACC-E") == {"e"}
    assert await _keys(client, world, accession="ACC-A,ACC-E") == {"a", "e"}
    assert await _keys(client, world, accession="http://wrong|ACC-A") == set()
    assert await _keys(client, world, **{"accession:missing": "true"}) == {
        "b",
        "c",
        "d",
    }


# ── type / bodysite / container ──────────────────────────────────────────────


async def test_type(client, world):
    assert await _keys(client, world, type="BLD") == {"a"}
    assert await _keys(client, world, type=f"{V2_0487}|SER") == {"c"}
    assert await _keys(client, world, type="http://wrong|BLD") == set()
    assert await _keys(client, world, type="BLD,SER") == {"a", "c"}
    assert await _keys(client, world, **{"type:text": "urine"}) == {
        "b"
    }  # a text-only concept is found
    assert await _keys(client, world, **{"type:text": "whole"}) == {
        "a"
    }  # Coding.display
    assert await _keys(client, world, **{"type:missing": "true"}) == {"d", "e"}


async def test_bodysite(client, world):
    assert await _keys(client, world, bodysite="368208006") == {"a"}
    assert await _keys(client, world, bodysite=f"{SCT}|999") == {"c"}
    assert await _keys(client, world, **{"bodysite:text": "left upper"}) == {"a"}
    assert await _keys(client, world, **{"bodysite:missing": "true"}) == {"b", "d", "e"}


async def test_container_type_reads_every_container(client, world):
    assert await _keys(client, world, container="434746001") == {"a"}
    assert await _keys(client, world, container="119339001") == {
        "a"
    }  # the second container
    assert await _keys(client, world, **{"container:text": "cup"}) == {"b"}
    assert await _keys(client, world, **{"container:text": "stool"}) == {"a"}
    assert await _keys(client, world, **{"container:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


# ── patient / subject / collector / parent ───────────────────────────────────


async def test_patient(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {
        "a"
    }  # one target: a bare id works
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"b"}
    assert await _keys(client, world, patient=f"{world['p1']},{world['p2']}") == {
        "a",
        "b",
    }
    assert await _keys(client, world, patient="999999") == set()
    assert await _keys(client, world, **{"patient:Patient": str(world["p1"])}) == {"a"}
    # a Location, a Group or a logical subject is not a Patient, so it counts as missing `patient`
    assert await _keys(client, world, **{"patient:missing": "true"}) == {"c", "d", "e"}
    assert await _keys(client, world, **{"patient:missing": "false"}) == {"a", "b"}


async def test_subject_is_multi_target(client, world):
    assert (
        await _status(client, subject=str(world["p1"])) == 400
    )  # a bare id is ambiguous
    assert await _keys(client, world, subject=f"Patient/{world['p1']}") == {"a"}
    assert await _keys(client, world, **{"subject:Patient": str(world["p2"])}) == {"b"}
    assert await _keys(client, world, subject=f"Location/{world['loc']}") == {"c"}
    assert await _keys(client, world, subject="Group/430001") == {
        "d"
    }  # the type is part of the match
    assert await _keys(client, world, subject=f"Group/{world['p1']}") == set()
    assert await _keys(client, world, **{"subject:identifier": "urn:pts|P-9"}) == {"e"}
    assert await _keys(client, world, **{"subject:missing": "true"}) == set()


async def test_collector_is_multi_target(client, world):
    assert (
        await _status(client, collector=str(world["pr"])) == 400
    )  # a bare id is ambiguous
    assert await _keys(client, world, collector=f"Practitioner/{world['pr']}") == {"a"}
    assert await _keys(
        client, world, **{"collector:Practitioner": str(world["pr"])}
    ) == {"a"}
    assert await _keys(
        client, world, collector=f"PractitionerRole/{world['role']}"
    ) == {"b"}
    assert (
        await _keys(client, world, collector=f"Practitioner/{world['role']}") == set()
    )  # the type is part of the match
    assert await _keys(client, world, **{"collector:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


async def test_parent(client, world):
    assert await _keys(client, world, parent=str(world["a"])) == {
        "b"
    }  # one target: a bare id works
    assert await _keys(client, world, parent=f"Specimen/{world['b']}") == {"e"}
    assert await _keys(client, world, parent="999999") == set()
    assert await _keys(client, world, **{"parent:missing": "true"}) == {"a", "c", "d"}
    assert await _keys(client, world, **{"parent:missing": "false"}) == {"b", "e"}


# ── chaining ─────────────────────────────────────────────────────────────────


async def test_chains(client, world):
    assert await _keys(client, world, **{"patient.family": "Windsor"}) == {"a"}
    assert await _keys(client, world, **{"subject:Patient.name": "Ben"}) == {"b"}
    assert await _keys(client, world, **{"subject:Location.name": "North"}) == {"c"}
    assert await _keys(
        client, world, **{"collector:Practitioner.family": "Careful"}
    ) == {"a"}
    assert await _keys(client, world, **{"parent.status": "available"}) == {
        "b"
    }  # b derives from a
    assert await _keys(client, world, **{"parent.parent.status": "available"}) == {
        "e"
    }  # e -> b -> a


async def test_bad_chains_are_400(client, world):
    assert await _status(client, **{"patient.nonsense": "x"}) == 400
    assert (
        await _status(client, **{"subject.family": "x"}) == 400
    )  # an untyped multi-target cannot be chained
    assert (
        await _status(client, **{"subject:Group.name": "x"}) == 400
    )  # Group is not searchable here
    assert await _status(client, **{"collector.family": "x"}) == 400
    assert (
        await _status(client, **{"type.x": "y"}) == 400
    )  # a token cannot be chained through
    assert await _status(client, **{"accession.x": "y"}) == 400
    assert await _status(client, **{"collected.x": "y"}) == 400


# ── _sort / _count / _offset / _total ────────────────────────────────────────


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "accession",
        "bodysite",
        "collected",
        "collector",
        "container",
        "container-id",
        "identifier",
        "parent",
        "patient",
        "status",
        "subject",
        "type",
        "_id",
    ):
        assert (await _search(client, _sort=key))["total"] == 5, key


async def test_sort_by_collected(client, world):
    async def ids(**params):
        return [
            int(e["resource"]["id"]) for e in (await _search(client, **params))["entry"]
        ]

    assert await ids(**{"collected:missing": "false", "_sort": "collected"}) == [
        world["d"],
        world["c"],
        world["a"],
        world["b"],
    ]
    assert await ids(**{"collected:missing": "false", "_sort": "-collected"}) == [
        world["b"],
        world["a"],
        world["c"],
        world["d"],
    ]


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
    assert resource["status"] == "available"
    assert "collection" not in resource and "container" not in resource


# ── _include / _revinclude ───────────────────────────────────────────────────


async def test_include_subject_collector_and_parent(client, world):
    ids = ",".join(str(world[k]) for k in KEYS)
    for param in ("patient", "subject"):
        bundle = await _search(client, _id=ids, _include=f"Specimen:{param}")
        assert _of_type(bundle, "Patient", "include") == {
            str(world["p1"]),
            str(world["p2"]),
        }
    bundle = await _search(client, _id=ids, _include="Specimen:subject")
    assert _of_type(bundle, "Location", "include") == {
        str(world["loc"])
    }  # a Group adds nothing
    bundle = await _search(client, _id=ids, _include="Specimen:subject:Location")
    assert _of_type(bundle, "Patient", "include") == set()
    bundle = await _search(client, _id=ids, _include="Specimen:collector")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "PractitionerRole", "include") == {str(world["role"])}
    bundle = await _search(client, _id=str(world["b"]), _include="Specimen:parent")
    assert _of_type(bundle, "Specimen", "include") == {str(world["a"])}


async def test_revinclude_specimens_on_the_resources_they_point_at(client, world):
    for param in ("patient", "subject"):
        bundle = await _other(
            client, "patients", _id=str(world["p1"]), _revinclude=f"Specimen:{param}"
        )
        assert _of_type(bundle, "Specimen", "include") == {str(world["a"])}
    bundle = await _other(
        client, "locations", _id=str(world["loc"]), _revinclude="Specimen:subject"
    )
    assert _of_type(bundle, "Specimen", "include") == {str(world["c"])}
    bundle = await _other(
        client, "practitioners", _id=str(world["pr"]), _revinclude="Specimen:collector"
    )
    assert _of_type(bundle, "Specimen", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "practitioner-roles",
        _id=str(world["role"]),
        _revinclude="Specimen:collector",
    )
    assert _of_type(bundle, "Specimen", "include") == {str(world["b"])}


async def test_revinclude_parent_on_itself(client, world):
    bundle = await _search(client, _id=str(world["a"]), _revinclude="Specimen:parent")
    assert _of_type(bundle, "Specimen", "include") == {str(world["b"])}


async def test_revinclude_the_observations_and_reports_that_point_at_a_specimen(
    client, world
):
    observation = await create_observation(
        client,
        observation_body(world["p1"], specimen={"reference": f"Specimen/{world['a']}"}),
    )
    report = (
        await client.post(
            f"{API}/diagnostic-reports/",
            json={
                "status": "final",
                "code": {"text": "R"},
                "specimen": [{"reference": f"Specimen/{world['a']}"}],
            },
        )
    ).json()["id"]
    bundle = await _search(
        client, _id=str(world["a"]), _revinclude="Observation:specimen"
    )
    assert _of_type(bundle, "Observation", "include") == {str(observation)}
    bundle = await _search(
        client, _id=str(world["a"]), _revinclude="DiagnosticReport:specimen"
    )
    assert _of_type(bundle, "DiagnosticReport", "include") == {report}


async def test_revinclude_is_tenant_scoped(client, other_client):
    from app.auth.dependencies import get_current_user
    from app.main import app
    from tests.conftest import make_test_user
    from tests.integration.specimen.conftest import SPECIMEN_PERMS

    def as_user(**kw):
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=SPECIMEN_PERMS, **kw
        )

    as_user()
    mine = await create_patient(client)
    await create_specimen(client, specimen_body(mine))
    as_user(sub="u-other", org_id="org-other")
    try:
        # The other org cannot see the patient, so nothing reaches its specimens.
        bundle = await _other(
            other_client, "patients", _id=str(mine), _revinclude="Specimen:patient"
        )
        assert bundle["total"] == 0 and "entry" not in bundle
        theirs = await create_patient(other_client)
        bundle = await _other(
            other_client, "patients", _id=str(theirs), _revinclude="Specimen:patient"
        )
        assert _of_type(bundle, "Specimen", "include") == set()
    finally:
        as_user()


# ── combination rules / lenient vs strict ────────────────────────────────────


async def test_params_are_anded(client, world):
    assert await _keys(client, world, status="available", type="BLD") == {"a"}
    assert await _keys(client, world, status="unavailable", type="BLD") == set()
    assert await _keys(client, world, patient=str(world["p1"]), collected="2023") == {
        "a"
    }
    assert await _keys(
        client, world, container="434746001", **{"container-id": "C-A2"}
    ) == {"a"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"patient:text": "x"}) == 400
    assert await _status(client, **{"collected:exact": "2020"}) == 400
    assert await _status(client, **{"identifier:below": "x"}) == 400
    assert await _status(client, **{"type:nonsense": "x"}) == 400
    assert await _status(client, **{"status:text": "x"}) == 400
    assert await _status(client, **{"accession:text": "x"}) == 400


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


# ── POST _search / Bundle shape ──────────────────────────────────────────────


async def test_post_search_form_encoded(client, world):
    resp = await client.post(
        BASE + "/_search", data={"type": "SER", "status": "unsatisfactory"}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["c"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, identifier="SP-B")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/specimens/{world['b']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "Specimen"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle


async def test_observations_and_reports_chain_to_and_include_a_specimen(client, world):
    specimen = f"Specimen/{world['a']}"
    observation = await create_observation(
        client, observation_body(world["p1"], specimen={"reference": specimen})
    )
    report = (
        await client.post(
            f"{API}/diagnostic-reports/",
            json={
                "status": "final",
                "code": {"text": "R"},
                "specimen": [{"reference": specimen}],
            },
        )
    ).json()["id"]
    got = await _other(client, "observations", **{"specimen.type": "BLD"})
    assert _ids(got) == {observation}
    assert (
        _ids(await _other(client, "observations", **{"specimen.type": "SER"})) == set()
    )
    got = await _other(client, "diagnostic-reports", **{"specimen.type": "BLD"})
    assert {int(e["resource"]["id"]) for e in got["entry"]} == {int(report)}
    got = await _other(
        client, "observations", _id=str(observation), _include="Observation:specimen"
    )
    assert _of_type(got, "Specimen", "include") == {str(world["a"])}
    got = await _other(
        client, "diagnostic-reports", _id=report, _include="DiagnosticReport:specimen"
    )
    assert _of_type(got, "Specimen", "include") == {str(world["a"])}
