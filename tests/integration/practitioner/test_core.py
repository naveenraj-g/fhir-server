"""Core practitioner endpoint coverage.

Practitioner is stored Medplum-style (like Organization/Location): the
request body (genuine FHIR R4 Practitioner JSON) is validated and stored
whole in `content`, every response is FHIR R4 (`application/fhir+json`,
regardless of Accept), and only the FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/practitioner.html#search). Unlike Organization
it keeps an end-user scope (`user_id`, carried as the user-id extension) and
a `/me` route — see PractitionerModel's docstring.

This file holds create, read, patch, delete, `/me`, the user-id rules and
auth (org-less token, missing scope, cross-org isolation). Search lives in
test_search.py.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_fhir_practitioner, assert_operation_outcome
from tests.integration.practitioner.support import (
    BASE,
    FULL,
    MINIMAL,
    USER_ID_EXT,
    create_practitioner,
)

PRACTITIONER_PERMS = [
    "practitioner:create",
    "practitioner:read",
    "practitioner:update",
    "practitioner:delete",
]


@pytest.fixture
def native_validation(monkeypatch):
    """configs/config.yaml ships with fhir_validation.enabled=false, which
    skips base R4 validation entirely. Tests that assert "a key that isn't
    FHIR is a 422" need the validator on: the project's own structural
    check (no sidecar needed)."""
    monkeypatch.setattr(settings.fhir_validation, "enabled", True)
    monkeypatch.setattr(settings.fhir_validation, "backend", "native")


def _ids(bundle: dict) -> set[int]:
    return {int(e["resource"]["id"]) for e in bundle.get("entry") or []}


def _as_user(sub="u-test", org_id="org-test", permissions=PRACTITIONER_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_practitioner_minimal(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert_fhir_practitioner(data, active=True)
    assert data["name"][0]["family"] == "Careful"


async def test_create_full_round_trip(client):
    resp = await client.post(BASE + "/", json=FULL)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    expected = {k: v for k, v in FULL.items() if k != "resourceType"}
    assert {k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")} == expected
    got = await client.get(f"{BASE}/{data['id']}")
    assert got.status_code == 200
    assert got.json() == data


async def test_create_keeps_elements_nothing_searches_on(client):
    """Photo and qualification have no search parameter — they live only in
    `content`, and must still round-trip."""
    data = (await client.post(BASE + "/", json=FULL)).json()
    assert data["photo"][0]["url"] == "https://fhir-server.dev/fhir/assets/photo.png"
    assert data["qualification"][0]["code"]["text"] == "Bachelor of Science"


async def test_create_ignores_server_managed_id_and_meta(client):
    resp = await client.post(
        BASE + "/", json={**MINIMAL, "id": "999", "meta": {"lastUpdated": "2000-01-01T00:00:00Z"}}
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["id"] != "999"
    assert not data["meta"]["lastUpdated"].startswith("2000")


async def test_create_non_fhir_key_rejected(client, native_validation):
    resp = await client.post(BASE + "/", json={**MINIMAL, "not_a_fhir_element": 1})
    assert resp.status_code == 422, resp.text


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in ({"birth_date": "1980-05-15"}, {"user_id": "u1"}, {"org_id": "x"}):
        resp = await client.post(BASE + "/", json={**MINIMAL, **stale})
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(BASE + "/", json={**MINIMAL, "resourceType": "Patient"})
    assert resp.status_code == 422, resp.text


async def test_create_bad_gender_rejected(client):
    resp = await client.post(BASE + "/", json={**MINIMAL, "gender": "robot"})
    assert resp.status_code == 422, resp.text


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=MINIMAL)).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


async def test_create_qualification_issuer_must_exist(client):
    body = {
        **MINIMAL,
        "qualification": [{"code": {"text": "MD"}, "issuer": {"reference": "Organization/999999"}}],
    }
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 422, resp.text


async def test_create_qualification_issuer_resolves(client):
    org = await client.post("/api/fhir/v1/organizations/", json={"name": "Issuer Org"})
    if org.status_code != 201:  # organization routes not mounted in this config
        return
    body = {
        **MINIMAL,
        "qualification": [
            {"code": {"text": "MD"}, "issuer": {"reference": f"Organization/{org.json()['id']}"}}
        ],
    }
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_absolute_issuer_reference_stored_not_resolved(client):
    ref = "https://other.example.org/fhir/Organization/42"
    body = {**MINIMAL, "qualification": [{"code": {"text": "MD"}, "issuer": {"reference": ref}}]}
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["qualification"][0]["issuer"]["reference"] == ref


# ── Read ─────────────────────────────────────────────────────────────────────


async def test_get_practitioner_by_id(client):
    pid = await create_practitioner(client, FULL)
    resp = await client.get(f"{BASE}/{pid}")
    assert resp.status_code == 200
    assert_fhir_practitioner(resp.json(), id=str(pid))


async def test_get_practitioner_is_fhir_regardless_of_accept(client):
    pid = await create_practitioner(client)
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{pid}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "Practitioner"


async def test_xml_only_accept_is_406(client):
    pid = await create_practitioner(client)
    resp = await client.get(f"{BASE}/{pid}", headers={"Accept": "application/fhir+xml"})
    assert resp.status_code == 406
    assert resp.json()["resourceType"] == "OperationOutcome"


async def test_get_practitioner_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_practitioner_scalar(client):
    pid = await create_practitioner(client, FULL)
    resp = await client.patch(f"{BASE}/{pid}", json={"active": False, "gender": "female"})
    assert resp.status_code == 200, resp.text
    assert_fhir_practitioner(resp.json(), active=False, gender="female")
    # Untouched elements survive.
    assert resp.json()["name"][0]["family"] == "Careful"


async def test_patch_reindexes_search(client):
    pid = await create_practitioner(client, FULL)
    await client.patch(f"{BASE}/{pid}", json={"name": [{"family": "Renamed"}]})
    old = await client.get(BASE + "/", params={"family": "Careful"})
    new = await client.get(BASE + "/", params={"family": "Renamed"})
    assert pid not in _ids(old.json())
    assert pid in _ids(new.json())


async def test_patch_replaces_list_wholesale_and_empty_clears(client):
    pid = await create_practitioner(client, FULL)
    resp = await client.patch(f"{BASE}/{pid}", json={"telecom": [{"system": "phone", "value": "111"}]})
    assert [t["value"] for t in resp.json()["telecom"]] == ["111"]
    resp = await client.patch(f"{BASE}/{pid}", json={"telecom": []})
    assert "telecom" not in resp.json()
    assert pid not in _ids((await client.get(BASE + "/", params={"phone": "111"})).json())


async def test_patch_photo_and_qualification_persist(client):
    pid = await create_practitioner(client, FULL)
    resp = await client.patch(
        f"{BASE}/{pid}", json={"qualification": [{"code": {"text": "MD"}}]}
    )
    assert resp.json()["qualification"][0]["code"]["text"] == "MD"
    assert resp.json()["photo"][0]["url"].endswith("photo.png")


async def test_patch_practitioner_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"active": False})
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    pid = await create_practitioner(client, FULL)
    resp = await client.patch(f"{BASE}/{pid}", json={"gender": "robot"})
    assert resp.status_code == 422
    assert (await client.get(f"{BASE}/{pid}")).json()["gender"] == "male"


# ── user_id (the user-id extension) ──────────────────────────────────────────


async def test_user_id_cannot_be_changed(client):
    pid = await create_practitioner(client, FULL)
    resp = await client.patch(
        f"{BASE}/{pid}", json={"extension": [{"url": USER_ID_EXT, "valueString": "someone-else"}]}
    )
    assert resp.status_code == 422, resp.text
    assert (await client.get(f"{BASE}/{pid}")).json()["extension"][0]["valueString"] == "end-user-1"


async def test_user_id_cannot_be_dropped_or_added_later(client):
    owned = await create_practitioner(client, FULL)
    assert (await client.patch(f"{BASE}/{owned}", json={"extension": []})).status_code == 422
    free = await create_practitioner(client)
    resp = await client.patch(
        f"{BASE}/{free}", json={"extension": [{"url": USER_ID_EXT, "valueString": "late"}]}
    )
    assert resp.status_code == 422


async def test_patch_leaving_extension_alone_keeps_user_id(client):
    owned = {**FULL, "extension": [{"url": USER_ID_EXT, "valueString": "u-test"}]}
    pid = await create_practitioner(client, owned)
    assert (await client.patch(f"{BASE}/{pid}", json={"active": False})).status_code == 200
    # Still the end-user's own record (and still indexed as such) after the patch.
    assert pid in _ids((await client.get(BASE + "/me")).json())


# ── /me ──────────────────────────────────────────────────────────────────────


async def test_me_returns_only_the_end_users_own_records(client):
    mine = await create_practitioner(
        client, {**MINIMAL, "extension": [{"url": USER_ID_EXT, "valueString": "u-test"}]}
    )
    await create_practitioner(
        client, {**MINIMAL, "extension": [{"url": USER_ID_EXT, "valueString": "someone-else"}]}
    )
    await create_practitioner(client)  # no owner at all
    resp = await client.get(BASE + "/me")
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {mine}
    assert resp.json()["total"] == 1


async def test_me_supports_search_parameters(client):
    ext = [{"url": USER_ID_EXT, "valueString": "u-test"}]
    a = await create_practitioner(client, {"extension": ext, "name": [{"family": "Alpha"}]})
    await create_practitioner(client, {"extension": ext, "name": [{"family": "Beta"}]})
    resp = await client.get(BASE + "/me", params={"family": "Alpha"})
    assert _ids(resp.json()) == {a}
    assert resp.json()["link"][0]["url"].split("?")[0].endswith("/practitioners/me")


async def test_me_is_not_shadowed_by_the_id_route(client):
    resp = await client.get(BASE + "/me")
    assert resp.status_code == 200
    assert resp.json()["resourceType"] == "Bundle"


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete_practitioner(client):
    pid = await create_practitioner(client, FULL)
    assert (await client.delete(f"{BASE}/{pid}")).status_code == 204
    assert (await client.get(f"{BASE}/{pid}")).status_code == 404
    # Its index rows are gone with it.
    assert pid not in _ids((await client.get(BASE + "/", params={"family": "Careful"})).json())


async def test_delete_practitioner_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_create_practitioner_no_permission(client):
    _as_user(permissions=["practitioner:read"])
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 403


async def test_org_less_token_rejected(client):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=PRACTITIONER_PERMS)
    pid = await create_practitioner(client)

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": PRACTITIONER_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=MINIMAL)).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{pid}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()
    pid = await create_practitioner(client)
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{pid}"),
            await other_client.patch(f"{BASE}/{pid}", json={"active": False}),
            await other_client.delete(f"{BASE}/{pid}"),
        ):
            assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_practitioner(client, {"name": [{"family": "TenantAOnly"}]})
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (await other_client.get(BASE + "/", params={"family": "TenantAOnly"})).json()
        assert bundle["total"] == 0
        assert "entry" not in bundle
    finally:
        _as_user()
