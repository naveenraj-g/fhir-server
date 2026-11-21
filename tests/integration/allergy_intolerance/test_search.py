"""FHIR R4 search over AllergyIntolerance (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/allergyintolerance.html#search).

One block per search parameter — `clinical-status`, `verification-status`,
`code`, `manifestation` and `route` are tokens on CodeableConcepts, `category`,
`severity`, `type` and `criticality` are tokens on plain codes, `identifier` is a
token on an Identifier, `date`/`last-date`/`onset` are dateTimes held as the range
they cover, `patient` is a single-target reference and `recorder`/`asserter` are
multi-target references (a bare id is ambiguous) — then chaining,
`_include`/`_revinclude` in both directions, result parameters, combination
rules, lenient vs strict handling and POST _search.
"""

import pytest

from tests.integration.allergy_intolerance.support import (
    API,
    BASE,
    AI_IDS,
    CATEGORY,
    CLIN,
    CRITICALITY,
    SCT,
    SEVERITY,
    TYPE_SYSTEM,
    VERIF,
    allergy_body,
    clinical,
    create_allergy_intolerance,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_related_person,
    related_person_body,
    verification,
)

KEYS = ("a", "b", "c", "d")
ALL = set(KEYS)
V2_0203 = "http://terminology.hl7.org/CodeSystem/v2-0203"


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
    """Two patients, a practitioner, a practitioner role and a related person, plus
    four allergies with distinct, searchable values. Returns {key: id}."""
    w = {}
    w["p1"] = await create_patient(
        client, {"active": True, "name": [{"family": "Windsor", "given": ["Anna"]}]}
    )
    w["p2"] = await create_patient(
        client, {"active": True, "name": [{"family": "Fairfax", "given": ["Ben"]}]}
    )
    w["pr"] = await create_practitioner(client)  # family "Careful"
    w["role"] = await create_practitioner_role(client)
    w["rp"] = await create_related_person(
        client,
        {
            **related_person_body(w["p1"]),
            "name": [{"family": "Gray", "given": ["Gail"]}],
        },
    )
    w["a"] = await create_allergy_intolerance(
        client,
        allergy_body(
            w["p1"],
            identifier=[
                {
                    "system": AI_IDS,
                    "value": "AI-A",
                    "type": {
                        "coding": [{"system": V2_0203, "code": "PRN"}],
                        "text": "Allergy id",
                    },
                }
            ],
            clinicalStatus=clinical("active"),
            verificationStatus=verification("confirmed"),
            type="allergy",
            category=["food", "environment"],
            criticality="high",
            code={
                "coding": [
                    {"system": SCT, "code": "227493005", "display": "Cashew nuts"}
                ]
            },
            recordedDate="2026-01-15T10:00:00Z",
            lastOccurrence="2026-03-01",
            recorder={"reference": f"Practitioner/{w['pr']}"},
            asserter={"reference": f"Patient/{w['p1']}"},
            reaction=[
                {
                    "substance": {
                        "coding": [
                            {"system": SCT, "code": "387207008", "display": "Ibuprofen"}
                        ]
                    },
                    "manifestation": [
                        {
                            "coding": [
                                {
                                    "system": SCT,
                                    "code": "64305001",
                                    "display": "Urticaria",
                                }
                            ]
                        },
                        {"text": "Skin rash"},
                    ],
                    "onset": "2026-01-15T09:40:00Z",
                    "severity": "severe",
                    "exposureRoute": {
                        "coding": [
                            {"system": SCT, "code": "26643006", "display": "Oral route"}
                        ]
                    },
                }
            ],
        ),
    )
    w["b"] = await create_allergy_intolerance(
        client,
        allergy_body(
            w["p2"],
            identifier=[{"system": AI_IDS, "value": "AI-B"}],
            clinicalStatus=clinical("inactive"),
            verificationStatus=verification("unconfirmed"),
            type="intolerance",
            category=["medication"],
            criticality="low",
            code={
                "coding": [
                    {"system": SCT, "code": "91936005", "display": "Penicillin allergy"}
                ]
            },
            recordedDate="2025-06",
            recorder={"reference": f"RelatedPerson/{w['rp']}"},
            asserter={"reference": f"Practitioner/{w['pr']}"},
            reaction=[
                {
                    "manifestation": [
                        {
                            "coding": [
                                {
                                    "system": SCT,
                                    "code": "422587007",
                                    "display": "Nausea",
                                }
                            ]
                        }
                    ],
                    "onset": "2025-06-02",
                    "severity": "mild",
                },
                {
                    "manifestation": [{"text": "Bloating"}],
                    "onset": "2025-07",
                    "severity": "moderate",
                },
            ],
        ),
    )
    w["c"] = await create_allergy_intolerance(
        client,
        allergy_body(
            w["p1"],
            clinicalStatus=clinical("resolved"),
            verificationStatus=verification("refuted"),
            type="allergy",
            category=["biologic"],
            criticality="unable-to-assess",
            code={"text": "Latex"},
            recordedDate="2024",
            recorder={"reference": f"PractitionerRole/{w['role']}"},
            asserter={"identifier": {"system": "urn:who", "value": "W-1"}},
        ),
    )
    w["d"] = await create_allergy_intolerance(
        client,
        {
            "patient": {
                "identifier": {"system": "urn:pts", "value": "P-9"},
                "display": "External",
            }
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


# ── _id / _lastUpdated ───────────────────────────────────────────────────────


async def test_id(client, world):
    assert await _keys(client, world, _id=str(world["a"])) == {"a"}
    assert await _keys(client, world, _id="999999") == set()
    assert await _keys(client, world, **{"_id:not": str(world["a"])}) == ALL - {"a"}


async def test_last_updated(client, world):
    assert await _keys(client, world, _lastUpdated="ge2020-01-01") == ALL
    assert await _keys(client, world, _lastUpdated="lt2020-01-01") == set()


# ── clinical-status / verification-status ────────────────────────────────────


async def test_clinical_status(client, world):
    assert await _keys(client, world, **{"clinical-status": "active"}) == {"a"}
    assert await _keys(client, world, **{"clinical-status": f"{CLIN}|resolved"}) == {
        "c"
    }
    assert await _keys(client, world, **{"clinical-status": "active,inactive"}) == {
        "a",
        "b",
    }
    assert await _keys(client, world, **{"clinical-status": f"{CLIN}|"}) == {
        "a",
        "b",
        "c",
    }
    assert (
        await _keys(client, world, **{"clinical-status": "http://wrong|active"})
        == set()
    )
    assert await _keys(client, world, **{"clinical-status": "nonsense"}) == set()
    assert await _keys(client, world, **{"clinical-status:not": "active"}) == {
        "b",
        "c",
        "d",
    }  # includes "no value"
    assert await _keys(client, world, **{"clinical-status:missing": "true"}) == {"d"}


async def test_verification_status(client, world):
    assert await _keys(client, world, **{"verification-status": "confirmed"}) == {"a"}
    assert await _keys(
        client, world, **{"verification-status": f"{VERIF}|refuted"}
    ) == {"c"}
    assert await _keys(
        client, world, **{"verification-status": "unconfirmed,refuted"}
    ) == {"b", "c"}
    assert (
        await _keys(client, world, **{"verification-status": "http://wrong|confirmed"})
        == set()
    )
    assert await _keys(client, world, **{"verification-status:missing": "true"}) == {
        "d"
    }


# ── type / criticality / category (plain codes) ──────────────────────────────


async def test_type(client, world):
    assert await _keys(client, world, type="allergy") == {"a", "c"}
    assert await _keys(client, world, type="intolerance") == {"b"}
    assert await _keys(client, world, type=f"{TYPE_SYSTEM}|allergy") == {"a", "c"}
    assert await _keys(client, world, type="http://wrong|allergy") == set()
    assert (
        await _keys(client, world, type="|allergy") == set()
    )  # a code with no system is not this one
    assert await _keys(client, world, type="robot") == set()
    assert await _keys(client, world, **{"type:not": "allergy"}) == {"b", "d"}
    assert await _keys(client, world, **{"type:missing": "true"}) == {"d"}
    assert (
        await _status(client, **{"type:text": "allergy"}) == 400
    )  # a plain code has no :text


async def test_criticality(client, world):
    assert await _keys(client, world, criticality="high") == {"a"}
    assert await _keys(client, world, criticality="low,high") == {"a", "b"}
    assert await _keys(
        client, world, criticality=f"{CRITICALITY}|unable-to-assess"
    ) == {"c"}
    assert await _keys(client, world, criticality="http://wrong|high") == set()
    assert await _keys(client, world, criticality="extreme") == set()
    assert await _keys(client, world, **{"criticality:not": "high"}) == {"b", "c", "d"}
    assert await _keys(client, world, **{"criticality:missing": "true"}) == {"d"}


async def test_category(client, world):
    assert await _keys(client, world, category="food") == {"a"}
    assert await _keys(client, world, category="environment") == {
        "a"
    }  # a has two categories
    assert await _keys(client, world, category="medication") == {"b"}
    assert await _keys(client, world, category="food,biologic") == {"a", "c"}
    assert await _keys(client, world, category=f"{CATEGORY}|medication") == {"b"}
    assert await _keys(client, world, category="|food") == set()
    assert await _keys(client, world, category="http://wrong|food") == set()
    assert await _keys(client, world, **{"category:not": "food"}) == {"b", "c", "d"}
    assert await _keys(client, world, **{"category:missing": "true"}) == {"d"}


# ── code (code + reaction.substance) ─────────────────────────────────────────


async def test_code_covers_code_and_reaction_substance(client, world):
    assert await _keys(client, world, code="227493005") == {
        "a"
    }  # AllergyIntolerance.code
    assert await _keys(client, world, code="387207008") == {
        "a"
    }  # AllergyIntolerance.reaction.substance
    assert await _keys(client, world, code="91936005") == {"b"}
    assert await _keys(client, world, code="227493005,91936005") == {"a", "b"}
    assert await _keys(client, world, code=f"{SCT}|") == {"a", "b"}
    assert await _keys(client, world, code="http://wrong|227493005") == set()
    assert await _keys(client, world, code="000") == set()


async def test_code_text_not_and_missing(client, world):
    assert await _keys(client, world, **{"code:text": "latex"}) == {
        "c"
    }  # a text-only concept is found
    assert await _keys(client, world, **{"code:text": "penicillin"}) == {
        "b"
    }  # Coding.display
    assert await _keys(client, world, **{"code:text": "ibupro"}) == {
        "a"
    }  # a reaction substance's display
    assert await _keys(client, world, **{"code:not": "227493005"}) == {"b", "c", "d"}
    assert await _keys(client, world, **{"code:missing": "true"}) == {"d"}


# ── identifier ───────────────────────────────────────────────────────────────


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="AI-A") == {"a"}
    assert await _keys(client, world, identifier=f"{AI_IDS}|AI-B") == {"b"}
    assert await _keys(client, world, identifier="AI-A,AI-B") == {"a", "b"}
    assert await _keys(client, world, identifier="urn:other|AI-A") == set()


async def test_identifier_text_of_type_not_and_missing(client, world):
    assert await _keys(client, world, **{"identifier:text": "allergy"}) == {"a"}
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|PRN|AI-A"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|PRN|AI-B"})
        == set()
    )
    assert await _keys(client, world, **{"identifier:not": "AI-A"}) == ALL - {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {"c", "d"}


# ── manifestation / route / severity (reaction.*) ────────────────────────────


async def test_manifestation(client, world):
    assert await _keys(client, world, manifestation="64305001") == {"a"}
    assert await _keys(client, world, manifestation="422587007") == {"b"}
    assert await _keys(client, world, manifestation=f"{SCT}|") == {"a", "b"}
    assert await _keys(client, world, manifestation="http://wrong|64305001") == set()
    assert await _keys(client, world, **{"manifestation:text": "urtic"}) == {
        "a"
    }  # Coding.display
    assert await _keys(client, world, **{"manifestation:text": "skin"}) == {
        "a"
    }  # a text-only manifestation
    assert await _keys(client, world, **{"manifestation:text": "bloat"}) == {
        "b"
    }  # the second reaction
    assert await _keys(client, world, **{"manifestation:missing": "true"}) == {"c", "d"}


async def test_route(client, world):
    assert await _keys(client, world, route="26643006") == {"a"}
    assert await _keys(client, world, route=f"{SCT}|26643006") == {"a"}
    assert await _keys(client, world, route="http://wrong|26643006") == set()
    assert await _keys(client, world, **{"route:text": "oral"}) == {"a"}
    assert await _keys(client, world, **{"route:missing": "true"}) == {"b", "c", "d"}


async def test_severity(client, world):
    assert await _keys(client, world, severity="severe") == {"a"}
    assert await _keys(client, world, severity="mild") == {"b"}
    assert await _keys(client, world, severity="moderate") == {
        "b"
    }  # b has two reactions
    assert await _keys(client, world, severity="severe,mild") == {"a", "b"}
    assert await _keys(client, world, severity=f"{SEVERITY}|severe") == {"a"}
    assert await _keys(client, world, severity="http://wrong|severe") == set()
    assert await _keys(client, world, severity="dire") == set()
    assert await _keys(client, world, **{"severity:not": "severe"}) == {"b", "c", "d"}
    assert await _keys(client, world, **{"severity:missing": "true"}) == {"c", "d"}


# ── date / last-date / onset (a dateTime held as the range it covers) ─────────


async def test_date_precision(client, world):
    assert await _keys(client, world, date="2026-01-15") == {
        "a"
    }  # the day contains the instant
    assert await _keys(client, world, date="2025") == {"b"}  # the year contains 2025-06
    assert await _keys(client, world, date="2025-06") == {"b"}
    assert await _keys(client, world, date="2024") == {"c"}
    assert (
        await _keys(client, world, date="2025-06-10") == set()
    )  # a day inside the month does not equal it


async def test_date_prefixes_and_missing(client, world):
    assert await _keys(client, world, date="ge2025-06") == {"a", "b"}
    assert await _keys(client, world, date="lt2025") == {"c"}
    assert await _keys(client, world, date=["ge2024", "lt2026"]) == {"b", "c"}
    assert await _keys(client, world, **{"date:missing": "true"}) == {"d"}
    assert await _status(client, date="banana") == 400


async def test_last_date(client, world):
    assert await _keys(client, world, **{"last-date": "2026-03-01"}) == {"a"}
    assert await _keys(client, world, **{"last-date": "ge2026"}) == {"a"}
    assert await _keys(client, world, **{"last-date": "lt2026"}) == set()
    assert await _keys(client, world, **{"last-date:missing": "true"}) == {
        "b",
        "c",
        "d",
    }


async def test_onset_reads_every_reaction(client, world):
    assert await _keys(client, world, onset="2026-01-15") == {"a"}
    assert await _keys(client, world, onset="2025-06-02") == {"b"}
    assert await _keys(client, world, onset="2025-07") == {"b"}  # the second reaction
    assert await _keys(client, world, onset="2025") == {"b"}
    assert await _keys(client, world, onset="ge2026") == {"a"}
    assert await _keys(client, world, onset="lt2025-07") == {"b"}
    assert await _keys(client, world, **{"onset:missing": "true"}) == {"c", "d"}


# ── patient ──────────────────────────────────────────────────────────────────


async def test_patient(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {
        "a",
        "c",
    }  # a bare id works: one target
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"b"}
    assert await _keys(client, world, patient=f"{world['p1']},{world['p2']}") == {
        "a",
        "b",
        "c",
    }
    assert await _keys(client, world, **{"patient:Patient": str(world["p1"])}) == {
        "a",
        "c",
    }
    assert await _keys(client, world, patient="999999") == set()


async def test_patient_identifier_and_missing(client, world):
    assert await _keys(client, world, **{"patient:identifier": "urn:pts|P-9"}) == {"d"}
    assert await _keys(client, world, **{"patient:missing": "true"}) == set()
    assert await _keys(client, world, **{"patient:missing": "false"}) == ALL


async def test_patient_chain(client, world):
    assert await _keys(client, world, **{"patient.family": "Windsor"}) == {"a", "c"}
    assert await _keys(client, world, **{"patient.name": "Ben"}) == {"b"}
    assert await _keys(client, world, **{"patient.family": "Nobody"}) == set()


# ── recorder / asserter (multi-target) ───────────────────────────────────────


@pytest.mark.parametrize("param", ["recorder", "asserter"])
async def test_bare_id_on_a_multi_target_reference_is_400(client, world, param):
    assert await _status(client, **{param: str(world["pr"])}) == 400


async def test_recorder(client, world):
    assert await _keys(client, world, recorder=f"Practitioner/{world['pr']}") == {"a"}
    assert await _keys(
        client, world, **{"recorder:RelatedPerson": str(world["rp"])}
    ) == {"b"}
    assert await _keys(client, world, recorder=f"PractitionerRole/{world['role']}") == {
        "c"
    }
    assert await _keys(
        client,
        world,
        recorder=f"Practitioner/{world['pr']},RelatedPerson/{world['rp']}",
    ) == {"a", "b"}
    # The type is part of the match: that number is a Patient, not a Practitioner.
    assert await _keys(client, world, recorder=f"Practitioner/{world['p1']}") == set()
    assert await _keys(client, world, **{"recorder:missing": "true"}) == {"d"}


async def test_asserter(client, world):
    assert await _keys(client, world, asserter=f"Patient/{world['p1']}") == {"a"}
    assert await _keys(
        client, world, **{"asserter:Practitioner": str(world["pr"])}
    ) == {"b"}
    assert await _keys(client, world, **{"asserter:identifier": "urn:who|W-1"}) == {"c"}
    assert await _keys(client, world, asserter=f"Practitioner/{world['p1']}") == set()
    assert await _keys(client, world, **{"asserter:missing": "true"}) == {
        "d"
    }  # c has a logical reference
    assert await _keys(client, world, **{"asserter:missing": "false"}) == {
        "a",
        "b",
        "c",
    }


async def test_recorder_and_asserter_chains(client, world):
    assert await _keys(
        client, world, **{"recorder:Practitioner.family": "Careful"}
    ) == {"a"}
    assert await _keys(client, world, **{"recorder:RelatedPerson.name": "Gray"}) == {
        "b"
    }
    assert await _keys(
        client, world, **{"asserter:Practitioner.family": "Careful"}
    ) == {"b"}
    assert await _keys(client, world, **{"asserter:Patient.family": "Windsor"}) == {"a"}
    assert await _keys(client, world, **{"asserter:Patient.family": "Nobody"}) == set()


async def test_bad_chains_are_400(client, world):
    assert await _status(client, **{"patient.nonsense": "x"}) == 400
    assert (
        await _status(client, **{"recorder.family": "x"}) == 400
    )  # an untyped multi-target cannot be chained
    assert (
        await _status(client, **{"recorder:Organization.name": "x"}) == 400
    )  # not a target of recorder
    assert (
        await _status(client, **{"code.x": "y"}) == 400
    )  # a token cannot be chained through
    assert await _status(client, **{"identifier.x": "y"}) == 400


# ── _sort / _count / _offset / _total ────────────────────────────────────────


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "asserter",
        "category",
        "clinical-status",
        "code",
        "criticality",
        "date",
        "identifier",
        "last-date",
        "manifestation",
        "onset",
        "patient",
        "recorder",
        "route",
        "severity",
        "type",
        "verification-status",
        "_id",
    ):
        assert (await _search(client, _sort=key))["total"] == 4, key
    assert await _status(client, _sort="note") == 400


