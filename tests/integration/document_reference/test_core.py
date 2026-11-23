"""Core document reference endpoint coverage.

DocumentReference is stored Medplum-style (like CareTeam, CarePlan, Encounter and the other
content-based resources): the request body (genuine FHIR R4 DocumentReference JSON) is validated
and stored whole in `content`, every response is FHIR R4 (`application/fhir+json`, regardless of
Accept), and only the FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/documentreference.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence checks on every local reference (`subject`, `author`,
`authenticator`, `custodian`, `relatesTo.target`, `context.encounter` / `.related` /
`.sourcePatientInfo` and every identifier's `assigner`). Search lives in test_search.py.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.document_reference.conftest import DOCUMENT_PERMS
from tests.integration.document_reference.support import (
    BASE,
    LOINC,
    concept,
    condition_body,
    content_entry,
    create_condition,
    create_document,
    create_encounter,
    create_group,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_related_person,
    document_body,
    encounter_body,
    full_body,
    group_body,
    related_person_body,
)


@pytest.fixture
def native_validation(monkeypatch):
    """The base R4 validator may be switched off in configs/config.yaml (`fhir_validation.enabled:
    false` skips it entirely). Tests that assert "a key that isn't FHIR is a 422" need it on: the
    project's own structural check (no sidecar needed)."""
    monkeypatch.setattr(settings.fhir_validation, "enabled", True)
    monkeypatch.setattr(settings.fhir_validation, "backend", "native")


def _ids(bundle: dict) -> set[int]:
    return {
        int(e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == "match"
    }


def _as_user(sub="u-test", org_id="org-test", permissions=DOCUMENT_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client) -> tuple[int, dict]:
    organization = await create_organization(client)
    patient = await create_patient(client)
    practitioner = await create_practitioner(client)
    encounter = await create_encounter(client, encounter_body())
    condition = await create_condition(client, condition_body(patient))
    body = full_body(organization, patient, practitioner, encounter, condition)
    return await create_document(client, body), body


# -- Create ---------------------------------------------------------------------------------


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=document_body())
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    assert resp.json()["resourceType"] == "DocumentReference"
    assert resp.json()["id"] == "320000"  # the first id of the block


