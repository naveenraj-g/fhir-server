"""Core communication-request endpoint coverage.

CommunicationRequest is stored content-based (like Communication, Task, Goal and the other rebuilt
resources): the request body (genuine FHIR R4 CommunicationRequest JSON) is validated and stored
whole in `content`, every response is FHIR R4 (`application/fhir+json`, regardless of Accept), and
only the FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/communicationrequest.html#search). R4 defines no search parameter
for `statusReason`, `doNotPerform`, `about`, `payload`, `reasonCode`, `reasonReference` or `note`,
so those live only in `content`.

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence checks on every local reference (`subject`, `encounter`,
`requester`, `sender`, `recipient`, `basedOn`, `replaces`, `about`, `reasonReference`,
`payload.contentReference`, a note's `authorReference` and every identifier's `assigner`). Search
lives in test_search.py.

R4 requires `status`; the native validator cannot see a missing primitive `status`, which only the
`java_validator` backend rejects.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.communication_request.conftest import COMMUNICATION_REQUEST_PERMS
from tests.integration.communication_request.support import (
    BASE,
    CATEGORY,
    communication_body,
    communication_request_body,
    concept,
    create_communication,
    create_communication_request,
    create_encounter,
    create_group,
    create_organization,
    create_patient,
    create_practitioner,
    create_service_request,
    encounter_body,
    full_body,
    group_body,
    service_request_body,
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


def _as_user(sub="u-test", org_id="org-test", permissions=COMMUNICATION_REQUEST_PERMS):
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
    service_request = await create_service_request(
        client, service_request_body(patient)
    )
    replaced = await create_communication_request(client, communication_request_body())
    body = full_body(
        patient, encounter, practitioner, organization, service_request, replaced
    )
    return await create_communication_request(client, body), body


async def _created(client, **extra) -> int:
    return (
        await client.post(BASE + "/", json=communication_request_body(**extra))
    ).status_code


# -- Create ---------------------------------------------------------------------------------


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=communication_request_body())
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "CommunicationRequest" and data["status"] == "active"


async def test_create_full_round_trip(client):
    request, body = await _full(client)
    data = (await client.get(f"{BASE}/{request}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_elements_nothing_searches_on(client):
    """`statusReason`, `doNotPerform`, `about`, `payload`, `reasonCode`, `reasonReference` and
    `note` live only in `content`."""
    request, _ = await _full(client)
    data = (await client.get(f"{BASE}/{request}")).json()
    assert data["doNotPerform"] is False
    assert data["statusReason"]["coding"][0]["code"] == "approved"
    assert data["payload"][0]["contentString"] == "Please book your follow-up visit."
    assert data["payload"][1]["contentAttachment"]["title"] == "leaflet"
    assert data["payload"][2]["contentReference"]["reference"].startswith("Patient/")
    assert data["reasonReference"] == [{"reference": "Device/9"}]
    assert data["note"][0]["text"] == "Call twice"


async def test_create_occurrence_period_is_kept(client):
    resp = await client.post(
        BASE + "/",
        json=communication_request_body(
            occurrencePeriod={"start": "2026-02-01", "end": "2026-02-28"}
        ),
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["occurrencePeriod"] == {
        "start": "2026-02-01",
        "end": "2026-02-28",
    }


@pytest.mark.parametrize(
    "status",
    [
        "draft",
        "active",
        "on-hold",
        "revoked",
        "completed",
        "entered-in-error",
        "unknown",
    ],
)
async def test_create_every_status_round_trips(client, status):
    resp = await client.post(BASE + "/", json=communication_request_body(status=status))
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


@pytest.mark.parametrize("priority", ["routine", "urgent", "asap", "stat"])
async def test_create_every_priority_round_trips(client, priority):
    resp = await client.post(
        BASE + "/", json=communication_request_body(priority=priority)
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["priority"] == priority


async def test_create_ignores_server_managed_id_and_meta(client):
    body = communication_request_body(
        id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"}
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client):
    for bad in (
        {"status": "robot"},
        {"priority": "now"},
        {"category": {"text": "x"}},
        {"medium": "x"},
        {"subject": "Patient/1"},
        {"encounter": "Encounter/1"},
        {"authoredOn": "yesterday"},
        {"occurrenceDateTime": 5},
        {"doNotPerform": "maybe"},
        {"recipient": {"reference": "Patient/1"}},
        {"sender": "Practitioner/1"},
        {"requester": "Practitioner/1"},
        {"basedOn": {"reference": "ServiceRequest/1"}},
        {"replaces": "CommunicationRequest/1"},
        {"groupIdentifier": "G-1"},
        {"payload": {"contentString": "x"}},
        {"payload": [{"contentString": 5}]},
        {"note": "x"},
        {"identifier": {"value": "x"}},
    ):
        resp = await client.post(BASE + "/", json=communication_request_body(**bad))
        assert resp.status_code == 422, (bad, resp.text)


async def test_create_non_fhir_key_rejected(client, native_validation):
    resp = await client.post(
        BASE + "/", json=communication_request_body(not_a_fhir_element=1)
    )
    assert resp.status_code == 422


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in ({"topic_text": "x"}, {"sender_id": 5}, {"org_id": "x"}):
        resp = await client.post(BASE + "/", json=communication_request_body(**stale))
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(
        BASE + "/", json=communication_request_body(resourceType="Patient")
    )
    assert resp.status_code == 422


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=communication_request_body())).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# -- Create: existence checks on local references --------------------------------------------


async def test_create_subject_must_exist(client):
    patient = await create_patient(client)
    group = await create_group(client, group_body())
    assert await _created(client, subject={"reference": f"Patient/{patient}"}) == 201
    assert await _created(client, subject={"reference": f"Group/{group}"}) == 201
    assert await _created(client, subject={"reference": "Patient/999999"}) == 422
    assert await _created(client, subject={"reference": "Group/999999"}) == 422


async def test_create_subject_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    assert await _created(client, subject={"reference": f"Patient/{theirs}"}) == 422


async def test_create_encounter_requester_sender_and_recipient_must_exist(client):
    patient = await create_patient(client)
    encounter = await create_encounter(
        client, encounter_body(subject={"reference": f"Patient/{patient}"})
    )
    practitioner = await create_practitioner(client)
    organization = await create_organization(client)
    ok = {
        "encounter": {"reference": f"Encounter/{encounter}"},
        "requester": {"reference": f"Practitioner/{practitioner}"},
        "sender": {"reference": f"Practitioner/{practitioner}"},
        "recipient": [
            {"reference": f"Patient/{patient}"},
            {"reference": f"Organization/{organization}"},
        ],
    }
    assert await _created(client, **ok) == 201
    for bad in (
        {"encounter": {"reference": "Encounter/999999"}},
        {"requester": {"reference": "Practitioner/999999"}},
        {"sender": {"reference": "Practitioner/999999"}},
        {"recipient": [{"reference": "Patient/999999"}]},
    ):
        assert await _created(client, **bad) == 422, bad


async def test_create_based_on_replaces_and_about_must_exist(client):
    patient = await create_patient(client)
    sr = await create_service_request(client, service_request_body(patient))
    replaced = await create_communication_request(client, communication_request_body())
    ok = {
        "basedOn": [{"reference": f"ServiceRequest/{sr}"}],
        "replaces": [{"reference": f"CommunicationRequest/{replaced}"}],
        "about": [{"reference": f"Patient/{patient}"}],
    }
    assert await _created(client, **ok) == 201
    for bad in (
        {"basedOn": [{"reference": "ServiceRequest/999999"}]},
        {"replaces": [{"reference": "CommunicationRequest/999999"}]},
        {"about": [{"reference": "Patient/999999"}]},
    ):
        assert await _created(client, **bad) == 422, bad
    # a type this server does not have is stored as sent
    assert await _created(client, basedOn=[{"reference": "DeviceRequest/9"}]) == 201


async def test_create_payload_reference_note_author_and_assigner_must_exist(client):
    patient = await create_patient(client)
    practitioner = await create_practitioner(client)
    organization = await create_organization(client)
    ok = {
        "payload": [{"contentReference": {"reference": f"Patient/{patient}"}}],
        "note": [
            {
                "text": "x",
                "authorReference": {"reference": f"Practitioner/{practitioner}"},
            }
        ],
        "identifier": [
            {"value": "1", "assigner": {"reference": f"Organization/{organization}"}}
        ],
        "groupIdentifier": {
            "value": "G",
            "assigner": {"reference": f"Organization/{organization}"},
        },
    }
    assert await _created(client, **ok) == 201
    for bad in (
        {"payload": [{"contentReference": {"reference": "Patient/999999"}}]},
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
        {
            "groupIdentifier": {
                "value": "G",
                "assigner": {"reference": "Organization/999999"},
            }
        },
    ):
        assert await _created(client, **bad) == 422, bad


async def test_create_unmodeled_targets_are_not_checked(client):
    """Device and DeviceRequest are not resources on this server: stored as sent."""
    body = communication_request_body(
        sender={"reference": "Device/999999"},
        requester={"reference": "Device/999997"},
        recipient=[{"reference": "Device/999998"}],
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["sender"] == {"reference": "Device/999999"}


async def test_create_absolute_and_logical_references_not_resolved(client):
    absolute = "https://other.example.org/fhir/Patient/7"
    resp = await client.post(
        BASE + "/", json=communication_request_body(subject={"reference": absolute})
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == {"reference": absolute}
    logical = {"identifier": {"system": "urn:mrn", "value": "M-9"}, "display": "Jane"}
    resp = await client.post(
        BASE + "/", json=communication_request_body(requester=logical)
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["requester"] == logical


# -- Read -----------------------------------------------------------------------------------


async def test_get_by_id(client):
    request, _ = await _full(client)
    resp = await client.get(f"{BASE}/{request}")
    assert resp.status_code == 200 and resp.json()["id"] == str(request)


async def test_get_is_fhir_regardless_of_accept(client):
    request = await create_communication_request(client, communication_request_body())
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{request}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "CommunicationRequest"


async def test_xml_only_accept_is_406(client):
    request = await create_communication_request(client, communication_request_body())
    resp = await client.get(
        f"{BASE}/{request}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Patch ----------------------------------------------------------------------------------


async def test_patch_scalar_keeps_the_rest(client):
    request, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{request}", json={"status": "on-hold", "priority": "stat"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "on-hold" and resp.json()["priority"] == "stat"
    assert resp.json()["doNotPerform"] is False  # untouched
    assert resp.json()["subject"]["reference"].startswith("Patient/")  # untouched


async def test_patch_reindexes_search(client):
    request, _ = await _full(client)
    patched = await client.patch(
        f"{BASE}/{request}",
        json={
            "status": "on-hold",
            "priority": "stat",
            "category": [concept(CATEGORY, "alert")],
            "authoredOn": "2027-03-03T00:00:00Z",
            "occurrenceDateTime": "2027-04-04T00:00:00Z",
            "groupIdentifier": {"system": "urn:groups", "value": "G-2"},
        },
    )
    assert patched.status_code == 200, patched.text
    for param, old, new in (
        ("status", "active", "on-hold"),
        ("priority", "urgent", "stat"),
        ("category", "reminder", "alert"),
        ("authored", "2026-01-15", "2027-03-03"),
        ("occurrence", "2026-02-01", "2027-04-04"),
        ("group-identifier", "urn:groups|G-1", "urn:groups|G-2"),
    ):
        assert request not in _ids(
            (await client.get(BASE + "/", params={param: old})).json()
        ), param
        assert request in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param


async def test_patch_replaces_lists_and_empty_clears(client):
    request, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{request}",
        json={
            "identifier": [],
            "basedOn": [],
            "replaces": [],
            "recipient": [],
            "category": [],
        },
    )
    for gone in ("identifier", "basedOn", "replaces", "recipient", "category"):
        assert gone not in resp.json()
    assert resp.json()["status"] == "active"  # untouched
    for param in ("identifier", "based-on", "replaces", "recipient", "category"):
        assert request in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_clears_subject_requester_sender_and_dates(client):
    request, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{request}",
        json={
            "subject": None,
            "requester": None,
            "sender": None,
            "authoredOn": None,
            "occurrenceDateTime": None,
            "groupIdentifier": None,
            "priority": None,
        },
    )
    assert all(
        k not in resp.json()
        for k in (
            "subject",
            "requester",
            "sender",
            "authoredOn",
            "occurrenceDateTime",
            "groupIdentifier",
            "priority",
        )
    )
    for param in (
        "subject",
        "patient",
        "requester",
        "sender",
        "authored",
        "occurrence",
        "group-identifier",
        "priority",
    ):
        assert request in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client):
    request = await create_communication_request(client, communication_request_body())
    resp = await client.patch(
        f"{BASE}/{request}", json={"sender": {"reference": "Practitioner/999999"}}
    )
    assert resp.status_code == 422
    assert "sender" not in (await client.get(f"{BASE}/{request}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    request = await create_communication_request(client, communication_request_body())
    assert (
        await client.patch(f"{BASE}/{request}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{request}")).json()["status"] == "active"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "active"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Delete ---------------------------------------------------------------------------------


async def test_delete(client):
    request, _ = await _full(client)
    assert (await client.delete(f"{BASE}/{request}")).status_code == 204
    assert (await client.get(f"{BASE}/{request}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "CR-1001"),
        ("category", "reminder"),
        ("group-identifier", "urn:groups|G-1"),
    ):
        assert request not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Auth -----------------------------------------------------------------------------------


async def test_create_without_permission(client):
    _as_user(permissions=["communication_request:read"])
    assert (
        await client.post(BASE + "/", json=communication_request_body())
    ).status_code == 403


async def test_org_less_token_rejected(client):
    request = await create_communication_request(client, communication_request_body())

    async def _no_org(request_: Request):
        request_.state.user = {
            "sub": "u-test",
            "permissions": COMMUNICATION_REQUEST_PERMS,
        }

    app.dependency_overrides[get_current_user] = _no_org
    assert (
        await client.post(BASE + "/", json=communication_request_body())
    ).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{request}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    request = await create_communication_request(client, communication_request_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{request}"),
            await other_client.patch(f"{BASE}/{request}", json={"status": "active"}),
            await other_client.delete(f"{BASE}/{request}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_communication_request(
        client,
        communication_request_body(
            identifier=[{"system": "urn:t", "value": "TenantAOnly"}]
        ),
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()


async def test_communication_request_is_checked_where_it_can_be_named(client):
    """Communication.basedOn is Reference(Any) and DetectedIssue.implicated is too: a relative
    CommunicationRequest there must exist (422 otherwise)."""
    request = await create_communication_request(client, communication_request_body())
    communications = "/api/fhir/v1/communications/"
    ok = communication_body(basedOn=[{"reference": f"CommunicationRequest/{request}"}])
    assert (await client.post(communications, json=ok)).status_code == 201
    missing = communication_body(basedOn=[{"reference": "CommunicationRequest/999999"}])
    assert (await client.post(communications, json=missing)).status_code == 422
    issues = "/api/fhir/v1/detected-issues/"
    ok = {
        "status": "final",
        "implicated": [{"reference": f"CommunicationRequest/{request}"}],
    }
    assert (await client.post(issues, json=ok)).status_code == 201
    missing = {
        "status": "final",
        "implicated": [{"reference": "CommunicationRequest/999999"}],
    }
    assert (await client.post(issues, json=missing)).status_code == 422


async def test_communication_based_on_a_request_is_searchable_from_the_request(client):
    request = await create_communication_request(client, communication_request_body())
    communication = await create_communication(
        client,
        communication_body(basedOn=[{"reference": f"CommunicationRequest/{request}"}]),
    )
    resp = await client.get(
        BASE + "/",
        params={"_id": str(request), "_revinclude": "Communication:based-on"},
    )
    assert resp.status_code == 200, resp.text
    included = {
        int(e["resource"]["id"])
        for e in resp.json()["entry"]
        if e["search"]["mode"] == "include"
        and e["resource"]["resourceType"] == "Communication"
    }
    assert included == {communication}
