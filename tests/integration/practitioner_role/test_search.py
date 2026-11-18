"""FHIR R4 search over PractitionerRole (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/practitionerrole.html#search).

One block per search parameter — including `date`, the engine's first
*Period* search — then chaining, `_include`, the result parameters (`_sort`,
`_count`/`_offset`/`_total`, `_summary`/`_elements`), combination rules,
lenient vs strict handling, the Bundle shape and POST _search.
"""

import pytest

from tests.integration.practitioner_role.support import (
    BASE,
    ROLE_CS,
    ROLE_IDS,
    SCT,
    create_endpoint,
    create_healthcare_service,
    create_location,
    create_organization,
    create_practitioner,
    create_role,
)

KEYS = ("cardio", "ortho", "locum", "bare")
ALL = set(KEYS)


@pytest.fixture
async def world(client):
    """Practitioners, organizations, locations, services, endpoints and four
    roles with distinct, searchable values. Returns {key: public id}."""
    w = {}
    w["prac_a"] = await create_practitioner(client, "Careful", "Adam")
    w["prac_b"] = await create_practitioner(client, "Bonesaw", "Beth")
    w["org_a"] = await create_organization(client, "Alpha Health")
    w["org_b"] = await create_organization(client, "Beta Clinics")
    w["loc1"] = await create_location(client, "North Wing", "Boston")
    w["loc2"] = await create_location(client, "South Wing", "Austin")
    w["svc"] = await create_healthcare_service(client, "Cardiology Clinic")
    w["ep"] = await create_endpoint(client)

    w["cardio"] = await create_role(
        client,
        {
            "active": True,
            "period": {"start": "2026-01-01T00:00:00Z", "end": "2026-06-30T23:59:59Z"},
            "practitioner": {"reference": f"Practitioner/{w['prac_a']}"},
            "organization": {"reference": f"Organization/{w['org_a']}"},
            "identifier": [
                {
                    "system": ROLE_IDS,
                    "value": "R-1",
                    "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "ROLE"}], "text": "Role number"},
                }
            ],
            "code": [{"coding": [{"system": ROLE_CS, "code": "doctor", "display": "Doctor"}], "text": "Medical doctor"}],
            "specialty": [{"coding": [{"system": SCT, "code": "394579002", "display": "Cardiology"}]}],
            "location": [{"reference": f"Location/{w['loc1']}"}],
            "healthcareService": [{"reference": f"HealthcareService/{w['svc']}"}],
            "telecom": [
                {"system": "phone", "value": "555-0001", "use": "work"},
                {"system": "email", "value": "cardio@example.org"},
            ],
            "endpoint": [{"reference": f"Endpoint/{w['ep']}"}],
        },
    )
    w["ortho"] = await create_role(
        client,
        {
            "active": False,
            "period": {"start": "2026-07-01T00:00:00Z", "end": "2026-12-31T23:59:59Z"},
            "practitioner": {"reference": f"Practitioner/{w['prac_b']}"},
            "organization": {"reference": f"Organization/{w['org_b']}"},
            "identifier": [{"system": ROLE_IDS, "value": "R-2"}],
            "code": [{"coding": [{"system": ROLE_CS, "code": "nurse"}]}],
            "specialty": [{"coding": [{"system": SCT, "code": "394801008", "display": "Orthopaedics"}]}],
            "location": [{"reference": f"Location/{w['loc2']}"}],
            "telecom": [{"system": "phone", "value": "555-0002", "use": "home"}],
        },
    )
    w["locum"] = await create_role(
        client,
        {
            "period": {"start": "2026-03-01T00:00:00Z"},  # still going
            "practitioner": {"reference": "https://other.example.org/fhir/Practitioner/7"},
            "code": [{"text": "Locum cover"}],
            "location": [{"reference": "https://other.example.org/fhir/Location/42"}],
        },
    )
    w["bare"] = await create_role(client, {"availabilityExceptions": "nothing indexed"})
    return w


async def _search(client, params=None, headers=None, base=BASE) -> dict:
    resp = await client.get(base + "/", params=params or {}, headers=headers or {})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _matches(bundle: dict) -> list[dict]:
    return [e["resource"] for e in bundle.get("entry") or [] if e["search"]["mode"] == "match"]


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


