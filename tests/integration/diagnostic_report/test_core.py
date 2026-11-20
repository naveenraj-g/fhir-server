"""Core diagnostic-report endpoint coverage.

DiagnosticReport is stored Medplum-style (like Patient, Appointment, Encounter,
Condition, Procedure and the other content-based resources): the request body
(genuine FHIR R4 DiagnosticReport JSON) is validated and stored whole in
`content`, every response is FHIR R4 (`application/fhir+json`, regardless of
Accept), and only the FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/diagnosticreport.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing
scope, cross-org isolation) plus the existence checks on every local reference
(`subject`, `encounter`, `performer`, `resultsInterpreter`, `identifier.assigner`)
and the fact that a DiagnosticReport is now a real target for the references that
name one (Procedure `reasonReference` / `report`, Condition `stage.assessment`).
Search lives in test_search.py.

R4 requires `status` and `code`, but only the `java_validator` backend enforces
cardinality minimums (the native structural check does not), so that is not
asserted here.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.diagnostic_report.conftest import REPORT_PERMS
from tests.integration.diagnostic_report.support import (
    API,
    BASE,
    create_encounter,
    create_location,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_report,
    encounter_body,
    full_body,
    report_body,
)


@pytest.fixture
def native_validation(monkeypatch):
    """The base R4 validator may be switched off in configs/config.yaml
    (`fhir_validation.enabled: false` skips it entirely). Tests that assert "a
    key that isn't FHIR is a 422" need it on: the project's own structural
    check (no sidecar needed)."""
    monkeypatch.setattr(settings.fhir_validation, "enabled", True)
    monkeypatch.setattr(settings.fhir_validation, "backend", "native")


@pytest.fixture
async def patient(client) -> int:
    return await create_patient(client)


def _ids(bundle: dict) -> set[int]:
    return {int(e["resource"]["id"]) for e in bundle.get("entry") or [] if e["search"]["mode"] == "match"}


def _as_user(sub="u-test", org_id="org-test", permissions=REPORT_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(sub=sub, org_id=org_id, permissions=permissions)


async def _full(client, patient) -> tuple[int, dict]:
    encounter = await create_encounter(client, encounter_body())
    practitioner = await create_practitioner(client)
    organization = await create_organization(client)
    body = full_body(patient, encounter, practitioner, organization)
    return await create_report(client, body), body


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_minimal(client, patient):
    resp = await client.post(BASE + "/", json=report_body(patient))
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "DiagnosticReport" and data["status"] == "final"
    assert data["subject"] == {"reference": f"Patient/{patient}"}


async def test_create_full_round_trip(client, patient):
    report, body = await _full(client, patient)
    data = (await client.get(f"{BASE}/{report}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")} == expected


async def test_create_keeps_elements_nothing_searches_on(client, patient):
    """`imagingStudy`, `media.comment`, `conclusion` and `presentedForm` live only in `content`."""
    report, _ = await _full(client, patient)
    data = (await client.get(f"{BASE}/{report}")).json()
    assert data["imagingStudy"] == [{"reference": "ImagingStudy/5"}]
    assert data["media"] == [{"comment": "Slide 1", "link": {"reference": "Media/9"}}]
    assert data["conclusion"] == "Normal blood count."
    assert data["presentedForm"][0]["title"] == "Report"


@pytest.mark.parametrize(
    "effective",
    [{"effectiveDateTime": "2023-01"}, {"effectivePeriod": {"start": "2020-01-01", "end": "2020-02-01"}}],
    ids=["dateTime", "period"],
)
async def test_create_each_effective_choice_round_trips(client, patient, effective):
    resp = await client.post(BASE + "/", json=report_body(patient, **effective))
    assert resp.status_code == 201, resp.text
    for key, value in effective.items():
        assert resp.json()[key] == value


@pytest.mark.parametrize(
    "status",
    ["registered", "partial", "preliminary", "final", "amended", "corrected", "appended", "cancelled", "entered-in-error", "unknown"],
)
async def test_create_every_status_round_trips(client, patient, status):
    resp = await client.post(BASE + "/", json=report_body(patient, status))
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


async def test_create_ignores_server_managed_id_and_meta(client, patient):
    body = report_body(patient, id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"})
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client, patient):
    for bad in ({"status": "robot"}, {"code": "58410-2"}, {"performer": {"reference": "Practitioner/1"}},
                {"category": {"text": "x"}}):
        resp = await client.post(BASE + "/", json=report_body(patient, **bad))
        assert resp.status_code == 422, (bad, resp.text)
    assert (await client.post(BASE + "/", json={"status": "final", "subject": "Patient/1"})).status_code == 422


async def test_create_non_fhir_key_rejected(client, patient, native_validation):
    assert (await client.post(BASE + "/", json=report_body(patient, not_a_fhir_element=1))).status_code == 422


async def test_create_old_flat_fields_rejected(client, patient, native_validation):
    for stale in ({"code_text": "x"}, {"effective_date_time": "2020-01-01"}, {"org_id": "x"}):
        resp = await client.post(BASE + "/", json={**report_body(patient), **stale})
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client, patient):
    assert (await client.post(BASE + "/", json=report_body(patient, resourceType="Patient"))).status_code == 422


async def test_create_audit_meta_from_actor(client, patient):
    data = (await client.post(BASE + "/", json=report_body(patient))).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# ── Create: existence checks on local references ─────────────────────────────


async def test_create_subject_patient_must_exist(client):
    assert (await client.post(BASE + "/", json=report_body(999999))).status_code == 422


async def test_create_subject_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    assert (await client.post(BASE + "/", json=report_body(theirs))).status_code == 422


async def test_create_location_subject_is_checked_but_group_and_device_are_not(client):
    location = await create_location(client)
    ok = {"status": "final", "code": {"text": "x"}, "subject": {"reference": f"Location/{location}"}}
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = {"status": "final", "code": {"text": "x"}, "subject": {"reference": "Location/999999"}}
    assert (await client.post(BASE + "/", json=missing)).status_code == 422
    for stored_as_sent in ("Group/5", "Device/5"):
        body = {"status": "final", "code": {"text": "x"}, "subject": {"reference": stored_as_sent}}
        resp = await client.post(BASE + "/", json=body)
        assert resp.status_code == 201, (stored_as_sent, resp.text)
        assert resp.json()["subject"] == {"reference": stored_as_sent}


async def test_create_encounter_must_exist(client, patient):
    missing = report_body(patient, encounter={"reference": "Encounter/999999"})
    assert (await client.post(BASE + "/", json=missing)).status_code == 422
    encounter = await create_encounter(client, encounter_body())
    assert (
        await client.post(BASE + "/", json=report_body(patient, encounter={"reference": f"Encounter/{encounter}"}))
    ).status_code == 201


@pytest.mark.parametrize("element", ["performer", "resultsInterpreter"])
async def test_create_performer_and_interpreter_are_checked_except_a_care_team(client, patient, element):
    practitioner = await create_practitioner(client)
    role = await create_practitioner_role(client)
    organization = await create_organization(client)
    for ref in (f"Practitioner/{practitioner}", f"PractitionerRole/{role}", f"Organization/{organization}", "CareTeam/999999"):
        resp = await client.post(BASE + "/", json=report_body(patient, **{element: [{"reference": ref}]}))
        assert resp.status_code == 201, (ref, resp.text)  # a CareTeam is not a resource here: stored as sent
    for missing in ("Practitioner/999999", "PractitionerRole/999999", "Organization/999999"):
        resp = await client.post(BASE + "/", json=report_body(patient, **{element: [{"reference": missing}]}))
        assert resp.status_code == 422, (missing, resp.text)


async def test_create_identifier_assigner_must_exist(client, patient):
    body = report_body(patient, identifier=[{"value": "1", "assigner": {"reference": "Organization/999999"}}])
    assert (await client.post(BASE + "/", json=body)).status_code == 422
    org = await create_organization(client)
    body = report_body(patient, identifier=[{"value": "1", "assigner": {"reference": f"Organization/{org}"}}])
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_unrebuilt_targets_are_not_checked(client, patient):
    """basedOn, specimen, result, imagingStudy and media.link point at resources this server does
    not rebuild: stored as sent."""
    body = report_body(
        patient,
        basedOn=[{"reference": "ServiceRequest/999999"}],
        specimen=[{"reference": "Specimen/999999"}],
        result=[{"reference": "Observation/999999"}],
        imagingStudy=[{"reference": "ImagingStudy/999999"}],
        media=[{"link": {"reference": "Media/999999"}}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_absolute_and_logical_references_not_resolved(client):
    absolute = "https://other.example.org/fhir/Patient/1"
    resp = await client.post(BASE + "/", json={"status": "final", "code": {"text": "x"}, "subject": {"reference": absolute}})
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == {"reference": absolute}
    logical = {"identifier": {"system": "urn:pts", "value": "P-9"}, "display": "External"}
    body = {"status": "final", "code": {"text": "x"}, "subject": logical,
            "performer": [{"reference": "https://other.example.org/fhir/Practitioner/7"}]}
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == logical
    assert resp.json()["performer"] == [{"reference": "https://other.example.org/fhir/Practitioner/7"}]


# ── A DiagnosticReport is now a real target of the references that name one ──


async def test_references_to_a_diagnostic_report_are_checked_and_resolve(client, patient):
    report = await create_report(client, report_body(patient))
    ref = f"DiagnosticReport/{report}"
    proc = {"status": "completed", "subject": {"reference": f"Patient/{patient}"},
            "report": [{"reference": ref}], "reasonReference": [{"reference": ref}]}
    resp = await client.post(f"{API}/procedures/", json=proc)
    assert resp.status_code == 201, resp.text
    cond = {"subject": {"reference": f"Patient/{patient}"}, "stage": [{"assessment": [{"reference": ref}]}]}
    resp = await client.post(f"{API}/conditions/", json=cond)
    assert resp.status_code == 201, resp.text


async def test_references_to_a_missing_diagnostic_report_are_rejected(client, patient):
    ref = "DiagnosticReport/999999"
    subject = {"reference": f"Patient/{patient}"}
    for proc in (
        {"status": "completed", "subject": subject, "report": [{"reference": ref}]},
        {"status": "completed", "subject": subject, "reasonReference": [{"reference": ref}]},
    ):
        assert (await client.post(f"{API}/procedures/", json=proc)).status_code == 422
    cond = {"subject": subject, "stage": [{"assessment": [{"reference": ref}]}]}
    assert (await client.post(f"{API}/conditions/", json=cond)).status_code == 422


# ── Read ─────────────────────────────────────────────────────────────────────


async def test_get_by_id(client, patient):
    report, _ = await _full(client, patient)
    resp = await client.get(f"{BASE}/{report}")
    assert resp.status_code == 200 and resp.json()["id"] == str(report)


async def test_get_is_fhir_regardless_of_accept(client, patient):
    report = await create_report(client, report_body(patient))
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{report}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "DiagnosticReport"


async def test_xml_only_accept_is_406(client, patient):
    report = await create_report(client, report_body(patient))
    resp = await client.get(f"{BASE}/{report}", headers={"Accept": "application/fhir+xml"})
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_scalar_keeps_the_rest(client, patient):
    report, _ = await _full(client, patient)
    resp = await client.patch(f"{BASE}/{report}", json={"status": "amended", "conclusion": "Corrected."})
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "amended" and resp.json()["conclusion"] == "Corrected."
    assert resp.json()["subject"] == {"reference": f"Patient/{patient}"}  # untouched
    assert resp.json()["presentedForm"][0]["title"] == "Report"
    assert resp.json()["media"][0]["comment"] == "Slide 1"


async def test_patch_reindexes_search(client, patient):
    report, _ = await _full(client, patient)
    await client.patch(
        f"{BASE}/{report}",
        json={"status": "amended", "code": {"coding": [{"system": "http://loinc.org", "code": "24323-8"}]},
              "effectivePeriod": None, "effectiveDateTime": "2024-05-01", "issued": "2024-05-02T10:00:00Z"},
    )
    for param, old, new in (
        ("status", "final", "amended"),
        ("code", "58410-2", "24323-8"),
        ("date", "2023-01-15", "2024-05-01"),
        ("issued", "2023-01-15", "2024-05-02"),
    ):
        assert report not in _ids((await client.get(BASE + "/", params={param: old})).json()), param
        assert report in _ids((await client.get(BASE + "/", params={param: new})).json()), param


async def test_patch_subject_replaced_and_reindexed(client, patient):
    report = await create_report(client, report_body(patient))
    other = await create_patient(client)
    resp = await client.patch(f"{BASE}/{report}", json={"subject": {"reference": f"Patient/{other}"}})
    assert resp.status_code == 200, resp.text
    assert report not in _ids((await client.get(BASE + "/", params={"patient": str(patient)})).json())
    assert report in _ids((await client.get(BASE + "/", params={"patient": str(other)})).json())


async def test_patch_replaces_lists_and_empty_clears(client, patient):
    report, _ = await _full(client, patient)
    assert report in _ids((await client.get(BASE + "/", params={"conclusion": "17621005"})).json())
    resp = await client.patch(
        f"{BASE}/{report}",
        json={"performer": [], "resultsInterpreter": [], "category": [], "conclusionCode": [], "identifier": [],
              "result": [], "specimen": [], "media": [], "basedOn": []},
    )
    for gone in ("performer", "resultsInterpreter", "category", "conclusionCode", "identifier", "result", "specimen",
                 "media", "basedOn"):
        assert gone not in resp.json()
    assert resp.json()["conclusion"] == "Normal blood count."  # untouched
    for param, value in (
        ("conclusion", "17621005"), ("category", "LAB"), ("identifier", "DR-1001"), ("result", "Observation/160001"),
        ("specimen", "310001"), ("media", "9"), ("based-on", "ServiceRequest/80001"),
    ):
        assert report not in _ids((await client.get(BASE + "/", params={param: value})).json()), param
    for param in ("performer", "results-interpreter"):
        assert report in _ids((await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()), param


async def test_patch_clears_a_date_and_missing_follows(client, patient):
    report = await create_report(client, report_body(patient, effectiveDateTime="2024-05-01", issued="2024-05-02T00:00:00Z"))
    resp = await client.patch(f"{BASE}/{report}", json={"effectiveDateTime": None, "issued": None})
    assert "effectiveDateTime" not in resp.json() and "issued" not in resp.json()
    for param in ("date", "issued"):
        assert report in _ids((await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()), param


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client, patient):
    report = await create_report(client, report_body(patient))
    resp = await client.patch(f"{BASE}/{report}", json={"performer": [{"reference": "Practitioner/999999"}]})
    assert resp.status_code == 422
    assert "performer" not in (await client.get(f"{BASE}/{report}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client, patient):
    report = await create_report(client, report_body(patient, "final"))
    assert (await client.patch(f"{BASE}/{report}", json={"status": "broken"})).status_code == 422
    assert (await client.get(f"{BASE}/{report}")).json()["status"] == "final"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "amended"})
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete(client, patient):
    report, _ = await _full(client, patient)
    assert (await client.delete(f"{BASE}/{report}")).status_code == 204
    assert (await client.get(f"{BASE}/{report}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (("identifier", "DR-1001"), ("code", "58410-2"), ("category", "LAB"), ("conclusion", "17621005")):
        assert report not in _ids((await client.get(BASE + "/", params={param: value})).json()), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_create_without_permission(client, patient):
    _as_user(permissions=["diagnostic_report:read"])
    assert (await client.post(BASE + "/", json=report_body(patient))).status_code == 403


async def test_org_less_token_rejected(client, patient):
    report = await create_report(client, report_body(patient))

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": REPORT_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=report_body())).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{report}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    report = await create_report(client, report_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{report}"),
            await other_client.patch(f"{BASE}/{report}", json={"status": "amended"}),
            await other_client.delete(f"{BASE}/{report}"),
        ):
            assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_report(client, report_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}]))
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})).json()
        assert bundle["total"] == 0
    finally:
        _as_user()
