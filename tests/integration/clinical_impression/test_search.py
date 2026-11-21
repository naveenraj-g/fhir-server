"""FHIR R4 search over ClinicalImpression (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/clinicalimpression.html#search).

One block per search parameter — `status` a code, `date` a dateTime range, `identifier` and
`finding-code` tokens, the single-target references (`patient`, `encounter`, `previous`), the
multi-target ones (`subject`, `assessor`) and the repeating ones held in one table (`problem`,
`investigation`, `finding-ref`, `supporting-info`, the last being Reference(Any)) — then
chaining, `_include`/`_revinclude`, result parameters, combination rules, lenient vs strict
handling and POST _search.
"""

import pytest

from tests.integration.clinical_impression.support import (
    API,
    BASE,
    IMPRESSION_IDS,
    SCT,
    V2_0203,
    allergy_body,
    condition_body,
    create_allergy_intolerance,
    create_condition,
    create_encounter,
    create_history,
    create_impression,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_report,
    create_risk,
    encounter_body,
    finding,
    history_body,
    impression_body,
    report_body,
    risk_body,
)

KEYS = ("a", "b", "c", "d", "e")
ALL = set(KEYS)


def _ids(bundle: dict) -> set[int]:
    return {int(e["resource"]["id"]) for e in bundle.get("entry") or [] if e["search"]["mode"] == "match"}


def _of_type(bundle: dict, rtype: str, mode: str) -> set[str]:
    return {
        e["resource"]["id"]
        for e in bundle.get("entry") or []
        if e["resource"]["resourceType"] == rtype and e["search"]["mode"] == mode
    }


