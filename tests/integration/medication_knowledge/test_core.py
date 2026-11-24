"""Core medication-knowledge endpoint coverage.

MedicationKnowledge is stored content-based (like Medication, Patient, Encounter and the other
rebuilt resources): the request body (genuine FHIR R4 MedicationKnowledge JSON) is validated and
stored whole in `content`, every response is FHIR R4 (`application/fhir+json`, regardless of
Accept), and only the FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/medicationknowledge.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence checks on every local reference (`manufacturer`, `monograph.source`,
`associatedMedication`, `relatedMedicationKnowledge`, `contraindication`,
`regulatory.regulatoryAuthority`). Search lives in test_search.py.

Every top-level MedicationKnowledge element is optional in R4, so an empty document is valid.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.medication_knowledge.conftest import MEDICATION_KNOWLEDGE_PERMS
from tests.integration.medication_knowledge.support import (
    ATC,
    BASE,
    RXNORM,
    SCT,
    concept,
    create_document,
    create_issue,
    create_medication,
    create_medication_knowledge,
    create_organization,
    document_body,
    full_body,
    issue_body,
    medication_body,
    medication_knowledge_body,
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


def _as_user(sub="u-test", org_id="org-test", permissions=MEDICATION_KNOWLEDGE_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client) -> tuple[int, dict]:
    organization = await create_organization(client)
    medication = await create_medication(client, medication_body(status="active"))
    document = await create_document(client, document_body())
    related = await create_medication_knowledge(client, medication_knowledge_body())
    body = full_body(organization, medication, document, related)
    return await create_medication_knowledge(client, body), body


# -- Create ---------------------------------------------------------------------------------


async def test_create_minimal(client):
    resp = await client.post(
        BASE + "/", json=medication_knowledge_body(status="active")
    )
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "MedicationKnowledge" and data["status"] == "active"


async def test_create_empty_document_is_valid(client):
    resp = await client.post(BASE + "/", json={})
    assert resp.status_code == 201, resp.text
    assert resp.json()["resourceType"] == "MedicationKnowledge"


async def test_create_full_round_trip(client):
    entry, body = await _full(client)
    data = (await client.get(f"{BASE}/{entry}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_elements_nothing_searches_on(client):
    """`amount`, `synonym`, `regulatory`, `kinetics`, `packaging`, ... live only in `content`."""
    entry, _ = await _full(client)
    data = (await client.get(f"{BASE}/{entry}")).json()
    assert data["amount"]["value"] == 30
    assert data["synonym"] == ["Oxycodone ER 10 mg", "OxyContin 10 mg"]
    assert data["ingredient"][0]["strength"]["denominator"]["unit"] == "tablet"
    assert data["regulatory"][0]["maxDispense"]["period"]["value"] == 30
    assert data["kinetics"][0]["halfLifePeriod"]["unit"] == "h"
    assert data["packaging"]["quantity"]["value"] == 30
    assert data["drugCharacteristic"][0]["valueString"] == "OC 10"
    assert data["administrationGuidelines"][0]["dosage"][0]["dosage"][0]["text"]


@pytest.mark.parametrize("status", ["active", "inactive", "entered-in-error"])
async def test_create_every_status_round_trips(client, status):
    resp = await client.post(BASE + "/", json=medication_knowledge_body(status=status))
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


async def test_create_ignores_server_managed_id_and_meta(client):
    body = medication_knowledge_body(
        id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"}
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client):
    for bad in (
        {"status": "robot"},
        {"code": "x"},
        {"doseForm": "x"},
        {"manufacturer": "Organization/1"},
        {"amount": "30"},
        {"synonym": "x"},
        {"synonym": [5]},
        {"ingredient": {"itemCodeableConcept": {"text": "x"}}},
        {"ingredient": [{"isActive": "yes"}]},
        {"monograph": {"type": {"text": "x"}}},
        {"cost": [{"source": 5}]},
        {"monitoringProgram": [{"name": 5}]},
        {"medicineClassification": [{"classification": "x"}]},
        {"preparationInstruction": 5},
    ):
        resp = await client.post(BASE + "/", json=medication_knowledge_body(**bad))
        assert resp.status_code == 422, (bad, resp.text)


async def test_create_non_fhir_key_rejected(client, native_validation):
    resp = await client.post(
        BASE + "/", json=medication_knowledge_body(not_a_fhir_element=1)
    )
    assert resp.status_code == 422


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in ({"code_text": "x"}, {"dose_form_text": "x"}, {"org_id": "x"}):
        resp = await client.post(BASE + "/", json=stale)
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(
        BASE + "/", json=medication_knowledge_body(resourceType="Patient")
    )
    assert resp.status_code == 422


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=medication_knowledge_body())).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# -- Create: existence checks on local references --------------------------------------------


async def test_create_manufacturer_must_exist(client):
    organization = await create_organization(client)
    ok = medication_knowledge_body(
        manufacturer={"reference": f"Organization/{organization}"}
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = medication_knowledge_body(
        manufacturer={"reference": "Organization/999999"}
    )
    assert (await client.post(BASE + "/", json=missing)).status_code == 422


async def test_create_manufacturer_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_organization(other_client)
    finally:
        _as_user()
    body = medication_knowledge_body(
        manufacturer={"reference": f"Organization/{theirs}"}
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_monograph_document_must_exist(client):
    document = await create_document(client, document_body())
    ok = medication_knowledge_body(
        monograph=[{"source": {"reference": f"DocumentReference/{document}"}}]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = medication_knowledge_body(
        monograph=[{"source": {"reference": "DocumentReference/999999"}}]
    )
    assert (await client.post(BASE + "/", json=missing)).status_code == 422


async def test_create_associated_medication_must_exist(client):
    medication = await create_medication(client, medication_body())
    ok = medication_knowledge_body(
        associatedMedication=[{"reference": f"Medication/{medication}"}]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = medication_knowledge_body(
        associatedMedication=[{"reference": "Medication/999999"}]
    )
    assert (await client.post(BASE + "/", json=missing)).status_code == 422


async def test_create_related_knowledge_must_exist(client):
    related = await create_medication_knowledge(client, medication_knowledge_body())
    ok = medication_knowledge_body(
        relatedMedicationKnowledge=[
            {
                "type": {"text": "similar"},
                "reference": [{"reference": f"MedicationKnowledge/{related}"}],
            }
        ]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = medication_knowledge_body(
        relatedMedicationKnowledge=[
            {
                "type": {"text": "similar"},
                "reference": [{"reference": "MedicationKnowledge/999999"}],
            }
        ]
    )
    assert (await client.post(BASE + "/", json=missing)).status_code == 422


async def test_create_contraindication_must_exist(client):
    issue = await create_issue(client, issue_body())
    ok = medication_knowledge_body(
        contraindication=[{"reference": f"DetectedIssue/{issue}"}]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = medication_knowledge_body(
        contraindication=[{"reference": "DetectedIssue/999999"}]
    )
    assert (await client.post(BASE + "/", json=missing)).status_code == 422


async def test_create_regulatory_authority_must_exist(client):
    organization = await create_organization(client)

    def body(reference):
        return medication_knowledge_body(
            regulatory=[{"regulatoryAuthority": {"reference": reference}}]
        )

    assert (
        await client.post(BASE + "/", json=body(f"Organization/{organization}"))
    ).status_code == 201
    assert (
        await client.post(BASE + "/", json=body("Organization/999999"))
    ).status_code == 422


async def test_create_substance_ingredient_and_media_monograph_are_not_checked(client):
    """Substance and Media are not resources on this server: stored as sent."""
    body = medication_knowledge_body(
        ingredient=[{"itemReference": {"reference": "Substance/999999"}}],
        monograph=[{"source": {"reference": "Media/999999"}}],
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["ingredient"][0]["itemReference"] == {
        "reference": "Substance/999999"
    }
    assert resp.json()["monograph"][0]["source"] == {"reference": "Media/999999"}


async def test_create_absolute_and_logical_references_not_resolved(client):
    absolute = "https://other.example.org/fhir/Organization/7"
    resp = await client.post(
        BASE + "/", json=medication_knowledge_body(manufacturer={"reference": absolute})
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["manufacturer"] == {"reference": absolute}
    logical = {"identifier": {"system": "urn:mfr", "value": "M-9"}, "display": "ACME"}
    resp = await client.post(
        BASE + "/", json=medication_knowledge_body(manufacturer=logical)
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["manufacturer"] == logical


# -- Read -----------------------------------------------------------------------------------


async def test_get_by_id(client):
    entry, _ = await _full(client)
    resp = await client.get(f"{BASE}/{entry}")
    assert resp.status_code == 200 and resp.json()["id"] == str(entry)


async def test_get_is_fhir_regardless_of_accept(client):
    entry = await create_medication_knowledge(client, medication_knowledge_body())
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{entry}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "MedicationKnowledge"


async def test_xml_only_accept_is_406(client):
    entry = await create_medication_knowledge(client, medication_knowledge_body())
    resp = await client.get(
        f"{BASE}/{entry}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Patch ----------------------------------------------------------------------------------


async def test_patch_scalar_keeps_the_rest(client):
    entry, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{entry}",
        json={"status": "inactive", "synonym": ["Only one"]},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "inactive"
    assert resp.json()["synonym"] == ["Only one"]
    assert resp.json()["code"]["coding"][0]["code"] == "1049502"  # untouched
    assert resp.json()["amount"]["value"] == 30


async def test_patch_reindexes_search(client):
    entry, _ = await _full(client)
    patched = await client.patch(
        f"{BASE}/{entry}",
        json={
            "status": "inactive",
            "code": concept(RXNORM, "9999"),
            "doseForm": concept(SCT, "888"),
            "ingredient": [{"itemCodeableConcept": concept(RXNORM, "555")}],
            "medicineClassification": [
                {"type": {"text": "other"}, "classification": [concept(ATC, "A01")]}
            ],
            "monitoringProgram": [{"name": "New-Program"}],
            "cost": [
                {"type": {"text": "x"}, "source": "New-Source", "cost": {"value": 1}}
            ],
        },
    )
    assert patched.status_code == 200, patched.text
    for param, old, new in (
        ("status", "active", "inactive"),
        ("code", "1049502", "9999"),
        ("doseform", "385057009", "888"),
        ("ingredient-code", "7804", "555"),
        ("classification", "N02AA05", "A01"),
        ("monitoring-program-name", "Opioid-Safety", "New-Program"),
        ("source-cost", "Wholesaler-A", "New-Source"),
    ):
        assert entry not in _ids(
            (await client.get(BASE + "/", params={param: old})).json()
        ), param
        assert entry in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param


async def test_patch_replaces_lists_and_empty_clears(client):
    entry, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{entry}", json={"ingredient": [], "monograph": []}
    )
    for gone in ("ingredient", "monograph"):
        assert gone not in resp.json()
    assert resp.json()["status"] == "active"  # untouched
    for param in ("ingredient", "ingredient-code", "monograph", "monograph-type"):
        assert entry in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_clears_manufacturer(client):
    entry, _ = await _full(client)
    resp = await client.patch(f"{BASE}/{entry}", json={"manufacturer": None})
    assert "manufacturer" not in resp.json()
    assert entry in _ids(
        (await client.get(BASE + "/", params={"manufacturer:missing": "true"})).json()
    )


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client):
    entry = await create_medication_knowledge(client, medication_knowledge_body())
    resp = await client.patch(
        f"{BASE}/{entry}",
        json={"manufacturer": {"reference": "Organization/999999"}},
    )
    assert resp.status_code == 422
    assert "manufacturer" not in (await client.get(f"{BASE}/{entry}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    entry = await create_medication_knowledge(
        client, medication_knowledge_body(status="active")
    )
    assert (
        await client.patch(f"{BASE}/{entry}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{entry}")).json()["status"] == "active"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "active"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Delete ---------------------------------------------------------------------------------


async def test_delete(client):
    entry, _ = await _full(client)
    assert (await client.delete(f"{BASE}/{entry}")).status_code == 204
    assert (await client.get(f"{BASE}/{entry}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("code", "1049502"),
        ("ingredient-code", "7804"),
        ("classification", "N02AA05"),
        ("source-cost", "Wholesaler-A"),
    ):
        assert entry not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Auth -----------------------------------------------------------------------------------


async def test_create_without_permission(client):
    _as_user(permissions=["medication_knowledge:read"])
    assert (
        await client.post(BASE + "/", json=medication_knowledge_body())
    ).status_code == 403


async def test_org_less_token_rejected(client):
    entry = await create_medication_knowledge(client, medication_knowledge_body())

    async def _no_org(request: Request):
        request.state.user = {
            "sub": "u-test",
            "permissions": MEDICATION_KNOWLEDGE_PERMS,
        }

    app.dependency_overrides[get_current_user] = _no_org
    assert (
        await client.post(BASE + "/", json=medication_knowledge_body())
    ).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{entry}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    entry = await create_medication_knowledge(client, medication_knowledge_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{entry}"),
            await other_client.patch(f"{BASE}/{entry}", json={"status": "active"}),
            await other_client.delete(f"{BASE}/{entry}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_medication_knowledge(
        client,
        medication_knowledge_body(
            cost=[
                {
                    "type": {"text": "x"},
                    "source": "TenantAOnly",
                    "cost": {"value": 1},
                }
            ]
        ),
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"source-cost": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()


async def test_medication_knowledge_is_checked_where_a_reference_any_can_name_it(
    client,
):
    """DetectedIssue.implicated is Reference(Any): a relative MedicationKnowledge there must
    exist (422 otherwise)."""
    entry = await create_medication_knowledge(client, medication_knowledge_body())
    issues = "/api/fhir/v1/detected-issues/"
    ok = {
        "status": "final",
        "implicated": [{"reference": f"MedicationKnowledge/{entry}"}],
    }
    assert (await client.post(issues, json=ok)).status_code == 201
    missing = {
        "status": "final",
        "implicated": [{"reference": "MedicationKnowledge/999999"}],
    }
    assert (await client.post(issues, json=missing)).status_code == 422
