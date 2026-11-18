"""Core endpoint coverage.

Endpoint is stored Medplum-style (like Organization/Location/Practitioner/
HealthcareService): the request body (genuine FHIR R4 Endpoint JSON) is
validated and stored whole in `content`, every response is FHIR R4
(`application/fhir+json`, regardless of Accept), and only the FHIR R4 search
parameters are indexed (https://www.hl7.org/fhir/R4/endpoint.html#search).

This file holds create, read, patch, delete, the existence checks other
resources now run against Endpoint, and auth (org-less token, missing scope,
cross-org isolation). Search lives in test_search.py.

R4's required elements (status, connectionType, payloadType, address) are only
enforced by the `java_validator` backend: the native structural check has no
cardinality minimums, so they are not asserted here.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.endpoint.support import (
    BASE,
    FULL,
    MINIMAL,
    ORG_BASE,
    create_endpoint,
    create_organization,
)

PERMS = [
    "endpoint:create",
    "endpoint:read",
    "endpoint:update",
    "endpoint:delete",
    "organization:create",
    "organization:read",
    "organization:update",
]


@pytest.fixture
def native_validation(monkeypatch):
    """The base R4 validator may be switched off in configs/config.yaml
    (`fhir_validation.enabled: false` skips it entirely). Tests that assert "a
    key that isn't FHIR is a 422" need it on: the project's own structural
    check (no sidecar needed)."""
    monkeypatch.setattr(settings.fhir_validation, "enabled", True)
    monkeypatch.setattr(settings.fhir_validation, "backend", "native")


def _ids(bundle: dict) -> set[int]:
    return {int(e["resource"]["id"]) for e in bundle.get("entry") or [] if e["search"]["mode"] == "match"}


def _as_user(sub="u-test", org_id="org-test", permissions=PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(sub=sub, org_id=org_id, permissions=permissions)


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "Endpoint"
    assert data["status"] == "active" and data["address"] == "https://fhir.example.org/r4"


async def test_create_full_round_trip(client):
    org = await create_organization(client)
    body = {**FULL, "managingOrganization": {"reference": f"Organization/{org}"}}
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")} == expected
    assert (await client.get(f"{BASE}/{data['id']}")).json() == data


async def test_create_keeps_elements_nothing_searches_on(client):
    data = (await client.post(BASE + "/", json=FULL)).json()
    assert data["payloadMimeType"] == ["application/fhir+json", "application/fhir+xml"]
    assert data["header"] == ["Authorization: Bearer abc"]
    assert data["contact"][0]["value"] == "it@example.org"
    assert data["period"]["start"].startswith("2026-01-01")


async def test_create_ignores_server_managed_id_and_meta(client):
    resp = await client.post(
        BASE + "/", json={**MINIMAL, "id": "999", "meta": {"lastUpdated": "2000-01-01T00:00:00Z"}}
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_non_fhir_key_rejected(client, native_validation):
    resp = await client.post(BASE + "/", json={**MINIMAL, "not_a_fhir_element": 1})
    assert resp.status_code == 422, resp.text


async def test_create_old_style_fields_rejected(client, native_validation):
    for stale in ({"org_id": "x"}, {"user_id": "u"}, {"payload_type": "x"}, {"connection_type": "x"}):
        resp = await client.post(BASE + "/", json={**MINIMAL, **stale})
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(BASE + "/", json={**MINIMAL, "resourceType": "Patient"})
    assert resp.status_code == 422, resp.text


async def test_create_bad_status_rejected(client):
    assert (await client.post(BASE + "/", json={**MINIMAL, "status": "broken"})).status_code == 422


async def test_every_status_code_is_accepted(client):
    for status in ("active", "suspended", "error", "off", "entered-in-error", "test"):
        resp = await client.post(BASE + "/", json={**MINIMAL, "status": status})
        assert resp.status_code == 201, (status, resp.text)
        assert resp.json()["status"] == status


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=MINIMAL)).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


async def test_create_managing_organization_must_exist(client):
    body = {**MINIMAL, "managingOrganization": {"reference": "Organization/999999"}}
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_identifier_assigner_must_exist(client):
    body = {**MINIMAL, "identifier": [{"value": "1", "assigner": {"reference": "Organization/999999"}}]}
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_absolute_and_logical_references_not_resolved(client):
    ref = "https://other.example.org/fhir/Organization/42"
    resp = await client.post(BASE + "/", json={**MINIMAL, "managingOrganization": {"reference": ref}})
    assert resp.status_code == 201, resp.text
    assert resp.json()["managingOrganization"]["reference"] == ref
    logical = {"identifier": {"system": "urn:registry", "value": "ORG-9"}}
    assert (await client.post(BASE + "/", json={**MINIMAL, "managingOrganization": logical})).status_code == 201


async def test_create_reference_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        other_org = await create_organization(other_client, "Other Tenant Org")
    finally:
        _as_user()
    body = {**MINIMAL, "managingOrganization": {"reference": f"Organization/{other_org}"}}
    assert (await client.post(BASE + "/", json=body)).status_code == 422


# ── Other resources now check that an Endpoint they point at exists ──────────


async def test_organization_endpoint_reference_must_exist(client):
    resp = await client.post(ORG_BASE + "/", json={"name": "Org", "endpoint": [{"reference": "Endpoint/999999"}]})
    assert resp.status_code == 422, resp.text


async def test_organization_endpoint_reference_resolves_to_a_real_endpoint(client):
    ep = await create_endpoint(client)
    resp = await client.post(ORG_BASE + "/", json={"name": "Org", "endpoint": [{"reference": f"Endpoint/{ep}"}]})
    assert resp.status_code == 201, resp.text


async def test_organization_endpoint_by_identifier_or_absolute_url_needs_no_endpoint(client):
    body = {
        "name": "Org",
        "endpoint": [
            {"identifier": {"system": "urn:ep", "value": "EP-9"}},
            {"reference": "https://other.example.org/fhir/Endpoint/9"},
        ],
    }
    assert (await client.post(ORG_BASE + "/", json=body)).status_code == 201


async def test_endpoint_in_another_org_cannot_be_referenced(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        other_ep = await create_endpoint(other_client)
    finally:
        _as_user()
    resp = await client.post(ORG_BASE + "/", json={"name": "Org", "endpoint": [{"reference": f"Endpoint/{other_ep}"}]})
    assert resp.status_code == 422, resp.text


# ── Read ─────────────────────────────────────────────────────────────────────


async def test_get_by_id(client):
    ep = await create_endpoint(client, FULL)
    resp = await client.get(f"{BASE}/{ep}")
    assert resp.status_code == 200 and resp.json()["id"] == str(ep)


async def test_get_is_fhir_regardless_of_accept(client):
    ep = await create_endpoint(client)
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{ep}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "Endpoint"


async def test_xml_only_accept_is_406(client):
    ep = await create_endpoint(client)
    resp = await client.get(f"{BASE}/{ep}", headers={"Accept": "application/fhir+xml"})
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_scalar_keeps_the_rest(client):
    ep = await create_endpoint(client, FULL)
    resp = await client.patch(f"{BASE}/{ep}", json={"status": "suspended", "name": "Renamed"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "suspended" and resp.json()["name"] == "Renamed"
    assert resp.json()["payloadMimeType"] == ["application/fhir+json", "application/fhir+xml"]
    assert resp.json()["address"] == "https://fhir.example.org/r4"  # required, untouched


async def test_patch_reindexes_search(client):
    ep = await create_endpoint(client, FULL)
    await client.patch(f"{BASE}/{ep}", json={"status": "off", "name": "Retired API"})
    assert ep not in _ids((await client.get(BASE + "/", params={"status": "active"})).json())
    assert ep in _ids((await client.get(BASE + "/", params={"status": "off"})).json())
    assert ep not in _ids((await client.get(BASE + "/", params={"name": "General"})).json())
    assert ep in _ids((await client.get(BASE + "/", params={"name": "Retired"})).json())


async def test_patch_connection_type_and_payload_type_reindex(client):
    ep = await create_endpoint(client, FULL)
    await client.patch(
        f"{BASE}/{ep}",
        json={"connectionType": {"code": "dicom-wado-rs"}, "payloadType": [{"coding": [{"code": "ccda"}]}]},
    )
    assert ep not in _ids((await client.get(BASE + "/", params={"connection-type": "hl7-fhir-rest"})).json())
    assert ep in _ids((await client.get(BASE + "/", params={"connection-type": "dicom-wado-rs"})).json())
    assert ep not in _ids((await client.get(BASE + "/", params={"payload-type": "any"})).json())
    assert ep in _ids((await client.get(BASE + "/", params={"payload-type": "ccda"})).json())


async def test_patch_replaces_list_wholesale_and_empty_clears(client):
    ep = await create_endpoint(client, FULL)
    resp = await client.patch(f"{BASE}/{ep}", json={"header": ["X-One: 1"]})
    assert resp.json()["header"] == ["X-One: 1"]
    resp = await client.patch(f"{BASE}/{ep}", json={"header": [], "contact": []})
    assert "header" not in resp.json() and "contact" not in resp.json()


async def test_patch_managing_organization_resolved_then_cleared(client):
    org = await create_organization(client)
    ep = await create_endpoint(client)
    await client.patch(f"{BASE}/{ep}", json={"managingOrganization": {"reference": f"Organization/{org}"}})
    assert ep in _ids((await client.get(BASE + "/", params={"organization": str(org)})).json())
    resp = await client.patch(f"{BASE}/{ep}", json={"managingOrganization": None})
    assert "managingOrganization" not in resp.json()
    assert ep not in _ids((await client.get(BASE + "/", params={"organization": str(org)})).json())


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client):
    ep = await create_endpoint(client, FULL)
    resp = await client.patch(f"{BASE}/{ep}", json={"managingOrganization": {"reference": "Organization/999999"}})
    assert resp.status_code == 422
    assert "managingOrganization" not in (await client.get(f"{BASE}/{ep}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    ep = await create_endpoint(client, FULL)
    assert (await client.patch(f"{BASE}/{ep}", json={"status": "broken"})).status_code == 422
    assert (await client.get(f"{BASE}/{ep}")).json()["status"] == "active"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "off"})
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete(client):
    ep = await create_endpoint(client, FULL)
    assert (await client.delete(f"{BASE}/{ep}")).status_code == 204
    assert (await client.get(f"{BASE}/{ep}")).status_code == 404
    # Its index rows are gone with it.
    assert ep not in _ids((await client.get(BASE + "/", params={"name": "General"})).json())
    assert ep not in _ids((await client.get(BASE + "/", params={"payload-type": "any"})).json())


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_create_without_permission(client):
    _as_user(permissions=["endpoint:read"])
    assert (await client.post(BASE + "/", json=MINIMAL)).status_code == 403


async def test_org_less_token_rejected(client):
    ep = await create_endpoint(client)

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=MINIMAL)).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{ep}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    ep = await create_endpoint(client)
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{ep}"),
            await other_client.patch(f"{BASE}/{ep}", json={"status": "off"}),
            await other_client.delete(f"{BASE}/{ep}"),
        ):
            assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_endpoint(client, {**MINIMAL, "name": "TenantAOnly API"})
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (await other_client.get(BASE + "/", params={"name": "TenantAOnly"})).json()
        assert bundle["total"] == 0 and "entry" not in bundle
    finally:
        _as_user()