@pytest.fixture
async def world(client):
    """Two patients, a practitioner, a practitioner role, an encounter, a condition, an allergy, a
    diagnostic report, a risk assessment and a family history, plus five impressions with
    distinct, searchable values. Returns {key: id}."""
    w = {}
    w["p1"] = await create_patient(client, {"active": True, "name": [{"family": "Windsor", "given": ["Anna"]}]})
    w["p2"] = await create_patient(client, {"active": True, "name": [{"family": "Fairfax", "given": ["Ben"]}]})
    w["pr"] = await create_practitioner(client)  # family "Careful"
    w["role"] = await create_practitioner_role(client)
    w["enc"] = await create_encounter(client, encounter_body())
    w["cond"] = await create_condition(client, condition_body(w["p1"]))
    w["allergy"] = await create_allergy_intolerance(client, allergy_body(w["p1"]))
    w["report"] = await create_report(client, report_body(w["p1"]))
    w["risk"] = await create_risk(client, risk_body(w["p1"]))
    w["history"] = await create_history(client, history_body(w["p1"]))
    w["a"] = await create_impression(
        client,
        impression_body(
            w["p1"],
            "completed",
            identifier=[
                {
                    "system": IMPRESSION_IDS,
                    "value": "CI-A",
                    "type": {"coding": [{"system": V2_0203, "code": "FILL"}], "text": "Impression id"},
                }
            ],
            date="2023-01-15T10:00:00Z",
            encounter={"reference": f"Encounter/{w['enc']}"},
            assessor={"reference": f"Practitioner/{w['pr']}"},
            problem=[{"reference": f"Condition/{w['cond']}"}, {"reference": f"AllergyIntolerance/{w['allergy']}"}],
            investigation=[
                {
                    "code": {"text": "Initial examination"},
                    "item": [
                        {"reference": f"DiagnosticReport/{w['report']}"},
                        {"reference": f"RiskAssessment/{w['risk']}"},
                        {"reference": "Observation/160001"},
                    ],
                }
            ],
            finding=[
                finding("194828000", "Angina"),
                {**finding("29857009", "Chest pain"), "itemReference": {"reference": f"Condition/{w['cond']}"}},
            ],
            supportingInfo=[{"reference": f"Condition/{w['cond']}"}, {"reference": "Observation/160002"}],
        ),
    )
    w["b"] = await create_impression(
        client,
        impression_body(
            w["p2"],
            "in-progress",
            identifier=[{"system": IMPRESSION_IDS, "value": "CI-B"}],
            date="2024-02",
            assessor={"reference": f"PractitionerRole/{w['role']}"},
            previous={"reference": f"ClinicalImpression/{w['a']}"},
            problem=[{"reference": f"AllergyIntolerance/{w['allergy']}"}],
            investigation=[
                {
                    "code": {"text": "Follow-up"},
                    "item": [{"reference": f"FamilyMemberHistory/{w['history']}"}, {"reference": "Media/9"}],
                }
            ],
            finding=[{"itemCodeableConcept": {"text": "Chest wall pain"}}],
            supportingInfo=[{"reference": f"Patient/{w['p2']}"}],
        ),
    )
    w["c"] = await create_impression(
        client,
        impression_body(
            w["p1"],
            "entered-in-error",
            investigation=[{"code": {"text": "Labs"}, "item": [{"reference": "Observation/160001"}]}],
            finding=[finding("386661006", "Fever"), {"itemReference": {"reference": "Observation/160009"}}],
        ),
    )
    w["d"] = await create_impression(
        client,
        {
            "status": "completed",
            "subject": {"reference": "Group/430001"},
            "date": "2019",
            "previous": {"reference": f"ClinicalImpression/{w['b']}"},
        },
    )
    w["e"] = await create_impression(
        client,
        {
            "status": "in-progress",
            "subject": {"identifier": {"system": "urn:pts", "value": "P-9"}, "display": "External"},
            "date": "2024-03-01T00:00:00Z",
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
    assert await _keys(client, world, status="completed") == {"a", "d"}
    assert await _keys(client, world, status="in-progress") == {"b", "e"}
    assert await _keys(client, world, status="entered-in-error") == {"c"}  # the real FHIR code
    assert await _keys(client, world, status="completed,entered-in-error") == {"a", "c", "d"}
    assert await _keys(client, world, status="http://hl7.org/fhir/event-status|completed") == {"a", "d"}
    assert await _keys(client, world, status="http://wrong|completed") == set()
    assert await _keys(client, world, status="no-such-code") == set()
    assert await _keys(client, world, **{"status:not": "completed"}) == {"b", "c", "e"}
    assert await _keys(client, world, **{"status:missing": "true"}) == set()
    assert await _keys(client, world, **{"status:missing": "false"}) == ALL


# ── date ─────────────────────────────────────────────────────────────────────


async def test_date(client, world):
    assert await _keys(client, world, date="2023-01-15") == {"a"}
    assert await _keys(client, world, date="2023") == {"a"}
    assert await _keys(client, world, date="2024") == {"b", "e"}  # 2024-02 and 2024-03-01 lie inside 2024
    assert await _keys(client, world, date="ge2024-01-01") == {"b", "e"}
    assert await _keys(client, world, date="lt2023-01-01") == {"d"}
    assert await _keys(client, world, date="sa2023-02-01") == {"b", "e"}
    assert await _keys(client, world, date="eb2020-01-01") == {"d"}
    assert await _keys(client, world, **{"date:missing": "true"}) == {"c"}
    assert await _keys(client, world, **{"date:missing": "false"}) == {"a", "b", "d", "e"}


# ── identifier ───────────────────────────────────────────────────────────────


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="CI-A") == {"a"}
    assert await _keys(client, world, identifier=f"{IMPRESSION_IDS}|CI-B") == {"b"}
    assert await _keys(client, world, identifier="CI-A,CI-B") == {"a", "b"}
    assert await _keys(client, world, identifier="urn:wrong|CI-A") == set()
    assert await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|FILL|CI-A"}) == {"a"}
    assert await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|FILL|CI-B"}) == set()
    assert await _keys(client, world, **{"identifier:text": "impression"}) == {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {"c", "d", "e"}


# ── finding-code ─────────────────────────────────────────────────────────────


async def test_finding_code_reads_every_finding(client, world):
    assert await _keys(client, world, **{"finding-code": "194828000"}) == {"a"}
    assert await _keys(client, world, **{"finding-code": "29857009"}) == {"a"}  # the second finding of `a`
    assert await _keys(client, world, **{"finding-code": f"{SCT}|386661006"}) == {"c"}
    assert await _keys(client, world, **{"finding-code": "http://wrong|386661006"}) == set()
    assert await _keys(client, world, **{"finding-code": "194828000,386661006"}) == {"a", "c"}
    assert await _keys(client, world, **{"finding-code:text": "chest wall"}) == {"b"}  # a text-only concept is found
    assert await _keys(client, world, **{"finding-code:text": "angina"}) == {"a"}  # Coding.display
    assert await _keys(client, world, **{"finding-code:missing": "true"}) == {"d", "e"}


# ── patient / subject ────────────────────────────────────────────────────────


async def test_patient(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {"a", "c"}  # one target: a bare id works
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"b"}
    assert await _keys(client, world, patient=f"{world['p1']},{world['p2']}") == {"a", "b", "c"}
    assert await _keys(client, world, patient="999999") == set()
    assert await _keys(client, world, **{"patient:Patient": str(world["p1"])}) == {"a", "c"}
    assert await _keys(client, world, **{"patient:identifier": "urn:pts|P-9"}) == set()  # not a Patient reference
    # a Group or a logical subject is not a Patient, so it counts as missing `patient`
    assert await _keys(client, world, **{"patient:missing": "true"}) == {"d", "e"}
    assert await _keys(client, world, **{"patient:missing": "false"}) == {"a", "b", "c"}


async def test_subject_is_multi_target(client, world):
    assert await _status(client, subject=str(world["p1"])) == 400  # a bare id is ambiguous
    assert await _keys(client, world, subject=f"Patient/{world['p1']}") == {"a", "c"}
    assert await _keys(client, world, **{"subject:Patient": str(world["p2"])}) == {"b"}
    assert await _keys(client, world, subject="Group/430001") == {"d"}  # the type is part of the match
    assert await _keys(client, world, subject=f"Group/{world['p1']}") == set()
    assert await _keys(client, world, **{"subject:identifier": "urn:pts|P-9"}) == {"e"}
    assert await _keys(client, world, **{"subject:missing": "true"}) == set()


# ── encounter / assessor / previous ──────────────────────────────────────────


async def test_encounter(client, world):
    assert await _keys(client, world, encounter=str(world["enc"])) == {"a"}
    assert await _keys(client, world, encounter=f"Encounter/{world['enc']}") == {"a"}
    assert await _keys(client, world, encounter="999999") == set()
    assert await _keys(client, world, **{"encounter:missing": "true"}) == {"b", "c", "d", "e"}


async def test_assessor_is_multi_target(client, world):
    assert await _status(client, assessor=str(world["pr"])) == 400  # a bare id is ambiguous
    assert await _keys(client, world, assessor=f"Practitioner/{world['pr']}") == {"a"}
    assert await _keys(client, world, **{"assessor:Practitioner": str(world["pr"])}) == {"a"}
    assert await _keys(client, world, assessor=f"PractitionerRole/{world['role']}") == {"b"}
    assert await _keys(client, world, assessor=f"Practitioner/{world['role']}") == set()  # the type is part of the match
    assert await _keys(client, world, **{"assessor:missing": "true"}) == {"c", "d", "e"}


async def test_previous(client, world):
    assert await _keys(client, world, previous=str(world["a"])) == {"b"}  # one target: a bare id works
    assert await _keys(client, world, previous=f"ClinicalImpression/{world['b']}") == {"d"}
    assert await _keys(client, world, previous="999999") == set()
    assert await _keys(client, world, **{"previous:missing": "true"}) == {"a", "c", "e"}
    assert await _keys(client, world, **{"previous:missing": "false"}) == {"b", "d"}


# ── problem / investigation / finding-ref / supporting-info ──────────────────


async def test_problem_is_multi_target(client, world):
    assert await _status(client, problem=str(world["cond"])) == 400  # a bare id is ambiguous
    assert await _keys(client, world, problem=f"Condition/{world['cond']}") == {"a"}
    assert await _keys(client, world, problem=f"AllergyIntolerance/{world['allergy']}") == {"a", "b"}
    assert await _keys(client, world, **{"problem:Condition": str(world["cond"])}) == {"a"}
    assert await _keys(client, world, problem=f"Condition/{world['allergy']}") == set()  # the type is part of the match
    assert await _keys(client, world, **{"problem:missing": "true"}) == {"c", "d", "e"}
    assert await _keys(client, world, **{"problem:missing": "false"}) == {"a", "b"}


async def test_investigation_reads_every_item(client, world):
    assert await _status(client, investigation=str(world["report"])) == 400
    assert await _keys(client, world, investigation=f"DiagnosticReport/{world['report']}") == {"a"}
    assert await _keys(client, world, investigation=f"RiskAssessment/{world['risk']}") == {"a"}
    assert await _keys(client, world, investigation=f"FamilyMemberHistory/{world['history']}") == {"b"}
    assert await _keys(client, world, investigation="Observation/160001") == {"a", "c"}  # not a resource here: by reference
    assert await _keys(client, world, investigation="Media/9") == {"b"}
    assert await _keys(client, world, **{"investigation:DiagnosticReport": str(world["report"])}) == {"a"}
    assert await _keys(client, world, **{"investigation:missing": "true"}) == {"d", "e"}


async def test_finding_ref(client, world):
    assert await _status(client, **{"finding-ref": str(world["cond"])}) == 400
    assert await _keys(client, world, **{"finding-ref": f"Condition/{world['cond']}"}) == {"a"}
    assert await _keys(client, world, **{"finding-ref:Condition": str(world["cond"])}) == {"a"}
    assert await _keys(client, world, **{"finding-ref": "Observation/160009"}) == {"c"}
    assert await _keys(client, world, **{"finding-ref:missing": "true"}) == {"b", "d", "e"}


async def test_supporting_info_is_reference_any(client, world):
    assert await _status(client, **{"supporting-info": str(world["cond"])}) == 400  # a bare id is ambiguous
    assert await _keys(client, world, **{"supporting-info": f"Condition/{world['cond']}"}) == {"a"}
    assert await _keys(client, world, **{"supporting-info": "Observation/160002"}) == {"a"}
    assert await _keys(client, world, **{"supporting-info": f"Patient/{world['p2']}"}) == {"b"}
    assert await _keys(client, world, **{"supporting-info:Condition": str(world["cond"])}) == {"a"}
    assert await _keys(client, world, **{"supporting-info:missing": "true"}) == {"c", "d", "e"}


# ── chaining ─────────────────────────────────────────────────────────────────


async def test_chains(client, world):
    assert await _keys(client, world, **{"patient.family": "Windsor"}) == {"a", "c"}
    assert await _keys(client, world, **{"subject:Patient.name": "Ben"}) == {"b"}
    assert await _keys(client, world, **{"assessor:Practitioner.family": "Careful"}) == {"a"}
    assert await _keys(client, world, **{"previous.status": "completed"}) == {"b"}  # b follows a (completed)
    assert await _keys(client, world, **{"previous.patient": str(world["p1"])}) == {"b"}
    assert await _keys(client, world, **{"problem:Condition.patient": str(world["p1"])}) == {"a"}
    assert await _keys(client, world, **{"problem:AllergyIntolerance.patient": str(world["p1"])}) == {"a", "b"}
    assert await _keys(client, world, **{"investigation:DiagnosticReport.patient": str(world["p1"])}) == {"a"}
    assert await _keys(client, world, **{"investigation:RiskAssessment.patient": str(world["p1"])}) == {"a"}
    assert await _keys(client, world, **{"investigation:FamilyMemberHistory.patient": str(world["p1"])}) == {"b"}
    assert await _keys(client, world, **{"finding-ref:Condition.patient": str(world["p1"])}) == {"a"}
    assert await _keys(client, world, **{"supporting-info:Condition.patient": str(world["p1"])}) == {"a"}
    assert await _keys(client, world, **{"supporting-info:Patient.family": "Fairfax"}) == {"b"}


async def test_bad_chains_are_400(client, world):
    assert await _status(client, **{"patient.nonsense": "x"}) == 400
    assert await _status(client, **{"subject.family": "x"}) == 400  # an untyped multi-target cannot be chained
    assert await _status(client, **{"subject:Group.name": "x"}) == 400  # Group is not searchable here
    assert await _status(client, **{"investigation:Observation.code": "x"}) == 400  # Observation is not built yet
    assert await _status(client, **{"status.x": "y"}) == 400  # a token cannot be chained through
    assert await _status(client, **{"date.x": "y"}) == 400


# ── _sort / _count / _offset / _total ────────────────────────────────────────


async def test_sort_by_every_declared_param(client, world):
    for key in ("assessor", "date", "encounter", "finding-code", "finding-ref", "identifier", "investigation",
                "patient", "previous", "problem", "status", "subject", "supporting-info", "_id"):
        assert (await _search(client, _sort=key))["total"] == 5, key


async def test_sort_by_date(client, world):
    async def ids(**params):
        return [int(e["resource"]["id"]) for e in (await _search(client, **params))["entry"]]

    assert await ids(**{"date:missing": "false", "_sort": "date"}) == [world["d"], world["a"], world["b"], world["e"]]
    assert await ids(**{"date:missing": "false", "_sort": "-date"}) == [world["e"], world["b"], world["a"], world["d"]]


async def test_default_sort_is_newest_first(client, world):
    got = [int(e["resource"]["id"]) for e in (await _search(client))["entry"]]
    assert got == sorted(got, reverse=True)


async def test_paging_and_total(client, world):
    page = await _search(client, _count=2, _sort="_id")
    assert page["total"] == 5 and len(page["entry"]) == 2
    assert any(link["relation"] == "next" for link in page["link"])
    nxt = await _search(client, _count=2, _offset=2, _sort="_id")
    assert not ({e["resource"]["id"] for e in page["entry"]} & {e["resource"]["id"] for e in nxt["entry"]})
    assert "entry" not in await _search(client, _count=0)
    assert "total" not in await _search(client, _total="none")


async def test_summary_count_and_elements(client, world):
    assert (await _search(client, _summary="count"))["total"] == 5
    resource = (await _search(client, _elements="status", _id=str(world["a"])))["entry"][0]["resource"]
    assert resource["status"] == "completed"
    assert "finding" not in resource and "summary" not in resource


# ── _include / _revinclude ───────────────────────────────────────────────────


async def test_include_subject_encounter_and_assessor(client, world):
    ids = f"{world['a']},{world['b']},{world['d']},{world['e']}"
    for param in ("patient", "subject"):
        bundle = await _search(client, _id=ids, _include=f"ClinicalImpression:{param}")
        assert _of_type(bundle, "Patient", "include") == {str(world["p1"]), str(world["p2"])}  # a Group adds nothing
    bundle = await _search(client, _id=ids, _include="ClinicalImpression:encounter")
    assert _of_type(bundle, "Encounter", "include") == {str(world["enc"])}
    bundle = await _search(client, _id=ids, _include="ClinicalImpression:assessor")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "PractitionerRole", "include") == {str(world["role"])}
    bundle = await _search(client, _id=ids, _include="ClinicalImpression:assessor:Practitioner")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "PractitionerRole", "include") == set()


