"""Core measure-report endpoint coverage.

MeasureReport is stored content-based (like QuestionnaireResponse and the other rebuilt
resources): the request body (genuine FHIR R4 MeasureReport JSON) is validated and stored whole in
`content`, every response is FHIR R4 (`application/fhir+json`, regardless of Accept), and only the
FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/measurereport.html#search) - the group tree (population counts,
scores, stratifier / stratum / component results), `type` and `improvementNotation` are plain
content.

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence checks on `subject`, `reporter`, `evaluatedResource`,
`identifier.assigner` and on a relative `MeasureReport/<id>` in a Reference element. Search lives
in test_search.py.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.measure_report.conftest import MEASURE_REPORT_PERMS
from tests.integration.measure_report.support import (
    BASE,
    MEASURE_URL,
    create_group,
    create_measure_report,
    create_organization,
    create_patient,
    create_practitioner,
    full_body,
    group_body,
    measure_report_body,
)

ISSUES = "/api/fhir/v1/detected-issues/"


@pytest.fixture
def native_validation(monkeypatch):
    """The base R4 validator may be switched off in configs/config.yaml; tests that assert "a key
    that isn't FHIR is a 422" need it on: the project's own structural check."""
    monkeypatch.setattr(settings.fhir_validation, "enabled", True)
    monkeypatch.setattr(settings.fhir_validation, "backend", "native")


def _ids(bundle: dict) -> set[int]:
    return {
        int(e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == "match"
    }


def _as_user(sub="u-test", org_id="org-test", permissions=MEASURE_REPORT_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client) -> tuple[int, dict]:
    patient = await create_patient(client)
    organization = await create_organization(client)
    body = full_body(patient, organization)
    return await create_measure_report(client, body), body


async def _created(client, **extra) -> int:
    return (
        await client.post(BASE + "/", json=measure_report_body(**extra))
    ).status_code


# -- Create ---------------------------------------------------------------------------------


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=measure_report_body())
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "MeasureReport" and data["status"] == "complete"
    assert data["id"] == "570000"  # the first id of the block


async def test_create_full_round_trip(client):
    report, body = await _full(client)
    data = (await client.get(f"{BASE}/{report}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_the_group_tree(client):
    report, _ = await _full(client)
    group = (await client.get(f"{BASE}/{report}")).json()["group"]
    assert group[0]["population"][0]["count"] == 120
    assert group[0]["population"][0]["subjectResults"] == {"reference": "List/1"}
    assert group[0]["measureScore"] == {"value": 0.15, "unit": "1"}
    stratifier = group[0]["stratifier"][0]
    assert stratifier["code"] == [{"text": "age"}, {"text": "sex"}]
    assert stratifier["stratum"][1]["component"][1]["value"] == {"text": "A"}
    assert group[1] == {"code": {"text": "second"}}


@pytest.mark.parametrize("status", ["complete", "pending", "error"])
async def test_create_every_status_round_trips(client, status):
    resp = await client.post(BASE + "/", json=measure_report_body(status=status))
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


@pytest.mark.parametrize(
    "report_type", ["individual", "subject-list", "summary", "data-collection"]
)
async def test_create_every_type_round_trips(client, report_type):
    resp = await client.post(BASE + "/", json=measure_report_body(type=report_type))
    assert resp.status_code == 201, resp.text
    assert resp.json()["type"] == report_type


async def test_create_ignores_server_managed_id_and_meta(client):
    body = measure_report_body(id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"})
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_missing_required_elements_rejected(client, native_validation):
    for missing in ("measure", "period"):
        body = measure_report_body()
        del body[missing]
        resp = await client.post(BASE + "/", json=body)
        assert resp.status_code == 422, missing


async def test_create_bad_datatypes_rejected(client):
    for bad in (
        {"status": "robot"},
        {"type": "banana"},
        {"identifier": {"value": "x"}},
        {"measure": 5},
        {"subject": "Patient/1"},
        {"reporter": "Organization/1"},
        {"date": "yesterday"},
        {"period": "2026"},
        {"improvementNotation": "increase"},
        {"group": {"code": {"text": "x"}}},
        {"group": [{"population": {"count": 1}}]},
        {"group": [{"population": [{"count": "many"}]}]},
        {"evaluatedResource": {"reference": "Patient/1"}},
        {"evaluatedResource": "Patient/1"},
    ):
        resp = await client.post(BASE + "/", json={**measure_report_body(), **bad})
        assert resp.status_code == 422, (bad, resp.text)


async def test_create_non_fhir_key_rejected(client, native_validation):
    resp = await client.post(BASE + "/", json=measure_report_body(not_a_fhir_element=1))
    assert resp.status_code == 422


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in (
        {"improvement_notation_text": "x"},
        {"subject_id": 5},
        {"org_id": "x"},
    ):
        resp = await client.post(BASE + "/", json=measure_report_body(**stale))
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(
        BASE + "/", json=measure_report_body(resourceType="Patient")
    )
    assert resp.status_code == 422


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=measure_report_body())).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# -- Create: existence checks on local references --------------------------------------------


async def test_create_subject_and_reporter_must_exist(client):
    patient = await create_patient(client)
    group = await create_group(client, group_body())
    practitioner = await create_practitioner(client)
    organization = await create_organization(client)
    assert await _created(client, subject={"reference": f"Patient/{patient}"}) == 201
    assert await _created(client, subject={"reference": f"Group/{group}"}) == 201
    assert await _created(client, subject={"reference": "Patient/999999"}) == 422
    assert await _created(client, subject={"reference": "Group/999999"}) == 422
    assert (
        await _created(client, reporter={"reference": f"Organization/{organization}"})
        == 201
    )
    assert (
        await _created(client, reporter={"reference": f"Practitioner/{practitioner}"})
        == 201
    )
    assert await _created(client, reporter={"reference": "Organization/999999"}) == 422


async def test_create_evaluated_resource_must_exist(client):
    patient = await create_patient(client)
    ok = [{"reference": f"Patient/{patient}"}, {"reference": "Device/9"}]
    assert await _created(client, evaluatedResource=ok) == 201
    resp = await client.post(
        BASE + "/",
        json=measure_report_body(evaluatedResource=[{"reference": "Patient/999999"}]),
    )
    assert resp.status_code == 422 and "evaluatedResource[0]" in resp.text


async def test_create_identifier_assigner_must_exist(client):
    organization = await create_organization(client)
    ok = measure_report_body(
        identifier=[
            {"value": "1", "assigner": {"reference": f"Organization/{organization}"}}
        ]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = measure_report_body(
        identifier=[{"value": "1", "assigner": {"reference": "Organization/999999"}}]
    )
    resp = await client.post(BASE + "/", json=bad)
    assert resp.status_code == 422 and "assigner" in resp.text


async def test_measure_canonical_is_never_existence_checked(client):
    """`measure` is a canonical URL, not a Reference object: even a relative `Measure/<id>` that
    does not exist is stored as sent."""
    for measure in (MEASURE_URL, f"{MEASURE_URL}|9.9", "Measure/999999"):
        resp = await client.post(BASE + "/", json=measure_report_body(measure=measure))
        assert resp.status_code == 201, (measure, resp.text)
        assert resp.json()["measure"] == measure


async def test_unmodeled_targets_are_stored_as_sent(client):
    resp = await client.post(
        BASE + "/",
        json=measure_report_body(
            subject={"reference": "Device/999999"},
            group=[{"population": [{"subjectResults": {"reference": "List/999999"}}]}],
        ),
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == {"reference": "Device/999999"}


async def test_absolute_and_logical_references_not_resolved(client):
    absolute = "https://other.example.org/fhir/Patient/7"
    resp = await client.post(
        BASE + "/", json=measure_report_body(subject={"reference": absolute})
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == {"reference": absolute}
    logical = {"identifier": {"system": "urn:mrn", "value": "M-9"}, "display": "Jane"}
    resp = await client.post(BASE + "/", json=measure_report_body(reporter=logical))
    assert resp.status_code == 201, resp.text
    assert resp.json()["reporter"] == logical


async def test_subject_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    assert await _created(client, subject={"reference": f"Patient/{theirs}"}) == 422


async def test_a_relative_measure_report_reference_is_checked(client):
    """MeasureReport is a rebuilt resource: a relative `MeasureReport/<id>` in a Reference
    (DetectedIssue.implicated is Reference(Any)) must exist."""
    report = await create_measure_report(client, measure_report_body())
    ok = {"status": "final", "implicated": [{"reference": f"MeasureReport/{report}"}]}
    assert (await client.post(ISSUES, json=ok)).status_code == 201
    bad = {"status": "final", "implicated": [{"reference": "MeasureReport/999999"}]}
    resp = await client.post(ISSUES, json=bad)
    assert resp.status_code == 422 and "implicated" in resp.text


# -- Read -----------------------------------------------------------------------------------


async def test_get_by_id(client):
    report, _ = await _full(client)
    resp = await client.get(f"{BASE}/{report}")
    assert resp.status_code == 200 and resp.json()["id"] == str(report)


async def test_get_is_fhir_regardless_of_accept(client):
    report = await create_measure_report(client, measure_report_body())
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{report}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "MeasureReport"


async def test_xml_only_accept_is_406(client):
    report = await create_measure_report(client, measure_report_body())
    resp = await client.get(
        f"{BASE}/{report}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Patch ----------------------------------------------------------------------------------


async def test_patch_scalar_keeps_the_rest(client):
    report, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{report}", json={"status": "pending", "type": "summary"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "pending" and resp.json()["type"] == "summary"
    assert resp.json()["group"][0]["population"][0]["count"] == 120  # untouched
    assert resp.json()["subject"]["reference"].startswith("Patient/")  # untouched


async def test_patch_reindexes_search(client):
    report, _ = await _full(client)
    patched = await client.patch(
        f"{BASE}/{report}",
        json={
            "status": "pending",
            "date": "2027-03-03",
            "period": {"start": "2027-01-01", "end": "2027-01-31"},
            "measure": "https://fhir-server.dev/fhir/Measure/other",
            "identifier": [{"system": "urn:mr", "value": "MR-2"}],
        },
    )
    assert patched.status_code == 200, patched.text
    for param, old, new in (
        ("status", "complete", "pending"),
        ("date", "2026-02-01", "2027-03-03"),
        ("period", "le2026-02-01", "ge2027-01-10"),
        (
            "measure",
            f"https://fhir-server.dev/fhir/Measure/readmission",
            "https://fhir-server.dev/fhir/Measure/other",
        ),
        ("identifier", "MR-1001", "MR-2"),
    ):
        assert report not in _ids(
            (await client.get(BASE + "/", params={param: old})).json()
        ), param
        assert report in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param


async def test_patch_replaces_lists_and_empty_clears(client):
    report, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{report}",
        json={"identifier": [], "evaluatedResource": [], "group": []},
    )
    for gone in ("identifier", "evaluatedResource", "group"):
        assert gone not in resp.json()
    assert resp.json()["status"] == "complete"  # untouched
    for param in ("identifier", "evaluated-resource"):
        assert report in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_clears_subject_reporter_and_date(client):
    report, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{report}", json={"subject": None, "reporter": None, "date": None}
    )
    assert all(k not in resp.json() for k in ("subject", "reporter", "date"))
    for param in ("subject", "patient", "reporter", "date"):
        assert report in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client):
    report = await create_measure_report(client, measure_report_body())
    resp = await client.patch(
        f"{BASE}/{report}", json={"reporter": {"reference": "Organization/999999"}}
    )
    assert resp.status_code == 422
    assert "reporter" not in (await client.get(f"{BASE}/{report}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    report = await create_measure_report(client, measure_report_body())
    assert (
        await client.patch(f"{BASE}/{report}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{report}")).json()["status"] == "complete"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "complete"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Delete ---------------------------------------------------------------------------------


async def test_delete(client):
    report, _ = await _full(client)
    assert (await client.delete(f"{BASE}/{report}")).status_code == 204
    assert (await client.get(f"{BASE}/{report}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "MR-1001"),
        ("measure", MEASURE_URL),
        ("evaluated-resource", "Device/9"),
    ):
        assert report not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Auth -----------------------------------------------------------------------------------


async def test_create_without_permission(client):
    _as_user(permissions=["measure_report:read"])
    assert (
        await client.post(BASE + "/", json=measure_report_body())
    ).status_code == 403


async def test_org_less_token_rejected(client):
    report = await create_measure_report(client, measure_report_body())

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": MEASURE_REPORT_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (
        await client.post(BASE + "/", json=measure_report_body())
    ).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{report}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    report = await create_measure_report(client, measure_report_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{report}"),
            await other_client.patch(f"{BASE}/{report}", json={"status": "pending"}),
            await other_client.delete(f"{BASE}/{report}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_measure_report(
        client,
        measure_report_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}]),
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()
