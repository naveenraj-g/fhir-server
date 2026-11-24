"""FHIR R4 search over MeasureReport (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/measurereport.html#search).

One block per search parameter - `status` a code, `date` a dateTime range, `period` a Period range,
`identifier` a token, the multi-target `subject` / `reporter`, `patient` (`subject` narrowed to
Patients), `evaluated-resource` (Reference(Any)) and `measure` (a canonical URL resolved against
the stored Measure's own `url`) - then chaining, `_include` / `_revinclude`, `_sort` and paging."""

import pytest

from tests.integration.measure_report.support import (
    BASE,
    MEASURE_URL,
    create_group,
    create_measure,
    create_measure_report,
    create_organization,
    create_patient,
    create_practitioner,
    group_body,
    measure_body,
    measure_report_body,
)

API = "/api/fhir/v1"


def _ids(bundle: dict) -> set[int]:
    return {
        int(e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == "match"
    }


async def _search(client, **params) -> dict:
    resp = await client.get(BASE + "/", params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _found(client, **params) -> set[int]:
    return _ids(await _search(client, **params))


# -- status / date / period ------------------------------------------------------------------


async def test_status(client):
    done = await create_measure_report(client, measure_report_body(status="complete"))
    wait = await create_measure_report(client, measure_report_body(status="pending"))
    assert await _found(client, status="complete") == {done}
    assert await _found(client, status="pending,error") == {wait}
    assert done in await _found(client, **{"status:not": "pending"})
    assert await _found(
        client, status="http://hl7.org/fhir/measure-report-status|complete"
    ) == {done}
    assert await _found(client, status="urn:other|complete") == set()
    assert await _found(client, status="bogus") == set()


async def test_date_ranges_and_missing(client):
    early = await create_measure_report(client, measure_report_body(date="2026-01-10"))
    late = await create_measure_report(
        client, measure_report_body(date="2026-06-10T12:00:00Z")
    )
    none = await create_measure_report(client, measure_report_body())
    assert await _found(client, date="2026-01-10") == {early}
    assert await _found(client, date="2026-06") == {late}
    assert await _found(client, date="ge2026-03-01") == {late}
    assert await _found(client, date="lt2026-03-01") == {early}
    assert await _found(client, date=["ge2026-01-01", "le2026-12-31"]) == {early, late}
    assert await _found(client, **{"date:missing": "true"}) == {none}
    assert none not in await _found(client, **{"date:missing": "false"})


async def test_period_overlap_semantics(client):
    jan = await create_measure_report(
        client, measure_report_body(period={"start": "2026-01-01", "end": "2026-01-31"})
    )
    open_end = await create_measure_report(
        client, measure_report_body(period={"start": "2026-06-01"})
    )
    assert await _found(client, period="2026") == {jan, open_end} - {open_end}
    assert await _found(client, period="ge2026-05-01") == {open_end}
    assert await _found(client, period="le2026-02-01") == {jan}
    assert await _found(client, period="sa2026-02-01") == {open_end}
    assert await _found(client, period="eb2026-02-01") == {jan}
    assert await _found(client, period="gt2030-01-01") == {open_end}


# -- identifier --------------------------------------------------------------------------------


async def test_identifier_variants(client):
    one = await create_measure_report(
        client,
        measure_report_body(
            identifier=[
                {
                    "system": "urn:mr",
                    "value": "MR-1",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "ACSN",
                            }
                        ],
                        "text": "Accession",
                    },
                }
            ]
        ),
    )
    two = await create_measure_report(
        client, measure_report_body(identifier=[{"system": "urn:mr", "value": "MR-2"}])
    )
    assert await _found(client, identifier="MR-1") == {one}
    assert await _found(client, identifier="urn:mr|MR-2") == {two}
    assert await _found(client, identifier="urn:mr|") == {one, two}
    assert await _found(client, identifier="urn:other|MR-1") == set()
    assert await _found(client, identifier="MR-1,MR-2") == {one, two}
    assert two in await _found(client, **{"identifier:not": "MR-1"})
    assert await _found(
        client,
        **{
            "identifier:of-type": "http://terminology.hl7.org/CodeSystem/v2-0203|ACSN|MR-1"
        },
    ) == {one}
    assert await _found(client, **{"identifier:text": "accession"}) == {one}


