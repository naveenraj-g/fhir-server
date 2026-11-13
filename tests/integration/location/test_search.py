"""FHIR R4 search over Location (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/location.html#search).

One block per Location search parameter — including `near` with its
location-distance result extension, `organization` chaining into
Organization's parameters and the partOf hierarchy — plus the cross-resource
includes (`_include=Location:organization`,
Organization `_revinclude=Location:organization`). The generic engine
behaviour (escaping, paging, `_summary`, lenient/strict handling, ...) is
covered once in tests/integration/organization/test_search.py.
"""

from tests.integration.location.support import BASE, FULL, MINIMAL, ORG_BASE, create_location, create_organization

ROLE = "http://terminology.hl7.org/CodeSystem/v3-RoleCode"
BED = "http://terminology.hl7.org/CodeSystem/v2-0116"
DISTANCE = "http://hl7.org/fhir/StructureDefinition/location-distance"


async def _get(client, params, base=BASE):
    return await client.get(base + "/", params=params)


async def _search(client, params=None, base=BASE) -> dict:
    resp = await _get(client, params or {}, base)
    assert resp.status_code == 200, resp.text
    return resp.json()


def _ids(bundle: dict, mode: str = "match") -> set[int]:
    return {int(e["resource"]["id"]) for e in bundle.get("entry") or [] if e["search"]["mode"] == mode}


def _typed(bundle: dict, mode: str = "include") -> set[tuple[str, int]]:
    return {
        (e["resource"]["resourceType"], int(e["resource"]["id"]))
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == mode
    }


async def _ids_for(client, params) -> set[int]:
    return _ids(await _search(client, params))


async def _loc(client, **fields) -> int:
    return await create_location(client, {**MINIMAL, **fields})


def _rejected(resp, code="invalid"):
    assert resp.status_code == 400, resp.text
    assert resp.json()["issue"][0]["code"] == code, resp.json()


# ── Bundle ───────────────────────────────────────────────────────────────────


async def test_bundle_shape(client):
    loc_id = await _loc(client)
    bundle = await _search(client)
    assert bundle["type"] == "searchset" and bundle["total"] == 1
    assert bundle["entry"][0]["fullUrl"] == f"http://test{BASE}/{loc_id}"
    assert bundle["entry"][0]["search"] == {"mode": "match"}


# ── name / address strings ───────────────────────────────────────────────────


async def test_name_and_alias(client):
    a = await _loc(client, name="Hôpital Saint-Éloi")
    b = await _loc(client, name="Annex", alias=["Hopital Annex"])
    assert await _ids_for(client, {"name": "hopital"}) == {a, b}
    assert await _ids_for(client, {"name": "saint"}) == set()  # starts-with, not contains
    assert await _ids_for(client, {"name:contains": "saint"}) == {a}
    assert await _ids_for(client, {"name:exact": "Hôpital Saint-Éloi"}) == {a}
    assert await _ids_for(client, {"name:exact": "hopital saint-eloi"}) == set()


async def test_address_parameters(client):
    loc_id = await _loc(
        client,
        address={"use": "work", "line": ["Suite 5", "12 Main St"], "city": "Springfield", "district": "Sangamon",
                 "state": "Illinois", "postalCode": "62701", "country": "USA"},
    )
    other = await _loc(client, address={"use": "home", "city": "Shelbyville"})
    for value in ("suite", "12 main", "spring", "sanga", "illi", "627", "us"):
        assert await _ids_for(client, {"address": value}) == {loc_id}, value
    assert await _ids_for(client, {"address-city": "spring"}) == {loc_id}
    assert await _ids_for(client, {"address-city:exact": "springfield"}) == set()
    assert await _ids_for(client, {"address-state": "ill"}) == {loc_id}
    assert await _ids_for(client, {"address-postalcode": "62"}) == {loc_id}
    assert await _ids_for(client, {"address-country": "usa"}) == {loc_id}
    assert await _ids_for(client, {"address-use": "work"}) == {loc_id}
    assert await _ids_for(client, {"address-use:not": "work"}) == {other}
    assert await _ids_for(client, {"address-state:missing": "true"}) == {other}


# ── tokens ───────────────────────────────────────────────────────────────────


