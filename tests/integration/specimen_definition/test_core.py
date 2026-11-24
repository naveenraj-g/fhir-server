"""Core specimen-definition endpoint coverage.

SpecimenDefinition is stored whole in `content` (like the other content-based resources): the
request body (genuine FHIR R4 SpecimenDefinition JSON) is validated and stored in `content`, every
response is FHIR R4 (`application/fhir+json`, regardless of Accept), and only what R4's three
search parameters (`identifier`, `type`, `container`) read is indexed - the rest of `typeTested`
(container, retention time, rejection criteria, handling, ...) is plain content.

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence check on `identifier.assigner`, on a container additive Reference
and on a relative `SpecimenDefinition/<id>` in a Reference element. Search lives in
test_search.py.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.specimen_definition.conftest import SPECIMEN_DEFINITION_PERMS
from tests.integration.specimen_definition.support import (
    BASE,
    concept,
    create_organization,
    create_specimen_definition,
    full_body,
    specimen_definition_body,
    type_tested,
)

ACTIVITY_DEFINITIONS = "/api/fhir/v1/activity-definitions/"
ISSUES = "/api/fhir/v1/detected-issues/"


@pytest.fixture
def native_validation(monkeypatch):
    """The base R4 validator may be switched off in configs/config.yaml; tests that assert "a key
    that isn't FHIR is a 422" need it on: the project's own structural check."""
    monkeypatch.setattr(settings.fhir_validation, "enabled", True)
    monkeypatch.setattr(settings.fhir_validation, "backend", "native")


def _ids(bundle: dict) -> set[int]:
    return {
        int(e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == "match"
    }


def _as_user(sub="u-test", org_id="org-test", permissions=SPECIMEN_DEFINITION_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client) -> tuple[int, dict]:
    organization = await create_organization(client)
    body = full_body(organization)
    return await create_specimen_definition(client, body), body


# -- Create ---------------------------------------------------------------------------------


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=specimen_definition_body())
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    assert resp.json()["resourceType"] == "SpecimenDefinition"
    assert resp.json()["id"] == "550000"  # the first id of the block


async def test_create_empty_document_is_valid(client):
    """R4 has no required top-level element."""
    resp = await client.post(BASE + "/", json={})
    assert resp.status_code == 201, resp.text


async def test_create_full_round_trip(client):
    specimen_definition, body = await _full(client)
    data = (await client.get(f"{BASE}/{specimen_definition}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


async def test_create_keeps_the_nested_type_tested_tree(client):
    specimen_definition, _ = await _full(client)
    data = (await client.get(f"{BASE}/{specimen_definition}")).json()
    first, second = data["typeTested"]
    assert first["container"]["additive"][0] == {
        "additiveCodeableConcept": {"text": "EDTA"}
    }
    assert first["handling"][0]["temperatureRange"]["high"]["value"] == 8
    assert first["rejectionCriterion"] == [{"text": "hemolyzed"}]
    assert second["container"]["minimumVolumeString"] == "about 1 mL"
    assert first["container"].get("minimumVolumeQuantity") == {"value": 1, "unit": "mL"}


@pytest.mark.parametrize("preference", ["preferred", "alternate"])
async def test_create_every_preference_round_trips(client, preference):
    body = specimen_definition_body(typeTested=[{"preference": preference}])
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["typeTested"][0]["preference"] == preference


async def test_create_ignores_server_managed_id_and_meta(client):
    body = specimen_definition_body(
        id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"}
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client):
    for bad in (
        {"identifier": [{"value": "x"}]},
        {"identifier": "SD-1"},
        {"typeCollected": "BLD"},
        {"typeCollected": [{"text": "x"}]},
        {"patientPreparation": {"text": "x"}},
        {"timeAspect": 5},
        {"collection": "x"},
        {"typeTested": {"preference": "preferred"}},
        {"typeTested": "x"},
    ):
        resp = await client.post(BASE + "/", json={**specimen_definition_body(), **bad})
        assert resp.status_code == 422, (bad, resp.text)


async def test_create_non_fhir_key_rejected(client, native_validation):
    resp = await client.post(
        BASE + "/", json=specimen_definition_body(not_a_fhir_element=1)
    )
    assert resp.status_code == 422


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in (
        {"type_collected_text": "x"},
        {"identifier_value": "x"},
        {"org_id": "x"},
    ):
        resp = await client.post(BASE + "/", json=specimen_definition_body(**stale))
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(
        BASE + "/", json=specimen_definition_body(resourceType="Patient")
    )
    assert resp.status_code == 422


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=specimen_definition_body())).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# -- Create: existence checks on local references --------------------------------------------


async def test_create_identifier_assigner_must_exist(client):
    organization = await create_organization(client)
    ok = specimen_definition_body(
        identifier={
            "value": "1",
            "assigner": {"reference": f"Organization/{organization}"},
        }
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = specimen_definition_body(
        identifier={"value": "1", "assigner": {"reference": "Organization/999999"}}
    )
    resp = await client.post(BASE + "/", json=bad)
    assert resp.status_code == 422 and "assigner" in resp.text


async def test_container_additive_reference_is_checked_when_a_rebuilt_type(client):
    """`additiveReference` is Reference(Substance), which is not a resource here, so it is stored
    as sent - but any rebuilt type in it is checked like every Reference."""
    stored = specimen_definition_body(
        typeTested=[
            {
                "preference": "preferred",
                "container": {
                    "additive": [
                        {"additiveReference": {"reference": "Substance/999999"}}
                    ]
                },
            }
        ]
    )
    assert (await client.post(BASE + "/", json=stored)).status_code == 201
    bad = specimen_definition_body(
        typeTested=[
            {
                "preference": "preferred",
                "container": {
                    "additive": [
                        {"additiveReference": {"reference": "Organization/999999"}}
                    ]
                },
            }
        ]
    )
    resp = await client.post(BASE + "/", json=bad)
    assert (
        resp.status_code == 422 and "typeTested[0].container.additive[0]" in resp.text
    )


async def test_a_relative_specimen_definition_reference_is_checked(client):
    """SpecimenDefinition is a rebuilt resource: a relative `SpecimenDefinition/<id>` in a
    Reference (DetectedIssue.implicated is Reference(Any)) must exist."""
    specimen_definition = await create_specimen_definition(
        client, specimen_definition_body()
    )
    ok = {
        "status": "final",
        "implicated": [{"reference": f"SpecimenDefinition/{specimen_definition}"}],
    }
    assert (await client.post(ISSUES, json=ok)).status_code == 201
    bad = {
        "status": "final",
        "implicated": [{"reference": "SpecimenDefinition/999999"}],
    }
    resp = await client.post(ISSUES, json=bad)
    assert resp.status_code == 422 and "implicated" in resp.text


async def test_activity_definition_specimen_requirement_is_checked(client):
    """ActivityDefinition.specimenRequirement names a SpecimenDefinition."""
    specimen_definition = await create_specimen_definition(
        client, specimen_definition_body()
    )
    ref = {"reference": f"SpecimenDefinition/{specimen_definition}"}
    ok = {"status": "active", "specimenRequirement": [ref]}
    assert (await client.post(ACTIVITY_DEFINITIONS, json=ok)).status_code == 201
    bad = {
        "status": "active",
        "specimenRequirement": [{"reference": "SpecimenDefinition/999999"}],
    }
    assert (await client.post(ACTIVITY_DEFINITIONS, json=bad)).status_code == 422


async def test_reference_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_organization(other_client)
    finally:
        _as_user()
    body = specimen_definition_body(
        identifier={"value": "1", "assigner": {"reference": f"Organization/{theirs}"}}
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 422


# -- Read -----------------------------------------------------------------------------------


async def test_get_by_id(client):
    specimen_definition, _ = await _full(client)
    resp = await client.get(f"{BASE}/{specimen_definition}")
    assert resp.status_code == 200 and resp.json()["id"] == str(specimen_definition)


async def test_get_is_fhir_regardless_of_accept(client):
    specimen_definition = await create_specimen_definition(
        client, specimen_definition_body()
    )
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{specimen_definition}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "SpecimenDefinition"


async def test_xml_only_accept_is_406(client):
    specimen_definition = await create_specimen_definition(
        client, specimen_definition_body()
    )
    resp = await client.get(
        f"{BASE}/{specimen_definition}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Patch ----------------------------------------------------------------------------------


async def test_patch_scalar_keeps_the_rest(client):
    specimen_definition, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{specimen_definition}", json={"timeAspect": "Afternoon"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["timeAspect"] == "Afternoon"
    assert resp.json()["collection"] == [{"text": "Venipuncture"}]  # untouched
    assert len(resp.json()["typeTested"]) == 2  # untouched


async def test_patch_reindexes_search(client):
    specimen_definition, _ = await _full(client)
    patched = await client.patch(
        f"{BASE}/{specimen_definition}",
        json={
            "typeCollected": concept("URN", "Urine"),
            "identifier": {"system": "urn:sd", "value": "SD-2"},
            "typeTested": [type_tested("CUP")],
        },
    )
    assert patched.status_code == 200, patched.text
    for param, old, new in (
        ("type", "BLD", "URN"),
        ("identifier", "SD-1001", "SD-2"),
        ("container", "SPECIMEN", "CUP"),
    ):
        assert specimen_definition not in _ids(
            (await client.get(BASE + "/", params={param: old})).json()
        ), param
        assert specimen_definition in _ids(
            (await client.get(BASE + "/", params={param: new})).json()
        ), param


async def test_patch_replaces_lists_and_empty_clears(client):
    specimen_definition, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{specimen_definition}",
        json={"typeTested": [], "patientPreparation": [], "collection": []},
    )
    for gone in ("typeTested", "patientPreparation", "collection"):
        assert gone not in resp.json()
    assert resp.json()["timeAspect"] == "Morning"  # untouched
    assert specimen_definition in _ids(
        (await client.get(BASE + "/", params={"container:missing": "true"})).json()
    )


async def test_patch_clears_an_element_and_missing_follows(client):
    specimen_definition, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{specimen_definition}",
        json={"identifier": None, "typeCollected": None},
    )
    assert "identifier" not in resp.json() and "typeCollected" not in resp.json()
    for param in ("identifier", "type"):
        assert specimen_definition in _ids(
            (await client.get(BASE + "/", params={f"{param}:missing": "true"})).json()
        ), param


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client):
    specimen_definition = await create_specimen_definition(
        client, specimen_definition_body()
    )
    resp = await client.patch(
        f"{BASE}/{specimen_definition}",
        json={
            "identifier": {
                "value": "1",
                "assigner": {"reference": "Organization/999999"},
            }
        },
    )
    assert resp.status_code == 422
    assert (
        "identifier" not in (await client.get(f"{BASE}/{specimen_definition}")).json()
    )


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    specimen_definition = await create_specimen_definition(
        client, specimen_definition_body()
    )
    assert (
        await client.patch(f"{BASE}/{specimen_definition}", json={"timeAspect": 5})
    ).status_code == 422
    assert (
        "timeAspect" not in (await client.get(f"{BASE}/{specimen_definition}")).json()
    )


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"timeAspect": "x"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Delete ---------------------------------------------------------------------------------


async def test_delete(client):
    specimen_definition, _ = await _full(client)
    assert (await client.delete(f"{BASE}/{specimen_definition}")).status_code == 204
    assert (await client.get(f"{BASE}/{specimen_definition}")).status_code == 404
    # Its index rows are gone with it.
    for param, value in (
        ("identifier", "SD-1001"),
        ("type", "BLD"),
        ("container", "SPECIMEN"),
    ):
        assert specimen_definition not in _ids(
            (await client.get(BASE + "/", params={param: value})).json()
        ), param


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Auth -----------------------------------------------------------------------------------


async def test_create_without_permission(client):
    _as_user(permissions=["specimen_definition:read"])
    assert (
        await client.post(BASE + "/", json=specimen_definition_body())
    ).status_code == 403


async def test_org_less_token_rejected(client):
    specimen_definition = await create_specimen_definition(
        client, specimen_definition_body()
    )

    async def _no_org(request: Request):
        request.state.user = {"sub": "u-test", "permissions": SPECIMEN_DEFINITION_PERMS}

    app.dependency_overrides[get_current_user] = _no_org
    assert (
        await client.post(BASE + "/", json=specimen_definition_body())
    ).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{specimen_definition}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    specimen_definition = await create_specimen_definition(
        client, specimen_definition_body()
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{specimen_definition}"),
            await other_client.patch(
                f"{BASE}/{specimen_definition}", json={"timeAspect": "x"}
            ),
            await other_client.delete(f"{BASE}/{specimen_definition}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    await create_specimen_definition(
        client,
        specimen_definition_body(
            identifier={"system": "urn:t", "value": "TenantAOnly"}
        ),
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(BASE + "/", params={"identifier": "TenantAOnly"})
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()
