"""Core immunization-recommendation endpoint coverage.

ImmunizationRecommendation is stored Medplum-style (like Patient, Appointment, Encounter,
Condition, Procedure, DiagnosticReport, Immunization and the other content-based
resources): the request body (genuine FHIR R4 ImmunizationRecommendation JSON) is
validated and stored whole in `content`, every response is FHIR R4
(`application/fhir+json`, regardless of Accept), and only the FHIR R4 search parameters
are indexed (https://www.hl7.org/fhir/R4/immunizationrecommendation.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing scope,
cross-org isolation) plus the existence checks on every local reference (`patient`,
`authority`, `supportingImmunization`, `supportingPatientInformation`,
`identifier.assigner`). Search lives in test_search.py.

R4 requires `patient`, `date` and a `recommendation` (with a `forecastStatus`, and a
`vaccineCode` or `targetDisease`), but only the `java_validator` backend enforces
cardinality minimums (the native structural check does not), so that is not asserted here.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.immunization_recommendation.conftest import RECOMMENDATION_PERMS
from tests.integration.immunization_recommendation.support import (
    BASE,
    condition_body,
    create_condition,
    create_evaluation,
    create_immunization,
    create_organization,
    create_patient,
    create_recommendation,
    entry,
    evaluation_body,
    full_body,
    immunization_body,
    recommendation_body,
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


def _as_user(sub="u-test", org_id="org-test", permissions=RECOMMENDATION_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client, patient) -> tuple[int, dict]:
    organization = await create_organization(client)
    immunization = await create_immunization(client, immunization_body(patient))
    condition = await create_condition(client, condition_body(patient))
    evaluation = await create_evaluation(client, evaluation_body(patient, immunization))
    body = full_body(patient, organization, immunization, condition, evaluation)
    return await create_recommendation(client, body), body


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_minimal(client, patient):
    resp = await client.post(BASE + "/", json=recommendation_body(patient))
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "ImmunizationRecommendation"
    assert data["patient"] == {"reference": f"Patient/{patient}"}
    assert data["recommendation"][0]["forecastStatus"]["coding"][0]["code"] == "due"


async def test_create_full_round_trip(client, patient):
    recommendation, body = await _full(client, patient)
    data = (await client.get(f"{BASE}/{recommendation}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_elements_nothing_searches_on(client, patient):
    """`authority`, `contraindicatedVaccineCode`, `forecastReason`, `dateCriterion`, `description`, `series`
    and the dose numbers live only in `content`."""
    recommendation, _ = await _full(client, patient)
    data = (await client.get(f"{BASE}/{recommendation}")).json()
    assert data["authority"]["reference"].startswith("Organization/")
    first, second = data["recommendation"]
    assert first["contraindicatedVaccineCode"][0]["coding"][0]["code"] == "99"
    assert first["forecastReason"] == [{"text": "Seasonal"}]
    assert first["dateCriterion"][0]["value"] == "2023-06-01T00:00:00Z"
    assert first["description"] == "Seasonal flu shot" and first["series"] == "Seasonal"
    assert first["doseNumberPositiveInt"] == 1 and first["seriesDosesPositiveInt"] == 1
    assert (
        second["doseNumberString"] == "booster"
        and second["seriesDosesString"] == "many"
    )


async def test_create_partial_date_round_trips(client, patient):
    resp = await client.post(
        BASE + "/", json=recommendation_body(patient, date="2023-01")
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["date"] == "2023-01"


async def test_create_ignores_server_managed_id_and_meta(client, patient):
    body = recommendation_body(
        patient, id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"}
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client, patient):
    for bad in (
        {"date": "yesterday"},
        {"recommendation": {"series": "x"}},
        {"identifier": {"value": "x"}},
        {"recommendation": [{"forecastStatus": "due"}]},
        {"recommendation": [{"vaccineCode": {"text": "x"}}]},
        {
            "recommendation": [
                {"supportingImmunization": {"reference": "Immunization/1"}}
            ]
        },
        {"recommendation": [{"doseNumberPositiveInt": "one"}]},
    ):
        resp = await client.post(BASE + "/", json=recommendation_body(patient, **bad))
        assert resp.status_code == 422, (bad, resp.text)
    assert (
        await client.post(
            BASE + "/", json={"patient": "Patient/1", "date": "2023-01-01"}
        )
    ).status_code == 422


async def test_create_non_fhir_key_rejected(client, patient, native_validation):
    assert (
        await client.post(
            BASE + "/", json=recommendation_body(patient, not_a_fhir_element=1)
        )
    ).status_code == 422


async def test_create_old_flat_fields_rejected(client, patient, native_validation):
    for stale in (
        {"target_disease_text": "x"},
        {"forecast_status": "due"},
        {"org_id": "x"},
    ):
        resp = await client.post(
            BASE + "/", json={**recommendation_body(patient), **stale}
        )
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client, patient):
    assert (
        await client.post(
            BASE + "/", json=recommendation_body(patient, resourceType="Patient")
        )
    ).status_code == 422


async def test_create_audit_meta_from_actor(client, patient):
    data = (await client.post(BASE + "/", json=recommendation_body(patient))).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# ── Create: existence checks on local references ─────────────────────────────


async def test_create_patient_must_exist(client):
    assert (
        await client.post(BASE + "/", json=recommendation_body(999999))
    ).status_code == 422


async def test_create_patient_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    assert (
        await client.post(BASE + "/", json=recommendation_body(theirs))
    ).status_code == 422


async def test_create_authority_must_exist(client, patient):
    missing = recommendation_body(
        patient, authority={"reference": "Organization/999999"}
    )
    assert (await client.post(BASE + "/", json=missing)).status_code == 422
    org = await create_organization(client)
    ok = recommendation_body(patient, authority={"reference": f"Organization/{org}"})
    assert (await client.post(BASE + "/", json=ok)).status_code == 201


async def test_create_supporting_immunization_and_evaluation_are_both_checked(
    client, patient
):
    immunization = await create_immunization(client, immunization_body(patient))
    evaluation = await create_evaluation(client, evaluation_body(patient, immunization))
    ok = recommendation_body(
        patient,
        recommendation=[
            entry(
                supportingImmunization=[
                    {"reference": f"Immunization/{immunization}"},
                    {"reference": f"ImmunizationEvaluation/{evaluation}"},
                ]
            )
        ],
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    for missing in ("Immunization/999999", "ImmunizationEvaluation/999999"):
        body = recommendation_body(
            patient,
            recommendation=[entry(supportingImmunization=[{"reference": missing}])],
        )
        assert (await client.post(BASE + "/", json=body)).status_code == 422, missing


async def test_create_supporting_patient_information_is_checked_for_resources_here(
    client, patient
):
    condition = await create_condition(client, condition_body(patient))
    ok = recommendation_body(
        patient,
        recommendation=[
            entry(
                supportingPatientInformation=[
                    {"reference": f"Condition/{condition}"},
                    {"reference": "Observation/160005"},
                ]
            )
        ],
    )
    assert (
        await client.post(BASE + "/", json=ok)
    ).status_code == 201  # an existing Observation is accepted
    missing = recommendation_body(
        patient,
        recommendation=[
            entry(supportingPatientInformation=[{"reference": "Condition/999999"}])
        ],
    )
    assert (await client.post(BASE + "/", json=missing)).status_code == 422


async def test_create_identifier_assigner_must_exist(client, patient):
    body = recommendation_body(
        patient,
        identifier=[{"value": "1", "assigner": {"reference": "Organization/999999"}}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 422
    org = await create_organization(client)
    body = recommendation_body(
        patient,
        identifier=[{"value": "1", "assigner": {"reference": f"Organization/{org}"}}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_absolute_and_logical_references_not_resolved(client):
    absolute = "https://other.example.org/fhir/Patient/1"
    resp = await client.post(BASE + "/", json=recommendation_body())
    assert resp.status_code == 201, resp.text
    assert resp.json()["patient"] == {"reference": absolute}
    logical = {
        "identifier": {"system": "urn:pts", "value": "P-9"},
        "display": "External",
    }
    body = recommendation_body(
        None,
        patient=logical,
        recommendation=[
            entry(
                supportingImmunization=[
                    {"reference": "https://other.example.org/fhir/Immunization/7"}
                ]
            )
        ],
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["patient"] == logical
    assert resp.json()["recommendation"][0]["supportingImmunization"] == [
        {"reference": "https://other.example.org/fhir/Immunization/7"}
    ]


# ── Read ─────────────────────────────────────────────────────────────────────


async def test_get_by_id(client, patient):
    recommendation, _ = await _full(client, patient)
    resp = await client.get(f"{BASE}/{recommendation}")
    assert resp.status_code == 200 and resp.json()["id"] == str(recommendation)


async def test_get_is_fhir_regardless_of_accept(client, patient):
    recommendation = await create_recommendation(client, recommendation_body(patient))
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{recommendation}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "ImmunizationRecommendation"


async def test_xml_only_accept_is_406(client, patient):
    recommendation = await create_recommendation(client, recommendation_body(patient))
    resp = await client.get(
        f"{BASE}/{recommendation}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_scalar_keeps_the_rest(client, patient):
    recommendation, _ = await _full(client, patient)
    resp = await client.patch(
        f"{BASE}/{recommendation}", json={"date": "2024-05-01T00:00:00Z"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["date"] == "2024-05-01T00:00:00Z"
    assert resp.json()["patient"] == {"reference": f"Patient/{patient}"}  # untouched
    assert resp.json()["authority"]["reference"].startswith("Organization/")
    assert len(resp.json()["recommendation"]) == 2


async def test_patch_reindexes_search(client, patient):
    recommendation, _ = await _full(client, patient)
    await client.patch(
        f"{BASE}/{recommendation}",
        json={
            "date": "2024-05-01",
            "recommendation": [
                entry(
                    vaccineCode=[
                        {
                            "coding": [
                                {"system": "http://hl7.org/fhir/sid/cvx", "code": "21"}
                            ]
                        }
                    ]
                )
            ],
        },
    )
    for param, old, new in (
        ("date", "2023-01-15", "2024-05-01"),
        ("vaccine-type", "140", "21"),
    ):
        assert recommendation not in _ids(
            (await client.get(BASE + "/", params={param: old})).json()
        ), param
        assert recommendation in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param
    assert recommendation not in _ids(
        (await client.get(BASE + "/", params={"target-disease": "6142004"})).json()
    )


async def test_patch_patient_replaced_and_reindexed(client, patient):
    recommendation = await create_recommendation(client, recommendation_body(patient))
    other = await create_patient(client)
    resp = await client.patch(
        f"{BASE}/{recommendation}", json={"patient": {"reference": f"Patient/{other}"}}
    )
    assert resp.status_code == 200, resp.text
    assert recommendation not in _ids(
        (await client.get(BASE + "/", params={"patient": str(patient)})).json()
    )
    assert recommendation in _ids(
        (await client.get(BASE + "/", params={"patient": str(other)})).json()
    )


async def test_patch_replaces_lists_and_empty_clears(client, patient):
    recommendation, _ = await _full(client, patient)
    assert recommendation in _ids(
        (await client.get(BASE + "/", params={"identifier": "IR-1001"})).json()
    )
    resp = await client.patch(
        f"{BASE}/{recommendation}", json={"identifier": [], "recommendation": [entry()]}
    )
    assert "identifier" not in resp.json()
    assert len(resp.json()["recommendation"]) == 1
    assert resp.json()["authority"]["reference"].startswith(
        "Organization/"
    )  # untouched
    for param, value in (
        ("identifier", "IR-1001"),
        ("target-disease", "6142004"),
        ("vaccine-type", "03"),
    ):
        assert recommendation not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param
    for param in ("support", "information"):
        assert recommendation in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_nonexistent_reference_rejected_and_nothing_written(
    client, patient
):
    recommendation = await create_recommendation(client, recommendation_body(patient))
    resp = await client.patch(
        f"{BASE}/{recommendation}",
        json={"authority": {"reference": "Organization/999999"}},
    )
    assert resp.status_code == 422
    assert "authority" not in (await client.get(f"{BASE}/{recommendation}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client, patient):
    recommendation = await create_recommendation(client, recommendation_body(patient))
    assert (
        await client.patch(f"{BASE}/{recommendation}", json={"date": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{recommendation}")).json()[
        "date"
    ] == "2023-01-15T09:30:00Z"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"date": "2024-05-01"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete(client, patient):
    recommendation, _ = await _full(client, patient)
    assert (await client.delete(f"{BASE}/{recommendation}")).status_code == 204
    assert (await client.get(f"{BASE}/{recommendation}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "IR-1001"),
        ("vaccine-type", "140"),
        ("target-disease", "6142004"),
        ("status", "due"),
    ):
        assert recommendation not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_create_without_permission(client, patient):
    _as_user(permissions=["immunization_recommendation:read"])
    assert (
        await client.post(BASE + "/", json=recommendation_body(patient))
    ).status_code == 403


async def test_org_less_token_rejected(client, patient):
    recommendation = await create_recommendation(client, recommendation_body(patient))

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": RECOMMENDATION_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (
        await client.post(BASE + "/", json=recommendation_body())
    ).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{recommendation}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    recommendation = await create_recommendation(client, recommendation_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{recommendation}"),
            await other_client.patch(
                f"{BASE}/{recommendation}", json={"date": "2024-05-01"}
            ),
            await other_client.delete(f"{BASE}/{recommendation}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_recommendation(
        client,
        recommendation_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}]),
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()


async def test_create_supporting_patient_information_observation_must_exist(
    client, patient
):
    missing = recommendation_body(
        patient,
        recommendation=[
            entry(supportingPatientInformation=[{"reference": "Observation/999999"}])
        ],
    )
    assert (await client.post(BASE + "/", json=missing)).status_code == 422
