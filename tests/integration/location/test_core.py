"""Integration tests for /api/fhir/v1/locations."""

import pytest

from app.auth.dependencies import get_current_user
from app.main import app
from tests.conftest import make_test_user

from .support import (
    BASE,
    FHIR_ACCEPT,
    FULL,
    MINIMAL,
    create_location,
    create_organization,
)

pytestmark = pytest.mark.anyio


# ── Create ─────────────────────────────────────────────────────────────────────


async def test_create_minimal(client):
    resp = await client.post(BASE + "/", json=MINIMAL)
    assert resp.status_code in (200, 201), resp.text
    body = resp.json()
    assert body["name"] == "Main Building"
    assert body["status"] == "active"
    assert body["mode"] == "instance"
    # org_id / created_by come from the token, never the body.
    assert body["org_id"] == "org-test"
    assert body["created_by"] == "u-test"
    assert body["id"] >= 230000


async def test_create_rejects_org_id_in_body(client):
    """org_id is not an accepted input field — extra='forbid' rejects it."""
    resp = await client.post(BASE + "/", json={**MINIMAL, "org_id": "other-org"})
    assert resp.status_code == 422, resp.text


async def test_create_rejects_user_id_in_body(client):
    """Location has no user_id at all, same as Organization."""
    resp = await client.post(BASE + "/", json={**MINIMAL, "user_id": "u-1"})
    assert resp.status_code == 422, resp.text


@pytest.mark.parametrize(
    "missing",
    ["status", "name", "mode", "address_type", "address_city", "address_state",
     "address_postal_code", "address_country"],
)
async def test_create_requires_not_null_fields(client, missing):
    payload = {k: v for k, v in MINIMAL.items() if k != missing}
    resp = await client.post(BASE + "/", json=payload)
    assert resp.status_code == 422, resp.text


async def test_create_full_roundtrips_every_sublist(client):
    loc_id = await create_location(client, FULL)
    body = (await client.get(f"{BASE}/{loc_id}")).json()

    assert len(body["identifier"]) == 1
    assert body["identifier"][0]["value"] == "B1-S.F2"
    assert body["identifier"][0]["assigner_identifier_value"] == "EXTERNAL-1"
    assert body["type"][0]["coding_code"] == "HOSP"
    assert body["alias"][0]["value"] == "South Wing OR"
    assert body["telecom"][0]["value"] == "2328"
    assert body["endpoint"][0]["reference_identifier_value"] == "EP-1"

    # address_line and days_of_week are stored comma-separated and split back
    # out by the mapper — the API surface stays a real list.
    assert body["address_line"] == ["Galapagosweg 91", "Building A"]
    hours = body["hours_of_operation"][0]
    assert hours["days_of_week"] == ["mon", "tue", "wed", "thu", "fri"]
    assert hours["opening_time"] == "09:00:00"
    assert hours["closing_time"] == "17:30:00"
    assert hours["all_day"] is False

    # every sub-resource row exposes its own id, for targeted follow-up
    for key in ("identifier", "type", "alias", "telecom", "hours_of_operation", "endpoint"):
        assert all("id" in row for row in body[key]), key


# ── position ───────────────────────────────────────────────────────────────────


async def test_position_requires_longitude_and_latitude_together(client):
    resp = await client.post(
        BASE + "/", json={**MINIMAL, "position_longitude": "-83.69"}
    )
    assert resp.status_code == 422, resp.text


async def test_position_roundtrips(client):
    loc_id = await create_location(client, FULL)
    body = (await client.get(f"{BASE}/{loc_id}")).json()
    assert float(body["position_longitude"]) == pytest.approx(-83.6945691)
    assert float(body["position_latitude"]) == pytest.approx(42.25475478)


# ── FHIR representation ────────────────────────────────────────────────────────


