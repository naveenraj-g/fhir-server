"""Core AllergyIntolerance endpoint coverage.

AllergyIntolerance has 5 endpoints (create/get/patch/list/delete), no sub-resource routes and no /me route.
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
    assert_fhir_allergy_intolerance,
    assert_fhir_bundle,
    assert_paginated,
    assert_plain_allergy_intolerance,
)
from tests.integration.allergy_intolerance.support import (
    BASE,
    FHIR_ACCEPT,
    create_allergy_intolerance,
    create_test_encounter,
    create_test_patient,
    create_test_practitioner,
    full_allergy_intolerance,
    minimal_allergy_intolerance,
)

ALLERGY_PERMS = [
    "allergy_intolerance:create",
    "allergy_intolerance:read",
    "allergy_intolerance:update",
    "allergy_intolerance:delete",
    "patient:create",
    "patient:read",
    "practitioner:create",
    "practitioner:read",
    "encounter:create",
    "encounter:read",
    "organization:create",
    "organization:read",
]


# ── Create ───────────────────────────────────────────────────────────────


async def test_create_allergy_intolerance_minimal(client):
    p_id = await create_test_patient(client)
    resp = await client.post(BASE + "/", json=minimal_allergy_intolerance(p_id))
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_allergy_intolerance(data)
    assert data["patient"] == f"Patient/{p_id}"
    assert data["id"] >= 260000


async def test_create_allergy_intolerance_full(client):
    p_id = await create_test_patient(client)
    pr_id = await create_test_practitioner(client)
    enc_id = await create_test_encounter(client, p_id)
    payload = full_allergy_intolerance(p_id, pr_id, enc_id)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_plain_allergy_intolerance(data)
    assert data["type"] == "allergy"
    assert data["category"] == ["food"]
    assert data["criticality"] == "high"
    assert data["patient"] == f"Patient/{p_id}"
    assert data["recorder"] == f"Practitioner/{pr_id}"
    assert data["encounter"] == f"Encounter/{enc_id}"
    assert len(data["reaction"]) == 1
    assert data["reaction"][0]["severity"] == "severe"
    assert len(data["reaction"][0]["manifestation"]) == 1
    assert len(data["note"]) == 1
    assert len(data["identifier"]) == 1


async def test_create_allergy_intolerance_fhir_format(client):
    p_id = await create_test_patient(client)
    resp = await client.post(
        BASE + "/", json=minimal_allergy_intolerance(p_id), headers=FHIR_ACCEPT
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert_fhir_allergy_intolerance(data)
    assert data["patient"]["reference"] == f"Patient/{p_id}"
    assert int(data["id"]) >= 260000


async def test_create_allergy_intolerance_unknown_patient_422(client):
    payload = minimal_allergy_intolerance(99999999)
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 422


async def test_create_allergy_intolerance_org_less_403(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None, permissions=ALLERGY_PERMS
    )
    p_id = 10001
    resp = await client.post(BASE + "/", json=minimal_allergy_intolerance(p_id))
    assert resp.status_code == 403


# ── Read ─────────────────────────────────────────────────────────────────


async def test_get_allergy_intolerance_plain(client):
    created = await create_allergy_intolerance(client)
    aid = created["id"]
    resp = await client.get(f"{BASE}/{aid}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_allergy_intolerance(data, id=aid)


async def test_get_allergy_intolerance_fhir(client):
    created = await create_allergy_intolerance(client)
    aid = created["id"]
    resp = await client.get(f"{BASE}/{aid}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_allergy_intolerance(data, id=str(aid))


async def test_get_allergy_intolerance_not_found(client):
    resp = await client.get(f"{BASE}/99999999")
    assert resp.status_code == 404


async def test_get_allergy_intolerance_cross_org_404(client):
    created = await create_allergy_intolerance(client)
    aid = created["id"]

    # Switch to different org
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="different-org-456", permissions=ALLERGY_PERMS
    )
    resp = await client.get(f"{BASE}/{aid}")
    assert resp.status_code == 404


# ── Patch ────────────────────────────────────────────────────────────────


async def test_patch_allergy_intolerance_scalars(client):
    created = await create_allergy_intolerance(client)
    aid = created["id"]
    resp = await client.patch(
        f"{BASE}/{aid}",
        json={
            "criticality": "low",
            "type": "intolerance",
            "onset_string": "early childhood",
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_plain_allergy_intolerance(data, id=aid)
    assert data["criticality"] == "low"
    assert data["type"] == "intolerance"
    assert data["onset_string"] == "early childhood"


async def test_patch_allergy_intolerance_reactions_replace(client):
    p_id = await create_test_patient(client)
    created = await create_allergy_intolerance(
        client, full_allergy_intolerance(p_id)
    )
    aid = created["id"]
    assert len(created["reaction"]) == 1

    # Replace reaction
    resp = await client.patch(
        f"{BASE}/{aid}",
        json={
            "reaction": [
                {
                    "description": "Mild tingling in mouth",
                    "severity": "mild",
                    "manifestation": [
                        {
                            "text": "Oral tingling",
                        }
                    ],
                }
            ]
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["reaction"]) == 1
    assert data["reaction"][0]["description"] == "Mild tingling in mouth"
    assert data["reaction"][0]["severity"] == "mild"


async def test_patch_allergy_intolerance_fhir_format(client):
    created = await create_allergy_intolerance(client)
    aid = created["id"]
    resp = await client.patch(
        f"{BASE}/{aid}",
        json={"criticality": "high"},
        headers=FHIR_ACCEPT,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_allergy_intolerance(data)
    assert data["criticality"] == "high"


async def test_patch_allergy_intolerance_not_found(client):
    resp = await client.patch(
        f"{BASE}/99999999", json={"criticality": "low"}
    )
    assert resp.status_code == 404


async def test_patch_allergy_intolerance_cross_org_404(client):
    created = await create_allergy_intolerance(client)
    aid = created["id"]

    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="different-org-456", permissions=ALLERGY_PERMS
    )
    resp = await client.patch(
        f"{BASE}/{aid}", json={"criticality": "low"}
    )
    assert resp.status_code == 404


# ── List ─────────────────────────────────────────────────────────────────


async def test_list_allergy_intolerances_plain(client):
    await create_allergy_intolerance(client)
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_paginated(data)
    assert len(data["data"]) >= 1
    assert_plain_allergy_intolerance(data["data"][0])


async def test_list_allergy_intolerances_fhir_bundle(client):
    await create_allergy_intolerance(client)
    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert_fhir_bundle(data)
    assert len(data["entry"]) >= 1
    assert data["entry"][0]["resource"]["resourceType"] == "AllergyIntolerance"


async def test_list_allergy_intolerances_filter_clinical_status(client):
    p_id = await create_test_patient(client)
    created = await create_allergy_intolerance(
        client, full_allergy_intolerance(p_id)
    )
    aid = created["id"]

    resp = await client.get(BASE + "/?clinical_status=active")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert aid in ids

    resp_empty = await client.get(BASE + "/?clinical_status=resolved")
    assert resp_empty.status_code == 200
    ids_empty = [item["id"] for item in resp_empty.json()["data"]]
    assert aid not in ids_empty


async def test_list_allergy_intolerances_filter_category(client):
    p_id = await create_test_patient(client)
    created = await create_allergy_intolerance(
        client, full_allergy_intolerance(p_id)
    )
    aid = created["id"]

    resp = await client.get(BASE + "/?category=food")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert aid in ids

    resp_empty = await client.get(BASE + "/?category=environment")
    assert resp_empty.status_code == 200
    ids_empty = [item["id"] for item in resp_empty.json()["data"]]
    assert aid not in ids_empty


async def test_list_allergy_intolerances_filter_patient(client):
    p_id = await create_test_patient(client)
    created = await create_allergy_intolerance(
        client, minimal_allergy_intolerance(p_id)
    )
    aid = created["id"]

    resp = await client.get(f"{BASE}/?patient=Patient/{p_id}")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert aid in ids


async def test_list_allergy_intolerances_filter_severity(client):
    p_id = await create_test_patient(client)
    created = await create_allergy_intolerance(
        client, full_allergy_intolerance(p_id)
    )
    aid = created["id"]

    resp = await client.get(BASE + "/?severity=severe")
    assert resp.status_code == 200, resp.text
    ids = [item["id"] for item in resp.json()["data"]]
    assert aid in ids

    resp_empty = await client.get(BASE + "/?severity=mild")
    assert resp_empty.status_code == 200
    ids_empty = [item["id"] for item in resp_empty.json()["data"]]
    assert aid not in ids_empty


async def test_list_allergy_intolerances_pagination(client):
    p_id = await create_test_patient(client)
    for _ in range(3):
        await create_allergy_intolerance(client, minimal_allergy_intolerance(p_id))

    resp = await client.get(BASE + "/?limit=2&offset=0")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert len(data["data"]) == 2
    assert data["total"] >= 3


# ── Delete ───────────────────────────────────────────────────────────────


async def test_delete_allergy_intolerance_success(client):
    created = await create_allergy_intolerance(client)
    aid = created["id"]

    del_resp = await client.delete(f"{BASE}/{aid}")
    assert del_resp.status_code == 204

    get_resp = await client.get(f"{BASE}/{aid}")
    assert get_resp.status_code == 404


async def test_delete_allergy_intolerance_not_found(client):
    resp = await client.delete(f"{BASE}/99999999")
    assert resp.status_code == 404


async def test_delete_allergy_intolerance_cross_org_404(client):
    created = await create_allergy_intolerance(client)
    aid = created["id"]

    app.dependency_overrides[get_current_user] = make_test_user(
        org_id="different-org-456", permissions=ALLERGY_PERMS
    )
    resp = await client.delete(f"{BASE}/{aid}")
    assert resp.status_code == 404