async def test_status(client):
    active = await _loc(client, name="A", status="active")
    suspended = await _loc(client, name="S", status="suspended")
    unknown = await create_location(client, {"name": "No status"})
    assert await _ids_for(client, {"status": "active"}) == {active}
    assert await _ids_for(client, {"status": "http://hl7.org/fhir/location-status|suspended"}) == {suspended}
    assert await _ids_for(client, {"status": "active,suspended"}) == {active, suspended}
    assert await _ids_for(client, {"status": "bogus"}) == set()
    # :not includes resources with no status at all.
    assert await _ids_for(client, {"status:not": "active"}) == {suspended, unknown}
    assert await _ids_for(client, {"status:missing": "true"}) == {unknown}


async def test_operational_status(client):
    unoccupied = await _loc(client, operationalStatus={"system": BED, "code": "U", "display": "Unoccupied"})
    await _loc(client, operationalStatus={"system": BED, "code": "K", "display": "Contaminated"})
    none = await _loc(client)
    assert await _ids_for(client, {"operational-status": "U"}) == {unoccupied}
    assert await _ids_for(client, {"operational-status": f"{BED}|U"}) == {unoccupied}
    assert await _ids_for(client, {"operational-status:text": "unocc"}) == {unoccupied}
    assert none in await _ids_for(client, {"operational-status:not": "K"})
    assert await _ids_for(client, {"operational-status:missing": "true"}) == {none}


async def test_identifier_and_type(client):
    loc_id = await create_location(client, FULL)
    await _loc(client, type=[{"text": "Pharmacy counter"}])
    system = "https://fhir-server.dev/fhir/identifier-system/location-ids"
    assert await _ids_for(client, {"identifier": f"{system}|B1-S.F2"}) == {loc_id}
    assert await _ids_for(client, {"identifier": "B1-S.F2"}) == {loc_id}
    assert await _ids_for(client, {"type": f"{ROLE}|HOSP"}) == {loc_id}
    assert await _ids_for(client, {"type:text": "hosp"}) == {loc_id}
    assert len(await _ids_for(client, {"type:text": "pharmacy"})) == 1


# ── references ───────────────────────────────────────────────────────────────


async def test_organization_reference_and_chain(client):
    org_a = await create_organization(client, "Acme Health")
    org_b = await create_organization(client, "Beta Care")
    at_a = await _loc(client, name="A1", managingOrganization={"reference": f"Organization/{org_a}"})
    at_b = await _loc(client, name="B1", managingOrganization={"reference": f"Organization/{org_b}"})
    by_ident = await _loc(client, name="I1", managingOrganization={"identifier": {"system": "urn:reg", "value": "R-1"}})
    assert await _ids_for(client, {"organization": f"Organization/{org_a}"}) == {at_a}
    assert await _ids_for(client, {"organization": str(org_b)}) == {at_b}
    assert await _ids_for(client, {"organization:Organization": str(org_a)}) == {at_a}
    assert await _ids_for(client, {"organization:identifier": "urn:reg|R-1"}) == {by_ident}
    # Chaining into Organization's own search parameters.
    assert await _ids_for(client, {"organization.name": "acme"}) == {at_a}
    assert await _ids_for(client, {"organization.name:exact": "Beta Care"}) == {at_b}
    assert await _ids_for(client, {"organization._id": str(org_a)}) == {at_a}
    _rejected(await _get(client, {"organization.nonsense": "x"}), "not-supported")


async def test_partof_hierarchy_and_chain(client):
    building = await _loc(client, name="Building")
    wing = await _loc(client, name="Wing", partOf={"reference": f"Location/{building}"})
    room = await _loc(client, name="Room", partOf={"reference": f"Location/{wing}"})
    assert await _ids_for(client, {"partof": f"Location/{building}"}) == {wing}
    assert await _ids_for(client, {"partof:below": str(building)}) == {wing, room}
    assert await _ids_for(client, {"partof:above": str(wing)}) == {wing, room}
    assert await _ids_for(client, {"partof.name": "build"}) == {wing}
    assert await _ids_for(client, {"partof.partof.name": "build"}) == {room}
    assert await _ids_for(client, {"partof:missing": "true"}) == {building}


async def test_endpoint(client):
    loc_id = await _loc(client, endpoint=[{"reference": "Endpoint/3"}])
    by_ident = await create_location(client, FULL)
    assert await _ids_for(client, {"endpoint": "Endpoint/3"}) == {loc_id}
    assert await _ids_for(client, {"endpoint:identifier": "urn:ext-endpoint|EP-1"}) == {by_ident}