async def test_sort_by_date_and_criticality(client, world):
    async def ids(**params):
        return [
            int(e["resource"]["id"]) for e in (await _search(client, **params))["entry"]
        ]

    assert await ids(**{"date:missing": "false", "_sort": "date"}) == [
        world["c"],
        world["b"],
        world["a"],
    ]
    assert await ids(**{"date:missing": "false", "_sort": "-date"}) == [
        world["a"],
        world["b"],
        world["c"],
    ]
    assert await ids(**{"criticality:missing": "false", "_sort": "criticality"}) == [
        world["a"],
        world["b"],
        world["c"],
    ]


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
    resource = (await _search(client, _elements="criticality", _id=str(world["a"])))[
        "entry"
    ][0]["resource"]
    assert resource["criticality"] == "high"
    assert "reaction" not in resource and "note" not in resource


# ── _include / _revinclude ───────────────────────────────────────────────────


async def test_include_patient(client, world):
    bundle = await _search(
        client, _id=str(world["a"]), _include="AllergyIntolerance:patient"
    )
    assert _of_type(bundle, "Patient", "include") == {str(world["p1"])}


async def test_include_patient_is_deduplicated_and_skips_non_resources(client, world):
    bundle = await _search(
        client,
        _id=f"{world['a']},{world['c']},{world['d']}",
        _include="AllergyIntolerance:patient",
    )
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"])
    }  # d points elsewhere
    assert (
        sum(1 for e in bundle["entry"] if e["resource"]["resourceType"] == "Patient")
        == 1
    )