# ── _id / _lastUpdated / active ──────────────────────────────────────────────


async def test_id(client, world):
    assert await _found(client, world, _id=str(world["ortho"])) == {"ortho"}
    assert await _found(client, world, _id="999999") == set()
    assert await _found(client, world, _id=f"{world['ortho']},{world['bare']}") == {"ortho", "bare"}
    assert await _found(client, world, **{"_id:not": str(world["ortho"])}) == ALL - {"ortho"}


async def test_last_updated(client, world):
    assert await _found(client, world, _lastUpdated="ge2000-01-01") == ALL
    assert await _found(client, world, _lastUpdated="lt2000-01-01") == set()


async def test_active(client, world):
    assert await _found(client, world, active="true") == {"cardio"}
    assert await _found(client, world, active="false") == {"ortho"}
    assert await _found(client, world, **{"active:not": "true"}) == ALL - {"cardio"}
    assert await _found(client, world, **{"active:missing": "true"}) == {"locum", "bare"}
    assert (await client.get(BASE + "/", params={"active": "maybe"})).status_code == 400


# ── date (a Period) ──────────────────────────────────────────────────────────
# cardio: Jan-Jun 2026   ortho: Jul-Dec 2026   locum: from Mar 2026, still going   bare: no period


async def test_date_default_is_eq_containment(client, world):
    # eq: the search range must wholly contain the period; open-ended periods never fit.
    assert await _found(client, world, date="2026") == {"cardio", "ortho"}
    assert await _found(client, world, date="eq2026") == {"cardio", "ortho"}
    assert await _found(client, world, date="2026-03") == set()  # no period sits wholly inside March
    assert await _found(client, world, date="2027") == set()


async def test_date_overlap_prefixes(client, world):
    # gt / ge: some part of the period lies above the value
    assert await _found(client, world, date="gt2026-06-30") == {"ortho", "locum"}  # cardio ends 30 Jun 23:59:59
    assert await _found(client, world, date="ge2026-12-31") == {"ortho", "locum"}
    assert await _found(client, world, date="gt2027-01-01") == {"locum"}  # only the open-ended one reaches past
    # lt / le: some part of the period lies below the value
    assert await _found(client, world, date="lt2026-02-01") == {"cardio"}  # locum starts in March
    assert await _found(client, world, date="le2026-03-15") == {"cardio", "locum"}
    assert await _found(client, world, date="lt2025-01-01") == set()


async def test_date_sa_and_eb(client, world):
    assert await _found(client, world, date="sa2026-06-30T23:59:59Z") == {"ortho"}  # entirely after
    assert await _found(client, world, date="eb2026-07-01") == {"cardio"}  # entirely before
    assert await _found(client, world, date="eb2026-01-01") == set()


async def test_date_ne_and_ap(client, world):
    assert await _found(client, world, date="ne2026") == {"locum"}  # the open-ended period isn't wholly inside 2026
    assert "bare" not in await _found(client, world, date="ne2026")  # no period -> no value -> no match
    assert "cardio" in await _found(client, world, date="ap2026-03")


async def test_date_missing(client, world):
    assert await _found(client, world, **{"date:missing": "true"}) == {"bare"}
    assert await _found(client, world, **{"date:missing": "false"}) == ALL - {"bare"}


async def test_date_malformed_is_400_and_modifiers_are_rejected(client, world):
    assert (await client.get(BASE + "/", params={"date": "last-tuesday"})).status_code == 400
    assert (await client.get(BASE + "/", params={"date:exact": "2026"})).status_code == 400


# ── identifier ───────────────────────────────────────────────────────────────


async def test_identifier(client, world):
    assert await _found(client, world, identifier="R-1") == {"cardio"}
    assert await _found(client, world, identifier=f"{ROLE_IDS}|R-2") == {"ortho"}
    assert await _found(client, world, identifier=f"{ROLE_IDS}|") == {"cardio", "ortho"}
    assert await _found(client, world, identifier="|R-1") == set()
    assert await _found(client, world, **{"identifier:not": f"{ROLE_IDS}|R-1"}) == ALL - {"cardio"}
    assert await _found(client, world, **{"identifier:missing": "true"}) == {"locum", "bare"}


