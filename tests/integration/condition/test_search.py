"""FHIR R4 search over Condition (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/condition.html#search).

One block per search parameter — eight CodeableConcept tokens (`clinical-status`,
`verification-status`, `category`, `severity`, `code`, `body-site`, `evidence`,
`stage`), `identifier`, three date searches that also read a Period (`onset-date`,
`abatement-date`, `recorded-date`), two quantity searches over an Age *or* a Range
(`onset-age`, `abatement-age`), two string searches (`onset-info`,
`abatement-string`), the single-target references (`encounter`, `patient`) and the
multi-target ones (`subject`, `asserter`, `evidence-detail`) — then chaining,
`_include`/`_revinclude` in both directions, result parameters, combination rules,
lenient vs strict handling and POST _search.
"""

import pytest

from tests.integration.condition.support import (
    API,
    BASE,
    CLIN,
    COND_IDS,
    SCT,
    UCUM,
    V2_0203,
    VERIF,
    appointment_body,
    category,
    clinical,
    condition_body,
    create_appointment,
    create_condition,
    create_encounter,
    create_patient,
    create_practitioner,
    create_related_person,
    encounter_body,
    related_person_body,
    verification,
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


def _age(value, unit="years"):
    return {"value": value, "unit": unit, "system": UCUM, "code": "a"}


@pytest.fixture
async def world(client):
    """Two patients, a practitioner, a related person and two encounters, plus five
    conditions with distinct, searchable values. Returns {key: id}."""
    w = {}
    w["p1"] = await create_patient(
        client, {"active": True, "name": [{"family": "Windsor", "given": ["Anna"]}]}
    )
    w["p2"] = await create_patient(
        client, {"active": True, "name": [{"family": "Fairfax", "given": ["Ben"]}]}
    )
    w["pr"] = await create_practitioner(client)  # family "Careful"
    w["rp"] = await create_related_person(
        client,
        {
            **related_person_body(w["p1"]),
            "name": [{"family": "Gray", "given": ["Gail"]}],
        },
    )
    w["enc1"] = await create_encounter(client, encounter_body())
    w["enc2"] = await create_encounter(client, encounter_body())
    w["a"] = await create_condition(
        client,
        condition_body(
            w["p1"],
            identifier=[
                {
                    "system": COND_IDS,
                    "value": "C-A",
                    "type": {
                        "coding": [{"system": V2_0203, "code": "PRN"}],
                        "text": "Condition id",
                    },
                }
            ],
            clinicalStatus=clinical("active"),
            verificationStatus=verification("confirmed"),
            category=[category("problem-list-item")],
            severity={
                "coding": [{"system": SCT, "code": "24484000", "display": "Severe"}]
            },
            code={
                "coding": [
                    {"system": SCT, "code": "38341003", "display": "Hypertension"}
                ]
            },
            bodySite=[
                {
                    "coding": [
                        {"system": SCT, "code": "368208006", "display": "Left arm"}
                    ]
                }
            ],
            encounter={"reference": f"Encounter/{w['enc1']}"},
            onsetDateTime="2020-03-10",
            abatementDateTime="2021-06-01",
            recordedDate="2020-03-11T08:00:00Z",
            asserter={"reference": f"Patient/{w['p1']}"},
            stage=[
                {
                    "summary": {
                        "coding": [
                            {"system": SCT, "code": "14803004", "display": "Temporary"}
                        ]
                    }
                }
            ],
            evidence=[
                {
                    "code": [
                        {
                            "coding": [
                                {
                                    "system": SCT,
                                    "code": "29857009",
                                    "display": "Chest pain",
                                }
                            ]
                        }
                    ],
                    "detail": [
                        {"reference": "Observation/160001"},
                        {"reference": f"Encounter/{w['enc2']}"},
                    ],
                }
            ],
        ),
    )
    w["b"] = await create_condition(
        client,
        condition_body(
            w["p2"],
            identifier=[{"system": COND_IDS, "value": "C-B"}],
            clinicalStatus=clinical("inactive"),
            verificationStatus=verification("provisional"),
            category=[category("encounter-diagnosis")],
            severity={"text": "Mild"},
            code={
                "coding": [{"system": SCT, "code": "44054006", "display": "Diabetes"}]
            },
            encounter={"reference": f"Encounter/{w['enc2']}"},
            onsetAge=_age(12),
            abatementAge=_age(30),
            recordedDate="2019",
            asserter={"reference": f"Practitioner/{w['pr']}"},
            evidence=[{"code": [{"text": "Thirst"}]}],
        ),
    )
    w["c"] = await create_condition(
        client,
        condition_body(
            w["p1"],
            clinicalStatus=clinical("resolved"),
            verificationStatus=verification("refuted"),
            category=[category("problem-list-item"), category("encounter-diagnosis")],
            code={"text": "Asthma"},
            onsetRange={"low": _age(5), "high": _age(10)},
            abatementRange={"low": _age(20), "high": _age(25)},
            asserter={"reference": f"RelatedPerson/{w['rp']}"},
        ),
    )
    w["d"] = await create_condition(
        client,
        {
            "subject": {"reference": "Group/430001"},
            "onsetString": "Childhood",
            "abatementString": "Resolved spontaneously",
            "asserter": {"identifier": {"system": "urn:who", "value": "W-1"}},
        },
    )
    w["e"] = await create_condition(
        client,
        {
            "subject": {
                "identifier": {"system": "urn:pts", "value": "P-9"},
                "display": "External",
            },
            "onsetPeriod": {"start": "2018-01-01", "end": "2018-06-30"},
            "abatementPeriod": {"start": "2019-01-01"},
            "recordedDate": "2026-01-01T00:00:00Z",
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


# ── clinical-status / verification-status / category ─────────────────────────


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
        "e",
    }
    assert await _keys(client, world, **{"clinical-status:missing": "true"}) == {
        "d",
        "e",
    }


async def test_verification_status(client, world):
    assert await _keys(client, world, **{"verification-status": "confirmed"}) == {"a"}
    assert await _keys(
        client, world, **{"verification-status": f"{VERIF}|refuted"}
    ) == {"c"}
    assert await _keys(
        client, world, **{"verification-status": "provisional,refuted"}
    ) == {"b", "c"}
    assert (
        await _keys(client, world, **{"verification-status": "http://wrong|confirmed"})
        == set()
    )
    assert await _keys(client, world, **{"verification-status:missing": "true"}) == {
        "d",
        "e",
    }


async def test_category_is_a_list(client, world):
    assert await _keys(client, world, category="problem-list-item") == {"a", "c"}
    assert await _keys(client, world, category="encounter-diagnosis") == {
        "b",
        "c",
    }  # c has both
    assert await _keys(
        client, world, category="problem-list-item,encounter-diagnosis"
    ) == {"a", "b", "c"}
    assert await _keys(client, world, **{"category:not": "problem-list-item"}) == {
        "b",
        "d",
        "e",
    }
    assert await _keys(client, world, **{"category:missing": "true"}) == {"d", "e"}
    assert await _keys(
        client, world, category=["problem-list-item", "encounter-diagnosis"]
    ) == {"c"}  # repeat = AND


# ── severity / code / body-site / evidence / stage ───────────────────────────


async def test_severity(client, world):
    assert await _keys(client, world, severity="24484000") == {"a"}
    assert await _keys(client, world, severity=f"{SCT}|24484000") == {"a"}
    assert await _keys(client, world, **{"severity:text": "mild"}) == {
        "b"
    }  # a text-only concept is found
    assert await _keys(client, world, **{"severity:text": "sev"}) == {
        "a"
    }  # Coding.display
    assert await _keys(client, world, **{"severity:missing": "true"}) == {"c", "d", "e"}


async def test_code(client, world):
    assert await _keys(client, world, code="38341003") == {"a"}
    assert await _keys(client, world, code="44054006") == {"b"}
    assert await _keys(client, world, code="38341003,44054006") == {"a", "b"}
    assert await _keys(client, world, code=f"{SCT}|") == {"a", "b"}
    assert await _keys(client, world, code="http://wrong|38341003") == set()
    assert await _keys(client, world, **{"code:text": "asthma"}) == {"c"}
    assert await _keys(client, world, **{"code:text": "hyper"}) == {"a"}
    assert await _keys(client, world, **{"code:not": "38341003"}) == {
        "b",
        "c",
        "d",
        "e",
    }
    assert await _keys(client, world, **{"code:missing": "true"}) == {"d", "e"}


async def test_body_site_evidence_and_stage(client, world):
    assert await _keys(client, world, **{"body-site": "368208006"}) == {"a"}
    assert await _keys(client, world, **{"body-site:text": "left"}) == {"a"}
    assert await _keys(client, world, **{"body-site:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }
    assert await _keys(client, world, evidence="29857009") == {
        "a"
    }  # Condition.evidence.code
    assert await _keys(client, world, **{"evidence:text": "thirst"}) == {"b"}
    assert await _keys(client, world, **{"evidence:text": "chest"}) == {"a"}
    assert await _keys(client, world, **{"evidence:missing": "true"}) == {"c", "d", "e"}
    assert await _keys(client, world, stage="14803004") == {
        "a"
    }  # Condition.stage.summary
    assert await _keys(client, world, **{"stage:text": "temp"}) == {"a"}
    assert await _keys(client, world, **{"stage:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }


# ── identifier ───────────────────────────────────────────────────────────────


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="C-A") == {"a"}
    assert await _keys(client, world, identifier=f"{COND_IDS}|C-B") == {"b"}
    assert await _keys(client, world, identifier="C-A,C-B") == {"a", "b"}
    assert await _keys(client, world, identifier="urn:other|C-A") == set()


async def test_identifier_text_of_type_not_and_missing(client, world):
    assert await _keys(client, world, **{"identifier:text": "condition"}) == {"a"}
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|PRN|C-A"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|PRN|C-B"})
        == set()
    )
    assert await _keys(client, world, **{"identifier:not": "C-A"}) == ALL - {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


# ── recorded-date / onset-date / abatement-date (a dateTime or Period as a range) ──


async def test_recorded_date(client, world):
    assert await _keys(client, world, **{"recorded-date": "2020-03-11"}) == {
        "a"
    }  # the day contains the instant
    assert await _keys(client, world, **{"recorded-date": "2019"}) == {"b"}
    assert await _keys(client, world, **{"recorded-date": "2026"}) == {"e"}
    assert await _keys(client, world, **{"recorded-date": "ge2020"}) == {"a", "e"}
    assert await _keys(client, world, **{"recorded-date": "lt2020"}) == {"b"}
    assert await _keys(client, world, **{"recorded-date:missing": "true"}) == {"c", "d"}
    assert await _status(client, **{"recorded-date": "banana"}) == 400


async def test_onset_date_reads_a_datetime_or_a_period(client, world):
    assert await _keys(client, world, **{"onset-date": "2020-03-10"}) == {
        "a"
    }  # onsetDateTime
    assert await _keys(client, world, **{"onset-date": "2018"}) == {
        "e"
    }  # onsetPeriod inside the year
    assert (
        await _keys(client, world, **{"onset-date": "2018-03"}) == set()
    )  # a month does not contain the period
    assert await _keys(client, world, **{"onset-date": "ge2018-06"}) == {
        "a",
        "e",
    }  # the period overlaps above
    assert await _keys(client, world, **{"onset-date": "lt2019"}) == {"e"}
    assert await _keys(client, world, **{"onset-date:missing": "true"}) == {
        "b",
        "c",
        "d",
    }


async def test_abatement_date_open_ended_period(client, world):
    assert await _keys(client, world, **{"abatement-date": "2021-06-01"}) == {"a"}
    assert await _keys(client, world, **{"abatement-date": "ge2021"}) == {
        "a",
        "e",
    }  # e is open-ended
    assert await _keys(client, world, **{"abatement-date": "lt2019"}) == set()
    assert (
        await _keys(client, world, **{"abatement-date": "2019"}) == set()
    )  # an open period is never inside a year
    assert await _keys(client, world, **{"abatement-date:missing": "true"}) == {
        "b",
        "c",
        "d",
    }


# ── onset-age / abatement-age (an Age or a Range) ────────────────────────────


async def test_onset_age_reads_an_age_or_a_range(client, world):
    assert await _keys(client, world, **{"onset-age": "12"}) == {"b"}  # the Age
    assert (
        await _keys(client, world, **{"onset-age": "7"}) == set()
    )  # eq: the range is not contained
    assert await _keys(client, world, **{"onset-age": "1e1"}) == {
        "b",
        "c",
    }  # [5, 15) holds the Age and the Range
    assert await _keys(client, world, **{"onset-age": "gt11"}) == {"b"}
    assert await _keys(client, world, **{"onset-age": "lt6"}) == {
        "c"
    }  # the range 5-10 overlaps below 6
    assert await _keys(client, world, **{"onset-age": "ge10"}) == {"b", "c"}
    assert await _keys(client, world, **{"onset-age": "le5"}) == {"c"}
    assert await _keys(client, world, **{"onset-age": "sa11"}) == {"b"}
    assert await _keys(client, world, **{"onset-age": "eb11"}) == {"c"}
    assert await _keys(client, world, **{"onset-age": "ap8"}) == {"c"}
    assert await _keys(client, world, **{"onset-age": "ne12"}) == {"c"}
    assert await _keys(client, world, **{"onset-age:missing": "true"}) == {
        "a",
        "d",
        "e",
    }


async def test_onset_age_units(client, world):
    assert await _keys(client, world, **{"onset-age": f"12|{UCUM}|a"}) == {"b"}
    assert await _keys(client, world, **{"onset-age": "12||a"}) == {"b"}
    assert await _keys(client, world, **{"onset-age": "12||years"}) == {
        "b"
    }  # the human unit
    assert await _keys(client, world, **{"onset-age": "12|http://wrong|a"}) == set()
    assert await _keys(client, world, **{"onset-age": f"12|{UCUM}|mo"}) == set()
    assert await _status(client, **{"onset-age": "abc"}) == 400


async def test_abatement_age(client, world):
    assert await _keys(client, world, **{"abatement-age": "30"}) == {"b"}
    assert await _keys(client, world, **{"abatement-age": "gt24"}) == {"b", "c"}
    assert await _keys(client, world, **{"abatement-age": "lt21"}) == {"c"}
    assert await _keys(client, world, **{"abatement-age:missing": "true"}) == {
        "a",
        "d",
        "e",
    }


# ── onset-info / abatement-string ────────────────────────────────────────────


async def test_onset_info_and_abatement_string(client, world):
    assert await _keys(client, world, **{"onset-info": "child"}) == {
        "d"
    }  # starts-with, case-insensitive
    assert await _keys(client, world, **{"onset-info": "hood"}) == set()  # not a prefix
    assert await _keys(client, world, **{"onset-info:contains": "hood"}) == {"d"}
    assert await _keys(client, world, **{"onset-info:exact": "Childhood"}) == {"d"}
    assert await _keys(client, world, **{"onset-info:exact": "childhood"}) == set()
    assert await _keys(client, world, **{"onset-info:missing": "true"}) == {
        "a",
        "b",
        "c",
        "e",
    }
    assert await _keys(client, world, **{"abatement-string": "resolv"}) == {"d"}
    assert await _keys(client, world, **{"abatement-string:contains": "spontan"}) == {
        "d"
    }
    assert await _keys(client, world, **{"abatement-string:missing": "true"}) == {
        "a",
        "b",
        "c",
        "e",
    }


# ── subject / patient / encounter ────────────────────────────────────────────


async def test_subject_is_multi_target(client, world):
    assert (
        await _status(client, subject=str(world["p1"])) == 400
    )  # a bare id with two targets is ambiguous
    assert await _keys(client, world, subject=f"Patient/{world['p1']}") == {"a", "c"}
    assert await _keys(client, world, subject="Group/430001") == {
        "d"
    }  # Group is a target, not a resource here
    assert await _keys(client, world, **{"subject:Patient": str(world["p2"])}) == {"b"}
    assert await _keys(client, world, **{"subject:Group": "430001"}) == {"d"}
    assert (
        await _keys(client, world, subject=f"Group/{world['p1']}") == set()
    )  # the type is part of the match
    assert await _keys(client, world, **{"subject:identifier": "urn:pts|P-9"}) == {"e"}
    assert await _keys(client, world, **{"subject:missing": "true"}) == set()
    assert await _keys(client, world, **{"subject:missing": "false"}) == ALL


async def test_patient_is_subject_narrowed_to_patients(client, world):
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
    # A Group subject and a logical subject are not known to be Patients.
    assert await _keys(client, world, **{"patient:missing": "true"}) == {"d", "e"}
    assert await _keys(client, world, **{"patient:missing": "false"}) == {"a", "b", "c"}


async def test_encounter(client, world):
    assert await _keys(client, world, encounter=str(world["enc1"])) == {
        "a"
    }  # one target: a bare id works
    assert await _keys(client, world, encounter=f"Encounter/{world['enc2']}") == {"b"}
    assert await _keys(client, world, encounter="999999") == set()
    assert await _keys(client, world, **{"encounter:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


# ── asserter (multi-target) ──────────────────────────────────────────────────


async def test_asserter(client, world):
    assert await _status(client, asserter=str(world["pr"])) == 400
    assert await _keys(client, world, asserter=f"Patient/{world['p1']}") == {"a"}
    assert await _keys(
        client, world, **{"asserter:Practitioner": str(world["pr"])}
    ) == {"b"}
    assert await _keys(client, world, asserter=f"RelatedPerson/{world['rp']}") == {"c"}
    assert await _keys(client, world, **{"asserter:identifier": "urn:who|W-1"}) == {"d"}
    assert (
        await _keys(client, world, asserter=f"Practitioner/{world['p1']}") == set()
    )  # the type is part of the match
    assert await _keys(client, world, **{"asserter:missing": "true"}) == {
        "e"
    }  # d has a logical reference
    assert await _keys(client, world, **{"asserter:missing": "false"}) == {
        "a",
        "b",
        "c",
        "d",
    }


# ── evidence-detail (Reference(Any)) ─────────────────────────────────────────


async def test_evidence_detail(client, world):
    assert (
        await _status(client, **{"evidence-detail": "160001"}) == 400
    )  # Reference(Any): needs a type
    assert await _keys(client, world, **{"evidence-detail": "Observation/160001"}) == {
        "a"
    }
    assert await _keys(
        client, world, **{"evidence-detail": f"Encounter/{world['enc2']}"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"evidence-detail:Encounter": str(world["enc2"])}
    ) == {"a"}
    assert await _keys(client, world, **{"evidence-detail": "Observation/999"}) == set()
    assert await _keys(client, world, **{"evidence-detail:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }


# ── chaining ─────────────────────────────────────────────────────────────────


async def test_chains(client, world):
    assert await _keys(client, world, **{"patient.family": "Windsor"}) == {"a", "c"}
    assert await _keys(client, world, **{"patient.name": "Ben"}) == {"b"}
    assert await _keys(client, world, **{"subject:Patient.family": "Fairfax"}) == {"b"}
    assert await _keys(client, world, **{"patient.family": "Nobody"}) == set()
    assert await _keys(client, world, **{"encounter.status": "in-progress"}) == {
        "a",
        "b",
    }
    assert await _keys(client, world, **{"encounter.status": "finished"}) == set()
    assert await _keys(
        client, world, **{"asserter:Practitioner.family": "Careful"}
    ) == {"b"}
    assert await _keys(client, world, **{"asserter:Patient.family": "Windsor"}) == {"a"}
    assert await _keys(client, world, **{"asserter:RelatedPerson.name": "Gray"}) == {
        "c"
    }
    assert await _keys(
        client, world, **{"evidence-detail:Encounter.status": "in-progress"}
    ) == {"a"}


async def test_bad_chains_are_400(client, world):
    assert await _status(client, **{"patient.nonsense": "x"}) == 400
    assert (
        await _status(client, **{"subject.family": "x"}) == 400
    )  # an untyped multi-target cannot be chained
    assert (
        await _status(client, **{"subject:Group.name": "x"}) == 400
    )  # Group is not searchable here
    assert await _status(client, **{"asserter.family": "x"}) == 400
    assert (
        await _status(client, **{"evidence-detail:MedicationRequest.status": "x"})
        == 400
    )  # not a resource here
    assert (
        await _status(client, **{"code.x": "y"}) == 400
    )  # a token cannot be chained through


# ── _sort / _count / _offset / _total ────────────────────────────────────────


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "abatement-age",
        "abatement-date",
        "abatement-string",
        "asserter",
        "body-site",
        "category",
        "clinical-status",
        "code",
        "encounter",
        "evidence",
        "evidence-detail",
        "identifier",
        "onset-age",
        "onset-date",
        "onset-info",
        "patient",
        "recorded-date",
        "severity",
        "stage",
        "subject",
        "verification-status",
        "_id",
    ):
        assert (await _search(client, _sort=key))["total"] == 5, key
    assert await _status(client, _sort="note") == 400


async def test_sort_by_dates_and_age(client, world):
    async def ids(**params):
        return [
            int(e["resource"]["id"]) for e in (await _search(client, **params))["entry"]
        ]

    assert await ids(
        **{"recorded-date:missing": "false", "_sort": "recorded-date"}
    ) == [world["b"], world["a"], world["e"]]
    assert await ids(
        **{"recorded-date:missing": "false", "_sort": "-recorded-date"}
    ) == [world["e"], world["a"], world["b"]]
    assert await ids(**{"onset-age:missing": "false", "_sort": "onset-age"}) == [
        world["c"],
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
    resource = (await _search(client, _elements="clinicalStatus", _id=str(world["a"])))[
        "entry"
    ][0]["resource"]
    assert resource["clinicalStatus"] == clinical("active")
    assert "stage" not in resource and "note" not in resource


# ── _include / _revinclude ───────────────────────────────────────────────────


async def test_include_subject_patient_and_encounter(client, world):
    ids = f"{world['a']},{world['b']},{world['c']}"
    for param in ("patient", "subject"):
        bundle = await _search(client, _id=ids, _include=f"Condition:{param}")
        assert _of_type(bundle, "Patient", "include") == {
            str(world["p1"]),
            str(world["p2"]),
        }
    bundle = await _search(client, _id=ids, _include="Condition:encounter")
    assert _of_type(bundle, "Encounter", "include") == {
        str(world["enc1"]),
        str(world["enc2"]),
    }


async def test_include_skips_non_resources(client, world):
    bundle = await _search(
        client, _id=f"{world['d']},{world['e']}", _include="Condition:subject"
    )
    assert (
        _of_type(bundle, "Patient", "include") == set()
    )  # a Group and a logical subject add nothing


async def test_include_asserter_brings_in_every_modeled_type(client, world):
    ids = f"{world['a']},{world['b']},{world['c']},{world['d']}"
    bundle = await _search(client, _id=ids, _include="Condition:asserter")
    assert _of_type(bundle, "Patient", "include") == {str(world["p1"])}
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "RelatedPerson", "include") == {str(world["rp"])}
    bundle = await _search(client, _id=ids, _include="Condition:asserter:Practitioner")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "Patient", "include") == set()


async def test_include_evidence_detail_only_brings_in_modeled_types(client, world):
    bundle = await _search(
        client, _id=str(world["a"]), _include="Condition:evidence-detail"
    )
    assert _of_type(bundle, "Encounter", "include") == {
        str(world["enc2"])
    }  # Observation is not a resource here


async def _other(client, path, **params) -> dict:
    resp = await client.get(f"{API}/{path}/", params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_revinclude_conditions_on_the_resources_they_point_at(client, world):
    for param in ("patient", "subject"):
        bundle = await _other(
            client, "patients", _id=str(world["p2"]), _revinclude=f"Condition:{param}"
        )
        assert _of_type(bundle, "Condition", "include") == {str(world["b"])}
    bundle = await _other(
        client, "patients", _id=str(world["p1"]), _revinclude="Condition:patient"
    )
    assert _of_type(bundle, "Condition", "include") == {
        str(world["a"]),
        str(world["c"]),
    }
    bundle = await _other(
        client, "patients", _id=str(world["p1"]), _revinclude="Condition:asserter"
    )
    assert _of_type(bundle, "Condition", "include") == {str(world["a"])}
    bundle = await _other(
        client, "practitioners", _id=str(world["pr"]), _revinclude="Condition:asserter"
    )
    assert _of_type(bundle, "Condition", "include") == {str(world["b"])}
    bundle = await _other(
        client,
        "related-persons",
        _id=str(world["rp"]),
        _revinclude="Condition:asserter",
    )
    assert _of_type(bundle, "Condition", "include") == {str(world["c"])}
    bundle = await _other(
        client, "encounters", _id=str(world["enc1"]), _revinclude="Condition:encounter"
    )
    assert _of_type(bundle, "Condition", "include") == {str(world["a"])}


async def test_revinclude_what_points_at_a_condition(client, world):
    ref_a, ref_b = f"Condition/{world['a']}", f"Condition/{world['b']}"
    enc = (
        await client.post(
            f"{API}/encounters/",
            json={
                "status": "finished",
                "class": {"code": "AMB"},
                "diagnosis": [{"condition": {"reference": ref_a}}],
                "reasonReference": [{"reference": ref_b}],
            },
        )
    ).json()["id"]
    appointment = await create_appointment(
        client, appointment_body(world["p1"], reasonReference=[{"reference": ref_a}])
    )

    def go(key, **params):
        return _search(client, _id=str(world[key]), **params)

    assert _of_type(
        await go("a", _revinclude="Encounter:diagnosis"), "Encounter", "include"
    ) == {enc}
    assert (
        _of_type(
            await go("a", _revinclude="Encounter:reason-reference"),
            "Encounter",
            "include",
        )
        == set()
    )
    assert _of_type(
        await go("b", _revinclude="Encounter:reason-reference"), "Encounter", "include"
    ) == {enc}
    assert _of_type(
        await go("a", _revinclude="Appointment:reason-reference"),
        "Appointment",
        "include",
    ) == {str(appointment)}
    assert (
        _of_type(
            await go("b", _revinclude="Appointment:reason-reference"),
            "Appointment",
            "include",
        )
        == set()
    )
    # ...and the other way round: _include the Conditions an Encounter / Appointment point at.
    bundle = await _other(client, "encounters", _id=enc, _include="Encounter:diagnosis")
    assert _of_type(bundle, "Condition", "include") == {str(world["a"])}
    bundle = await _other(
        client, "encounters", _id=enc, _include="Encounter:reason-reference"
    )
    assert _of_type(bundle, "Condition", "include") == {str(world["b"])}
    bundle = await _other(
        client,
        "appointments",
        _id=str(appointment),
        _include="Appointment:reason-reference",
    )
    assert _of_type(bundle, "Condition", "include") == {str(world["a"])}
    # And a Condition can be chained to from them.
    bundle = await _other(
        client, "encounters", **{"diagnosis:Condition.clinical-status": "active"}
    )
    assert _ids(bundle) == {int(enc)}
    bundle = await _other(
        client,
        "appointments",
        **{"reason-reference:Condition.clinical-status": "active"},
    )
    assert _ids(bundle) == {appointment}
    bundle = await _other(
        client,
        "appointments",
        **{"reason-reference:Condition.clinical-status": "resolved"},
    )
    assert _ids(bundle) == set()


async def test_revinclude_is_tenant_scoped(client, other_client):
    from app.auth.dependencies import get_current_user
    from app.main import app
    from tests.conftest import make_test_user
    from tests.integration.condition.conftest import CONDITION_PERMS

    def as_user(**kw):
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=CONDITION_PERMS, **kw
        )

    as_user()
    mine = await create_patient(client)
    await create_condition(client, condition_body(mine))
    as_user(sub="u-other", org_id="org-other")
    try:
        # The other org cannot see the patient, so nothing reaches its conditions.
        bundle = await _other(
            other_client, "patients", _id=str(mine), _revinclude="Condition:patient"
        )
        assert bundle["total"] == 0 and "entry" not in bundle
        theirs = await create_patient(other_client)
        bundle = await _other(
            other_client, "patients", _id=str(theirs), _revinclude="Condition:patient"
        )
        assert _of_type(bundle, "Condition", "include") == set()
    finally:
        as_user()


# ── combination rules / lenient vs strict ────────────────────────────────────


async def test_params_are_anded(client, world):
    assert await _keys(
        client, world, **{"clinical-status": "active", "category": "problem-list-item"}
    ) == {"a"}
    assert (
        await _keys(
            client,
            world,
            **{"clinical-status": "active", "category": "encounter-diagnosis"},
        )
        == set()
    )
    assert await _keys(
        client, world, patient=str(world["p1"]), **{"verification-status": "refuted"}
    ) == {"c"}
    assert await _keys(
        client, world, code="38341003", **{"recorded-date": "ge2020"}
    ) == {"a"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"onset-age:above": "x"}) == 400
    assert await _status(client, **{"patient:text": "x"}) == 400
    assert await _status(client, **{"onset-date:exact": "2020"}) == 400
    assert await _status(client, **{"onset-info:text": "x"}) == 400


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
        BASE + "/_search",
        data={"clinical-status": "inactive", "patient": str(world["p2"])},
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, **{"clinical-status": "inactive"})
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/conditions/{world['b']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "Condition"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
