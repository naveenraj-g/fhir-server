"""Core task endpoint coverage.

Task is stored content-based (like Goal, CarePlan, Patient and the other rebuilt resources): the
request body (genuine FHIR R4 Task JSON) is validated and stored whole in `content`, every
response is FHIR R4 (`application/fhir+json`, regardless of Accept), and only the FHIR R4 search
parameters are indexed (https://www.hl7.org/fhir/R4/task.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence checks on every local reference (`for`, `focus`, `basedOn`,
`partOf`, `encounter`, `requester`, `owner`, `location`, `restriction.recipient`, a note's
`authorReference` and every identifier's `assigner`). Search lives in test_search.py.

R4 requires `status` and `intent`; only the `java_validator` backend enforces that (the native
structural check cannot see a missing primitive code, which may also arrive as `_status`).
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.task.conftest import TASK_PERMS
from tests.integration.task.support import (
    BASE,
    BUSINESS,
    concept,
    create_encounter,
    create_group,
    create_location,
    create_organization,
    create_patient,
    create_practitioner,
    create_service_request,
    create_task,
    encounter_body,
    full_body,
    group_body,
    service_request_body,
    task_body,
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


def _as_user(sub="u-test", org_id="org-test", permissions=TASK_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client) -> tuple[int, dict]:
    patient = await create_patient(client)
    encounter = await create_encounter(
        client, encounter_body(subject={"reference": f"Patient/{patient}"})
    )
    practitioner = await create_practitioner(client)
    organization = await create_organization(client)
    location = await create_location(client)
    service_request = await create_service_request(
        client, service_request_body(patient)
    )
    parent = await create_task(client, task_body())
    body = full_body(
        patient,
        encounter,
        practitioner,
        organization,
        location,
        service_request,
        parent,
    )
    return await create_task(client, body), body


# -- Create ---------------------------------------------------------------------------------


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=task_body())
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "Task" and data["status"] == "requested"
    assert data["intent"] == "order"


async def test_create_full_round_trip(client):
    task, body = await _full(client)
    data = (await client.get(f"{BASE}/{task}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_elements_nothing_searches_on(client):
    """`description`, `statusReason`, `location`, `reasonCode`, `insurance`, `note`,
    `restriction` and every `input` / `output` (with its open `value[x]`) live only in
    `content`."""
    task, _ = await _full(client)
    data = (await client.get(f"{BASE}/{task}")).json()
    assert data["description"] == "Collect a blood sample"
    assert data["restriction"]["repetitions"] == 2
    assert data["input"][1]["valueQuantity"]["unit"] == "mL"
    assert data["input"][2]["valueBoolean"] is True
    assert data["output"][0]["valueReference"]["reference"].startswith("Patient/")
    assert data["note"][0]["text"] == "Fasting required"
    assert data["insurance"] == [{"reference": "Coverage/9"}]
    assert data["for"]["reference"].startswith("Patient/")


@pytest.mark.parametrize(
    "status",
    [
        "draft",
        "requested",
        "received",
        "accepted",
        "rejected",
        "ready",
        "cancelled",
        "in-progress",
        "on-hold",
        "failed",
        "completed",
        "entered-in-error",
    ],
)
async def test_create_every_status_round_trips(client, status):
    resp = await client.post(BASE + "/", json=task_body(status=status))
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


@pytest.mark.parametrize(
    "intent",
    [
        "unknown",
        "proposal",
        "plan",
        "order",
        "original-order",
        "reflex-order",
        "filler-order",
        "instance-order",
        "option",
    ],
)
async def test_create_every_intent_round_trips(client, intent):
    resp = await client.post(BASE + "/", json=task_body(intent=intent))
    assert resp.status_code == 201, resp.text
    assert resp.json()["intent"] == intent


@pytest.mark.parametrize("priority", ["routine", "urgent", "asap", "stat"])
async def test_create_every_priority_round_trips(client, priority):
    resp = await client.post(BASE + "/", json=task_body(priority=priority))
    assert resp.status_code == 201, resp.text
    assert resp.json()["priority"] == priority


async def test_create_ignores_server_managed_id_and_meta(client):
    body = task_body(id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"})
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client):
    for bad in (
        {"status": "robot"},
        {"intent": "robot"},
        {"priority": "now"},
        {"code": "x"},
        {"businessStatus": "x"},
        {"identifier": {"value": "x"}},
        {"groupIdentifier": "x"},
        {"basedOn": {"reference": "ServiceRequest/1"}},
        {"partOf": {"reference": "Task/1"}},
        {"focus": "ServiceRequest/1"},
        {"for": "Patient/1"},
        {"encounter": "Encounter/1"},
        {"executionPeriod": "today"},
        {"authoredOn": "yesterday"},
        {"lastModified": 5},
        {"requester": "Practitioner/1"},
        {"owner": "Practitioner/1"},
        {"performerType": {"text": "x"}},
        {"restriction": "x"},
        {"restriction": {"repetitions": "twice"}},
        {"input": {"type": {"text": "x"}}},
        {"output": "x"},
        {"description": 5},
    ):
        resp = await client.post(BASE + "/", json=task_body(**bad))
        assert resp.status_code == 422, (bad, resp.text)


async def test_create_non_fhir_key_rejected(client, native_validation):
    resp = await client.post(BASE + "/", json=task_body(not_a_fhir_element=1))
    assert resp.status_code == 422


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in ({"for_id": 5}, {"authored_on": "2026-01-01"}, {"org_id": "x"}):
        resp = await client.post(BASE + "/", json=task_body(**stale))
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(BASE + "/", json=task_body(resourceType="Patient"))
    assert resp.status_code == 422


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=task_body())).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# -- Create: existence checks on local references --------------------------------------------


async def _created(client, **extra) -> int:
    return (await client.post(BASE + "/", json=task_body(**extra))).status_code


async def test_create_for_must_exist(client):
    patient = await create_patient(client)
    group = await create_group(client, group_body())
    assert await _created(client, **{"for": {"reference": f"Patient/{patient}"}}) == 201
    assert await _created(client, **{"for": {"reference": f"Group/{group}"}}) == 201
    assert await _created(client, **{"for": {"reference": "Patient/999999"}}) == 422
    assert await _created(client, **{"for": {"reference": "Group/999999"}}) == 422


async def test_create_for_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    assert await _created(client, **{"for": {"reference": f"Patient/{theirs}"}}) == 422


async def test_create_focus_and_based_on_are_reference_any(client):
    patient = await create_patient(client)
    sr = await create_service_request(client, service_request_body(patient))
    assert await _created(client, focus={"reference": f"ServiceRequest/{sr}"}) == 201
    assert await _created(client, focus={"reference": "ServiceRequest/999999"}) == 422
    assert (
        await _created(client, basedOn=[{"reference": f"ServiceRequest/{sr}"}]) == 201
    )
    assert (
        await _created(client, basedOn=[{"reference": "ServiceRequest/999999"}]) == 422
    )
    # a type this server does not have is stored as sent
    assert await _created(client, focus={"reference": "Device/999999"}) == 201


async def test_create_part_of_must_exist(client):
    parent = await create_task(client, task_body())
    assert await _created(client, partOf=[{"reference": f"Task/{parent}"}]) == 201
    assert await _created(client, partOf=[{"reference": "Task/999999"}]) == 422


async def test_create_encounter_requester_owner_location_must_exist(client):
    patient = await create_patient(client)
    encounter = await create_encounter(
        client, encounter_body(subject={"reference": f"Patient/{patient}"})
    )
    practitioner = await create_practitioner(client)
    location = await create_location(client)
    ok = {
        "encounter": {"reference": f"Encounter/{encounter}"},
        "requester": {"reference": f"Practitioner/{practitioner}"},
        "owner": {"reference": f"Practitioner/{practitioner}"},
        "location": {"reference": f"Location/{location}"},
    }
    assert await _created(client, **ok) == 201
    for element, reference in (
        ("encounter", "Encounter/999999"),
        ("requester", "Practitioner/999999"),
        ("owner", "Practitioner/999999"),
        ("location", "Location/999999"),
    ):
        assert await _created(client, **{element: {"reference": reference}}) == 422, (
            element
        )


async def test_create_restriction_recipient_note_author_and_assigner_must_exist(client):
    practitioner = await create_practitioner(client)
    organization = await create_organization(client)
    ok = {
        "restriction": {"recipient": [{"reference": f"Practitioner/{practitioner}"}]},
        "note": [
            {
                "text": "x",
                "authorReference": {"reference": f"Practitioner/{practitioner}"},
            }
        ],
        "identifier": [
            {"value": "1", "assigner": {"reference": f"Organization/{organization}"}}
        ],
    }
    assert await _created(client, **ok) == 201
    for bad in (
        {"restriction": {"recipient": [{"reference": "Practitioner/999999"}]}},
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
        assert await _created(client, **bad) == 422, bad


async def test_create_input_and_output_references_are_checked(client):
    """A `valueReference` at any depth is checked by the shared rule."""
    patient = await create_patient(client)
    ok = {
        "input": [
            {
                "type": {"text": "t"},
                "valueReference": {"reference": f"Patient/{patient}"},
            }
        ]
    }
    assert await _created(client, **ok) == 201
    bad = {
        "output": [
            {"type": {"text": "t"}, "valueReference": {"reference": "Patient/999999"}}
        ]
    }
    assert await _created(client, **bad) == 422


async def test_create_unmodeled_targets_are_not_checked(client):
    """Coverage and Provenance are not resources on this server: stored as sent."""
    body = task_body(
        insurance=[{"reference": "Coverage/999999"}],
        relevantHistory=[{"reference": "Provenance/999999"}],
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["insurance"] == [{"reference": "Coverage/999999"}]


async def test_create_absolute_and_logical_references_not_resolved(client):
    absolute = "https://other.example.org/fhir/Patient/7"
    resp = await client.post(
        BASE + "/", json=task_body(**{"for": {"reference": absolute}})
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["for"] == {"reference": absolute}
    logical = {"identifier": {"system": "urn:mrn", "value": "M-9"}, "display": "Jane"}
    resp = await client.post(BASE + "/", json=task_body(owner=logical))
    assert resp.status_code == 201, resp.text
    assert resp.json()["owner"] == logical


# -- Read -----------------------------------------------------------------------------------


async def test_get_by_id(client):
    task, _ = await _full(client)
    resp = await client.get(f"{BASE}/{task}")
    assert resp.status_code == 200 and resp.json()["id"] == str(task)


async def test_get_is_fhir_regardless_of_accept(client):
    task = await create_task(client, task_body())
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{task}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "Task"


async def test_xml_only_accept_is_406(client):
    task = await create_task(client, task_body())
    resp = await client.get(
        f"{BASE}/{task}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Patch ----------------------------------------------------------------------------------


async def test_patch_scalar_keeps_the_rest(client):
    task, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{task}", json={"status": "completed", "description": "Done"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "completed"
    assert resp.json()["description"] == "Done"
    assert resp.json()["intent"] == "order"  # untouched
    assert resp.json()["for"]["reference"].startswith("Patient/")  # untouched


async def test_patch_reindexes_search(client):
    task, _ = await _full(client)
    patched = await client.patch(
        f"{BASE}/{task}",
        json={
            "status": "completed",
            "intent": "plan",
            "priority": "stat",
            "businessStatus": concept(BUSINESS, "done"),
            "authoredOn": "2027-03-03T00:00:00Z",
            "lastModified": "2027-03-04T00:00:00Z",
            "executionPeriod": {"start": "2027-03-03T00:00:00Z"},
            "groupIdentifier": {"system": "urn:g", "value": "GRP-2"},
        },
    )
    assert patched.status_code == 200, patched.text
    for param, old, new in (
        ("status", "in-progress", "completed"),
        ("intent", "order", "plan"),
        ("priority", "urgent", "stat"),
        ("business-status", "specimen-collected", "done"),
        ("authored-on", "2026-01-15", "2027-03-03"),
        ("modified", "2026-01-15", "2027-03-04"),
        ("group-identifier", "GRP-1", "GRP-2"),
    ):
        assert task not in _ids(
            (await client.get(BASE + "/", params={param: old})).json()
        ), param
        assert task in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param


async def test_patch_replaces_lists_and_empty_clears(client):
    task, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{task}",
        json={"identifier": [], "basedOn": [], "partOf": [], "performerType": []},
    )
    for gone in ("identifier", "basedOn", "partOf", "performerType"):
        assert gone not in resp.json()
    assert resp.json()["status"] == "in-progress"  # untouched
    for param in ("identifier", "based-on", "part-of", "performer"):
        assert task in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_clears_for_focus_and_owner(client):
    task, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{task}", json={"for": None, "focus": None, "owner": None}
    )
    assert all(k not in resp.json() for k in ("for", "focus", "owner"))
    for param in ("subject", "patient", "focus", "owner"):
        assert task in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client):
    task = await create_task(client, task_body())
    resp = await client.patch(
        f"{BASE}/{task}", json={"owner": {"reference": "Practitioner/999999"}}
    )
    assert resp.status_code == 422
    assert "owner" not in (await client.get(f"{BASE}/{task}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    task = await create_task(client, task_body())
    assert (
        await client.patch(f"{BASE}/{task}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{task}")).json()["status"] == "requested"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "completed"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Delete ---------------------------------------------------------------------------------


async def test_delete(client):
    task, _ = await _full(client)
    assert (await client.delete(f"{BASE}/{task}")).status_code == 204
    assert (await client.get(f"{BASE}/{task}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "T-1001"),
        ("business-status", "specimen-collected"),
        ("group-identifier", "GRP-1"),
        ("code", "fulfill"),
    ):
        assert task not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Auth -----------------------------------------------------------------------------------


async def test_create_without_permission(client):
    _as_user(permissions=["task:read"])
    assert (await client.post(BASE + "/", json=task_body())).status_code == 403


async def test_org_less_token_rejected(client):
    task = await create_task(client, task_body())

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": TASK_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=task_body())).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{task}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    task = await create_task(client, task_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{task}"),
            await other_client.patch(f"{BASE}/{task}", json={"status": "completed"}),
            await other_client.delete(f"{BASE}/{task}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_task(
        client, task_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}])
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()


async def test_task_is_checked_where_it_can_be_named(client):
    """CarePlan.activity.reference can be a Task and DetectedIssue.implicated is Reference(Any):
    a relative Task there must exist (422 otherwise)."""
    task = await create_task(client, task_body())
    plans = "/api/fhir/v1/care-plans/"
    subject = {"reference": "https://other.example.org/fhir/Patient/1"}
    ok = {
        "status": "active",
        "intent": "plan",
        "subject": subject,
        "activity": [{"reference": {"reference": f"Task/{task}"}}],
    }
    assert (await client.post(plans, json=ok)).status_code == 201
    missing = {**ok, "activity": [{"reference": {"reference": "Task/999999"}}]}
    assert (await client.post(plans, json=missing)).status_code == 422
    issues = "/api/fhir/v1/detected-issues/"
    ok = {"status": "final", "implicated": [{"reference": f"Task/{task}"}]}
    assert (await client.post(issues, json=ok)).status_code == 201
    missing = {"status": "final", "implicated": [{"reference": "Task/999999"}]}
    assert (await client.post(issues, json=missing)).status_code == 422