# -- subject / patient / reporter ---------------------------------------------------------------


async def test_subject_patient_and_reporter(client):
    patient = await create_patient(client)
    group = await create_group(client, group_body())
    organization = await create_organization(client)
    practitioner = await create_practitioner(client)
    for_patient = await create_measure_report(
        client,
        measure_report_body(
            subject={"reference": f"Patient/{patient}"},
            reporter={"reference": f"Organization/{organization}"},
        ),
    )
    for_group = await create_measure_report(
        client,
        measure_report_body(
            subject={"reference": f"Group/{group}"},
            reporter={"reference": f"Practitioner/{practitioner}"},
        ),
    )
    nobody = await create_measure_report(client, measure_report_body())

    assert await _found(client, subject=f"Patient/{patient}") == {for_patient}
    assert await _found(client, **{"subject:Group": str(group)}) == {for_group}
    assert await _found(client, subject=f"Group/{group}") == {for_group}
    # `patient` is `subject` narrowed to Patients; a bare id works
    assert await _found(client, patient=str(patient)) == {for_patient}
    assert await _found(client, patient=f"Patient/{patient}") == {for_patient}
    assert await _found(client, patient=str(group)) == set()
    # a bare id on a multi-target element is ambiguous
    assert (
        await client.get(BASE + "/", params={"subject": str(patient)})
    ).status_code == 400
    assert (
        await client.get(BASE + "/", params={"reporter": str(organization)})
    ).status_code == 400

    assert await _found(client, reporter=f"Organization/{organization}") == {
        for_patient
    }
    assert await _found(client, **{"reporter:Practitioner": str(practitioner)}) == {
        for_group
    }
    assert await _found(client, **{"subject:missing": "true"}) == {nobody}
    assert await _found(client, **{"patient:missing": "true"}) == {for_group, nobody}
    assert await _found(client, **{"reporter:missing": "false"}) == {
        for_patient,
        for_group,
    }


async def test_subject_identifier_modifier(client):
    logical = {"identifier": {"system": "urn:mrn", "value": "M-9"}}
    report = await create_measure_report(client, measure_report_body(subject=logical))
    assert await _found(client, **{"subject:identifier": "urn:mrn|M-9"}) == {report}
    assert await _found(client, **{"subject:identifier": "urn:mrn|M-0"}) == set()
    # a logical subject counts as missing a patient
    assert report in await _found(client, **{"patient:missing": "true"})


# -- evaluated-resource --------------------------------------------------------------------------


async def test_evaluated_resource(client):
    patient = await create_patient(client)
    other = await create_patient(client)
    report = await create_measure_report(
        client,
        measure_report_body(
            evaluatedResource=[
                {"reference": f"Patient/{patient}"},
                {"reference": "Device/9"},
            ]
        ),
    )
    await create_measure_report(
        client,
        measure_report_body(evaluatedResource=[{"reference": f"Patient/{other}"}]),
    )
    bare = await client.get(BASE + "/", params={"evaluated-resource": str(patient)})
    assert bare.status_code == 400  # Reference(Any): a bare id is ambiguous
    assert await _found(client, **{"evaluated-resource": f"Patient/{patient}"}) == {
        report
    }
    assert await _found(client, **{"evaluated-resource:Patient": str(patient)}) == {
        report
    }
    assert await _found(client, **{"evaluated-resource": "Device/9"}) == {report}
    assert await _found(client, **{"evaluated-resource:missing": "false"}) == (
        await _found(client, **{"evaluated-resource:Patient": f"{patient},{other}"})
    )


async def test_evaluated_resource_chains_into_a_rebuilt_type(client):
    patient = await create_patient(client)
    report = await create_measure_report(
        client,
        measure_report_body(evaluatedResource=[{"reference": f"Patient/{patient}"}]),
    )
    patient_resource = (await client.get(f"{API}/patients/{patient}")).json()
    family = patient_resource["name"][0]["family"]
    assert await _found(client, **{"evaluated-resource:Patient.family": family}) == {
        report
    }
    assert (
        await _found(client, **{"evaluated-resource:Patient.family": "Nobody"}) == set()
    )


# -- measure (canonical URL) ----------------------------------------------------------------------


