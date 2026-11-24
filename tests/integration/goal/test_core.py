"""Core goal endpoint coverage.

Goal is stored content-based (like CarePlan, CareTeam, Patient and the other rebuilt resources):
the request body (genuine FHIR R4 Goal JSON) is validated and stored whole in `content`, every
response is FHIR R4 (`application/fhir+json`, regardless of Accept), and only the FHIR R4 search
parameters are indexed (https://www.hl7.org/fhir/R4/goal.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence checks on every local reference (`subject`, `expressedBy`,
`addresses`, `outcomeReference`, a note's `authorReference` and every identifier's `assigner`).
Search lives in test_search.py.

R4 requires `lifecycleStatus`, `description` and `subject`; the native validator checks `description`
and `subject` (a missing `lifecycleStatus` is only rejected by the `java_validator` backend).
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.goal.conftest import GOAL_PERMS
from tests.integration.goal.support import (
    ACHIEVEMENT,
    BASE,
    concept,
    condition_body,
    create_condition,
    create_goal,
    create_observation,
    create_organization,
    create_patient,
    create_practitioner,
    full_body,
    goal_body,
    observation_body,
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


def _as_user(sub="u-test", org_id="org-test", permissions=GOAL_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client) -> tuple[int, dict]:
    patient = await create_patient(client)
    organization = await create_organization(client)
    condition = await create_condition(client, condition_body(patient))
    observation = await create_observation(client, observation_body(patient))
    practitioner = await create_practitioner(client)
    body = full_body(patient, organization, condition, observation, practitioner)
    return await create_goal(client, body), body


def _subject(patient: int) -> dict:
    return {"reference": f"Patient/{patient}"}


# -- Create ---------------------------------------------------------------------------------


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=goal_body())
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "Goal" and data["lifecycleStatus"] == "active"


async def test_create_full_round_trip(client):
    goal, body = await _full(client)
    data = (await client.get(f"{BASE}/{goal}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_elements_nothing_searches_on(client):
    """`priority`, `statusReason`, `expressedBy`, `addresses`, `note`, `outcomeCode`,
    `outcomeReference` and every target element but its due date live only in `content`."""
    goal, _ = await _full(client)
    data = (await client.get(f"{BASE}/{goal}")).json()
    assert data["priority"]["coding"][0]["code"] == "high-priority"
    assert data["statusReason"] == "Patient agreed"
    assert data["target"][0]["detailQuantity"]["comparator"] == "<"
    assert data["target"][1]["detailRange"]["high"]["value"] == 70
    assert data["target"][1]["dueDuration"]["unit"] == "mo"
    assert data["note"][0]["text"] == "Agreed with the patient."
    assert data["outcomeCode"][0]["text"] == "improved"
    assert data["addresses"][1] == {"reference": "NutritionOrder/9"}


@pytest.mark.parametrize(
    "status",
    [
        "proposed",
        "planned",
        "accepted",
        "active",
        "on-hold",
        "completed",
        "cancelled",
        "entered-in-error",
        "rejected",
    ],
)
async def test_create_every_lifecycle_status_round_trips(client, status):
    resp = await client.post(BASE + "/", json=goal_body(lifecycleStatus=status))
    assert resp.status_code == 201, resp.text
    assert resp.json()["lifecycleStatus"] == status


async def test_create_start_as_a_concept_round_trips(client):
    resp = await client.post(
        BASE + "/",
        json=goal_body(startCodeableConcept=concept(ACHIEVEMENT, "in-progress")),
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["startCodeableConcept"]["coding"][0]["code"] == "in-progress"


async def test_create_ignores_server_managed_id_and_meta(client):
    body = goal_body(id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"})
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client):
    for bad in (
        {"lifecycleStatus": "robot"},
        {"description": "x"},
        {"subject": "Patient/1"},
        {"achievementStatus": "x"},
        {"category": {"text": "x"}},
        {"priority": "high"},
        {"startDate": 5},
        {"target": {"measure": {"text": "x"}}},
        {"target": [{"dueDate": 5}]},
        {"target": [{"detailBoolean": "yes"}]},
        {"statusReason": 5},
        {"expressedBy": "Patient/1"},
        {"addresses": {"reference": "Condition/1"}},
        {"note": "x"},
        {"outcomeCode": "x"},
    ):
        resp = await client.post(BASE + "/", json=goal_body(**bad))
        assert resp.status_code == 422, (bad, resp.text)


async def test_create_missing_required_elements_rejected(client, native_validation):
    for missing in ("description", "subject"):
        body = goal_body()
        del body[missing]
        resp = await client.post(BASE + "/", json=body)
        assert resp.status_code == 422, (missing, resp.text)


async def test_create_non_fhir_key_rejected(client, native_validation):
    resp = await client.post(BASE + "/", json=goal_body(not_a_fhir_element=1))
    assert resp.status_code == 422


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in ({"description_text": "x"}, {"status_date": "2026-01-01"}):
        resp = await client.post(BASE + "/", json={**goal_body(), **stale})
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(BASE + "/", json=goal_body(resourceType="Patient"))
    assert resp.status_code == 422


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=goal_body())).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# -- Create: existence checks on local references --------------------------------------------


async def test_create_subject_must_exist(client):
    patient = await create_patient(client)
    assert (
        await client.post(BASE + "/", json=goal_body(_subject(patient)))
    ).status_code == 201
    missing = goal_body({"reference": "Patient/999999"})
    assert (await client.post(BASE + "/", json=missing)).status_code == 422


async def test_create_subject_group_and_organization_must_exist(client):
    organization = await create_organization(client)
    ok = goal_body({"reference": f"Organization/{organization}"})
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    assert (
        await client.post(
            BASE + "/", json=goal_body({"reference": "Organization/999999"})
        )
    ).status_code == 422
    assert (
        await client.post(BASE + "/", json=goal_body({"reference": "Group/999999"}))
    ).status_code == 422


async def test_create_subject_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    resp = await client.post(BASE + "/", json=goal_body(_subject(theirs)))
    assert resp.status_code == 422


async def test_create_expressed_by_must_exist(client):
    practitioner = await create_practitioner(client)
    ok = goal_body(expressedBy={"reference": f"Practitioner/{practitioner}"})
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = goal_body(expressedBy={"reference": "Practitioner/999999"})
    assert (await client.post(BASE + "/", json=missing)).status_code == 422


async def test_create_addresses_and_outcome_reference_must_exist(client):
    patient = await create_patient(client)
    condition = await create_condition(client, condition_body(patient))
    observation = await create_observation(client, observation_body(patient))
    ok = goal_body(
        addresses=[{"reference": f"Condition/{condition}"}],
        outcomeReference=[{"reference": f"Observation/{observation}"}],
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    for bad in (
        {"addresses": [{"reference": "Condition/999999"}]},
        {"outcomeReference": [{"reference": "Observation/999999"}]},
    ):
        assert (
            await client.post(BASE + "/", json=goal_body(**bad))
        ).status_code == 422, bad


async def test_create_note_author_and_identifier_assigner_must_exist(client):
    practitioner = await create_practitioner(client)
    organization = await create_organization(client)
    ok = goal_body(
        note=[
            {
                "text": "x",
                "authorReference": {"reference": f"Practitioner/{practitioner}"},
            }
        ],
        identifier=[
            {"value": "1", "assigner": {"reference": f"Organization/{organization}"}}
        ],
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    for bad in (
        {
            "note": [
                {"text": "x", "authorReference": {"reference": "Practitioner/999999"}}
            ]
        },
        {
            "identifier": [
                {"value": "1", "assigner": {"reference": "Organization/999999"}}
            ]
        },
    ):
        assert (
            await client.post(BASE + "/", json=goal_body(**bad))
        ).status_code == 422, bad


async def test_create_unmodeled_targets_are_not_checked(client):
    """A NutritionOrder is not a resource on this server: stored as sent."""
    body = goal_body(addresses=[{"reference": "NutritionOrder/999999"}])
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["addresses"] == [{"reference": "NutritionOrder/999999"}]


async def test_create_absolute_and_logical_subjects_not_resolved(client):
    absolute = "https://other.example.org/fhir/Patient/7"
    resp = await client.post(BASE + "/", json=goal_body({"reference": absolute}))
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == {"reference": absolute}
    logical = {"identifier": {"system": "urn:mrn", "value": "M-9"}, "display": "Jane"}
    resp = await client.post(BASE + "/", json=goal_body(logical))
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == logical


# -- Read -----------------------------------------------------------------------------------


async def test_get_by_id(client):
    goal, _ = await _full(client)
    resp = await client.get(f"{BASE}/{goal}")
    assert resp.status_code == 200 and resp.json()["id"] == str(goal)


async def test_get_is_fhir_regardless_of_accept(client):
    goal = await create_goal(client, goal_body())
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{goal}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "Goal"


async def test_xml_only_accept_is_406(client):
    goal = await create_goal(client, goal_body())
    resp = await client.get(
        f"{BASE}/{goal}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Patch ----------------------------------------------------------------------------------


async def test_patch_scalar_keeps_the_rest(client):
    goal, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{goal}",
        json={"lifecycleStatus": "completed", "statusReason": "Done"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["lifecycleStatus"] == "completed"
    assert resp.json()["statusReason"] == "Done"
    assert resp.json()["achievementStatus"]["coding"][0]["code"] == "in-progress"
    assert resp.json()["subject"]["reference"].startswith("Patient/")  # untouched


async def test_patch_reindexes_search(client):
    goal, _ = await _full(client)
    patched = await client.patch(
        f"{BASE}/{goal}",
        json={
            "lifecycleStatus": "completed",
            "achievementStatus": concept(ACHIEVEMENT, "achieved"),
            "category": [concept("http://example.org/cat", "other")],
            "startDate": "2027-02-01",
            "target": [{"dueDate": "2028-05-05"}],
        },
    )
    assert patched.status_code == 200, patched.text
    for param, old, new in (
        ("lifecycle-status", "active", "completed"),
        ("achievement-status", "in-progress", "achieved"),
        ("category", "dietary", "other"),
        ("start-date", "2026-01-15", "2027-02-01"),
        ("target-date", "2026-12-31", "2028-05-05"),
    ):
        assert goal not in _ids(
            (await client.get(BASE + "/", params={param: old})).json()
        ), param
        assert goal in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param


async def test_patch_replaces_lists_and_empty_clears(client):
    goal, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{goal}", json={"identifier": [], "category": [], "target": []}
    )
    for gone in ("identifier", "category", "target"):
        assert gone not in resp.json()
    assert resp.json()["lifecycleStatus"] == "active"  # untouched
    for param in ("identifier", "category", "target-date"):
        assert goal in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_clears_start_and_achievement_status(client):
    goal, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{goal}", json={"startDate": None, "achievementStatus": None}
    )
    assert "startDate" not in resp.json() and "achievementStatus" not in resp.json()
    for param in ("start-date", "achievement-status"):
        assert goal in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client):
    goal = await create_goal(client, goal_body())
    resp = await client.patch(
        f"{BASE}/{goal}", json={"expressedBy": {"reference": "Patient/999999"}}
    )
    assert resp.status_code == 422
    assert "expressedBy" not in (await client.get(f"{BASE}/{goal}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    goal = await create_goal(client, goal_body())
    assert (
        await client.patch(f"{BASE}/{goal}", json={"lifecycleStatus": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{goal}")).json()["lifecycleStatus"] == "active"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"lifecycleStatus": "active"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Delete ---------------------------------------------------------------------------------


async def test_delete(client):
    goal, _ = await _full(client)
    assert (await client.delete(f"{BASE}/{goal}")).status_code == 204
    assert (await client.get(f"{BASE}/{goal}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "G-1001"),
        ("achievement-status", "in-progress"),
        ("category", "dietary"),
        ("target-date", "2026-12-31"),
    ):
        assert goal not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Auth -----------------------------------------------------------------------------------


async def test_create_without_permission(client):
    _as_user(permissions=["goal:read"])
    assert (await client.post(BASE + "/", json=goal_body())).status_code == 403


async def test_org_less_token_rejected(client):
    goal = await create_goal(client, goal_body())

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": GOAL_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=goal_body())).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{goal}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    goal = await create_goal(client, goal_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{goal}"),
            await other_client.patch(
                f"{BASE}/{goal}", json={"lifecycleStatus": "active"}
            ),
            await other_client.delete(f"{BASE}/{goal}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_goal(
        client, goal_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}])
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()


async def test_goal_is_checked_where_it_can_be_named(client):
    """CarePlan.goal is Reference(Goal) and DetectedIssue.implicated is Reference(Any): a
    relative Goal there must exist (422 otherwise)."""
    goal = await create_goal(client, goal_body())
    plans = "/api/fhir/v1/care-plans/"
    subject = {"reference": "https://other.example.org/fhir/Patient/1"}
    ok = {
        "status": "active",
        "intent": "plan",
        "subject": subject,
        "goal": [{"reference": f"Goal/{goal}"}],
    }
    assert (await client.post(plans, json=ok)).status_code == 201
    missing = {**ok, "goal": [{"reference": "Goal/999999"}]}
    assert (await client.post(plans, json=missing)).status_code == 422
    issues = "/api/fhir/v1/detected-issues/"
    ok = {"status": "final", "implicated": [{"reference": f"Goal/{goal}"}]}
    assert (await client.post(issues, json=ok)).status_code == 201
    missing = {"status": "final", "implicated": [{"reference": "Goal/999999"}]}
    assert (await client.post(issues, json=missing)).status_code == 422
