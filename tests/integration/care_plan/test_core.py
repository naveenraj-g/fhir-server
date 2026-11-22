"""Core care plan endpoint coverage.

CarePlan is stored Medplum-style (like Patient, Encounter, Condition, ServiceRequest, CareTeam,
Group and the other content-based resources): the request body (genuine FHIR R4 CarePlan JSON) is
validated and stored whole in `content`, every response is FHIR R4 (`application/fhir+json`,
regardless of Accept), and only the FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/careplan.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence checks on every local reference (`subject`, `encounter`, `basedOn` /
`replaces` / `partOf`, `author` / `contributor`, `careTeam`, `addresses`, `supportingInfo`, the
activities' references, performers, locations, reasons and products, note authors and every
identifier's `assigner`). Search lives in test_search.py.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.care_plan.conftest import CARE_PLAN_PERMS
from tests.integration.care_plan.support import (
    BASE,
    SCT,
    appointment_body,
    care_plan_body,
    care_team_body,
    concept,
    condition_body,
    create_appointment,
    create_care_plan,
    create_care_team,
    create_condition,
    create_encounter,
    create_group,
    create_healthcare_service,
    create_location,
    create_medication,
    create_medication_request,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_related_person,
    create_service_request,
    encounter_body,
    full_body,
    group_body,
    medication_body,
    medication_request_body,
    related_person_body,
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


def _as_user(sub="u-test", org_id="org-test", permissions=CARE_PLAN_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client) -> tuple[int, dict]:
    organization = await create_organization(client)
    patient = await create_patient(client)
    practitioner = await create_practitioner(client)
    encounter = await create_encounter(client, encounter_body())
    condition = await create_condition(client, condition_body(patient))
    care_team = await create_care_team(client, care_team_body())
    service_request = await create_service_request(
        client, service_request_body(patient)
    )
    location = await create_location(client)
    medication = await create_medication(client, medication_body())
    other = await create_care_plan(client, care_plan_body())
    body = full_body(
        organization,
        patient,
        practitioner,
        encounter,
        condition,
        care_team,
        service_request,
        location,
        medication,
        other,
    )
    return await create_care_plan(client, body), body


# -- Create ---------------------------------------------------------------------------------


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=care_plan_body())
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "CarePlan"
    assert data["status"] == "active" and data["intent"] == "plan"


async def test_create_full_round_trip(client):
    care_plan, body = await _full(client)
    data = (await client.get(f"{BASE}/{care_plan}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_elements_nothing_searches_on(client):
    """`title`, `description`, `created`, `author`, `contributor`, `supportingInfo`, `note` and
    every activity element no parameter reads live only in `content`."""
    care_plan, _ = await _full(client)
    data = (await client.get(f"{BASE}/{care_plan}")).json()
    assert data["title"] == "Diabetes management plan"
    assert data["description"].startswith("Long-term")
    assert data["created"] == "2026-01-01T09:00:00Z"
    assert data["author"]["reference"].startswith("Practitioner/")
    assert data["supportingInfo"][0]["reference"].startswith("Condition/")
    assert data["note"][0]["text"] == "Review monthly."
    first, second = data["activity"]
    assert first["outcomeCodeableConcept"][0]["coding"][0]["code"] == "385669000"
    assert first["progress"][0]["text"] == "On track"
    detail = second["detail"]
    assert detail["status"] == "in-progress" and detail["doNotPerform"] is False
    assert detail["dailyAmount"] == {"value": 2, "unit": "mg"}
    assert detail["productReference"]["reference"].startswith("Medication/")
    assert detail["description"] == "Daily walk."


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
    resp = await client.post(BASE + "/", json=care_plan_body(status=status))
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


@pytest.mark.parametrize("intent", ["proposal", "plan", "order", "option"])
async def test_create_every_intent_round_trips(client, intent):
    resp = await client.post(BASE + "/", json=care_plan_body(intent=intent))
    assert resp.status_code == 201, resp.text
    assert resp.json()["intent"] == intent


@pytest.mark.parametrize(
    "status",
    [
        "not-started",
        "scheduled",
        "in-progress",
        "on-hold",
        "completed",
        "cancelled",
        "stopped",
        "unknown",
        "entered-in-error",
    ],
)
async def test_create_every_activity_status_round_trips(client, status):
    activity = [{"detail": {"status": status}}]
    resp = await client.post(BASE + "/", json=care_plan_body(activity=activity))
    assert resp.status_code == 201, resp.text
    assert resp.json()["activity"] == activity


async def test_create_each_scheduled_choice_round_trips(client):
    for scheduled in (
        {"scheduledPeriod": {"start": "2026-01-01"}},
        {"scheduledTiming": {"event": ["2026-01-01T08:00:00Z"]}},
        {"scheduledString": "next week"},
    ):
        activity = [{"detail": {"status": "scheduled", **scheduled}}]
        resp = await client.post(BASE + "/", json=care_plan_body(activity=activity))
        assert resp.status_code == 201, (scheduled, resp.text)
        assert resp.json()["activity"] == activity


async def test_create_ignores_server_managed_id_and_meta(client):
    body = care_plan_body(id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"})
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client):
    for bad in (
        {"status": "retired"},
        {"intent": "directive"},
        {"title": 5},
        {"category": {"text": "x"}},
        {"category": ["x"]},
        {"subject": "Patient/1"},
        {"encounter": "Encounter/1"},
        {"period": "2026"},
        {"created": 5},
        {"author": "Practitioner/1"},
        {"identifier": {"value": "x"}},
        {"basedOn": {"reference": "CarePlan/1"}},
        {"instantiatesCanonical": "http://x"},
        {"instantiatesUri": "http://x"},
        {"careTeam": {"reference": "CareTeam/1"}},
        {"addresses": {"reference": "Condition/1"}},
        {"goal": {"reference": "Goal/1"}},
        {"activity": {"detail": {"status": "scheduled"}}},
        {"activity": [{"reference": "Appointment/1"}]},
        {"activity": [{"detail": {"status": "done"}}]},
        {"activity": [{"detail": {"kind": "Observation"}}]},
        {"activity": [{"detail": {"doNotPerform": "no"}}]},
        {"activity": [{"detail": {"scheduledPeriod": "2026"}}]},
        {"activity": [{"detail": {"performer": {"reference": "Practitioner/1"}}}]},
        {"activity": [{"detail": {"location": "Location/1"}}]},
        {"note": {"text": "x"}},
    ):
        resp = await client.post(BASE + "/", json=care_plan_body(**bad))
        assert resp.status_code == 422, (bad, resp.text)


async def test_create_non_fhir_key_rejected(client, native_validation):
    resp = await client.post(BASE + "/", json=care_plan_body(not_a_fhir_element=1))
    assert resp.status_code == 422


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in ({"subject_id": 1}, {"org_id": "x"}, {"user_id": "x"}):
        resp = await client.post(BASE + "/", json={**care_plan_body(), **stale})
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(BASE + "/", json=care_plan_body(resourceType="Patient"))
    assert resp.status_code == 422


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=care_plan_body())).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# -- Create: existence checks on local references --------------------------------------------


async def _created_ok(client, **extra) -> bool:
    resp = await client.post(BASE + "/", json=care_plan_body(**extra))
    assert resp.status_code in (201, 422), resp.text
    return resp.status_code == 201


async def test_create_subject_must_exist(client):
    patient = await create_patient(client)
    group = await create_group(client, group_body())
    for ref in (f"Patient/{patient}", f"Group/{group}"):
        body = care_plan_body()
        body["subject"] = {"reference": ref}
        assert (await client.post(BASE + "/", json=body)).status_code == 201, ref
    for missing in ("Patient/999999", "Group/999999"):
        body = care_plan_body()
        body["subject"] = {"reference": missing}
        assert (await client.post(BASE + "/", json=body)).status_code == 422, missing


async def test_create_encounter_must_exist(client):
    encounter = await create_encounter(client, encounter_body())
    assert await _created_ok(client, encounter={"reference": f"Encounter/{encounter}"})
    assert not await _created_ok(client, encounter={"reference": "Encounter/999999"})


async def test_create_care_plan_references_must_exist(client):
    first = await create_care_plan(client, care_plan_body())
    for element in ("basedOn", "replaces", "partOf"):
        assert await _created_ok(
            client, **{element: [{"reference": f"CarePlan/{first}"}]}
        )
        assert not await _created_ok(
            client, **{element: [{"reference": "CarePlan/999999"}]}
        ), element


async def test_create_author_and_contributors_must_exist(client):
    practitioner = await create_practitioner(client)
    role = await create_practitioner_role(client)
    patient = await create_patient(client)
    related = await create_related_person(client, related_person_body(patient))
    organization = await create_organization(client)
    team = await create_care_team(client, care_team_body())
    for ref in (
        f"Practitioner/{practitioner}",
        f"PractitionerRole/{role}",
        f"Patient/{patient}",
        f"RelatedPerson/{related}",
        f"Organization/{organization}",
        f"CareTeam/{team}",
    ):
        assert await _created_ok(client, author={"reference": ref}), ref
        assert await _created_ok(client, contributor=[{"reference": ref}]), ref
    for missing in (
        "Practitioner/999999",
        "PractitionerRole/999999",
        "Patient/999999",
        "RelatedPerson/999999",
        "Organization/999999",
        "CareTeam/999999",
    ):
        assert not await _created_ok(client, author={"reference": missing}), missing
        assert not await _created_ok(client, contributor=[{"reference": missing}]), (
            missing
        )
    # A Device author is not a resource here: stored as sent.
    assert await _created_ok(client, author={"reference": "Device/5"})


async def test_create_care_team_and_addresses_must_exist(client):
    patient = await create_patient(client)
    team = await create_care_team(client, care_team_body())
    condition = await create_condition(client, condition_body(patient))
    assert await _created_ok(client, careTeam=[{"reference": f"CareTeam/{team}"}])
    assert not await _created_ok(client, careTeam=[{"reference": "CareTeam/999999"}])
    assert await _created_ok(
        client, addresses=[{"reference": f"Condition/{condition}"}]
    )
    assert not await _created_ok(client, addresses=[{"reference": "Condition/999999"}])


async def test_create_supporting_info_is_a_reference_any(client):
    patient = await create_patient(client)
    team = await create_care_team(client, care_team_body())
    assert await _created_ok(
        client,
        supportingInfo=[
            {"reference": f"Patient/{patient}"},
            {"reference": f"CareTeam/{team}"},
        ],
    )
    assert not await _created_ok(
        client, supportingInfo=[{"reference": "Patient/999999"}]
    )
    assert not await _created_ok(
        client, supportingInfo=[{"reference": "CareTeam/999999"}]
    )
    # a type that is not a resource here is stored as sent
    assert await _created_ok(client, supportingInfo=[{"reference": "Task/5"}])


async def test_create_goal_is_stored_as_sent(client):
    """Goal is not a resource here yet."""
    assert await _created_ok(client, goal=[{"reference": "Goal/999999"}])


async def test_create_activity_reference_must_exist_for_rebuilt_types(client):
    patient = await create_patient(client)
    appointment = await create_appointment(client, appointment_body(patient))
    medication_request = await create_medication_request(
        client, medication_request_body(patient)
    )
    service_request = await create_service_request(
        client, service_request_body(patient)
    )
    for ref in (
        f"Appointment/{appointment}",
        f"MedicationRequest/{medication_request}",
        f"ServiceRequest/{service_request}",
    ):
        assert await _created_ok(
            client, activity=[{"reference": {"reference": ref}}]
        ), ref
    for missing in (
        "Appointment/999999",
        "MedicationRequest/999999",
        "ServiceRequest/999999",
    ):
        assert not await _created_ok(
            client, activity=[{"reference": {"reference": missing}}]
        ), missing
    # CommunicationRequest, Task, DeviceRequest ... are not resources here: stored as sent.
    for sent in ("Task/999999", "CommunicationRequest/999999", "RequestGroup/999999"):
        assert await _created_ok(
            client, activity=[{"reference": {"reference": sent}}]
        ), sent


async def test_create_activity_detail_references_must_exist(client):
    patient = await create_patient(client)
    practitioner = await create_practitioner(client)
    team = await create_care_team(client, care_team_body())
    service = await create_healthcare_service(client)
    location = await create_location(client)
    condition = await create_condition(client, condition_body(patient))
    medication = await create_medication(client, medication_body())

    def detail(**extra):
        return [{"detail": {"status": "scheduled", **extra}}]

    for performer in (
        f"Practitioner/{practitioner}",
        f"CareTeam/{team}",
        f"HealthcareService/{service}",
        f"Patient/{patient}",
    ):
        assert await _created_ok(
            client, activity=detail(performer=[{"reference": performer}])
        ), performer
    for missing in (
        "Practitioner/999999",
        "CareTeam/999999",
        "HealthcareService/999999",
        "Patient/999999",
    ):
        assert not await _created_ok(
            client, activity=detail(performer=[{"reference": missing}])
        ), missing
    assert await _created_ok(
        client, activity=detail(performer=[{"reference": "Device/5"}])
    )
    assert await _created_ok(
        client, activity=detail(location={"reference": f"Location/{location}"})
    )
    assert not await _created_ok(
        client, activity=detail(location={"reference": "Location/999999"})
    )
    assert await _created_ok(
        client,
        activity=detail(reasonReference=[{"reference": f"Condition/{condition}"}]),
    )
    assert not await _created_ok(
        client, activity=detail(reasonReference=[{"reference": "Condition/999999"}])
    )
    assert await _created_ok(
        client,
        activity=detail(productReference={"reference": f"Medication/{medication}"}),
    )
    assert not await _created_ok(
        client, activity=detail(productReference={"reference": "Medication/999999"})
    )
    # a Substance product is not a resource here: stored as sent
    assert await _created_ok(
        client, activity=detail(productReference={"reference": "Substance/5"})
    )


async def test_create_activity_outcome_reference_is_a_reference_any(client):
    patient = await create_patient(client)
    ok = [{"outcomeReference": [{"reference": f"Patient/{patient}"}]}]
    bad = [{"outcomeReference": [{"reference": "Patient/999999"}]}]
    assert await _created_ok(client, activity=ok)
    assert not await _created_ok(client, activity=bad)


async def test_create_note_and_progress_authors_must_exist(client):
    practitioner = await create_practitioner(client)
    ref = {"reference": f"Practitioner/{practitioner}"}
    gone = {"reference": "Practitioner/999999"}
    assert await _created_ok(client, note=[{"authorReference": ref, "text": "x"}])
    assert not await _created_ok(client, note=[{"authorReference": gone, "text": "x"}])
    assert await _created_ok(
        client, activity=[{"progress": [{"authorReference": ref, "text": "x"}]}]
    )
    assert not await _created_ok(
        client, activity=[{"progress": [{"authorReference": gone, "text": "x"}]}]
    )


async def test_create_every_identifier_assigner_must_exist(client):
    organization = await create_organization(client)

    def ident(ref):
        return [{"system": "urn:t", "value": "1", "assigner": {"reference": ref}}]

    assert await _created_ok(client, identifier=ident(f"Organization/{organization}"))
    assert not await _created_ok(client, identifier=ident("Organization/999999"))


async def test_create_reference_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    body = care_plan_body()
    body["subject"] = {"reference": f"Patient/{theirs}"}
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_absolute_and_logical_references_not_resolved(client):
    body = care_plan_body(
        encounter={"identifier": {"system": "urn:enc", "value": "E-1"}},
        author={"reference": "https://other.example.org/fhir/Practitioner/9"},
        careTeam=[{"reference": "https://other.example.org/fhir/CareTeam/9"}],
        activity=[
            {
                "reference": {"reference": "https://other.example.org/fhir/Task/9"},
            },
            {
                "detail": {
                    "status": "scheduled",
                    "performer": [{"identifier": {"system": "urn:pr", "value": "P-9"}}],
                }
            },
        ],
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["author"]["reference"].endswith("/Practitioner/9")
    assert data["activity"][1]["detail"]["performer"][0]["identifier"]["value"] == "P-9"


# -- Read -----------------------------------------------------------------------------------


async def test_get_by_id(client):
    care_plan, _ = await _full(client)
    resp = await client.get(f"{BASE}/{care_plan}")
    assert resp.status_code == 200 and resp.json()["id"] == str(care_plan)


async def test_get_is_fhir_regardless_of_accept(client):
    care_plan = await create_care_plan(client, care_plan_body())
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{care_plan}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "CarePlan"


async def test_xml_only_accept_is_406(client):
    care_plan = await create_care_plan(client, care_plan_body())
    resp = await client.get(
        f"{BASE}/{care_plan}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Patch ----------------------------------------------------------------------------------


async def test_patch_scalar_keeps_the_rest(client):
    care_plan, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{care_plan}", json={"status": "completed", "title": "Closed plan"}
    )
    assert resp.status_code == 200, resp.text
    assert (
        resp.json()["status"] == "completed" and resp.json()["title"] == "Closed plan"
    )
    assert resp.json()["intent"] == "plan"  # untouched
    assert resp.json()["category"][0]["coding"][0]["code"] == "assess-plan"
    assert resp.json()["activity"][1]["detail"]["description"] == "Daily walk."


async def test_patch_reindexes_search(client):
    care_plan, _ = await _full(client)
    patient = await create_patient(client)
    await client.patch(
        f"{BASE}/{care_plan}",
        json={
            "status": "revoked",
            "intent": "order",
            "category": [concept(SCT, "999")],
            "period": {"start": "2030-01-01"},
            "subject": {"reference": f"Patient/{patient}"},
            "activity": [
                {
                    "detail": {
                        "status": "scheduled",
                        "code": concept(SCT, "555"),
                        "scheduledPeriod": {"start": "2035-01-01"},
                    }
                }
            ],
        },
    )
    for param, old, new in (
        ("status", "active", "revoked"),
        ("intent", "plan", "order"),
        ("category", "assess-plan", "999"),
        ("date", "eq2026-03-01", "ge2031-01-01"),
        ("activity-code", "386053000", "555"),
        ("activity-date", "eq2026-02", "ge2035-06-01"),
        ("patient", None, str(patient)),
    ):
        if old is not None:
            assert care_plan not in _ids(
                (await client.get(BASE + "/", params={param: old})).json()
            ), param
        assert care_plan in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param
    assert care_plan in _ids(
        (
            await client.get(BASE + "/", params={"activity-reference:missing": "true"})
        ).json()
    )
    assert care_plan in _ids(
        (await client.get(BASE + "/", params={"performer:missing": "true"})).json()
    )


async def test_patch_replaces_lists_and_empty_clears(client):
    care_plan, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{care_plan}",
        json={"identifier": [], "category": [], "activity": [], "careTeam": []},
    )
    for gone in ("identifier", "category", "activity", "careTeam"):
        assert gone not in resp.json()
    assert resp.json()["status"] == "active"  # untouched
    for param in (
        "identifier",
        "category",
        "activity-reference",
        "activity-code",
        "performer",
        "care-team",
    ):
        assert care_plan in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_clears_encounter_and_missing_follows(client):
    encounter = await create_encounter(client, encounter_body())
    care_plan = await create_care_plan(
        client, care_plan_body(encounter={"reference": f"Encounter/{encounter}"})
    )
    resp = await client.patch(f"{BASE}/{care_plan}", json={"encounter": None})
    assert "encounter" not in resp.json()
    assert care_plan in _ids(
        (await client.get(BASE + "/", params={"encounter:missing": "true"})).json()
    )


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client):
    care_plan = await create_care_plan(client, care_plan_body())
    resp = await client.patch(
        f"{BASE}/{care_plan}",
        json={"careTeam": [{"reference": "CareTeam/999999"}]},
    )
    assert resp.status_code == 422
    assert "careTeam" not in (await client.get(f"{BASE}/{care_plan}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    care_plan = await create_care_plan(client, care_plan_body(status="active"))
    assert (
        await client.patch(f"{BASE}/{care_plan}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{care_plan}")).json()["status"] == "active"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"title": "x"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Delete ---------------------------------------------------------------------------------


async def test_delete(client):
    care_plan, _ = await _full(client)
    assert (await client.delete(f"{BASE}/{care_plan}")).status_code == 204
    assert (await client.get(f"{BASE}/{care_plan}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "CP-1001"),
        ("category", "assess-plan"),
        ("activity-code", "386053000"),
        ("status", "active"),
    ):
        assert care_plan not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Auth -----------------------------------------------------------------------------------


async def test_create_without_permission(client):
    _as_user(permissions=["care_plan:read"])
    assert (await client.post(BASE + "/", json=care_plan_body())).status_code == 403


async def test_org_less_token_rejected(client):
    care_plan = await create_care_plan(client, care_plan_body())

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": CARE_PLAN_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=care_plan_body())).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{care_plan}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    care_plan = await create_care_plan(client, care_plan_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{care_plan}"),
            await other_client.patch(f"{BASE}/{care_plan}", json={"title": "x"}),
            await other_client.delete(f"{BASE}/{care_plan}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_care_plan(
        client,
        care_plan_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}]),
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()


async def test_care_plan_is_checked_where_a_reference_any_can_name_it(client):
    """DetectedIssue.implicated is a Reference(Any): a relative CarePlan there must exist."""
    care_plan = await create_care_plan(client, care_plan_body())
    issues = "/api/fhir/v1/detected-issues/"
    ok = {"status": "final", "implicated": [{"reference": f"CarePlan/{care_plan}"}]}
    assert (await client.post(issues, json=ok)).status_code == 201
    missing = {"status": "final", "implicated": [{"reference": "CarePlan/999999"}]}
    assert (await client.post(issues, json=missing)).status_code == 422