async def test_include_previous(client, world):
    bundle = await _search(client, _id=str(world["b"]), _include="ClinicalImpression:previous")
    assert _of_type(bundle, "ClinicalImpression", "include") == {str(world["a"])}


async def test_include_problem_investigation_finding_and_supporting_info(client, world):
    ids = f"{world['a']},{world['b']}"
    bundle = await _search(client, _id=ids, _include="ClinicalImpression:problem")
    assert _of_type(bundle, "Condition", "include") == {str(world["cond"])}
    assert _of_type(bundle, "AllergyIntolerance", "include") == {str(world["allergy"])}
    bundle = await _search(client, _id=ids, _include="ClinicalImpression:problem:Condition")
    assert _of_type(bundle, "AllergyIntolerance", "include") == set()
    bundle = await _search(client, _id=ids, _include="ClinicalImpression:investigation")
    assert _of_type(bundle, "DiagnosticReport", "include") == {str(world["report"])}
    assert _of_type(bundle, "RiskAssessment", "include") == {str(world["risk"])}
    assert _of_type(bundle, "FamilyMemberHistory", "include") == {str(world["history"])}  # Observation / Media add nothing
    bundle = await _search(client, _id=ids, _include="ClinicalImpression:finding-ref")
    assert _of_type(bundle, "Condition", "include") == {str(world["cond"])}
    bundle = await _search(client, _id=ids, _include="ClinicalImpression:supporting-info")
    assert _of_type(bundle, "Condition", "include") == {str(world["cond"])}
    assert _of_type(bundle, "Patient", "include") == {str(world["p2"])}


