"""Core family-member-history endpoint coverage.

FamilyMemberHistory is stored Medplum-style (like Patient, Appointment, Encounter, Condition,
Procedure, DiagnosticReport, Immunization and the other content-based resources): the request
body (genuine FHIR R4 FamilyMemberHistory JSON) is validated and stored whole in `content`,
every response is FHIR R4 (`application/fhir+json`, regardless of Accept), and only the FHIR
R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/familymemberhistory.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing scope,
cross-org isolation) plus the existence checks on every local reference (`patient`,
`reasonReference`, note authors, `identifier.assigner`). Search lives in test_search.py.

R4 requires `status`, `patient` and `relationship` (and rules fhs-1 / fhs-2), but only the
`java_validator` backend enforces cardinality minimums and invariants (the native structural
check does not), so that is not asserted here.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.family_member_history.conftest import HISTORY_PERMS
from tests.integration.family_member_history.support import (
    BASE,
    allergy_body,
    condition_body,
    create_allergy_intolerance,
    create_condition,
    create_history,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_report,
    disease,
    full_body,
    history_body,
    relationship,
    report_body,
    sex,
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


def _as_user(sub="u-test", org_id="org-test", permissions=HISTORY_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client, patient) -> tuple[int, dict]:
    organization = await create_organization(client)
    practitioner = await create_practitioner(client)
    condition = await create_condition(client, condition_body(patient))
    body = full_body(patient, organization, practitioner, condition)
    return await create_history(client, body), body


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_minimal(client, patient):
    resp = await client.post(BASE + "/", json=history_body(patient))
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert (
        data["resourceType"] == "FamilyMemberHistory" and data["status"] == "completed"
    )
    assert data["patient"] == {"reference": f"Patient/{patient}"}
    assert data["relationship"]["coding"][0]["code"] == "MTH"


async def test_create_full_round_trip(client, patient):
    history, body = await _full(client, patient)
    data = (await client.get(f"{BASE}/{history}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_elements_nothing_searches_on(client, patient):
    """`name`, `age[x]`, `deceased[x]`, `reasonCode`, `note`, `dataAbsentReason` and every condition
    element but `code` live only in `content`."""
    history, _ = await _full(client, patient)
    data = (await client.get(f"{BASE}/{history}")).json()
    assert data["name"] == "Mary Windsor"
    assert (
        data["ageAge"]["value"] == 70
        and data["estimatedAge"] is True
        and data["deceasedBoolean"] is False
    )
    assert data["reasonCode"][0]["coding"][0]["code"] == "160303001"
    assert data["note"][0]["authorString"] == "Nurse Joy"
    assert data["dataAbsentReason"]["coding"][0]["code"] == "withheld"
    first, second = data["condition"]
    assert (
        first["outcome"]["coding"][0]["code"] == "6736007"
        and first["contributedToDeath"] is False
    )
    assert (
        first["onsetAge"]["value"] == 42
        and first["note"][0]["text"] == "Insulin from 55"
    )
    assert second["onsetString"] == "in her fifties"


@pytest.mark.parametrize(
    "extra",
    [
        {"bornDate": "1950-03-12"},
        {"bornPeriod": {"start": "1950-01-01", "end": "1951-01-01"}},
        {"bornString": "around 1950"},
        {"ageAge": {"value": 70, "unit": "yr"}, "estimatedAge": False},
        {
            "ageRange": {
                "low": {"value": 60, "unit": "yr"},
                "high": {"value": 70, "unit": "yr"},
            }
        },
        {"ageString": "elderly"},
        {"deceasedBoolean": True},
        {"deceasedAge": {"value": 80, "comparator": ">", "unit": "yr"}},
        {
            "deceasedRange": {
                "low": {"value": 70, "unit": "yr"},
                "high": {"value": 80, "unit": "yr"},
            }
        },
        {"deceasedDate": "2010-05-01"},
        {"deceasedString": "in the war"},
    ],
    ids=[
        "bornDate",
        "bornPeriod",
        "bornString",
        "ageAge",
        "ageRange",
        "ageString",
        "deceasedBoolean",
        "deceasedAge",
        "deceasedRange",
        "deceasedDate",
        "deceasedString",
    ],
)
async def test_create_each_born_age_and_deceased_choice_round_trips(
    client, patient, extra
):
    resp = await client.post(BASE + "/", json=history_body(patient, **extra))
    assert resp.status_code == 201, resp.text
    for key, value in extra.items():
        assert resp.json()[key] == value


@pytest.mark.parametrize(
    "onset",
    [
        {"onsetAge": {"value": 42, "unit": "yr"}},
        {
            "onsetRange": {
                "low": {"value": 40, "unit": "yr"},
                "high": {"value": 50, "unit": "yr"},
            }
        },
        {"onsetPeriod": {"start": "1990-01-01", "end": "1991-01-01"}},
        {"onsetString": "childhood"},
    ],
    ids=["onsetAge", "onsetRange", "onsetPeriod", "onsetString"],
)
async def test_create_each_condition_onset_choice_round_trips(client, patient, onset):
    body = history_body(patient, condition=[{"code": disease("44054006"), **onset}])
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    for key, value in onset.items():
        assert resp.json()["condition"][0][key] == value


@pytest.mark.parametrize(
    "status", ["partial", "completed", "entered-in-error", "health-unknown"]
)
async def test_create_every_status_round_trips(client, patient, status):
    resp = await client.post(BASE + "/", json=history_body(patient, status))
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


async def test_create_ignores_server_managed_id_and_meta(client, patient):
    body = history_body(patient, id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"})
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client, patient):
    for bad in (
        {"status": "robot"},
        {"date": "yesterday"},
        {"relationship": "MTH"},
        {"sex": "female"},
        {"condition": {"code": {"text": "x"}}},
        {"identifier": {"value": "x"}},
        {"estimatedAge": "yes"},
        {"instantiatesCanonical": "http://x"},
        {"bornDate": "long ago"},
        {"ageAge": "70"},
    ):
        resp = await client.post(BASE + "/", json=history_body(patient, **bad))
        assert resp.status_code == 422, (bad, resp.text)
    assert (
        await client.post(
            BASE + "/", json={"status": "completed", "patient": "Patient/1"}
        )
    ).status_code == 422


async def test_create_non_fhir_key_rejected(client, patient, native_validation):
    assert (
        await client.post(BASE + "/", json=history_body(patient, not_a_fhir_element=1))
    ).status_code == 422


async def test_create_old_flat_fields_rejected(client, patient, native_validation):
    for stale in (
        {"relationship_text": "x"},
        {"born_date": "1950-01-01"},
        {"org_id": "x"},
    ):
        resp = await client.post(BASE + "/", json={**history_body(patient), **stale})
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client, patient):
    assert (
        await client.post(
            BASE + "/", json=history_body(patient, resourceType="Patient")
        )
    ).status_code == 422


async def test_create_audit_meta_from_actor(client, patient):
    data = (await client.post(BASE + "/", json=history_body(patient))).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# ── Create: existence checks on local references ─────────────────────────────


async def test_create_patient_must_exist(client):
    assert (await client.post(BASE + "/", json=history_body(999999))).status_code == 422


async def test_create_patient_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    assert (await client.post(BASE + "/", json=history_body(theirs))).status_code == 422


async def test_create_reason_reference_is_checked_for_resources_here(client, patient):
    condition = await create_condition(client, condition_body(patient))
    allergy = await create_allergy_intolerance(client, allergy_body(patient))
    report = await create_report(client, report_body(patient))
    ok = history_body(
        patient,
        reasonReference=[
            {"reference": f"Condition/{condition}"},
            {"reference": f"AllergyIntolerance/{allergy}"},
            {"reference": f"DiagnosticReport/{report}"},
            {"reference": "Observation/160005"},
            {"reference": "QuestionnaireResponse/999999"},
        ],
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    for missing in (
        "Condition/999999",
        "AllergyIntolerance/999999",
        "DiagnosticReport/999999",
        "DocumentReference/999999",
    ):
        resp = await client.post(
            BASE + "/",
            json=history_body(patient, reasonReference=[{"reference": missing}]),
        )
        assert resp.status_code == 422, (missing, resp.text)


async def test_create_note_authors_are_checked_in_both_places(client, patient):
    practitioner = await create_practitioner(client)
    role = await create_practitioner_role(client)
    organization = await create_organization(client)
    for ref in (
        f"Practitioner/{practitioner}",
        f"PractitionerRole/{role}",
        f"Organization/{organization}",
        f"Patient/{patient}",
    ):
        body = history_body(
            patient,
            note=[{"text": "n", "authorReference": {"reference": ref}}],
            condition=[
                {
                    "code": disease("44054006"),
                    "note": [{"text": "c", "authorReference": {"reference": ref}}],
                }
            ],
        )
        assert (await client.post(BASE + "/", json=body)).status_code == 201, ref
    missing = "Practitioner/999999"
    top = history_body(
        patient, note=[{"text": "n", "authorReference": {"reference": missing}}]
    )
    assert (await client.post(BASE + "/", json=top)).status_code == 422
    nested = history_body(
        patient,
        condition=[
            {
                "code": disease("44054006"),
                "note": [{"text": "c", "authorReference": {"reference": missing}}],
            }
        ],
    )
    assert (await client.post(BASE + "/", json=nested)).status_code == 422


async def test_create_identifier_assigner_must_exist(client, patient):
    body = history_body(
        patient,
        identifier=[{"value": "1", "assigner": {"reference": "Organization/999999"}}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 422
    org = await create_organization(client)
    body = history_body(
        patient,
        identifier=[{"value": "1", "assigner": {"reference": f"Organization/{org}"}}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_absolute_and_logical_references_not_resolved(client):
    absolute = "https://other.example.org/fhir/Patient/1"
    resp = await client.post(BASE + "/", json=history_body())
    assert resp.status_code == 201, resp.text
    assert resp.json()["patient"] == {"reference": absolute}
    logical = {
        "identifier": {"system": "urn:pts", "value": "P-9"},
        "display": "External",
    }
    resp = await client.post(BASE + "/", json=history_body(None, patient=logical))
    assert resp.status_code == 201, resp.text
    assert resp.json()["patient"] == logical


# ── Read ─────────────────────────────────────────────────────────────────────


async def test_get_by_id(client, patient):
    history, _ = await _full(client, patient)
    resp = await client.get(f"{BASE}/{history}")
    assert resp.status_code == 200 and resp.json()["id"] == str(history)


async def test_get_is_fhir_regardless_of_accept(client, patient):
    history = await create_history(client, history_body(patient))
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{history}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "FamilyMemberHistory"


async def test_xml_only_accept_is_406(client, patient):
    history = await create_history(client, history_body(patient))
    resp = await client.get(
        f"{BASE}/{history}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_scalar_keeps_the_rest(client, patient):
    history, _ = await _full(client, patient)
    resp = await client.patch(
        f"{BASE}/{history}", json={"status": "entered-in-error", "name": "M. Windsor"}
    )
    assert resp.status_code == 200, resp.text
    assert (
        resp.json()["status"] == "entered-in-error"
        and resp.json()["name"] == "M. Windsor"
    )
    assert resp.json()["patient"] == {"reference": f"Patient/{patient}"}  # untouched
    assert resp.json()["ageAge"]["value"] == 70
    assert len(resp.json()["condition"]) == 2


async def test_patch_reindexes_search(client, patient):
    history, _ = await _full(client, patient)
    await client.patch(
        f"{BASE}/{history}",
        json={
            "status": "partial",
            "date": "2024-05-01",
            "relationship": relationship("FTH", "father"),
            "sex": sex("male"),
            "condition": [{"code": disease("195967001", "Asthma")}],
        },
    )
    for param, old, new in (
        ("status", "completed", "partial"),
        ("date", "2023-01-15", "2024-05-01"),
        ("relationship", "MTH", "FTH"),
        ("sex", "female", "male"),
        ("code", "44054006", "195967001"),
    ):
        assert history not in _ids(
            (await client.get(BASE + "/", params={param: old})).json()
        ), param
        assert history in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param


async def test_patch_patient_replaced_and_reindexed(client, patient):
    history = await create_history(client, history_body(patient))
    other = await create_patient(client)
    resp = await client.patch(
        f"{BASE}/{history}", json={"patient": {"reference": f"Patient/{other}"}}
    )
    assert resp.status_code == 200, resp.text
    assert history not in _ids(
        (await client.get(BASE + "/", params={"patient": str(patient)})).json()
    )
    assert history in _ids(
        (await client.get(BASE + "/", params={"patient": str(other)})).json()
    )


async def test_patch_replaces_lists_and_empty_clears(client, patient):
    history, _ = await _full(client, patient)
    assert history in _ids(
        (await client.get(BASE + "/", params={"identifier": "FMH-1001"})).json()
    )
    resp = await client.patch(
        f"{BASE}/{history}",
        json={
            "identifier": [],
            "instantiatesCanonical": [],
            "instantiatesUri": [],
            "condition": [],
            "note": [],
            "reasonCode": [],
            "reasonReference": [],
        },
    )
    for gone in (
        "identifier",
        "instantiatesCanonical",
        "instantiatesUri",
        "condition",
        "note",
        "reasonCode",
        "reasonReference",
    ):
        assert gone not in resp.json()
    assert resp.json()["name"] == "Mary Windsor"  # untouched
    for param, value in (
        ("identifier", "FMH-1001"),
        ("code", "44054006"),
        ("instantiates-uri", "http://example.org/protocols/family-history"),
        (
            "instantiates-canonical",
            "http://example.org/fhir/PlanDefinition/family-history",
        ),
    ):
        assert history not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_patch_clears_a_date_and_missing_follows(client, patient):
    history = await create_history(client, history_body(patient, date="2024-05-01"))
    resp = await client.patch(f"{BASE}/{history}", json={"date": None})
    assert "date" not in resp.json()
    assert history in _ids(
        (await client.get(BASE + "/", params={"date:missing": "true"})).json()
    )


async def test_patch_nonexistent_reference_rejected_and_nothing_written(
    client, patient
):
    history = await create_history(client, history_body(patient))
    resp = await client.patch(
        f"{BASE}/{history}",
        json={"reasonReference": [{"reference": "Condition/999999"}]},
    )
    assert resp.status_code == 422
    assert "reasonReference" not in (await client.get(f"{BASE}/{history}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client, patient):
    history = await create_history(client, history_body(patient, "completed"))
    assert (
        await client.patch(f"{BASE}/{history}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{history}")).json()["status"] == "completed"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "entered-in-error"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete(client, patient):
    history, _ = await _full(client, patient)
    assert (await client.delete(f"{BASE}/{history}")).status_code == 204
    assert (await client.get(f"{BASE}/{history}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "FMH-1001"),
        ("relationship", "MTH"),
        ("code", "44054006"),
        ("instantiates-uri", "http://example.org/protocols/family-history"),
    ):
        assert history not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_create_without_permission(client, patient):
    _as_user(permissions=["family_member_history:read"])
    assert (
        await client.post(BASE + "/", json=history_body(patient))
    ).status_code == 403


async def test_org_less_token_rejected(client, patient):
    history = await create_history(client, history_body(patient))

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": HISTORY_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=history_body())).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{history}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    history = await create_history(client, history_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{history}"),
            await other_client.patch(
                f"{BASE}/{history}", json={"status": "entered-in-error"}
            ),
            await other_client.delete(f"{BASE}/{history}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_history(
        client, history_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}])
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
    missing = history_body(
        patient, reasonReference=[{"reference": "Observation/999999"}]
    )
    assert (await client.post(BASE + "/", json=missing)).status_code == 422