async def test_identifier_of_type_and_text(client, world):
    v2 = "http://terminology.hl7.org/CodeSystem/v2-0203"
    assert await _found(client, world, **{"identifier:of-type": f"{v2}|ROLE|R-1"}) == {"cardio"}
    assert await _found(client, world, **{"identifier:of-type": f"{v2}|ROLE|R-2"}) == set()
    assert await _found(client, world, **{"identifier:text": "Role num"}) == {"cardio"}


# ── telecom / phone / email ──────────────────────────────────────────────────


async def test_telecom_phone_email(client, world):
    assert await _found(client, world, telecom="555-0001") == {"cardio"}
    assert await _found(client, world, phone="555-0002") == {"ortho"}
    assert await _found(client, world, email="cardio@example.org") == {"cardio"}
    assert await _found(client, world, email="555-0001") == set()  # phone/email only look at their own system
    assert await _found(client, world, phone="cardio@example.org") == set()
    assert await _found(client, world, telecom="work|555-0001") == {"cardio"}  # `use|value`
    assert await _found(client, world, telecom="home|555-0001") == set()
    assert await _found(client, world, **{"phone:missing": "true"}) == {"locum", "bare"}
    assert await _found(client, world, **{"phone:not": "555-0001"}) == ALL - {"cardio"}


# ── role / specialty (tokens in the shared table) ────────────────────────────


@pytest.mark.parametrize(
    "param,system,code,expected",
    [
        ("role", ROLE_CS, "doctor", {"cardio"}),
        ("specialty", SCT, "394579002", {"cardio"}),
    ],
)
async def test_token_parameters(client, world, param, system, code, expected):
    assert await _found(client, world, **{param: code}) == expected
    assert await _found(client, world, **{param: f"{system}|{code}"}) == expected
    assert await _found(client, world, **{param: f"urn:other|{code}"}) == set()  # wrong system
    assert await _found(client, world, **{param: f"|{code}"}) == set()  # has a system
    assert await _found(client, world, **{param: "no-such-code"}) == set()
    assert await _found(client, world, **{f"{param}:not": code}) == ALL - expected


async def test_role_and_specialty_do_not_bleed_into_each_other(client, world):
    assert await _found(client, world, role="394579002") == set()
    assert await _found(client, world, specialty="doctor") == set()


async def test_token_comma_or_text_and_missing(client, world):
    assert await _found(client, world, role="doctor,nurse") == {"cardio", "ortho"}
    assert await _found(client, world, **{"role:text": "Medical"}) == {"cardio"}  # concept text
    assert await _found(client, world, **{"role:text": "Doc"}) == {"cardio"}  # coding display
    assert await _found(client, world, **{"role:text": "Locum"}) == {"locum"}  # text-only concept
    assert await _found(client, world, **{"specialty:text": "Ortho"}) == {"ortho"}
    assert await _found(client, world, **{"role:missing": "true"}) == {"bare"}
    assert await _found(client, world, **{"specialty:missing": "true"}) == {"locum", "bare"}


# ── practitioner / organization ──────────────────────────────────────────────


async def test_practitioner_reference_forms(client, world):
    a, b = world["prac_a"], world["prac_b"]
    assert await _found(client, world, practitioner=f"Practitioner/{a}") == {"cardio"}
    assert await _found(client, world, practitioner=str(b)) == {"ortho"}
    assert await _found(client, world, **{"practitioner:Practitioner": str(a)}) == {"cardio"}
    assert await _found(client, world, practitioner=f"{a},{b}") == {"cardio", "ortho"}
    assert await _found(client, world, practitioner="Organization/1") == set()  # wrong type
    assert (await client.get(BASE + "/", params={"practitioner:Organization": str(a)})).status_code == 400
    assert await _found(client, world, **{"practitioner:missing": "true"}) == {"bare"}