async def test_measure_matches_the_canonical_string(client):
    unversioned = await create_measure_report(
        client, measure_report_body(measure=MEASURE_URL)
    )
    v1 = await create_measure_report(
        client, measure_report_body(measure=f"{MEASURE_URL}|1.0")
    )
    v2 = await create_measure_report(
        client, measure_report_body(measure=f"{MEASURE_URL}|2.0")
    )
    other = await create_measure_report(
        client,
        measure_report_body(measure="https://fhir-server.dev/fhir/Measure/other"),
    )
    # an unversioned search finds every stored version of that url
    assert await _found(client, measure=MEASURE_URL) == {unversioned, v1, v2}
    assert await _found(client, measure=f"{MEASURE_URL}|1.0") == {v1}
    assert await _found(client, measure=f"{MEASURE_URL}|3.0") == set()
    assert await _found(
        client, measure="https://fhir-server.dev/fhir/Measure/other"
    ) == {other}
    # a bare id works (one target) but a canonical never matches it
    assert await _found(client, measure="999999") == set()


async def test_measure_resolves_against_the_stored_measure(client):
    stored = await create_measure(
        client, measure_body(url=MEASURE_URL, title="Readmission rate", version="1.0")
    )
    other_measure = await create_measure(
        client,
        measure_body(url="https://fhir-server.dev/fhir/Measure/other", title="Other"),
    )
    by_url = await create_measure_report(
        client, measure_report_body(measure=MEASURE_URL)
    )
    by_version = await create_measure_report(
        client, measure_report_body(measure=f"{MEASURE_URL}|1.0")
    )
    by_id = await create_measure_report(
        client, measure_report_body(measure=f"Measure/{stored}")
    )
    elsewhere = await create_measure_report(
        client,
        measure_report_body(measure="https://fhir-server.dev/fhir/Measure/other"),
    )
    # chaining through the canonical
    assert await _found(client, **{"measure.title": "Readmission"}) == {
        by_url,
        by_version,
        by_id,
    }
    assert await _found(client, **{"measure.title": "Other"}) == {elsewhere}
    # a relative Measure/<id> matches by its id
    assert await _found(client, measure=f"Measure/{stored}") == {by_id}
    assert other_measure != stored


async def test_measure_include_and_revinclude(client):
    stored = await create_measure(
        client, measure_body(url=MEASURE_URL, title="Readmission rate")
    )
    report = await create_measure_report(
        client, measure_report_body(measure=MEASURE_URL)
    )
    await create_measure_report(
        client, measure_report_body(measure="https://fhir-server.dev/fhir/Measure/none")
    )
    bundle = await _search(
        client, _include="MeasureReport:measure", **{"_id": str(report)}
    )
    included = {
        e["resource"]["id"] for e in bundle["entry"] if e["search"]["mode"] == "include"
    }
    assert included == {str(stored)}

    resp = await client.get(
        f"{API}/measures/", params={"_revinclude": "MeasureReport:measure"}
    )
    assert resp.status_code == 200, resp.text
    reverse = {
        e["resource"]["id"]
        for e in resp.json()["entry"]
        if e["search"]["mode"] == "include"
        and e["resource"]["resourceType"] == "MeasureReport"
    }
    assert reverse == {str(report)}


async def test_measure_missing(client):
    with_measure = await create_measure_report(client, measure_report_body())
    assert await _found(client, **{"measure:missing": "false"}) == {with_measure}
    assert await _found(client, **{"measure:missing": "true"}) == set()


# -- chaining, includes ------------------------------------------------------------------------------


async def test_chain_through_subject_and_reporter(client):
    patient = await create_patient(client)
    organization = await create_organization(client, name="Reporting Hospital")
    report = await create_measure_report(
        client,
        measure_report_body(
            subject={"reference": f"Patient/{patient}"},
            reporter={"reference": f"Organization/{organization}"},
        ),
    )
    family = (await client.get(f"{API}/patients/{patient}")).json()["name"][0]["family"]
    assert await _found(client, **{"patient.family": family}) == {report}
    assert await _found(client, **{"subject:Patient.family": family}) == {report}
    assert await _found(client, **{"reporter:Organization.name": "Reporting"}) == {
        report
    }
    assert await _found(client, **{"reporter:Organization.name": "Nowhere"}) == set()