async def test_revinclude_impressions_on_the_resources_they_point_at(client, world):
    for param in ("patient", "subject"):
        bundle = await _other(client, "patients", _id=str(world["p1"]), _revinclude=f"ClinicalImpression:{param}")
        assert _of_type(bundle, "ClinicalImpression", "include") == {str(world["a"]), str(world["c"])}
    bundle = await _other(client, "encounters", _id=str(world["enc"]), _revinclude="ClinicalImpression:encounter")
    assert _of_type(bundle, "ClinicalImpression", "include") == {str(world["a"])}
    bundle = await _other(client, "practitioners", _id=str(world["pr"]), _revinclude="ClinicalImpression:assessor")
    assert _of_type(bundle, "ClinicalImpression", "include") == {str(world["a"])}
    bundle = await _other(client, "practitioner-roles", _id=str(world["role"]), _revinclude="ClinicalImpression:assessor")
    assert _of_type(bundle, "ClinicalImpression", "include") == {str(world["b"])}
    bundle = await _other(client, "conditions", _id=str(world["cond"]), _revinclude="ClinicalImpression:problem")
    assert _of_type(bundle, "ClinicalImpression", "include") == {str(world["a"])}
    bundle = await _other(
        client, "allergy-intolerances", _id=str(world["allergy"]), _revinclude="ClinicalImpression:problem"
    )
    assert _of_type(bundle, "ClinicalImpression", "include") == {str(world["a"]), str(world["b"])}
    bundle = await _other(
        client, "diagnostic-reports", _id=str(world["report"]), _revinclude="ClinicalImpression:investigation"
    )
    assert _of_type(bundle, "ClinicalImpression", "include") == {str(world["a"])}
    bundle = await _other(
        client, "risk-assessments", _id=str(world["risk"]), _revinclude="ClinicalImpression:investigation"
    )
    assert _of_type(bundle, "ClinicalImpression", "include") == {str(world["a"])}
    bundle = await _other(
        client, "family-member-histories", _id=str(world["history"]), _revinclude="ClinicalImpression:investigation"
    )
    assert _of_type(bundle, "ClinicalImpression", "include") == {str(world["b"])}