async def test_practitioner_absolute_url_of_another_server_matches_raw_string(client, world):
    assert await _found(client, world, practitioner="https://other.example.org/fhir/Practitioner/7") == {"locum"}
    assert await _found(client, world, practitioner="https://other.example.org/fhir/Practitioner/8") == set()


async def test_practitioner_chaining(client, world):
    assert await _found(client, world, **{"practitioner.family": "Careful"}) == {"cardio"}
    assert await _found(client, world, **{"practitioner.given": "Beth"}) == {"ortho"}
    assert await _found(client, world, **{"practitioner.family": "Nobody"}) == set()


async def test_organization(client, world):
    a, b = world["org_a"], world["org_b"]
    assert await _found(client, world, organization=f"Organization/{a}") == {"cardio"}
    assert await _found(client, world, organization=f"{a},{b}") == {"cardio", "ortho"}
    assert await _found(client, world, **{"organization:missing": "true"}) == {"locum", "bare"}
    assert await _found(client, world, **{"organization.name": "Alpha"}) == {"cardio"}
    assert await _found(client, world, **{"organization.name": "Beta"}) == {"ortho"}


async def test_organization_absolute_url_resolves_only_for_this_server(client, world):
    self_link = next(link["url"] for link in (await _search(client))["link"] if link["relation"] == "self")
    fhir_base = self_link.split("/practitioner-roles")[0]
    assert await _found(client, world, organization=f"{fhir_base}/Organization/{world['org_a']}") == {"cardio"}
    other = f"https://other.example.org/fhir/Organization/{world['org_a']}"
    assert await _found(client, world, organization=other) == set()


async def test_organization_and_practitioner_identifier_modifier(client, world):
    role = await create_role(
        client,
        {
            "organization": {"identifier": {"system": "urn:registry", "value": "ORG-9"}},
            "practitioner": {"identifier": {"system": "urn:npi", "value": "NPI-1"}},
        },
    )
    assert _ids(await _search(client, {"organization:identifier": "urn:registry|ORG-9"})) == {role}
    assert _ids(await _search(client, {"practitioner:identifier": "urn:npi|NPI-1"})) == {role}


# ── location / service / endpoint ────────────────────────────────────────────


async def test_location(client, world):
    l1, l2 = world["loc1"], world["loc2"]
    assert await _found(client, world, location=f"Location/{l1}") == {"cardio"}
    assert await _found(client, world, location=f"{l1},{l2}") == {"cardio", "ortho"}
    assert await _found(client, world, location="https://other.example.org/fhir/Location/42") == {"locum"}
    assert await _found(client, world, **{"location:missing": "true"}) == {"bare"}
    assert await _found(client, world, **{"location.name": "North"}) == {"cardio"}
    assert await _found(client, world, **{"location.address-city": "Austin"}) == {"ortho"}
    assert await _found(client, world, **{"location.name": "Nowhere"}) == set()


async def test_service(client, world):
    assert await _found(client, world, service=f"HealthcareService/{world['svc']}") == {"cardio"}
    assert await _found(client, world, service=str(world["svc"])) == {"cardio"}
    assert await _found(client, world, **{"service:missing": "true"}) == {"ortho", "locum", "bare"}
    assert await _found(client, world, **{"service.name": "Cardiology"}) == {"cardio"}
    assert await _found(client, world, **{"service.name": "Nope"}) == set()


async def test_location_and_service_are_separate_parameters(client, world):
    """The reference table holds both: a Location id must not satisfy `service`."""
    assert await _found(client, world, service=str(world["loc1"])) == set()  # a Location id is not a HealthcareService id
    assert await _found(client, world, service=f"Location/{world['loc1']}") == set()  # wrong type for the param
    assert await _found(client, world, location=f"HealthcareService/{world['svc']}") == set()


async def test_endpoint(client, world):
    assert await _found(client, world, endpoint=f"Endpoint/{world['ep']}") == {"cardio"}
    assert await _found(client, world, **{"endpoint:missing": "true"}) == {"ortho", "locum", "bare"}
    assert (await client.get(BASE + "/", params={"endpoint.name": "x"})).status_code == 400  # not chainable


