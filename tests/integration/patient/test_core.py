"""Core patient endpoint coverage.

Patient has 6 endpoints (create/get/patch/list/delete/me), no
sub-resource routes. Every supplied sub-resource list on create/patch
(identifier, name, telecom, address, photo, contact, communication,
general_practitioner, link, marital_status_coding) replaces the corresponding rows wholesale.
Patient keeps `user_id` and a `/me` route.

This file holds:
- create (minimal + full nested payload, FHIR format, validation)
- read (plain + FHIR, not found)
- patch (field updates, sub-list replace, empty list clear, not found)
- list (plain, FHIR bundle, filters, pagination)
- /me (scoped to user_id)
- delete
- auth: cross-org isolation
"""

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import (
    assert_fhir_bundle,
    assert_fhir_patient,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_patient,
)
from tests.integration.patient.support import (
    BASE,
    FHIR_ACCEPT,
    FULL,
    MINIMAL,
    create_patient,
)

PATIENT_PERMS = [
    "patient:create",
    "patient:read",
    "patient:update",
    "patient:delete",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_patient_minimal(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 201, resp.text
    assert_plain_patient(resp.json(), active=True)
    assert resp.json()["name"][0]["family"] == "Chalmers"


async def test_create_patient_full(client):
    resp = await client.post(BASE + "/", json=FULL)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_patient(data, active=True, gender="male", user_id="end-user-1")
    assert data["birth_date"] == "1974-12-25"
    assert data["deceased_boolean"] is False
    assert data["marital_status_text"] == "Married"
    assert data["marital_status_codings"][0]["code"] == "M"
    assert data["identifier"][0]["value"] == "MRN-12345"
    assert data["name"][0]["family"] == "Chalmers"
    assert data["telecom"][0]["value"] == "+1-555-123-4567"
    assert data["address"][0]["city"] == "PleasantVille"
    assert data["photo"][0]["url"] == "https://fhir-server.dev/fhir/assets/patient.png"
    assert data["contact"][0]["name_family"] == "Chalmers"
    assert data["contact"][0]["relationships"][0]["codings"][0]["code"] == "N"
    assert data["communication"][0]["language_codings"][0]["code"] == "en"


async def test_create_patient_returns_fhir_format(client):
    resp = await client.post(BASE + "/", json=MINIMAL, headers=FHIR_ACCEPT)
    assert resp.status_code == 201
    assert "application/fhir+json" in resp.headers["content-type"]
    assert_fhir_patient(resp.json())
    assert resp.json()["name"][0]["family"] == "Chalmers"


async def test_create_patient_extra_field_rejected(client):
    resp = await client.post(BASE + "/", json={**MINIMAL, "nonexistent_field": "value"})
    assert_operation_outcome(
        resp.json(), expected_status=422, response_status=resp.status_code
    )


async def test_create_patient_tenant_id_in_body_rejected(client):
    """tenant_id/created_by/updated_by come from the verified token — not request-body fields."""
    resp = await client.post(BASE + "/", json={**MINIMAL, "tenant_id": "sneaky-org"})
    assert_operation_outcome(
        resp.json(), expected_status=422, response_status=resp.status_code
    )


async def test_create_patient_created_by_derived_from_actor(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 201
    data = resp.json()
    assert data["created_by"] == "u-test"
    assert data["org_id"] == "org-test"


async def test_create_patient_nonexistent_managing_organization_rejected(client):
    payload = {
        **MINIMAL,
        "managing_organization": "Organization/999999",
    }
    resp = await client.post(BASE + "/", json=payload)
    assert_operation_outcome(
        resp.json(), expected_status=422, response_status=resp.status_code
    )


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_patient_plain(client):
    pid = await create_patient(client, MINIMAL)
    resp = await client.get(f"{BASE}/{pid}")
    assert resp.status_code == 200
    assert_plain_patient(resp.json(), id=pid, active=True)
    assert resp.json()["name"][0]["family"] == "Chalmers"


async def test_get_patient_fhir(client):
    pid = await create_patient(client, MINIMAL)
    resp = await client.get(f"{BASE}/{pid}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert "application/fhir+json" in resp.headers["content-type"]
    assert_fhir_patient(resp.json(), id=str(pid))


async def test_get_patient_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert resp.status_code == 404
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_patient_scalar_fields(client):
    pid = await create_patient(client, MINIMAL)
    patch_payload = {"active": False, "gender": "female"}
    resp = await client.patch(f"{BASE}/{pid}", json=patch_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert_plain_patient(data, id=pid, active=False, gender="female")
    # Sub-resource from create should still be present
    assert data["name"][0]["family"] == "Chalmers"


async def test_patch_patient_sub_list_replace(client):
    pid = await create_patient(client, MINIMAL)
    patch_payload = {
        "name": [{"family": "NewFamily", "given": ["NewGiven"]}]
    }
    resp = await client.patch(f"{BASE}/{pid}", json=patch_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["name"]) == 1
    assert data["name"][0]["family"] == "NewFamily"


async def test_patch_patient_empty_list_clears(client):
    pid = await create_patient(client, FULL)
    resp = await client.patch(f"{BASE}/{pid}", json={"telecom": []})
    assert resp.status_code == 200
    data = resp.json()
    assert data["telecom"] == []


async def test_patch_patient_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"active": False})
    assert resp.status_code == 404
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_patients_plain(client):
    await create_patient(client, MINIMAL)
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200
    assert_paginated(resp.json())
    assert len(resp.json()["data"]) >= 1


async def test_list_patients_fhir(client):
    await create_patient(client, MINIMAL)
    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert "application/fhir+json" in resp.headers["content-type"]
    assert_fhir_bundle(resp.json())


async def test_list_patients_filter_by_family(client):
    await create_patient(
        client, {**MINIMAL, "name": [{"family": "SearchFamilyUnique"}]}
    )
    resp = await client.get(BASE + "/", params={"family": "SearchFamilyUnique"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["name"][0]["family"] == "SearchFamilyUnique"


async def test_list_patients_filter_by_active(client):
    await create_patient(client, {**MINIMAL, "active": False})
    resp = await client.get(BASE + "/", params={"active": "false"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert all(p["active"] is False for p in data)


async def test_list_patients_filter_by_identifier(client):
    await create_patient(
        client,
        {
            **MINIMAL,
            "identifier": [
                {"system": "http://hospital.example.com", "value": "ID-FILTER-123"}
            ],
        },
    )
    resp = await client.get(BASE + "/", params={"identifier": "ID-FILTER-123"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["identifier"][0]["value"] == "ID-FILTER-123"


async def test_list_patients_pagination(client):
    await create_patient(client, MINIMAL)
    await create_patient(client, MINIMAL)
    resp = await client.get(BASE + "/", params={"limit": 1, "offset": 0})
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 1
    assert resp.json()["limit"] == 1


# ── Me ───────────────────────────────────────────────────────────────────


async def test_me_scopes_to_user_id(client):
    # Patient 1 owned by u-test
    await create_patient(
        client,
        {
            **MINIMAL,
            "user_id": "u-test",
            "name": [{"family": "MyPatient"}],
        },
    )
    # Patient 2 owned by other-user
    await create_patient(
        client,
        {
            **MINIMAL,
            "user_id": "other-user",
            "name": [{"family": "OtherPatient"}],
        },
    )

    resp = await client.get(BASE + "/me")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert all(p["user_id"] == "u-test" for p in data)
    families = [p["name"][0]["family"] for p in data]
    assert "MyPatient" in families
    assert "OtherPatient" not in families


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_patient(client):
    pid = await create_patient(client, MINIMAL)
    del_resp = await client.delete(f"{BASE}/{pid}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"{BASE}/{pid}")
    assert get_resp.status_code == 404


async def test_delete_patient_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert resp.status_code == 404


# ── Cross-org isolation ──────────────────────────────────────────────────


async def test_patient_cross_org_isolation(client):
    # Create patient under org-test
    pid = await create_patient(client, MINIMAL)

    # Switch token to org-other
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other",
        org_id="org-other",
        permissions=PATIENT_PERMS,
    )

    # GET -> 404 (not 403, avoids existence leakage)
    resp_get = await client.get(f"{BASE}/{pid}")
    assert resp_get.status_code == 404

    # PATCH -> 404
    resp_patch = await client.patch(f"{BASE}/{pid}", json={"active": False})
    assert resp_patch.status_code == 404

    # DELETE -> 404
    resp_del = await client.delete(f"{BASE}/{pid}")
    assert resp_del.status_code == 404

    # LIST -> does not include patient from org-test
    resp_list = await client.get(BASE + "/")
    assert resp_list.status_code == 200
    pids = [p["id"] for p in resp_list.json()["data"]]
    assert pid not in pids