async def test_include_recorder_and_asserter_bring_in_every_modeled_type(client, world):
    everything = f"{world['a']},{world['b']},{world['c']}"
    bundle = await _search(
        client, _id=everything, _include="AllergyIntolerance:recorder"
    )
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "RelatedPerson", "include") == {str(world["rp"])}
    assert _of_type(bundle, "PractitionerRole", "include") == {str(world["role"])}
    bundle = await _search(
        client, _id=everything, _include="AllergyIntolerance:asserter"
    )
    assert _of_type(bundle, "Patient", "include") == {str(world["p1"])}
    assert _of_type(bundle, "Practitioner", "include") == {
        str(world["pr"])
    }  # c's logical asserter adds nothing


async def test_include_with_a_type_narrows_it(client, world):
    everything = f"{world['a']},{world['b']},{world['c']}"
    bundle = await _search(
        client, _id=everything, _include="AllergyIntolerance:asserter:Patient"
    )
    assert _of_type(bundle, "Patient", "include") == {str(world["p1"])}
    assert _of_type(bundle, "Practitioner", "include") == set()
    bundle = await _search(
        client, _id=everything, _include="AllergyIntolerance:recorder:RelatedPerson"
    )
    assert _of_type(bundle, "RelatedPerson", "include") == {str(world["rp"])}
    assert _of_type(bundle, "Practitioner", "include") == set()


