"""FHIR R4 search over Endpoint (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/endpoint.html#search).

One block per search parameter, then chaining, `_include` / `_revinclude`
(in both directions — Endpoint <-> Organization / Location / HealthcareService),
the result parameters (`_sort`, `_count`/`_offset`/`_total`,
`_summary`/`_elements`), combination rules, lenient vs strict handling, the
Bundle shape and POST _search.
"""

import pytest

from tests.integration.endpoint.support import (
    BASE,
    CONN,
    EP_IDS,
    MINIMAL,
    ORG_BASE,
    PAYLOAD,
    create_endpoint,
    create_organization,
)

LOC_BASE = "/api/fhir/v1/locations"
HS_BASE = "/api/fhir/v1/healthcare-services"


def _endpoint(**changes) -> dict:
    return {**MINIMAL, **changes}


@pytest.fixture
async def world(client):
    """Two organizations and four endpoints with distinct, searchable values.
    Returns {key: public id}."""
    w = {}
    w["org_a"] = await create_organization(client, "Alpha Health")
    w["org_b"] = await create_organization(client, "Beta Clinics")
    w["rest"] = await create_endpoint(
        client,
        _endpoint(
            name="Alpha FHIR API",
            status="active",
            managingOrganization={"reference": f"Organization/{w['org_a']}"},
            identifier=[
                {
                    "system": EP_IDS,
                    "value": "EP-1",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "EPT",
                            }
                        ],
                        "text": "Endpoint number",
                    },
                }
            ],
            connectionType={
                "system": CONN,
                "code": "hl7-fhir-rest",
                "display": "HL7 FHIR",
            },
            payloadType=[
                {
                    "coding": [{"system": PAYLOAD, "code": "any", "display": "Any"}],
                    "text": "Any payload",
                }
            ],
        ),
    )
    w["dicom"] = await create_endpoint(
        client,
        _endpoint(
            name="Beta Imaging Müller",
            status="suspended",
            managingOrganization={"reference": f"Organization/{w['org_b']}"},
            identifier=[{"system": EP_IDS, "value": "EP-2"}],
            connectionType={
                "system": CONN,
                "code": "dicom-wado-rs",
                "display": "DICOM WADO-RS",
            },
            payloadType=[
                {"coding": [{"system": PAYLOAD, "code": "ccda"}]},
                {"coding": [{"system": PAYLOAD, "code": "any"}]},
            ],
        ),
    )
    w["off"] = await create_endpoint(
        client,
        _endpoint(
            name="Retired Gateway",
            status="off",
            connectionType={"system": "urn:other", "code": "hl7-fhir-rest"},
            payloadType=[{"text": "Legacy only"}],
        ),
    )
    w["bare"] = await create_endpoint(
        client,
        _endpoint(
            status="test",
            connectionType={"code": "x"},
            payloadType=[{"coding": [{"code": "zzz"}]}],
        ),
    )
    return w


KEYS = ("rest", "dicom", "off", "bare")
ALL = set(KEYS)


async def _search(client, params=None, headers=None, base=BASE) -> dict:
    resp = await client.get(base + "/", params=params or {}, headers=headers or {})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _matches(bundle: dict) -> list[dict]:
    return [
        e["resource"]
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == "match"
    ]


def _ids(bundle: dict) -> set[int]:
    return {int(r["id"]) for r in _matches(bundle)}