async def test_fhir_shape(client):
    loc_id = await create_location(client, FULL)
    body = (await client.get(f"{BASE}/{loc_id}", headers=FHIR_ACCEPT)).json()

    assert body["resourceType"] == "Location"
    assert body["id"] == str(loc_id)
    assert body["status"] == "active"
    assert body["mode"] == "instance"
    # operationalStatus is a Coding — no coding[] wrapper, no text sibling.
    assert body["operationalStatus"]["code"] == "U"
    assert "coding" not in body["operationalStatus"]
    # physicalType is a CodeableConcept — it does have coding[].
    assert body["physicalType"]["coding"][0]["code"] == "wi"
    # address is singular (0..1) in R4, unlike Organization's repeating address
    assert isinstance(body["address"], dict)
    assert body["address"]["line"] == ["Galapagosweg 91", "Building A"]
    # alias collapses to bare strings in FHIR
    assert body["alias"] == ["South Wing OR"]
    assert body["hoursOfOperation"][0]["daysOfWeek"] == [
        "mon", "tue", "wed", "thu", "fri"
    ]
    assert body["hoursOfOperation"][0]["openingTime"] == "09:00:00"
    assert body["position"]["longitude"] == pytest.approx(-83.6945691)
    assert body["availabilityExceptions"].startswith("Reduced")


# ── References ─────────────────────────────────────────────────────────────────


async def test_managing_organization_resolves(client):
    org_id = await create_organization(client)
    loc_id = await create_location(
        client, MINIMAL, managing_organization=f"Organization/{org_id}"
    )
    body = (await client.get(f"{BASE}/{loc_id}")).json()
    assert body["managing_organization"] == f"Organization/{org_id}"
    assert body["managing_organization_id"] == org_id

    fhir = (await client.get(f"{BASE}/{loc_id}", headers=FHIR_ACCEPT)).json()
    assert fhir["managingOrganization"]["reference"] == f"Organization/{org_id}"


async def test_managing_organization_unresolvable_rejected(client):
    resp = await client.post(
        BASE + "/", json={**MINIMAL, "managing_organization": "Organization/999999"}
    )
    assert resp.status_code == 422, resp.text


async def test_part_of_resolves(client):
    parent = await create_location(client, MINIMAL)
    child = await create_location(client, MINIMAL, part_of=f"Location/{parent}")
    body = (await client.get(f"{BASE}/{child}")).json()
    assert body["part_of"] == f"Location/{parent}"
    assert body["part_of_id"] == parent


async def test_part_of_unresolvable_rejected(client):
    resp = await client.post(
        BASE + "/", json={**MINIMAL, "part_of": "Location/999999"}
    )
    assert resp.status_code == 422, resp.text


# ── partOf hierarchy cycle check ───────────────────────────────────────────────


async def test_part_of_self_reference_rejected(client):
    loc_id = await create_location(client, MINIMAL)
    resp = await client.patch(
        f"{BASE}/{loc_id}", json={"part_of": f"Location/{loc_id}"}
    )
    assert resp.status_code == 422, resp.text
    assert "circular" in resp.text.lower()


async def test_part_of_direct_cycle_rejected(client):
    a = await create_location(client, MINIMAL)
    b = await create_location(client, MINIMAL, part_of=f"Location/{a}")
    # a is already b's parent; making b a's parent closes the loop.
    resp = await client.patch(f"{BASE}/{a}", json={"part_of": f"Location/{b}"})
    assert resp.status_code == 422, resp.text
    assert "circular" in resp.text.lower()


async def test_part_of_deep_cycle_rejected(client):
    a = await create_location(client, MINIMAL)
    b = await create_location(client, MINIMAL, part_of=f"Location/{a}")
    c = await create_location(client, MINIMAL, part_of=f"Location/{b}")
    # a -> b -> c; pointing a at c would close a three-node loop.
    resp = await client.patch(f"{BASE}/{a}", json={"part_of": f"Location/{c}"})
    assert resp.status_code == 422, resp.text
    assert "circular" in resp.text.lower()


