"""Core detected-issue endpoint coverage.

DetectedIssue is stored Medplum-style (like Patient, Encounter, Condition, Procedure,
DiagnosticReport, RiskAssessment, ClinicalImpression and the other content-based resources): the
request body (genuine FHIR R4 DetectedIssue JSON) is validated and stored whole in `content`,
every response is FHIR R4 (`application/fhir+json`, regardless of Accept), and only the FHIR R4
search parameters are indexed (https://www.hl7.org/fhir/R4/detectedissue.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence checks on every local reference (`patient`, `author`,
`implicated`, `evidence.detail`, `mitigation.author`, `identifier.assigner`). Search lives in
test_search.py.

R4 requires `status` (and `mitigation.action`), but only the `java_validator` backend enforces
cardinality minimums (the native structural check does not), so that is not asserted here. Note
that `status` and `severity` have no search parameter on this resource.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.detected_issue.conftest import ISSUE_PERMS
from tests.integration.detected_issue.support import (
    BASE,
    category,
    condition_body,
    create_condition,
    create_impression,
    create_issue,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_report,
    full_body,
    impression_body,
    issue_body,
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
    return {
        int(e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == "match"
    }


def _as_user(sub="u-test", org_id="org-test", permissions=ISSUE_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client, patient) -> tuple[int, dict]:
    practitioner = await create_practitioner(client)
    condition = await create_condition(client, condition_body(patient))
    report = await create_report(client, report_body(patient))
    organization = await create_organization(client)
    body = full_body(patient, practitioner, condition, report, organization)
    return await create_issue(client, body), body


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_minimal(client, patient):
    resp = await client.post(BASE + "/", json=issue_body(patient))
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "DetectedIssue" and data["status"] == "final"
    assert data["patient"] == {"reference": f"Patient/{patient}"}


async def test_create_without_a_patient(client):
    resp = await client.post(BASE + "/", json=issue_body())
    assert resp.status_code == 201, resp.text
    assert "patient" not in resp.json()


async def test_create_full_round_trip(client, patient):
    issue, body = await _full(client, patient)
    data = (await client.get(f"{BASE}/{issue}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_elements_nothing_searches_on(client, patient):
    """`status`, `severity`, `detail`, `reference`, `evidence` and `mitigation` live only in `content`."""
    issue, _ = await _full(client, patient)
    data = (await client.get(f"{BASE}/{issue}")).json()
    assert data["status"] == "final" and data["severity"] == "high"
    assert data["detail"].startswith("The patient is prescribed")
    assert data["reference"] == "http://example.org/protocols/duplicate-therapy"
    assert data["evidence"][0]["code"] == [{"text": "Two active statin prescriptions"}]
    assert data["mitigation"][0]["action"] == {"text": "Stopped the older prescription"}
    assert data["mitigation"][0]["date"] == "2023-01-16T08:00:00Z"


@pytest.mark.parametrize(
    "extra",
    [
        {"identifiedDateTime": "2023-01"},
        {"identifiedPeriod": {"start": "2023-01-01", "end": "2023-06-01"}},
    ],
    ids=["identifiedDateTime", "identifiedPeriod"],
)
async def test_create_each_identified_choice_round_trips(client, patient, extra):
    resp = await client.post(BASE + "/", json=issue_body(patient, **extra))
    assert resp.status_code == 201, resp.text
    for key, value in extra.items():
        assert resp.json()[key] == value


@pytest.mark.parametrize(
    "status",
    [
        "registered",
        "preliminary",
        "final",
        "amended",
        "corrected",
        "cancelled",
        "entered-in-error",
        "unknown",
    ],
)
async def test_create_every_status_round_trips(client, patient, status):
    resp = await client.post(BASE + "/", json=issue_body(patient, status))
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


@pytest.mark.parametrize("severity", ["high", "moderate", "low"])
async def test_create_every_severity_round_trips(client, patient, severity):
    resp = await client.post(BASE + "/", json=issue_body(patient, severity=severity))
    assert resp.status_code == 201, resp.text
    assert resp.json()["severity"] == severity


async def test_create_ignores_server_managed_id_and_meta(client, patient):
    body = issue_body(patient, id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"})
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client, patient):
    for bad in (
        {"status": "robot"},
        {"severity": "critical"},
        {"identifiedDateTime": "yesterday"},
        {"code": "x"},
        {"author": [{"reference": "Practitioner/1"}]},
        {"implicated": {"reference": "Condition/1"}},
        {"evidence": {"detail": []}},
        {"evidence": [{"code": "x"}]},
        {"mitigation": {"action": {"text": "x"}}},
        {"mitigation": [{"action": "x"}]},
        {"identifier": {"value": "x"}},
        {"detail": 5},
        {"reference": 5},
    ):
        resp = await client.post(BASE + "/", json=issue_body(patient, **bad))
        assert resp.status_code == 422, (bad, resp.text)
    assert (
        await client.post(BASE + "/", json={"status": "final", "patient": "Patient/1"})
    ).status_code == 422


async def test_create_non_fhir_key_rejected(client, patient, native_validation):
    assert (
        await client.post(BASE + "/", json=issue_body(patient, not_a_fhir_element=1))
    ).status_code == 422


async def test_create_old_flat_fields_rejected(client, patient, native_validation):
    for stale in (
        {"code_text": "x"},
        {"identified_date_time": "2020-01-01"},
        {"org_id": "x"},
    ):
        resp = await client.post(BASE + "/", json={**issue_body(patient), **stale})
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client, patient):
    assert (
        await client.post(BASE + "/", json=issue_body(patient, resourceType="Patient"))
    ).status_code == 422


async def test_create_audit_meta_from_actor(client, patient):
    data = (await client.post(BASE + "/", json=issue_body(patient))).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# ── Create: existence checks on local references ─────────────────────────────


async def test_create_patient_must_exist(client):
    assert (await client.post(BASE + "/", json=issue_body(999999))).status_code == 422


async def test_create_patient_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    assert (await client.post(BASE + "/", json=issue_body(theirs))).status_code == 422


async def test_create_author_is_checked_except_a_device(client, patient):
    practitioner = await create_practitioner(client)
    role = await create_practitioner_role(client)
    for ref in (
        f"Practitioner/{practitioner}",
        f"PractitionerRole/{role}",
        "Device/999999",
    ):
        resp = await client.post(
            BASE + "/", json=issue_body(patient, author={"reference": ref})
        )
        assert resp.status_code == 201, (
            ref,
            resp.text,
        )  # a Device is not a resource here: stored as sent
    for missing in ("Practitioner/999999", "PractitionerRole/999999"):
        resp = await client.post(
            BASE + "/", json=issue_body(patient, author={"reference": missing})
        )
        assert resp.status_code == 422, (missing, resp.text)


async def test_create_implicated_is_checked_for_resources_here(client, patient):
    condition = await create_condition(client, condition_body(patient))
    impression = await create_impression(client, impression_body(patient))
    ok = issue_body(
        patient,
        implicated=[
            {"reference": f"Condition/{condition}"},
            {"reference": f"ClinicalImpression/{impression}"},
            {"reference": f"Patient/{patient}"},
            {"reference": "MedicationRequest/999999"},
            {"reference": "Observation/999999"},
        ],
    )
    assert (
        await client.post(BASE + "/", json=ok)
    ).status_code == 201  # not rebuilt: stored as sent
    for missing in ("Condition/999999", "ClinicalImpression/999999", "Patient/999999"):
        resp = await client.post(
            BASE + "/", json=issue_body(patient, implicated=[{"reference": missing}])
        )
        assert resp.status_code == 422, (missing, resp.text)


async def test_create_evidence_detail_is_checked_for_resources_here(client, patient):
    report = await create_report(client, report_body(patient))
    ok = issue_body(
        patient,
        evidence=[
            {
                "detail": [
                    {"reference": f"DiagnosticReport/{report}"},
                    {"reference": "GuidanceResponse/9"},
                ]
            }
        ],
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = issue_body(
        patient, evidence=[{"detail": [{"reference": "DiagnosticReport/999999"}]}]
    )
    assert (await client.post(BASE + "/", json=bad)).status_code == 422


async def test_create_mitigation_author_is_checked(client, patient):
    practitioner = await create_practitioner(client)
    ok = issue_body(
        patient,
        mitigation=[
            {
                "action": {"text": "a"},
                "author": {"reference": f"Practitioner/{practitioner}"},
            }
        ],
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = issue_body(
        patient,
        mitigation=[
            {"action": {"text": "a"}, "author": {"reference": "Practitioner/999999"}}
        ],
    )
    assert (await client.post(BASE + "/", json=bad)).status_code == 422


async def test_create_identifier_assigner_must_exist(client, patient):
    body = issue_body(
        patient,
        identifier=[{"value": "1", "assigner": {"reference": "Organization/999999"}}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 422
    org = await create_organization(client)
    body = issue_body(
        patient,
        identifier=[{"value": "1", "assigner": {"reference": f"Organization/{org}"}}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_absolute_and_logical_references_not_resolved(client):
    absolute = "https://other.example.org/fhir/Patient/1"
    resp = await client.post(
        BASE + "/", json={"status": "final", "patient": {"reference": absolute}}
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["patient"] == {"reference": absolute}
    logical = {
        "identifier": {"system": "urn:pts", "value": "P-9"},
        "display": "External",
    }
    body = issue_body(
        None,
        patient=logical,
        author={"reference": "https://other.example.org/fhir/Practitioner/7"},
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["patient"] == logical
    assert resp.json()["author"] == {
        "reference": "https://other.example.org/fhir/Practitioner/7"
    }


# ── Read ─────────────────────────────────────────────────────────────────────


async def test_get_by_id(client, patient):
    issue, _ = await _full(client, patient)
    resp = await client.get(f"{BASE}/{issue}")
    assert resp.status_code == 200 and resp.json()["id"] == str(issue)


async def test_get_is_fhir_regardless_of_accept(client, patient):
    issue = await create_issue(client, issue_body(patient))
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{issue}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "DetectedIssue"


async def test_xml_only_accept_is_406(client, patient):
    issue = await create_issue(client, issue_body(patient))
    resp = await client.get(
        f"{BASE}/{issue}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_scalar_keeps_the_rest(client, patient):
    issue, _ = await _full(client, patient)
    resp = await client.patch(
        f"{BASE}/{issue}", json={"status": "amended", "severity": "low"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "amended" and resp.json()["severity"] == "low"
    assert resp.json()["patient"] == {"reference": f"Patient/{patient}"}  # untouched
    assert len(resp.json()["mitigation"]) == 1


async def test_patch_reindexes_search(client, patient):
    issue, _ = await _full(client, patient)
    await client.patch(
        f"{BASE}/{issue}",
        json={
            "identifiedDateTime": "2024-05-01",
            "code": category("DRG", "Drug interaction"),
        },
    )
    for param, old, new in (
        ("identified", "2023-01-15", "2024-05-01"),
        ("code", "DUPTHPY", "DRG"),
    ):
        assert issue not in _ids(
            (await client.get(BASE + "/", params={param: old})).json()
        ), param
        assert issue in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param


async def test_patch_patient_replaced_and_reindexed(client, patient):
    issue = await create_issue(client, issue_body(patient))
    other = await create_patient(client)
    resp = await client.patch(
        f"{BASE}/{issue}", json={"patient": {"reference": f"Patient/{other}"}}
    )
    assert resp.status_code == 200, resp.text
    assert issue not in _ids(
        (await client.get(BASE + "/", params={"patient": str(patient)})).json()
    )
    assert issue in _ids(
        (await client.get(BASE + "/", params={"patient": str(other)})).json()
    )


async def test_patch_replaces_lists_and_empty_clears(client, patient):
    issue, _ = await _full(client, patient)
    assert issue in _ids(
        (await client.get(BASE + "/", params={"identifier": "DI-1001"})).json()
    )
    resp = await client.patch(
        f"{BASE}/{issue}",
        json={"identifier": [], "implicated": [], "evidence": [], "mitigation": []},
    )
    for gone in ("identifier", "implicated", "evidence", "mitigation"):
        assert gone not in resp.json()
    assert resp.json()["severity"] == "high"  # untouched
    assert issue not in _ids(
        (await client.get(BASE + "/", params={"identifier": "DI-1001"})).json()
    )
    assert issue in _ids(
        (await client.get(BASE + "/", params={"implicated:missing": "true"})).json()
    )


async def test_patch_clears_identified_and_missing_follows(client, patient):
    issue = await create_issue(
        client, issue_body(patient, identifiedDateTime="2024-05-01")
    )
    resp = await client.patch(f"{BASE}/{issue}", json={"identifiedDateTime": None})
    assert "identifiedDateTime" not in resp.json()
    assert issue in _ids(
        (await client.get(BASE + "/", params={"identified:missing": "true"})).json()
    )


async def test_patch_nonexistent_reference_rejected_and_nothing_written(
    client, patient
):
    issue = await create_issue(client, issue_body(patient))
    resp = await client.patch(
        f"{BASE}/{issue}", json={"implicated": [{"reference": "Condition/999999"}]}
    )
    assert resp.status_code == 422
    assert "implicated" not in (await client.get(f"{BASE}/{issue}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client, patient):
    issue = await create_issue(client, issue_body(patient, "final"))
    assert (
        await client.patch(f"{BASE}/{issue}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{issue}")).json()["status"] == "final"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "amended"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete(client, patient):
    issue, _ = await _full(client, patient)
    assert (await client.delete(f"{BASE}/{issue}")).status_code == 204
    assert (await client.get(f"{BASE}/{issue}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (("identifier", "DI-1001"), ("code", "DUPTHPY")):
        assert issue not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_create_without_permission(client, patient):
    _as_user(permissions=["detected_issue:read"])
    assert (await client.post(BASE + "/", json=issue_body(patient))).status_code == 403


async def test_org_less_token_rejected(client, patient):
    issue = await create_issue(client, issue_body(patient))

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": ISSUE_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=issue_body())).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{issue}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    issue = await create_issue(client, issue_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{issue}"),
            await other_client.patch(f"{BASE}/{issue}", json={"status": "amended"}),
            await other_client.delete(f"{BASE}/{issue}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_issue(
        client, issue_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}])
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()