# ── near ─────────────────────────────────────────────────────────────────────


async def test_near(client):
    # Ann Arbor, ~0.6 km and ~12 km from the query point; Detroit ~55 km.
    close = await _loc(client, name="Close", position={"latitude": 42.2808, "longitude": -83.7430})
    mid = await _loc(client, name="Mid", position={"latitude": 42.2400, "longitude": -83.6000})
    far = await _loc(client, name="Far", position={"latitude": 42.3314, "longitude": -83.0458})
    await _loc(client, name="Nowhere")
    point = "42.2770|-83.7400"
    assert await _ids_for(client, {"near": f"{point}|1|km"}) == {close}
    assert await _ids_for(client, {"near": f"{point}|20|km"}) == {close, mid}
    assert await _ids_for(client, {"near": f"{point}|20"}) == {close, mid}  # km by default
    assert await _ids_for(client, {"near": f"{point}|1000|m"}) == {close}
    assert await _ids_for(client, {"near": f"{point}|40|[mi_i]"}) == {close, mid, far}
    assert await _ids_for(client, {"near": point}) == {close, mid}  # default 50 km


async def test_near_reports_distance(client):
    await _loc(client, name="Close", position={"latitude": 42.2808, "longitude": -83.7430})
    bundle = await _search(client, {"near": "42.2770|-83.7400|5|km"})
    ext = bundle["entry"][0]["search"]["extension"][0]
    assert ext["url"] == DISTANCE
    assert ext["valueDistance"]["unit"] == "km" and ext["valueDistance"]["code"] == "km"
    assert 0.3 < ext["valueDistance"]["value"] < 0.7


async def test_near_rejects_malformed(client):
    for value in ("north|south|1", "42", "91|0|1", "42|-83|1|parsecs", "42|-83|-1"):
        _rejected(await _get(client, {"near": value}))
    _rejected(await _get(client, {"near:missing": "true"}), "not-supported")


# ── _include / _revinclude, across resource types ────────────────────────────


async def test_include_organization_and_partof(client):
    org_id = await create_organization(client, "Acme Health")
    building = await _loc(client, name="Building")
    room = await _loc(
        client, name="Room",
        managingOrganization={"reference": f"Organization/{org_id}"},
        partOf={"reference": f"Location/{building}"},
    )
    bundle = await _search(client, {"_id": str(room), "_include": "Location:organization"})
    assert _typed(bundle) == {("Organization", org_id)}
    inc = next(e for e in bundle["entry"] if e["search"]["mode"] == "include")
    assert inc["fullUrl"] == f"http://test{ORG_BASE}/{org_id}"

    both = await _search(client, [("_id", str(room)), ("_include", "*")])
    assert _typed(both) == {("Organization", org_id), ("Location", building)}

    rev = await _search(client, {"_id": str(building), "_revinclude": "Location:partof"})
    assert _typed(rev) == {("Location", room)}


async def test_organization_revinclude_locations(client):
    org_id = await create_organization(client, "Acme Health")
    loc_id = await _loc(client, managingOrganization={"reference": f"Organization/{org_id}"})
    await _loc(client, name="Unmanaged")
    bundle = await _search(client, {"_id": str(org_id), "_revinclude": "Location:organization"}, base=ORG_BASE)
    assert _ids(bundle) == {org_id}
    assert _typed(bundle) == {("Location", loc_id)}


# ── sort / summary ───────────────────────────────────────────────────────────


async def test_sort_and_summary(client):
    b = await create_location(client, FULL)
    a = await _loc(client, name="Alpha")
    order = [int(e["resource"]["id"]) for e in (await _search(client, {"_sort": "name"}))["entry"]]
    assert order == [a, b]
    summary = (await _search(client, {"_id": str(b), "_summary": "true"}))["entry"][0]["resource"]
    assert "hoursOfOperation" not in summary and "address" not in summary
    assert summary["name"] == FULL["name"] and summary["mode"] == "instance"
    assert any(t["code"] == "SUBSETTED" for t in summary["meta"]["tag"])


async def test_post_search(client):
    loc_id = await _loc(client, name="Riverside Clinic")
    resp = await client.post(
        BASE + "/_search", content="name=river", headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {loc_id}
