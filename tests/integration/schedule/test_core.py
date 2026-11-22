"""Core schedule endpoint coverage.

Schedule is stored Medplum-style (like Organization/Location/Practitioner/
HealthcareService/Endpoint/PractitionerRole): the request body (genuine FHIR
R4 Schedule JSON) is validated and stored whole in `content`, every response
is FHIR R4 (`application/fhir+json`, regardless of Accept), and only the FHIR
R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/schedule.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing
scope, cross-org isolation), plus the existence checks on `actor` — which can
point at seven resource types, only four of which are resources on this server.
Search lives in test_search.py.

R4 requires at least one `actor`, but only the `java_validator` backend
enforces cardinality minimums (the native structural check does not), so that
is not asserted here.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.schedule.conftest import SCHEDULE_PERMS
from tests.integration.patient.support import create_patient
from tests.integration.related_person.support import (
    create_related_person,
    related_person_body,
)
from tests.integration.schedule.support import (
    EXTERNAL_PATIENT,
    BASE,
    FULL,
    MINIMAL,
    create_healthcare_service,
    create_location,
    create_organization,
    create_practitioner,
    create_practitioner_role,
    create_schedule,
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


def _as_user(sub="u-test", org_id="org-test", permissions=SCHEDULE_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    assert resp.json()["resourceType"] == "Schedule" and resp.json()["active"] is True


async def test_create_full_round_trip_with_every_kind_of_actor(client):
    patient = await create_patient(client)
    related = await create_related_person(client, related_person_body(patient))
    body = {
        **FULL,
        "actor": [
            {"reference": f"Practitioner/{await create_practitioner(client)}"},
            {"reference": f"PractitionerRole/{await create_practitioner_role(client)}"},
            {
                "reference": f"HealthcareService/{await create_healthcare_service(client)}"
            },
            {"reference": f"Location/{await create_location(client)}"},
            {"reference": f"Patient/{patient}"},
            {"reference": f"RelatedPerson/{related}"},
            {"reference": "Device/5"},
        ],
    }
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected
    assert (await client.get(f"{BASE}/{data['id']}")).json() == data


async def test_create_keeps_elements_nothing_searches_on(client):
    """`comment` has no search parameter — it lives only in `content`."""
    assert (await client.post(BASE + "/", json=FULL)).json()[
        "comment"
    ] == "Weekday clinic"


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
        {"planning_horizon_start": "2026-01-01T00:00:00Z"},
        {"service_category": [{"code": "17"}]},
        {"org_id": "x"},
    ):
        resp = await client.post(BASE + "/", json={**MINIMAL, **stale})
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    assert (
        await client.post(BASE + "/", json={**MINIMAL, "resourceType": "Patient"})
    ).status_code == 422


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=MINIMAL)).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


@pytest.mark.parametrize(
    "actor",
    [
        {"reference": "Practitioner/999999"},
        {"reference": "PractitionerRole/999999"},
        {"reference": "HealthcareService/999999"},
        {"reference": "Location/999999"},
    ],
    ids=["Practitioner", "PractitionerRole", "HealthcareService", "Location"],
)
async def test_create_actor_of_a_modeled_type_must_exist(client, actor):
    resp = await client.post(BASE + "/", json={**MINIMAL, "actor": [actor]})
    assert resp.status_code == 422, resp.text


async def test_create_identifier_assigner_must_exist(client):
    body = {
        **MINIMAL,
        "identifier": [
            {"value": "1", "assigner": {"reference": "Organization/999999"}}
        ],
    }
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_patient_and_related_person_actors_must_exist_a_device_is_not_checked(
    client,
):
    """A Patient / RelatedPerson actor is a resource here, so it must exist; a Device is not a
    resource on this server, so there is nothing to resolve: stored as sent."""
    patient = await create_patient(client)
    related = await create_related_person(client, related_person_body(patient))
    for ref in (f"Patient/{patient}", f"RelatedPerson/{related}", "Device/999999"):
        resp = await client.post(
            BASE + "/", json={**MINIMAL, "actor": [{"reference": ref}]}
        )
        assert resp.status_code == 201, (ref, resp.text)
    for missing in ("Patient/999999", "RelatedPerson/999999"):
        resp = await client.post(
            BASE + "/", json={**MINIMAL, "actor": [{"reference": missing}]}
        )
        assert resp.status_code == 422, (missing, resp.text)


async def test_create_absolute_and_logical_actors_not_resolved(client):
    absolute = "https://other.example.org/fhir/Practitioner/42"
    logical = {"identifier": {"system": "urn:device", "value": "D-9"}}
    resp = await client.post(
        BASE + "/", json={**MINIMAL, "actor": [{"reference": absolute}, logical]}
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["actor"][0]["reference"] == absolute


async def test_create_actor_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        other_practitioner = await create_practitioner(other_client, "Other")
    finally:
        _as_user()
    body = {**MINIMAL, "actor": [{"reference": f"Practitioner/{other_practitioner}"}]}
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_identifier_assigner_that_exists(client):
    org = await create_organization(client)
    body = {
        **MINIMAL,
        "identifier": [
            {"value": "1", "assigner": {"reference": f"Organization/{org}"}}
        ],
    }
    assert (await client.post(BASE + "/", json=body)).status_code == 201


# ── Read ─────────────────────────────────────────────────────────────────────


async def test_get_by_id(client):
    sched = await create_schedule(client, FULL)
    resp = await client.get(f"{BASE}/{sched}")
    assert resp.status_code == 200 and resp.json()["id"] == str(sched)


async def test_get_is_fhir_regardless_of_accept(client):
    sched = await create_schedule(client)
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{sched}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "Schedule"


async def test_xml_only_accept_is_406(client):
    sched = await create_schedule(client)
    resp = await client.get(
        f"{BASE}/{sched}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_scalar_keeps_the_rest(client):
    sched = await create_schedule(client, FULL)
    resp = await client.patch(
        f"{BASE}/{sched}", json={"active": False, "comment": "Closed"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["active"] is False and resp.json()["comment"] == "Closed"
    assert resp.json()["actor"] == FULL["actor"]  # required element untouched


async def test_patch_reindexes_search(client):
    sched = await create_schedule(client, FULL)
    await client.patch(
        f"{BASE}/{sched}",
        json={"specialty": [{"coding": [{"code": "NEW"}]}], "active": False},
    )
    assert sched not in _ids(
        (await client.get(BASE + "/", params={"specialty": "394579002"})).json()
    )
    assert sched in _ids(
        (await client.get(BASE + "/", params={"specialty": "NEW"})).json()
    )
    assert sched in _ids(
        (await client.get(BASE + "/", params={"active": "false"})).json()
    )


async def test_patch_planning_horizon_reindexes_the_date_search(client):
    sched = await create_schedule(client, FULL)  # all of 2026
    assert sched in _ids((await client.get(BASE + "/", params={"date": "2026"})).json())
    await client.patch(
        f"{BASE}/{sched}", json={"planningHorizon": {"start": "2030-01-01T00:00:00Z"}}
    )
    assert sched not in _ids(
        (await client.get(BASE + "/", params={"date": "2026"})).json()
    )
    assert sched in _ids(
        (await client.get(BASE + "/", params={"date": "ge2031-01-01"})).json()
    )  # still going
    resp = await client.patch(f"{BASE}/{sched}", json={"planningHorizon": None})
    assert "planningHorizon" not in resp.json()
    assert sched not in _ids(
        (await client.get(BASE + "/", params={"date": "ge2031-01-01"})).json()
    )


async def test_patch_actor_list_replaced_and_reindexed(client):
    prac = await create_practitioner(client)
    patient = await create_patient(client)
    sched = await create_schedule(
        client, {**MINIMAL, "actor": [{"reference": f"Patient/{patient}"}]}
    )
    assert sched in _ids(
        (await client.get(BASE + "/", params={"actor": f"Patient/{patient}"})).json()
    )
    resp = await client.patch(
        f"{BASE}/{sched}", json={"actor": [{"reference": f"Practitioner/{prac}"}]}
    )
    assert resp.json()["actor"] == [{"reference": f"Practitioner/{prac}"}]
    assert sched not in _ids(
        (await client.get(BASE + "/", params={"actor": f"Patient/{patient}"})).json()
    )
    assert sched in _ids(
        (await client.get(BASE + "/", params={"actor": f"Practitioner/{prac}"})).json()
    )


async def test_patch_empty_list_clears(client):
    sched = await create_schedule(client, FULL)
    resp = await client.patch(
        f"{BASE}/{sched}", json={"serviceCategory": [], "identifier": []}
    )
    assert "serviceCategory" not in resp.json() and "identifier" not in resp.json()
    assert sched not in _ids(
        (await client.get(BASE + "/", params={"service-category": "17"})).json()
    )
    assert sched not in _ids(
        (await client.get(BASE + "/", params={"identifier": "S-1001"})).json()
    )


async def test_patch_nonexistent_actor_rejected_and_nothing_written(client):
    sched = await create_schedule(client, FULL)
    resp = await client.patch(
        f"{BASE}/{sched}", json={"actor": [{"reference": "Location/999999"}]}
    )
    assert resp.status_code == 422
    assert (await client.get(f"{BASE}/{sched}")).json()["actor"] == FULL["actor"]


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    sched = await create_schedule(client, FULL)
    assert (
        await client.patch(f"{BASE}/{sched}", json={"active": "not-a-bool"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{sched}")).json()["active"] is True


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"active": False})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete(client):
    sched = await create_schedule(client, FULL)
    assert (await client.delete(f"{BASE}/{sched}")).status_code == 204
    assert (await client.get(f"{BASE}/{sched}")).status_code == 404
    # Its index rows are gone with it.
    assert sched not in _ids(
        (await client.get(BASE + "/", params={"identifier": "S-1001"})).json()
    )
    assert sched not in _ids(
        (await client.get(BASE + "/", params={"actor": EXTERNAL_PATIENT})).json()
    )


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_create_without_permission(client):
    _as_user(permissions=["schedule:read"])
    assert (await client.post(BASE + "/", json=MINIMAL)).status_code == 403


async def test_org_less_token_rejected(client):
    sched = await create_schedule(client)

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": SCHEDULE_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=MINIMAL)).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{sched}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    sched = await create_schedule(client)
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{sched}"),
            await other_client.patch(f"{BASE}/{sched}", json={"active": False}),
            await other_client.delete(f"{BASE}/{sched}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_schedule(
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
