"""Core organization endpoint coverage.

Organization is stored Medplum-style: the request body (genuine FHIR R4
Organization JSON) is validated and stored whole in `content`, every
response is FHIR R4 (`application/fhir+json`, regardless of Accept), and
only the FHIR R4 search parameters are indexed into columns/tables
(https://www.hl7.org/fhir/R4/organization.html#search).

This file holds:
- create (minimal, full, validation, server-managed fields)
- read (round trip, not found)
- (search lives in test_search.py)
- patch (merge-patch semantics, partOf hierarchy business rule, not found)
- delete
- auth: org-less token, missing permission scope, cross-org isolation
"""

import json
from pathlib import Path

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import (
    assert_fhir_organization,
    assert_operation_outcome,
)
from tests.integration.organization.support import BASE, FULL, MINIMAL, create_organization

ORG_PERMS = [
    "organization:create",
    "organization:read",
    "organization:update",
    "organization:delete",
]

_EXT = "https://fhir-server.dev/fhir/StructureDefinition"


def _meta_ext(org: dict, name: str):
    for ext in (org.get("meta") or {}).get("extension") or []:
        if ext["url"] == f"{_EXT}/{name}":
            return ext.get("valueString") or ext.get("valueDateTime")
    return None


def _ids(bundle: dict) -> set[int]:
    return {int(e["resource"]["id"]) for e in bundle.get("entry") or []}


def _load_fixture(name: str) -> dict:
    return json.loads((Path(__file__).parent / "fixtures" / name).read_text())


def _content(org: dict) -> dict:
    return {k: v for k, v in org.items() if k not in ("resourceType", "id", "meta")}