async def test_create_full_round_trip(client):
    document, body = await _full(client)
    data = (await client.get(f"{BASE}/{document}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_elements_nothing_searches_on(client):
    """`docStatus`, the attachment's `data` / `size` / `title` / `creation` and
    `context.sourcePatientInfo` live only in `content`."""
    document, _ = await _full(client)
    data = (await client.get(f"{BASE}/{document}")).json()
    assert data["docStatus"] == "final"
    attachment = data["content"][0]["attachment"]
    assert attachment["size"] == 1234 and attachment["title"] == "Discharge summary"
    assert attachment["creation"] == "2026-02-01"
    assert data["context"]["sourcePatientInfo"]["reference"].startswith("Patient/")


@pytest.mark.parametrize("status", ["current", "superseded", "entered-in-error"])
async def test_create_every_status_round_trips(client, status):
    resp = await client.post(BASE + "/", json=document_body(status=status))
    assert resp.status_code == 201, resp.text
    assert resp.json()["status"] == status


@pytest.mark.parametrize("code", ["replaces", "transforms", "signs", "appends"])
async def test_create_every_relation_round_trips(client, code):
    target = await create_document(client, document_body())
    body = document_body(
        relatesTo=[
            {"code": code, "target": {"reference": f"DocumentReference/{target}"}}
        ]
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["relatesTo"][0]["code"] == code


async def test_create_ignores_server_managed_id_and_meta(client):
    body = document_body(id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"})
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client):
    for bad in (
        {"status": "retired"},
        {"docStatus": "draft"},
        {"type": [concept(LOINC, "1")]},
        {"category": {"text": "x"}},
        {"category": ["x"]},
        {"subject": "Patient/1"},
        {"date": 5},
        {"author": {"reference": "Practitioner/1"}},
        {"author": ["Practitioner/1"]},
        {"authenticator": "Practitioner/1"},
        {"custodian": "Organization/1"},
        {"identifier": {"value": "x"}},
        {"masterIdentifier": [{"value": "x"}]},
        {"relatesTo": {"code": "replaces"}},
        {
            "relatesTo": [
                {"code": "deletes", "target": {"reference": "DocumentReference/1"}}
            ]
        },
        {"relatesTo": [{"code": "replaces", "target": "DocumentReference/1"}]},
        {"description": 5},
        {"securityLabel": {"text": "x"}},
        {"content": {"attachment": {}}},
        {"content": [{"attachment": "x"}]},
        {"content": [{"attachment": {"size": "big"}}]},
        {"content": [{"attachment": {}, "format": "x"}]},
        {"context": [{"encounter": []}]},
        {"context": {"encounter": {"reference": "Encounter/1"}}},
        {"context": {"period": "2026"}},
        {"context": {"facilityType": [concept(LOINC, "1")]}},
    ):
        resp = await client.post(BASE + "/", json=document_body(**bad))
        assert resp.status_code == 422, (bad, resp.text)


async def test_create_non_fhir_key_rejected(client, native_validation):
    resp = await client.post(BASE + "/", json=document_body(not_a_fhir_element=1))
    assert resp.status_code == 422


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in (
        {"subject_id": 1},
        {"org_id": "x"},
        {"user_id": "x"},
        {"doc_status": "final"},
    ):
        resp = await client.post(BASE + "/", json={**document_body(), **stale})
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(BASE + "/", json=document_body(resourceType="Patient"))
    assert resp.status_code == 422


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=document_body())).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# -- Create: existence checks on local references --------------------------------------------


async def test_create_subject_must_exist(client):
    resp = await client.post(
        BASE + "/", json=document_body(subject={"reference": "Patient/999999"})
    )
    assert resp.status_code == 422 and "subject" in resp.text
    patient = await create_patient(client)
    group = await create_group(client, group_body(type="person"))
    practitioner = await create_practitioner(client)
    for ref in (f"Patient/{patient}", f"Group/{group}", f"Practitioner/{practitioner}"):
        body = document_body(subject={"reference": ref})
        assert (await client.post(BASE + "/", json=body)).status_code == 201, ref
    for ref in ("Group/999999", "Practitioner/999999"):
        body = document_body(subject={"reference": ref})
        assert (await client.post(BASE + "/", json=body)).status_code == 422, ref


async def test_create_authors_must_exist(client):
    practitioner = await create_practitioner(client)
    organization = await create_organization(client)
    patient = await create_patient(client)
    related = await create_related_person(client, related_person_body(patient))
    role = await create_practitioner_role(
        client, {"practitioner": {"reference": f"Practitioner/{practitioner}"}}
    )
    ok = document_body(
        author=[
            {"reference": f"Practitioner/{practitioner}"},
            {"reference": f"PractitionerRole/{role}"},
            {"reference": f"Organization/{organization}"},
            {"reference": f"Patient/{patient}"},
            {"reference": f"RelatedPerson/{related}"},
        ]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = document_body(
        author=[
            {"reference": f"Practitioner/{practitioner}"},
            {"reference": "RelatedPerson/999999"},
        ]
    )
    resp = await client.post(BASE + "/", json=bad)
    assert resp.status_code == 422 and "author[1]" in resp.text


async def test_create_authenticator_and_custodian_must_exist(client):
    practitioner = await create_practitioner(client)
    organization = await create_organization(client)
    ok = document_body(
        authenticator={"reference": f"Practitioner/{practitioner}"},
        custodian={"reference": f"Organization/{organization}"},
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    for element, ref in (
        ("authenticator", "Practitioner/999999"),
        ("authenticator", "Organization/999999"),
        ("custodian", "Organization/999999"),
    ):
        resp = await client.post(
            BASE + "/", json=document_body(**{element: {"reference": ref}})
        )
        assert resp.status_code == 422 and element in resp.text, (element, ref)


async def test_create_relates_to_target_must_exist(client):
    target = await create_document(client, document_body())
    ok = document_body(
        relatesTo=[
            {"code": "replaces", "target": {"reference": f"DocumentReference/{target}"}}
        ]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = document_body(
        relatesTo=[
            {
                "code": "replaces",
                "target": {"reference": f"DocumentReference/{target}"},
            },
            {"code": "appends", "target": {"reference": "DocumentReference/999999"}},
        ]
    )
    resp = await client.post(BASE + "/", json=bad)
    assert resp.status_code == 422 and "relatesTo[1].target" in resp.text


async def test_create_context_references_must_exist(client):
    encounter = await create_encounter(client, encounter_body())
    patient = await create_patient(client)
    condition = await create_condition(client, condition_body(patient))
    ok = document_body(
        context={
            "encounter": [{"reference": f"Encounter/{encounter}"}],
            "sourcePatientInfo": {"reference": f"Patient/{patient}"},
            "related": [{"reference": f"Condition/{condition}"}],
        }
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    for context in (
        {"encounter": [{"reference": "Encounter/999999"}]},
        {"encounter": [{"reference": "EpisodeOfCare/999999"}]},
        {"sourcePatientInfo": {"reference": "Patient/999999"}},
        {"related": [{"reference": "Condition/999999"}]},
    ):
        resp = await client.post(BASE + "/", json=document_body(context=context))
        assert resp.status_code == 422, context
        assert "context" in resp.text


async def test_create_every_identifier_assigner_must_exist(client):
    for body in (
        document_body(
            masterIdentifier={
                "value": "1",
                "assigner": {"reference": "Organization/999999"},
            }
        ),
        document_body(
            identifier=[
                {"value": "1", "assigner": {"reference": "Organization/999999"}}
            ]
        ),
    ):
        assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_reference_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_patient(other_client)
    finally:
        _as_user()
    body = document_body(subject={"reference": f"Patient/{theirs}"})
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_absolute_logical_and_unmodeled_references_not_resolved(client):
    """An absolute URL, a logical (identifier-only) reference and a Device (not a resource on this
    server) are stored as sent."""
    body = document_body(
        subject={"reference": "https://other.example.org/fhir/Patient/1"},
        author=[
            {"reference": "https://other.example.org/fhir/Practitioner/9"},
            {"reference": "Device/12"},
            {"identifier": {"system": "urn:pr", "value": "P-9"}},
        ],
        custodian={"identifier": {"system": "urn:org", "value": "O-9"}},
        context={"related": [{"reference": "https://other.example.org/fhir/Task/3"}]},
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["subject"]["reference"] == "https://other.example.org/fhir/Patient/1"
    assert data["author"][1]["reference"] == "Device/12"
    assert data["author"][2]["identifier"]["value"] == "P-9"
    assert data["custodian"]["identifier"]["value"] == "O-9"


# -- Read -----------------------------------------------------------------------------------


async def test_get_by_id(client):
    document, _ = await _full(client)
    resp = await client.get(f"{BASE}/{document}")
    assert resp.status_code == 200 and resp.json()["id"] == str(document)


async def test_get_is_fhir_regardless_of_accept(client):
    document = await create_document(client, document_body())
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{document}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "DocumentReference"


async def test_xml_only_accept_is_406(client):
    document = await create_document(client, document_body())
    resp = await client.get(
        f"{BASE}/{document}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Patch ----------------------------------------------------------------------------------


async def test_patch_scalar_keeps_the_rest(client):
    document, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{document}",
        json={"status": "superseded", "description": "Old summary"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "superseded"
    assert resp.json()["description"] == "Old summary"
    assert resp.json()["type"]["coding"][0]["code"] == "34133-9"  # untouched
    assert resp.json()["docStatus"] == "final"


async def test_patch_reindexes_search(client):
    document, _ = await _full(client)
    patient = await create_patient(client)
    await client.patch(
        f"{BASE}/{document}",
        json={
            "status": "superseded",
            "type": concept(LOINC, "11488-4"),
            "description": "Consult note",
            "context": {"period": {"start": "2030-01-01"}},
            "subject": {"reference": f"Patient/{patient}"},
            "content": [content_entry("text/plain", url="https://d.example.org/n.txt")],
        },
    )
    for param, old, new in (
        ("status", "current", "superseded"),
        ("type", "34133-9", "11488-4"),
        ("description", "Discharge", "Consult"),
        ("period", "le2026-12-31", "ge2031-01-01"),
        ("contenttype", "application/pdf", "text/plain"),
        (
            "location",
            "https://documents.example.org/doc-1001.pdf",
            "https://d.example.org/n.txt",
        ),
        ("patient", None, str(patient)),
    ):
        if old is not None:
            assert document not in _ids(
                (await client.get(BASE + "/", params={param: old})).json()
            ), param
        assert document in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param


async def test_patch_replaces_lists_and_empty_clears(client):
    document, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{document}",
        json={"identifier": [], "category": [], "author": [], "securityLabel": []},
    )
    for gone in ("identifier", "category", "author", "securityLabel"):
        assert gone not in resp.json()
    assert resp.json()["status"] == "current"  # untouched
    for param in ("category", "author", "security-label"):
        assert document in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_clears_custodian_and_missing_follows(client):
    organization = await create_organization(client)
    document = await create_document(
        client, document_body(custodian={"reference": f"Organization/{organization}"})
    )
    resp = await client.patch(f"{BASE}/{document}", json={"custodian": None})
    assert "custodian" not in resp.json()
    assert document in _ids(
        (await client.get(BASE + "/", params={"custodian:missing": "true"})).json()
    )


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client):
    document = await create_document(client, document_body())
    resp = await client.patch(
        f"{BASE}/{document}",
        json={"author": [{"reference": "Practitioner/999999"}]},
    )
    assert resp.status_code == 422
    assert "author" not in (await client.get(f"{BASE}/{document}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    document = await create_document(client, document_body(status="current"))
    assert (
        await client.patch(f"{BASE}/{document}", json={"status": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{document}")).json()["status"] == "current"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"description": "x"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Delete ---------------------------------------------------------------------------------


async def test_delete(client):
    document, _ = await _full(client)
    assert (await client.delete(f"{BASE}/{document}")).status_code == 204
    assert (await client.get(f"{BASE}/{document}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "DOC-1001"),
        ("type", "34133-9"),
        ("status", "current"),
        ("contenttype", "application/pdf"),
    ):
        assert document not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Auth -----------------------------------------------------------------------------------


async def test_create_without_permission(client):
    _as_user(permissions=["document_reference:read"])
    assert (await client.post(BASE + "/", json=document_body())).status_code == 403


async def test_org_less_token_rejected(client):
    document = await create_document(client, document_body())

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": DOCUMENT_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=document_body())).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{document}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    document = await create_document(client, document_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{document}"),
            await other_client.patch(f"{BASE}/{document}", json={"description": "x"}),
            await other_client.delete(f"{BASE}/{document}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_document(
        client,
        document_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}]),
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()


# -- Other resources that point at a document ------------------------------------------------


async def test_document_is_checked_where_a_reference_any_can_name_it(client):
    """DetectedIssue.implicated is a Reference(Any): a relative DocumentReference there must
    exist."""
    document = await create_document(client, document_body())
    issues = "/api/fhir/v1/detected-issues/"
    ok = {
        "status": "final",
        "implicated": [{"reference": f"DocumentReference/{document}"}],
    }
    assert (await client.post(issues, json=ok)).status_code == 201
    missing = {
        "status": "final",
        "implicated": [{"reference": "DocumentReference/999999"}],
    }
    assert (await client.post(issues, json=missing)).status_code == 422