async def test_part_of_sibling_chain_allowed(client):
    """A deep but acyclic chain must NOT be rejected — guards against the
    cycle check being too eager."""
    a = await create_location(client, MINIMAL)
    b = await create_location(client, MINIMAL, part_of=f"Location/{a}")
    c = await create_location(client, MINIMAL)
    resp = await client.patch(f"{BASE}/{c}", json={"part_of": f"Location/{b}"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["part_of"] == f"Location/{b}"


async def test_part_of_can_be_cleared(client):
    parent = await create_location(client, MINIMAL)
    child = await create_location(client, MINIMAL, part_of=f"Location/{parent}")
    resp = await client.patch(f"{BASE}/{child}", json={"part_of": None})
    assert resp.status_code == 200, resp.text
    assert resp.json()["part_of"] is None
    assert resp.json()["part_of_id"] is None


# ── Patch ──────────────────────────────────────────────────────────────────────


async def test_patch_scalar_fields(client):
    loc_id = await create_location(client, MINIMAL)
    resp = await client.patch(
        f"{BASE}/{loc_id}", json={"status": "suspended", "description": "closed"}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "suspended"
    assert body["description"] == "closed"
    assert body["name"] == "Main Building"  # untouched
    assert body["updated_by"] == "u-test"


async def test_patch_replaces_supplied_sublist_only(client):
    loc_id = await create_location(client, FULL)
    resp = await client.patch(
        f"{BASE}/{loc_id}", json={"alias": [{"value": "New Alias"}]}
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert [a["value"] for a in body["alias"]] == ["New Alias"]
    # telecom was not supplied, so it is untouched
    assert len(body["telecom"]) == 1


async def test_patch_empty_list_clears_sublist(client):
    loc_id = await create_location(client, FULL)
    resp = await client.patch(f"{BASE}/{loc_id}", json={"telecom": []})
    assert resp.status_code == 200, resp.text
    assert resp.json()["telecom"] == []
    assert len(resp.json()["alias"]) == 1  # untouched


async def test_patch_address_line_rejoins(client):
    loc_id = await create_location(client, FULL)
    resp = await client.patch(
        f"{BASE}/{loc_id}", json={"address_line": ["One", "Two", "Three"]}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["address_line"] == ["One", "Two", "Three"]


async def test_patch_hours_of_operation_rejoins_days(client):
    loc_id = await create_location(client, FULL)
    resp = await client.patch(
        f"{BASE}/{loc_id}",
        json={"hours_of_operation": [{"days_of_week": ["sat", "sun"], "all_day": True}]},
    )
    assert resp.status_code == 200, resp.text
    hours = resp.json()["hours_of_operation"][0]
    assert hours["days_of_week"] == ["sat", "sun"]
    assert hours["all_day"] is True


async def test_patch_unknown_location_404(client):
    resp = await client.patch(f"{BASE}/999999", json={"name": "x"})
    assert resp.status_code == 404, resp.text


# ── List + filters ─────────────────────────────────────────────────────────────


async def test_list_pagination_envelope(client):
    await create_location(client, MINIMAL)
    resp = await client.get(BASE + "/")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert set(body) == {"total", "limit", "offset", "data"}
    assert body["total"] >= 1


async def test_list_fhir_bundle(client):
    await create_location(client, MINIMAL)
    body = (await client.get(BASE + "/", headers=FHIR_ACCEPT)).json()
    assert body["resourceType"] == "Bundle"
    assert body["type"] == "searchset"
    assert body["entry"][0]["resource"]["resourceType"] == "Location"


async def test_filter_name_matches_name_or_alias(client):
    await create_location(client, MINIMAL, name="Cardiology Ward")
    await create_location(client, MINIMAL, name="Radiology", alias=[{"value": "X-Ray Dept"}])

    by_name = (await client.get(BASE + "/", params={"name": "cardio"})).json()
    assert [d["name"] for d in by_name["data"]] == ["Cardiology Ward"]

    by_alias = (await client.get(BASE + "/", params={"name": "x-ray"})).json()
    assert [d["name"] for d in by_alias["data"]] == ["Radiology"]


async def test_filter_identifier_status_type_physical_type(client):
    await create_location(client, FULL)
    await create_location(client, MINIMAL, name="Other")

    assert (await client.get(BASE + "/", params={"identifier": "B1-S.F2"})).json()["total"] == 1
    assert (await client.get(BASE + "/", params={"type": "HOSP"})).json()["total"] == 1
    assert (await client.get(BASE + "/", params={"physical-type": "wi"})).json()["total"] == 1
    assert (await client.get(BASE + "/", params={"operational-status": "U"})).json()["total"] == 1
    assert (await client.get(BASE + "/", params={"status": "active"})).json()["total"] == 2


async def test_filter_address_fields(client):
    await create_location(client, MINIMAL)
    await create_location(
        client, MINIMAL, name="Elsewhere", address_city="Shelbyville",
        address_state="NY", address_postal_code="10001", address_country="US",
    )

    assert (await client.get(BASE + "/", params={"address-city": "spring"})).json()["total"] == 1
    assert (await client.get(BASE + "/", params={"address-state": "NY"})).json()["total"] == 1
    assert (await client.get(BASE + "/", params={"address-postalcode": "62701"})).json()["total"] == 1
    assert (await client.get(BASE + "/", params={"address-country": "US"})).json()["total"] == 2
    # `address` searches across every sub-field at once
    assert (await client.get(BASE + "/", params={"address": "shelby"})).json()["total"] == 1


async def test_filter_by_organization_and_partof(client):
    org_id = await create_organization(client)
    parent = await create_location(client, MINIMAL)
    child = await create_location(
        client, MINIMAL, part_of=f"Location/{parent}",
        managing_organization=f"Organization/{org_id}",
    )

    by_org = (await client.get(BASE + "/", params={"organization": f"Organization/{org_id}"})).json()
    assert [d["id"] for d in by_org["data"]] == [child]

    by_partof = (await client.get(BASE + "/", params={"partof": f"Location/{parent}"})).json()
    assert [d["id"] for d in by_partof["data"]] == [child]


async def test_sort_and_total_mode(client):
    await create_location(client, MINIMAL, name="AAA")
    await create_location(client, MINIMAL, name="ZZZ")

    asc = (await client.get(BASE + "/", params={"sort": "name"})).json()
    assert [d["name"] for d in asc["data"]] == ["AAA", "ZZZ"]

    desc = (await client.get(BASE + "/", params={"sort": "-name"})).json()
    assert [d["name"] for d in desc["data"]] == ["ZZZ", "AAA"]

    none = (await client.get(BASE + "/", params={"total_mode": "none"})).json()
    assert none["total"] is None


async def _seed_near_fixtures(client):
    """Ann Arbor and Detroit are ~57.7 km apart; the third location has no
    position at all and must never match a `near` query."""
    ann_arbor = await create_location(
        client, MINIMAL, name="Ann Arbor",
        position_latitude="42.28083", position_longitude="-83.74303",
    )
    detroit = await create_location(
        client, MINIMAL, name="Detroit",
        position_latitude="42.33143", position_longitude="-83.04575",
    )
    no_position = await create_location(client, MINIMAL, name="No Position")
    return ann_arbor, detroit, no_position


async def test_near_radius_filters_by_distance(client):
    await _seed_near_fixtures(client)

    async def names(near):
        resp = await client.get(BASE + "/", params={"near": near})
        assert resp.status_code == 200, resp.text
        return sorted(d["name"] for d in resp.json()["data"])

    # 1 km around Ann Arbor: only Ann Arbor.
    assert await names("42.28083|-83.74303|1|km") == ["Ann Arbor"]
    # 100 km reaches Detroit as well.
    assert await names("42.28083|-83.74303|100|km") == ["Ann Arbor", "Detroit"]
    # 30 mi is 48.3 km — still short of Detroit's ~57.7 km.
    assert await names("42.28083|-83.74303|30|mi") == ["Ann Arbor"]
    # 40 mi is 64.4 km — now it reaches.
    assert await names("42.28083|-83.74303|40|mi") == ["Ann Arbor", "Detroit"]
    # Units are optional and default to km.
    assert await names("42.28083|-83.74303|1") == ["Ann Arbor"]


async def test_near_excludes_locations_without_position(client):
    await _seed_near_fixtures(client)
    resp = await client.get(BASE + "/", params={"near": "42.28083|-83.74303|20000|km"})
    names = sorted(d["name"] for d in resp.json()["data"])
    # A radius that spans the planet still must not pull in the positionless row.
    assert names == ["Ann Arbor", "Detroit"]


async def test_near_rejects_out_of_range_coordinates(client):
    resp = await client.get(BASE + "/", params={"near": "999|-83.0|10|km"})
    assert resp.status_code == 422, resp.text


async def test_near_rejects_malformed_value(client):
    resp = await client.get(BASE + "/", params={"near": "not-a-position"})
    assert resp.status_code == 422, resp.text


async def test_near_rejects_unknown_unit(client):
    resp = await client.get(BASE + "/", params={"near": "42.0|-83.0|10|parsecs"})
    assert resp.status_code == 422, resp.text


# ── Delete ─────────────────────────────────────────────────────────────────────


async def test_delete_cascades(client):
    loc_id = await create_location(client, FULL)
    resp = await client.delete(f"{BASE}/{loc_id}")
    assert resp.status_code == 204, resp.text
    assert (await client.get(f"{BASE}/{loc_id}")).status_code == 404


async def test_delete_unknown_404(client):
    assert (await client.delete(f"{BASE}/999999")).status_code == 404


# ── Auth / tenancy ─────────────────────────────────────────────────────────────


async def test_other_org_cannot_read_update_or_delete(client):
    loc_id = await create_location(client, MINIMAL)

    app.dependency_overrides[get_current_user] = make_test_user(
        sub="u-other",
        org_id="org-other",
        permissions=[
            "location:create", "location:read", "location:update", "location:delete"
        ],
    )
    try:
        # 404 rather than 403 — never leak that the id exists in another org.
        assert (await client.get(f"{BASE}/{loc_id}")).status_code == 404
        assert (await client.patch(f"{BASE}/{loc_id}", json={"name": "x"})).status_code == 404
        assert (await client.delete(f"{BASE}/{loc_id}")).status_code == 404
        # and it is absent from that org's list
        assert (await client.get(BASE + "/")).json()["total"] == 0
    finally:
        app.dependency_overrides[get_current_user] = make_test_user()


async def test_org_less_token_rejected(client):
    await create_location(client, MINIMAL)
    app.dependency_overrides[get_current_user] = make_test_user(
        org_id=None,
        permissions=["location:create", "location:read"],
    )
    try:
        assert (await client.get(BASE + "/")).status_code == 403
        assert (await client.post(BASE + "/", json=MINIMAL)).status_code == 403
    finally:
        app.dependency_overrides[get_current_user] = make_test_user()


@pytest.mark.parametrize(
    "method,path,body",
    [
        ("post", "/", MINIMAL),
        ("get", "/", None),
        ("patch", "/230000", {"name": "x"}),
        ("delete", "/230000", None),
    ],
)
async def test_missing_permission_denied(client, method, path, body):
    app.dependency_overrides[get_current_user] = make_test_user(permissions=[])
    try:
        kwargs = {"json": body} if body is not None else {}
        resp = await getattr(client, method)(BASE + path, **kwargs)
        assert resp.status_code == 403, resp.text
    finally:
        app.dependency_overrides[get_current_user] = make_test_user()
