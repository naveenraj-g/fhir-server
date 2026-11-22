"""Core group endpoint coverage.

Group is stored Medplum-style (like Patient, Encounter, Condition, Procedure, ServiceRequest,
Medication and the other content-based resources): the request body (genuine FHIR R4 Group JSON)
is validated and stored whole in `content`, every response is FHIR R4 (`application/fhir+json`,
regardless of Accept), and only the FHIR R4 search parameters are indexed
(https://www.hl7.org/fhir/R4/group.html#search).

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence checks on every local reference (`managingEntity`, `member.entity`,
`characteristic.valueReference` and every identifier's `assigner`). Search lives in
test_search.py.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.group.conftest import GROUP_PERMS
from tests.integration.group.support import (
    BASE,
    LOINC,
    SCT,
    concept,
    create_group,
    create_medication,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_related_person,
    full_body,
    group_body,
    medication_body,
    related_person_body,
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


def _as_user(sub="u-test", org_id="org-test", permissions=GROUP_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client) -> tuple[int, dict]:
    organization = await create_organization(client)
    patient = await create_patient(client)
    practitioner = await create_practitioner(client)
    member_group = await create_group(client, group_body(type="person"))
    body = full_body(organization, patient, practitioner, member_group)
    return await create_group(client, body), body


# -- Create ---------------------------------------------------------------------------------


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=group_body())
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    data = resp.json()
    assert data["resourceType"] == "Group"
    assert data["type"] == "person" and data["actual"] is True


async def test_create_full_round_trip(client):
    group, body = await _full(client)
    data = (await client.get(f"{BASE}/{group}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_elements_nothing_searches_on(client):
    """`name`, `quantity`, `active`, a Range characteristic value, `characteristic.period` and
    `member.period` / `.inactive` live only in `content`."""
    group, _ = await _full(client)
    data = (await client.get(f"{BASE}/{group}")).json()
    assert data["name"] == "Diabetes cohort" and data["quantity"] == 3
    assert data["active"] is True
    assert data["characteristic"][0]["valueRange"]["high"]["value"] == 190
    assert data["characteristic"][0]["period"] == {"start": "2023-01-01"}
    assert data["member"][0]["period"] == {"start": "2023-01-01"}
    assert data["member"][0]["inactive"] is False


@pytest.mark.parametrize(
    "value",
    [
        {"valueCodeableConcept": {"text": "x"}},
        {"valueBoolean": True},
        {"valueQuantity": {"value": 5, "unit": "kg"}},
        {"valueRange": {"low": {"value": 1}, "high": {"value": 3}}},
        {
            "valueReference": {
                "reference": "https://other.example.org/fhir/Observation/1"
            }
        },
    ],
    ids=["codeableConcept", "boolean", "quantity", "range", "reference"],
)
async def test_create_each_characteristic_value_choice_round_trips(client, value):
    characteristic = [{"code": {"text": "c"}, "exclude": False, **value}]
    resp = await client.post(BASE + "/", json=group_body(characteristic=characteristic))
    assert resp.status_code == 201, resp.text
    assert resp.json()["characteristic"] == characteristic


@pytest.mark.parametrize(
    "group_type",
    ["person", "animal", "practitioner", "device", "medication", "substance"],
)
async def test_create_every_type_round_trips(client, group_type):
    resp = await client.post(BASE + "/", json=group_body(type=group_type))
    assert resp.status_code == 201, resp.text
    assert resp.json()["type"] == group_type


async def test_create_ignores_server_managed_id_and_meta(client):
    body = group_body(id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"})
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client):
    for bad in (
        {"type": "robot"},
        {"actual": "yes"},
        {"active": "yes"},
        {"code": "x"},
        {"name": 5},
        {"quantity": -1},
        {"quantity": "many"},
        {"identifier": {"value": "x"}},
        {"managingEntity": "Organization/1"},
        {"characteristic": {"code": {"text": "x"}}},
        {"characteristic": [{"code": "x"}]},
        {"characteristic": [{"exclude": "no"}]},
        {"characteristic": [{"valueBoolean": "yes"}]},
        {"member": {"entity": {"reference": "Patient/1"}}},
        {"member": [{"entity": "Patient/1"}]},
        {"member": [{"inactive": "no"}]},
    ):
        resp = await client.post(BASE + "/", json=group_body(**bad))
        assert resp.status_code == 422, (bad, resp.text)


async def test_create_non_fhir_key_rejected(client, native_validation):
    resp = await client.post(BASE + "/", json=group_body(not_a_fhir_element=1))
    assert resp.status_code == 422


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in ({"code_text": "x"}, {"managing_entity_id": 1}, {"org_id": "x"}):
        resp = await client.post(BASE + "/", json={**group_body(), **stale})
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(BASE + "/", json=group_body(resourceType="Patient"))
    assert resp.status_code == 422


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=group_body())).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# -- Create: existence checks on local references --------------------------------------------


async def test_create_managing_entity_must_exist(client):
    organization = await create_organization(client)
    practitioner = await create_practitioner(client)
    role = await create_practitioner_role(client)
    patient = await create_patient(client)
    related = await create_related_person(client, related_person_body(patient))
    for ref in (
        f"Organization/{organization}",
        f"Practitioner/{practitioner}",
        f"PractitionerRole/{role}",
        f"RelatedPerson/{related}",
    ):
        body = group_body(managingEntity={"reference": ref})
        assert (await client.post(BASE + "/", json=body)).status_code == 201, ref
    for missing in (
        "Organization/999999",
        "Practitioner/999999",
        "PractitionerRole/999999",
        "RelatedPerson/999999",
    ):
        body = group_body(managingEntity={"reference": missing})
        assert (await client.post(BASE + "/", json=body)).status_code == 422, missing


async def test_create_managing_entity_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_organization(other_client)
    finally:
        _as_user()
    body = group_body(managingEntity={"reference": f"Organization/{theirs}"})
    assert (await client.post(BASE + "/", json=body)).status_code == 422


async def test_create_members_must_exist(client):
    patient = await create_patient(client)
    practitioner = await create_practitioner(client)
    role = await create_practitioner_role(client)
    medication = await create_medication(client, medication_body())
    first = await create_group(client, group_body())
    for ref in (
        f"Patient/{patient}",
        f"Practitioner/{practitioner}",
        f"PractitionerRole/{role}",
        f"Medication/{medication}",
        f"Group/{first}",
    ):
        body = group_body(member=[{"entity": {"reference": ref}}])
        assert (await client.post(BASE + "/", json=body)).status_code == 201, ref
    for missing in (
        "Patient/999999",
        "Practitioner/999999",
        "PractitionerRole/999999",
        "Medication/999999",
        "Group/999999",
    ):
        body = group_body(member=[{"entity": {"reference": missing}}])
        assert (await client.post(BASE + "/", json=body)).status_code == 422, missing


async def test_create_device_and_substance_members_are_not_checked(client):
    body = group_body(
        member=[
            {"entity": {"reference": "Device/999999"}},
            {"entity": {"reference": "Substance/999999"}},
        ]
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["member"][0]["entity"] == {"reference": "Device/999999"}


async def test_create_characteristic_value_reference_is_checked_for_rebuilt_types(
    client,
):
    patient = await create_patient(client)
    ok = group_body(
        characteristic=[
            {
                "code": {"text": "c"},
                "exclude": False,
                "valueReference": {"reference": f"Patient/{patient}"},
            }
        ]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    missing = group_body(
        characteristic=[
            {
                "code": {"text": "c"},
                "exclude": False,
                "valueReference": {"reference": "Patient/999999"},
            }
        ]
    )
    assert (await client.post(BASE + "/", json=missing)).status_code == 422


async def test_create_every_identifier_assigner_must_exist(client):
    org = await create_organization(client)
    ok = {"value": "1", "assigner": {"reference": f"Organization/{org}"}}
    missing = {"value": "1", "assigner": {"reference": "Organization/999999"}}
    assert (
        await client.post(BASE + "/", json=group_body(identifier=[ok]))
    ).status_code == 201
    assert (
        await client.post(BASE + "/", json=group_body(identifier=[missing]))
    ).status_code == 422


async def test_create_absolute_and_logical_references_not_resolved(client):
    absolute = "https://other.example.org/fhir/Organization/7"
    resp = await client.post(
        BASE + "/", json=group_body(managingEntity={"reference": absolute})
    )
    assert resp.status_code == 201, resp.text
    assert resp.json()["managingEntity"] == {"reference": absolute}
    logical = {
        "identifier": {"system": "urn:pts", "value": "P-9"},
        "display": "External",
    }
    resp = await client.post(BASE + "/", json=group_body(member=[{"entity": logical}]))
    assert resp.status_code == 201, resp.text
    assert resp.json()["member"][0]["entity"] == logical


# -- Read -----------------------------------------------------------------------------------


async def test_get_by_id(client):
    group, _ = await _full(client)
    resp = await client.get(f"{BASE}/{group}")
    assert resp.status_code == 200 and resp.json()["id"] == str(group)


async def test_get_is_fhir_regardless_of_accept(client):
    group = await create_group(client, group_body())
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{group}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "Group"


async def test_xml_only_accept_is_406(client):
    group = await create_group(client, group_body())
    resp = await client.get(
        f"{BASE}/{group}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Patch ----------------------------------------------------------------------------------


async def test_patch_scalar_keeps_the_rest(client):
    group, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{group}", json={"active": False, "name": "Retired", "type": "animal"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["active"] is False and resp.json()["name"] == "Retired"
    assert resp.json()["type"] == "animal"
    assert resp.json()["actual"] is True  # untouched
    assert resp.json()["member"][0]["inactive"] is False


async def test_patch_reindexes_search(client):
    group, _ = await _full(client)
    await client.patch(
        f"{BASE}/{group}",
        json={
            "type": "animal",
            "actual": False,
            "member": [],
            "code": concept(SCT, "999"),
            "characteristic": [
                {
                    "code": concept(LOINC, "1111-1"),
                    "valueBoolean": False,
                    "exclude": False,
                }
            ],
        },
    )
    for param, old, new in (
        ("type", "person", "animal"),
        ("actual", "true", "false"),
        ("code", "385093006", "999"),
        ("characteristic", "8302-2", "1111-1"),
    ):
        assert group not in _ids(
            (await client.get(BASE + "/", params={param: old})).json()
        ), param
        assert group in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param
    assert group in _ids(
        (await client.get(BASE + "/", params={"member:missing": "true"})).json()
    )
    assert group in _ids(
        (await client.get(BASE + "/", params={"exclude": "false"})).json()
    )
    assert group not in _ids(
        (await client.get(BASE + "/", params={"exclude": "true"})).json()
    )


async def test_patch_replaces_lists_and_empty_clears(client):
    group, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{group}", json={"identifier": [], "characteristic": [], "member": []}
    )
    for gone in ("identifier", "characteristic", "member"):
        assert gone not in resp.json()
    assert resp.json()["type"] == "person"  # untouched
    for param in ("identifier", "characteristic", "member", "value", "exclude"):
        assert group in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_clears_managing_entity_and_missing_follows(client):
    organization = await create_organization(client)
    group = await create_group(
        client, group_body(managingEntity={"reference": f"Organization/{organization}"})
    )
    resp = await client.patch(f"{BASE}/{group}", json={"managingEntity": None})
    assert "managingEntity" not in resp.json()
    assert group in _ids(
        (
            await client.get(BASE + "/", params={"managing-entity:missing": "true"})
        ).json()
    )


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client):
    group = await create_group(client, group_body())
    resp = await client.patch(
        f"{BASE}/{group}",
        json={"member": [{"entity": {"reference": "Patient/999999"}}]},
    )
    assert resp.status_code == 422
    assert "member" not in (await client.get(f"{BASE}/{group}")).json()


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    group = await create_group(client, group_body(type="person"))
    assert (
        await client.patch(f"{BASE}/{group}", json={"type": "broken"})
    ).status_code == 422
    assert (await client.get(f"{BASE}/{group}")).json()["type"] == "person"


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"active": True})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Delete ---------------------------------------------------------------------------------


async def test_delete(client):
    group, _ = await _full(client)
    assert (await client.delete(f"{BASE}/{group}")).status_code == 204
    assert (await client.get(f"{BASE}/{group}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "GRP-1001"),
        ("code", "385093006"),
        ("characteristic", "8302-2"),
        ("exclude", "true"),
    ):
        assert group not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Auth -----------------------------------------------------------------------------------


async def test_create_without_permission(client):
    _as_user(permissions=["group:read"])
    assert (await client.post(BASE + "/", json=group_body())).status_code == 403


async def test_org_less_token_rejected(client):
    group = await create_group(client, group_body())

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": GROUP_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (await client.post(BASE + "/", json=group_body())).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{group}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    group = await create_group(client, group_body())
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{group}"),
            await other_client.patch(f"{BASE}/{group}", json={"active": True}),
            await other_client.delete(f"{BASE}/{group}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_group(
        client, group_body(identifier=[{"system": "urn:t", "value": "TenantAOnly"}])
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()


async def test_group_is_checked_where_a_reference_any_can_name_it(client):
    """DetectedIssue.implicated is a Reference(Any): a relative Group there must exist."""
    group = await create_group(client, group_body())
    issues = "/api/fhir/v1/detected-issues/"
    ok = {"status": "final", "implicated": [{"reference": f"Group/{group}"}]}
    assert (await client.post(issues, json=ok)).status_code == 201
    missing = {"status": "final", "implicated": [{"reference": "Group/999999"}]}
    assert (await client.post(issues, json=missing)).status_code == 422
