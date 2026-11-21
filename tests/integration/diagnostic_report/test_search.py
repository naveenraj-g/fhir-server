"""FHIR R4 search over DiagnosticReport (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/diagnosticreport.html#search).

One block per search parameter — `category`, `code` and `conclusion` are tokens on
CodeableConcepts, `status` a token on a plain code, `identifier` a token on an
Identifier, `date` a dateTime-or-Period range, `issued` a date on an instant, the
single-target references (`encounter`, `patient`, `media`, `result`, `specimen`)
and the multi-target ones (`subject`, `performer`, `results-interpreter`,
`based-on`) — then chaining, `_include`/`_revinclude` in both directions, result
parameters, combination rules, lenient vs strict handling and POST _search.
"""

import pytest

from tests.integration.diagnostic_report.support import (
    API,
    BASE,
    LOINC,
    REPORT_IDS,
    SCT,
    STATUS_SYSTEM,
    V2_0074,
    V2_0203,
    create_encounter,
    create_location,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_report,
    encounter_body,
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


def _code(code, display=None):
    return {
        "coding": [
            {"system": LOINC, "code": code, **({"display": display} if display else {})}
        ]
    }


@pytest.fixture
async def world(client):
    """Two patients, a practitioner, a practitioner role, an organization, a location
    and two encounters, plus five reports with distinct, searchable values.
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
    w["enc1"] = await create_encounter(client, encounter_body())
    w["enc2"] = await create_encounter(client, encounter_body())
    w["a"] = await create_report(
        client,
        report_body(
            w["p1"],
            "final",
            identifier=[
                {
                    "system": REPORT_IDS,
                    "value": "DR-A",
                    "type": {
                        "coding": [{"system": V2_0203, "code": "FILL"}],
                        "text": "Report id",
                    },
                }
            ],
            basedOn=[{"reference": "ServiceRequest/80001"}],
            category=[
                {
                    "coding": [
                        {"system": V2_0074, "code": "LAB", "display": "Laboratory"}
                    ]
                }
            ],
            code=_code("58410-2", "CBC panel"),
            encounter={"reference": f"Encounter/{w['enc1']}"},
            effectivePeriod={
                "start": "2023-01-15T09:30:00Z",
                "end": "2023-01-15T10:00:00Z",
            },
            issued="2023-01-15T12:00:00Z",
            performer=[
                {"reference": f"Practitioner/{w['pr']}"},
                {"reference": f"Organization/{w['org']}"},
            ],
            resultsInterpreter=[{"reference": f"PractitionerRole/{w['role']}"}],
            specimen=[{"reference": "Specimen/310001"}],
            result=[
                {"reference": "Observation/160001"},
                {"reference": "Observation/160002"},
            ],
            media=[{"link": {"reference": "Media/9"}}],
            conclusionCode=[
                {"coding": [{"system": SCT, "code": "17621005", "display": "Normal"}]}
            ],
        ),
    )
    w["b"] = await create_report(
        client,
        report_body(
            w["p2"],
            "preliminary",
            identifier=[{"system": REPORT_IDS, "value": "DR-B"}],
            category=[
                {"coding": [{"system": V2_0074, "code": "RAD", "display": "Radiology"}]}
            ],
            code=_code("24323-8", "Comprehensive metabolic panel"),
            encounter={"reference": f"Encounter/{w['enc2']}"},
            effectiveDateTime="2024-02",
            issued="2024-02-03T08:00:00Z",
            performer=[{"reference": f"Practitioner/{w['pr']}"}],
            resultsInterpreter=[{"reference": f"Practitioner/{w['pr']}"}],
            conclusionCode=[{"text": "Borderline"}],
        ),
    )
    w["c"] = await create_report(
        client,
        report_body(
            w["p1"],
            "amended",
            code={"text": "Physio report"},
            performer=[{"reference": "CareTeam/7"}],
            specimen=[{"reference": "Specimen/310002"}],
        ),
    )
    w["d"] = await create_report(
        client,
        {
            "status": "cancelled",
            "code": {"text": "Cancelled"},
            "subject": {"reference": f"Location/{w['loc']}"},
        },
    )
    w["e"] = await create_report(
        client,
        {
            "status": "entered-in-error",
            "code": {"text": "Error"},
            "subject": {
                "identifier": {"system": "urn:pts", "value": "P-9"},
                "display": "External",
            },
            "effectivePeriod": {"start": "2019-01-01"},
            "performer": [{"identifier": {"system": "urn:who", "value": "W-1"}}],
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


# ── status ───────────────────────────────────────────────────────────────────


async def test_status(client, world):
    assert await _keys(client, world, status="final") == {"a"}
    assert await _keys(client, world, status="preliminary,amended") == {"b", "c"}
    assert await _keys(client, world, status="entered-in-error") == {
        "e"
    }  # the real FHIR code
    assert await _keys(client, world, status=f"{STATUS_SYSTEM}|cancelled") == {"d"}
    assert await _keys(client, world, status="http://wrong|final") == set()
    assert (
        await _keys(client, world, status="|final") == set()
    )  # a code with no system is not this one
    assert await _keys(client, world, status="nonsense") == set()
    assert await _keys(client, world, **{"status:not": "final"}) == {"b", "c", "d", "e"}
    assert (
        await _status(client, **{"status:text": "final"}) == 400
    )  # a plain code has no :text


# ── category / code / conclusion ─────────────────────────────────────────────


async def test_category(client, world):
    assert await _keys(client, world, category="LAB") == {"a"}
    assert await _keys(client, world, category=f"{V2_0074}|RAD") == {"b"}
    assert await _keys(client, world, category="LAB,RAD") == {"a", "b"}
    assert await _keys(client, world, category="http://wrong|LAB") == set()
    assert await _keys(client, world, **{"category:text": "radio"}) == {
        "b"
    }  # Coding.display
    assert await _keys(client, world, **{"category:missing": "true"}) == {"c", "d", "e"}


async def test_code(client, world):
    assert await _keys(client, world, code="58410-2") == {"a"}
    assert await _keys(client, world, code=f"{LOINC}|24323-8") == {"b"}
    assert await _keys(client, world, code=f"{LOINC}|") == {"a", "b"}
    assert await _keys(client, world, **{"code:text": "physio"}) == {
        "c"
    }  # a text-only concept is found
    assert await _keys(client, world, **{"code:text": "comprehensive"}) == {"b"}
    assert await _keys(client, world, **{"code:not": "58410-2"}) == {"b", "c", "d", "e"}
    assert (
        await _keys(client, world, **{"code:missing": "true"}) == set()
    )  # R4 requires a code


async def test_conclusion_reads_conclusion_code(client, world):
    assert await _keys(client, world, conclusion="17621005") == {"a"}
    assert await _keys(client, world, **{"conclusion:text": "borderline"}) == {
        "b"
    }  # a text-only concept
    assert await _keys(client, world, **{"conclusion:text": "normal"}) == {"a"}
    assert await _keys(client, world, **{"conclusion:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


# ── identifier ───────────────────────────────────────────────────────────────


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="DR-A") == {"a"}
    assert await _keys(client, world, identifier=f"{REPORT_IDS}|DR-B") == {"b"}
    assert await _keys(client, world, identifier="DR-A,DR-B") == {"a", "b"}
    assert await _keys(client, world, identifier="urn:other|DR-A") == set()


async def test_identifier_text_of_type_not_and_missing(client, world):
    assert await _keys(client, world, **{"identifier:text": "report"}) == {"a"}
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|FILL|DR-A"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|FILL|DR-B"})
        == set()
    )
    assert await _keys(client, world, **{"identifier:not": "DR-A"}) == ALL - {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


# ── date (effective[x]) / issued ─────────────────────────────────────────────


async def test_date_reads_a_period_or_a_datetime(client, world):
    assert await _keys(client, world, date="2023-01-15") == {
        "a"
    }  # the day holds the whole period
    assert (
        await _keys(client, world, date="2023-01-15T09:30") == set()
    )  # a minute does not
    assert await _keys(client, world, date="2024-02") == {"b"}  # the dateTime `2024-02`
    assert await _keys(client, world, date="2024") == {"b"}
    assert await _keys(client, world, date="ge2024") == {
        "b",
        "e",
    }  # e's period is open-ended
    assert await _keys(client, world, date="lt2020") == {"e"}
    assert await _keys(client, world, date="lt2019") == set()
    assert await _keys(client, world, **{"date:missing": "true"}) == {"c", "d"}
    assert await _status(client, date="banana") == 400


async def test_issued_is_an_instant(client, world):
    assert await _keys(client, world, issued="2023-01-15") == {"a"}
    assert await _keys(client, world, issued="2023-01-15T12:00:00Z") == {"a"}
    assert await _keys(client, world, issued="2023-01-15T13:00:00Z") == set()
    assert await _keys(client, world, issued="ge2024") == {"b"}
    assert await _keys(client, world, issued="lt2024") == {"a"}
    assert await _keys(client, world, **{"issued:missing": "true"}) == {"c", "d", "e"}
    assert await _status(client, issued="banana") == 400


# ── patient / subject / encounter ────────────────────────────────────────────


async def test_subject_is_multi_target(client, world):
    assert (
        await _status(client, subject=str(world["p1"])) == 400
    )  # a bare id with four targets is ambiguous
    assert await _keys(client, world, subject=f"Patient/{world['p1']}") == {"a", "c"}
    assert await _keys(client, world, subject=f"Location/{world['loc']}") == {"d"}
    assert await _keys(client, world, **{"subject:Patient": str(world["p2"])}) == {"b"}
    assert await _keys(client, world, **{"subject:Location": str(world["loc"])}) == {
        "d"
    }
    assert (
        await _keys(client, world, subject=f"Group/{world['p1']}") == set()
    )  # the type is part of the match
    assert await _keys(client, world, **{"subject:identifier": "urn:pts|P-9"}) == {"e"}
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
    assert await _keys(client, world, patient="999999") == set()
    assert await _keys(client, world, **{"patient:missing": "true"}) == {
        "d",
        "e",
    }  # a Location / logical subject
    assert await _keys(client, world, **{"patient:missing": "false"}) == {"a", "b", "c"}


async def test_encounter(client, world):
    assert await _keys(client, world, encounter=str(world["enc1"])) == {"a"}
    assert await _keys(client, world, encounter=f"Encounter/{world['enc2']}") == {"b"}
    assert await _keys(client, world, **{"encounter:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


# ── performer / results-interpreter ──────────────────────────────────────────


async def test_performer_and_results_interpreter_are_separate(client, world):
    assert (
        await _status(client, performer=str(world["pr"])) == 400
    )  # four targets: needs a type
    assert await _keys(client, world, performer=f"Practitioner/{world['pr']}") == {
        "a",
        "b",
    }
    assert await _keys(client, world, performer=f"Organization/{world['org']}") == {
        "a"
    }  # a has two performers
    assert await _keys(
        client, world, **{"performer:Practitioner": str(world["pr"])}
    ) == {"a", "b"}
    assert await _keys(client, world, performer="CareTeam/7") == {
        "c"
    }  # not a resource here, still searchable
    assert await _keys(client, world, **{"performer:identifier": "urn:who|W-1"}) == {
        "e"
    }
    assert await _keys(client, world, **{"performer:missing": "true"}) == {"d"}
    # the interpreter is a different list: b's interpreter is the practitioner, a's is the role
    assert await _keys(
        client, world, **{"results-interpreter": f"Practitioner/{world['pr']}"}
    ) == {"b"}
    assert await _keys(
        client, world, **{"results-interpreter": f"PractitionerRole/{world['role']}"}
    ) == {"a"}
    assert await _keys(client, world, **{"results-interpreter:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


# ── based-on / media / result / specimen ─────────────────────────────────────


async def test_based_on(client, world):
    assert await _status(client, **{"based-on": "80001"}) == 400
    assert await _keys(client, world, **{"based-on": "ServiceRequest/80001"}) == {"a"}
    assert await _keys(client, world, **{"based-on:ServiceRequest": "80001"}) == {"a"}
    assert await _keys(client, world, **{"based-on:CarePlan": "80001"}) == set()
    assert await _keys(client, world, **{"based-on:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }


async def test_media_result_and_specimen_have_one_target(client, world):
    assert await _keys(client, world, media="9") == {"a"}  # a bare id works
    assert await _keys(client, world, media="Media/9") == {"a"}
    assert await _keys(client, world, result="160001") == {"a"}
    assert await _keys(client, world, result="160001,160002") == {"a"}
    assert await _keys(client, world, result="Observation/160002") == {"a"}
    assert await _keys(client, world, specimen="310001") == {"a"}
    assert await _keys(client, world, specimen="310002") == {"c"}
    assert await _keys(client, world, **{"specimen:missing": "true"}) == {"b", "d", "e"}
    assert await _keys(client, world, **{"media:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }
    assert await _keys(client, world, result="999") == set()


# ── chaining ─────────────────────────────────────────────────────────────────


async def test_chains(client, world):
    assert await _keys(client, world, **{"patient.family": "Windsor"}) == {"a", "c"}
    assert await _keys(client, world, **{"subject:Patient.name": "Ben"}) == {"b"}
    assert await _keys(client, world, **{"subject:Location.name": "North"}) == {"d"}
    assert await _keys(client, world, **{"encounter.status": "in-progress"}) == {
        "a",
        "b",
    }
    assert await _keys(
        client, world, **{"performer:Practitioner.family": "Careful"}
    ) == {"a", "b"}
    assert await _keys(
        client, world, **{"performer:Organization.name": "Providing"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"results-interpreter:PractitionerRole.active": "true"}
    ) == {"a"}


async def test_bad_chains_are_400(client, world):
    assert await _status(client, **{"patient.nonsense": "x"}) == 400
    assert (
        await _status(client, **{"subject.family": "x"}) == 400
    )  # an untyped multi-target cannot be chained
    assert (
        await _status(client, **{"subject:Group.name": "x"}) == 400
    )  # Group is not searchable here
    assert await _status(client, **{"performer:CareTeam.name": "x"}) == 400
    assert (
        await _status(client, **{"result.code": "x"}) == 400
    )  # Observation is not a resource here
    assert (
        await _status(client, **{"code.x": "y"}) == 400
    )  # a token cannot be chained through


# ── _sort / _count / _offset / _total ────────────────────────────────────────


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "based-on",
        "category",
        "code",
        "conclusion",
        "date",
        "encounter",
        "identifier",
        "issued",
        "media",
        "patient",
        "performer",
        "result",
        "results-interpreter",
        "specimen",
        "status",
        "subject",
        "_id",
    ):
        assert (await _search(client, _sort=key))["total"] == 5, key
    assert await _status(client, _sort="conclusion-text") == 400


async def test_sort_by_issued_and_date(client, world):
    async def ids(**params):
        return [
            int(e["resource"]["id"]) for e in (await _search(client, **params))["entry"]
        ]

    assert await ids(**{"issued:missing": "false", "_sort": "issued"}) == [
        world["a"],
        world["b"],
    ]
    assert await ids(**{"issued:missing": "false", "_sort": "-issued"}) == [
        world["b"],
        world["a"],
    ]
    assert await ids(**{"date:missing": "false", "_sort": "date"}) == [
        world["e"],
        world["a"],
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
    assert resource["status"] == "final"
    assert "performer" not in resource and "media" not in resource


# ── _include / _revinclude ───────────────────────────────────────────────────


async def test_include_subject_and_encounter(client, world):
    ids = f"{world['a']},{world['b']},{world['d']}"
    for param in ("patient", "subject"):
        bundle = await _search(client, _id=ids, _include=f"DiagnosticReport:{param}")
        assert _of_type(bundle, "Patient", "include") == {
            str(world["p1"]),
            str(world["p2"]),
        }
    bundle = await _search(client, _id=ids, _include="DiagnosticReport:subject")
    assert _of_type(bundle, "Location", "include") == {
        str(world["loc"])
    }  # a Location subject comes too
    bundle = await _search(client, _id=ids, _include="DiagnosticReport:patient")
    assert _of_type(bundle, "Location", "include") == set()
    bundle = await _search(client, _id=ids, _include="DiagnosticReport:encounter")
    assert _of_type(bundle, "Encounter", "include") == {
        str(world["enc1"]),
        str(world["enc2"]),
    }


async def test_include_skips_non_resources(client, world):
    bundle = await _search(
        client, _id=str(world["e"]), _include="DiagnosticReport:subject"
    )
    assert (
        _of_type(bundle, "Patient", "include") == set()
    )  # a logical subject adds nothing


async def test_include_performer_brings_in_every_modeled_type(client, world):
    ids = f"{world['a']},{world['b']},{world['c']},{world['e']}"
    bundle = await _search(client, _id=ids, _include="DiagnosticReport:performer")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "Organization", "include") == {
        str(world["org"])
    }  # a CareTeam adds nothing
    bundle = await _search(
        client, _id=ids, _include="DiagnosticReport:performer:Organization"
    )
    assert _of_type(bundle, "Organization", "include") == {str(world["org"])}
    assert _of_type(bundle, "Practitioner", "include") == set()
    bundle = await _search(
        client, _id=ids, _include="DiagnosticReport:results-interpreter"
    )
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "PractitionerRole", "include") == {str(world["role"])}


async def _other(client, path, **params) -> dict:
    resp = await client.get(f"{API}/{path}/", params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_revinclude_reports_on_the_resources_they_point_at(client, world):
    for param in ("patient", "subject"):
        bundle = await _other(
            client,
            "patients",
            _id=str(world["p2"]),
            _revinclude=f"DiagnosticReport:{param}",
        )
        assert _of_type(bundle, "DiagnosticReport", "include") == {str(world["b"])}
    bundle = await _other(
        client, "patients", _id=str(world["p1"]), _revinclude="DiagnosticReport:patient"
    )
    assert _of_type(bundle, "DiagnosticReport", "include") == {
        str(world["a"]),
        str(world["c"]),
    }
    bundle = await _other(
        client,
        "locations",
        _id=str(world["loc"]),
        _revinclude="DiagnosticReport:subject",
    )
    assert _of_type(bundle, "DiagnosticReport", "include") == {str(world["d"])}
    bundle = await _other(
        client,
        "encounters",
        _id=str(world["enc1"]),
        _revinclude="DiagnosticReport:encounter",
    )
    assert _of_type(bundle, "DiagnosticReport", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "practitioners",
        _id=str(world["pr"]),
        _revinclude="DiagnosticReport:performer",
    )
    assert _of_type(bundle, "DiagnosticReport", "include") == {
        str(world["a"]),
        str(world["b"]),
    }
    bundle = await _other(
        client,
        "practitioners",
        _id=str(world["pr"]),
        _revinclude="DiagnosticReport:results-interpreter",
    )
    assert _of_type(bundle, "DiagnosticReport", "include") == {str(world["b"])}
    bundle = await _other(
        client,
        "practitioner-roles",
        _id=str(world["role"]),
        _revinclude="DiagnosticReport:results-interpreter",
    )
    assert _of_type(bundle, "DiagnosticReport", "include") == {str(world["a"])}


async def test_revinclude_what_points_at_a_diagnostic_report(client, world):
    ref = f"DiagnosticReport/{world['a']}"
    procedure = (
        await client.post(
            f"{API}/procedures/",
            json={
                "status": "completed",
                "subject": {"reference": f"Patient/{world['p1']}"},
                "reasonReference": [{"reference": ref}],
                "report": [{"reference": ref}],
            },
        )
    ).json()["id"]

    def go(**params):
        return _search(client, _id=str(world["a"]), **params)

    assert _of_type(
        await go(_revinclude="Procedure:reason-reference"), "Procedure", "include"
    ) == {procedure}
    # ...and the other way round: _include the DiagnosticReports a Procedure points at.
    bundle = await _other(
        client, "procedures", _id=procedure, _include="Procedure:reason-reference"
    )
    assert _of_type(bundle, "DiagnosticReport", "include") == {str(world["a"])}
    # And a DiagnosticReport can be chained to from it.
    bundle = await _other(
        client, "procedures", **{"reason-reference:DiagnosticReport.status": "final"}
    )
    assert _ids(bundle) == {int(procedure)}
    bundle = await _other(
        client, "procedures", **{"reason-reference:DiagnosticReport.status": "amended"}
    )
    assert _ids(bundle) == set()


async def test_revinclude_is_tenant_scoped(client, other_client):
    from app.auth.dependencies import get_current_user
    from app.main import app
    from tests.conftest import make_test_user
    from tests.integration.diagnostic_report.conftest import REPORT_PERMS

    def as_user(**kw):
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=REPORT_PERMS, **kw
        )

    as_user()
    mine = await create_patient(client)
    await create_report(client, report_body(mine))
    as_user(sub="u-other", org_id="org-other")
    try:
        # The other org cannot see the patient, so nothing reaches its reports.
        bundle = await _other(
            other_client,
            "patients",
            _id=str(mine),
            _revinclude="DiagnosticReport:patient",
        )
        assert bundle["total"] == 0 and "entry" not in bundle
        theirs = await create_patient(other_client)
        bundle = await _other(
            other_client,
            "patients",
            _id=str(theirs),
            _revinclude="DiagnosticReport:patient",
        )
        assert _of_type(bundle, "DiagnosticReport", "include") == set()
    finally:
        as_user()


# ── combination rules / lenient vs strict ────────────────────────────────────


async def test_params_are_anded(client, world):
    assert await _keys(client, world, status="final", category="LAB") == {"a"}
    assert await _keys(client, world, status="final", category="RAD") == set()
    assert await _keys(client, world, patient=str(world["p1"]), status="amended") == {
        "c"
    }
    assert await _keys(client, world, code="58410-2", date="ge2023") == {"a"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"status:above": "x"}) == 400
    assert await _status(client, **{"patient:text": "x"}) == 400
    assert await _status(client, **{"date:exact": "2020"}) == 400
    assert await _status(client, **{"issued:contains": "2020"}) == 400


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
        BASE + "/_search", data={"status": "preliminary", "patient": str(world["p2"])}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, status="preliminary")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/diagnostic-reports/{world['b']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "DiagnosticReport"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