# ── combination rules ────────────────────────────────────────────────────────


async def test_comma_is_or_repeat_is_and_and_parameters_and_together(client, world):
    assert await _found(client, world, identifier="R-1,R-2") == {"cardio", "ortho"}
    resp = await client.get(BASE + "/", params=[("role", "doctor"), ("specialty", "394579002")])
    assert _ids(resp.json()) == {world["cardio"]}
    resp = await client.get(BASE + "/", params=[("role", "doctor"), ("role", "nurse")])
    assert _ids(resp.json()) == set()  # no single role has both
    assert await _found(client, world, active="true", organization=str(world["org_a"])) == {"cardio"}
    assert await _found(client, world, active="false", organization=str(world["org_a"])) == set()
    assert await _found(client, world, date="ge2026-07-01", role="doctor") == set()


# ── _include ─────────────────────────────────────────────────────────────────


async def test_include_each_referenced_resource(client, world):
    for param, kind, key in (
        ("practitioner", "Practitioner", "prac_a"),
        ("organization", "Organization", "org_a"),
        ("location", "Location", "loc1"),
        ("service", "HealthcareService", "svc"),
        ("endpoint", "Endpoint", "ep"),
    ):
        bundle = await _search(client, {"_id": str(world["cardio"]), "_include": f"PractitionerRole:{param}"})
        assert _ids(bundle) == {world["cardio"]}
        assert _included(bundle) == {(kind, str(world[key]))}, param


async def test_include_star_and_dedup(client, world):
    bundle = await _search(client, {"_id": str(world["cardio"]), "_include": "*"})
    assert _included(bundle) == {
        ("Practitioner", str(world["prac_a"])),
        ("Organization", str(world["org_a"])),
        ("Location", str(world["loc1"])),
        ("HealthcareService", str(world["svc"])),
        ("Endpoint", str(world["ep"])),
    }
    # Across all roles: each Organization once; absolute-URL references resolve to nothing.
    orgs = await _search(client, {"_include": "PractitionerRole:organization"})
    assert _included(orgs) == {("Organization", str(world["org_a"])), ("Organization", str(world["org_b"]))}


async def test_unsupported_include_is_400(client, world):
    for value in ("PractitionerRole:bogus", "Patient:organization", "PractitionerRole"):
        assert (await client.get(BASE + "/", params={"_include": value})).status_code == 400, value


async def test_revinclude_roles_from_every_resource_they_reference(client, world):
    """The reverse direction: Practitioner / Organization / Location /
    HealthcareService / Endpoint searches can pull in the roles that point at them."""
    api = "/api/fhir/v1"
    cardio = ("PractitionerRole", str(world["cardio"]))
    for path, param, key in (
        ("practitioners", "practitioner", "prac_a"),
        ("organizations", "organization", "org_a"),
        ("locations", "location", "loc1"),
        ("healthcare-services", "service", "svc"),
        ("endpoints", "endpoint", "ep"),
    ):
        bundle = await _search(
            client, {"_id": str(world[key]), "_revinclude": f"PractitionerRole:{param}"}, base=f"{api}/{path}"
        )
        assert _included(bundle) == {cardio}, path
        entry = next(e for e in bundle["entry"] if e["search"]["mode"] == "include")
        assert entry["fullUrl"].endswith(f"/practitioner-roles/{world['cardio']}"), path
    # A resource no role points at pulls in nothing; so does the other role's own target.
    lonely = await create_practitioner(client, "Lonely", "Larry")
    none = await _search(client, {"_id": str(lonely), "_revinclude": "PractitionerRole:practitioner"}, base=f"{api}/practitioners")
    assert _included(none) == set()
    ortho = await _search(
        client, {"_id": str(world["prac_b"]), "_revinclude": "PractitionerRole:practitioner"}, base=f"{api}/practitioners"
    )
    assert _included(ortho) == {("PractitionerRole", str(world["ortho"]))}


# ── _sort / paging / totals ──────────────────────────────────────────────────


