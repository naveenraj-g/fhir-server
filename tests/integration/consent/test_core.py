"""Core consent endpoint coverage.

Consent has 5 endpoints (create/get/patch/list/delete), no sub-resource routes and no /me route.
Every supplied sub-resource list on create/patch replaces corresponding rows wholesale.

This file holds:
- create (minimal + full nested payload, FHIR format, validation, reference check)
- read (plain + FHIR, not found)
- patch (field updates, sub-list replace, not found)
- list (plain, FHIR bundle, filters, pagination)
- delete
- auth: cross-org isolation and org-less rejection
"""

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import (
    assert_fhir_bundle,
    assert_fhir_consent,
    assert_paginated,
    assert_plain_consent,
)
from tests.integration.consent.support import (
    BASE,
    FHIR_ACCEPT,
    create_consent,
    create_test_organization,
    create_test_patient,
    create_test_practitioner,
    full_consent,
    minimal_consent,
)

CONSENT_PERMS = [
    "consent:create",
    "consent:read",
    "consent:update",
    "consent:delete",
    "patient:create",
    "patient:read",
    "practitioner:create",
    "practitioner:read",
    "organization:create",
    "organization:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_consent_minimal(client):
    p_id = await create_test_patient(client)
    resp = await client.post(BASE + "/", json=minimal_consent(p_id))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_consent(data)
    assert data["status"] == "active"
    assert data["id"] >= 440000


async def test_create_consent_full(client):
    p_id = await create_test_patient(client)
    pr_id = await create_test_practitioner(client)
    org_id = await create_test_organization(client)
    payload = full_consent(p_id, pr_id, org_id)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_consent(data)
    assert data["status"] == "active"
    assert data["patient"] == f"Patient/{p_id}"
    assert len(data["performer"]) == 1
    assert data["performer"][0]["reference"] == f"Practitioner/{pr_id}"
    assert len(data["organization"]) == 1
    assert data["organization"][0]["reference"] == f"Organization/{org_id}"
    assert len(data["policy"]) == 1
    assert data["policy"][0]["authority"] == "http://example.org/fhir/ConsentPolicy"
    assert data["policy_rule"]["text"] == "opt-in"
    assert len(data["verification"]) == 1
    assert data["verification"][0]["verified"] is True
    assert data["provision"] is not None
    assert data["provision"]["type"] == "permit"
    assert len(data["provision"]["actor"]) == 1
    assert len(data["provision"]["action"]) == 1
    assert len(data["identifier"]) == 1


async def test_create_consent_fhir_format(client):
    p_id = await create_test_patient(client)
    resp = await client.post(
        BASE + "/", json=minimal_consent(p_id), headers=FHIR_ACCEPT
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_consent(data)
    assert data["status"] == "active"
    assert int(data["id"]) >= 440000


async def test_create_consent_invalid_ref_422(client):
    payload = minimal_consent()
    payload["patient"] = "Patient/999999"
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 422, resp.text


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_consent_plain(client):
    c_id = await create_consent(client)
    resp = await client.get(f"{BASE}/{c_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_consent(data)
    assert data["id"] == c_id


async def test_get_consent_fhir(client):
    c_id = await create_consent(client)
    resp = await client.get(f"{BASE}/{c_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_consent(data)
    assert data["id"] == str(c_id)


async def test_get_consent_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert resp.status_code == 404, resp.text


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_consent_fields(client):
    c_id = await create_consent(client)
    patch_payload = {
        "status": "inactive",
    }
    resp = await client.patch(f"{BASE}/{c_id}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "inactive"


async def test_patch_consent_sub_resources(client):
    c_id = await create_consent(client)
    patch_payload = {
        "policy": [
            {
                "authority": "http://example.org/new-policy",
                "uri": "http://example.org/new-policy/1",
            }
        ],
        "identifier": [
            {
                "system": "http://example.org/new-sys",
                "value": "NEW-001",
            }
        ],
    }
    resp = await client.patch(f"{BASE}/{c_id}", json=patch_payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["policy"]) == 1
    assert data["policy"][0]["authority"] == "http://example.org/new-policy"
    assert len(data["identifier"]) == 1
    assert data["identifier"][0]["value"] == "NEW-001"


async def test_patch_consent_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "inactive"})
    assert resp.status_code == 404, resp.text


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_consents_plain(client):
    await create_consent(client)
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data, min_total=1)


async def test_list_consents_fhir_bundle(client):
    await create_consent(client)
    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data, min_total=1)
    assert data["entry"][0]["resource"]["resourceType"] == "Consent"


async def test_list_consents_filter_status(client):
    p_id = await create_test_patient(client)
    c_id = await create_consent(client, minimal_consent(p_id))
    resp = await client.get(f"{BASE}/?status=active")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert any(c["id"] == c_id for c in data["data"])

    resp_none = await client.get(f"{BASE}/?status=entered-in-error")
    assert resp_none.status_code == 200, resp_none.text
    data_none = resp_none.json()
    assert not any(c["id"] == c_id for c in data_none["data"])


async def test_list_consents_filter_patient(client):
    p_id = await create_test_patient(client)
    c_id = await create_consent(client, minimal_consent(p_id))
    resp = await client.get(f"{BASE}/?patient=Patient/{p_id}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert any(c["id"] == c_id for c in data["data"])


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_consent(client):
    c_id = await create_consent(client)
    del_resp = await client.delete(f"{BASE}/{c_id}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"{BASE}/{c_id}")
    assert get_resp.status_code == 404


# ── Auth & Scoping ───────────────────────────────────────────────────────


async def test_cross_org_isolation(client):
    # Create consent under default org
    c_id = await create_consent(client)

    # Switch to different org
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="other-org",
        permissions=CONSENT_PERMS,
    )

    # Different org cannot read, patch, or delete (returns 404, never leaks existence)
    resp_get = await client.get(f"{BASE}/{c_id}")
    assert resp_get.status_code == 404

    resp_patch = await client.patch(f"{BASE}/{c_id}", json={"status": "inactive"})
    assert resp_patch.status_code == 404

    resp_del = await client.delete(f"{BASE}/{c_id}")
    assert resp_del.status_code == 404

    # Restore default test user
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=CONSENT_PERMS
    )


async def test_org_less_token_rejected(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=CONSENT_PERMS,
    )

    resp_post = await client.post(BASE + "/", json=minimal_consent())
    assert resp_post.status_code == 403

    resp_list = await client.get(BASE + "/")
    assert resp_list.status_code == 403

    # Restore
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=CONSENT_PERMS
    )
