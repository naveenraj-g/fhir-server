"""Core condition endpoint coverage.

Condition is stored Medplum-style (like Patient, Appointment, Encounter and the
other content-based resources): the request body (genuine FHIR R4 Condition
JSON) is validated and stored whole in `content`, every response is FHIR R4
(`application/fhir+json`, regardless of Accept), and only the FHIR R4 search
parameters are indexed (https://www.hl7.org/fhir/R4/condition.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing
scope, cross-org isolation), the existence checks on every local reference
(`subject`, `encounter`, `recorder`, `asserter`, note authors,
`identifier.assigner`), and the fact that a Condition is now a real target for
the references that name one (Encounter `diagnosis` / `reasonReference`,
Appointment `reasonReference`). Search lives in test_search.py.

R4 requires `subject`, but only the `java_validator` backend enforces cardinality
minimums and the con-3/con-4/con-5 invariants (the native structural check does
not), so those are not asserted here.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.condition.conftest import CONDITION_PERMS
from tests.integration.condition.support import (
    API,
    BASE,
    appointment_body,
    category,
    clinical,
    condition_body,
    create_condition,
    create_encounter,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_related_person,
    encounter_body,
    full_body,
    related_person_body,
    verification,
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
    return {int(e["resource"]["id"]) for e in bundle.get("entry") or [] if e["search"]["mode"] == "match"}


def _as_user(sub="u-test", org_id="org-test", permissions=CONDITION_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(sub=sub, org_id=org_id, permissions=permissions)


async def _full(client, patient) -> tuple[int, dict]:
    encounter = await create_encounter(client, encounter_body())
    practitioner = await create_practitioner(client)
    organization = await create_organization(client)
    body = full_body(patient, encounter, practitioner, organization)
    return await create_condition(client, body), body


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_minimal(client, patient):
    resp = await client.post(BASE + "/", json=condition_body(patient))
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "Condition"
    assert data["subject"] == {"reference": f"Patient/{patient}"}


async def test_create_full_round_trip(client, patient):
    cond, body = await _full(client, patient)
    data = (await client.get(f"{BASE}/{cond}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")} == expected


async def test_create_keeps_elements_nothing_searches_on(client, patient):
    """`recorder`, `note`, `stage.assessment` / `.type` and the rest of `evidence` live only in `content`."""
    cond, _ = await _full(client, patient)
    data = (await client.get(f"{BASE}/{cond}")).json()
    assert data["recorder"]["reference"].startswith("Practitioner/")
    assert data["note"][0]["text"] == "Blood pressure poorly controlled."
    assert data["stage"][0]["assessment"] == [{"reference": "Observation/160001"}]
    assert data["stage"][0]["type"] == {"text": "clinical"}


_CHOICES = {
    "DateTime": {"DateTime": "2023-01"},
    "Age": {"Age": {"value": 12, "unit": "years", "system": "http://unitsofmeasure.org", "code": "a"}},
    "Period": {"Period": {"start": "2020-01-01", "end": "2020-02-01"}},
    "Range": {"Range": {"low": {"value": 5, "unit": "years"}, "high": {"value": 10, "unit": "years"}}},
    "String": {"String": "as a child"},
}


@pytest.mark.parametrize("element", ["onset", "abatement"])
@pytest.mark.parametrize("choice", sorted(_CHOICES))
async def test_create_every_onset_and_abatement_choice_round_trips(client, patient, element, choice):
    extra = {f"{element}{k}": v for k, v in _CHOICES[choice].items()}
    resp = await client.post(BASE + "/", json=condition_body(patient, **extra))
    assert resp.status_code == 201, resp.text
    for key, value in extra.items():
        assert resp.json()[key] == value


async def test_create_ignores_server_managed_id_and_meta(client, patient):
    body = condition_body(patient, id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"})
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client, patient):
    for bad in ({"clinicalStatus": "active"}, {"category": "problem-list-item"}, {"onsetAge": "12"}):
        resp = await client.post(BASE + "/", json=condition_body(patient, **bad))
        assert resp.status_code == 422, (bad, resp.text)
    assert (await client.post(BASE + "/", json={"subject": "Patient/1"})).status_code == 422


async def test_create_non_fhir_key_rejected(client, patient, native_validation):
    assert (await client.post(BASE + "/", json=condition_body(patient, not_a_fhir_element=1))).status_code == 422


async def test_create_old_flat_fields_rejected(client, patient, native_validation):
    for stale in ({"clinical_status": {"text": "x"}}, {"onset_date_time": "2020-01-01"}, {"org_id": "x"}):
        resp = await client.post(BASE + "/", json={**condition_body(patient), **stale})
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client, patient):
    assert (await client.post(BASE + "/", json=condition_body(patient, resourceType="Patient"))).status_code == 422


async def test_create_audit_meta_from_actor(client, patient):
    data = (await client.post(BASE + "/", json=condition_body(patient))).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# ── Create: existence checks on local references ─────────────────────────────


async def test_create_subject_patient_must_exist(client):
    assert (await client.post(BASE + "/", json=condition_body(999999))).status_code == 422


async def test_create_subject_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    assert (await client.post(BASE + "/", json=condition_body(theirs))).status_code == 422


async def test_create_group_subject_is_stored_as_sent(client):
    """Group is not a resource on this server, so its reference is not checked."""
    resp = await client.post(BASE + "/", json={"subject": {"reference": "Group/5"}})
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == {"reference": "Group/5"}


async def test_create_encounter_must_exist(client, patient):
    missing = condition_body(patient, encounter={"reference": "Encounter/999999"})
    assert (await client.post(BASE + "/", json=missing)).status_code == 422
    encounter = await create_encounter(client, encounter_body())
    assert (
        await client.post(BASE + "/", json=condition_body(patient, encounter={"reference": f"Encounter/{encounter}"}))
    ).status_code == 201


@pytest.mark.parametrize("element", ["recorder", "asserter"])
async def test_create_recorder_and_asserter_are_checked_for_all_four_types(client, patient, element):
    practitioner = await create_practitioner(client)
    role = await create_practitioner_role(client)
    related_person = await create_related_person(client, related_person_body(patient))
    for ref in (f"Practitioner/{practitioner}", f"PractitionerRole/{role}", f"Patient/{patient}", f"RelatedPerson/{related_person}"):
        resp = await client.post(BASE + "/", json=condition_body(patient, **{element: {"reference": ref}}))
        assert resp.status_code == 201, (ref, resp.text)
    for missing in ("Practitioner/999999", "PractitionerRole/999999", "Patient/999999", "RelatedPerson/999999"):
        resp = await client.post(BASE + "/", json=condition_body(patient, **{element: {"reference": missing}}))
        assert resp.status_code == 422, (missing, resp.text)


async def test_create_note_author_reference_is_checked(client, patient):
    note = [{"authorReference": {"reference": "Practitioner/999999"}, "text": "x"}]
    assert (await client.post(BASE + "/", json=condition_body(patient, note=note))).status_code == 422
    practitioner = await create_practitioner(client)
    ok = [{"authorReference": {"reference": f"Practitioner/{practitioner}"}, "text": "x"}]
    assert (await client.post(BASE + "/", json=condition_body(patient, note=ok))).status_code == 201


async def test_create_identifier_assigner_must_exist(client, patient):
    body = condition_body(patient, identifier=[{"value": "1", "assigner": {"reference": "Organization/999999"}}])
    assert (await client.post(BASE + "/", json=body)).status_code == 422
    org = await create_organization(client)
    body = condition_body(patient, identifier=[{"value": "1", "assigner": {"reference": f"Organization/{org}"}}])
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_unrebuilt_targets_are_not_checked(client, patient):
    """stage.assessment and evidence.detail point at resources this server does not rebuild
    (or at Any): stored as sent."""
    body = condition_body(
        patient,
        stage=[{"assessment": [{"reference": "Observation/999999"}]}],
        evidence=[{"detail": [{"reference": "DiagnosticReport/999999"}]}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_absolute_and_logical_references_not_resolved(client):
    absolute = "https://other.example.org/fhir/Patient/1"
    resp = await client.post(BASE + "/", json={"subject": {"reference": absolute}})
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == {"reference": absolute}
    logical = {"identifier": {"system": "urn:pts", "value": "P-9"}, "display": "External"}
    body = {"subject": logical, "asserter": {"reference": "https://other.example.org/fhir/Practitioner/7"}}
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == logical
    assert resp.json()["asserter"] == {"reference": "https://other.example.org/fhir/Practitioner/7"}


# ── A Condition is now a real target of the references that name one ─────────


async def test_references_to_a_condition_are_checked_and_resolve(client, patient):
    cond = await create_condition(client, condition_body(patient))
    ref = f"Condition/{cond}"
    enc = {
        "status": "finished",
        "class": {"code": "AMB"},
        "diagnosis": [{"condition": {"reference": ref}}],
        "reasonReference": [{"reference": ref}],
    }
    assert (await client.post(f"{API}/encounters/", json=enc)).status_code == 201
    appointment = appointment_body(patient, reasonReference=[{"reference": ref}])
    assert (await client.post(f"{API}/appointments/", json=appointment)).status_code == 201


async def test_references_to_a_missing_condition_are_rejected(client, patient):
    ref = "Condition/999999"
    enc = {"status": "finished", "class": {"code": "AMB"}, "diagnosis": [{"condition": {"reference": ref}}]}
    assert (await client.post(f"{API}/encounters/", json=enc)).status_code == 422
    enc = {"status": "finished", "class": {"code": "AMB"}, "reasonReference": [{"reference": ref}]}
    assert (await client.post(f"{API}/encounters/", json=enc)).status_code == 422
    appointment = appointment_body(patient, reasonReference=[{"reference": ref}])
    assert (await client.post(f"{API}/appointments/", json=appointment)).status_code == 422
    # A reference to another type in the same element is not checked: stored as sent.
    enc = {"status": "finished", "class": {"code": "AMB"}, "reasonReference": [{"reference": "Observation/999999"}]}
    assert (await client.post(f"{API}/encounters/", json=enc)).status_code == 201


# ── Read ─────────────────────────────────────────────────────────────────────


async def test_get_by_id(client, patient):
    cond, _ = await _full(client, patient)
    resp = await client.get(f"{BASE}/{cond}")
    assert resp.status_code == 200 and resp.json()["id"] == str(cond)


async def test_get_is_fhir_regardless_of_accept(client, patient):
    cond = await create_condition(client, condition_body(patient))
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{cond}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "Condition"


async def test_xml_only_accept_is_406(client, patient):
    cond = await create_condition(client, condition_body(patient))
    resp = await client.get(f"{BASE}/{cond}", headers={"Accept": "application/fhir+xml"})
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_scalar_keeps_the_rest(client, patient):
    cond, _ = await _full(client, patient)
    resp = await client.patch(f"{BASE}/{cond}", json={"clinicalStatus": clinical("resolved"), "recordedDate": "2024-05-01"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["clinicalStatus"] == clinical("resolved") and resp.json()["recordedDate"] == "2024-05-01"
    assert resp.json()["subject"] == {"reference": f"Patient/{patient}"}  # untouched
    assert resp.json()["stage"][0]["type"] == {"text": "clinical"}
    assert resp.json()["note"][0]["time"] == "2023-01-15T10:05:00Z"


async def test_patch_reindexes_search(client, patient):
    cond, _ = await _full(client, patient)
    await client.patch(
        f"{BASE}/{cond}",
        json={"clinicalStatus": clinical("resolved"), "category": [category("encounter-diagnosis")], "recordedDate": "2024-05-01"},
    )
    for param, old, new in (
        ("clinical-status", "active", "resolved"),
        ("category", "problem-list-item", "encounter-diagnosis"),
        ("recorded-date", "2023-01-15", "2024-05-01"),
    ):
        assert cond not in _ids((await client.get(BASE + "/", params={param: old})).json()), param
        assert cond in _ids((await client.get(BASE + "/", params={param: new})).json()), param


async def test_patch_subject_replaced_and_reindexed(client, patient):
    cond = await create_condition(client, condition_body(patient))
    other = await create_patient(client)
    resp = await client.patch(f"{BASE}/{cond}", json={"subject": {"reference": f"Patient/{other}"}})
    assert resp.status_code == 200, resp.text
    assert cond not in _ids((await client.get(BASE + "/", params={"patient": str(patient)})).json())
    assert cond in _ids((await client.get(BASE + "/", params={"patient": str(other)})).json())


async def test_patch_replaces_lists_and_empty_clears(client, patient):
    cond, _ = await _full(client, patient)
    assert cond in _ids((await client.get(BASE + "/", params={"evidence": "29857009"})).json())
    resp = await client.patch(f"{BASE}/{cond}", json={"evidence": [], "category": [], "identifier": [], "stage": [], "bodySite": []})
    for gone in ("evidence", "category", "identifier", "stage", "bodySite"):
        assert gone not in resp.json()
    assert resp.json()["severity"]["coding"][0]["code"] == "24484000"  # untouched
    for param, value in (
        ("evidence", "29857009"), ("category", "problem-list-item"), ("identifier", "C-1001"),
        ("stage", "14803004"), ("body-site", "368208006"),
    ):
        assert cond not in _ids((await client.get(BASE + "/", params={param: value})).json()), param


async def test_patch_onset_choice_can_be_swapped(client, patient):
    cond = await create_condition(client, condition_body(patient, onsetString="as a child"))
    assert cond in _ids((await client.get(BASE + "/", params={"onset-info": "as a"})).json())
    resp = await client.patch(f"{BASE}/{cond}", json={"onsetString": None, "onsetAge": {"value": 7, "unit": "years"}})
    assert resp.status_code == 200, resp.text
    assert "onsetString" not in resp.json() and resp.json()["onsetAge"] == {"value": 7, "unit": "years"}
    assert cond not in _ids((await client.get(BASE + "/", params={"onset-info": "as a"})).json())
    assert cond in _ids((await client.get(BASE + "/", params={"onset-age": "7"})).json())


async def test_patch_clears_a_date_and_missing_follows(client, patient):
    cond = await create_condition(client, condition_body(patient, recordedDate="2024-05-01"))
    resp = await client.patch(f"{BASE}/{cond}", json={"recordedDate": None})
    assert "recordedDate" not in resp.json()
    assert cond in _ids((await client.get(BASE + "/", params={"recorded-date:missing": "true"})).json())


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client, patient):
    cond = await create_condition(client, condition_body(patient))
    resp = await client.patch(f"{BASE}/{cond}", json={"asserter": {"reference": "Practitioner/999999"}})
    assert resp.status_code == 422
    assert "asserter" not in (await client.get(f"{BASE}/{cond}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client, patient):
    cond = await create_condition(client, condition_body(patient, verificationStatus=verification("confirmed")))
    assert (await client.patch(f"{BASE}/{cond}", json={"verificationStatus": "broken"})).status_code == 422
    assert (await client.get(f"{BASE}/{cond}")).json()["verificationStatus"] == verification("confirmed")


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"recordedDate": "2024"})
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete(client, patient):
    cond, _ = await _full(client, patient)
    assert (await client.delete(f"{BASE}/{cond}")).status_code == 204
    assert (await client.get(f"{BASE}/{cond}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (("identifier", "C-1001"), ("evidence", "29857009"), ("code", "38341003"), ("body-site", "368208006")):
        assert cond not in _ids((await client.get(BASE + "/", params={param: value})).json()), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_create_without_permission(client, patient):
    _as_user(permissions=["condition:read"])
    assert (await client.post(BASE + "/", json=condition_body(patient))).status_code == 403


async def test_org_less_token_rejected(client, patient):
    cond = await create_condition(client, condition_body(patient))

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": CONDITION_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=condition_body())).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{cond}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    cond = await create_condition(client, condition_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{cond}"),
            await other_client.patch(f"{BASE}/{cond}", json={"recordedDate": "2024"}),
            await other_client.delete(f"{BASE}/{cond}"),
        ):
            assert_operation_outcome(resp.json(), expected_status=404, response_status=resp.status_code)
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_condition(client, condition_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}]))
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})).json()
        assert bundle["total"] == 0
    finally:
        _as_user()
