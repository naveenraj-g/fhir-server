"""Core observation-definition endpoint coverage.

ObservationDefinition is stored whole in `content` (like the other content-based resources): the
request body (genuine FHIR R4 ObservationDefinition JSON) is validated and stored in `content`,
every response is FHIR R4 (`application/fhir+json`, regardless of Accept). **R4 defines no search
parameter for it**, so nothing is indexed: every element must round-trip through `content`.

This file holds create, read, patch, delete and auth (org-less token, missing scope, cross-org
isolation) plus the existence check on `identifier.assigner` and on a relative
`ObservationDefinition/<id>` in a Reference element. Search (only `_id` / `_lastUpdated`) lives in
test_search.py.
"""

import pytest
from fastapi import Request

from app.auth.dependencies import get_current_user
from app.core.config import settings
from app.main import app
from tests.conftest import make_test_user
from tests.helpers.assertions import assert_operation_outcome
from tests.integration.observation_definition.conftest import (
    OBSERVATION_DEFINITION_PERMS,
)
from tests.integration.observation_definition.support import (
    BASE,
    create_observation_definition,
    create_organization,
    full_body,
    observation_definition_body,
)

ACTIVITY_DEFINITIONS = "/api/fhir/v1/activity-definitions/"
ISSUES = "/api/fhir/v1/detected-issues/"


@pytest.fixture
def native_validation(monkeypatch):
    """The base R4 validator may be switched off in configs/config.yaml; tests that assert "a key
    that isn't FHIR is a 422" need it on: the project's own structural check."""
    monkeypatch.setattr(settings.fhir_validation, "enabled", True)
    monkeypatch.setattr(settings.fhir_validation, "backend", "native")


def _as_user(sub="u-test", org_id="org-test", permissions=OBSERVATION_DEFINITION_PERMS):
    app.dependency_overrides[get_current_user] = make_test_user(
        sub=sub, org_id=org_id, permissions=permissions
    )


async def _full(client) -> tuple[int, dict]:
    organization = await create_organization(client)
    body = full_body(organization)
    return await create_observation_definition(client, body), body


# -- Create ---------------------------------------------------------------------------------


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=observation_definition_body())
    assert resp.status_code == 201, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    assert resp.json()["resourceType"] == "ObservationDefinition"
    assert resp.json()["id"] == "400000"  # the first id of the block


async def test_create_full_round_trip(client):
    observation_definition, body = await _full(client)
    data = (await client.get(f"{BASE}/{observation_definition}")).json()
    expected = {k: v for k, v in body.items() if k != "resourceType"}
    assert {
        k: v for k, v in data.items() if k not in ("resourceType", "id", "meta")
    } == expected


@pytest.mark.parametrize(
    "datatype",
    [
        "Quantity",
        "CodeableConcept",
        "string",
        "boolean",
        "integer",
        "Range",
        "Ratio",
        "SampledData",
        "time",
        "dateTime",
        "Period",
    ],
)
async def test_create_every_permitted_data_type_round_trips(client, datatype):
    body = observation_definition_body(permittedDataType=[datatype])
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["permittedDataType"] == [datatype]