async def test_revinclude_previous_on_itself(client, world):
    bundle = await _search(client, _id=str(world["a"]), _revinclude="ClinicalImpression:previous")
    assert _of_type(bundle, "ClinicalImpression", "include") == {str(world["b"])}


async def test_revinclude_is_tenant_scoped(client, other_client):
    from app.auth.dependencies import get_current_user
    from app.main import app
    from tests.conftest import make_test_user
    from tests.integration.clinical_impression.conftest import IMPRESSION_PERMS

    def as_user(**kw):
        app.dependency_overrides[get_current_user] = make_test_user(permissions=IMPRESSION_PERMS, **kw)

    as_user()
    mine = await create_patient(client)
    await create_impression(client, impression_body(mine))
    as_user(sub="u-other", org_id="org-other")
    try:
        # The other org cannot see the patient, so nothing reaches its impressions.
        bundle = await _other(other_client, "patients", _id=str(mine), _revinclude="ClinicalImpression:patient")
        assert bundle["total"] == 0 and "entry" not in bundle
        theirs = await create_patient(other_client)
        bundle = await _other(other_client, "patients", _id=str(theirs), _revinclude="ClinicalImpression:patient")
        assert _of_type(bundle, "ClinicalImpression", "include") == set()
    finally:
        as_user()


