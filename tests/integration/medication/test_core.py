"""Core medication endpoint coverage.

Medication is stored Medplum-style (like Patient, Encounter, Condition, Procedure, Specimen,
ServiceRequest and the other content-based resources): the request body (genuine FHIR R4
Medication JSON) is validated and stored whole in `content`, every response is FHIR R4
(`application/fhir+json`, regardless of Accept), and only the FHIR R4 search parameters are
indexed (https://www.hl7.org/fhir/R4/medication.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence checks on every local reference (`manufacturer`, a Medication
`ingredient` and every identifier's `assigner`). Search lives in test_search.py.

Every Medication element is optional in R4, so an empty document is valid.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.medication.conftest import MEDICATION_PERMS
from tests.integration.medication.support import (
    BASE,
    RXNORM,
    SCT,
    concept,
    create_medication,
    create_organization,
    full_body,
    medication_body,
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


def _as_user(sub="u-test", org_id="org-test", permissions=MEDICATION_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client) -> tuple[int, dict]:
    organization = await create_organization(client)
    ingredient = await create_medication(client, medication_body(status="active"))
    body = full_body(organization, ingredient)
    return await create_medication(client, body), body


# -- Create ---------------------------------------------------------------------------------


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=medication_body(status="active"))
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "Medication" and data["status"] == "active"


async def test_create_empty_document_is_valid(client):
    resp = await client.post(BASE + "/", json={})
    assert resp.status_code == 201, resp.text
    assert resp.json()["resourceType"] == "Medication"


async def test_create_full_round_trip(client):
    medication, body = await _full(client)
    data = (await client.get(f"{BASE}/{medication}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_elements_nothing_searches_on(client):
    """`amount`, `ingredient.isActive` and `ingredient.strength` live only in `content`."""
    medication, _ = await _full(client)
    data = (await client.get(f"{BASE}/{medication}")).json()
    assert data["amount"]["numerator"]["value"] == 30
    assert data["ingredient"][0]["isActive"] is True
    assert data["ingredient"][0]["strength"]["denominator"]["unit"] == "tablet"
    assert data["ingredient"][1]["isActive"] is False


@pytest.mark.parametrize("status", ["active", "inactive", "entered-in-error"])
async def test_create_every_status_round_trips(client, status):
    resp = await client.post(BASE + "/", json=medication_body(status=status))
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


async def test_create_ignores_server_managed_id_and_meta(client):
    body = medication_body(id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"})
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client):
    for bad in (
        {"status": "robot"},
        {"code": "x"},
        {"form": "x"},
        {"identifier": {"value": "x"}},
        {"manufacturer": "Organization/1"},
        {"amount": "30"},
        {"ingredient": {"itemCodeableConcept": {"text": "x"}}},
        {"ingredient": [{"isActive": "yes"}]},
        {"ingredient": [{"strength": "10mg"}]},
        {"batch": "LOT"},
        {"batch": {"expirationDate": "soon"}},
        {"batch": {"lotNumber": 5}},
    ):
        resp = await client.post(BASE + "/", json=medication_body(**bad))
        assert resp.status_code == 422, (bad, resp.text)


async def test_create_non_fhir_key_rejected(client, native_validation):
    resp = await client.post(BASE + "/", json=medication_body(not_a_fhir_element=1))
    assert resp.status_code == 422


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in ({"code_text": "x"}, {"batch_lot_number": "x"}, {"org_id": "x"}):
        resp = await client.post(BASE + "/", json=stale)
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(BASE + "/", json=medication_body(resourceType="Patient"))
    assert resp.status_code == 422


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=medication_body())).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# -- Create: existence checks on local references --------------------------------------------


async def test_create_manufacturer_must_exist(client):
    organization = await create_organization(client)
    ok = medication_body(manufacturer={"reference": f"Organization/{organization}"})
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = medication_body(manufacturer={"reference": "Organization/999999"})
    assert (await client.post(BASE + "/", json=missing)).status_code == 422


async def test_create_manufacturer_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_organization(other_client)
    finally:
        _as_user()
    body = medication_body(manufacturer={"reference": f"Organization/{theirs}"})
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_ingredient_medication_must_exist(client):
    first = await create_medication(client, medication_body())
    ok = medication_body(
        ingredient=[{"itemReference": {"reference": f"Medication/{first}"}}]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = medication_body(
        ingredient=[{"itemReference": {"reference": "Medication/999999"}}]
    )
    assert (await client.post(BASE + "/", json=missing)).status_code == 422


async def test_create_substance_ingredient_is_not_checked(client):
    body = medication_body(
        ingredient=[{"itemReference": {"reference": "Substance/999999"}}]
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["ingredient"][0]["itemReference"] == {
        "reference": "Substance/999999"
    }


async def test_create_every_identifier_assigner_must_exist(client):
    org = await create_organization(client)
    ok = {"value": "1", "assigner": {"reference": f"Organization/{org}"}}
    missing = {"value": "1", "assigner": {"reference": "Organization/999999"}}
    assert (
        await client.post(BASE + "/", json=medication_body(identifier=[ok]))
    ).status_code == 201
    assert (
        await client.post(BASE + "/", json=medication_body(identifier=[missing]))
    ).status_code == 422


async def test_create_absolute_and_logical_references_not_resolved(client):
    absolute = "https://other.example.org/fhir/Organization/7"
    resp = await client.post(
        BASE + "/", json=medication_body(manufacturer={"reference": absolute})
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["manufacturer"] == {"reference": absolute}
    logical = {"identifier": {"system": "urn:mfr", "value": "M-9"}, "display": "ACME"}
    resp = await client.post(BASE + "/", json=medication_body(manufacturer=logical))
    assert resp.status_code == 201, resp.text
    assert resp.json()["manufacturer"] == logical


# -- Read -----------------------------------------------------------------------------------


async def test_get_by_id(client):
    medication, _ = await _full(client)
    resp = await client.get(f"{BASE}/{medication}")
    assert resp.status_code == 200 and resp.json()["id"] == str(medication)


async def test_get_is_fhir_regardless_of_accept(client):
    medication = await create_medication(client, medication_body())
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{medication}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "Medication"


async def test_xml_only_accept_is_406(client):
    medication = await create_medication(client, medication_body())
    resp = await client.get(
        f"{BASE}/{medication}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Patch ----------------------------------------------------------------------------------


async def test_patch_scalar_keeps_the_rest(client):
    medication, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{medication}",
        json={"status": "inactive", "batch": {"lotNumber": "LOT-2"}},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "inactive"
    assert resp.json()["batch"] == {"lotNumber": "LOT-2"}
    assert resp.json()["code"]["coding"][0]["code"] == "1049502"  # untouched
    assert resp.json()["amount"]["numerator"]["value"] == 30


async def test_patch_reindexes_search(client):
    medication, _ = await _full(client)
    await client.patch(
        f"{BASE}/{medication}",
        json={
            "status": "inactive",
            "code": concept(RXNORM, "9999"),
            "form": concept(SCT, "888"),
            "batch": {"lotNumber": "NEW-LOT", "expirationDate": "2030-01-01"},
            "ingredient": [{"itemCodeableConcept": concept(RXNORM, "555")}],
        },
    )
    for param, old, new in (
        ("status", "active", "inactive"),
        ("code", "1049502", "9999"),
        ("form", "385057009", "888"),
        ("lot-number", "LOT-1", "NEW-LOT"),
        ("expiration-date", "2027-06-30", "2030-01-01"),
        ("ingredient-code", "7804", "555"),
    ):
        assert medication not in _ids(
            (await client.get(BASE + "/", params={param: old})).json()
        ), param
        assert medication in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param


async def test_patch_replaces_lists_and_empty_clears(client):
    medication, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{medication}", json={"identifier": [], "ingredient": []}
    )
    for gone in ("identifier", "ingredient"):
        assert gone not in resp.json()
    assert resp.json()["status"] == "active"  # untouched
    for param in ("identifier", "ingredient", "ingredient-code"):
        assert medication in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_clears_batch_and_manufacturer(client):
    medication, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{medication}", json={"batch": None, "manufacturer": None}
    )
    assert "batch" not in resp.json() and "manufacturer" not in resp.json()
    for param in ("lot-number", "expiration-date", "manufacturer"):
        assert medication in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client):
    medication = await create_medication(client, medication_body())
    resp = await client.patch(
        f"{BASE}/{medication}",
        json={"manufacturer": {"reference": "Organization/999999"}},
    )
    assert resp.status_code == 422
    assert "manufacturer" not in (await client.get(f"{BASE}/{medication}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    medication = await create_medication(client, medication_body(status="active"))
    assert (
        await client.patch(f"{BASE}/{medication}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{medication}")).json()["status"] == "active"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "active"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Delete ---------------------------------------------------------------------------------


async def test_delete(client):
    medication, _ = await _full(client)
    assert (await client.delete(f"{BASE}/{medication}")).status_code == 204
    assert (await client.get(f"{BASE}/{medication}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "MED-1001"),
        ("code", "1049502"),
        ("ingredient-code", "7804"),
        ("lot-number", "LOT-1"),
    ):
        assert medication not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Auth -----------------------------------------------------------------------------------


async def test_create_without_permission(client):
    _as_user(permissions=["medication:read"])
    assert (await client.post(BASE + "/", json=medication_body())).status_code == 403


async def test_org_less_token_rejected(client):
    medication = await create_medication(client, medication_body())

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": MEDICATION_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=medication_body())).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{medication}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    medication = await create_medication(client, medication_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{medication}"),
            await other_client.patch(f"{BASE}/{medication}", json={"status": "active"}),
            await other_client.delete(f"{BASE}/{medication}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_medication(
        client,
        medication_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}]),
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()


async def test_medication_is_checked_where_a_reference_any_can_name_it(client):
    """DetectedIssue.implicated and ClinicalImpression.supportingInfo are Reference(Any): a
    relative Medication there must exist (422 otherwise)."""
    medication = await create_medication(client, medication_body())
    issues = "/api/fhir/v1/detected-issues/"
    ok = {"status": "final", "implicated": [{"reference": f"Medication/{medication}"}]}
    assert (await client.post(issues, json=ok)).status_code == 201
    missing = {"status": "final", "implicated": [{"reference": "Medication/999999"}]}
    assert (await client.post(issues, json=missing)).status_code == 422
    impressions = "/api/fhir/v1/clinical-impressions/"
    subject = {"reference": "https://other.example.org/fhir/Patient/1"}
    ok = {
        "status": "completed",
        "subject": subject,
        "supportingInfo": [{"reference": f"Medication/{medication}"}],
    }
    assert (await client.post(impressions, json=ok)).status_code == 201
    missing = {
        "status": "completed",
        "subject": subject,
        "supportingInfo": [{"reference": "Medication/999999"}],
    }
    assert (await client.post(impressions, json=missing)).status_code == 422
