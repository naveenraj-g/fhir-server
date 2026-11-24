"""Core flag endpoint coverage.

Flag is stored content-based (like Goal, Task, CarePlan and the other rebuilt resources): the
request body (genuine FHIR R4 Flag JSON) is validated and stored whole in `content`, every
response is FHIR R4 (`application/fhir+json`, regardless of Accept), and only the FHIR R4 search
parameters are indexed (https://www.hl7.org/fhir/R4/flag.html#search). R4 defines no search
parameter for `status`, `category` or `code`, so those live only in `content`.

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence checks on every local reference (`subject`, `encounter`, `author`
and every identifier's `assigner`). Search lives in test_search.py.

R4 requires `status`, `code` and `subject`; the native validator checks `code` and `subject` (it
cannot see a missing primitive `status`, which only the `java_validator` backend rejects).
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.flag.conftest import FLAG_PERMS
from tests.integration.flag.support import (
    BASE,
    FLAG_CATEGORY,
    concept,
    create_encounter,
    create_flag,
    create_group,
    create_location,
    create_medication,
    create_organization,
    create_patient,
    create_practitioner,
    encounter_body,
    flag_body,
    full_body,
    group_body,
    medication_body,
)


@pytest.fixture
def native_validation(monkeypatch):
    """The base R4 validator may be switched off in configs/config.yaml
    (`fhir_validation.enabled: false` skips it entirely). Tests that assert "a
    key that isn't FHIR is a 422" need it on: the project's own structural
    check (no sidecar needed)."""
    monkeypatch.setattr(settings.fhir_validation, "enabled", True)
    monkeypatch.setattr(settings.fhir_validation, "backend", "native")


def _ids(bundle: dict) -> set[int]:
    return {
        int(e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == "match"
    }


def _as_user(sub="u-test", org_id="org-test", permissions=FLAG_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client) -> tuple[int, dict]:
    patient = await create_patient(client)
    encounter = await create_encounter(
        client, encounter_body(subject={"reference": f"Patient/{patient}"})
    )
    practitioner = await create_practitioner(client)
    organization = await create_organization(client)
    body = full_body(patient, encounter, practitioner, organization)
    return await create_flag(client, body), body


def _subject(patient: int) -> dict:
    return {"reference": f"Patient/{patient}"}


async def _created(client, subject=None, **extra) -> int:
    return (await client.post(BASE + "/", json=flag_body(subject, **extra))).status_code


# -- Create ---------------------------------------------------------------------------------


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=flag_body())
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "Flag" and data["status"] == "active"


async def test_create_full_round_trip(client):
    flag, body = await _full(client)
    data = (await client.get(f"{BASE}/{flag}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_status_category_and_code_nothing_searches_on(client):
    """R4 defines no search parameter for `status`, `category` or `code`: they live only in
    `content`."""
    flag, _ = await _full(client)
    data = (await client.get(f"{BASE}/{flag}")).json()
    assert data["status"] == "active"
    assert data["category"][0]["coding"][0]["code"] == "safety"
    assert data["code"]["coding"][0]["code"] == "300916003"


@pytest.mark.parametrize("status", ["active", "inactive", "entered-in-error"])
async def test_create_every_status_round_trips(client, status):
    resp = await client.post(BASE + "/", json=flag_body(status=status))
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


async def test_create_ignores_server_managed_id_and_meta(client):
    body = flag_body(id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"})
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client):
    for bad in (
        {"status": "robot"},
        {"code": "x"},
        {"category": {"text": "x"}},
        {"subject": "Patient/1"},
        {"period": "today"},
        {"period": {"start": "soon"}},
        {"encounter": "Encounter/1"},
        {"author": "Practitioner/1"},
        {"identifier": {"value": "x"}},
    ):
        resp = await client.post(BASE + "/", json=flag_body(**bad))
        assert resp.status_code == 422, (bad, resp.text)


async def test_create_missing_required_elements_rejected(client, native_validation):
    for missing in ("code", "subject"):
        body = flag_body()
        del body[missing]
        resp = await client.post(BASE + "/", json=body)
        assert resp.status_code == 422, (missing, resp.text)


async def test_create_non_fhir_key_rejected(client, native_validation):
    resp = await client.post(BASE + "/", json=flag_body(not_a_fhir_element=1))
    assert resp.status_code == 422


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in ({"code_text": "x"}, {"subject_id": 5}, {"org_id": "x"}):
        resp = await client.post(BASE + "/", json=flag_body(**stale))
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(BASE + "/", json=flag_body(resourceType="Patient"))
    assert resp.status_code == 422


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=flag_body())).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# -- Create: existence checks on local references --------------------------------------------


async def test_create_subject_must_exist_for_every_rebuilt_type(client):
    patient = await create_patient(client)
    group = await create_group(client, group_body())
    organization = await create_organization(client)
    practitioner = await create_practitioner(client)
    location = await create_location(client)
    medication = await create_medication(client, medication_body())
    for reference in (
        f"Patient/{patient}",
        f"Group/{group}",
        f"Organization/{organization}",
        f"Practitioner/{practitioner}",
        f"Location/{location}",
        f"Medication/{medication}",
    ):
        assert await _created(client, {"reference": reference}) == 201, reference
    for missing in (
        "Patient/999999",
        "Group/999999",
        "Organization/999999",
        "Practitioner/999999",
        "Location/999999",
        "Medication/999999",
    ):
        assert await _created(client, {"reference": missing}) == 422, missing


async def test_create_subject_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    assert await _created(client, _subject(theirs)) == 422


async def test_create_encounter_and_author_must_exist(client):
    patient = await create_patient(client)
    encounter = await create_encounter(
        client, encounter_body(subject=_subject(patient))
    )
    practitioner = await create_practitioner(client)
    assert (
        await _created(
            client,
            encounter={"reference": f"Encounter/{encounter}"},
            author={"reference": f"Practitioner/{practitioner}"},
        )
        == 201
    )
    assert await _created(client, encounter={"reference": "Encounter/999999"}) == 422
    assert await _created(client, author={"reference": "Practitioner/999999"}) == 422


async def test_create_identifier_assigner_must_exist(client):
    organization = await create_organization(client)
    ok = [{"value": "1", "assigner": {"reference": f"Organization/{organization}"}}]
    bad = [{"value": "1", "assigner": {"reference": "Organization/999999"}}]
    assert await _created(client, identifier=ok) == 201
    assert await _created(client, identifier=bad) == 422


async def test_create_unmodeled_targets_are_not_checked(client):
    """A PlanDefinition subject and a Device author are not resources here yet / at all: stored as
    sent."""
    body = flag_body(
        {"reference": "PlanDefinition/999999"}, author={"reference": "Device/999999"}
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == {"reference": "PlanDefinition/999999"}
    assert resp.json()["author"] == {"reference": "Device/999999"}


async def test_create_absolute_and_logical_subjects_not_resolved(client):
    absolute = "https://other.example.org/fhir/Patient/7"
    resp = await client.post(BASE + "/", json=flag_body({"reference": absolute}))
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == {"reference": absolute}
    logical = {"identifier": {"system": "urn:mrn", "value": "M-9"}, "display": "Jane"}
    resp = await client.post(BASE + "/", json=flag_body(logical))
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == logical


# -- Read -----------------------------------------------------------------------------------


async def test_get_by_id(client):
    flag, _ = await _full(client)
    resp = await client.get(f"{BASE}/{flag}")
    assert resp.status_code == 200 and resp.json()["id"] == str(flag)


async def test_get_is_fhir_regardless_of_accept(client):
    flag = await create_flag(client, flag_body())
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{flag}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "Flag"


async def test_xml_only_accept_is_406(client):
    flag = await create_flag(client, flag_body())
    resp = await client.get(
        f"{BASE}/{flag}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Patch ----------------------------------------------------------------------------------


async def test_patch_scalar_keeps_the_rest(client):
    flag, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{flag}",
        json={"status": "inactive", "category": [concept(FLAG_CATEGORY, "admin")]},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "inactive"
    assert resp.json()["category"][0]["coding"][0]["code"] == "admin"
    assert resp.json()["code"]["coding"][0]["code"] == "300916003"  # untouched
    assert resp.json()["subject"]["reference"].startswith("Patient/")  # untouched


async def test_patch_reindexes_search(client):
    flag, _ = await _full(client)
    other = await create_patient(client)
    patched = await client.patch(
        f"{BASE}/{flag}",
        json={
            "subject": _subject(other),
            "period": {"start": "2027-03-01", "end": "2027-03-31"},
            "identifier": [{"system": "urn:f", "value": "F-2"}],
        },
    )
    assert patched.status_code == 200, patched.text
    assert flag not in _ids(
        (await client.get(BASE + "/", params={"identifier": "F-1001"})).json()
    )
    for param, value in (("identifier", "F-2"), ("date", "ge2027-03-01")):
        assert flag in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param
    assert flag not in _ids(
        (await client.get(BASE + "/", params={"date": "ge2028-01-01"})).json()
    )
    assert flag in _ids(
        (await client.get(BASE + "/", params={"patient": str(other)})).json()
    )


async def test_patch_replaces_lists_and_empty_clears(client):
    flag, _ = await _full(client)
    resp = await client.patch(f"{BASE}/{flag}", json={"identifier": []})
    assert "identifier" not in resp.json()
    assert resp.json()["status"] == "active"  # untouched
    assert flag in _ids(
        (await client.get(BASE + "/", params={"identifier:missing": "true"})).json()
    )


async def test_patch_clears_period_encounter_and_author(client):
    flag, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{flag}", json={"period": None, "encounter": None, "author": None}
    )
    assert all(k not in resp.json() for k in ("period", "encounter", "author"))
    for param in ("date", "encounter", "author"):
        assert flag in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client):
    flag = await create_flag(client, flag_body())
    resp = await client.patch(
        f"{BASE}/{flag}", json={"author": {"reference": "Practitioner/999999"}}
    )
    assert resp.status_code == 422
    assert "author" not in (await client.get(f"{BASE}/{flag}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    flag = await create_flag(client, flag_body())
    assert (
        await client.patch(f"{BASE}/{flag}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{flag}")).json()["status"] == "active"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "active"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Delete ---------------------------------------------------------------------------------


async def test_delete(client):
    flag, _ = await _full(client)
    assert (await client.delete(f"{BASE}/{flag}")).status_code == 204
    assert (await client.get(f"{BASE}/{flag}")).status_code == 404
    # Its index rows are gone with it.
    assert flag not in _ids(
        (await client.get(BASE + "/", params={"identifier": "F-1001"})).json()
    )


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Auth -----------------------------------------------------------------------------------


async def test_create_without_permission(client):
    _as_user(permissions=["flag:read"])
    assert (await client.post(BASE + "/", json=flag_body())).status_code == 403


async def test_org_less_token_rejected(client):
    flag = await create_flag(client, flag_body())

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": FLAG_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=flag_body())).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{flag}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    flag = await create_flag(client, flag_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{flag}"),
            await other_client.patch(f"{BASE}/{flag}", json={"status": "active"}),
            await other_client.delete(f"{BASE}/{flag}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_flag(
        client, flag_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}])
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()


async def test_flag_is_checked_where_a_reference_any_can_name_it(client):
    """DetectedIssue.implicated is Reference(Any): a relative Flag there must exist (422
    otherwise)."""
    flag = await create_flag(client, flag_body())
    issues = "/api/fhir/v1/detected-issues/"
    ok = {"status": "final", "implicated": [{"reference": f"Flag/{flag}"}]}
    assert (await client.post(issues, json=ok)).status_code == 201
    missing = {"status": "final", "implicated": [{"reference": "Flag/999999"}]}
    assert (await client.post(issues, json=missing)).status_code == 422
