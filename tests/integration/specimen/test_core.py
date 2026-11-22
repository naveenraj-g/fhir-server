"""Core specimen endpoint coverage.

Specimen is stored Medplum-style (like Patient, Encounter, Condition, Procedure, DiagnosticReport,
Observation and the other content-based resources): the request body (genuine FHIR R4 Specimen
JSON) is validated and stored whole in `content`, every response is FHIR R4
(`application/fhir+json`, regardless of Accept), and only the FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/specimen.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence checks on every local reference (`subject`, `collection.collector`,
`parent`, note authors and every identifier's `assigner`). Search lives in test_search.py.

Every Specimen element is optional in R4, so (unlike most resources) an empty document is valid.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.specimen.conftest import SPECIMEN_PERMS
from tests.integration.specimen.support import (
    BASE,
    SCT,
    V2_0487,
    concept,
    create_location,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_specimen,
    full_body,
    specimen_body,
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


def _as_user(sub="u-test", org_id="org-test", permissions=SPECIMEN_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client, patient) -> tuple[int, dict]:
    practitioner = await create_practitioner(client)
    organization = await create_organization(client)
    parent = await create_specimen(client, specimen_body(patient))
    body = full_body(patient, practitioner, organization, parent)
    return await create_specimen(client, body), body


# ── Create ───────────────────────────────────────────────────────────────────


async def test_create_minimal(client, patient):
    resp = await client.post(
        BASE + "/", json=specimen_body(patient, status="available")
    )
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "Specimen" and data["status"] == "available"
    assert data["subject"] == {"reference": f"Patient/{patient}"}


async def test_create_empty_document_is_valid(client):
    resp = await client.post(BASE + "/", json={})
    assert resp.status_code == 201, resp.text
    assert resp.json()["resourceType"] == "Specimen"


async def test_create_full_round_trip(client, patient):
    specimen, body = await _full(client, patient)
    data = (await client.get(f"{BASE}/{specimen}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_elements_nothing_searches_on(client, patient):
    """`receivedTime`, `request`, `processing`, `condition`, `note` and the collection details that
    no parameter reads (duration, quantity, method, fasting status) live only in `content`."""
    specimen, _ = await _full(client, patient)
    data = (await client.get(f"{BASE}/{specimen}")).json()
    assert data["receivedTime"] == "2023-01-15T11:00:00Z"
    assert data["request"] == [{"reference": "ServiceRequest/80001"}]
    assert data["processing"][0]["description"] == "Centrifuged"
    assert data["condition"][0]["coding"][0]["code"] == "HEM"
    assert data["note"][0]["authorString"] == "Nurse Joy"
    assert data["collection"]["duration"]["value"] == 5
    assert (
        data["collection"]["fastingStatusCodeableConcept"]["coding"][0]["code"] == "F"
    )
    assert data["container"][0]["capacity"]["value"] == 10


@pytest.mark.parametrize(
    "collection",
    [
        {"collectedDateTime": "2023-01"},
        {"collectedPeriod": {"start": "2023-01-01", "end": "2023-01-02"}},
    ],
    ids=["collectedDateTime", "collectedPeriod"],
)
async def test_create_each_collected_choice_round_trips(client, patient, collection):
    resp = await client.post(
        BASE + "/", json=specimen_body(patient, collection=collection)
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["collection"] == collection


@pytest.mark.parametrize(
    "extra",
    [
        {
            "fastingStatusDuration": {
                "value": 8,
                "unit": "h",
                "system": "http://unitsofmeasure.org",
                "code": "h",
            }
        },
        {"fastingStatusCodeableConcept": {"text": "Fasting"}},
    ],
    ids=["duration", "codeableConcept"],
)
async def test_create_each_fasting_status_choice_round_trips(client, patient, extra):
    body = specimen_body(patient, collection=extra)
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["collection"] == extra


@pytest.mark.parametrize(
    "status", ["available", "unavailable", "unsatisfactory", "entered-in-error"]
)
async def test_create_every_status_round_trips(client, patient, status):
    resp = await client.post(BASE + "/", json=specimen_body(patient, status=status))
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


async def test_create_ignores_server_managed_id_and_meta(client, patient):
    body = specimen_body(
        patient, id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"}
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client, patient):
    for bad in (
        {"status": "robot"},
        {"receivedTime": "yesterday"},
        {"type": "x"},
        {"parent": {"reference": "Specimen/1"}},
        {"request": {"reference": "ServiceRequest/1"}},
        {"collection": "x"},
        {"collection": {"collectedDateTime": "yesterday"}},
        {"collection": {"collector": "x"}},
        {"collection": {"quantity": "5"}},
        {"processing": {"description": "x"}},
        {"processing": [{"time": 5}]},
        {"container": {"description": "x"}},
        {"container": [{"type": "x"}]},
        {"container": [{"capacity": "10"}]},
        {"condition": "x"},
        {"identifier": {"value": "x"}},
        {"accessionIdentifier": [{"value": "x"}]},
        {"note": {"text": "x"}},
    ):
        resp = await client.post(BASE + "/", json=specimen_body(patient, **bad))
        assert resp.status_code == 422, (bad, resp.text)
    assert (
        await client.post(
            BASE + "/", json={"status": "available", "subject": "Patient/1"}
        )
    ).status_code == 422


async def test_create_non_fhir_key_rejected(client, patient, native_validation):
    assert (
        await client.post(BASE + "/", json=specimen_body(patient, not_a_fhir_element=1))
    ).status_code == 422


async def test_create_old_flat_fields_rejected(client, patient, native_validation):
    for stale in (
        {"type_text": "x"},
        {"collection_collected_date_time": "2020-01-01"},
        {"org_id": "x"},
    ):
        resp = await client.post(BASE + "/", json={**specimen_body(patient), **stale})
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client, patient):
    assert (
        await client.post(
            BASE + "/", json=specimen_body(patient, resourceType="Patient")
        )
    ).status_code == 422


async def test_create_audit_meta_from_actor(client, patient):
    data = (await client.post(BASE + "/", json=specimen_body(patient))).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# ── Create: existence checks on local references ─────────────────────────────


async def test_create_patient_subject_must_exist(client):
    assert (
        await client.post(BASE + "/", json=specimen_body(999999))
    ).status_code == 422


async def test_create_subject_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    assert (
        await client.post(BASE + "/", json=specimen_body(theirs))
    ).status_code == 422


async def test_create_subject_is_checked_for_a_patient_or_location_only(client):
    location = await create_location(client)
    ok = {"subject": {"reference": f"Location/{location}"}}
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = {"subject": {"reference": "Location/999999"}}
    assert (await client.post(BASE + "/", json=missing)).status_code == 422
    for stored in (
        "Group/999999",
        "Device/999999",
        "Substance/999999",
    ):  # not rebuilt: stored as sent
        resp = await client.post(BASE + "/", json={"subject": {"reference": stored}})
        assert resp.status_code == 201, (stored, resp.text)
        assert resp.json()["subject"] == {"reference": stored}


async def test_create_collector_must_exist(client):
    practitioner = await create_practitioner(client)
    role = await create_practitioner_role(client)
    for ref in (f"Practitioner/{practitioner}", f"PractitionerRole/{role}"):
        body = {"collection": {"collector": {"reference": ref}}}
        assert (await client.post(BASE + "/", json=body)).status_code == 201, ref
    for missing in ("Practitioner/999999", "PractitionerRole/999999"):
        body = {"collection": {"collector": {"reference": missing}}}
        assert (await client.post(BASE + "/", json=body)).status_code == 422, missing


async def test_create_parent_must_exist(client, patient):
    first = await create_specimen(client, specimen_body(patient))
    ok = {"parent": [{"reference": f"Specimen/{first}"}]}
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = {"parent": [{"reference": "Specimen/999999"}]}
    assert (await client.post(BASE + "/", json=missing)).status_code == 422


async def test_create_additive_is_not_checked(client):
    body = {
        "processing": [{"additive": [{"reference": "Substance/999999"}]}],
        "container": [{"additiveReference": {"reference": "Substance/999999"}}],
    }
    assert (await client.post(BASE + "/", json=body)).status_code == 201


async def test_create_note_author_is_checked(client):
    practitioner = await create_practitioner(client)
    ok = {
        "note": [
            {
                "text": "n",
                "authorReference": {"reference": f"Practitioner/{practitioner}"},
            }
        ]
    }
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = {
        "note": [{"text": "n", "authorReference": {"reference": "Practitioner/999999"}}]
    }
    assert (await client.post(BASE + "/", json=bad)).status_code == 422


async def test_create_every_identifier_assigner_must_exist(client):
    org = await create_organization(client)
    ok = {"value": "1", "assigner": {"reference": f"Organization/{org}"}}
    missing = {"value": "1", "assigner": {"reference": "Organization/999999"}}
    for good, bad in (
        ({"identifier": [ok]}, {"identifier": [missing]}),
        ({"accessionIdentifier": ok}, {"accessionIdentifier": missing}),
        (
            {"container": [{"identifier": [ok]}]},
            {"container": [{"identifier": [missing]}]},
        ),
    ):
        assert (await client.post(BASE + "/", json=good)).status_code == 201, good
        assert (await client.post(BASE + "/", json=bad)).status_code == 422, bad


async def test_create_absolute_and_logical_references_not_resolved(client):
    absolute = "https://other.example.org/fhir/Patient/1"
    resp = await client.post(BASE + "/", json={"subject": {"reference": absolute}})
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == {"reference": absolute}
    logical = {
        "identifier": {"system": "urn:pts", "value": "P-9"},
        "display": "External",
    }
    body = {
        "subject": logical,
        "collection": {
            "collector": {"reference": "https://other.example.org/fhir/Practitioner/7"}
        },
    }
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["subject"] == logical
    assert resp.json()["collection"]["collector"] == {
        "reference": "https://other.example.org/fhir/Practitioner/7"
    }


# ── Read ─────────────────────────────────────────────────────────────────────


async def test_get_by_id(client, patient):
    specimen, _ = await _full(client, patient)
    resp = await client.get(f"{BASE}/{specimen}")
    assert resp.status_code == 200 and resp.json()["id"] == str(specimen)


async def test_get_is_fhir_regardless_of_accept(client, patient):
    specimen = await create_specimen(client, specimen_body(patient))
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{specimen}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "Specimen"


async def test_xml_only_accept_is_406(client, patient):
    specimen = await create_specimen(client, specimen_body(patient))
    resp = await client.get(
        f"{BASE}/{specimen}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Patch ────────────────────────────────────────────────────────────────────


async def test_patch_scalar_keeps_the_rest(client, patient):
    specimen, _ = await _full(client, patient)
    resp = await client.patch(
        f"{BASE}/{specimen}",
        json={"status": "unsatisfactory", "condition": [{"text": "Clotted"}]},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "unsatisfactory"
    assert resp.json()["condition"] == [{"text": "Clotted"}]
    assert resp.json()["subject"] == {"reference": f"Patient/{patient}"}  # untouched
    assert resp.json()["collection"]["bodySite"]["coding"][0]["code"] == "368208006"


async def test_patch_reindexes_search(client, patient):
    specimen, _ = await _full(client, patient)
    await client.patch(
        f"{BASE}/{specimen}",
        json={
            "status": "unavailable",
            "type": concept(V2_0487, "SER"),
            "collection": {
                "collectedDateTime": "2024-05-01",
                "bodySite": concept(SCT, "999"),
            },
            "accessionIdentifier": {"system": "urn:acc", "value": "NEW-1"},
            "container": [{"type": concept(SCT, "888")}],
        },
    )
    for param, old, new in (
        ("status", "available", "unavailable"),
        ("type", "BLD", "SER"),
        ("collected", "2023-01-15", "2024-05-01"),
        ("bodysite", "368208006", "999"),
        ("accession", "ACC-1", "NEW-1"),
        ("container", "434746001", "888"),
    ):
        assert specimen not in _ids(
            (await client.get(BASE + "/", params={param: old})).json()
        ), param
        assert specimen in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param


async def test_patch_subject_replaced_and_reindexed(client, patient):
    specimen = await create_specimen(client, specimen_body(patient))
    other = await create_patient(client)
    resp = await client.patch(
        f"{BASE}/{specimen}", json={"subject": {"reference": f"Patient/{other}"}}
    )
    assert resp.status_code == 200, resp.text
    assert specimen not in _ids(
        (await client.get(BASE + "/", params={"patient": str(patient)})).json()
    )
    assert specimen in _ids(
        (await client.get(BASE + "/", params={"patient": str(other)})).json()
    )


async def test_patch_replaces_lists_and_empty_clears(client, patient):
    specimen, _ = await _full(client, patient)
    assert specimen in _ids(
        (await client.get(BASE + "/", params={"identifier": "SP-1001"})).json()
    )
    resp = await client.patch(
        f"{BASE}/{specimen}",
        json={
            "identifier": [],
            "parent": [],
            "container": [],
            "processing": [],
            "note": [],
            "condition": [],
        },
    )
    for gone in (
        "identifier",
        "parent",
        "container",
        "processing",
        "note",
        "condition",
    ):
        assert gone not in resp.json()
    assert resp.json()["status"] == "available"  # untouched
    assert specimen not in _ids(
        (await client.get(BASE + "/", params={"identifier": "SP-1001"})).json()
    )
    for param in ("parent", "container", "container-id"):
        assert specimen in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_clears_collected_and_missing_follows(client, patient):
    specimen = await create_specimen(
        client, specimen_body(patient, collection={"collectedDateTime": "2024-05-01"})
    )
    resp = await client.patch(f"{BASE}/{specimen}", json={"collection": None})
    assert "collection" not in resp.json()
    assert specimen in _ids(
        (await client.get(BASE + "/", params={"collected:missing": "true"})).json()
    )


async def test_patch_nonexistent_reference_rejected_and_nothing_written(
    client, patient
):
    specimen = await create_specimen(client, specimen_body(patient))
    resp = await client.patch(
        f"{BASE}/{specimen}", json={"parent": [{"reference": "Specimen/999999"}]}
    )
    assert resp.status_code == 422
    assert "parent" not in (await client.get(f"{BASE}/{specimen}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client, patient):
    specimen = await create_specimen(client, specimen_body(patient, status="available"))
    assert (
        await client.patch(f"{BASE}/{specimen}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{specimen}")).json()["status"] == "available"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"status": "available"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Delete ───────────────────────────────────────────────────────────────────


async def test_delete(client, patient):
    specimen, _ = await _full(client, patient)
    assert (await client.delete(f"{BASE}/{specimen}")).status_code == 204
    assert (await client.get(f"{BASE}/{specimen}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "SP-1001"),
        ("type", "BLD"),
        ("container-id", "C-1"),
        ("accession", "ACC-1"),
    ):
        assert specimen not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# ── Auth ─────────────────────────────────────────────────────────────────────


async def test_create_without_permission(client, patient):
    _as_user(permissions=["specimen:read"])
    assert (
        await client.post(BASE + "/", json=specimen_body(patient))
    ).status_code == 403


async def test_org_less_token_rejected(client, patient):
    specimen = await create_specimen(client, specimen_body(patient))

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": SPECIMEN_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=specimen_body())).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{specimen}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    specimen = await create_specimen(client, specimen_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{specimen}"),
            await other_client.patch(
                f"{BASE}/{specimen}", json={"status": "available"}
            ),
            await other_client.delete(f"{BASE}/{specimen}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_specimen(
        client, specimen_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}])
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()


async def test_create_request_must_exist(client):
    ok = {"request": [{"reference": "ServiceRequest/80001"}]}
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = {"request": [{"reference": "ServiceRequest/999999"}]}
    assert (await client.post(BASE + "/", json=missing)).status_code == 422