async def _search(client, **params) -> dict:
    resp = await client.get(BASE + "/", params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_organization_minimal(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 201
    assert "application/fhir+json" in resp.headers["content-type"]
    assert_fhir_organization(resp.json(), name="Test Hospital", active=True)


async def test_create_full_round_trip(client):
    resp = await client.post(BASE + "/", json=FULL)
    assert resp.status_code == 201, resp.text
    org = resp.json()
    assert org["resourceType"] == "Organization"
    expected = {k: v for k, v in FULL.items() if k != "resourceType"}
    assert _content(org) == expected


async def test_create_full_r4_payload_stored_as_sent(client):
    """A complete R4 Organization — including elements no search parameter
    uses (contact, telecom, periods, `assigner.type`, ...) — is stored and
    served back exactly as sent."""
    body = _load_fixture("r4_full_organization.json")
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    org = resp.json()
    assert _content(org) == {k: v for k, v in body.items() if k != "resourceType"}

    got = await client.get(f"{BASE}/{org['id']}")
    assert _content(got.json()) == _content(org)


async def test_create_ignores_server_managed_id_and_meta(client):
    resp = await client.post(
        BASE + "/", json={**MINIMAL, "id": "999", "meta": {"versionId": "7"}}
    )
    assert resp.status_code == 201, resp.text
    org = resp.json()
    assert org["id"] != "999"
    assert "versionId" not in org["meta"]


async def test_create_organization_extra_field_rejected(client):
    resp = await client.post(BASE + "/", json={**MINIMAL, "nonexistent_field": "value"})
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_organization_org_id_in_body_rejected(client):
    """org_id/created_by/updated_by come from the verified token — not
    request-body fields. `org_id` isn't FHIR, so R4 validation rejects it."""
    resp = await client.post(BASE + "/", json={**MINIMAL, "org_id": "sneaky-org"})
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_old_flat_fields_rejected(client):
    for body in (
        {**MINIMAL, "partof": "Organization/1"},
        {**MINIMAL, "address": [{"postal_code": "12345"}]},
        {**MINIMAL, "contact": [{"name_family": "Smith"}]},
        {**MINIMAL, "identifier": [{"value": "1", "period_start": "2024-01-01T00:00:00Z"}]},
    ):
        resp = await client.post(BASE + "/", json=body)
        assert resp.status_code == 422, body


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(BASE + "/", json={**MINIMAL, "resourceType": "Patient"})
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_organization_audit_meta_from_actor(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 201
    org = resp.json()
    assert _meta_ext(org, "created-by") == "u-test"
    assert _meta_ext(org, "org-id") == "org-test"
    assert org["meta"]["lastUpdated"]


async def test_create_organization_with_partof(client):
    parent_id = await create_organization(client, {**MINIMAL, "name": "Parent Org"})
    resp = await client.post(
        BASE + "/",
        json={**MINIMAL, "name": "Child Org", "partOf": {"reference": f"Organization/{parent_id}"}},
    )
    assert resp.status_code == 201
    assert resp.json()["partOf"] == {"reference": f"Organization/{parent_id}"}


async def test_create_organization_nonexistent_partof_rejected(client):
    resp = await client.post(
        BASE + "/", json={**MINIMAL, "partOf": {"reference": "Organization/9999999"}}
    )
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_nonexistent_identifier_assigner_rejected(client):
    resp = await client.post(
        BASE + "/",
        json={
            **MINIMAL,
            "identifier": [{"value": "1", "assigner": {"reference": "Organization/9999999"}}],
        },
    )
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_create_absolute_partof_reference_stored_not_resolved(client):
    """An absolute URL can't resolve to a local row — it's kept in content
    as sent, with nothing indexed for `partof`."""
    ref = {"reference": "https://other.example/fhir/Organization/42"}
    resp = await client.post(BASE + "/", json={**MINIMAL, "partOf": ref})
    assert resp.status_code == 201, resp.text
    assert resp.json()["partOf"] == ref


# ── Get ──────────────────────────────────────────────────────────────────────


async def test_get_organization_by_id(client):
    org_id = await create_organization(client)
    resp = await client.get(f"{BASE}/{org_id}")
    assert resp.status_code == 200
    assert "application/fhir+json" in resp.headers["content-type"]
    assert_fhir_organization(resp.json(), name="Test Hospital")
    assert resp.json()["id"] == str(org_id)


async def test_get_organization_is_fhir_regardless_of_accept(client):
    org_id = await create_organization(client)
    resp = await client.get(f"{BASE}/{org_id}", headers={"Accept": "application/json"})
    assert resp.status_code == 200
    assert resp.json()["resourceType"] == "Organization"


async def test_get_organization_not_found(client):
    resp = await client.get(f"{BASE}/9999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_organization_name(client):
    org_id = await create_organization(client)
    resp = await client.patch(f"{BASE}/{org_id}", json={"name": "Updated Hospital"})
    assert resp.status_code == 200
    org = resp.json()
    assert org["name"] == "Updated Hospital"
    assert _meta_ext(org, "updated-by") == "u-test"


async def test_patch_reindexes_search_columns(client):
    org_id = await create_organization(client, {**MINIMAL, "name": "Old Name"})
    await client.patch(f"{BASE}/{org_id}", json={"name": "Brand New Name"})
    assert org_id in _ids(await _search(client, name="Brand New"))
    assert org_id not in _ids(await _search(client, name="Old Name"))
    assert org_id in _ids(await _search(client, phonetic="Brand"))


async def test_patch_organization_active(client):
    org_id = await create_organization(client)
    resp = await client.patch(f"{BASE}/{org_id}", json={"active": False})
    assert resp.status_code == 200
    assert resp.json()["active"] is False


async def test_patch_replaces_only_supplied_elements(client):
    org_id = await create_organization(client, FULL)
    resp = await client.patch(f"{BASE}/{org_id}", json={"alias": ["New Alias"]})
    assert resp.status_code == 200
    org = resp.json()
    assert org["alias"] == ["New Alias"]
    for element in ("identifier", "type", "telecom", "address", "contact", "endpoint"):
        assert org[element] == FULL[element], element
    assert org_id in _ids(await _search(client, name="New Alias"))
    assert org_id not in _ids(await _search(client, name="Gen Hosp"))


async def test_patch_replaces_list_and_reindexes(client):
    org_id = await create_organization(client, FULL)
    new_identifier = [{"system": "urn:x", "value": "NEW-1"}]
    resp = await client.patch(f"{BASE}/{org_id}", json={"identifier": new_identifier})
    assert resp.status_code == 200, resp.text
    assert resp.json()["identifier"] == new_identifier
    assert _ids(await _search(client, identifier="urn:x|NEW-1")) == {org_id}
    assert org_id not in _ids(await _search(client, identifier="1234567893"))


async def test_patch_empty_list_clears(client):
    org_id = await create_organization(client, FULL)
    resp = await client.patch(f"{BASE}/{org_id}", json={"telecom": [], "address": []})
    assert resp.status_code == 200, resp.text
    org = resp.json()
    assert "telecom" not in org
    assert "address" not in org
    assert org["contact"] == FULL["contact"]
    assert org_id not in _ids(await _search(client, **{"address-city": "Anytown"}))


async def test_patch_partof_resolved(client):
    parent_id = await create_organization(client, {**MINIMAL, "name": "Parent Org"})
    child_id = await create_organization(client, {**MINIMAL, "name": "Child Org"})
    resp = await client.patch(
        f"{BASE}/{child_id}", json={"partOf": {"reference": f"Organization/{parent_id}"}}
    )
    assert resp.status_code == 200
    assert _ids(await _search(client, partof=f"Organization/{parent_id}")) == {child_id}


async def test_patch_partof_null_clears(client):
    parent_id = await create_organization(client, {**MINIMAL, "name": "Parent Org"})
    child_id = await create_organization(
        client,
        {**MINIMAL, "name": "Child Org", "partOf": {"reference": f"Organization/{parent_id}"}},
    )
    resp = await client.patch(f"{BASE}/{child_id}", json={"partOf": None})
    assert resp.status_code == 200, resp.text
    assert "partOf" not in resp.json()
    assert child_id not in _ids(await _search(client, partof=f"Organization/{parent_id}"))


async def test_patch_organization_partof_cycle_rejected(client):
    parent_id = await create_organization(client, {**MINIMAL, "name": "Parent Org"})
    child_id = await create_organization(
        client,
        {**MINIMAL, "name": "Child Org", "partOf": {"reference": f"Organization/{parent_id}"}},
    )
    resp = await client.patch(
        f"{BASE}/{parent_id}", json={"partOf": {"reference": f"Organization/{child_id}"}}
    )
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_patch_organization_partof_self_reference_rejected(client):
    org_id = await create_organization(client)
    resp = await client.patch(
        f"{BASE}/{org_id}", json={"partOf": {"reference": f"Organization/{org_id}"}}
    )
    assert_operation_outcome(resp.json(), expected_status=422, response_status=resp.status_code)


async def test_patch_keeps_reference_type(client):
    parent_id = await create_organization(client, {**MINIMAL, "name": "Parent Org"})
    child_id = await create_organization(client, {**MINIMAL, "name": "Child Org"})
    part_of = {"reference": f"Organization/{parent_id}", "type": "Organization"}
    resp = await client.patch(f"{BASE}/{child_id}", json={"partOf": part_of})
    assert resp.status_code == 200, resp.text
    assert resp.json()["partOf"] == part_of


async def test_patch_extension_null_clears(client):
    ext = [{"url": "https://fhir-server.dev/fhir/StructureDefinition/x", "valueString": "y"}]
    org_id = await create_organization(client, {**MINIMAL, "extension": ext})
    resp = await client.patch(f"{BASE}/{org_id}", json={"extension": None})
    assert resp.status_code == 200, resp.text
    assert "extension" not in resp.json()


async def test_patch_organization_not_found(client):
    resp = await client.patch(f"{BASE}/9999999", json={"name": "X"})
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete_organization(client):
    org_id = await create_organization(client, FULL)
    resp = await client.delete(f"{BASE}/{org_id}")
    assert resp.status_code == 204
    assert (await client.get(f"{BASE}/{org_id}")).status_code == 404
    assert org_id not in _ids(await _search(client, identifier="1234567893"))


async def test_delete_organization_not_found(client):
    resp = await client.delete(f"{BASE}/9999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Auth & tenancy ───────────────────────────────────────────────────────────


async def test_create_organization_no_permission(client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=["organization:read"])
    try:
        resp = await client.post(BASE + "/", json=MINIMAL)
        assert_operation_outcome(resp.json(), expected_status=403, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_PERMS)


async def test_create_organization_org_less_token_rejected(client):
    app.dependency_overrides[get_current_user] = make_test_user(org_id=None, permissions=ORG_PERMS)
    try:
        resp = await client.post(BASE + "/", json=MINIMAL)
        assert resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_PERMS)


async def test_list_organizations_org_less_token_rejected(client):
    app.dependency_overrides[get_current_user] = make_test_user(org_id=None, permissions=ORG_PERMS)
    try:
        resp = await client.get(BASE + "/")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_PERMS)


async def test_get_organization_org_mismatch_returns_404(client, other_client):
    # Requesting other_client overwrote the get_current_user override with its
    # own (patient-scoped) default identity — restore org-test's organization
    # permissions before creating, then switch to org-other before the read.
    app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_PERMS)
    org_id = await create_organization(client)
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=ORG_PERMS
    )
    try:
        resp = await other_client.get(f"{BASE}/{org_id}")
        assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_PERMS)


