"""FHIR R4 search over Organization (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/organization.html#search).

One block per search parameter type and per result parameter: default
matching, every supported modifier, OR (comma) / AND (repeat), escaping,
`_id`/`_lastUpdated`, `_sort`/`_count`/`_offset`/`_total`, `_summary`/
`_elements`, `_include`/`_revinclude`, chaining, lenient/strict handling,
rejected modifiers, the Bundle's links/fullUrl/search.mode and POST _search.
"""

from datetime import UTC, datetime, timedelta

from app.models.terminology.terminology import (
    TerminologyCodeSystem,
    TerminologyConcept,
    TerminologyRelationship,
    TerminologyValueSet,
    TerminologyValueSetConcept,
)
from tests.integration.organization.support import BASE, FULL, MINIMAL, create_organization

ORG_TYPE = "http://terminology.hl7.org/CodeSystem/organization-type"
NPI = "http://hl7.org/fhir/sid/us-npi"


async def _get(client, params, headers=None):
    return await client.get(BASE + "/", params=params, headers=headers or {})


async def _search(client, params=None, headers=None) -> dict:
    resp = await _get(client, params or {}, headers)
    assert resp.status_code == 200, resp.text
    assert "application/fhir+json" in resp.headers["content-type"]
    return resp.json()


def _ids(bundle: dict, mode: str = "match") -> set[int]:
    return {
        int(e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == mode
    }


def _order(bundle: dict) -> list[int]:
    return [int(e["resource"]["id"]) for e in bundle.get("entry") or [] if e["search"]["mode"] == "match"]


async def _ids_for(client, params) -> set[int]:
    return _ids(await _search(client, params))


def _link(bundle: dict, relation: str) -> str | None:
    return next((l["url"] for l in bundle["link"] if l["relation"] == relation), None)


async def _org(client, **fields) -> int:
    return await create_organization(client, {**MINIMAL, **fields})


def _rejected(resp, code="invalid"):
    assert resp.status_code == 400, resp.text
    body = resp.json()
    assert body["resourceType"] == "OperationOutcome"
    assert body["issue"][0]["code"] == code, body


# ── Bundle shape ─────────────────────────────────────────────────────────────


async def test_searchset_bundle_shape(client):
    org_id = await _org(client)
    bundle = await _search(client)
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "searchset"
    assert bundle["total"] == 1
    entry = bundle["entry"][0]
    assert entry["fullUrl"] == f"http://test{BASE}/{org_id}"
    assert entry["search"] == {"mode": "match"}
    assert {l["relation"] for l in bundle["link"]} == {"self", "first", "last"}
    assert _link(bundle, "self").startswith(f"http://test{BASE}/?")


async def test_empty_result_has_no_entry_array(client):
    bundle = await _search(client, {"name": "nothing-matches"})
    assert bundle["total"] == 0
    assert "entry" not in bundle  # FHIR JSON forbids empty arrays


# ── string: name (name | alias) ──────────────────────────────────────────────


async def test_string_default_is_starts_with(client):
    org_id = await _org(client, name="Riverside Clinic")
    assert await _ids_for(client, {"name": "river"}) == {org_id}
    assert await _ids_for(client, {"name": "Riverside Clinic"}) == {org_id}
    assert await _ids_for(client, {"name": "clinic"}) == set()  # not a prefix


async def test_string_is_case_and_accent_insensitive(client):
    org_id = await _org(client, name="Hôpital Général")
    assert await _ids_for(client, {"name": "hopital"}) == {org_id}
    assert await _ids_for(client, {"name": "HÔPITAL GEN"}) == {org_id}


async def test_string_contains(client):
    org_id = await _org(client, name="Riverside Clinic")
    assert await _ids_for(client, {"name:contains": "side cli"}) == {org_id}
    assert await _ids_for(client, {"name:contains": "SIDE"}) == {org_id}


async def test_string_exact_is_case_and_accent_sensitive(client):
    org_id = await _org(client, name="Hôpital Général")
    assert await _ids_for(client, {"name:exact": "Hôpital Général"}) == {org_id}
    assert await _ids_for(client, {"name:exact": "hôpital général"}) == set()
    assert await _ids_for(client, {"name:exact": "Hopital General"}) == set()
    assert await _ids_for(client, {"name:exact": "Hôpital"}) == set()


async def test_name_matches_alias_array(client):
    by_name = await _org(client, name="Riverside Clinic")
    by_alias = await _org(client, name="Unrelated", alias=["Old Name", "Riverside Annex"])
    assert await _ids_for(client, {"name": "riverside"}) == {by_name, by_alias}
    assert await _ids_for(client, {"name:contains": "annex"}) == {by_alias}
    assert await _ids_for(client, {"name:exact": "Riverside Annex"}) == {by_alias}
    assert await _ids_for(client, {"name": "annex"}) == set()


async def test_string_missing(client):
    named = await _org(client, name="Named")
    unnamed = await create_organization(client, {"active": True, "alias": ["Only Alias"]})
    nothing = await create_organization(
        client, {"active": True, "identifier": [{"value": "x"}]}
    )
    assert await _ids_for(client, {"name:missing": "true"}) == {nothing}
    assert await _ids_for(client, {"name:missing": "false"}) == {named, unnamed}


async def test_comma_is_or_and_repeat_is_and(client):
    a = await _org(client, name="Alpha Health")
    b = await _org(client, name="Beta Health")
    await _org(client, name="Gamma Health")
    assert await _ids_for(client, {"name": "alpha,beta"}) == {a, b}
    both = await _search(client, [("name", "alpha,beta"), ("name", "alpha h")])
    assert _ids(both) == {a}


async def test_escaped_comma_is_literal(client):
    org_id = await _org(client, name="Smith, Jones & Partners")
    assert await _ids_for(client, {"name": "smith\\, jones"}) == {org_id}
    # Escaped, "nobody\,smith" is the one literal value "nobody,smith".
    assert await _ids_for(client, {"name": "nobody\\,smith"}) == set()


async def test_like_wildcards_are_literal(client):
    await _org(client, name="Anything")
    assert await _ids_for(client, {"name": "%"}) == set()
    assert await _ids_for(client, {"name": "_"}) == set()


# ── string: phonetic ─────────────────────────────────────────────────────────


async def test_phonetic(client):
    org_id = await _org(client, name="General Hospital")
    await _org(client, name="Totally Different")
    assert await _ids_for(client, {"phonetic": "Generel Hospitel"}) == {org_id}
    assert await _ids_for(client, {"phonetic": "Hospital"}) == {org_id}
    assert await _ids_for(client, {"phonetic": "Clinic"}) == set()


async def test_phonetic_rejects_exact_and_contains(client):
    _rejected(await _get(client, {"phonetic:exact": "x"}), "not-supported")
    _rejected(await _get(client, {"phonetic:contains": "x"}), "not-supported")


# ── string: address, address-* ───────────────────────────────────────────────


async def test_address_matches_start_of_any_part(client):
    org_id = await _org(
        client,
        address=[{"line": ["Suite 5", "123 Main St"], "city": "Springfield", "district": "Greene",
                  "state": "Illinois", "postalCode": "62701", "country": "USA", "text": "Main campus"}],
    )
    for value in ("suite", "123 main", "spring", "greene", "illi", "627", "us", "main campus"):
        assert await _ids_for(client, {"address": value}) == {org_id}, value
    assert await _ids_for(client, {"address": "field"}) == set()
    assert await _ids_for(client, {"address:contains": "field"}) == {org_id}
    assert await _ids_for(client, {"address:exact": "123 Main St"}) == {org_id}
    assert await _ids_for(client, {"address:exact": "123 main st"}) == set()


async def test_address_parts(client):
    org_id = await create_organization(client, FULL)
    assert await _ids_for(client, {"address-city": "any"}) == {org_id}
    assert await _ids_for(client, {"address-state": "ca"}) == {org_id}
    assert await _ids_for(client, {"address-postalcode": "123"}) == {org_id}
    assert await _ids_for(client, {"address-country": "us"}) == {org_id}
    assert await _ids_for(client, {"address-city:exact": "Anytown"}) == {org_id}
    assert await _ids_for(client, {"address-city:exact": "anytown"}) == set()
    assert await _ids_for(client, {"address-city:contains": "town"}) == {org_id}
    assert await _ids_for(client, {"address-city": "town"}) == set()


async def test_address_part_missing(client):
    with_city = await create_organization(client, FULL)
    no_address = await _org(client)
    no_city = await _org(client, address=[{"country": "US"}])
    assert await _ids_for(client, {"address-city:missing": "true"}) == {no_address, no_city}
    assert await _ids_for(client, {"address-city:missing": "false"}) == {with_city}
    assert await _ids_for(client, {"address:missing": "true"}) == {no_address}


async def test_address_does_not_match_contact_address(client):
    org_id = await _org(client, contact=[{"address": {"city": "Contactville"}}])
    assert org_id not in await _ids_for(client, {"address-city": "Contactville"})


# ── token ────────────────────────────────────────────────────────────────────


async def test_active_token(client):
    on = await _org(client, name="On", active=True)
    off = await _org(client, name="Off", active=False)
    unknown = await create_organization(client, {"name": "Unknown"})
    assert await _ids_for(client, {"active": "true"}) == {on}
    assert await _ids_for(client, {"active": "false"}) == {off}
    assert await _ids_for(client, {"active:not": "true"}) == {off, unknown}
    assert await _ids_for(client, {"active:missing": "true"}) == {unknown}
    _rejected(await _get(client, {"active": "yes"}))


async def test_address_use_token(client):
    org_id = await create_organization(client, FULL)  # use=work
    other = await _org(client, address=[{"use": "billing", "city": "X"}])
    assert await _ids_for(client, {"address-use": "work"}) == {org_id}
    assert await _ids_for(client, {"address-use": "http://hl7.org/fhir/address-use|work"}) == {org_id}
    assert await _ids_for(client, {"address-use": "urn:other|work"}) == set()
    assert await _ids_for(client, {"address-use": "bogus"}) == set()
    assert await _ids_for(client, {"address-use:not": "work"}) == {other}


async def test_identifier_token_forms(client):
    org_id = await create_organization(client, FULL)
    other = await _org(client, identifier=[{"value": "1234567893"}])
    assert await _ids_for(client, {"identifier": "1234567893"}) == {org_id, other}
    assert await _ids_for(client, {"identifier": f"{NPI}|1234567893"}) == {org_id}
    assert await _ids_for(client, {"identifier": "|1234567893"}) == {other}
    assert await _ids_for(client, {"identifier": f"{NPI}|"}) == {org_id}
    assert await _ids_for(client, {"identifier": "urn:other|1234567893"}) == set()
    assert await _ids_for(client, {"identifier": "123456789"}) == set()  # tokens match whole codes


async def test_identifier_not_and_missing(client):
    org_id = await create_organization(client, FULL)
    other = await _org(client, identifier=[{"value": "A-1"}])
    bare = await _org(client)
    assert await _ids_for(client, {"identifier:not": f"{NPI}|1234567893"}) == {other, bare}
    assert await _ids_for(client, {"identifier:missing": "true"}) == {bare}
    assert await _ids_for(client, {"identifier:missing": "false"}) == {org_id, other}


async def test_identifier_of_type_and_text(client):
    v2 = "http://terminology.hl7.org/CodeSystem/v2-0203"
    org_id = await _org(
        client,
        identifier=[{
            "type": {"coding": [{"system": v2, "code": "TAX", "display": "Tax ID number"}], "text": "GSTIN"},
            "system": "urn:gstin", "value": "29AAF",
        }],
    )
    await _org(client, identifier=[{"system": "urn:gstin", "value": "29AAF"}])
    assert await _ids_for(client, {"identifier:of-type": f"{v2}|TAX|29AAF"}) == {org_id}
    assert await _ids_for(client, {"identifier:of-type": f"{v2}|NPI|29AAF"}) == set()
    assert await _ids_for(client, {"identifier:text": "gst"}) == {org_id}
    assert await _ids_for(client, {"identifier:text": "tax id"}) == {org_id}
    _rejected(await _get(client, {"identifier:of-type": "TAX|29AAF"}))


async def test_type_token_forms_and_text(client):
    org_id = await create_organization(client, FULL)  # prov / "Healthcare Provider"
    text_only = await _org(client, type=[{"text": "Community Pharmacy"}])
    assert await _ids_for(client, {"type": "prov"}) == {org_id}
    assert await _ids_for(client, {"type": f"{ORG_TYPE}|prov"}) == {org_id}
    assert await _ids_for(client, {"type": "urn:other|prov"}) == set()
    assert await _ids_for(client, {"type": "prov,ins"}) == {org_id}
    assert await _ids_for(client, {"type:text": "healthcare"}) == {org_id}
    assert await _ids_for(client, {"type:text": "community"}) == {text_only}
    assert await _ids_for(client, {"type:not": "prov"}) == {text_only}


async def _seed_terminology(engine):
    """organization-type: prov (with child `prov-hosp` under IS-A) and ins;
    a ValueSet containing only `prov`."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    async with async_sessionmaker(engine)() as session:
        cs = TerminologyCodeSystem(canonical_url=ORG_TYPE, name="OrganizationType")
        session.add(cs)
        await session.flush()
        prov = TerminologyConcept(code_system_id=cs.id, code="prov", display="Healthcare Provider")
        hosp = TerminologyConcept(code_system_id=cs.id, code="prov-hosp", display="Hospital")
        ins = TerminologyConcept(code_system_id=cs.id, code="ins", display="Insurer")
        session.add_all([prov, hosp, ins])
        await session.flush()
        session.add(TerminologyRelationship(parent_concept_id=prov.id, child_concept_id=hosp.id, relationship_type="is-a"))
        vs = TerminologyValueSet(canonical_url="urn:vs:providers", name="Providers", binding_strength="example")
        session.add(vs)
        await session.flush()
        session.add(TerminologyValueSetConcept(value_set_id=vs.id, concept_id=prov.id))
        await session.commit()


async def test_type_in_not_in_above_below(client, _engine):
    await _seed_terminology(_engine)
    prov = await _org(client, type=[{"coding": [{"system": ORG_TYPE, "code": "prov"}]}])
    hosp = await _org(client, type=[{"coding": [{"system": ORG_TYPE, "code": "prov-hosp"}]}])
    ins = await _org(client, type=[{"coding": [{"system": ORG_TYPE, "code": "ins"}]}])
    assert await _ids_for(client, {"type:in": "urn:vs:providers"}) == {prov}
    assert await _ids_for(client, {"type:not-in": "urn:vs:providers"}) == {hosp, ins}
    assert await _ids_for(client, {"type:in": "urn:vs:unknown"}) == set()
    assert await _ids_for(client, {"type:below": f"{ORG_TYPE}|prov"}) == {prov, hosp}
    assert await _ids_for(client, {"type:above": f"{ORG_TYPE}|prov-hosp"}) == {prov, hosp}
    assert await _ids_for(client, {"type:below": "ins"}) == {ins}


# ── reference: partof, endpoint ──────────────────────────────────────────────


async def test_partof_reference_forms(client):
    parent = await _org(client, name="Parent")
    child = await _org(client, name="Child", partOf={"reference": f"Organization/{parent}"})
    for value in (
        str(parent),
        f"Organization/{parent}",
        f"http://test/api/fhir/v1/Organization/{parent}",
        f"http://test/api/fhir/v1/organizations/{parent}",
        f"Organization/{parent}/_history/3",
    ):
        assert await _ids_for(client, {"partof": value}) == {child}, value
    assert await _ids_for(client, {"partof:Organization": str(parent)}) == {child}
    assert await _ids_for(client, {"partof": "Location/1"}) == set()
    _rejected(await _get(client, {"partof:Patient": "1"}))


async def test_partof_absolute_external_and_identifier(client):
    url = "https://other.example/fhir/Organization/42"
    external = await _org(client, partOf={"reference": url})
    by_ident = await _org(client, partOf={"identifier": {"system": "urn:reg", "value": "R-9"}})
    root = await _org(client)
    assert await _ids_for(client, {"partof": url}) == {external}
    assert await _ids_for(client, {"partof:identifier": "urn:reg|R-9"}) == {by_ident}
    assert await _ids_for(client, {"partof:identifier": "R-9"}) == {by_ident}
    assert await _ids_for(client, {"partof:missing": "true"}) == {root}


async def test_partof_above_and_below(client):
    root = await _org(client, name="Root")
    mid = await _org(client, name="Mid", partOf={"reference": f"Organization/{root}"})
    leaf = await _org(client, name="Leaf", partOf={"reference": f"Organization/{mid}"})
    assert await _ids_for(client, {"partof:below": f"Organization/{root}"}) == {mid, leaf}
    assert await _ids_for(client, {"partof:below": str(mid)}) == {leaf}
    assert await _ids_for(client, {"partof:above": f"Organization/{mid}"}) == {mid, leaf}
    assert await _ids_for(client, {"partof:above": str(root)}) == {mid}


async def test_partof_chaining(client):
    root = await _org(client, name="Acme Holdings")
    mid = await _org(client, name="Acme Regional", partOf={"reference": f"Organization/{root}"})
    leaf = await _org(client, name="Acme Clinic", partOf={"reference": f"Organization/{mid}"})
    assert await _ids_for(client, {"partof.name": "acme hold"}) == {mid}
    assert await _ids_for(client, {"partof:Organization.name": "acme reg"}) == {leaf}
    assert await _ids_for(client, {"partof.partof.name:exact": "Acme Holdings"}) == {leaf}
    assert await _ids_for(client, {"partof._id": str(root)}) == {mid}
    _rejected(await _get(client, {"partof.nonsense": "x"}), "not-supported")
    _rejected(await _get(client, {"name.foo": "x"}))


async def test_endpoint_reference_and_identifier(client):
    org_id = await _org(client, endpoint=[{"reference": "Endpoint/7"}])
    by_ident = await create_organization(client, FULL)  # endpoint identifier urn:ext-endpoint|EP-1
    assert await _ids_for(client, {"endpoint": "Endpoint/7"}) == {org_id}
    assert await _ids_for(client, {"endpoint": "7"}) == {org_id}
    assert await _ids_for(client, {"endpoint": "Endpoint/8"}) == set()
    assert await _ids_for(client, {"endpoint:identifier": "urn:ext-endpoint|EP-1"}) == {by_ident}
    _rejected(await _get(client, {"endpoint.name": "x"}), "not-supported")


# ── _id / _lastUpdated ───────────────────────────────────────────────────────


async def test_id(client):
    a = await _org(client)
    b = await _org(client)
    c = await _org(client)
    assert await _ids_for(client, {"_id": str(a)}) == {a}
    assert await _ids_for(client, {"_id": f"{a},{b}"}) == {a, b}
    assert await _ids_for(client, {"_id:not": str(a)}) == {b, c}
    assert await _ids_for(client, {"_id": "not-a-number"}) == set()


async def test_last_updated_prefixes(client):
    org_id = await _org(client)
    now = datetime.now(UTC)
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    assert await _ids_for(client, {"_lastUpdated": f"gt{yesterday}"}) == {org_id}
    assert await _ids_for(client, {"_lastUpdated": f"ge{now.year}"}) == {org_id}
    assert await _ids_for(client, {"_lastUpdated": str(now.year)}) == {org_id}  # eq at year precision
    assert await _ids_for(client, {"_lastUpdated": f"lt{tomorrow}"}) == {org_id}
    assert await _ids_for(client, {"_lastUpdated": "lt2000-01-01"}) == set()
    assert await _ids_for(client, {"_lastUpdated": f"sa{tomorrow}"}) == set()
    assert await _ids_for(client, {"_lastUpdated": "eb2000"}) == set()
    assert await _ids_for(client, {"_lastUpdated": f"ne{now.year}"}) == set()
    ranged = await _search(client, [("_lastUpdated", f"ge{yesterday}"), ("_lastUpdated", f"lt{tomorrow}")])
    assert _ids(ranged) == {org_id}
    _rejected(await _get(client, {"_lastUpdated": "xx2024"}))
    _rejected(await _get(client, {"_lastUpdated": "2024-13-01"}))


# ── _sort / _count / _offset / _total ────────────────────────────────────────


async def test_sort(client):
    b = await _org(client, name="beta")
    a = await _org(client, name="Alpha")
    c = await _org(client, name="Charlie")
    assert _order(await _search(client, {"_sort": "name"})) == [a, b, c]
    assert _order(await _search(client, {"_sort": "-name"})) == [c, b, a]
    assert _order(await _search(client, {"_sort": "_id"})) == [b, a, c]
    assert _order(await _search(client)) == [c, a, b]  # default: newest first
    _rejected(await _get(client, {"_sort": "nonsense"}))
    _rejected(await _get(client, {"_sort": "address"}), "not-supported")


async def test_sort_multiple_values_uses_earliest_in_sort_order(client):
    """R4: a resource with several values for the sort parameter sorts by
    the one that comes earliest in the requested order — the smallest
    ascending, the largest descending. `name` is `name | alias`."""
    m = await _org(client, name="Mike")
    z = await _org(client, name="Zulu", alias=["Alpha Clinic"])  # alias sorts first ascending
    k = await _org(client, name="Kilo", alias=["Yankee"])  # alias sorts first descending
    no_alias = await _org(client, name="Lima")
    assert _order(await _search(client, {"_sort": "name"})) == [z, k, no_alias, m]
    assert _order(await _search(client, {"_sort": "-name"})) == [z, k, m, no_alias]

    # Same rule for values held in a child table (several addresses).
    a = await _org(client, name="A", address=[{"city": "Boston"}, {"city": "Zagreb"}])
    b = await _org(client, name="B", address=[{"city": "Madrid"}])
    ids = {a, b}
    asc = [i for i in _order(await _search(client, {"_sort": "address-city"})) if i in ids]
    desc = [i for i in _order(await _search(client, {"_sort": "-address-city"})) if i in ids]
    assert asc == [a, b] and desc == [a, b]


async def test_paging_links(client):
    ids = [await _org(client, name=f"Org {i}") for i in range(5)]
    page1 = await _search(client, {"_count": "2", "_sort": "_id"})
    assert _order(page1) == ids[:2]
    assert page1["total"] == 5
    assert _link(page1, "previous") is None
    assert "_offset=2" in _link(page1, "next")
    assert "_offset=4" in _link(page1, "last")

    page2 = await client.get(_link(page1, "next"))
    assert _order(page2.json()) == ids[2:4]
    assert "_offset=0" in _link(page2.json(), "previous")

    page3 = await _search(client, {"_count": "2", "_offset": "4", "_sort": "_id"})
    assert _order(page3) == ids[4:]
    assert _link(page3, "next") is None


async def test_count_is_capped_and_zero_means_count_only(client):
    await _org(client)
    bundle = await _search(client, {"_count": "0"})
    assert bundle["total"] == 1
    assert "entry" not in bundle
    _rejected(await _get(client, {"_count": "-1"}))
    _rejected(await _get(client, {"_count": "abc"}))


async def test_total_none(client):
    await _org(client)
    bundle = await _search(client, {"_total": "none"})
    assert "total" not in bundle
    assert len(bundle["entry"]) == 1
    _rejected(await _get(client, {"_total": "some"}))


# ── _summary / _elements ─────────────────────────────────────────────────────


def _subsetted(resource):
    return any(t["code"] == "SUBSETTED" for t in resource["meta"].get("tag", []))


async def test_summary_true_returns_summary_elements(client):
    await create_organization(client, FULL)
    resource = (await _search(client, {"_summary": "true"}))["entry"][0]["resource"]
    assert set(resource) <= {"resourceType", "id", "meta", "implicitRules", "identifier", "active", "type", "name", "partOf"}
    assert resource["name"] == "General Hospital"
    assert "address" not in resource and "telecom" not in resource
    assert _subsetted(resource)


async def test_summary_count_and_data(client):
    await create_organization(client, FULL)
    counted = await _search(client, {"_summary": "count"})
    assert counted["total"] == 1 and "entry" not in counted
    data = (await _search(client, {"_summary": "data"}))["entry"][0]["resource"]
    assert data["address"] and not _subsetted(data)  # nothing to drop: no narrative
    _rejected(await _get(client, {"_summary": "maybe"}))


async def test_elements(client):
    await create_organization(client, FULL)
    resource = (await _search(client, {"_elements": "name,alias"}))["entry"][0]["resource"]
    assert set(resource) == {"resourceType", "id", "meta", "name", "alias"}
    assert _subsetted(resource)


# ── _include / _revinclude ───────────────────────────────────────────────────


async def test_include_partof(client):
    root = await _org(client, name="Root")
    mid = await _org(client, name="Mid", partOf={"reference": f"Organization/{root}"})
    leaf = await _org(client, name="Leaf", partOf={"reference": f"Organization/{mid}"})
    bundle = await _search(client, {"_id": str(leaf), "_include": "Organization:partof"})
    assert _ids(bundle) == {leaf}
    assert _ids(bundle, "include") == {mid}
    assert bundle["total"] == 1  # included resources aren't counted

    iterated = await _search(client, {"_id": str(leaf), "_include:iterate": "Organization:partof"})
    assert _ids(iterated, "include") == {mid, root}
    assert _ids(await _search(client, {"_id": str(leaf), "_include": "*"}), "include") == {mid}


async def test_revinclude_partof(client):
    root = await _org(client, name="Root")
    mid = await _org(client, name="Mid", partOf={"reference": f"Organization/{root}"})
    leaf = await _org(client, name="Leaf", partOf={"reference": f"Organization/{mid}"})
    bundle = await _search(client, {"_id": str(root), "_revinclude": "Organization:partof"})
    assert _ids(bundle, "include") == {mid}
    iterated = await _search(client, {"_id": str(root), "_revinclude:iterate": "Organization:partof"})
    assert _ids(iterated, "include") == {mid, leaf}


async def test_include_unsupported(client):
    _rejected(await _get(client, {"_include": "Organization:nonsense"}), "not-supported")
    _rejected(await _get(client, {"_revinclude": "PractitionerRole:organization"}), "not-supported")
    _rejected(await _get(client, {"_include": "Organization:partof", "_summary": "text"}))


# ── unknown parameters, modifiers, handling ──────────────────────────────────


async def test_unknown_parameter_lenient_is_ignored_and_reported(client):
    org_id = await _org(client)
    bundle = await _search(client, {"nonsense": "x", "_tag": "y"})
    assert _ids(bundle) == {org_id}
    outcome = [e for e in bundle["entry"] if e["search"]["mode"] == "outcome"]
    assert len(outcome) == 1
    assert {i["expression"][0] for i in outcome[0]["resource"]["issue"]} == {"nonsense", "_tag"}
    assert "nonsense" not in _link(bundle, "self")


async def test_unknown_parameter_strict_is_rejected(client):
    resp = await _get(client, {"nonsense": "x"}, headers={"Prefer": "handling=strict"})
    _rejected(resp, "not-supported")


async def test_modifier_errors(client):
    _rejected(await _get(client, {"name:bogus": "x"}))  # unknown modifier
    _rejected(await _get(client, {"name:not": "x"}), "not-supported")  # wrong type's modifier
    _rejected(await _get(client, {"identifier:in": "urn:vs"}), "not-supported")
    _rejected(await _get(client, {"name:missing": "maybe"}))
    _rejected(await _get(client, {"_query": "anything"}), "not-supported")
    _rejected(await _get(client, {"_contained": "true"}), "not-supported")
    xml = await _get(client, {"_format": "xml"})  # can't serve XML at all -> 406, not 400
    assert xml.status_code == 406 and xml.json()["issue"][0]["code"] == "not-supported"


async def test_empty_parameter_value_is_ignored(client):
    org_id = await _org(client)
    assert await _ids_for(client, {"name": ""}) == {org_id}


async def test_old_non_fhir_paging_params_are_ignored(client):
    """`limit`/`offset`/`sort` were this server's own names; FHIR's are
    `_count`/`_offset`/`_sort`. The old names are now unknown parameters."""
    for _ in range(3):
        await _org(client)
    bundle = await _search(client, {"limit": "1"})
    assert len(_ids(bundle)) == 3


# ── POST _search ─────────────────────────────────────────────────────────────


async def test_post_search_form_body(client):
    org_id = await _org(client, name="Riverside Clinic")
    await _org(client, name="Other")
    resp = await client.post(
        BASE + "/_search",
        content="name=river&_count=5",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200, resp.text
    bundle = resp.json()
    assert _ids(bundle) == {org_id}
    assert _link(bundle, "self").startswith(f"http://test{BASE}/?")


# ── tenant scoping ───────────────────────────────────────────────────────────


async def test_chain_and_hierarchy_stay_in_tenant(client):
    parent = await _org(client, name="Scoped Parent")
    child = await _org(client, name="Scoped Child", partOf={"reference": f"Organization/{parent}"})
    assert await _ids_for(client, {"partof.name": "scoped"}) == {child}
    assert await _ids_for(client, {"partof:below": str(parent)}) == {child}