async def _other(client, path, **params) -> dict:
    resp = await client.get(f"{API}/{path}/", params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_revinclude_allergies_on_patients(client, world):
    bundle = await _other(
        client,
        "patients",
        _id=str(world["p2"]),
        _revinclude="AllergyIntolerance:patient",
    )
    assert _of_type(bundle, "AllergyIntolerance", "include") == {str(world["b"])}
    bundle = await _other(
        client,
        "patients",
        _id=f"{world['p1']},{world['p2']}",
        _revinclude="AllergyIntolerance:patient",
    )
    assert _of_type(bundle, "AllergyIntolerance", "include") == {
        str(world["a"]),
        str(world["b"]),
        str(world["c"]),
    }
    # Patient is also an allowed asserter (a's asserter is p1).
    bundle = await _other(
        client,
        "patients",
        _id=str(world["p1"]),
        _revinclude="AllergyIntolerance:asserter",
    )
    assert _of_type(bundle, "AllergyIntolerance", "include") == {str(world["a"])}


async def test_revinclude_recorder_and_asserter_on_the_other_actor_types(client, world):
    bundle = await _other(
        client,
        "practitioners",
        _id=str(world["pr"]),
        _revinclude="AllergyIntolerance:recorder",
    )
    assert _of_type(bundle, "AllergyIntolerance", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "practitioners",
        _id=str(world["pr"]),
        _revinclude="AllergyIntolerance:asserter",
    )
    assert _of_type(bundle, "AllergyIntolerance", "include") == {str(world["b"])}
    bundle = await _other(
        client,
        "practitioner-roles",
        _id=str(world["role"]),
        _revinclude="AllergyIntolerance:recorder",
    )
    assert _of_type(bundle, "AllergyIntolerance", "include") == {str(world["c"])}
    bundle = await _other(
        client,
        "related-persons",
        _id=str(world["rp"]),
        _revinclude="AllergyIntolerance:recorder",
    )
    assert _of_type(bundle, "AllergyIntolerance", "include") == {str(world["b"])}


async def test_revinclude_is_tenant_scoped(client, other_client):
    from app.auth.dependencies import get_current_user
    from app.main import app
    from tests.conftest import make_test_user
    from tests.integration.allergy_intolerance.conftest import ALLERGY_PERMS

    def as_user(**kw):
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=ALLERGY_PERMS, **kw
        )

    as_user()
    mine = await create_patient(client)
    await create_allergy_intolerance(client, allergy_body(mine))
    as_user(sub="u-other", org_id="org-other")
    try:
        # The other org cannot see the patient, so nothing reaches its allergies.
        bundle = await _other(
            other_client,
            "patients",
            _id=str(mine),
            _revinclude="AllergyIntolerance:patient",
        )
        assert bundle["total"] == 0 and "entry" not in bundle
        theirs = await create_patient(other_client)
        bundle = await _other(
            other_client,
            "patients",
            _id=str(theirs),
            _revinclude="AllergyIntolerance:patient",
        )
        assert _of_type(bundle, "AllergyIntolerance", "include") == set()
    finally:
        as_user()


# ── combination rules / lenient vs strict ────────────────────────────────────


async def test_params_are_anded(client, world):
    assert await _keys(client, world, type="allergy", criticality="high") == {"a"}
    assert await _keys(client, world, type="allergy", criticality="low") == set()
    assert await _keys(
        client, world, patient=str(world["p1"]), **{"clinical-status": "resolved"}
    ) == {"c"}
    assert await _keys(client, world, category="food", severity="severe") == {"a"}


async def test_repeated_param_is_and(client, world):
    assert await _keys(client, world, category=["food", "environment"]) == {
        "a"
    }  # one row each, both present
    assert await _keys(client, world, category=["food", "medication"]) == set()


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"criticality:above": "x"}) == 400
    assert await _status(client, **{"patient:text": "x"}) == 400
    assert await _status(client, **{"date:exact": "2026"}) == 400


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
        BASE + "/_search", data={"type": "intolerance", "patient": str(world["p2"])}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, type="intolerance")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/allergy-intolerances/{world['b']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "AllergyIntolerance"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
