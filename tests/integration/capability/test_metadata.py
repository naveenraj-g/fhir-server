"""GET /api/fhir/v1/metadata — the generated CapabilityStatement."""

import pytest

from app.core.config import settings
from app.repository.endpoint.search import endpoint_search
from app.repository.healthcare_service.search import healthcare_service_search
from app.repository.location.search import location_search
from app.repository.organization.search import organization_search
from app.repository.practitioner_role.search import practitioner_role_search
from app.repository.practitioner.search import practitioner_search

URL = "/api/fhir/v1/metadata"


async def _statement(client) -> dict:
    r = await client.get(URL)
    assert r.status_code == 200, r.text
    assert r.headers["content-type"].startswith("application/fhir+json")
    return r.json()


async def test_statement_basics(client):
    cs = await _statement(client)
    assert cs["resourceType"] == "CapabilityStatement"
    assert cs["fhirVersion"] == "4.0.1"
    assert cs["kind"] == "instance"
    assert cs["status"] == "active"
    assert cs["rest"][0]["mode"] == "server"


async def test_search_params_match_registries(client):
    cs = await _statement(client)
    by_type = {r["type"]: r for r in cs["rest"][0]["resource"]}
    expected = {
        "organization": ("Organization", organization_search()),
        "location": ("Location", location_search()),
        "practitioner": ("Practitioner", practitioner_search()),
        "healthcare_service": ("HealthcareService", healthcare_service_search()),
        "endpoint": ("Endpoint", endpoint_search()),
        "practitioner_role": ("PractitionerRole", practitioner_role_search()),
    }
    enabled = {k: v for k, v in expected.items() if k in settings.routes.enabled}
    assert set(by_type) == {t for t, _ in enabled.values()}  # only what is mounted
    for rtype, registry in enabled.values():
        entry = by_type[rtype]
        assert {p["name"] for p in entry["searchParam"]} == set(registry.params)
        assert {"read", "create", "patch", "delete", "search-type"} == {i["code"] for i in entry["interaction"]}


async def test_includes_and_param_types(client):
    cs = await _statement(client)
    by_type = {r["type"]: r for r in cs["rest"][0]["resource"]}
    assert "Organization:partof" in by_type["Organization"]["searchInclude"]
    assert "Location:organization" in by_type["Organization"]["searchRevInclude"]
    if "location" not in settings.routes.enabled:
        pytest.skip("location router not enabled in configs/config.yaml")
    loc = {p["name"]: p for p in by_type["Location"]["searchParam"]}
    assert loc["near"]["type"] == "special"
    assert loc["_id"]["definition"] == "http://hl7.org/fhir/SearchParameter/Resource-id"
    assert loc["address-city"]["definition"].endswith("/Location-address-city")
