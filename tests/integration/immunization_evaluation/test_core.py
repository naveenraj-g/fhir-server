"""Core immunization-evaluation endpoint coverage.

ImmunizationEvaluation is stored Medplum-style (like Patient, Appointment, Encounter,
Condition, Procedure, DiagnosticReport, Immunization and the other content-based
resources): the request body (genuine FHIR R4 ImmunizationEvaluation JSON) is validated and
stored whole in `content`, every response is FHIR R4 (`application/fhir+json`, regardless
of Accept), and only the FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/immunizationevaluation.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing scope,
cross-org isolation) plus the existence checks on every local reference (`patient`,
`immunizationEvent`, `authority`, `identifier.assigner`). Search lives in test_search.py.

R4 requires `status`, `patient`, `targetDisease`, `immunizationEvent` and `doseStatus`, but
only the `java_validator` backend enforces cardinality minimums (the native structural
check does not), so that is not asserted here.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.immunization_evaluation.conftest import EVALUATION_PERMS
from tests.integration.immunization_evaluation.support import (
    BASE,
    create_evaluation,
    create_immunization,
    create_organization,
    create_patient,
    dose_status,
    evaluation_body,
    full_body,
    immunization_body,
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


@pytest.fixture
async def immunization(client, patient) -> int:
    return await create_immunization(client, immunization_body(patient))


def _ids(bundle: dict) -> set[int]:
    return {
        int(e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == "match"
    }


def _as_user(sub="u-test", org_id="org-test", permissions=EVALUATION_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client, patient, immunization) -> tuple[int, dict]:
    organization = await create_organization(client)
    body = full_body(patient, immunization, organization)
    return await create_evaluation(client, body), body


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_minimal(client, patient, immunization):
    resp = await client.post(BASE + "/", json=evaluation_body(patient, immunization))
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert (
        data["resourceType"] == "ImmunizationEvaluation"
        and data["status"] == "completed"
    )
    assert data["patient"] == {"reference": f"Patient/{patient}"}
    assert data["immunizationEvent"] == {"reference": f"Immunization/{immunization}"}


async def test_create_full_round_trip(client, patient, immunization):
    evaluation, body = await _full(client, patient, immunization)
    data = (await client.get(f"{BASE}/{evaluation}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_elements_nothing_searches_on(client, patient, immunization):
    """`authority`, `doseStatusReason`, `description`, `series` and the dose numbers live only in `content`."""
    evaluation, _ = await _full(client, patient, immunization)
    data = (await client.get(f"{BASE}/{evaluation}")).json()
    assert data["authority"]["reference"].startswith("Organization/")
    assert data["doseStatusReason"][0]["coding"][0]["code"] == "agedoses" and data[
        "doseStatusReason"
    ][1] == {"text": "Other"}
    assert (
        data["description"] == "Evaluated against the seasonal flu schedule"
        and data["series"] == "Seasonal"
    )
    assert data["doseNumberPositiveInt"] == 1 and data["seriesDosesPositiveInt"] == 1


async def test_create_dose_number_string_choices_round_trip(
    client, patient, immunization
):
    body = evaluation_body(
        patient, immunization, doseNumberString="booster", seriesDosesString="many"
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert (
        resp.json()["doseNumberString"] == "booster"
        and resp.json()["seriesDosesString"] == "many"
    )


@pytest.mark.parametrize("status", ["completed", "entered-in-error"])
async def test_create_every_status_round_trips(client, patient, immunization, status):
    resp = await client.post(
        BASE + "/", json=evaluation_body(patient, immunization, status)
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


async def test_create_partial_date_round_trips(client, patient, immunization):
    resp = await client.post(
        BASE + "/", json=evaluation_body(patient, immunization, date="2023-01")
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["date"] == "2023-01"


async def test_create_ignores_server_managed_id_and_meta(client, patient, immunization):
    body = evaluation_body(
        patient, immunization, id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"}
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client, patient, immunization):
    for bad in (
        {"status": "robot"},
        {"date": "yesterday"},
        {"targetDisease": "6142004"},
        {"doseStatus": "valid"},
        {"doseStatusReason": {"text": "x"}},
        {"identifier": {"value": "x"}},
        {"doseNumberPositiveInt": "one"},
        {"description": 5},
    ):
        resp = await client.post(
            BASE + "/", json=evaluation_body(patient, immunization, **bad)
        )
        assert resp.status_code == 422, (bad, resp.text)
    assert (
        await client.post(
            BASE + "/", json={"status": "completed", "patient": "Patient/1"}
        )
    ).status_code == 422


async def test_create_non_fhir_key_rejected(
    client, patient, immunization, native_validation
):
    body = evaluation_body(patient, immunization, not_a_fhir_element=1)
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_old_flat_fields_rejected(
    client, patient, immunization, native_validation
):
    for stale in (
        {"target_disease_text": "x"},
        {"dose_status_text": "valid"},
        {"org_id": "x"},
    ):
        resp = await client.post(
            BASE + "/", json={**evaluation_body(patient, immunization), **stale}
        )
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client, patient, immunization):
    body = evaluation_body(patient, immunization, resourceType="Patient")
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_audit_meta_from_actor(client, patient, immunization):
    data = (
        await client.post(BASE + "/", json=evaluation_body(patient, immunization))
    ).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# ── Create: existence checks on local references ─────────────────────────────


async def test_create_patient_must_exist(client, immunization):
    assert (
        await client.post(BASE + "/", json=evaluation_body(999999, immunization))
    ).status_code == 422


async def test_create_immunization_event_must_exist(client, patient):
    assert (
        await client.post(BASE + "/", json=evaluation_body(patient, 999999))
    ).status_code == 422


async def test_create_references_in_another_org_are_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
        their_immunization = await create_immunization(
            other_client, immunization_body(theirs)
        )
    finally:
        _as_user()
    mine = await create_patient(client)
    assert (
        await client.post(BASE + "/", json=evaluation_body(theirs))
    ).status_code == 422
    assert (
        await client.post(BASE + "/", json=evaluation_body(mine, their_immunization))
    ).status_code == 422


async def test_create_authority_must_exist(client, patient, immunization):
    missing = evaluation_body(
        patient, immunization, authority={"reference": "Organization/999999"}
    )
    assert (await client.post(BASE + "/", json=missing)).status_code == 422
    org = await create_organization(client)
    ok = evaluation_body(
        patient, immunization, authority={"reference": f"Organization/{org}"}
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201


async def test_create_identifier_assigner_must_exist(client, patient, immunization):
    body = evaluation_body(
        patient,
        immunization,
        identifier=[{"value": "1", "assigner": {"reference": "Organization/999999"}}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 422
    org = await create_organization(client)
    body = evaluation_body(
        patient,
        immunization,
        identifier=[{"value": "1", "assigner": {"reference": f"Organization/{org}"}}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_absolute_and_logical_references_not_resolved(client):
    resp = await client.post(BASE + "/", json=evaluation_body())
    assert resp.status_code == 201, resp.text
    assert resp.json()["patient"] == {
        "reference": "https://other.example.org/fhir/Patient/1"
    }
    assert resp.json()["immunizationEvent"] == {
        "reference": "https://other.example.org/fhir/Immunization/1"
    }
    logical = {
        "identifier": {"system": "urn:pts", "value": "P-9"},
        "display": "External",
    }
    body = evaluation_body(
        None,
        patient=logical,
        immunizationEvent={"identifier": {"system": "urn:imm", "value": "I-9"}},
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["patient"] == logical
    assert resp.json()["immunizationEvent"] == {
        "identifier": {"system": "urn:imm", "value": "I-9"}
    }


# ── Read ─────────────────────────────────────────────────────────────────────


async def test_get_by_id(client, patient, immunization):
    evaluation, _ = await _full(client, patient, immunization)
    resp = await client.get(f"{BASE}/{evaluation}")
    assert resp.status_code == 200 and resp.json()["id"] == str(evaluation)


async def test_get_is_fhir_regardless_of_accept(client, patient, immunization):
    evaluation = await create_evaluation(client, evaluation_body(patient, immunization))
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{evaluation}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "ImmunizationEvaluation"


async def test_xml_only_accept_is_406(client, patient, immunization):
    evaluation = await create_evaluation(client, evaluation_body(patient, immunization))
    resp = await client.get(
        f"{BASE}/{evaluation}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_scalar_keeps_the_rest(client, patient, immunization):
    evaluation, _ = await _full(client, patient, immunization)
    resp = await client.patch(
        f"{BASE}/{evaluation}", json={"status": "entered-in-error", "series": "Revised"}
    )
    assert resp.status_code == 200, resp.text
    assert (
        resp.json()["status"] == "entered-in-error"
        and resp.json()["series"] == "Revised"
    )
    assert resp.json()["patient"] == {"reference": f"Patient/{patient}"}  # untouched
    assert resp.json()["authority"]["reference"].startswith("Organization/")
    assert resp.json()["doseNumberPositiveInt"] == 1


async def test_patch_reindexes_search(client, patient, immunization):
    evaluation, _ = await _full(client, patient, immunization)
    await client.patch(
        f"{BASE}/{evaluation}",
        json={
            "status": "entered-in-error",
            "date": "2024-05-01",
            "doseStatus": dose_status("invalid"),
            "targetDisease": {
                "coding": [{"system": "http://snomed.info/sct", "code": "14189004"}]
            },
        },
    )
    for param, old, new in (
        ("status", "completed", "entered-in-error"),
        ("date", "2023-01-15", "2024-05-01"),
        ("dose-status", "valid", "invalid"),
        ("target-disease", "6142004", "14189004"),
    ):
        assert evaluation not in _ids(
            (await client.get(BASE + "/", params={param: old})).json()
        ), param
        assert evaluation in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param


async def test_patch_references_replaced_and_reindexed(client, patient, immunization):
    evaluation = await create_evaluation(client, evaluation_body(patient, immunization))
    other = await create_patient(client)
    other_immunization = await create_immunization(client, immunization_body(other))
    resp = await client.patch(
        f"{BASE}/{evaluation}",
        json={
            "patient": {"reference": f"Patient/{other}"},
            "immunizationEvent": {"reference": f"Immunization/{other_immunization}"},
        },
    )
    assert resp.status_code == 200, resp.text
    assert evaluation not in _ids(
        (await client.get(BASE + "/", params={"patient": str(patient)})).json()
    )
    assert evaluation in _ids(
        (await client.get(BASE + "/", params={"patient": str(other)})).json()
    )
    assert evaluation in _ids(
        (
            await client.get(
                BASE + "/", params={"immunization-event": str(other_immunization)}
            )
        ).json()
    )


async def test_patch_replaces_lists_and_empty_clears(client, patient, immunization):
    evaluation, _ = await _full(client, patient, immunization)
    assert evaluation in _ids(
        (await client.get(BASE + "/", params={"identifier": "IE-1001"})).json()
    )
    resp = await client.patch(
        f"{BASE}/{evaluation}", json={"identifier": [], "doseStatusReason": []}
    )
    assert "identifier" not in resp.json() and "doseStatusReason" not in resp.json()
    assert resp.json()["authority"]["reference"].startswith(
        "Organization/"
    )  # untouched
    assert evaluation not in _ids(
        (await client.get(BASE + "/", params={"identifier": "IE-1001"})).json()
    )
    assert evaluation in _ids(
        (await client.get(BASE + "/", params={"identifier:missing": "true"})).json()
    )


async def test_patch_clears_a_date_and_missing_follows(client, patient, immunization):
    evaluation = await create_evaluation(
        client, evaluation_body(patient, immunization, date="2024-05-01")
    )
    resp = await client.patch(f"{BASE}/{evaluation}", json={"date": None})
    assert "date" not in resp.json()
    assert evaluation in _ids(
        (await client.get(BASE + "/", params={"date:missing": "true"})).json()
    )


async def test_patch_nonexistent_reference_rejected_and_nothing_written(
    client, patient, immunization
):
    evaluation = await create_evaluation(client, evaluation_body(patient, immunization))
    resp = await client.patch(
        f"{BASE}/{evaluation}",
        json={"immunizationEvent": {"reference": "Immunization/999999"}},
    )
    assert resp.status_code == 422
    event = (await client.get(f"{BASE}/{evaluation}")).json()["immunizationEvent"]
    assert event == {"reference": f"Immunization/{immunization}"}


async def test_patch_invalid_value_rejected_and_nothing_written(
    client, patient, immunization
):
    evaluation = await create_evaluation(
        client, evaluation_body(patient, immunization, "completed")
    )
    assert (
        await client.patch(f"{BASE}/{evaluation}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{evaluation}")).json()["status"] == "completed"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "entered-in-error"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete(client, patient, immunization):
    evaluation, _ = await _full(client, patient, immunization)
    assert (await client.delete(f"{BASE}/{evaluation}")).status_code == 204
    assert (await client.get(f"{BASE}/{evaluation}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "IE-1001"),
        ("dose-status", "valid"),
        ("target-disease", "6142004"),
    ):
        assert evaluation not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_create_without_permission(client, patient, immunization):
    _as_user(permissions=["immunization_evaluation:read"])
    assert (
        await client.post(BASE + "/", json=evaluation_body(patient, immunization))
    ).status_code == 403


async def test_org_less_token_rejected(client, patient, immunization):
    evaluation = await create_evaluation(client, evaluation_body(patient, immunization))

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": EVALUATION_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=evaluation_body())).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{evaluation}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    evaluation = await create_evaluation(client, evaluation_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{evaluation}"),
            await other_client.patch(
                f"{BASE}/{evaluation}", json={"status": "entered-in-error"}
            ),
            await other_client.delete(f"{BASE}/{evaluation}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_evaluation(
        client,
        evaluation_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}]),
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()
