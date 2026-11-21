"""Core practitioner endpoint coverage.

Practitioner is stored Medplum-style (like Organization/Location): the
request body (genuine FHIR R4 Practitioner JSON) is validated and stored
whole in `content`, every response is FHIR R4 (`application/fhir+json`,
regardless of Accept), and only the FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/practitioner.html#search). Unlike Organization
it can be linked to an end-user (`user_id`, set by `PUT /{id}/user`, not part
of the FHIR resource) and has a `/me` route — see PractitionerModel's docstring.

This file holds create, read, patch, delete, the end-user link, `/me` and
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
    create_practitioner,
    link_user,
)

PRACTITIONER_PERMS = [
    "practitioner:create",
    "practitioner:read",
    "practitioner:update",
    "practitioner:delete",
    "practitioner:link",
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
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected
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
        BASE + "/",
        json={**MINIMAL, "id": "999", "meta": {"lastUpdated": "2000-01-01T00:00:00Z"}},
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
        "qualification": [
            {"code": {"text": "MD"}, "issuer": {"reference": "Organization/999999"}}
        ],
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
            {
                "code": {"text": "MD"},
                "issuer": {"reference": f"Organization/{org.json()['id']}"},
            }
        ],
    }
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_absolute_issuer_reference_stored_not_resolved(client):
    ref = "https://other.example.org/fhir/Organization/42"
    body = {
        **MINIMAL,
        "qualification": [{"code": {"text": "MD"}, "issuer": {"reference": ref}}],
    }
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
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_practitioner_scalar(client):
    pid = await create_practitioner(client, FULL)
    resp = await client.patch(
        f"{BASE}/{pid}", json={"active": False, "gender": "female"}
    )
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
    resp = await client.patch(
        f"{BASE}/{pid}", json={"telecom": [{"system": "phone", "value": "111"}]}
    )
    assert [t["value"] for t in resp.json()["telecom"]] == ["111"]
    resp = await client.patch(f"{BASE}/{pid}", json={"telecom": []})
    assert "telecom" not in resp.json()
    assert pid not in _ids(
        (await client.get(BASE + "/", params={"phone": "111"})).json()
    )


async def test_patch_photo_and_qualification_persist(client):
    pid = await create_practitioner(client, FULL)
    resp = await client.patch(
        f"{BASE}/{pid}", json={"qualification": [{"code": {"text": "MD"}}]}
    )
    assert resp.json()["qualification"][0]["code"]["text"] == "MD"
    assert resp.json()["photo"][0]["url"].endswith("photo.png")


async def test_patch_practitioner_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"active": False})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    pid = await create_practitioner(client, FULL)
    resp = await client.patch(f"{BASE}/{pid}", json={"gender": "robot"})
    assert resp.status_code == 422
    assert (await client.get(f"{BASE}/{pid}")).json()["gender"] == "male"


# ── End-user link (user_id) ──────────────────────────────────────────────────
# user_id is not a FHIR element: it is set by PUT /{id}/user, never by
# create/patch, and never appears in the resource.


async def test_create_starts_unlinked(client):
    pid = await create_practitioner(client, FULL)
    resp = await client.get(f"{BASE}/{pid}/user")
    assert resp.status_code == 200
    assert resp.json() == {"practitioner_id": pid, "user_id": None}


async def test_link_get_and_unlink(client):
    pid = await create_practitioner(client)
    linked = await link_user(client, pid, "user-abc")
    assert linked.status_code == 200, linked.text
    assert linked.json() == {"practitioner_id": pid, "user_id": "user-abc"}
    assert (await client.get(f"{BASE}/{pid}/user")).json()["user_id"] == "user-abc"
    assert (await client.delete(f"{BASE}/{pid}/user")).status_code == 204
    assert (await client.get(f"{BASE}/{pid}/user")).json()["user_id"] is None
    # Idempotent.
    assert (await client.delete(f"{BASE}/{pid}/user")).status_code == 204


async def test_link_is_not_part_of_the_resource(client):
    pid = await create_practitioner(client, FULL)
    await link_user(client, pid, "user-abc")
    body = (await client.get(f"{BASE}/{pid}")).json()
    assert "user-abc" not in str(body)
    assert "extension" not in body


async def test_relinking_replaces_the_user_and_same_user_is_a_noop(client):
    pid = await create_practitioner(client)
    await link_user(client, pid, "first")
    assert (await link_user(client, pid, "first")).status_code == 200
    assert (await link_user(client, pid, "second")).json()["user_id"] == "second"


async def test_a_user_can_act_as_only_one_practitioner_per_org(client):
    a = await create_practitioner(client)
    b = await create_practitioner(client)
    assert (await link_user(client, a, "same-user")).status_code == 200
    resp = await link_user(client, b, "same-user")
    assert resp.status_code == 422, resp.text
    # Unlinking the first frees the user.
    await client.delete(f"{BASE}/{a}/user")
    assert (await link_user(client, b, "same-user")).status_code == 200


async def test_link_needs_its_own_permission(client):
    pid = await create_practitioner(client)
    _as_user(permissions=[p for p in PRACTITIONER_PERMS if p != "practitioner:link"])
    assert (await link_user(client, pid)).status_code == 403
    assert (await client.delete(f"{BASE}/{pid}/user")).status_code == 403
    assert (
        await client.get(f"{BASE}/{pid}/user")
    ).status_code == 200  # read is enough to look


async def test_link_rejects_empty_or_unknown_fields(client):
    pid = await create_practitioner(client)
    assert (
        await client.put(f"{BASE}/{pid}/user", json={"user_id": ""})
    ).status_code == 422
    assert (await client.put(f"{BASE}/{pid}/user", json={})).status_code == 422
    assert (
        await client.put(f"{BASE}/{pid}/user", json={"user_id": "u", "x": 1})
    ).status_code == 422


async def test_link_not_found(client):
    for resp in (
        await link_user(client, 999999),
        await client.delete(f"{BASE}/999999/user"),
    ):
        assert_operation_outcome(
            resp.json(), expected_status=404, response_status=resp.status_code
        )


async def test_link_cross_org_returns_404(client, other_client):
    _as_user()
    pid = await create_practitioner(client)
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await link_user(other_client, pid),
            await other_client.delete(f"{BASE}/{pid}/user"),
            await other_client.get(f"{BASE}/{pid}/user"),
        ):
            assert resp.status_code == 404, resp.text
    finally:
        _as_user()


async def test_the_same_user_can_be_linked_in_different_orgs(client, other_client):
    _as_user()
    mine = await create_practitioner(client)
    assert (await link_user(client, mine, "shared-user")).status_code == 200
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_practitioner(other_client)
        assert (await link_user(other_client, theirs, "shared-user")).status_code == 200
    finally:
        _as_user()


async def test_patch_cannot_set_the_link_through_an_extension(client):
    """An extension named like the old user-id one is just an extension now;
    it does not link anything."""
    pid = await create_practitioner(client)
    ext = [
        {
            "url": "https://fhir-server.dev/fhir/StructureDefinition/user-id",
            "valueString": "u-test",
        }
    ]
    assert (
        await client.patch(f"{BASE}/{pid}", json={"extension": ext})
    ).status_code == 200
    assert (await client.get(f"{BASE}/{pid}/user")).json()["user_id"] is None
    assert pid not in _ids((await client.get(BASE + "/me")).json())


async def test_patch_and_delete_leave_the_link_alone(client):
    pid = await create_practitioner(client, FULL)
    await link_user(client, pid, "user-abc")
    await client.patch(
        f"{BASE}/{pid}", json={"active": False, "name": [{"family": "Renamed"}]}
    )
    assert (await client.get(f"{BASE}/{pid}/user")).json()["user_id"] == "user-abc"


# ── /me ──────────────────────────────────────────────────────────────────────


async def test_me_returns_only_records_linked_to_the_caller(client):
    mine = await create_practitioner(client)
    await link_user(client, mine, "u-test")  # u-test is the caller's `sub`
    other = await create_practitioner(client)
    await link_user(client, other, "someone-else")
    await create_practitioner(client)  # never linked
    resp = await client.get(BASE + "/me")
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {mine}
    assert resp.json()["total"] == 1


async def test_me_follows_the_link(client):
    pid = await create_practitioner(client)
    assert _ids((await client.get(BASE + "/me")).json()) == set()
    await link_user(client, pid, "u-test")
    assert _ids((await client.get(BASE + "/me")).json()) == {pid}
    await client.delete(f"{BASE}/{pid}/user")
    assert _ids((await client.get(BASE + "/me")).json()) == set()


async def test_me_supports_search_parameters(client):
    a = await create_practitioner(client, {"name": [{"family": "Alpha"}]})
    await link_user(client, a, "u-test")
    resp = await client.get(BASE + "/me", params={"family": "Beta"})
    assert _ids(resp.json()) == set()
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
    assert pid not in _ids(
        (await client.get(BASE + "/", params={"family": "Careful"})).json()
    )


async def test_delete_practitioner_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_create_practitioner_no_permission(client):
    _as_user(permissions=["practitioner:read"])
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 403


async def test_org_less_token_rejected(client):
    app.dependency_overrides[get_current_user] = make_test_user(
        permissions=PRACTITIONER_PERMS
    )
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
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_practitioner(client, {"name": [{"family": "TenantAOnly"}]})
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"family": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
        assert "entry" not in bundle
    finally:
        _as_user()
