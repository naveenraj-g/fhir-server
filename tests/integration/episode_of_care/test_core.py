"""Core episode of care endpoint coverage.

EpisodeOfCare is stored Medplum-style (like CareTeam, CarePlan, Encounter and the other
content-based resources): the request body (genuine FHIR R4 EpisodeOfCare JSON) is validated and
stored whole in `content`, every response is FHIR R4 (`application/fhir+json`, regardless of
Accept), and only the FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/episodeofcare.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence checks on every local reference (`patient`, `managingOrganization`,
`careManager`, `referralRequest`, `team`, `diagnosis.condition` and every identifier's `assigner`),
and the places other resources point at an episode. Search lives in test_search.py.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.episode_of_care.conftest import EPISODE_PERMS
from tests.integration.episode_of_care.support import (
    BASE,
    EPISODE_TYPE,
    concept,
    condition_body,
    create_condition,
    create_episode,
    create_minimal_care_team,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_service_request,
    episode_body,
    full_body,
    service_request_body,
)


@pytest.fixture
def native_validation(monkeypatch):
    """The base R4 validator may be switched off in configs/config.yaml (`fhir_validation.enabled:
    false` skips it entirely). Tests that assert "a key that isn't FHIR is a 422" need it on: the
    project's own structural check (no sidecar needed)."""
    monkeypatch.setattr(settings.fhir_validation, "enabled", True)
    monkeypatch.setattr(settings.fhir_validation, "backend", "native")


def _ids(bundle: dict) -> set[int]:
    return {
        int(e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == "match"
    }


def _as_user(sub="u-test", org_id="org-test", permissions=EPISODE_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client) -> tuple[int, dict]:
    organization = await create_organization(client)
    patient = await create_patient(client)
    practitioner = await create_practitioner(client)
    condition = await create_condition(client, condition_body(patient))
    referral = await create_service_request(client, service_request_body(patient))
    team = await create_minimal_care_team(client)
    body = full_body(organization, patient, practitioner, condition, referral, team)
    return await create_episode(client, body), body


# -- Create ---------------------------------------------------------------------------------


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=episode_body())
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    assert resp.json()["resourceType"] == "EpisodeOfCare"
    assert resp.json()["id"] == "350000"  # the first id of the block


async def test_create_full_round_trip(client):
    episode, body = await _full(client)
    data = (await client.get(f"{BASE}/{episode}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_elements_nothing_searches_on(client):
    """`statusHistory`, `diagnosis.role` / `.rank`, `team` and `account` live only in `content`."""
    episode, _ = await _full(client)
    data = (await client.get(f"{BASE}/{episode}")).json()
    assert [h["status"] for h in data["statusHistory"]] == ["planned", "active"]
    assert data["statusHistory"][0]["period"] == {
        "start": "2025-12-01",
        "end": "2025-12-31",
    }
    assert data["diagnosis"][0]["role"]["coding"][0]["code"] == "AD"
    assert data["diagnosis"][0]["rank"] == 1
    assert data["team"][0]["reference"].startswith("CareTeam/")
    assert data["account"][0]["reference"].endswith("/Account/7")


@pytest.mark.parametrize(
    "status",
    [
        "planned",
        "waitlist",
        "active",
        "onhold",
        "finished",
        "cancelled",
        "entered-in-error",
    ],
)
async def test_create_every_status_round_trips(client, status):
    resp = await client.post(BASE + "/", json=episode_body(status=status))
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


async def test_create_ignores_server_managed_id_and_meta(client):
    body = episode_body(id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"})
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client):
    for bad in (
        {"status": "retired"},
        {"type": {"text": "x"}},
        {"type": ["x"]},
        {"patient": "Patient/1"},
        {"managingOrganization": "Organization/1"},
        {"managingOrganization": [{"reference": "Organization/1"}]},
        {"careManager": "Practitioner/1"},
        {"period": "2026"},
        {"identifier": {"value": "x"}},
        {"statusHistory": {"status": "active"}},
        {"statusHistory": [{"status": "retired", "period": {"start": "2026"}}]},
        {"diagnosis": {"condition": {"reference": "Condition/1"}}},
        {"diagnosis": [{"condition": "Condition/1"}]},
        {"diagnosis": [{"condition": {"reference": "Condition/1"}, "rank": "first"}]},
        {"referralRequest": {"reference": "ServiceRequest/1"}},
        {"team": {"reference": "CareTeam/1"}},
        {"account": {"reference": "Account/1"}},
    ):
        resp = await client.post(BASE + "/", json=episode_body(**bad))
        assert resp.status_code == 422, (bad, resp.text)


async def test_create_non_fhir_key_rejected(client, native_validation):
    resp = await client.post(BASE + "/", json=episode_body(not_a_fhir_element=1))
    assert resp.status_code == 422


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in (
        {"patient_id": 1},
        {"org_id": "x"},
        {"user_id": "x"},
        {"status_history": [{"status": "active"}]},
    ):
        resp = await client.post(BASE + "/", json={**episode_body(), **stale})
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(BASE + "/", json=episode_body(resourceType="Patient"))
    assert resp.status_code == 422


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=episode_body())).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# -- Create: existence checks on local references --------------------------------------------