async def test_include_subject_and_reporter(client):
    patient = await create_patient(client)
    organization = await create_organization(client)
    report = await create_measure_report(
        client,
        measure_report_body(
            subject={"reference": f"Patient/{patient}"},
            reporter={"reference": f"Organization/{organization}"},
        ),
    )
    bundle = await _search(
        client,
        _id=str(report),
        _include=["MeasureReport:patient", "MeasureReport:reporter"],
    )
    included = {
        (e["resource"]["resourceType"], e["resource"]["id"])
        for e in bundle["entry"]
        if e["search"]["mode"] == "include"
    }
    assert included == {("Patient", str(patient)), ("Organization", str(organization))}


async def test_revinclude_from_patient_and_organization(client):
    patient = await create_patient(client)
    organization = await create_organization(client)
    report = await create_measure_report(
        client,
        measure_report_body(
            subject={"reference": f"Patient/{patient}"},
            reporter={"reference": f"Organization/{organization}"},
        ),
    )
    for url, param in (
        (f"{API}/patients/", "MeasureReport:patient"),
        (f"{API}/patients/", "MeasureReport:subject"),
        (f"{API}/organizations/", "MeasureReport:reporter"),
    ):
        resp = await client.get(url, params={"_revinclude": param})
        assert resp.status_code == 200, (param, resp.text)
        included = {
            e["resource"]["id"]
            for e in resp.json()["entry"]
            if e["search"]["mode"] == "include"
            and e["resource"]["resourceType"] == "MeasureReport"
        }
        assert included == {str(report)}, param


# -- common parameters, paging, sort -------------------------------------------------------------------


async def test_id_and_last_updated(client):
    report = await create_measure_report(client, measure_report_body())
    assert await _found(client, _id=str(report)) == {report}
    assert await _found(client, _id="999999") == set()
    assert report in await _found(client, _lastUpdated="ge2020-01-01")
    assert await _found(client, _lastUpdated="lt2020-01-01") == set()


async def test_sort_and_paging(client):
    ids = [
        await create_measure_report(
            client, measure_report_body(date=f"2026-0{m}-01", status="complete")
        )
        for m in (3, 1, 2)
    ]
    ordered = (await _search(client, _sort="date"))["entry"]
    assert [int(e["resource"]["id"]) for e in ordered] == [ids[1], ids[2], ids[0]]
    descending = (await _search(client, _sort="-date"))["entry"]
    assert [int(e["resource"]["id"]) for e in descending] == [ids[0], ids[2], ids[1]]
    page = await _search(client, _sort="date", _count=2)
    assert page["total"] == 3 and len(page["entry"]) == 2
    assert any(link["relation"] == "next" for link in page["link"])
    assert (await _search(client, _count=0))["total"] == 3


async def test_post_search_matches_get(client):
    report = await create_measure_report(
        client, measure_report_body(status="pending", date="2026-05-05")
    )
    resp = await client.post(
        BASE + "/_search",
        data={"status": "pending", "date": "2026-05-05"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {report}


async def test_summary_and_elements(client):
    report = await create_measure_report(client, measure_report_body())
    bundle = await _search(client, _id=str(report), _elements="status")
    resource = bundle["entry"][0]["resource"]
    assert resource["status"] == "complete"
    assert "group" not in resource and "date" not in resource
    # mandatory elements survive a summary
    summary = (await _search(client, _id=str(report), _summary="text"))["entry"][0][
        "resource"
    ]
    assert {"status", "type", "measure", "period"} <= set(summary)


@pytest.mark.parametrize(
    "param", ["group", "type", "improvement-notation", "report-type"]
)
async def test_unsearchable_elements_are_unknown_parameters(client, param):
    """R4 defines no search parameter for these: ignored by default, a 400 under strict handling."""
    await create_measure_report(client, measure_report_body())
    resp = await client.get(BASE + "/", params={param: "x"})
    assert resp.status_code == 200
    strict = await client.get(
        BASE + "/", params={param: "x"}, headers={"Prefer": "handling=strict"}
    )
    assert strict.status_code == 400


async def test_unknown_modifier_is_rejected(client):
    resp = await client.get(BASE + "/", params={"status:exact": "complete"})
    assert resp.status_code == 400
