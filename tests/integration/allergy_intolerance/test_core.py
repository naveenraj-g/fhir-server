"""Core allergy-intolerance endpoint coverage.

AllergyIntolerance is stored Medplum-style (like Patient, Appointment, Encounter
and the other content-based resources): the request body (genuine FHIR R4
AllergyIntolerance JSON) is validated and stored whole in `content`, every
response is FHIR R4 (`application/fhir+json`, regardless of Accept), and only
the FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/allergyintolerance.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing
scope, cross-org isolation) plus the existence checks on every local reference
(`patient`, `encounter`, `recorder`, `asserter`, note authors,
`identifier.assigner`). Search lives in test_search.py.

R4 requires `patient`, but only the `java_validator` backend enforces cardinality
minimums and the ait-1/ait-2 invariants (the native structural check does not),
so those are not asserted here.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.allergy_intolerance.conftest import ALLERGY_PERMS
from tests.integration.allergy_intolerance.support import (
    BASE,
    allergy_body,
    clinical,
    create_allergy_intolerance,
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
    return {
        int(e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == "match"
    }


def _as_user(sub="u-test", org_id="org-test", permissions=ALLERGY_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client, patient) -> tuple[int, dict]:
    encounter = await create_encounter(client, encounter_body())
    practitioner = await create_practitioner(client)
    organization = await create_organization(client)
    body = full_body(patient, encounter, practitioner, organization)
    return await create_allergy_intolerance(client, body), body


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_minimal(client, patient):
    resp = await client.post(BASE + "/", json=allergy_body(patient))
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "AllergyIntolerance"
    assert data["patient"] == {"reference": f"Patient/{patient}"}


async def test_create_full_round_trip(client, patient):
    ai, body = await _full(client, patient)
    data = (await client.get(f"{BASE}/{ai}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_elements_nothing_searches_on(client, patient):
    """`encounter`, `onset[x]`, `note` and the reaction elements no parameter reads live only in `content`."""
    ai, _ = await _full(client, patient)
    data = (await client.get(f"{BASE}/{ai}")).json()
    assert data["onsetDateTime"] == "2023-01-15T09:30:00Z"
    assert data["note"][0]["text"] == "Severe urticaria after cashew ingestion."
    assert data["reaction"][0]["description"] == "Severe hives on face and neck"
    assert data["reaction"][0]["note"] == [
        {"authorString": "Triage nurse", "text": "Resolved after epinephrine."}
    ]


@pytest.mark.parametrize(
    "onset",
    [
        {"onsetDateTime": "2023-01"},
        {
            "onsetAge": {
                "value": 12,
                "unit": "years",
                "system": "http://unitsofmeasure.org",
                "code": "a",
            }
        },
        {"onsetPeriod": {"start": "2020-01-01", "end": "2020-02-01"}},
        {
            "onsetRange": {
                "low": {"value": 5, "unit": "years"},
                "high": {"value": 10, "unit": "years"},
            }
        },
        {"onsetString": "as a child"},
    ],
    ids=["dateTime", "age", "period", "range", "string"],
)
async def test_create_every_onset_choice_round_trips(client, patient, onset):
    resp = await client.post(BASE + "/", json=allergy_body(patient, **onset))
    assert resp.status_code == 201, resp.text
    for key, value in onset.items():
        assert resp.json()[key] == value


async def test_create_ignores_server_managed_id_and_meta(client, patient):
    body = allergy_body(patient, id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"})
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_codes_rejected(client, patient):
    for bad in (
        {"type": "robot"},
        {"criticality": "extreme"},
        {"category": ["cosmic"]},
    ):
        resp = await client.post(BASE + "/", json=allergy_body(patient, **bad))
        assert resp.status_code == 422, (bad, resp.text)
    bad_severity = {
        "reaction": [{"manifestation": [{"text": "rash"}], "severity": "dire"}]
    }
    assert (
        await client.post(BASE + "/", json=allergy_body(patient, **bad_severity))
    ).status_code == 422


async def test_create_non_fhir_key_rejected(client, patient, native_validation):
    assert (
        await client.post(BASE + "/", json=allergy_body(patient, not_a_fhir_element=1))
    ).status_code == 422


async def test_create_old_flat_fields_rejected(client, patient, native_validation):
    for stale in (
        {"clinical_status": {"text": "x"}},
        {"onset_date_time": "2020-01-01"},
        {"org_id": "x"},
    ):
        resp = await client.post(BASE + "/", json={**allergy_body(patient), **stale})
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client, patient):
    assert (
        await client.post(
            BASE + "/", json=allergy_body(patient, resourceType="Patient")
        )
    ).status_code == 422


async def test_create_audit_meta_from_actor(client, patient):
    data = (await client.post(BASE + "/", json=allergy_body(patient))).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# ── Create: existence checks on local references ─────────────────────────────


async def test_create_patient_must_exist(client):
    assert (await client.post(BASE + "/", json=allergy_body(999999))).status_code == 422


async def test_create_patient_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    assert (await client.post(BASE + "/", json=allergy_body(theirs))).status_code == 422


async def test_create_encounter_must_exist(client, patient):
    missing = allergy_body(patient, encounter={"reference": "Encounter/999999"})
    assert (await client.post(BASE + "/", json=missing)).status_code == 422
    encounter = await create_encounter(client, encounter_body())
    assert (
        await client.post(
            BASE + "/",
            json=allergy_body(
                patient, encounter={"reference": f"Encounter/{encounter}"}
            ),
        )
    ).status_code == 201


@pytest.mark.parametrize("element", ["recorder", "asserter"])
async def test_create_recorder_and_asserter_are_checked_for_all_four_types(
    client, patient, element
):
    """Practitioner, PractitionerRole, Patient and RelatedPerson are all rebuilt resources here."""
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
            BASE + "/", json=allergy_body(patient, **{element: {"reference": ref}})
        )
        assert resp.status_code == 201, (ref, resp.text)
    for missing in (
        "Practitioner/999999",
        "PractitionerRole/999999",
        "Patient/999999",
        "RelatedPerson/999999",
    ):
        resp = await client.post(
            BASE + "/", json=allergy_body(patient, **{element: {"reference": missing}})
        )
        assert resp.status_code == 422, (missing, resp.text)


async def test_create_note_author_reference_is_checked(client, patient):
    note = [{"authorReference": {"reference": "Practitioner/999999"}, "text": "x"}]
    assert (
        await client.post(BASE + "/", json=allergy_body(patient, note=note))
    ).status_code == 422
    reaction = [{"manifestation": [{"text": "rash"}], "note": note}]
    assert (
        await client.post(BASE + "/", json=allergy_body(patient, reaction=reaction))
    ).status_code == 422
    practitioner = await create_practitioner(client)
    ok = [
        {"authorReference": {"reference": f"Practitioner/{practitioner}"}, "text": "x"}
    ]
    assert (
        await client.post(BASE + "/", json=allergy_body(patient, note=ok))
    ).status_code == 201


async def test_create_identifier_assigner_must_exist(client, patient):
    body = allergy_body(
        patient,
        identifier=[{"value": "1", "assigner": {"reference": "Organization/999999"}}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 422
    org = await create_organization(client)
    body = allergy_body(
        patient,
        identifier=[{"value": "1", "assigner": {"reference": f"Organization/{org}"}}],
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_absolute_and_logical_references_not_resolved(client):
    absolute = "https://other.example.org/fhir/Patient/1"
    resp = await client.post(BASE + "/", json={"patient": {"reference": absolute}})
    assert resp.status_code == 201, resp.text
    assert resp.json()["patient"] == {"reference": absolute}
    logical = {
        "identifier": {"system": "urn:pts", "value": "P-9"},
        "display": "External",
    }
    body = {
        "patient": logical,
        "asserter": {"reference": "https://other.example.org/fhir/Practitioner/7"},
    }
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["patient"] == logical
    assert resp.json()["asserter"] == {
        "reference": "https://other.example.org/fhir/Practitioner/7"
    }


# ── Read ─────────────────────────────────────────────────────────────────────


async def test_get_by_id(client, patient):
    ai, _ = await _full(client, patient)
    resp = await client.get(f"{BASE}/{ai}")
    assert resp.status_code == 200 and resp.json()["id"] == str(ai)


async def test_get_is_fhir_regardless_of_accept(client, patient):
    ai = await create_allergy_intolerance(client, allergy_body(patient))
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{ai}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "AllergyIntolerance"


async def test_xml_only_accept_is_406(client, patient):
    ai = await create_allergy_intolerance(client, allergy_body(patient))
    resp = await client.get(f"{BASE}/{ai}", headers={"Accept": "application/fhir+xml"})
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_scalar_keeps_the_rest(client, patient):
    ai, _ = await _full(client, patient)
    resp = await client.patch(
        f"{BASE}/{ai}", json={"criticality": "low", "type": "intolerance"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["criticality"] == "low" and resp.json()["type"] == "intolerance"
    assert resp.json()["patient"] == {"reference": f"Patient/{patient}"}  # untouched
    assert resp.json()["reaction"][0]["description"] == "Severe hives on face and neck"
    assert resp.json()["note"][0]["time"] == "2023-01-15T10:05:00Z"


async def test_patch_reindexes_search(client, patient):
    ai, _ = await _full(client, patient)
    await client.patch(
        f"{BASE}/{ai}",
        json={
            "clinicalStatus": clinical("resolved"),
            "category": ["medication"],
            "recordedDate": "2024-05-01",
        },
    )
    for param, old, new in (
        ("clinical-status", "active", "resolved"),
        ("category", "food", "medication"),
        ("date", "2023-01-15", "2024-05-01"),
    ):
        assert ai not in _ids(
            (await client.get(BASE + "/", params={param: old})).json()
        ), param
        assert ai in _ids((await client.get(BASE + "/", params={param: new})).json()), (
            param
        )


async def test_patch_patient_replaced_and_reindexed(client, patient):
    ai = await create_allergy_intolerance(client, allergy_body(patient))
    other = await create_patient(client)
    resp = await client.patch(
        f"{BASE}/{ai}", json={"patient": {"reference": f"Patient/{other}"}}
    )
    assert resp.status_code == 200, resp.text
    assert ai not in _ids(
        (await client.get(BASE + "/", params={"patient": str(patient)})).json()
    )
    assert ai in _ids(
        (await client.get(BASE + "/", params={"patient": str(other)})).json()
    )


async def test_patch_replaces_lists_and_empty_clears(client, patient):
    ai, _ = await _full(client, patient)
    assert ai in _ids(
        (await client.get(BASE + "/", params={"manifestation": "64305001"})).json()
    )
    resp = await client.patch(
        f"{BASE}/{ai}",
        json={"reaction": [], "category": [], "identifier": [], "note": []},
    )
    for gone in ("reaction", "category", "identifier", "note"):
        assert gone not in resp.json()
    assert resp.json()["criticality"] == "high"  # untouched
    for param, value in (
        ("manifestation", "64305001"),
        ("severity", "severe"),
        ("onset", "2023-01"),
        ("category", "food"),
        ("identifier", "AI-1001"),
    ):
        assert ai not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_patch_onset_choice_can_be_swapped(client, patient):
    ai = await create_allergy_intolerance(
        client, allergy_body(patient, onsetString="as a child")
    )
    resp = await client.patch(
        f"{BASE}/{ai}", json={"onsetString": None, "onsetDateTime": "2020-02"}
    )
    assert resp.status_code == 200, resp.text
    assert (
        "onsetString" not in resp.json() and resp.json()["onsetDateTime"] == "2020-02"
    )


async def test_patch_clears_a_date_and_missing_follows(client, patient):
    ai = await create_allergy_intolerance(
        client, allergy_body(patient, recordedDate="2024-05-01")
    )
    resp = await client.patch(f"{BASE}/{ai}", json={"recordedDate": None})
    assert "recordedDate" not in resp.json()
    assert ai in _ids(
        (await client.get(BASE + "/", params={"date:missing": "true"})).json()
    )


async def test_patch_nonexistent_reference_rejected_and_nothing_written(
    client, patient
):
    ai = await create_allergy_intolerance(client, allergy_body(patient))
    resp = await client.patch(
        f"{BASE}/{ai}", json={"recorder": {"reference": "Practitioner/999999"}}
    )
    assert resp.status_code == 422
    assert "recorder" not in (await client.get(f"{BASE}/{ai}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client, patient):
    ai = await create_allergy_intolerance(
        client, allergy_body(patient, criticality="high")
    )
    assert (
        await client.patch(f"{BASE}/{ai}", json={"criticality": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{ai}")).json()["criticality"] == "high"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"criticality": "low"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete(client, patient):
    ai, _ = await _full(client, patient)
    assert (await client.delete(f"{BASE}/{ai}")).status_code == 204
    assert (await client.get(f"{BASE}/{ai}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "AI-1001"),
        ("manifestation", "64305001"),
        ("code", "227493005"),
        ("category", "food"),
    ):
        assert ai not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_create_without_permission(client, patient):
    _as_user(permissions=["allergy_intolerance:read"])
    assert (
        await client.post(BASE + "/", json=allergy_body(patient))
    ).status_code == 403


async def test_org_less_token_rejected(client, patient):
    ai = await create_allergy_intolerance(client, allergy_body(patient))

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": ALLERGY_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=allergy_body())).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{ai}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    ai = await create_allergy_intolerance(client, allergy_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{ai}"),
            await other_client.patch(f"{BASE}/{ai}", json={"criticality": "low"}),
            await other_client.delete(f"{BASE}/{ai}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_allergy_intolerance(
        client, allergy_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}])
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()


async def test_verification_status_round_trip(client, patient):
    """clinicalStatus / verificationStatus are CodeableConcepts (ait-1/ait-2 are the java validator's)."""
    body = allergy_body(
        patient,
        clinicalStatus=clinical("inactive"),
        verificationStatus=verification("unconfirmed"),
    )
    data = (await client.post(BASE + "/", json=body)).json()
    assert data["clinicalStatus"] == clinical("inactive") and data[
        "verificationStatus"
    ] == verification("unconfirmed")