async def test_patch_organization_org_mismatch_returns_404(client, other_client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_PERMS)
    org_id = await create_organization(client)
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=ORG_PERMS
    )
    try:
        resp = await other_client.patch(f"{BASE}/{org_id}", json={"name": "Hacked"})
        assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_PERMS)


async def test_delete_organization_org_mismatch_returns_404(client, other_client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_PERMS)
    org_id = await create_organization(client)
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=ORG_PERMS
    )
    try:
        resp = await other_client.delete(f"{BASE}/{org_id}")
        assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_PERMS)


async def test_list_organizations_cross_tenant_isolation(client, other_client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_PERMS)
    await create_organization(client, {**MINIMAL, "name": "Tenant-A-Only-Org"})
    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other", org_id="org-other", permissions=ORG_PERMS
    )
    try:
        bundle = await _search(other_client, name="Tenant-A-Only-Org")
        assert bundle["total"] == 0
        assert "entry" not in bundle
    finally:
        app.dependency_overrides[get_current_user] = make_test_user(permissions=ORG_PERMS)


# ── Content type: always FHIR JSON; 406 only when JSON is ruled out ──────────


async def test_any_json_compatible_accept_gets_fhir_json(client):
    org_id = await create_organization(client)
    for accept in (
        None,
        "application/fhir+json",
        "application/json",
        "*/*",
        "text/html, application/xhtml+xml, */*;q=0.8",
        "application/fhir+json; fhirVersion=4.0",
        "application/fhir+xml, application/json;q=0.5",
    ):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{org_id}", headers=headers)
        assert resp.status_code == 200, (accept, resp.text)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "Organization"


async def test_xml_only_accept_is_406(client):
    org_id = await create_organization(client)
    for accept in ("application/fhir+xml", "application/xml, text/xml", "application/json;q=0"):
        resp = await client.get(f"{BASE}/{org_id}", headers={"Accept": accept})
        assert resp.status_code == 406, (accept, resp.text)
        body = resp.json()
        assert body["resourceType"] == "OperationOutcome"
        assert body["issue"][0]["code"] == "not-supported"
    # Search too, not just read.
    assert (await client.get(BASE + "/", headers={"Accept": "application/fhir+xml"})).status_code == 406


async def test_format_overrides_accept(client):
    org_id = await create_organization(client)
    xml = await client.get(f"{BASE}/{org_id}", params={"_format": "xml"})
    assert xml.status_code == 406
    ok = await client.get(
        f"{BASE}/{org_id}", params={"_format": "json"}, headers={"Accept": "application/fhir+xml"}
    )
    assert ok.status_code == 200
    assert ok.headers["content-type"].startswith("application/fhir+json")
