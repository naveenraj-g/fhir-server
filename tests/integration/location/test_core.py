"""Core Location endpoint coverage.

Location is stored Medplum-style, like Organization: the request body
(genuine FHIR R4 Location JSON) is validated and stored whole in `content`,
every response is FHIR R4 (`application/fhir+json`, regardless of Accept),
and only the FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/location.html#search).

This file holds create / read / patch / delete, reference checks, the partOf
hierarchy rule, auth, and content type. Search lives in test_search.py.
"""

import json
from pathlib import Path

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.location.support import (
    BASE,
    FULL,
    MINIMAL,
    create_location,
    create_organization,
)

LOC_PERMS = [
    "location:create",
    "location:read",
    "location:update",
    "location:delete",
    "organization:create",
    "organization:read",
]

_EXT = "https://fhir-server.dev/fhir/StructureDefinition"


def _meta_ext(resource: dict, name: str):
    for ext in (resource.get("meta") or {}).get("extension") or []:
        if ext["url"] == f"{_EXT}/{name}":
            return ext.get("valueString") or ext.get("valueDateTime")
    return None


def _content(resource: dict) -> dict:
    return {k: v for k, v in resource.items() if k not in ("resourceType", "id", "meta")}


def _fixture() -> dict:
    return json.loads((Path(__file__).parent / "fixtures" / "r4_full_location.json").read_text())


def _422(resp):
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 201, resp.text
    assert resp.headers["content-type"].startswith("application/fhir+json")
    body = resp.json()
    assert body["resourceType"] == "Location"
    assert body["name"] == "Main Building"
    assert int(body["id"]) >= 230000


async def test_create_full_round_trip(client):
    resp = await client.post(BASE + "/", json=FULL)
    assert resp.status_code == 201, resp.text
    assert _content(resp.json()) == {k: v for k, v in FULL.items() if k != "resourceType"}


async def test_create_full_r4_payload_stored_as_sent(client):
    """Every R4 element — including ones nothing searches on (telecom,
    hoursOfOperation, physicalType, position.altitude, periods) — is stored
    and served back exactly as sent."""
    body = _fixture()
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    loc = resp.json()
    assert _content(loc) == {k: v for k, v in body.items() if k != "resourceType"}
    got = await client.get(f"{BASE}/{loc['id']}")
    assert _content(got.json()) == _content(loc)


async def test_create_ignores_server_managed_id_and_meta(client):
    resp = await client.post(BASE + "/", json={**MINIMAL, "id": "999", "meta": {"versionId": "7"}})
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert "versionId" not in resp.json()["meta"]


async def test_create_audit_meta_from_actor(client):
    loc = (await client.post(BASE + "/", json=MINIMAL)).json()
    assert _meta_ext(loc, "created-by") == "u-test"
    assert _meta_ext(loc, "org-id") == "org-test"
    assert loc["meta"]["lastUpdated"]


async def test_create_rejects_non_fhir_and_old_flat_fields(client):
    for body in (
        {**MINIMAL, "nonexistent_field": "x"},
        {**MINIMAL, "org_id": "sneaky"},
        {**MINIMAL, "address_city": "Springfield"},
        {**MINIMAL, "position_latitude": "42.1"},
        {**MINIMAL, "managing_organization": "Organization/1"},
        {**MINIMAL, "resourceType": "Organization"},
    ):
        resp = await client.post(BASE + "/", json=body)
        assert resp.status_code == 422, body


async def test_create_rejects_invalid_codes(client):
    for body in (
        {**MINIMAL, "status": "open"},
        {**MINIMAL, "mode": "both"},
        {**MINIMAL, "hoursOfOperation": [{"daysOfWeek": ["monday"]}]},
        {**MINIMAL, "address": [{"city": "X"}]},  # Location.address is 0..1
        {**MINIMAL, "position": {"latitude": 1}},  # longitude is 1..1 within position
    ):
        resp = await client.post(BASE + "/", json=body)
        assert resp.status_code == 422, body


async def test_create_with_managing_organization_and_partof(client):
    org_id = await create_organization(client)
    parent = await create_location(client, {**MINIMAL, "name": "Building"})
    body = {
        **MINIMAL,
        "name": "Room 1",
        "managingOrganization": {"reference": f"Organization/{org_id}"},
        "partOf": {"reference": f"Location/{parent}"},
    }
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["partOf"] == {"reference": f"Location/{parent}"}


async def test_create_nonexistent_references_rejected(client):
    for body in (
        {**MINIMAL, "managingOrganization": {"reference": "Organization/9999999"}},
        {**MINIMAL, "partOf": {"reference": "Location/9999999"}},
        {**MINIMAL, "identifier": [{"value": "1", "assigner": {"reference": "Organization/9999999"}}]},
    ):
        _422(await client.post(BASE + "/", json=body))


