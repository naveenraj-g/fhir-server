"""Shared helpers and payloads for location integration tests."""

BASE = "/api/fhir/v1/locations"
ORG_BASE = "/api/fhir/v1/organizations"
FHIR_ACCEPT = {"Accept": "application/fhir+json"}

# org_id / created_by are never request-body fields — they come from the
# verified JWT (actor.org_id / actor.sub), same as Organization. Location has
# no user_id at all.
MINIMAL = {
    "status": "active",
    "name": "Main Building",
    "mode": "instance",
    "address_type": "physical",
    "address_city": "Springfield",
    "address_state": "IL",
    "address_postal_code": "62701",
    "address_country": "US",
}

FULL = {
    **MINIMAL,
    "name": "South Wing, second floor",
    "description": "Second floor of the Old South Wing",
    "operational_status_system": "http://terminology.hl7.org/CodeSystem/v2-0116",
    "operational_status_code": "U",
    "operational_status_display": "Unoccupied",
    "address_use": "work",
    "address_type": "both",
    "address_line": ["Galapagosweg 91", "Building A"],
    "physical_type_system": "http://terminology.hl7.org/CodeSystem/location-physical-type",
    "physical_type_code": "wi",
    "physical_type_display": "Wing",
    "position_longitude": "-83.6945691",
    "position_latitude": "42.25475478",
    "position_altitude": "0",
    "availability_exceptions": "Reduced services on public holidays",
    "identifier": [
        {
            "system": "http://example.org/location-ids",
            "value": "B1-S.F2",
            "use": "official",
            "assigner_identifier_system": "urn:external-registry",
            "assigner_identifier_value": "EXTERNAL-1",
        }
    ],
    "type": [
        {
            "coding_system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
            "coding_code": "HOSP",
            "coding_display": "Hospital",
        }
    ],
    "alias": [{"value": "South Wing OR"}],
    "telecom": [{"system": "phone", "value": "2328", "use": "work"}],
    "hours_of_operation": [
        {
            "days_of_week": ["mon", "tue", "wed", "thu", "fri"],
            "all_day": False,
            "opening_time": "09:00:00",
            "closing_time": "17:30:00",
        }
    ],
    "endpoint": [
        {
            "reference_identifier_system": "urn:ext-endpoint",
            "reference_identifier_value": "EP-1",
        }
    ],
}


async def create_location(client, payload=None, **overrides) -> int:
    """Create a location and return its public location_id."""
    body = {**(payload or MINIMAL), **overrides}
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["id"]


async def create_organization(client, name="Owning Org") -> int:
    """Create an Organization so managingOrganization references resolve."""
    resp = await client.post(ORG_BASE + "/", json={"active": True, "name": name})
    assert resp.status_code in (200, 201), resp.text
    return resp.json()["id"]