@pytest.mark.parametrize("category", ["reference", "critical", "absolute"])
async def test_create_every_interval_category_round_trips(client, category):
    body = observation_definition_body(
        qualifiedInterval=[{"category": category, "range": {"low": {"value": 1}}}]
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["qualifiedInterval"][0]["category"] == category


async def test_create_ignores_server_managed_id_and_meta(client):
    body = observation_definition_body(
        id="999", meta={"lastUpdated": "2000-01-01T00:00:00Z"}
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["id"] != "999"
    assert not resp.json()["meta"]["lastUpdated"].startswith("2000")


async def test_create_bad_datatypes_rejected(client):
    for bad in (
        {"permittedDataType": ["banana"]},
        {"permittedDataType": "Quantity"},
        {"identifier": {"value": "x"}},
        {"category": {"text": "x"}},
        {"code": "718-7"},
        {"multipleResultsAllowed": "maybe"},
        {"method": "automated"},
        {"preferredReportName": 5},
        {"quantitativeDetails": "x"},
        {"qualifiedInterval": {"category": "reference"}},
        {"qualifiedInterval": [{"category": "banana"}]},
        {"qualifiedInterval": [{"gender": "robot"}]},
        {"validCodedValueSet": "ValueSet/1"},
    ):
        body = {**observation_definition_body(), **bad}
        resp = await client.post(BASE + "/", json=body)
        assert resp.status_code == 422, (bad, resp.text)


async def test_create_missing_code_rejected(client, native_validation):
    resp = await client.post(BASE + "/", json={"preferredReportName": "x"})
    assert resp.status_code == 422


async def test_create_non_fhir_key_rejected(client, native_validation):
    resp = await client.post(
        BASE + "/", json=observation_definition_body(not_a_fhir_element=1)
    )
    assert resp.status_code == 422


async def test_create_old_flat_fields_rejected(client, native_validation):
    for stale in ({"code_text": "x"}, {"method_text": "x"}, {"org_id": "x"}):
        resp = await client.post(BASE + "/", json=observation_definition_body(**stale))
        assert resp.status_code == 422, (stale, resp.text)


async def test_create_wrong_resource_type_rejected(client):
    resp = await client.post(
        BASE + "/", json=observation_definition_body(resourceType="Patient")
    )
    assert resp.status_code == 422


async def test_create_audit_meta_from_actor(client):
    data = (await client.post(BASE + "/", json=observation_definition_body())).json()
    exts = {e["url"].rsplit("/", 1)[1]: e for e in data["meta"]["extension"]}
    assert exts["org-id"]["valueString"] == "org-test"
    assert exts["created-by"]["valueString"] == "u-test"


# -- Create: existence checks on local references --------------------------------------------


async def test_create_identifier_assigner_must_exist(client):
    organization = await create_organization(client)
    ok = observation_definition_body(
        identifier=[
            {"value": "1", "assigner": {"reference": f"Organization/{organization}"}}
        ]
    )
    assert (await client.post(BASE + "/", json=ok)).status_code == 201
    bad = observation_definition_body(
        identifier=[{"value": "1", "assigner": {"reference": "Organization/999999"}}]
    )
    resp = await client.post(BASE + "/", json=bad)
    assert resp.status_code == 422 and "assigner" in resp.text


async def test_value_set_references_are_stored_as_sent(client):
    """ValueSet is not a resource on this server, so a relative, absolute or logical reference
    to one is stored as sent."""
    body = observation_definition_body(
        validCodedValueSet={"reference": "ValueSet/999999"},
        normalCodedValueSet={"reference": "https://example.org/fhir/ValueSet/normal"},
        criticalCodedValueSet={"identifier": {"value": "crit"}},
    )
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    assert resp.json()["validCodedValueSet"] == {"reference": "ValueSet/999999"}


async def test_a_relative_observation_definition_reference_is_checked(client):
    """ObservationDefinition is a rebuilt resource: a relative `ObservationDefinition/<id>` in a
    Reference (DetectedIssue.implicated is Reference(Any)) must exist."""
    observation_definition = await create_observation_definition(
        client, observation_definition_body()
    )
    ok = {
        "status": "final",
        "implicated": [
            {"reference": f"ObservationDefinition/{observation_definition}"}
        ],
    }
    assert (await client.post(ISSUES, json=ok)).status_code == 201
    bad = {
        "status": "final",
        "implicated": [{"reference": "ObservationDefinition/999999"}],
    }
    resp = await client.post(ISSUES, json=bad)
    assert resp.status_code == 422 and "implicated" in resp.text


async def test_activity_definition_requirements_are_checked(client):
    """ActivityDefinition.observationRequirement / observationResultRequirement name an
    ObservationDefinition: a relative reference must exist."""
    observation_definition = await create_observation_definition(
        client, observation_definition_body()
    )
    ref = {"reference": f"ObservationDefinition/{observation_definition}"}
    ok = {
        "status": "active",
        "observationRequirement": [ref],
        "observationResultRequirement": [ref],
    }
    assert (await client.post(ACTIVITY_DEFINITIONS, json=ok)).status_code == 201
    bad = {
        "status": "active",
        "observationRequirement": [{"reference": "ObservationDefinition/999999"}],
    }
    assert (await client.post(ACTIVITY_DEFINITIONS, json=bad)).status_code == 422


async def test_reference_in_another_org_is_rejected(client, other_client):
    _as_user(sub="u-other", org_id="org-other")
    try:
        theirs = await create_organization(other_client)
    finally:
        _as_user()
    body = observation_definition_body(
        identifier=[{"value": "1", "assigner": {"reference": f"Organization/{theirs}"}}]
    )
    assert (await client.post(BASE + "/", json=body)).status_code == 422


# -- Read -----------------------------------------------------------------------------------


async def test_get_by_id(client):
    observation_definition, _ = await _full(client)
    resp = await client.get(f"{BASE}/{observation_definition}")
    assert resp.status_code == 200 and resp.json()["id"] == str(observation_definition)


async def test_get_is_fhir_regardless_of_accept(client):
    observation_definition = await create_observation_definition(
        client, observation_definition_body()
    )
    for accept in (None, "application/json", "*/*"):
        headers = {"Accept": accept} if accept else {}
        resp = await client.get(f"{BASE}/{observation_definition}", headers=headers)
        assert resp.headers["content-type"].startswith("application/fhir+json"), accept
        assert resp.json()["resourceType"] == "ObservationDefinition"


async def test_xml_only_accept_is_406(client):
    observation_definition = await create_observation_definition(
        client, observation_definition_body()
    )
    resp = await client.get(
        f"{BASE}/{observation_definition}", headers={"Accept": "application/fhir+xml"}
    )
    assert resp.status_code == 406 and resp.json()["resourceType"] == "OperationOutcome"


async def test_get_not_found(client):
    resp = await client.get(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Patch ----------------------------------------------------------------------------------


async def test_patch_scalar_keeps_the_rest(client):
    observation_definition, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{observation_definition}",
        json={"preferredReportName": "Haemoglobin", "multipleResultsAllowed": True},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["preferredReportName"] == "Haemoglobin"
    assert resp.json()["multipleResultsAllowed"] is True
    assert resp.json()["quantitativeDetails"]["decimalPrecision"] == 1  # untouched
    assert resp.json()["qualifiedInterval"][0]["gender"] == "female"  # untouched


async def test_patch_replaces_lists_and_objects_wholesale(client):
    observation_definition, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{observation_definition}",
        json={
            "permittedDataType": ["boolean"],
            "qualifiedInterval": [],
            "quantitativeDetails": {"decimalPrecision": 3},
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["permittedDataType"] == ["boolean"]
    assert "qualifiedInterval" not in resp.json()
    assert resp.json()["quantitativeDetails"] == {"decimalPrecision": 3}
    assert resp.json()["identifier"][0]["value"] == "OD-1001"  # untouched


async def test_patch_clears_an_element(client):
    observation_definition, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{observation_definition}",
        json={"method": None, "validCodedValueSet": None},
    )
    assert "method" not in resp.json() and "validCodedValueSet" not in resp.json()
    assert resp.json()["code"]["coding"][0]["code"] == "718-7"  # untouched


async def test_patch_changes_the_code(client):
    observation_definition, _ = await _full(client)
    resp = await client.patch(
        f"{BASE}/{observation_definition}",
        json={"code": {"coding": [{"system": "http://loinc.org", "code": "4548-4"}]}},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["code"]["coding"][0]["code"] == "4548-4"


async def test_patch_nonexistent_reference_rejected_and_nothing_written(client):
    observation_definition = await create_observation_definition(
        client, observation_definition_body()
    )
    resp = await client.patch(
        f"{BASE}/{observation_definition}",
        json={
            "identifier": [
                {"value": "1", "assigner": {"reference": "Organization/999999"}}
            ]
        },
    )
    assert resp.status_code == 422
    assert (
        "identifier"
        not in (await client.get(f"{BASE}/{observation_definition}")).json()
    )


async def test_patch_invalid_value_rejected_and_nothing_written(client):
    observation_definition = await create_observation_definition(
        client, observation_definition_body()
    )
    assert (
        await client.patch(
            f"{BASE}/{observation_definition}",
            json={"permittedDataType": ["broken"]},
        )
    ).status_code == 422
    assert (
        "permittedDataType"
        not in (await client.get(f"{BASE}/{observation_definition}")).json()
    )


async def test_patch_not_found(client):
    resp = await client.patch(f"{BASE}/999999", json={"preferredReportName": "x"})
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Delete ---------------------------------------------------------------------------------


async def test_delete(client):
    observation_definition, _ = await _full(client)
    assert (await client.delete(f"{BASE}/{observation_definition}")).status_code == 204
    assert (await client.get(f"{BASE}/{observation_definition}")).status_code == 404
    bundle = (
        await client.get(BASE + "/", params={"_id": str(observation_definition)})
    ).json()
    assert bundle["total"] == 0


async def test_delete_not_found(client):
    resp = await client.delete(f"{BASE}/999999")
    assert_operation_outcome(
        resp.json(), expected_status=404, response_status=resp.status_code
    )


# -- Auth -----------------------------------------------------------------------------------


async def test_create_without_permission(client):
    _as_user(permissions=["observation_definition:read"])
    assert (
        await client.post(BASE + "/", json=observation_definition_body())
    ).status_code == 403


async def test_org_less_token_rejected(client):
    observation_definition = await create_observation_definition(
        client, observation_definition_body()
    )

    async def _no_org(request: Request):
        request.state.user = {
            "sub": "u-test",
            "permissions": OBSERVATION_DEFINITION_PERMS,
        }

    app.dependency_overrides[get_current_user] = _no_org
    assert (
        await client.post(BASE + "/", json=observation_definition_body())
    ).status_code == 403
    assert (await client.get(BASE + "/")).status_code == 403
    assert (await client.get(f"{BASE}/{observation_definition}")).status_code == 403


async def test_cross_org_get_patch_delete_return_404(client, other_client):
    _as_user()  # the other_client fixture resets the override
    observation_definition = await create_observation_definition(
        client, observation_definition_body()
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        for resp in (
            await other_client.get(f"{BASE}/{observation_definition}"),
            await other_client.patch(
                f"{BASE}/{observation_definition}", json={"preferredReportName": "x"}
            ),
            await other_client.delete(f"{BASE}/{observation_definition}"),
        ):
            assert_operation_outcome(
                resp.json(), expected_status=404, response_status=resp.status_code
            )
    finally:
        _as_user()


async def test_search_cross_tenant_isolation(client, other_client):
    _as_user()
    observation_definition = await create_observation_definition(
        client, observation_definition_body()
    )
    _as_user(sub="u-other", org_id="org-other")
    try:
        bundle = (
            await other_client.get(
                BASE + "/", params={"_id": str(observation_definition)}
            )
        ).json()
        assert bundle["total"] == 0
    finally:
        _as_user()
