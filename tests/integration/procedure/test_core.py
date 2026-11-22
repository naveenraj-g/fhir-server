"""Core procedure endpoint coverage.

Procedure is stored Medplum-style (like Patient, Appointment, Encounter,
Condition and the other content-based resources): the request body (genuine FHIR
R4 Procedure JSON) is validated and stored whole in `content`, every response is
FHIR R4 (`application/fhir+json`, regardless of Accept), and only the FHIR R4
search parameters are indexed (https://www.hl7.org/fhir/R4/procedure.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing
scope, cross-org isolation), the existence checks on every local reference
(`subject`, `encounter`, `location`, `recorder`, `asserter`, `performer.actor` /
`.onBehalfOf`, `partOf`, `reasonReference`, `complicationDetail`, note authors,
`identifier.assigner`), and the fact that a Procedure is now a real target for the
references that name one (Encounter `diagnosis` / `reasonReference`, Appointment
`reasonReference`). Search lives in test_search.py.

R4 requires `status` and `subject`, but only the `java_validator` backend enforces
cardinality minimums (the native structural check does not), so that is not
asserted here.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.procedure.conftest import PROCEDURE_PERMS
from tests.integration.procedure.support import (
    API,
    BASE,
    appointment_body,
    create_condition,
    create_diagnostic_report,
    create_encounter,
    create_location,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_procedure,
    create_related_person,
    encounter_body,
    full_body,
    procedure_body,
    related_person_body,
)


@pytest.fixture
def native_validation(monkeypatch):
    """The base R4 validator may be switched off in configs/config.yaml
    (`fhir_validation.enabled: false` skips it entirely). Tests that assert "a
    key that isn't FHIR is a 422" need it on: the project's own structural
    check (no sidecar needed)."""
    monkeypatch.setattr(settings.fhir_validation, "enabled", True)
    monkeypatch.setattr(settings.fhir_validation, "backend", "native")


@pytest.fixture
async def patient(client) -> int:
    return await create_patient(client)


def _ids(bundle: dict) -> set[int]:
    return {
        int(e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == "match"
    }


def _as_user(sub="u-test", org_id="org-test", permissions=PROCEDURE_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client, patient) -> tuple[int, dict]:
    encounter = await create_encounter(client, encounter_body())
    practitioner = await create_practitioner(client)
    organization = await create_organization(client)
    location = await create_location(client)
    report = await create_diagnostic_report(client, patient)
    body = full_body(patient, encounter, practitioner, organization, location, report)
    return await create_procedure(client, body), body


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_minimal(client, patient):
    resp = await client.post(BASE + "/", json=procedure_body(patient))
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "Procedure" and data["status"] == "completed"
    assert data["subject"] == {"reference": f"Patient/{patient}"}


async def test_create_full_round_trip(client, patient):
    proc, body = await _full(client, patient)
    data = (await client.get(f"{BASE}/{proc}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_elements_nothing_searches_on(client, patient):
    """`outcome`, `bodySite`, `complication`, `focalDevice`, `usedCode`, `note` and the performer's
    `function` / `onBehalfOf` live only in `content`."""
    proc, _ = await _full(client, patient)
    data = (await client.get(f"{BASE}/{proc}")).json()
    assert data["outcome"]["coding"][0]["code"] == "385669000"
    assert data["bodySite"][0]["coding"][0]["code"] == "66754008"
    assert data["performer"][0]["function"]["coding"][0]["code"] == "304292004"
    assert data["performer"][0]["onBehalfOf"]["reference"].startswith("Organization/")
    assert data["focalDevice"][0]["manipulated"] == {"reference": "Device/7"}
    assert data["note"][0]["text"] == "Uneventful."


_PERFORMED = {
    "DateTime": {"performedDateTime": "2023-01"},
    "Period": {"performedPeriod": {"start": "2020-01-01", "end": "2020-02-01"}},
    "String": {"performedString": "as a child"},
    "Age": {
        "performedAge": {
            "value": 12,
            "unit": "years",
            "system": "http://unitsofmeasure.org",
            "code": "a",
        }
    },
    "Range": {
        "performedRange": {
            "low": {"value": 5, "unit": "years"},
            "high": {"value": 10, "unit": "years"},
        }
    },
}


@pytest.mark.parametrize("choice", sorted(_PERFORMED))
async def test_create_every_performed_choice_round_trips(client, patient, choice):
    extra = _PERFORMED[choice]
    resp = await client.post(BASE + "/", json=procedure_body(patient, **extra))
    assert resp.status_code == 201, resp.text
    for key, value in extra.items():
        assert resp.json()[key] == value


@pytest.mark.parametrize(
    "status",
    [
        "preparation",
        "in-progress",
        "not-done",
        "on-hold",
        "stopped",
        "completed",
        "entered-in-error",
        "unknown",
    ],
)
async def test_create_every_status_round_trips(client, patient, status):
    resp = await client.post(BASE + "/", json=procedure_body(patient, status))
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


async def test_create_ignores_server_managed_id_and_meta(client, patient):
    body = procedure_body(
        patient, id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"}
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client, patient):
    for bad in (
        {"status": "robot"},
        {"code": "80146002"},
        {"performer": {"actor": {"reference": "Practitioner/1"}}},
        {"performedAge": "12"},
    ):
        resp = await client.post(BASE + "/", json=procedure_body(patient, **bad))
        assert resp.status_code == 422, (bad, resp.text)
    assert (
        await client.post(
            BASE + "/", json={"status": "completed", "subject": "Patient/1"}
        )
    ).status_code == 422


async def test_create_non_fhir_key_rejected(client, patient, native_validation):
    assert (
        await client.post(
            BASE + "/", json=procedure_body(patient, not_a_fhir_element=1)
        )
    ).status_code == 422


async def test_create_old_flat_fields_rejected(client, patient, native_validation):
    for stale in (
        {"status_reason": {"text": "x"}},
        {"performed_string": "x"},
        {"org_id": "x"},
    ):
        resp = await client.post(BASE + "/", json={**procedure_body(patient), **stale})
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client, patient):
    assert (
        await client.post(
            BASE + "/", json=procedure_body(patient, resourceType="Patient")
        )
    ).status_code == 422


async def test_create_audit_meta_from_actor(client, patient):
    data = (await client.post(BASE + "/", json=procedure_body(patient))).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# ── Create: existence checks on local references ─────────────────────────────


async def test_create_subject_patient_must_exist(client):
    assert (
        await client.post(BASE + "/", json=procedure_body(999999))
    ).status_code == 422


async def test_create_subject_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    assert (
        await client.post(BASE + "/", json=procedure_body(theirs))
    ).status_code == 422


async def test_create_group_subject_is_stored_as_sent(client):
    """Group is not a resource on this server, so its reference is not checked."""
    resp = await client.post(
        BASE + "/", json={"status": "completed", "subject": {"reference": "Group/5"}}
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == {"reference": "Group/5"}


async def test_create_encounter_and_location_must_exist(client, patient):
    for element, missing, kind in (
        ("encounter", "Encounter/999999", "enc"),
        ("location", "Location/999999", "loc"),
    ):
        assert (
            await client.post(
                BASE + "/",
                json=procedure_body(patient, **{element: {"reference": missing}}),
            )
        ).status_code == 422
    encounter = await create_encounter(client, encounter_body())
    location = await create_location(client)
    ok = procedure_body(
        patient,
        encounter={"reference": f"Encounter/{encounter}"},
        location={"reference": f"Location/{location}"},
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201


@pytest.mark.parametrize("element", ["recorder", "asserter"])
async def test_create_recorder_and_asserter_are_checked_for_all_four_types(
    client, patient, element
):
    practitioner = await create_practitioner(client)
    role = await create_practitioner_role(client)
    related_person = await create_related_person(client, related_person_body(patient))
    for ref in (
        f"Practitioner/{practitioner}",
        f"PractitionerRole/{role}",
        f"Patient/{patient}",
        f"RelatedPerson/{related_person}",
    ):
        resp = await client.post(
            BASE + "/", json=procedure_body(patient, **{element: {"reference": ref}})
        )
        assert resp.status_code == 201, (ref, resp.text)
    for missing in (
        "Practitioner/999999",
        "PractitionerRole/999999",
        "Patient/999999",
        "RelatedPerson/999999",
    ):
        resp = await client.post(
            BASE + "/",
            json=procedure_body(patient, **{element: {"reference": missing}}),
        )
        assert resp.status_code == 422, (missing, resp.text)


async def test_create_performer_actor_is_checked_except_for_a_device(client, patient):
    practitioner = await create_practitioner(client)
    role = await create_practitioner_role(client)
    organization = await create_organization(client)
    related_person = await create_related_person(client, related_person_body(patient))
    for ref in (
        f"Practitioner/{practitioner}",
        f"PractitionerRole/{role}",
        f"Organization/{organization}",
        f"Patient/{patient}",
        f"RelatedPerson/{related_person}",
        "Device/999999",
    ):
        resp = await client.post(
            BASE + "/",
            json=procedure_body(patient, performer=[{"actor": {"reference": ref}}]),
        )
        assert resp.status_code == 201, (
            ref,
            resp.text,
        )  # a Device is not a resource here: stored as sent
    for missing in (
        "Practitioner/999999",
        "PractitionerRole/999999",
        "Organization/999999",
        "Patient/999999",
        "RelatedPerson/999999",
    ):
        resp = await client.post(
            BASE + "/",
            json=procedure_body(patient, performer=[{"actor": {"reference": missing}}]),
        )
        assert resp.status_code == 422, (missing, resp.text)


async def test_create_performer_on_behalf_of_must_exist(client, patient):
    practitioner = await create_practitioner(client)
    actor = {"reference": f"Practitioner/{practitioner}"}
    missing = procedure_body(
        patient,
        performer=[
            {"actor": actor, "onBehalfOf": {"reference": "Organization/999999"}}
        ],
    )
    assert (await client.post(BASE + "/", json=missing)).status_code == 422
    organization = await create_organization(client)
    ok = procedure_body(
        patient,
        performer=[
            {
                "actor": actor,
                "onBehalfOf": {"reference": f"Organization/{organization}"},
            }
        ],
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201


async def test_create_part_of_reason_reference_and_complication_detail_are_checked(
    client, patient
):
    other = await create_procedure(client, procedure_body(patient))
    condition = await create_condition(client, patient)
    ok = procedure_body(
        patient,
        partOf=[{"reference": f"Procedure/{other}"}],
        reasonReference=[
            {"reference": f"Condition/{condition}"},
            {"reference": f"Procedure/{other}"},
        ],
        complicationDetail=[{"reference": f"Condition/{condition}"}],
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    for bad in (
        {"partOf": [{"reference": "Procedure/999999"}]},
        {"reasonReference": [{"reference": "Condition/999999"}]},
        {"reasonReference": [{"reference": "Procedure/999999"}]},
        {"complicationDetail": [{"reference": "Condition/999999"}]},
    ):
        assert (
            await client.post(BASE + "/", json=procedure_body(patient, **bad))
        ).status_code == 422, bad


async def test_create_report_and_reason_diagnostic_report_are_checked(client, patient):
    report = await create_diagnostic_report(client, patient)
    ok = procedure_body(
        patient,
        report=[{"reference": f"DiagnosticReport/{report}"}],
        reasonReference=[{"reference": f"DiagnosticReport/{report}"}],
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    for bad in (
        {"report": [{"reference": "DiagnosticReport/999999"}]},
        {"reasonReference": [{"reference": "DiagnosticReport/999999"}]},
    ):
        assert (
            await client.post(BASE + "/", json=procedure_body(patient, **bad))
        ).status_code == 422, bad


async def test_create_note_author_reference_is_checked(client, patient):
    note = [{"authorReference": {"reference": "Practitioner/999999"}, "text": "x"}]
    assert (
        await client.post(BASE + "/", json=procedure_body(patient, note=note))
    ).status_code == 422
    practitioner = await create_practitioner(client)
    ok = [
        {"authorReference": {"reference": f"Practitioner/{practitioner}"}, "text": "x"}
    ]
    assert (
        await client.post(BASE + "/", json=procedure_body(patient, note=ok))
    ).status_code == 201


async def test_create_identifier_assigner_must_exist(client, patient):
    body = procedure_body(
        patient,
        identifier=[{"value": "1", "assigner": {"reference": "Organization/999999"}}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 422
    org = await create_organization(client)
    body = procedure_body(
        patient,
        identifier=[{"value": "1", "assigner": {"reference": f"Organization/{org}"}}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_unrebuilt_targets_are_not_checked(client, patient):
    """basedOn, a report that is not a DiagnosticReport, usedReference, focalDevice.manipulated and the
    reasonReference type that is not rebuilt (DocumentReference) is stored as sent."""
    body = procedure_body(
        patient,
        basedOn=[{"reference": "CarePlan/999999"}],
        report=[
            {"reference": "DocumentReference/999999"},
            {"reference": "Composition/999999"},
        ],
        usedReference=[{"reference": "Device/999999"}],
        reasonReference=[{"reference": "DocumentReference/999999"}],
        partOf=[{"reference": "Observation/999999"}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_absolute_and_logical_references_not_resolved(client):
    absolute = "https://other.example.org/fhir/Patient/1"
    resp = await client.post(
        BASE + "/", json={"status": "completed", "subject": {"reference": absolute}}
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == {"reference": absolute}
    logical = {
        "identifier": {"system": "urn:pts", "value": "P-9"},
        "display": "External",
    }
    body = {
        "status": "completed",
        "subject": logical,
        "location": {"reference": "https://other.example.org/fhir/Location/7"},
    }
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == logical
    assert resp.json()["location"] == {
        "reference": "https://other.example.org/fhir/Location/7"
    }


# ── A Procedure is now a real target of the references that name one ─────────


async def test_references_to_a_procedure_are_checked_and_resolve(client, patient):
    proc = await create_procedure(client, procedure_body(patient))
    ref = f"Procedure/{proc}"
    enc = {
        "status": "finished",
        "class": {"code": "AMB"},
        "diagnosis": [{"condition": {"reference": ref}}],
        "reasonReference": [{"reference": ref}],
    }
    assert (await client.post(f"{API}/encounters/", json=enc)).status_code == 201
    appointment = appointment_body(patient, reasonReference=[{"reference": ref}])
    assert (
        await client.post(f"{API}/appointments/", json=appointment)
    ).status_code == 201


async def test_references_to_a_missing_procedure_are_rejected(client, patient):
    ref = "Procedure/999999"
    enc = {
        "status": "finished",
        "class": {"code": "AMB"},
        "diagnosis": [{"condition": {"reference": ref}}],
    }
    assert (await client.post(f"{API}/encounters/", json=enc)).status_code == 422
    enc = {
        "status": "finished",
        "class": {"code": "AMB"},
        "reasonReference": [{"reference": ref}],
    }
    assert (await client.post(f"{API}/encounters/", json=enc)).status_code == 422
    appointment = appointment_body(patient, reasonReference=[{"reference": ref}])
    assert (
        await client.post(f"{API}/appointments/", json=appointment)
    ).status_code == 422


# ── Read ─────────────────────────────────────────────────────────────────────


async def test_get_by_id(client, patient):
    proc, _ = await _full(client, patient)
    resp = await client.get(f"{BASE}/{proc}")
    assert resp.status_code == 200 and resp.json()["id"] == str(proc)


async def test_get_is_fhir_regardless_of_accept(client, patient):
    proc = await create_procedure(client, procedure_body(patient))
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{proc}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "Procedure"


async def test_xml_only_accept_is_406(client, patient):
    proc = await create_procedure(client, procedure_body(patient))
    resp = await client.get(
        f"{BASE}/{proc}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_scalar_keeps_the_rest(client, patient):
    proc, _ = await _full(client, patient)
    resp = await client.patch(
        f"{BASE}/{proc}", json={"status": "stopped", "performedDateTime": "2024-05-01"}
    )
    assert resp.status_code == 200, resp.text
    assert (
        resp.json()["status"] == "stopped"
        and resp.json()["performedDateTime"] == "2024-05-01"
    )
    assert resp.json()["subject"] == {"reference": f"Patient/{patient}"}  # untouched
    assert resp.json()["outcome"]["coding"][0]["code"] == "385669000"
    assert resp.json()["note"][0]["time"] == "2023-01-15T11:00:00Z"


async def test_patch_reindexes_search(client, patient):
    proc, _ = await _full(client, patient)
    await client.patch(
        f"{BASE}/{proc}",
        json={
            "status": "stopped",
            "code": {
                "coding": [{"system": "http://snomed.info/sct", "code": "71651007"}]
            },
            "performedPeriod": None,
            "performedDateTime": "2024-05-01",
        },
    )
    for param, old, new in (
        ("status", "completed", "stopped"),
        ("code", "80146002", "71651007"),
        ("date", "2023-01-15", "2024-05-01"),
    ):
        assert proc not in _ids(
            (await client.get(BASE + "/", params={param: old})).json()
        ), param
        assert proc in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param


async def test_patch_subject_replaced_and_reindexed(client, patient):
    proc = await create_procedure(client, procedure_body(patient))
    other = await create_patient(client)
    resp = await client.patch(
        f"{BASE}/{proc}", json={"subject": {"reference": f"Patient/{other}"}}
    )
    assert resp.status_code == 200, resp.text
    assert proc not in _ids(
        (await client.get(BASE + "/", params={"patient": str(patient)})).json()
    )
    assert proc in _ids(
        (await client.get(BASE + "/", params={"patient": str(other)})).json()
    )


async def test_patch_replaces_lists_and_empty_clears(client, patient):
    proc, _ = await _full(client, patient)
    assert proc in _ids(
        (await client.get(BASE + "/", params={"reason-code": "74400008"})).json()
    )
    resp = await client.patch(
        f"{BASE}/{proc}",
        json={
            "performer": [],
            "reasonCode": [],
            "identifier": [],
            "instantiatesUri": [],
            "instantiatesCanonical": [],
            "basedOn": [],
        },
    )
    for gone in (
        "performer",
        "reasonCode",
        "identifier",
        "instantiatesUri",
        "instantiatesCanonical",
        "basedOn",
    ):
        assert gone not in resp.json()
    assert resp.json()["bodySite"][0]["coding"][0]["code"] == "66754008"  # untouched
    for param, value in (
        ("reason-code", "74400008"),
        ("identifier", "PR-1001"),
        ("instantiates-uri", "http://example.org/protocols/appendectomy"),
        (
            "instantiates-canonical",
            "http://example.org/fhir/PlanDefinition/appendectomy",
        ),
        ("based-on", "ServiceRequest/80001"),
    ):
        assert proc not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param
    assert proc in _ids(
        (await client.get(BASE + "/", params={"performer:missing": "true"})).json()
    )


async def test_patch_clears_a_date_and_missing_follows(client, patient):
    proc = await create_procedure(
        client, procedure_body(patient, performedDateTime="2024-05-01")
    )
    resp = await client.patch(f"{BASE}/{proc}", json={"performedDateTime": None})
    assert "performedDateTime" not in resp.json()
    assert proc in _ids(
        (await client.get(BASE + "/", params={"date:missing": "true"})).json()
    )


async def test_patch_nonexistent_reference_rejected_and_nothing_written(
    client, patient
):
    proc = await create_procedure(client, procedure_body(patient))
    resp = await client.patch(
        f"{BASE}/{proc}", json={"location": {"reference": "Location/999999"}}
    )
    assert resp.status_code == 422
    assert "location" not in (await client.get(f"{BASE}/{proc}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client, patient):
    proc = await create_procedure(client, procedure_body(patient, "completed"))
    assert (
        await client.patch(f"{BASE}/{proc}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{proc}")).json()["status"] == "completed"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "stopped"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete(client, patient):
    proc, _ = await _full(client, patient)
    assert (await client.delete(f"{BASE}/{proc}")).status_code == 204
    assert (await client.get(f"{BASE}/{proc}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "PR-1001"),
        ("code", "80146002"),
        ("reason-code", "74400008"),
        ("instantiates-uri", "http://example.org/protocols/appendectomy"),
    ):
        assert proc not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_create_without_permission(client, patient):
    _as_user(permissions=["procedure:read"])
    assert (
        await client.post(BASE + "/", json=procedure_body(patient))
    ).status_code == 403


async def test_org_less_token_rejected(client, patient):
    proc = await create_procedure(client, procedure_body(patient))

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": PROCEDURE_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=procedure_body())).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{proc}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    proc = await create_procedure(client, procedure_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{proc}"),
            await other_client.patch(f"{BASE}/{proc}", json={"status": "stopped"}),
            await other_client.delete(f"{BASE}/{proc}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_procedure(
        client, procedure_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}])
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()


async def test_create_reason_reference_observation_must_exist(client, patient):
    ok = procedure_body(patient, reasonReference=[{"reference": "Observation/160005"}])
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = procedure_body(
        patient, reasonReference=[{"reference": "Observation/999999"}]
    )
    assert (await client.post(BASE + "/", json=missing)).status_code == 422


async def test_create_based_on_service_request_must_exist(client, patient):
    ok = procedure_body(patient, basedOn=[{"reference": "ServiceRequest/80001"}])
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = procedure_body(patient, basedOn=[{"reference": "ServiceRequest/999999"}])
    assert (await client.post(BASE + "/", json=missing)).status_code == 422
