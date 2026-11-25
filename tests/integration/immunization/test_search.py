"""FHIR R4 search over Immunization (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/immunization.html#search).

One block per search parameter — `status`, `reason-code`, `status-reason`,
`target-disease` and `vaccine-code` are tokens, `identifier` a token on an
Identifier, `date` and `reaction-date` date ranges, `lot-number` and `series`
strings, the single-target references (`patient`, `location`, `manufacturer`,
`reaction`) and the multi-target ones (`performer`, `reason-reference`) — then
chaining, `_include`/`_revinclude` in both directions, result parameters,
combination rules, lenient vs strict handling and POST _search.
"""

import pytest

from tests.integration.immunization.support import (
    ACT_REASON,
    API,
    BASE,
    CVX,
    IMMUNIZATION_IDS,
    SCT,
    STATUS_SYSTEM,
    V2_0203,
    condition_body,
    create_condition,
    create_immunization,
    create_location,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_report,
    immunization_body,
    report_body,
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


def _vaccine(code, display=None):
    return {
        "coding": [
            {"system": CVX, "code": code, **({"display": display} if display else {})}
        ]
    }


@pytest.fixture
async def world(client):
    """Two patients, a practitioner, a practitioner role, an organization, a location, a condition
    and a diagnostic report, plus five immunizations with distinct, searchable values.
    Returns {key: id}."""
    w = {}
    w["p1"] = await create_patient(
        client, {"active": True, "name": [{"family": "Windsor", "given": ["Anna"]}]}
    )
    w["p2"] = await create_patient(
        client, {"active": True, "name": [{"family": "Fairfax", "given": ["Ben"]}]}
    )
    w["pr"] = await create_practitioner(client)  # family "Careful"
    w["role"] = await create_practitioner_role(client)
    w["org"] = await create_organization(client)  # name "Providing Org"
    w["loc"] = await create_location(client)  # name "North Wing"
    w["cond"] = await create_condition(client, condition_body(w["p1"]))
    w["rep"] = await create_report(client, report_body(w["p1"]))
    w["a"] = await create_immunization(
        client,
        immunization_body(
            w["p1"],
            "completed",
            identifier=[
                {
                    "system": IMMUNIZATION_IDS,
                    "value": "IM-A",
                    "type": {
                        "coding": [{"system": V2_0203, "code": "FILL"}],
                        "text": "Immunization id",
                    },
                }
            ],
            vaccineCode=_vaccine("140", "Influenza vaccine"),
            occurrenceDateTime="2023-01-15T09:30:00Z",
            lotNumber="AAJN11K",
            location={"reference": f"Location/{w['loc']}"},
            manufacturer={"reference": f"Organization/{w['org']}"},
            performer=[
                {"actor": {"reference": f"Practitioner/{w['pr']}"}},
                {"actor": {"reference": f"Organization/{w['org']}"}},
            ],
            reasonCode=[
                {
                    "coding": [
                        {
                            "system": SCT,
                            "code": "429060002",
                            "display": "Occupational requirement",
                        }
                    ]
                }
            ],
            reasonReference=[
                {"reference": f"Condition/{w['cond']}"},
                {"reference": f"DiagnosticReport/{w['rep']}"},
            ],
            reaction=[
                {
                    "date": "2023-01-16T08:00:00Z",
                    "detail": {"reference": "Observation/160001"},
                }
            ],
            protocolApplied=[
                {
                    "series": "2-dose",
                    "targetDisease": [
                        {
                            "coding": [
                                {
                                    "system": SCT,
                                    "code": "6142004",
                                    "display": "Influenza",
                                }
                            ]
                        }
                    ],
                    "doseNumberPositiveInt": 1,
                }
            ],
        ),
    )
    w["b"] = await create_immunization(
        client,
        immunization_body(
            w["p2"],
            "not-done",
            identifier=[{"system": IMMUNIZATION_IDS, "value": "IM-B"}],
            vaccineCode=_vaccine("03", "MMR vaccine"),
            occurrenceDateTime="2024-02",
            lotNumber="BB22",
            statusReason={
                "coding": [{"system": ACT_REASON, "code": "PATOBJ"}],
                "text": "Patient objection",
            },
            performer=[{"actor": {"reference": f"PractitionerRole/{w['role']}"}}],
            reaction=[
                {"date": "2024-02-20", "detail": {"reference": "Observation/160009"}}
            ],
            protocolApplied=[
                {
                    "series": "Booster",
                    "targetDisease": [
                        {
                            "coding": [
                                {
                                    "system": SCT,
                                    "code": "14189004",
                                    "display": "Measles",
                                }
                            ]
                        }
                    ],
                    "doseNumberString": "booster",
                }
            ],
        ),
    )
    w["c"] = await create_immunization(
        client,
        immunization_body(
            w["p1"],
            "entered-in-error",
            vaccineCode={"text": "Tetanus shot"},
            occurrenceString="last spring",
            performer=[
                {"actor": {"identifier": {"system": "urn:who", "value": "W-1"}}}
            ],
            reasonReference=[{"reference": "Observation/160003"}],
        ),
    )
    w["d"] = await create_immunization(
        client,
        immunization_body(
            w["p2"],
            "completed",
            vaccineCode=_vaccine("140", "Influenza vaccine"),
            occurrenceDateTime="2022-06-10T00:00:00Z",
            lotNumber="AAJN12",
        ),
    )
    w["e"] = await create_immunization(
        client,
        {
            "status": "completed",
            "vaccineCode": _vaccine("21", "Varicella"),
            "patient": {
                "identifier": {"system": "urn:pts", "value": "P-9"},
                "display": "External",
            },
            "occurrenceDateTime": "2019",
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
    assert await _keys(client, world, status="completed") == {"a", "d", "e"}
    assert await _keys(client, world, status="not-done,entered-in-error") == {"b", "c"}
    assert await _keys(client, world, status="entered-in-error") == {
        "c"
    }  # the real FHIR code
    assert await _keys(client, world, status=f"{STATUS_SYSTEM}|not-done") == {"b"}
    assert await _keys(client, world, status="http://wrong|completed") == set()
    assert (
        await _keys(client, world, status="|completed") == set()
    )  # a code with no system is not this one
    assert await _keys(client, world, status="nonsense") == set()
    assert await _keys(client, world, **{"status:not": "completed"}) == {"b", "c"}
    assert (
        await _status(client, **{"status:text": "completed"}) == 400
    )  # a plain code has no :text


# ── date ─────────────────────────────────────────────────────────────────────


async def test_date(client, world):
    assert await _keys(client, world, date="2023-01-15") == {"a"}
    assert await _keys(client, world, date="2023") == {"a"}
    assert await _keys(client, world, date="2024") == {"b"}  # 2024-02 lies inside 2024
    assert await _keys(client, world, date="ge2024-01-01") == {"b"}
    assert await _keys(client, world, date="lt2023-01-01") == {"d", "e"}
    assert await _keys(client, world, date="lt2023-01-01,ge2024-01-01") == {
        "b",
        "d",
        "e",
    }
    assert await _keys(
        client, world, date="ge2022-01-01", _id=f"{world['d']},{world['e']}"
    ) == {"d"}
    assert await _keys(client, world, date="sa2023-02-01") == {"b"}
    assert await _keys(client, world, date="eb2020-01-01") == {"e"}
    # a string occurrence is not a date: it never matches, and counts as missing
    assert await _keys(client, world, **{"date:missing": "true"}) == {"c"}
    assert await _keys(client, world, **{"date:missing": "false"}) == {
        "a",
        "b",
        "d",
        "e",
    }


# ── identifier ───────────────────────────────────────────────────────────────


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="IM-A") == {"a"}
    assert await _keys(client, world, identifier=f"{IMMUNIZATION_IDS}|IM-B") == {"b"}
    assert await _keys(client, world, identifier="IM-A,IM-B") == {"a", "b"}
    assert await _keys(client, world, identifier="urn:wrong|IM-A") == set()
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|FILL|IM-A"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|FILL|IM-B"})
        == set()
    )
    assert await _keys(client, world, **{"identifier:text": "immunization"}) == {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


# ── lot-number / series (strings) ────────────────────────────────────────────


async def test_lot_number(client, world):
    assert await _keys(client, world, **{"lot-number": "aajn"}) == {
        "a",
        "d",
    }  # case-insensitive starts-with
    assert await _keys(client, world, **{"lot-number": "AAJN11K"}) == {"a"}
    assert await _keys(client, world, **{"lot-number:exact": "AAJN11K"}) == {"a"}
    assert await _keys(client, world, **{"lot-number:exact": "aajn11k"}) == set()
    assert await _keys(client, world, **{"lot-number:contains": "22"}) == {"b"}
    assert (
        await _keys(client, world, **{"lot-number": "11K"}) == set()
    )  # starts-with, not contains
    assert await _keys(client, world, **{"lot-number:missing": "true"}) == {"c", "e"}
    assert await _status(client, **{"lot-number:text": "x"}) == 400


async def test_series(client, world):
    assert await _keys(client, world, series="2-dose") == {"a"}
    assert await _keys(client, world, series="boost") == {"b"}
    assert await _keys(client, world, **{"series:exact": "Booster"}) == {"b"}
    assert await _keys(client, world, **{"series:exact": "booster"}) == set()
    assert await _keys(client, world, **{"series:contains": "dose"}) == {"a"}
    assert await _keys(client, world, series="2-dose,boost") == {"a", "b"}
    assert await _keys(client, world, **{"series:missing": "true"}) == {"c", "d", "e"}


# ── vaccine-code / status-reason / reason-code / target-disease ──────────────


async def test_vaccine_code(client, world):
    assert await _keys(client, world, **{"vaccine-code": "140"}) == {"a", "d"}
    assert await _keys(client, world, **{"vaccine-code": f"{CVX}|03"}) == {"b"}
    assert await _keys(client, world, **{"vaccine-code": f"{CVX}|"}) == {
        "a",
        "b",
        "d",
        "e",
    }
    assert await _keys(client, world, **{"vaccine-code": "140,21"}) == {"a", "d", "e"}
    assert await _keys(client, world, **{"vaccine-code": "http://wrong|140"}) == set()
    assert await _keys(client, world, **{"vaccine-code:text": "tetanus"}) == {
        "c"
    }  # a text-only concept is found
    assert await _keys(client, world, **{"vaccine-code:text": "influenza"}) == {
        "a",
        "d",
    }  # Coding.display
    assert await _keys(client, world, **{"vaccine-code:not": "140"}) == {"b", "c", "e"}
    assert await _keys(client, world, **{"vaccine-code:missing": "true"}) == set()


async def test_status_reason(client, world):
    assert await _keys(client, world, **{"status-reason": "PATOBJ"}) == {"b"}
    assert await _keys(client, world, **{"status-reason": f"{ACT_REASON}|PATOBJ"}) == {
        "b"
    }
    assert await _keys(client, world, **{"status-reason:text": "patient"}) == {"b"}
    assert await _keys(client, world, **{"status-reason:missing": "true"}) == {
        "a",
        "c",
        "d",
        "e",
    }


async def test_reason_code(client, world):
    assert await _keys(client, world, **{"reason-code": "429060002"}) == {"a"}
    assert await _keys(client, world, **{"reason-code": f"{SCT}|429060002"}) == {"a"}
    assert await _keys(client, world, **{"reason-code:text": "occupational"}) == {"a"}
    assert await _keys(client, world, **{"reason-code:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }


async def test_target_disease(client, world):
    assert await _keys(client, world, **{"target-disease": "6142004"}) == {"a"}
    assert await _keys(client, world, **{"target-disease": f"{SCT}|14189004"}) == {"b"}
    assert await _keys(client, world, **{"target-disease": "6142004,14189004"}) == {
        "a",
        "b",
    }
    assert await _keys(client, world, **{"target-disease:text": "measles"}) == {"b"}
    assert await _keys(client, world, **{"target-disease:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


# ── patient / location / manufacturer ────────────────────────────────────────


async def test_patient(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {
        "a",
        "c",
    }  # one target: a bare id works
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"b", "d"}
    assert await _keys(client, world, patient=f"{world['p1']},{world['p2']}") == {
        "a",
        "b",
        "c",
        "d",
    }
    assert await _keys(client, world, patient="999999") == set()
    assert await _keys(client, world, **{"patient:Patient": str(world["p1"])}) == {
        "a",
        "c",
    }
    assert await _keys(client, world, **{"patient:identifier": "urn:pts|P-9"}) == {"e"}
    assert await _keys(client, world, **{"patient:missing": "false"}) == ALL


async def test_location_and_manufacturer(client, world):
    assert await _keys(client, world, location=str(world["loc"])) == {"a"}
    assert await _keys(client, world, location=f"Location/{world['loc']}") == {"a"}
    assert await _keys(client, world, **{"location:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }
    assert await _keys(client, world, manufacturer=str(world["org"])) == {"a"}
    assert await _keys(client, world, manufacturer=f"Organization/{world['org']}") == {
        "a"
    }
    assert await _keys(client, world, **{"manufacturer:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }
    assert await _keys(client, world, location="999999") == set()


# ── performer ────────────────────────────────────────────────────────────────


async def test_performer_is_multi_target(client, world):
    assert (
        await _status(client, performer=str(world["pr"])) == 400
    )  # a bare id is ambiguous
    assert await _keys(client, world, performer=f"Practitioner/{world['pr']}") == {"a"}
    assert await _keys(
        client, world, **{"performer:Practitioner": str(world["pr"])}
    ) == {"a"}
    assert await _keys(client, world, performer=f"Organization/{world['org']}") == {"a"}
    assert await _keys(
        client, world, performer=f"PractitionerRole/{world['role']}"
    ) == {"b"}
    assert (
        await _keys(client, world, performer=f"Practitioner/{world['org']}") == set()
    )  # the type is part of the match
    assert await _keys(client, world, **{"performer:identifier": "urn:who|W-1"}) == {
        "c"
    }
    assert await _keys(client, world, **{"performer:missing": "true"}) == {"d", "e"}


# ── reaction / reaction-date ─────────────────────────────────────────────────


async def test_reaction(client, world):
    assert await _keys(client, world, reaction="160001") == {
        "a"
    }  # one target: a bare id works
    assert await _keys(client, world, reaction="Observation/160009") == {"b"}
    assert await _keys(client, world, reaction="160001,160009") == {"a", "b"}
    assert await _keys(client, world, **{"reaction:missing": "true"}) == {"c", "d", "e"}
    assert await _keys(client, world, reaction="999999") == set()


async def test_reaction_date(client, world):
    assert await _keys(client, world, **{"reaction-date": "2023-01-16"}) == {"a"}
    assert await _keys(client, world, **{"reaction-date": "ge2024-01-01"}) == {"b"}
    assert await _keys(client, world, **{"reaction-date": "lt2024-01-01"}) == {"a"}
    assert await _keys(client, world, **{"reaction-date:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


# ── reason-reference ─────────────────────────────────────────────────────────


async def test_reason_reference_is_multi_target(client, world):
    assert (
        await _status(client, **{"reason-reference": str(world["cond"])}) == 400
    )  # a bare id is ambiguous
    assert await _keys(
        client, world, **{"reason-reference": f"Condition/{world['cond']}"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"reason-reference:Condition": str(world["cond"])}
    ) == {"a"}
    assert await _keys(
        client, world, **{"reason-reference": f"DiagnosticReport/{world['rep']}"}
    ) == {"a"}
    assert await _keys(client, world, **{"reason-reference": "Observation/160003"}) == {
        "c"
    }  # not a resource here
    assert await _keys(client, world, **{"reason-reference:Observation": "160003"}) == {
        "c"
    }
    assert await _keys(client, world, **{"reason-reference:missing": "true"}) == {
        "b",
        "d",
        "e",
    }


# ── chaining ─────────────────────────────────────────────────────────────────


async def test_chains(client, world):
    assert await _keys(client, world, **{"patient.family": "Windsor"}) == {"a", "c"}
    assert await _keys(client, world, **{"patient.name": "Ben"}) == {"b", "d"}
    assert await _keys(client, world, **{"location.name": "North"}) == {"a"}
    assert await _keys(client, world, **{"manufacturer.name": "Providing"}) == {"a"}
    assert await _keys(
        client, world, **{"performer:Practitioner.family": "Careful"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"performer:Organization.name": "Providing"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"reason-reference:Condition.patient": str(world["p1"])}
    ) == {"a"}
    assert await _keys(
        client, world, **{"reason-reference:DiagnosticReport.status": "final"}
    ) == {"a"}
    assert (
        await _keys(
            client, world, **{"reason-reference:DiagnosticReport.status": "amended"}
        )
        == set()
    )


async def test_bad_chains_are_400(client, world):
    assert await _status(client, **{"patient.nonsense": "x"}) == 400
    assert (
        await _status(client, **{"performer.family": "x"}) == 400
    )  # an untyped multi-target cannot be chained
    assert (
        await _status(client, **{"reason-reference:DocumentReference.x": "x"}) == 400
    )  # not a target of reasonReference
    assert (
        await _status(client, **{"vaccine-code.x": "y"}) == 400
    )  # a token cannot be chained through
    assert await _status(client, **{"lot-number.x": "y"}) == 400


# ── _sort / _count / _offset / _total ────────────────────────────────────────


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "date",
        "identifier",
        "location",
        "lot-number",
        "manufacturer",
        "patient",
        "performer",
        "reaction",
        "reaction-date",
        "reason-code",
        "reason-reference",
        "series",
        "status",
        "status-reason",
        "target-disease",
        "vaccine-code",
        "_id",
    ):
        assert (await _search(client, _sort=key))["total"] == 5, key
    assert await _status(client, _sort="dose") == 400


async def test_sort_by_date_and_lot_number(client, world):
    async def ids(**params):
        return [
            int(e["resource"]["id"]) for e in (await _search(client, **params))["entry"]
        ]

    assert await ids(**{"date:missing": "false", "_sort": "date"}) == [
        world["e"],
        world["d"],
        world["a"],
        world["b"],
    ]
    assert await ids(**{"date:missing": "false", "_sort": "-date"}) == [
        world["b"],
        world["a"],
        world["d"],
        world["e"],
    ]
    assert await ids(**{"lot-number:missing": "false", "_sort": "lot-number"}) == [
        world["a"],
        world["d"],
        world["b"],
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
    assert resource["status"] == "completed"
    assert "performer" not in resource and "lotNumber" not in resource


# ── _include / _revinclude ───────────────────────────────────────────────────


async def test_include_patient_location_manufacturer(client, world):
    ids = f"{world['a']},{world['b']},{world['e']}"
    bundle = await _search(client, _id=ids, _include="Immunization:patient")
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }  # a logical patient adds nothing
    bundle = await _search(client, _id=ids, _include="Immunization:location")
    assert _of_type(bundle, "Location", "include") == {str(world["loc"])}
    bundle = await _search(client, _id=ids, _include="Immunization:manufacturer")
    assert _of_type(bundle, "Organization", "include") == {str(world["org"])}


async def test_include_performer_brings_in_every_modeled_type(client, world):
    ids = f"{world['a']},{world['b']},{world['c']}"
    bundle = await _search(client, _id=ids, _include="Immunization:performer")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "Organization", "include") == {str(world["org"])}
    assert _of_type(bundle, "PractitionerRole", "include") == {
        str(world["role"])
    }  # a logical performer adds nothing
    bundle = await _search(
        client, _id=ids, _include="Immunization:performer:Organization"
    )
    assert _of_type(bundle, "Organization", "include") == {str(world["org"])}
    assert _of_type(bundle, "Practitioner", "include") == set()


async def test_include_reason_reference(client, world):
    ids = f"{world['a']},{world['c']}"
    bundle = await _search(client, _id=ids, _include="Immunization:reason-reference")
    assert _of_type(bundle, "Condition", "include") == {str(world["cond"])}
    assert _of_type(bundle, "DiagnosticReport", "include") == {
        str(world["rep"])
    }  # an Observation adds nothing
    bundle = await _search(
        client, _id=ids, _include="Immunization:reason-reference:Condition"
    )
    assert _of_type(bundle, "DiagnosticReport", "include") == set()


async def test_revinclude_immunizations_on_the_resources_they_point_at(client, world):
    bundle = await _other(
        client, "patients", _id=str(world["p1"]), _revinclude="Immunization:patient"
    )
    assert _of_type(bundle, "Immunization", "include") == {
        str(world["a"]),
        str(world["c"]),
    }
    bundle = await _other(
        client, "locations", _id=str(world["loc"]), _revinclude="Immunization:location"
    )
    assert _of_type(bundle, "Immunization", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "practitioners",
        _id=str(world["pr"]),
        _revinclude="Immunization:performer",
    )
    assert _of_type(bundle, "Immunization", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "practitioner-roles",
        _id=str(world["role"]),
        _revinclude="Immunization:performer",
    )
    assert _of_type(bundle, "Immunization", "include") == {str(world["b"])}
    bundle = await _other(
        client,
        "conditions",
        _id=str(world["cond"]),
        _revinclude="Immunization:reason-reference",
    )
    assert _of_type(bundle, "Immunization", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "diagnostic-reports",
        _id=str(world["rep"]),
        _revinclude="Immunization:reason-reference",
    )
    assert _of_type(bundle, "Immunization", "include") == {str(world["a"])}


async def test_revinclude_is_tenant_scoped(client, other_client):
    from app.auth.dependencies import get_current_user
    from app.main import app
    from tests.conftest import make_test_user
    from tests.integration.immunization.conftest import IMMUNIZATION_PERMS

    def as_user(**kw):
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=IMMUNIZATION_PERMS, **kw
        )

    as_user()
    mine = await create_patient(client)
    await create_immunization(client, immunization_body(mine))
    as_user(sub="u-other", org_id="org-other")
    try:
        # The other org cannot see the patient, so nothing reaches its immunizations.
        bundle = await _other(
            other_client, "patients", _id=str(mine), _revinclude="Immunization:patient"
        )
        assert bundle["total"] == 0 and "entry" not in bundle
        theirs = await create_patient(other_client)
        bundle = await _other(
            other_client,
            "patients",
            _id=str(theirs),
            _revinclude="Immunization:patient",
        )
        assert _of_type(bundle, "Immunization", "include") == set()
    finally:
        as_user()


# ── combination rules / lenient vs strict ────────────────────────────────────


async def test_params_are_anded(client, world):
    assert await _keys(
        client, world, status="completed", **{"vaccine-code": "140"}
    ) == {"a", "d"}
    assert (
        await _keys(client, world, status="completed", **{"vaccine-code": "03"})
        == set()
    )
    assert await _keys(
        client, world, patient=str(world["p1"]), status="entered-in-error"
    ) == {"c"}
    assert await _keys(client, world, **{"vaccine-code": "140"}, date="ge2023") == {"a"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"status:above": "x"}) == 400
    assert await _status(client, **{"patient:text": "x"}) == 400
    assert await _status(client, **{"date:exact": "2020"}) == 400
    assert await _status(client, **{"series:below": "x"}) == 400


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
        BASE + "/_search", data={"status": "not-done", "patient": str(world["p2"])}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, status="not-done")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/immunizations/{world['b']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "Immunization"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