async def test_create_patient_must_exist(client):
    resp = await client.post(
        BASE + "/", json=episode_body(patient={"reference": "Patient/999999"})
    )
    assert resp.status_code == 422
    assert "patient" in resp.text
    patient = await create_patient(client)
    assert (
        await client.post(BASE + "/", json=episode_body(patient))
    ).status_code == 201


async def test_create_managing_organization_must_exist(client):
    body = episode_body(managingOrganization={"reference": "Organization/999999"})
    assert (await client.post(BASE + "/", json=body)).status_code == 422
    organization = await create_organization(client)
    ok = episode_body(
        managingOrganization={"reference": f"Organization/{organization}"}
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201


async def test_create_care_manager_must_exist(client):
    """careManager is a Practitioner or a PractitionerRole - either must exist."""
    for ref in ("Practitioner/999999", "PractitionerRole/999999"):
        body = episode_body(careManager={"reference": ref})
        assert (await client.post(BASE + "/", json=body)).status_code == 422, ref
    practitioner = await create_practitioner(client)
    role = await create_practitioner_role(
        client, {"practitioner": {"reference": f"Practitioner/{practitioner}"}}
    )
    for ref in (f"Practitioner/{practitioner}", f"PractitionerRole/{role}"):
        body = episode_body(careManager={"reference": ref})
        assert (await client.post(BASE + "/", json=body)).status_code == 201, ref


async def test_create_referral_requests_must_exist(client):
    patient = await create_patient(client)
    referral = await create_service_request(client, service_request_body(patient))
    ok = episode_body(referralRequest=[{"reference": f"ServiceRequest/{referral}"}])
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = episode_body(
        referralRequest=[
            {"reference": f"ServiceRequest/{referral}"},
            {"reference": "ServiceRequest/999999"},
        ]
    )
    resp = await client.post(BASE + "/", json=bad)
    assert resp.status_code == 422
    assert "referralRequest[1]" in resp.text


async def test_create_team_must_exist(client):
    team = await create_minimal_care_team(client)
    ok = episode_body(team=[{"reference": f"CareTeam/{team}"}])
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = episode_body(team=[{"reference": "CareTeam/999999"}])
    assert (await client.post(BASE + "/", json=bad)).status_code == 422


async def test_create_diagnosis_condition_must_exist(client):
    patient = await create_patient(client)
    condition = await create_condition(client, condition_body(patient))
    ok = episode_body(
        diagnosis=[{"condition": {"reference": f"Condition/{condition}"}}]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = episode_body(diagnosis=[{"condition": {"reference": "Condition/999999"}}])
    resp = await client.post(BASE + "/", json=bad)
    assert resp.status_code == 422
    assert "diagnosis[0].condition" in resp.text


async def test_create_every_identifier_assigner_must_exist(client):
    bad = episode_body(
        identifier=[
            {"value": "1", "assigner": {"reference": "Organization/999999"}},
        ]
    )
    assert (await client.post(BASE + "/", json=bad)).status_code == 422


async def test_create_reference_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    body = episode_body(patient={"reference": f"Patient/{theirs}"})
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_absolute_logical_and_unmodeled_references_not_resolved(client):
    """An absolute URL, a logical (identifier-only) reference and an Account (not a resource on
    this server) are stored as sent."""
    body = episode_body(
        patient={"reference": "https://other.example.org/fhir/Patient/1"},
        managingOrganization={"identifier": {"system": "urn:org", "value": "O-9"}},
        careManager={"reference": "https://other.example.org/fhir/Practitioner/9"},
        referralRequest=[
            {"reference": "https://other.example.org/fhir/ServiceRequest/7"}
        ],
        diagnosis=[
            {"condition": {"identifier": {"system": "urn:cond", "value": "C-1"}}},
        ],
        account=[{"reference": "Account/12"}],
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["patient"]["reference"] == "https://other.example.org/fhir/Patient/1"
    assert data["managingOrganization"]["identifier"]["value"] == "O-9"
    assert data["account"][0]["reference"] == "Account/12"


# -- Read -----------------------------------------------------------------------------------


async def test_get_by_id(client):
    episode, _ = await _full(client)
    resp = await client.get(f"{BASE}/{episode}")
    assert resp.status_code == 200 and resp.json()["id"] == str(episode)


async def test_get_is_fhir_regardless_of_accept(client):
    episode = await create_episode(client, episode_body())
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{episode}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "EpisodeOfCare"


async def test_xml_only_accept_is_406(client):
    episode = await create_episode(client, episode_body())
    resp = await client.get(
        f"{BASE}/{episode}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Patch ----------------------------------------------------------------------------------


async def test_patch_scalar_keeps_the_rest(client):
    episode, _ = await _full(client)
    resp = await client.patch(f"{BASE}/{episode}", json={"status": "finished"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "finished"
    assert resp.json()["type"][0]["coding"][0]["code"] == "cacp"  # untouched
    assert resp.json()["diagnosis"][0]["rank"] == 1


async def test_patch_reindexes_search(client):
    episode, _ = await _full(client)
    patient = await create_patient(client)
    await client.patch(
        f"{BASE}/{episode}",
        json={
            "status": "onhold",
            "type": [concept(EPISODE_TYPE, "hacc")],
            "period": {"start": "2030-01-01"},
            "patient": {"reference": f"Patient/{patient}"},
            "diagnosis": [],
            "referralRequest": [],
        },
    )
    for param, old, new in (
        ("status", "active", "onhold"),
        ("type", "cacp", "hacc"),
        ("date", "le2026-12-31", "ge2031-01-01"),
        ("patient", None, str(patient)),
    ):
        if old is not None:
            assert episode not in _ids(
                (await client.get(BASE + "/", params={param: old})).json()
            ), param
        assert episode in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param
    for param in ("condition", "incoming-referral"):
        assert episode in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_replaces_lists_and_empty_clears(client):
    episode, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{episode}",
        json={"identifier": [], "type": [], "diagnosis": [], "referralRequest": []},
    )
    for gone in ("identifier", "type", "diagnosis", "referralRequest"):
        assert gone not in resp.json()
    assert resp.json()["status"] == "active"  # untouched
    for param in ("identifier", "type", "condition", "incoming-referral"):
        assert episode in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_clears_manager_and_missing_follows(client):
    practitioner = await create_practitioner(client)
    episode = await create_episode(
        client,
        episode_body(careManager={"reference": f"Practitioner/{practitioner}"}),
    )
    assert episode not in _ids(
        (await client.get(BASE + "/", params={"care-manager:missing": "true"})).json()
    )
    resp = await client.patch(f"{BASE}/{episode}", json={"careManager": None})
    assert "careManager" not in resp.json()
    assert episode in _ids(
        (await client.get(BASE + "/", params={"care-manager:missing": "true"})).json()
    )


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client):
    episode = await create_episode(client, episode_body())
    resp = await client.patch(
        f"{BASE}/{episode}",
        json={"team": [{"reference": "CareTeam/999999"}]},
    )
    assert resp.status_code == 422
    assert "team" not in (await client.get(f"{BASE}/{episode}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    episode = await create_episode(client, episode_body(status="active"))
    assert (
        await client.patch(f"{BASE}/{episode}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{episode}")).json()["status"] == "active"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "finished"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Delete ---------------------------------------------------------------------------------


async def test_delete(client):
    episode, _ = await _full(client)
    assert (await client.delete(f"{BASE}/{episode}")).status_code == 204
    assert (await client.get(f"{BASE}/{episode}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "EOC-1001"),
        ("type", "cacp"),
        ("status", "active"),
    ):
        assert episode not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Auth -----------------------------------------------------------------------------------


async def test_create_without_permission(client):
    _as_user(permissions=["episode_of_care:read"])
    assert (await client.post(BASE + "/", json=episode_body())).status_code == 403


async def test_org_less_token_rejected(client):
    episode = await create_episode(client, episode_body())

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": EPISODE_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=episode_body())).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{episode}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    episode = await create_episode(client, episode_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{episode}"),
            await other_client.patch(f"{BASE}/{episode}", json={"status": "finished"}),
            await other_client.delete(f"{BASE}/{episode}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_episode(
        client,
        episode_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}]),
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()


# -- Other resources that point at an episode ------------------------------------------------


async def test_episode_is_checked_in_encounter_episode_of_care(client):
    """Encounter.episodeOfCare names an episode: a relative reference must exist."""
    episode = await create_episode(client, episode_body())
    encounters = "/api/fhir/v1/encounters/"
    from tests.integration.encounter.support import encounter_body

    ok = encounter_body(episodeOfCare=[{"reference": f"EpisodeOfCare/{episode}"}])
    assert (await client.post(encounters, json=ok)).status_code == 201
    missing = encounter_body(episodeOfCare=[{"reference": "EpisodeOfCare/999999"}])
    resp = await client.post(encounters, json=missing)
    assert resp.status_code == 422 and "episodeOfCare[0]" in resp.text


async def test_episode_is_checked_where_a_reference_any_can_name_it(client):
    """DetectedIssue.implicated is a Reference(Any): a relative EpisodeOfCare there must exist."""
    episode = await create_episode(client, episode_body())
    issues = "/api/fhir/v1/detected-issues/"
    ok = {"status": "final", "implicated": [{"reference": f"EpisodeOfCare/{episode}"}]}
    assert (await client.post(issues, json=ok)).status_code == 201
    missing = {"status": "final", "implicated": [{"reference": "EpisodeOfCare/999999"}]}
    assert (await client.post(issues, json=missing)).status_code == 422