def _included(bundle: dict) -> set[tuple[str, str]]:
    return {
        (e["resource"]["resourceType"], e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == "include"
    }


async def _found(client, w, **params) -> set[str]:
    by_id = {w[k]: k for k in KEYS}
    return {by_id[i] for i in _ids(await _search(client, params))}


# ── _id / _lastUpdated ───────────────────────────────────────────────────────


async def test_id(client, world):
    assert await _found(client, world, _id=str(world["dicom"])) == {"dicom"}
    assert await _found(client, world, _id="999999") == set()
    assert await _found(client, world, _id=f"{world['dicom']},{world['bare']}") == {
        "dicom",
        "bare",
    }
    assert await _found(client, world, **{"_id:not": str(world["dicom"])}) == ALL - {
        "dicom"
    }


async def test_last_updated(client, world):
    assert await _found(client, world, _lastUpdated="ge2000-01-01") == ALL
    assert await _found(client, world, _lastUpdated="lt2000-01-01") == set()


# ── status ───────────────────────────────────────────────────────────────────


async def test_status(client, world):
    assert await _found(client, world, status="active") == {"rest"}
    assert await _found(client, world, status="suspended") == {"dicom"}
    assert await _found(
        client, world, status="http://hl7.org/fhir/endpoint-status|off"
    ) == {"off"}
    assert await _found(client, world, status="active,suspended") == {"rest", "dicom"}
    assert await _found(client, world, **{"status:not": "active"}) == ALL - {"rest"}
    assert await _found(client, world, status="nonsense") == set()
    assert await _found(client, world, status="urn:other|active") == set()
    assert await _found(client, world, status="|active") == set()


async def test_status_entered_in_error_is_stored_and_found(client, world):
    ep = await create_endpoint(client, _endpoint(status="entered-in-error"))
    assert ep in _ids(await _search(client, {"status": "entered-in-error"}))


# ── name ─────────────────────────────────────────────────────────────────────


async def test_name_is_case_and_accent_insensitive_starts_with(client, world):
    assert await _found(client, world, name="alpha") == {"rest"}
    assert await _found(client, world, name="BETA IMAGING") == {"dicom"}
    assert await _found(client, world, name="beta imaging muller") == {
        "dicom"
    }  # ü -> u
    assert await _found(client, world, name="fhir") == set()  # not a prefix


async def test_name_modifiers(client, world):
    assert await _found(client, world, **{"name:contains": "fhir"}) == {"rest"}
    assert await _found(client, world, **{"name:exact": "Retired Gateway"}) == {"off"}
    assert await _found(client, world, **{"name:exact": "retired gateway"}) == set()
    assert await _found(client, world, **{"name:missing": "true"}) == {"bare"}
    assert await _found(client, world, **{"name:missing": "false"}) == ALL - {"bare"}


# ── identifier ───────────────────────────────────────────────────────────────


async def test_identifier(client, world):
    assert await _found(client, world, identifier="EP-1") == {"rest"}
    assert await _found(client, world, identifier=f"{EP_IDS}|EP-2") == {"dicom"}
    assert await _found(client, world, identifier=f"{EP_IDS}|") == {"rest", "dicom"}
    assert await _found(client, world, identifier="|EP-1") == set()
    assert await _found(
        client, world, **{"identifier:not": f"{EP_IDS}|EP-1"}
    ) == ALL - {"rest"}
    assert await _found(client, world, **{"identifier:missing": "true"}) == {
        "off",
        "bare",
    }


async def test_identifier_of_type_and_text(client, world):
    v2 = "http://terminology.hl7.org/CodeSystem/v2-0203"
    assert await _found(client, world, **{"identifier:of-type": f"{v2}|EPT|EP-1"}) == {
        "rest"
    }
    assert (
        await _found(client, world, **{"identifier:of-type": f"{v2}|EPT|EP-2"}) == set()
    )
    assert await _found(client, world, **{"identifier:text": "Endpoint num"}) == {
        "rest"
    }


# ── connection-type (one Coding on the row) ──────────────────────────────────


async def test_connection_type(client, world):
    assert await _found(client, world, **{"connection-type": "hl7-fhir-rest"}) == {
        "rest",
        "off",
    }
    assert await _found(
        client, world, **{"connection-type": f"{CONN}|hl7-fhir-rest"}
    ) == {"rest"}
    assert await _found(client, world, **{"connection-type": f"{CONN}|"}) == {
        "rest",
        "dicom",
    }
    assert await _found(client, world, **{"connection-type": "|hl7-fhir-rest"}) == set()
    assert await _found(
        client, world, **{"connection-type": "hl7-fhir-rest,dicom-wado-rs"}
    ) == {"rest", "dicom", "off"}
    assert await _found(client, world, **{"connection-type": "nope"}) == set()
    assert await _found(client, world, **{"connection-type:not": "hl7-fhir-rest"}) == {
        "dicom",
        "bare",
    }


async def test_connection_type_text_and_missing(client, world):
    assert await _found(client, world, **{"connection-type:text": "DICOM"}) == {
        "dicom"
    }  # coding.display
    assert await _found(client, world, **{"connection-type:text": "HL7"}) == {"rest"}
    assert await _found(client, world, **{"connection-type:missing": "false"}) == ALL


# ── payload-type (1..*, a row per coding) ────────────────────────────────────


async def test_payload_type(client, world):
    assert await _found(client, world, **{"payload-type": "any"}) == {"rest", "dicom"}
    assert await _found(client, world, **{"payload-type": f"{PAYLOAD}|ccda"}) == {
        "dicom"
    }
    assert await _found(client, world, **{"payload-type": "ccda,any"}) == {
        "rest",
        "dicom",
    }
    assert await _found(client, world, **{"payload-type": "|any"}) == set()
    assert await _found(client, world, **{"payload-type:not": "any"}) == ALL - {
        "rest",
        "dicom",
    }


async def test_payload_type_text(client, world):
    assert await _found(client, world, **{"payload-type:text": "Any pay"}) == {
        "rest"
    }  # concept text
    assert await _found(client, world, **{"payload-type:text": "Legacy"}) == {
        "off"
    }  # text-only concept
    assert await _found(client, world, **{"payload-type:text": "Any"}) == {
        "rest"
    }  # coding display "Any" / text "Any payload"


# ── organization (managingOrganization) ──────────────────────────────────────


async def test_organization_reference_forms(client, world):
    a, b = world["org_a"], world["org_b"]
    assert await _found(client, world, organization=f"Organization/{a}") == {"rest"}
    assert await _found(client, world, organization=str(b)) == {"dicom"}
    assert await _found(client, world, **{"organization:Organization": str(a)}) == {
        "rest"
    }
    assert await _found(client, world, organization=f"{a},{b}") == {"rest", "dicom"}
    assert await _found(client, world, organization="Location/1") == set()  # wrong type
    assert (
        await client.get(BASE + "/", params={"organization:Location": str(a)})
    ).status_code == 400
    assert await _found(client, world, **{"organization:missing": "true"}) == {
        "off",
        "bare",
    }


async def test_organization_absolute_url_resolves_only_for_this_server(client, world):
    self_link = next(
        link["url"]
        for link in (await _search(client))["link"]
        if link["relation"] == "self"
    )
    fhir_base = self_link.split("/endpoints")[0]
    assert await _found(
        client, world, organization=f"{fhir_base}/Organization/{world['org_a']}"
    ) == {"rest"}
    other = f"https://other.example.org/fhir/Organization/{world['org_a']}"
    assert await _found(client, world, organization=other) == set()


async def test_organization_identifier_modifier(client, world):
    ep = await create_endpoint(
        client,
        _endpoint(
            managingOrganization={
                "identifier": {"system": "urn:registry", "value": "ORG-9"}
            }
        ),
    )
    assert _ids(
        await _search(client, {"organization:identifier": "urn:registry|ORG-9"})
    ) == {ep}


async def test_organization_chaining(client, world):
    assert await _found(client, world, **{"organization.name": "Alpha"}) == {"rest"}
    assert await _found(client, world, **{"organization.name": "Beta"}) == {"dicom"}
    assert await _found(client, world, **{"organization.name": "Nope"}) == set()


# ── combination rules ────────────────────────────────────────────────────────


async def test_comma_is_or_repeat_is_and_and_parameters_and_together(client, world):
    assert await _found(client, world, name="Alpha,Retired") == {"rest", "off"}
    resp = await client.get(
        BASE + "/", params=[("payload-type", "ccda"), ("payload-type", "any")]
    )
    assert _ids(resp.json()) == {world["dicom"]}  # only one endpoint has both codings
    assert await _found(client, world, status="active", **{"payload-type": "any"}) == {
        "rest"
    }
    assert await _found(client, world, status="off", **{"payload-type": "any"}) == set()


async def test_escaped_comma_is_literal(client, world):
    assert await _found(client, world, name="Alpha\\,Retired") == set()


# ── _include / _revinclude ───────────────────────────────────────────────────


async def test_include_organization(client, world):
    bundle = await _search(
        client, {"_id": str(world["rest"]), "_include": "Endpoint:organization"}
    )
    assert _ids(bundle) == {world["rest"]}
    assert _included(bundle) == {("Organization", str(world["org_a"]))}


async def test_include_dedups_and_skips_unresolved(client, world):
    bundle = await _search(client, {"_include": "Endpoint:organization"})
    assert _included(bundle) == {
        ("Organization", str(world["org_a"])),
        ("Organization", str(world["org_b"])),
    }


async def test_unsupported_include_is_400(client, world):
    for value in ("Endpoint:bogus", "Patient:organization", "Endpoint"):
        assert (
            await client.get(BASE + "/", params={"_include": value})
        ).status_code == 400, value


async def test_revinclude_organizations_that_point_at_the_endpoint(client, world):
    org = (
        await client.post(
            ORG_BASE + "/",
            json={
                "name": "Via Endpoint",
                "endpoint": [{"reference": f"Endpoint/{world['rest']}"}],
            },
        )
    ).json()["id"]
    bundle = await _search(
        client, {"_id": str(world["rest"]), "_revinclude": "Organization:endpoint"}
    )
    assert _included(bundle) == {("Organization", org)}
    none = await _search(
        client, {"_id": str(world["dicom"]), "_revinclude": "Organization:endpoint"}
    )
    assert _included(none) == set()


async def test_organization_search_can_include_its_endpoints_and_revinclude_the_ones_it_manages(
    client, world
):
    org = (
        await client.post(
            ORG_BASE + "/",
            json={
                "name": "Pointer Org",
                "endpoint": [{"reference": f"Endpoint/{world['off']}"}],
            },
        )
    ).json()["id"]
    inc = await _search(
        client, {"_id": org, "_include": "Organization:endpoint"}, base=ORG_BASE
    )
    assert _included(inc) == {("Endpoint", str(world["off"]))}
    rev = await _search(
        client,
        {"_id": str(world["org_a"]), "_revinclude": "Endpoint:organization"},
        base=ORG_BASE,
    )
    assert _included(rev) == {("Endpoint", str(world["rest"]))}
    entry = next(e for e in rev["entry"] if e["search"]["mode"] == "include")
    assert entry["fullUrl"].endswith(f"/endpoints/{world['rest']}")


async def test_healthcare_service_and_location_endpoint_includes(client, world):
    hs = (
        await client.post(
            HS_BASE + "/",
            json={
                "name": "Clinic",
                "endpoint": [{"reference": f"Endpoint/{world['dicom']}"}],
            },
        )
    ).json()["id"]
    loc = (
        await client.post(
            LOC_BASE + "/",
            json={
                "status": "active",
                "name": "Wing",
                "endpoint": [{"reference": f"Endpoint/{world['dicom']}"}],
            },
        )
    ).json()["id"]
    hs_inc = await _search(
        client, {"_id": hs, "_include": "HealthcareService:endpoint"}, base=HS_BASE
    )
    assert _included(hs_inc) == {("Endpoint", str(world["dicom"]))}
    loc_inc = await _search(
        client, {"_id": loc, "_include": "Location:endpoint"}, base=LOC_BASE
    )
    assert _included(loc_inc) == {("Endpoint", str(world["dicom"]))}
    rev = await _search(
        client,
        {
            "_id": str(world["dicom"]),
            "_revinclude": ["HealthcareService:endpoint", "Location:endpoint"],
        },
    )
    assert _included(rev) == {("HealthcareService", hs), ("Location", loc)}
    assert (
        _included(
            await _search(
                client, {"_id": str(world["rest"]), "_revinclude": "Location:endpoint"}
            )
        )
        == set()
    )


# ── _sort / paging / totals ──────────────────────────────────────────────────


async def test_sort_by_name_and_id(client, world):
    asc = [r["id"] for r in _matches(await _search(client, {"_sort": "name"}))]
    assert asc[:3] == [
        str(world[k]) for k in ("rest", "dicom", "off")
    ]  # Alpha, Beta, Retired
    assert asc[-1] == str(world["bare"])  # no name sorts last
    assert [r["id"] for r in _matches(await _search(client, {"_sort": "-name"}))][
        0
    ] == str(world["off"])
    default = [int(r["id"]) for r in _matches(await _search(client))]
    assert default == sorted(default, reverse=True)
    assert [
        int(r["id"]) for r in _matches(await _search(client, {"_sort": "_id"}))
    ] == sorted(default)


async def test_sort_by_status_and_connection_type(client, world):
    assert (await client.get(BASE + "/", params={"_sort": "status"})).status_code == 200
    assert (
        await client.get(BASE + "/", params={"_sort": "connection-type"})
    ).status_code == 200
    assert (
        await client.get(BASE + "/", params={"_sort": "payload-type"})
    ).status_code == 200


async def test_count_offset_total_and_links(client, world):
    page1 = await _search(client, {"_count": "2", "_sort": "_id"})
    assert page1["total"] == 4 and len(page1["entry"]) == 2
    assert {"self", "first", "next", "last"} <= {
        link["relation"] for link in page1["link"]
    }
    page2 = await _search(client, {"_count": "2", "_offset": "2", "_sort": "_id"})
    assert _ids(page1).isdisjoint(_ids(page2))
    assert "next" not in {link["relation"] for link in page2["link"]}
    only = await _search(client, {"_count": "0"})
    assert only["total"] == 4 and "entry" not in only
    assert "total" not in await _search(client, {"_total": "none"})


async def test_summary_and_elements(client, world):
    from tests.integration.endpoint.support import FULL

    full = str(
        await create_endpoint(client, {**FULL, "name": "Subsettable"})
    )  # has contact + header
    resource = _matches(await _search(client, {"_id": full, "_summary": "true"}))[0]
    assert (
        "name" in resource
        and "address" in resource
        and "contact" not in resource
        and "header" not in resource
    )
    assert any(t.get("code") == "SUBSETTED" for t in resource["meta"]["tag"])
    el = _matches(await _search(client, {"_id": full, "_elements": "name"}))[0]
    assert el["name"] == "Subsettable" and "header" not in el and "contact" not in el
    # _summary=text / _elements keep the elements R4 makes mandatory (min cardinality 1).
    assert {"status", "connectionType", "payloadType", "address"} <= set(el)
    text = _matches(await _search(client, {"_id": full, "_summary": "text"}))[0]
    assert {"status", "connectionType", "payloadType", "address"} <= set(text)
    assert "name" not in text
    # Nothing to strip -> not tagged as subsetted.
    plain = _matches(
        await _search(client, {"_id": str(world["rest"]), "_summary": "true"})
    )[0]
    assert not any(t.get("code") == "SUBSETTED" for t in plain["meta"].get("tag", []))


# ── lenient / strict handling, rejected input ────────────────────────────────


async def test_unknown_parameter_ignored_with_outcome_or_400_when_strict(client, world):
    bundle = await _search(client, {"bogus": "x", "name": "Alpha"})
    assert _ids(bundle) == {world["rest"]}
    assert [e for e in bundle["entry"] if e["search"]["mode"] == "outcome"]
    resp = await client.get(
        BASE + "/", params={"bogus": "x"}, headers={"Prefer": "handling=strict"}
    )
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"


async def test_unsupported_common_parameters_ignored(client, world):
    for name in ("_tag", "_profile", "_has", "_text", "_filter"):
        assert (await client.get(BASE + "/", params={name: "x"})).status_code == 200, (
            name
        )


async def test_bad_modifier_and_malformed_value_are_400(client, world):
    for params in (
        {"name:bogus": "x"},
        {"status:contains": "x"},
        {"status:text": "x"},
        {"organization:not": "1"},
        {"organization:above": "1"},
        {"_lastUpdated": "notadate"},
        {"_count": "abc"},
        {"_query": "x"},
        {"status.name": "x"},  # token parameters can't be chained
    ):
        assert (await client.get(BASE + "/", params=params)).status_code == 400, params


# ── Bundle shape / POST _search ──────────────────────────────────────────────


async def test_bundle_shape(client, world):
    bundle = await _search(client, {"name": "Alpha"})
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/endpoints/{world['rest']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "Endpoint"


async def test_xml_only_accept_is_406_on_search(client):
    assert (
        await client.get(BASE + "/", headers={"Accept": "application/fhir+xml"})
    ).status_code == 406


async def test_post_search_form_encoded_and_combined_with_query_string(client, world):
    form = {"Content-Type": "application/x-www-form-urlencoded"}
    resp = await client.post(
        BASE + "/_search", content="name=Alpha&status=active", headers=form
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["rest"]}
    resp = await client.post(
        BASE + "/_search?status=active", content="name=Alpha", headers=form
    )
    assert _ids(resp.json()) == {world["rest"]}
    resp = await client.post(
        BASE + "/_search?status=off", content="name=Alpha", headers=form
    )
    assert _ids(resp.json()) == set()
