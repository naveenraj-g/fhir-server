"""Core risk-assessment endpoint coverage.

RiskAssessment is stored Medplum-style (like Patient, Appointment, Encounter, Condition,
Procedure, DiagnosticReport, Immunization and the other content-based resources): the request
body (genuine FHIR R4 RiskAssessment JSON) is validated and stored whole in `content`, every
response is FHIR R4 (`application/fhir+json`, regardless of Accept), and only the FHIR R4
search parameters are indexed (https://www.hl7.org/fhir/R4/riskassessment.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence checks on every local reference (`subject`, `encounter`,
`condition`, `performer`, `reasonReference`, note authors, `identifier.assigner`). Search lives
in test_search.py.

R4 requires `status` and `subject` (and rules ras-1 / ras-2), but only the `java_validator`
backend enforces cardinality minimums and invariants (the native structural check does not), so
that is not asserted here. Note that `status` has no search parameter on this resource.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.risk_assessment.conftest import ASSESSMENT_PERMS
from tests.integration.risk_assessment.support import (
    BASE,
    assessment_body,
    condition_body,
    create_assessment,
    create_condition,
    create_encounter,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_report,
    encounter_body,
    full_body,
    percent,
    report_body,
    risk,
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


def _as_user(sub="u-test", org_id="org-test", permissions=ASSESSMENT_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client, patient) -> tuple[int, dict]:
    encounter = await create_encounter(client, encounter_body())
    condition = await create_condition(client, condition_body(patient))
    practitioner = await create_practitioner(client)
    organization = await create_organization(client)
    body = full_body(patient, encounter, condition, practitioner, organization)
    return await create_assessment(client, body), body


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_minimal(client, patient):
    resp = await client.post(BASE + "/", json=assessment_body(patient))
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "RiskAssessment" and data["status"] == "final"
    assert data["subject"] == {"reference": f"Patient/{patient}"}


async def test_create_full_round_trip(client, patient):
    assessment, body = await _full(client, patient)
    data = (await client.get(f"{BASE}/{assessment}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_elements_nothing_searches_on(client, patient):
    """`status`, `basedOn`, `parent`, `code`, `reasonCode`, `basis`, `mitigation`, `note` and every
    prediction element but the probability and the qualitative risk live only in `content`."""
    assessment, _ = await _full(client, patient)
    data = (await client.get(f"{BASE}/{assessment}")).json()
    assert data["status"] == "final"
    assert data["basedOn"] == {"reference": "ServiceRequest/80001"} and data[
        "parent"
    ] == {"reference": "Device/580001"}
    assert data["code"]["coding"][0]["code"] == "709510001"
    assert data["reasonCode"] == [{"text": "Family history of heart disease"}]
    assert data["basis"] == [{"reference": "Observation/160002"}]
    assert data["mitigation"] == "Statin therapy and lifestyle changes."
    assert data["note"][0]["authorString"] == "Nurse Joy"
    first, second = data["prediction"]
    assert (
        first["outcome"]["coding"][0]["code"] == "54329005"
        and first["relativeRisk"] == 1.4
    )
    assert first["whenRange"]["low"]["value"] == 40 and first["rationale"].startswith(
        "Based on"
    )
    assert second["whenPeriod"] == {"start": "2023-01-01", "end": "2033-01-01"}


@pytest.mark.parametrize(
    "extra",
    [
        {"occurrenceDateTime": "2023-01"},
        {"occurrencePeriod": {"start": "2023-01-01", "end": "2023-06-01"}},
    ],
    ids=["occurrenceDateTime", "occurrencePeriod"],
)
async def test_create_each_occurrence_choice_round_trips(client, patient, extra):
    resp = await client.post(BASE + "/", json=assessment_body(patient, **extra))
    assert resp.status_code == 201, resp.text
    for key, value in extra.items():
        assert resp.json()[key] == value


@pytest.mark.parametrize(
    "prediction",
    [
        {"probabilityDecimal": 25},
        {"probabilityRange": {"low": percent(10), "high": percent(20)}},
        {"probabilityRange": {"low": percent(10)}},
        {"whenPeriod": {"start": "2023-01-01"}, "qualitativeRisk": risk("high")},
        {"whenRange": {"high": {"value": 10, "unit": "yr"}}, "relativeRisk": 2},
    ],
    ids=["decimal", "range", "open-range", "whenPeriod", "whenRange"],
)
async def test_create_each_prediction_choice_round_trips(client, patient, prediction):
    resp = await client.post(
        BASE + "/", json=assessment_body(patient, prediction=[prediction])
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["prediction"] == [prediction]


@pytest.mark.parametrize(
    "status",
    [
        "registered",
        "preliminary",
        "final",
        "amended",
        "corrected",
        "cancelled",
        "entered-in-error",
        "unknown",
    ],
)
async def test_create_every_status_round_trips(client, patient, status):
    resp = await client.post(BASE + "/", json=assessment_body(patient, status))
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


async def test_create_ignores_server_managed_id_and_meta(client, patient):
    body = assessment_body(
        patient, id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"}
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client, patient):
    for bad in (
        {"status": "robot"},
        {"occurrenceDateTime": "yesterday"},
        {"method": "x"},
        {"performer": [{"reference": "Practitioner/1"}]},
        {"prediction": {"probabilityDecimal": 5}},
        {"prediction": [{"probabilityDecimal": "high"}]},
        {"prediction": [{"qualitativeRisk": "low"}]},
        {"prediction": [{"relativeRisk": "twice"}]},
        {"identifier": {"value": "x"}},
        {"mitigation": 5},
        {"note": {"text": "x"}},
    ):
        resp = await client.post(BASE + "/", json=assessment_body(patient, **bad))
        assert resp.status_code == 422, (bad, resp.text)
    assert (
        await client.post(BASE + "/", json={"status": "final", "subject": "Patient/1"})
    ).status_code == 422


async def test_create_non_fhir_key_rejected(client, patient, native_validation):
    assert (
        await client.post(
            BASE + "/", json=assessment_body(patient, not_a_fhir_element=1)
        )
    ).status_code == 422


async def test_create_old_flat_fields_rejected(client, patient, native_validation):
    for stale in (
        {"method_text": "x"},
        {"occurrence_date_time": "2020-01-01"},
        {"org_id": "x"},
    ):
        resp = await client.post(BASE + "/", json={**assessment_body(patient), **stale})
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client, patient):
    assert (
        await client.post(
            BASE + "/", json=assessment_body(patient, resourceType="Patient")
        )
    ).status_code == 422


async def test_create_audit_meta_from_actor(client, patient):
    data = (await client.post(BASE + "/", json=assessment_body(patient))).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# ── Create: existence checks on local references ─────────────────────────────


async def test_create_subject_patient_must_exist(client):
    assert (
        await client.post(BASE + "/", json=assessment_body(999999))
    ).status_code == 422


async def test_create_subject_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    assert (
        await client.post(BASE + "/", json=assessment_body(theirs))
    ).status_code == 422


async def test_create_group_subject_must_exist(client):
    body = {"status": "final", "subject": {"reference": "Group/430001"}}
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == {"reference": "Group/430001"}
    missing = {"status": "final", "subject": {"reference": "Group/999999"}}
    assert (await client.post(BASE + "/", json=missing)).status_code == 422


async def test_create_encounter_and_condition_must_exist(client, patient):
    encounter = await create_encounter(client, encounter_body())
    condition = await create_condition(client, condition_body(patient))
    ok = assessment_body(
        patient,
        encounter={"reference": f"Encounter/{encounter}"},
        condition={"reference": f"Condition/{condition}"},
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    for element, missing in (
        ("encounter", "Encounter/999999"),
        ("condition", "Condition/999999"),
    ):
        resp = await client.post(
            BASE + "/",
            json=assessment_body(patient, **{element: {"reference": missing}}),
        )
        assert resp.status_code == 422, (element, resp.text)


async def test_create_performer_is_checked_except_a_device(client, patient):
    practitioner = await create_practitioner(client)
    role = await create_practitioner_role(client)
    for ref in (
        f"Practitioner/{practitioner}",
        f"PractitionerRole/{role}",
        "Device/999999",
    ):
        resp = await client.post(
            BASE + "/", json=assessment_body(patient, performer={"reference": ref})
        )
        assert resp.status_code == 201, (
            ref,
            resp.text,
        )  # a Device is not a resource here: stored as sent
    for missing in ("Practitioner/999999", "PractitionerRole/999999"):
        resp = await client.post(
            BASE + "/", json=assessment_body(patient, performer={"reference": missing})
        )
        assert resp.status_code == 422, (missing, resp.text)


async def test_create_reason_reference_is_checked_for_resources_here(client, patient):
    condition = await create_condition(client, condition_body(patient))
    report = await create_report(client, report_body(patient))
    ok = assessment_body(
        patient,
        reasonReference=[
            {"reference": f"Condition/{condition}"},
            {"reference": f"DiagnosticReport/{report}"},
            {"reference": "Observation/160005"},
        ],
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    for missing in (
        "DocumentReference/999999",
        "Condition/999999",
        "DiagnosticReport/999999",
        "Observation/999999",
    ):
        resp = await client.post(
            BASE + "/",
            json=assessment_body(patient, reasonReference=[{"reference": missing}]),
        )
        assert resp.status_code == 422, (missing, resp.text)


async def test_create_reference_any_elements_are_checked_for_rebuilt_types(
    client, patient
):
    """basedOn, parent and basis are Reference(Any): a rebuilt type must exist, a type this
    server does not have (a Device, a DeviceRequest) is stored as sent."""
    stored = assessment_body(
        patient,
        basedOn={"reference": "Device/999998"},
        parent={"reference": "Device/999999"},
        basis=[{"reference": "Device/999997"}],
    )
    assert (await client.post(BASE + "/", json=stored)).status_code == 201
    for element, ref in (
        ("basedOn", {"reference": "ServiceRequest/999999"}),
        ("parent", {"reference": "Procedure/999999"}),
        ("parent", {"reference": "MedicationAdministration/999999"}),
        ("basis", [{"reference": "Observation/999999"}]),
    ):
        body = assessment_body(patient, **{element: ref})
        assert (await client.post(BASE + "/", json=body)).status_code == 422, element


async def test_create_note_author_is_checked(client, patient):
    practitioner = await create_practitioner(client)
    ok = assessment_body(
        patient,
        note=[
            {
                "text": "n",
                "authorReference": {"reference": f"Practitioner/{practitioner}"},
            }
        ],
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = assessment_body(
        patient,
        note=[{"text": "n", "authorReference": {"reference": "Practitioner/999999"}}],
    )
    assert (await client.post(BASE + "/", json=bad)).status_code == 422


async def test_create_identifier_assigner_must_exist(client, patient):
    body = assessment_body(
        patient,
        identifier=[{"value": "1", "assigner": {"reference": "Organization/999999"}}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 422
    org = await create_organization(client)
    body = assessment_body(
        patient,
        identifier=[{"value": "1", "assigner": {"reference": f"Organization/{org}"}}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_absolute_and_logical_references_not_resolved(client):
    absolute = "https://other.example.org/fhir/Patient/1"
    resp = await client.post(BASE + "/", json=assessment_body())
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == {"reference": absolute}
    logical = {
        "identifier": {"system": "urn:pts", "value": "P-9"},
        "display": "External",
    }
    body = assessment_body(
        None,
        subject=logical,
        performer={"reference": "https://other.example.org/fhir/Practitioner/7"},
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == logical
    assert resp.json()["performer"] == {
        "reference": "https://other.example.org/fhir/Practitioner/7"
    }


# ── Read ─────────────────────────────────────────────────────────────────────


async def test_get_by_id(client, patient):
    assessment, _ = await _full(client, patient)
    resp = await client.get(f"{BASE}/{assessment}")
    assert resp.status_code == 200 and resp.json()["id"] == str(assessment)


async def test_get_is_fhir_regardless_of_accept(client, patient):
    assessment = await create_assessment(client, assessment_body(patient))
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{assessment}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "RiskAssessment"


async def test_xml_only_accept_is_406(client, patient):
    assessment = await create_assessment(client, assessment_body(patient))
    resp = await client.get(
        f"{BASE}/{assessment}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_scalar_keeps_the_rest(client, patient):
    assessment, _ = await _full(client, patient)
    resp = await client.patch(
        f"{BASE}/{assessment}", json={"status": "amended", "mitigation": "Diet only."}
    )
    assert resp.status_code == 200, resp.text
    assert (
        resp.json()["status"] == "amended" and resp.json()["mitigation"] == "Diet only."
    )
    assert resp.json()["subject"] == {"reference": f"Patient/{patient}"}  # untouched
    assert len(resp.json()["prediction"]) == 2


async def test_patch_reindexes_search(client, patient):
    assessment, _ = await _full(client, patient)
    await client.patch(
        f"{BASE}/{assessment}",
        json={
            "occurrenceDateTime": "2024-05-01",
            "method": {"coding": [{"system": "http://snomed.info/sct", "code": "999"}]},
            "prediction": [{"probabilityDecimal": 80, "qualitativeRisk": risk("high")}],
        },
    )
    for param, old, new in (
        ("date", "2023-01-15", "2024-05-01"),
        ("method", "225338004", "999"),
        ("risk", "moderate", "high"),
        ("probability", "12.5", "80"),
    ):
        assert assessment not in _ids(
            (await client.get(BASE + "/", params={param: old})).json()
        ), param
        assert assessment in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param


async def test_patch_subject_replaced_and_reindexed(client, patient):
    assessment = await create_assessment(client, assessment_body(patient))
    other = await create_patient(client)
    resp = await client.patch(
        f"{BASE}/{assessment}", json={"subject": {"reference": f"Patient/{other}"}}
    )
    assert resp.status_code == 200, resp.text
    assert assessment not in _ids(
        (await client.get(BASE + "/", params={"patient": str(patient)})).json()
    )
    assert assessment in _ids(
        (await client.get(BASE + "/", params={"patient": str(other)})).json()
    )


async def test_patch_replaces_lists_and_empty_clears(client, patient):
    assessment, _ = await _full(client, patient)
    assert assessment in _ids(
        (await client.get(BASE + "/", params={"identifier": "RA-1001"})).json()
    )
    resp = await client.patch(
        f"{BASE}/{assessment}",
        json={
            "identifier": [],
            "prediction": [],
            "reasonCode": [],
            "reasonReference": [],
            "basis": [],
            "note": [],
        },
    )
    for gone in (
        "identifier",
        "prediction",
        "reasonCode",
        "reasonReference",
        "basis",
        "note",
    ):
        assert gone not in resp.json()
    assert (
        resp.json()["mitigation"] == "Statin therapy and lifestyle changes."
    )  # untouched
    for param, value in (
        ("identifier", "RA-1001"),
        ("risk", "moderate"),
        ("probability", "12.5"),
        ("risk", "low"),
    ):
        assert assessment not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), (param, value)
    assert assessment in _ids(
        (await client.get(BASE + "/", params={"probability:missing": "true"})).json()
    )


async def test_patch_clears_a_date_and_missing_follows(client, patient):
    assessment = await create_assessment(
        client, assessment_body(patient, occurrenceDateTime="2024-05-01")
    )
    resp = await client.patch(f"{BASE}/{assessment}", json={"occurrenceDateTime": None})
    assert "occurrenceDateTime" not in resp.json()
    assert assessment in _ids(
        (await client.get(BASE + "/", params={"date:missing": "true"})).json()
    )


async def test_patch_nonexistent_reference_rejected_and_nothing_written(
    client, patient
):
    assessment = await create_assessment(client, assessment_body(patient))
    resp = await client.patch(
        f"{BASE}/{assessment}", json={"condition": {"reference": "Condition/999999"}}
    )
    assert resp.status_code == 422
    assert "condition" not in (await client.get(f"{BASE}/{assessment}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client, patient):
    assessment = await create_assessment(client, assessment_body(patient, "final"))
    assert (
        await client.patch(f"{BASE}/{assessment}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{assessment}")).json()["status"] == "final"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "amended"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete(client, patient):
    assessment, _ = await _full(client, patient)
    assert (await client.delete(f"{BASE}/{assessment}")).status_code == 204
    assert (await client.get(f"{BASE}/{assessment}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "RA-1001"),
        ("method", "225338004"),
        ("risk", "moderate"),
        ("probability", "12.5"),
    ):
        assert assessment not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_create_without_permission(client, patient):
    _as_user(permissions=["risk_assessment:read"])
    assert (
        await client.post(BASE + "/", json=assessment_body(patient))
    ).status_code == 403


async def test_org_less_token_rejected(client, patient):
    assessment = await create_assessment(client, assessment_body(patient))

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": ASSESSMENT_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=assessment_body())).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{assessment}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    assessment = await create_assessment(client, assessment_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{assessment}"),
            await other_client.patch(
                f"{BASE}/{assessment}", json={"status": "amended"}
            ),
            await other_client.delete(f"{BASE}/{assessment}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_assessment(
        client,
        assessment_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}]),
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()