async def test_create_absolute_references_stored_not_resolved(client):
    ref = {"reference": "https://other.example/fhir/Organization/42"}
    resp = await client.post(BASE + "/", json={**MINIMAL, "managingOrganization": ref})
    assert resp.status_code == 201, resp.text
    assert resp.json()["managingOrganization"] == ref


# ── Read ─────────────────────────────────────────────────────────────────────


async def test_get_by_id(client):
    loc_id = await create_location(client)
    resp = await client.get(f"{BASE}/{loc_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(loc_id)


async def test_get_is_fhir_regardless_of_accept(client):
    loc_id = await create_location(client)
    resp = await client.get(f"{BASE}/{loc_id}", headers={"Accept": "application/json"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/fhir+json")
    assert resp.json()["resourceType"] == "Location"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/9999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


async def test_xml_only_accept_is_406(client):
    loc_id = await create_location(client)
    resp = await client.get(f"{BASE}/{loc_id}", headers={"Accept": "application/fhir+xml"})
    assert resp.status_code == 406
    assert resp.json()["issue"][0]["code"] == "not-supported"
    assert (await client.get(f"{BASE}/{loc_id}", params={"_format": "xml"})).status_code == 406


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_replaces_only_supplied_elements(client):
    loc_id = await create_location(client, FULL)
    resp = await client.patch(f"{BASE}/{loc_id}", json={"status": "suspended", "alias": ["New Alias"]})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "suspended"
    assert body["alias"] == ["New Alias"]
    assert body["address"] == FULL["address"]
    assert body["hoursOfOperation"] == FULL["hoursOfOperation"]
    assert _meta_ext(body, "updated-by") == "u-test"


async def test_patch_null_and_empty_list_clear(client):
    loc_id = await create_location(client, FULL)
    resp = await client.patch(f"{BASE}/{loc_id}", json={"address": None, "telecom": [], "position": None})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert "address" not in body and "telecom" not in body and "position" not in body


async def test_patch_reindexes(client):
    loc_id = await create_location(client, {**MINIMAL, "name": "Old Name"})
    await client.patch(f"{BASE}/{loc_id}", json={"name": "Fresh Name", "address": {"city": "Newtown"}})
    found = (await client.get(BASE + "/", params={"name": "fresh", "address-city": "newt"})).json()
    assert [e["resource"]["id"] for e in found["entry"]] == [str(loc_id)]
    assert (await client.get(BASE + "/", params={"name": "old"})).json()["total"] == 0


async def test_patch_invalid_result_rejected(client):
    loc_id = await create_location(client)
    _422(await client.patch(f"{BASE}/{loc_id}", json={"status": "open"}))
    _422(await client.patch(f"{BASE}/{loc_id}", json={"not_fhir": 1}))


async def test_patch_partof_cycle_rejected(client):
    a = await create_location(client, {**MINIMAL, "name": "A"})
    b = await create_location(client, {**MINIMAL, "name": "B", "partOf": {"reference": f"Location/{a}"}})
    _422(await client.patch(f"{BASE}/{a}", json={"partOf": {"reference": f"Location/{b}"}}))
    _422(await client.patch(f"{BASE}/{a}", json={"partOf": {"reference": f"Location/{a}"}}))


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/9999999", json={"name": "x"})
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete(client):
    loc_id = await create_location(client, FULL)
    assert (await client.delete(f"{BASE}/{loc_id}")).status_code == 204
    assert (await client.get(f"{BASE}/{loc_id}")).status_code == 404
    assert (await client.delete(f"{BASE}/{loc_id}")).status_code == 404


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_create_without_permission_forbidden(client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=["location:read"])
    try:
        assert (await client.post(BASE + "/", json=MINIMAL)).status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=LOC_PERMS)


async def test_org_less_token_rejected(client):
    app.dependency_overrides[get_current_user] = make_test_user(org_id=None, permissions=LOC_PERMS)
    try:
        assert (await client.post(BASE + "/", json=MINIMAL)).status_code == 403
        assert (await client.get(BASE + "/")).status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=LOC_PERMS)


async def test_other_org_gets_404_and_empty_search(client, other_client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=LOC_PERMS)
    loc_id = await create_location(client, {**MINIMAL, "name": "Tenant-A-Only"})
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=LOC_PERMS
    )
    try:
        assert (await other_client.get(f"{BASE}/{loc_id}")).status_code == 404
        assert (await other_client.patch(f"{BASE}/{loc_id}", json={"name": "x"})).status_code == 404
        assert (await other_client.delete(f"{BASE}/{loc_id}")).status_code == 404
        assert (await other_client.get(BASE + "/", params={"name": "tenant-a"})).json()["total"] == 0
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=LOC_PERMS)
