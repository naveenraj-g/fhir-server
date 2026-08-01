"""Core patient endpoint coverage.

This file holds the top-level patient contract:
- create
- read
- patch
- delete
- list
- /me
- permission and content negotiation checks
"""

from app.auth.dependencies import get_current_user
from tests.conftest import make_test_user
from tests.helpers.assertions import (
    assert_fhir_bundle,
    assert_fhir_patient,
    assert_operation_outcome,
    assert_paginated,
    assert_plain_patient,
)
from tests.integration.patient.support import BASE, FHIR_ACCEPT, FULL, MINIMAL, create_patient


async def test_create_patient_minimal(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 200
    assert_plain_patient(resp.json(), gender="male", active=True)


async def test_create_patient_full(client):
    resp = await client.post(BASE + "/", json=FULL)
    assert resp.status_code == 200
    data = resp.json()
    assert_plain_patient(
        data,
        gender="female",
        birth_date="1990-06-15",
        marital_status_code="M",
        marital_status_display="Married",
        multiple_birth_boolean=False,
    )


async def test_create_patient_returns_fhir_format(client):
    resp = await client.post(BASE + "/", json=MINIMAL, headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert "application/fhir+json" in resp.headers["content-type"]
    assert_fhir_patient(resp.json(), gender="male")


async def test_create_patient_full_returns_fhir_reference_mapping(client):
    resp = await client.post(BASE + "/", json=FULL, headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    data = resp.json()
    assert_fhir_patient(data, gender="female")
    assert data["birthDate"] == "1990-06-15"
    assert data["maritalStatus"]["coding"][0]["code"] == "M"


async def test_create_patient_extra_field_rejected(client):
    resp = await client.post(BASE + "/", json={**MINIMAL, "nonexistent_field": "value"})
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_patient_invalid_managing_organization_reference_rejected(client):
    resp = await client.post(BASE + "/", json={**MINIMAL, "managing_organization": "BadReference"})
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_get_patient_by_id_plain(client):
    patient_id = await create_patient(client)
    resp = await client.get(f"{BASE}/{patient_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert_plain_patient(data, gender="male")
    assert data["id"] == patient_id


async def test_get_patient_by_id_fhir(client):
    patient_id = await create_patient(client)
    resp = await client.get(f"{BASE}/{patient_id}", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert_fhir_patient(resp.json())
    assert resp.json()["id"] == str(patient_id)


async def test_get_patient_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


async def test_patch_patient_gender(client):
    patient_id = await create_patient(client)
    resp = await client.patch(f"{BASE}/{patient_id}", json={"gender": "female"})
    assert resp.status_code == 200
    assert resp.json()["gender"] == "female"


async def test_patch_patient_birth_date(client):
    patient_id = await create_patient(client)
    resp = await client.patch(f"{BASE}/{patient_id}", json={"birth_date": "1985-03-20"})
    assert resp.status_code == 200
    assert resp.json()["birth_date"] == "1985-03-20"


async def test_patch_patient_active_false(client):
    patient_id = await create_patient(client)
    resp = await client.patch(f"{BASE}/{patient_id}", json={"active": False})
    assert resp.status_code == 200
    assert resp.json()["active"] is False


async def test_patch_patient_can_clear_nullable_fields(client):
    patient_id = await create_patient(client, FULL)
    resp = await client.patch(
        f"{BASE}/{patient_id}",
        json={
            "multiple_birth_boolean": None,
            "marital_status_code": None,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "multiple_birth_boolean" not in data or data["multiple_birth_boolean"] is None
    assert "marital_status_code" not in data or data["marital_status_code"] is None


async def test_patch_patient_invalid_managing_organization_reference_rejected(client):
    patient_id = await create_patient(client)
    resp = await client.patch(f"{BASE}/{patient_id}", json={"managing_organization": "Not/A/Valid/Ref"})
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_patch_patient_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"gender": "female"})
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


async def test_delete_patient(client):
    patient_id = await create_patient(client)
    resp = await client.delete(f"{BASE}/{patient_id}")
    assert resp.status_code == 204
    assert (await client.get(f"{BASE}/{patient_id}")).status_code == 404


async def test_delete_patient_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


async def test_list_patients_plain(client):
    await client.post(BASE + "/", json=MINIMAL)
    await client.post(BASE + "/", json={**FULL, "user_id": "u-test-full"})
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200
    assert_paginated(resp.json(), min_total=2)


async def test_list_patients_fhir_bundle(client):
    await client.post(BASE + "/", json=MINIMAL)
    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    data = resp.json()
    assert_fhir_bundle(data, min_total=1)
    assert data["entry"][0]["resource"]["resourceType"] == "Patient"


async def test_list_patients_pagination(client):
    for idx in range(5):
        await client.post(BASE + "/", json={**MINIMAL, "user_id": f"u-test-{idx}"})
    resp = await client.get(BASE + "/?limit=2&offset=0")
    assert resp.status_code == 200
    data = resp.json()
    assert data["limit"] == 2
    assert data["offset"] == 0
    assert len(data["data"]) == 2
    assert data["total"] >= 5


async def test_list_patients_filter_gender(client):
    await client.post(BASE + "/", json={**MINIMAL, "user_id": "u-gender-male", "gender": "male"})
    await client.post(BASE + "/", json={**MINIMAL, "user_id": "u-gender-female", "gender": "female"})
    resp = await client.get(BASE + "/?gender=female")
    assert resp.status_code == 200
    data = resp.json()
    assert_paginated(data, min_total=1)
    for patient in data["data"]:
        assert patient["gender"] == "female"


async def test_list_patients_filter_active(client):
    await client.post(BASE + "/", json={**MINIMAL, "user_id": "u-active-true", "active": True})
    await client.post(BASE + "/", json={**MINIMAL, "user_id": "u-active-false", "active": False})
    resp = await client.get(BASE + "/?active=true")
    assert resp.status_code == 200
    for patient in resp.json()["data"]:
        assert patient["active"] is True


async def test_list_patients_empty(client):
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["data"] == []


async def test_get_my_patient_profile_found(client):
    await client.post(BASE + "/", json=MINIMAL)
    resp = await client.get(BASE + "/me")
    assert resp.status_code == 200
    assert_plain_patient(resp.json(), gender="male")


async def test_get_my_patient_profile_not_found(client):
    resp = await client.get(BASE + "/me")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


async def test_get_my_patient_profile_org_isolation(client, other_client):
    await client.post(BASE + "/", json=MINIMAL)
    resp = await other_client.get(BASE + "/me")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


async def test_create_patient_no_permission(client):
    app = client._transport.app
    app.dependency_overrides[get_current_user] = make_test_user(permissions=["patient:read"])
    try:
        resp = await client.post(BASE + "/", json=MINIMAL)
        assert_operation_outcome(resp.json(), expected_status=403, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user()


async def test_content_negotiation_defaults_to_plain(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 200
    assert "application/json" in resp.headers["content-type"]
    data = resp.json()
    assert "resourceType" not in data
    assert isinstance(data["id"], int)


async def test_content_negotiation_fhir_accept(client):
    resp = await client.post(BASE + "/", json=MINIMAL, headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "Patient"
    assert isinstance(data["id"], str)


async def test_list_content_negotiation_fhir(client):
    await client.post(BASE + "/", json=MINIMAL)
    resp = await client.get(BASE + "/", headers=FHIR_ACCEPT)
    assert resp.status_code == 200
    data = resp.json()
    assert data["resourceType"] == "Bundle"
    assert data["type"] == "searchset"