async def test_sort(client, world):
    default = [int(r["id"]) for r in _matches(await _search(client))]
    assert default == sorted(default, reverse=True)
    assert [int(r["id"]) for r in _matches(await _search(client, {"_sort": "_id"}))] == sorted(default)
    by_date = [int(r["id"]) for r in _matches(await _search(client, {"_sort": "date"}))]
    assert by_date[:3] == [world["cardio"], world["locum"], world["ortho"]]  # Jan, Mar, Jul; no period last
    assert by_date[-1] == world["bare"]
    for name in ("active", "identifier", "role", "specialty", "practitioner", "organization", "location", "service"):
        assert (await client.get(BASE + "/", params={"_sort": name})).status_code == 200, name


async def test_count_offset_total_and_links(client, world):
    page1 = await _search(client, {"_count": "2", "_sort": "_id"})
    assert page1["total"] == 4 and len(page1["entry"]) == 2
    assert {"self", "first", "next", "last"} <= {link["relation"] for link in page1["link"]}
    page2 = await _search(client, {"_count": "2", "_offset": "2", "_sort": "_id"})
    assert _ids(page1).isdisjoint(_ids(page2))
    assert "next" not in {link["relation"] for link in page2["link"]}
    only = await _search(client, {"_count": "0"})
    assert only["total"] == 4 and "entry" not in only
    assert "total" not in await _search(client, {"_total": "none"})


async def test_summary_and_elements(client, world):
    cardio = str(world["cardio"])
    # availableTime / notAvailable aren't Σ elements; give the role some so there is something to strip.
    role = await create_role(client, {"active": True, "availableTime": [{"daysOfWeek": ["mon"]}], "availabilityExceptions": "x"})
    resource = _matches(await _search(client, {"_id": str(role), "_summary": "true"}))[0]
    assert "active" in resource and "availableTime" not in resource and "availabilityExceptions" not in resource
    assert any(t.get("code") == "SUBSETTED" for t in resource["meta"]["tag"])
    el = _matches(await _search(client, {"_id": cardio, "_elements": "active"}))[0]
    assert el["active"] is True and "specialty" not in el


# ── lenient / strict handling, rejected input ────────────────────────────────


async def test_unknown_parameter_ignored_with_outcome_or_400_when_strict(client, world):
    bundle = await _search(client, {"bogus": "x", "identifier": "R-1"})
    assert _ids(bundle) == {world["cardio"]}
    assert [e for e in bundle["entry"] if e["search"]["mode"] == "outcome"]
    resp = await client.get(BASE + "/", params={"bogus": "x"}, headers={"Prefer": "handling=strict"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"


async def test_unsupported_common_parameters_ignored(client, world):
    for name in ("_tag", "_profile", "_has", "_text", "_filter"):
        assert (await client.get(BASE + "/", params={name: "x"})).status_code == 200, name


async def test_bad_modifier_and_malformed_value_are_400(client, world):
    for params in (
        {"active:contains": "x"},
        {"role:exact": "x"},
        {"organization:not": "1"},
        {"practitioner:above": "1"},
        {"_lastUpdated": "notadate"},
        {"_count": "abc"},
        {"_query": "x"},
        {"role.name": "x"},  # token parameters can't be chained
    ):
        assert (await client.get(BASE + "/", params=params)).status_code == 400, params


# ── Bundle shape / POST _search ──────────────────────────────────────────────


async def test_bundle_shape(client, world):
    bundle = await _search(client, {"identifier": "R-1"})
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/practitioner-roles/{world['cardio']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "PractitionerRole"


async def test_xml_only_accept_is_406_on_search(client):
    assert (await client.get(BASE + "/", headers={"Accept": "application/fhir+xml"})).status_code == 406


async def test_post_search_form_encoded_and_combined_with_query_string(client, world):
    form = {"Content-Type": "application/x-www-form-urlencoded"}
    resp = await client.post(BASE + "/_search", content="role=doctor&active=true", headers=form)
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["cardio"]}
    resp = await client.post(BASE + "/_search?active=true", content="role=doctor", headers=form)
    assert _ids(resp.json()) == {world["cardio"]}
    resp = await client.post(BASE + "/_search?active=false", content="role=doctor", headers=form)
    assert _ids(resp.json()) == set()