# ── combination rules / lenient vs strict ────────────────────────────────────


async def test_params_are_anded(client, world):
    assert await _keys(client, world, status="completed", **{"finding-code": "194828000"}) == {"a"}
    assert await _keys(client, world, status="in-progress", **{"finding-code": "194828000"}) == set()
    assert await _keys(client, world, patient=str(world["p1"]), status="entered-in-error") == {"c"}
    assert await _keys(client, world, date="ge2023", **{"finding-code": "194828000"}) == {"a"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"patient:text": "x"}) == 400
    assert await _status(client, **{"date:exact": "2020"}) == 400
    assert await _status(client, **{"identifier:below": "x"}) == 400
    assert await _status(client, **{"finding-code:nonsense": "x"}) == 400
    assert await _status(client, **{"status:text": "x"}) == 400


async def test_unknown_param_lenient_vs_strict(client, world):
    lenient = await client.get(BASE + "/", params={"nonsense": "1"})
    assert lenient.status_code == 200
    assert any(e["search"]["mode"] == "outcome" for e in lenient.json()["entry"])
    strict = await client.get(BASE + "/", params={"nonsense": "1"}, headers={"Prefer": "handling=strict"})
    assert strict.status_code == 400


async def test_query_param_refused(client, world):
    assert await _status(client, _query="x") == 400


# ── POST _search / Bundle shape ──────────────────────────────────────────────


async def test_post_search_form_encoded(client, world):
    resp = await client.post(BASE + "/_search", data={"status": "in-progress", "patient": str(world["p2"])})
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, identifier="CI-B")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/clinical-impressions/{world['b']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "ClinicalImpression"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
