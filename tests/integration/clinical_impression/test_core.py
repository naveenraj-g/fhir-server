"""Core clinical-impression endpoint coverage.

ClinicalImpression is stored Medplum-style (like Patient, Appointment, Encounter, Condition,
Procedure, DiagnosticReport, Immunization, RiskAssessment and the other content-based
resources): the request body (genuine FHIR R4 ClinicalImpression JSON) is validated and stored
whole in `content`, every response is FHIR R4 (`application/fhir+json`, regardless of Accept),
and only the FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/clinicalimpression.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence checks on every local reference (`subject`, `encounter`,
`assessor`, `previous`, `problem`, `investigation.item`, `finding.itemReference`,
`prognosisReference`, `supportingInfo`, note authors, `identifier.assigner`). Search lives in
test_search.py.

R4 requires `status` and `subject` (and `investigation.code`), but only the `java_validator`
backend enforces cardinality minimums (the native structural check does not), so that is not
asserted here.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.clinical_impression.conftest import IMPRESSION_PERMS
from tests.integration.clinical_impression.support import (
    BASE,
    allergy_body,
    condition_body,
    create_allergy_intolerance,
    create_condition,
    create_encounter,
    create_history,
    create_impression,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_report,
    create_risk,
    encounter_body,
    finding,
    full_body,
    history_body,
    impression_body,
    report_body,
    risk_body,
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


def _as_user(sub="u-test", org_id="org-test", permissions=IMPRESSION_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client, patient) -> tuple[int, dict]:
    encounter = await create_encounter(client, encounter_body())
    condition = await create_condition(client, condition_body(patient))
    practitioner = await create_practitioner(client)
    organization = await create_organization(client)
    report = await create_report(client, report_body(patient))
    risk = await create_risk(client, risk_body(patient))
    body = full_body(
        patient, encounter, condition, practitioner, organization, report, risk
    )
    return await create_impression(client, body), body


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_minimal(client, patient):
    resp = await client.post(BASE + "/", json=impression_body(patient))
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert (
        data["resourceType"] == "ClinicalImpression" and data["status"] == "completed"
    )
    assert data["subject"] == {"reference": f"Patient/{patient}"}


async def test_create_full_round_trip(client, patient):
    impression, body = await _full(client, patient)
    data = (await client.get(f"{BASE}/{impression}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_elements_nothing_searches_on(client, patient):
    """`statusReason`, `code`, `description`, `effective[x]`, `protocol`, `summary`, `finding.basis`,
    `investigation.code`, `prognosis*` and `note` live only in `content`."""
    impression, _ = await _full(client, patient)
    data = (await client.get(f"{BASE}/{impression}")).json()
    assert data["statusReason"] == {"text": "Completed after review"}
    assert data["code"]["coding"][0]["code"] == "225338004"
    assert data["description"].startswith("Assessment of")
    assert data["effectiveDateTime"] == "2023-01-15T09:30:00Z"
    assert data["protocol"] == ["http://example.org/protocols/chest-pain"]
    assert data["summary"].startswith("Stable angina")
    assert data["finding"][0]["basis"] == "Exercise ECG and history."
    assert data["investigation"][0]["code"] == {"text": "Initial examination"}
    assert data["prognosisCodeableConcept"] == [{"text": "Good"}]
    assert data["note"][0]["authorString"] == "Nurse Joy"


@pytest.mark.parametrize(
    "extra",
    [
        {"effectiveDateTime": "2023-01"},
        {"effectivePeriod": {"start": "2023-01-01", "end": "2023-06-01"}},
    ],
    ids=["effectiveDateTime", "effectivePeriod"],
)
async def test_create_each_effective_choice_round_trips(client, patient, extra):
    resp = await client.post(BASE + "/", json=impression_body(patient, **extra))
    assert resp.status_code == 201, resp.text
    for key, value in extra.items():
        assert resp.json()[key] == value


@pytest.mark.parametrize("status", ["in-progress", "completed", "entered-in-error"])
async def test_create_every_status_round_trips(client, patient, status):
    resp = await client.post(BASE + "/", json=impression_body(patient, status))
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


async def test_create_ignores_server_managed_id_and_meta(client, patient):
    body = impression_body(
        patient, id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"}
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client, patient):
    for bad in (
        {"status": "robot"},
        {"date": "yesterday"},
        {"code": "x"},
        {"assessor": [{"reference": "Practitioner/1"}]},
        {"problem": {"reference": "Condition/1"}},
        {"investigation": {"code": {"text": "x"}}},
        {"finding": [{"basis": 5}]},
        {"finding": [{"itemCodeableConcept": "x"}]},
        {"identifier": {"value": "x"}},
        {"summary": 5},
        {"note": {"text": "x"}},
        {"protocol": "x"},
    ):
        resp = await client.post(BASE + "/", json=impression_body(patient, **bad))
        assert resp.status_code == 422, (bad, resp.text)
    assert (
        await client.post(
            BASE + "/", json={"status": "completed", "subject": "Patient/1"}
        )
    ).status_code == 422


async def test_create_non_fhir_key_rejected(client, patient, native_validation):
    assert (
        await client.post(
            BASE + "/", json=impression_body(patient, not_a_fhir_element=1)
        )
    ).status_code == 422


async def test_create_old_flat_fields_rejected(client, patient, native_validation):
    for stale in (
        {"code_text": "x"},
        {"effective_date_time": "2020-01-01"},
        {"org_id": "x"},
    ):
        resp = await client.post(BASE + "/", json={**impression_body(patient), **stale})
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client, patient):
    assert (
        await client.post(
            BASE + "/", json=impression_body(patient, resourceType="Patient")
        )
    ).status_code == 422


async def test_create_audit_meta_from_actor(client, patient):
    data = (await client.post(BASE + "/", json=impression_body(patient))).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# ── Create: existence checks on local references ─────────────────────────────


async def test_create_subject_patient_must_exist(client):
    assert (
        await client.post(BASE + "/", json=impression_body(999999))
    ).status_code == 422


async def test_create_subject_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    assert (
        await client.post(BASE + "/", json=impression_body(theirs))
    ).status_code == 422


async def test_create_group_subject_is_not_checked(client):
    body = {"status": "completed", "subject": {"reference": "Group/999999"}}
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == {"reference": "Group/999999"}


async def test_create_encounter_must_exist(client, patient):
    encounter = await create_encounter(client, encounter_body())
    ok = impression_body(patient, encounter={"reference": f"Encounter/{encounter}"})
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    resp = await client.post(
        BASE + "/",
        json=impression_body(patient, encounter={"reference": "Encounter/999999"}),
    )
    assert resp.status_code == 422


async def test_create_assessor_must_exist(client, patient):
    practitioner = await create_practitioner(client)
    role = await create_practitioner_role(client)
    for ref in (f"Practitioner/{practitioner}", f"PractitionerRole/{role}"):
        resp = await client.post(
            BASE + "/", json=impression_body(patient, assessor={"reference": ref})
        )
        assert resp.status_code == 201, (ref, resp.text)
    for missing in ("Practitioner/999999", "PractitionerRole/999999"):
        resp = await client.post(
            BASE + "/", json=impression_body(patient, assessor={"reference": missing})
        )
        assert resp.status_code == 422, (missing, resp.text)


async def test_create_previous_must_exist(client, patient):
    first = await create_impression(client, impression_body(patient))
    ok = impression_body(patient, previous={"reference": f"ClinicalImpression/{first}"})
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    resp = await client.post(
        BASE + "/",
        json=impression_body(
            patient, previous={"reference": "ClinicalImpression/999999"}
        ),
    )
    assert resp.status_code == 422


async def test_create_problem_must_exist(client, patient):
    condition = await create_condition(client, condition_body(patient))
    allergy = await create_allergy_intolerance(client, allergy_body(patient))
    ok = impression_body(
        patient,
        problem=[
            {"reference": f"Condition/{condition}"},
            {"reference": f"AllergyIntolerance/{allergy}"},
        ],
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    for missing in ("Condition/999999", "AllergyIntolerance/999999"):
        resp = await client.post(
            BASE + "/", json=impression_body(patient, problem=[{"reference": missing}])
        )
        assert resp.status_code == 422, (missing, resp.text)


async def test_create_investigation_items_are_checked_for_resources_here(
    client, patient
):
    report = await create_report(client, report_body(patient))
    risk = await create_risk(client, risk_body(patient))
    history = await create_history(client, history_body(patient))
    ok = impression_body(
        patient,
        investigation=[
            {
                "code": {"text": "Set"},
                "item": [
                    {"reference": f"DiagnosticReport/{report}"},
                    {"reference": f"RiskAssessment/{risk}"},
                    {"reference": f"FamilyMemberHistory/{history}"},
                    {"reference": "Observation/999999"},  # not rebuilt: stored as sent
                    {"reference": "Media/999999"},
                ],
            }
        ],
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    for missing in (
        "DiagnosticReport/999999",
        "RiskAssessment/999999",
        "FamilyMemberHistory/999999",
    ):
        body = impression_body(
            patient,
            investigation=[{"code": {"text": "Set"}, "item": [{"reference": missing}]}],
        )
        assert (await client.post(BASE + "/", json=body)).status_code == 422, missing


async def test_create_finding_item_reference_is_checked_for_a_condition(
    client, patient
):
    condition = await create_condition(client, condition_body(patient))
    ok = impression_body(
        patient,
        finding=[
            {"itemReference": {"reference": f"Condition/{condition}"}},
            {"itemReference": {"reference": "Observation/999999"}},
        ],
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = impression_body(
        patient, finding=[{"itemReference": {"reference": "Condition/999999"}}]
    )
    assert (await client.post(BASE + "/", json=bad)).status_code == 422


async def test_create_prognosis_reference_must_exist(client, patient):
    risk = await create_risk(client, risk_body(patient))
    assert (
        await client.post(
            BASE + "/",
            json=impression_body(
                patient, prognosisReference=[{"reference": f"RiskAssessment/{risk}"}]
            ),
        )
    ).status_code == 201
    resp = await client.post(
        BASE + "/",
        json=impression_body(
            patient, prognosisReference=[{"reference": "RiskAssessment/999999"}]
        ),
    )
    assert resp.status_code == 422


async def test_create_supporting_info_is_checked_for_resources_here(client, patient):
    condition = await create_condition(client, condition_body(patient))
    ok = impression_body(
        patient,
        supportingInfo=[
            {"reference": f"Condition/{condition}"},
            {"reference": f"Patient/{patient}"},
            {"reference": "Observation/999999"},
            {"reference": "Questionnaire/999999"},
        ],
    )
    assert (
        await client.post(BASE + "/", json=ok)
    ).status_code == 201  # not rebuilt: stored as sent
    for missing in ("Condition/999999", "Patient/999999"):
        resp = await client.post(
            BASE + "/",
            json=impression_body(patient, supportingInfo=[{"reference": missing}]),
        )
        assert resp.status_code == 422, (missing, resp.text)


async def test_create_note_author_is_checked(client, patient):
    practitioner = await create_practitioner(client)
    ok = impression_body(
        patient,
        note=[
            {
                "text": "n",
                "authorReference": {"reference": f"Practitioner/{practitioner}"},
            }
        ],
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = impression_body(
        patient,
        note=[{"text": "n", "authorReference": {"reference": "Practitioner/999999"}}],
    )
    assert (await client.post(BASE + "/", json=bad)).status_code == 422


async def test_create_identifier_assigner_must_exist(client, patient):
    body = impression_body(
        patient,
        identifier=[{"value": "1", "assigner": {"reference": "Organization/999999"}}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 422
    org = await create_organization(client)
    body = impression_body(
        patient,
        identifier=[{"value": "1", "assigner": {"reference": f"Organization/{org}"}}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_absolute_and_logical_references_not_resolved(client):
    absolute = "https://other.example.org/fhir/Patient/1"
    resp = await client.post(BASE + "/", json=impression_body())
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == {"reference": absolute}
    logical = {
        "identifier": {"system": "urn:pts", "value": "P-9"},
        "display": "External",
    }
    body = impression_body(
        None,
        subject=logical,
        assessor={"reference": "https://other.example.org/fhir/Practitioner/7"},
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == logical
    assert resp.json()["assessor"] == {
        "reference": "https://other.example.org/fhir/Practitioner/7"
    }


# ── Read ─────────────────────────────────────────────────────────────────────


async def test_get_by_id(client, patient):
    impression, _ = await _full(client, patient)
    resp = await client.get(f"{BASE}/{impression}")
    assert resp.status_code == 200 and resp.json()["id"] == str(impression)


async def test_get_is_fhir_regardless_of_accept(client, patient):
    impression = await create_impression(client, impression_body(patient))
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{impression}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "ClinicalImpression"


async def test_xml_only_accept_is_406(client, patient):
    impression = await create_impression(client, impression_body(patient))
    resp = await client.get(
        f"{BASE}/{impression}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_scalar_keeps_the_rest(client, patient):
    impression, _ = await _full(client, patient)
    resp = await client.patch(
        f"{BASE}/{impression}",
        json={"status": "entered-in-error", "summary": "Withdrawn."},
    )
    assert resp.status_code == 200, resp.text
    assert (
        resp.json()["status"] == "entered-in-error"
        and resp.json()["summary"] == "Withdrawn."
    )
    assert resp.json()["subject"] == {"reference": f"Patient/{patient}"}  # untouched
    assert len(resp.json()["finding"]) == 2


async def test_patch_reindexes_search(client, patient):
    impression, _ = await _full(client, patient)
    await client.patch(
        f"{BASE}/{impression}",
        json={
            "date": "2024-05-01",
            "status": "in-progress",
            "finding": [finding("999")],
        },
    )
    for param, old, new in (
        ("date", "2023-01-15", "2024-05-01"),
        ("status", "completed", "in-progress"),
        ("finding-code", "194828000", "999"),
    ):
        assert impression not in _ids(
            (await client.get(BASE + "/", params={param: old})).json()
        ), param
        assert impression in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param


async def test_patch_subject_replaced_and_reindexed(client, patient):
    impression = await create_impression(client, impression_body(patient))
    other = await create_patient(client)
    resp = await client.patch(
        f"{BASE}/{impression}", json={"subject": {"reference": f"Patient/{other}"}}
    )
    assert resp.status_code == 200, resp.text
    assert impression not in _ids(
        (await client.get(BASE + "/", params={"patient": str(patient)})).json()
    )
    assert impression in _ids(
        (await client.get(BASE + "/", params={"patient": str(other)})).json()
    )


async def test_patch_replaces_lists_and_empty_clears(client, patient):
    impression, _ = await _full(client, patient)
    assert impression in _ids(
        (await client.get(BASE + "/", params={"identifier": "CI-1001"})).json()
    )
    resp = await client.patch(
        f"{BASE}/{impression}",
        json={
            "identifier": [],
            "problem": [],
            "investigation": [],
            "finding": [],
            "supportingInfo": [],
            "note": [],
        },
    )
    for gone in (
        "identifier",
        "problem",
        "investigation",
        "finding",
        "supportingInfo",
        "note",
    ):
        assert gone not in resp.json()
    assert resp.json()["summary"].startswith("Stable angina")  # untouched
    for param, value in (("identifier", "CI-1001"), ("finding-code", "194828000")):
        assert impression not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), (param, value)
    for param in ("problem", "investigation", "finding-ref", "supporting-info"):
        assert impression in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_clears_a_date_and_missing_follows(client, patient):
    impression = await create_impression(
        client, impression_body(patient, date="2024-05-01")
    )
    resp = await client.patch(f"{BASE}/{impression}", json={"date": None})
    assert "date" not in resp.json()
    assert impression in _ids(
        (await client.get(BASE + "/", params={"date:missing": "true"})).json()
    )


async def test_patch_nonexistent_reference_rejected_and_nothing_written(
    client, patient
):
    impression = await create_impression(client, impression_body(patient))
    resp = await client.patch(
        f"{BASE}/{impression}", json={"problem": [{"reference": "Condition/999999"}]}
    )
    assert resp.status_code == 422
    assert "problem" not in (await client.get(f"{BASE}/{impression}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client, patient):
    impression = await create_impression(client, impression_body(patient, "completed"))
    assert (
        await client.patch(f"{BASE}/{impression}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{impression}")).json()["status"] == "completed"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "completed"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete(client, patient):
    impression, _ = await _full(client, patient)
    assert (await client.delete(f"{BASE}/{impression}")).status_code == 204
    assert (await client.get(f"{BASE}/{impression}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "CI-1001"),
        ("finding-code", "194828000"),
        ("status", "completed"),
    ):
        assert impression not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_create_without_permission(client, patient):
    _as_user(permissions=["clinical_impression:read"])
    assert (
        await client.post(BASE + "/", json=impression_body(patient))
    ).status_code == 403


async def test_org_less_token_rejected(client, patient):
    impression = await create_impression(client, impression_body(patient))

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": IMPRESSION_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=impression_body())).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{impression}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    impression = await create_impression(client, impression_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{impression}"),
            await other_client.patch(
                f"{BASE}/{impression}", json={"status": "completed"}
            ),
            await other_client.delete(f"{BASE}/{impression}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_impression(
        client,
        impression_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}]),
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()
