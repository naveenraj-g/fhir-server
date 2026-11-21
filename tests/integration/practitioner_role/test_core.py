"""Core practitioner-role endpoint coverage.

PractitionerRole is stored Medplum-style (like Organization/Location/
Practitioner/HealthcareService/Endpoint): the request body (genuine FHIR R4
PractitionerRole JSON) is validated and stored whole in `content`, every
response is FHIR R4 (`application/fhir+json`, regardless of Accept), and only
the FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/practitionerrole.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing
scope, cross-org isolation), plus the existence checks on every local
reference. Search lives in test_search.py.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.practitioner_role.conftest import ROLE_PERMS
from tests.integration.practitioner_role.support import (
    BASE,
    FULL,
    MINIMAL,
    create_endpoint,
    create_healthcare_service,
    create_location,
    create_organization,
    create_practitioner,
    create_role,
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


def _as_user(sub="u-test", org_id="org-test", permissions=ROLE_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _linked_body(client) -> dict:
    """A role pointing at one real resource of every referenced kind."""
    return {
        **FULL,
        "practitioner": {
            "reference": f"Practitioner/{await create_practitioner(client)}"
        },
        "organization": {
            "reference": f"Organization/{await create_organization(client)}"
        },
        "location": [{"reference": f"Location/{await create_location(client)}"}],
        "healthcareService": [
            {
                "reference": f"HealthcareService/{await create_healthcare_service(client)}"
            }
        ],
        "endpoint": [{"reference": f"Endpoint/{await create_endpoint(client)}"}],
    }


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    assert (
        resp.json()["resourceType"] == "PractitionerRole"
        and resp.json()["active"] is True
    )


async def test_create_full_round_trip(client):
    body = await _linked_body(client)
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected
    assert (await client.get(f"{BASE}/{data['id']}")).json() == data


async def test_create_keeps_elements_nothing_searches_on(client):
    """availableTime, notAvailable and availabilityExceptions have no search
    parameter — they live only in `content`."""
    data = (await client.post(BASE + "/", json=FULL)).json()
    assert data["availableTime"][0]["daysOfWeek"] == ["mon", "tue"]
    assert data["availableTime"][1]["allDay"] is True
    assert data["notAvailable"][0]["description"] == "Conference week"
    assert data["availabilityExceptions"] == "Not on public holidays"


async def test_create_ignores_server_managed_id_and_meta(client):
    resp = await client.post(
        BASE + "/",
        json={**MINIMAL, "id": "999", "meta": {"lastUpdated": "2000-01-01T00:00:00Z"}},
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_non_fhir_key_rejected(client, native_validation):
    assert (
        await client.post(BASE + "/", json={**MINIMAL, "not_a_fhir_element": 1})
    ).status_code == 422


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in (
        {"period_start": "2026-01-01T00:00:00Z"},
        {"availability_exceptions": "x"},
        {"org_id": "x"},
    ):
        resp = await client.post(BASE + "/", json={**MINIMAL, **stale})
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    assert (
        await client.post(BASE + "/", json={**MINIMAL, "resourceType": "Patient"})
    ).status_code == 422


async def test_create_bad_day_of_week_and_missing_description_rejected(client):
    assert (
        await client.post(
            BASE + "/", json={**MINIMAL, "availableTime": [{"daysOfWeek": ["funday"]}]}
        )
    ).status_code == 422
    body = {**MINIMAL, "notAvailable": [{"during": {"start": "2026-09-01T00:00:00Z"}}]}
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=MINIMAL)).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


@pytest.mark.parametrize(
    "body",
    [
        {"practitioner": {"reference": "Practitioner/999999"}},
        {"organization": {"reference": "Organization/999999"}},
        {"location": [{"reference": "Location/999999"}]},
        {"healthcareService": [{"reference": "HealthcareService/999999"}]},
        {"endpoint": [{"reference": "Endpoint/999999"}]},
        {
            "identifier": [
                {"value": "1", "assigner": {"reference": "Organization/999999"}}
            ]
        },
    ],
    ids=[
        "practitioner",
        "organization",
        "location",
        "healthcareService",
        "endpoint",
        "identifier.assigner",
    ],
)
async def test_create_local_reference_must_exist(client, body):
    resp = await client.post(BASE + "/", json={**MINIMAL, **body})
    assert resp.status_code == 422, resp.text


async def test_create_absolute_and_logical_references_not_resolved(client):
    absolute = "https://other.example.org/fhir/Practitioner/42"
    resp = await client.post(
        BASE + "/", json={**MINIMAL, "practitioner": {"reference": absolute}}
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["practitioner"]["reference"] == absolute
    logical = {
        "organization": {"identifier": {"system": "urn:registry", "value": "ORG-9"}}
    }
    assert (
        await client.post(BASE + "/", json={**MINIMAL, **logical})
    ).status_code == 201


async def test_create_reference_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        other_practitioner = await create_practitioner(other_client, "Other")
    finally:
        _as_user()
    body = {
        **MINIMAL,
        "practitioner": {"reference": f"Practitioner/{other_practitioner}"},
    }
    assert (await client.post(BASE + "/", json=body)).status_code == 422


# ── Read ─────────────────────────────────────────────────────────────────────


async def test_get_by_id(client):
    role = await create_role(client, FULL)
    resp = await client.get(f"{BASE}/{role}")
    assert resp.status_code == 200 and resp.json()["id"] == str(role)


async def test_get_is_fhir_regardless_of_accept(client):
    role = await create_role(client)
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{role}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "PractitionerRole"


async def test_xml_only_accept_is_406(client):
    role = await create_role(client)
    resp = await client.get(
        f"{BASE}/{role}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_scalar_keeps_the_rest(client):
    role = await create_role(client, FULL)
    resp = await client.patch(
        f"{BASE}/{role}", json={"active": False, "availabilityExceptions": "Open daily"}
    )
    assert resp.status_code == 200, resp.text
    assert (
        resp.json()["active"] is False
        and resp.json()["availabilityExceptions"] == "Open daily"
    )
    assert resp.json()["availableTime"][0]["daysOfWeek"] == ["mon", "tue"]


async def test_patch_reindexes_search(client):
    role = await create_role(client, FULL)
    await client.patch(
        f"{BASE}/{role}",
        json={"specialty": [{"coding": [{"code": "NEW"}]}], "active": False},
    )
    assert role not in _ids(
        (await client.get(BASE + "/", params={"specialty": "394579002"})).json()
    )
    assert role in _ids(
        (await client.get(BASE + "/", params={"specialty": "NEW"})).json()
    )
    assert role in _ids(
        (await client.get(BASE + "/", params={"active": "false"})).json()
    )


async def test_patch_period_reindexes_the_date_search(client):
    role = await create_role(client, FULL)  # 2026
    # eq (the default) = the search range wholly contains the period, so use the whole of 2026.
    assert role in _ids((await client.get(BASE + "/", params={"date": "2026"})).json())
    await client.patch(
        f"{BASE}/{role}", json={"period": {"start": "2030-01-01T00:00:00Z"}}
    )
    assert role not in _ids(
        (await client.get(BASE + "/", params={"date": "2026"})).json()
    )
    assert role in _ids(
        (await client.get(BASE + "/", params={"date": "ge2031-01-01"})).json()
    )  # still going
    resp = await client.patch(f"{BASE}/{role}", json={"period": None})
    assert "period" not in resp.json()
    assert role not in _ids(
        (await client.get(BASE + "/", params={"date": "ge2031-01-01"})).json()
    )


async def test_patch_replaces_list_wholesale_and_empty_clears(client):
    role = await create_role(client, FULL)
    resp = await client.patch(
        f"{BASE}/{role}",
        json={"telecom": [{"system": "email", "value": "r@example.org"}]},
    )
    assert resp.json()["telecom"] == [{"system": "email", "value": "r@example.org"}]
    assert role not in _ids(
        (await client.get(BASE + "/", params={"phone": "555-0100"})).json()
    )
    assert role in _ids(
        (await client.get(BASE + "/", params={"email": "r@example.org"})).json()
    )
    resp = await client.patch(f"{BASE}/{role}", json={"telecom": [], "code": []})
    assert "telecom" not in resp.json() and "code" not in resp.json()
    assert role not in _ids(
        (await client.get(BASE + "/", params={"role": "doctor"})).json()
    )


async def test_patch_practitioner_resolved_then_cleared(client):
    prac = await create_practitioner(client)
    role = await create_role(client)
    await client.patch(
        f"{BASE}/{role}", json={"practitioner": {"reference": f"Practitioner/{prac}"}}
    )
    assert role in _ids(
        (await client.get(BASE + "/", params={"practitioner": str(prac)})).json()
    )
    resp = await client.patch(f"{BASE}/{role}", json={"practitioner": None})
    assert "practitioner" not in resp.json()
    assert role not in _ids(
        (await client.get(BASE + "/", params={"practitioner": str(prac)})).json()
    )


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client):
    role = await create_role(client, FULL)
    resp = await client.patch(
        f"{BASE}/{role}", json={"location": [{"reference": "Location/999999"}]}
    )
    assert resp.status_code == 422
    assert "location" not in (await client.get(f"{BASE}/{role}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    role = await create_role(client, FULL)
    resp = await client.patch(
        f"{BASE}/{role}", json={"availableTime": [{"daysOfWeek": ["funday"]}]}
    )
    assert resp.status_code == 422
    assert (await client.get(f"{BASE}/{role}")).json()["availableTime"][0][
        "daysOfWeek"
    ] == ["mon", "tue"]


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"active": False})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete(client):
    role = await create_role(client, FULL)
    assert (await client.delete(f"{BASE}/{role}")).status_code == 204
    assert (await client.get(f"{BASE}/{role}")).status_code == 404
    # Its index rows are gone with it.
    assert role not in _ids(
        (await client.get(BASE + "/", params={"role": "doctor"})).json()
    )
    assert role not in _ids(
        (await client.get(BASE + "/", params={"identifier": "R-1001"})).json()
    )


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_create_without_permission(client):
    _as_user(permissions=["practitioner_role:read"])
    assert (await client.post(BASE + "/", json=MINIMAL)).status_code == 403


async def test_org_less_token_rejected(client):
    role = await create_role(client)

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": ROLE_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=MINIMAL)).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{role}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    role = await create_role(client)
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{role}"),
            await other_client.patch(f"{BASE}/{role}", json={"active": False}),
            await other_client.delete(f"{BASE}/{role}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_role(
        client, {**FULL, "identifier": [{"system": "urn:t", "value": "TenantAOnly"}]}
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0 and "entry" not in bundle
    finally:
        _as_user()
