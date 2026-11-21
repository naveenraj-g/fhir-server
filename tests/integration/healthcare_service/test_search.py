"""FHIR R4 search over HealthcareService (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/healthcareservice.html#search).

One block per search parameter, then chaining, `_include` / `_revinclude`,
the result parameters (`_sort`, `_count`/`_offset`/`_total`,
`_summary`/`_elements`), combination rules, lenient vs strict handling, the
Bundle shape and POST _search.
"""

import pytest

from tests.integration.healthcare_service.support import (
    BASE,
    ORG_BASE,
    create_healthcare_service,
    create_organization,
    seed_location,
)

LOC_BASE = "/api/fhir/v1/locations"
CAT = "http://terminology.hl7.org/CodeSystem/service-category"
TYPE = "http://terminology.hl7.org/CodeSystem/service-type"
SCT = "http://snomed.info/sct"
PROG = "https://fhir-server.dev/fhir/CodeSystem/program"
CHAR = "https://fhir-server.dev/fhir/CodeSystem/characteristic"
SVC = "https://fhir-server.dev/fhir/identifier-system/hs-ids"


@pytest.fixture
async def world(client, _engine):
    """Two organizations, two locations and four services with distinct,
    searchable values. Returns {key: public id}."""
    w = {}
    w["org_a"] = await create_organization(client, "Alpha Health")
    w["org_b"] = await create_organization(client, "Beta Clinics")
    w["loc1"] = await seed_location(
        _engine, location_id=230101, name="North Wing", city="Boston"
    )
    w["loc2"] = await seed_location(
        _engine, location_id=230102, name="South Wing", city="Austin"
    )

    w["cardio"] = await create_healthcare_service(
        client,
        {
            "active": True,
            "name": "Cardiology Clinic",
            "providedBy": {"reference": f"Organization/{w['org_a']}"},
            "location": [{"reference": f"Location/{w['loc1']}"}],
            "coverageArea": [{"reference": f"Location/{w['loc2']}"}],
            "identifier": [
                {
                    "system": SVC,
                    "value": "HS-1",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "SVC",
                            }
                        ],
                        "text": "Service number",
                    },
                }
            ],
            "category": [
                {
                    "coding": [
                        {"system": CAT, "code": "35", "display": "Specialist Medical"}
                    ],
                    "text": "Specialist",
                }
            ],
            "type": [
                {
                    "coding": [
                        {"system": TYPE, "code": "124", "display": "General Practice"}
                    ]
                }
            ],
            "specialty": [
                {
                    "coding": [
                        {"system": SCT, "code": "394579002", "display": "Cardiology"}
                    ]
                }
            ],
            "program": [
                {
                    "coding": [
                        {"system": PROG, "code": "diabetes", "display": "Diabetes"}
                    ]
                }
            ],
            "characteristic": [
                {
                    "coding": [
                        {
                            "system": CHAR,
                            "code": "wheelchair",
                            "display": "Wheelchair access",
                        }
                    ]
                }
            ],
            "endpoint": [{"identifier": {"system": "urn:ep", "value": "EP-1"}}],
        },
    )
    w["derm"] = await create_healthcare_service(
        client,
        {
            "active": False,
            "name": "Dermatology Center",
            "providedBy": {"reference": f"Organization/{w['org_b']}"},
            "location": [{"reference": f"Location/{w['loc2']}"}],
            "identifier": [{"system": SVC, "value": "HS-2"}],
            "category": [
                {"coding": [{"system": CAT, "code": "17", "display": "Other"}]}
            ],
            "type": [{"coding": [{"system": TYPE, "code": "124"}]}],
            "specialty": [
                {
                    "coding": [
                        {"system": SCT, "code": "394582007", "display": "Dermatology"}
                    ]
                }
            ],
        },
    )
    w["ortho"] = await create_healthcare_service(
        client,
        {
            "name": "Ortho & Müller Spine",
            "location": [{"reference": "https://other.example.org/fhir/Location/42"}],
            "program": [{"text": "Rehab only"}],
        },
    )
    w["bare"] = await create_healthcare_service(client, {"comment": "no name, no refs"})
    return w


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
    by_id = {v: k for k, v in w.items() if k in ("cardio", "derm", "ortho", "bare")}
    return {by_id[i] for i in _ids(await _search(client, params))}


ALL = {"cardio", "derm", "ortho", "bare"}


# ── _id / _lastUpdated / active ──────────────────────────────────────────────


async def test_id(client, world):
    assert await _found(client, world, _id=str(world["derm"])) == {"derm"}
    assert await _found(client, world, _id="999999") == set()
    assert await _found(client, world, _id=f"{world['derm']},{world['bare']}") == {
        "derm",
        "bare",
    }
    assert await _found(client, world, **{"_id:not": str(world["derm"])}) == ALL - {
        "derm"
    }


async def test_last_updated(client, world):
    assert await _found(client, world, _lastUpdated="ge2000-01-01") == ALL
    assert await _found(client, world, _lastUpdated="lt2000-01-01") == set()


async def test_active(client, world):
    assert await _found(client, world, active="true") == {"cardio"}
    assert await _found(client, world, active="false") == {"derm"}
    assert await _found(client, world, **{"active:not": "true"}) == ALL - {"cardio"}
    assert await _found(client, world, **{"active:missing": "true"}) == {
        "ortho",
        "bare",
    }
    assert (await client.get(BASE + "/", params={"active": "maybe"})).status_code == 400


# ── name ─────────────────────────────────────────────────────────────────────


async def test_name_is_case_and_accent_insensitive_starts_with(client, world):
    assert await _found(client, world, name="cardio") == {"cardio"}
    assert await _found(client, world, name="CARDIOLOGY CL") == {"cardio"}
    assert await _found(client, world, name="ortho & muller") == {"ortho"}  # ü -> u
    assert await _found(client, world, name="clinic") == set()  # not a prefix


async def test_name_modifiers(client, world):
    assert await _found(client, world, **{"name:contains": "clinic"}) == {"cardio"}
    assert await _found(client, world, **{"name:exact": "Dermatology Center"}) == {
        "derm"
    }
    assert await _found(client, world, **{"name:exact": "dermatology center"}) == set()
    assert await _found(client, world, **{"name:missing": "true"}) == {"bare"}
    assert await _found(client, world, **{"name:missing": "false"}) == ALL - {"bare"}


# ── identifier ───────────────────────────────────────────────────────────────


async def test_identifier(client, world):
    assert await _found(client, world, identifier="HS-1") == {"cardio"}
    assert await _found(client, world, identifier=f"{SVC}|HS-2") == {"derm"}
    assert await _found(client, world, identifier=f"{SVC}|") == {"cardio", "derm"}
    assert await _found(client, world, identifier="|HS-1") == set()
    assert await _found(client, world, **{"identifier:not": f"{SVC}|HS-1"}) == ALL - {
        "cardio"
    }
    assert await _found(client, world, **{"identifier:missing": "true"}) == {
        "ortho",
        "bare",
    }


async def test_identifier_of_type_and_text(client, world):
    v2 = "http://terminology.hl7.org/CodeSystem/v2-0203"
    assert await _found(client, world, **{"identifier:of-type": f"{v2}|SVC|HS-1"}) == {
        "cardio"
    }
    assert (
        await _found(client, world, **{"identifier:of-type": f"{v2}|SVC|HS-2"}) == set()
    )
    assert await _found(client, world, **{"identifier:text": "Service num"}) == {
        "cardio"
    }


# ── the five CodeableConcept token parameters ────────────────────────────────


@pytest.mark.parametrize(
    "param,system,code,expected",
    [
        ("service-category", CAT, "35", {"cardio"}),
        ("service-type", TYPE, "124", {"cardio", "derm"}),
        ("specialty", SCT, "394579002", {"cardio"}),
        ("program", PROG, "diabetes", {"cardio"}),
        ("characteristic", CHAR, "wheelchair", {"cardio"}),
    ],
)
async def test_token_parameters(client, world, param, system, code, expected):
    assert await _found(client, world, **{param: code}) == expected
    assert await _found(client, world, **{param: f"{system}|{code}"}) == expected
    assert await _found(client, world, **{param: f"{system}|"}) >= expected
    assert (
        await _found(client, world, **{param: f"urn:other|{code}"}) == set()
    )  # wrong system
    assert await _found(client, world, **{param: f"|{code}"}) == set()  # has a system
    assert await _found(client, world, **{param: "no-such-code"}) == set()
    assert await _found(client, world, **{f"{param}:not": code}) == ALL - expected


async def test_token_parameters_do_not_bleed_into_each_other(client, world):
    """All five live in one table: a code in `specialty` must not satisfy `program`."""
    assert await _found(client, world, program="394579002") == set()
    assert await _found(client, world, specialty="diabetes") == set()
    assert await _found(client, world, **{"service-type": "35"}) == set()


async def test_token_comma_or_and_missing(client, world):
    assert await _found(client, world, specialty="394579002,394582007") == {
        "cardio",
        "derm",
    }
    assert await _found(client, world, **{"specialty:missing": "true"}) == {
        "ortho",
        "bare",
    }
    assert await _found(client, world, **{"program:missing": "true"}) == {
        "derm",
        "bare",
    }


async def test_token_text_modifier(client, world):
    assert await _found(client, world, **{"specialty:text": "Cardio"}) == {
        "cardio"
    }  # coding.display
    assert await _found(client, world, **{"service-category:text": "Specialist"}) == {
        "cardio"
    }  # concept text
    assert await _found(client, world, **{"program:text": "Rehab"}) == {
        "ortho"
    }  # text-only concept
    assert await _found(client, world, **{"specialty:text": "Derm"}) == {"derm"}


# ── organization (providedBy) ────────────────────────────────────────────────


async def test_organization_reference_forms(client, world):
    a, b = world["org_a"], world["org_b"]
    assert await _found(client, world, organization=f"Organization/{a}") == {"cardio"}
    assert await _found(client, world, organization=str(b)) == {"derm"}
    assert await _found(client, world, **{"organization:Organization": str(a)}) == {
        "cardio"
    }
    assert await _found(client, world, organization=f"{a},{b}") == {"cardio", "derm"}
    assert await _found(client, world, organization="Location/1") == set()  # wrong type
    # A type modifier that isn't a target of the parameter is rejected, not "no match".
    assert (
        await client.get(BASE + "/", params={"organization:Location": str(a)})
    ).status_code == 400
    assert await _found(client, world, **{"organization:missing": "true"}) == {
        "ortho",
        "bare",
    }
    # `:not` is a token modifier in R4; a reference parameter doesn't take it.
    assert (
        await client.get(BASE + "/", params={"organization:not": f"Organization/{a}"})
    ).status_code == 400


async def test_organization_absolute_url_resolves_only_for_this_server(client, world):
    self_link = next(
        l["url"] for l in (await _search(client))["link"] if l["relation"] == "self"
    )
    fhir_base = self_link.split("/healthcare-services")[0]
    # This server's own absolute URL is the same as the relative reference...
    assert await _found(
        client, world, organization=f"{fhir_base}/Organization/{world['org_a']}"
    ) == {"cardio"}
    # ...another server's never matches a local row.
    assert (
        await _found(
            client,
            world,
            organization=f"https://other.example.org/fhir/Organization/{world['org_a']}",
        )
        == set()
    )


async def test_organization_identifier_modifier(client, world):
    org = await create_organization(client, "Gamma")
    hs = await create_healthcare_service(
        client,
        {
            "name": "Via Registry",
            "providedBy": {"identifier": {"system": "urn:registry", "value": "ORG-9"}},
        },
    )
    bundle = await _search(client, {"organization:identifier": "urn:registry|ORG-9"})
    assert _ids(bundle) == {hs}
    assert org not in _ids(bundle)


async def test_organization_chaining(client, world):
    assert await _found(client, world, **{"organization.name": "Alpha"}) == {"cardio"}
    assert await _found(client, world, **{"organization.name": "Beta"}) == {"derm"}
    assert await _found(client, world, **{"organization.name": "Nope"}) == set()


# ── location / coverage-area / endpoint ──────────────────────────────────────


async def test_location_reference_forms(client, world):
    l1, l2 = world["loc1"], world["loc2"]
    assert await _found(client, world, location=f"Location/{l1}") == {"cardio"}
    assert await _found(client, world, location=str(l2)) == {"derm"}
    assert await _found(client, world, location=f"{l1},{l2}") == {"cardio", "derm"}
    assert await _found(client, world, **{"location:Location": str(l1)}) == {"cardio"}
    assert (
        await client.get(BASE + "/", params={"location:Organization": str(l1)})
    ).status_code == 400
    assert await _found(client, world, **{"location:missing": "true"}) == {"bare"}


async def test_location_absolute_url_of_another_server_matches_raw_string(
    client, world
):
    assert await _found(
        client, world, location="https://other.example.org/fhir/Location/42"
    ) == {"ortho"}
    assert (
        await _found(
            client, world, location="https://other.example.org/fhir/Location/43"
        )
        == set()
    )


async def test_location_chaining(client, world):
    assert await _found(client, world, **{"location.name": "North"}) == {"cardio"}
    assert await _found(client, world, **{"location.address-city": "Austin"}) == {
        "derm"
    }
    assert await _found(client, world, **{"location.name": "Nowhere"}) == set()


async def test_coverage_area(client, world):
    assert await _found(client, world, **{"coverage-area": str(world["loc2"])}) == {
        "cardio"
    }
    assert await _found(client, world, **{"coverage-area": str(world["loc1"])}) == set()
    assert await _found(client, world, **{"coverage-area.name": "South"}) == {"cardio"}
    assert await _found(client, world, **{"coverage-area:missing": "true"}) == {
        "derm",
        "ortho",
        "bare",
    }


async def test_location_and_coverage_area_are_separate_parameters(client, world):
    """cardio is located at loc1 and covers loc2; derm is located at loc2."""
    assert await _found(client, world, location=str(world["loc2"])) == {"derm"}
    assert await _found(client, world, **{"coverage-area": str(world["loc2"])}) == {
        "cardio"
    }


async def test_endpoint_identifier(client, world):
    assert await _found(client, world, **{"endpoint:identifier": "urn:ep|EP-1"}) == {
        "cardio"
    }
    assert (
        await _found(client, world, **{"endpoint:identifier": "urn:ep|EP-9"}) == set()
    )
    assert await _found(client, world, **{"endpoint:missing": "true"}) == {
        "derm",
        "ortho",
        "bare",
    }


# ── combination rules ────────────────────────────────────────────────────────


async def test_comma_is_or_repeat_is_and_and_parameters_and_together(client, world):
    assert await _found(client, world, name="Cardiology,Dermatology") == {
        "cardio",
        "derm",
    }
    resp = await client.get(
        BASE + "/", params=[("specialty", "394579002"), ("program", "diabetes")]
    )
    assert _ids(resp.json()) == {world["cardio"]}
    resp = await client.get(
        BASE + "/", params=[("specialty", "394579002"), ("specialty", "394582007")]
    )
    assert _ids(resp.json()) == set()  # one service has only one of the two
    assert await _found(client, world, active="true", **{"service-type": "124"}) == {
        "cardio"
    }
    assert (
        await _found(client, world, active="false", **{"service-category": "35"})
        == set()
    )


async def test_escaped_comma_is_literal(client, world):
    assert await _found(client, world, name="Cardiology\\,Dermatology") == set()


# ── _include / _revinclude ───────────────────────────────────────────────────


async def test_include_organization(client, world):
    bundle = await _search(
        client,
        {"_id": str(world["cardio"]), "_include": "HealthcareService:organization"},
    )
    assert _ids(bundle) == {world["cardio"]}
    assert _included(bundle) == {("Organization", str(world["org_a"]))}


async def test_include_location_and_coverage_area(client, world):
    bundle = await _search(
        client, {"_id": str(world["cardio"]), "_include": "HealthcareService:location"}
    )
    assert _included(bundle) == {("Location", str(world["loc1"]))}
    bundle = await _search(
        client,
        {"_id": str(world["cardio"]), "_include": "HealthcareService:coverage-area"},
    )
    assert _included(bundle) == {("Location", str(world["loc2"]))}


async def test_include_star_and_several_includes(client, world):
    bundle = await _search(client, {"_id": str(world["cardio"]), "_include": "*"})
    assert _included(bundle) == {
        ("Organization", str(world["org_a"])),
        ("Location", str(world["loc1"])),
        ("Location", str(world["loc2"])),
    }


async def test_include_dedups_and_skips_unresolved(client, world):
    bundle = await _search(client, {"_include": "HealthcareService:location"})
    # loc1 (cardio) and loc2 (derm), once each; ortho's absolute URL isn't a local row.
    assert _included(bundle) == {
        ("Location", str(world["loc1"])),
        ("Location", str(world["loc2"])),
    }


async def test_include_endpoint_is_accepted_and_adds_nothing(client, world):
    bundle = await _search(
        client, {"_id": str(world["cardio"]), "_include": "HealthcareService:endpoint"}
    )
    assert _included(bundle) == set()


async def test_unsupported_include_is_400(client, world):
    for value in (
        "HealthcareService:bogus",
        "Patient:organization",
        "HealthcareService",
    ):
        assert (
            await client.get(BASE + "/", params={"_include": value})
        ).status_code == 400, value


async def test_organization_search_can_revinclude_its_services(client, world):
    bundle = await _search(
        client,
        {"_id": str(world["org_a"]), "_revinclude": "HealthcareService:organization"},
        base=ORG_BASE,
    )
    assert _included(bundle) == {("HealthcareService", str(world["cardio"]))}
    inc = next(e for e in bundle["entry"] if e["search"]["mode"] == "include")
    assert inc["fullUrl"].endswith(f"/healthcare-services/{world['cardio']}")


async def test_location_search_can_revinclude_services_by_location_and_coverage_area(
    client, world
):
    by_location = await _search(
        client,
        {"_id": str(world["loc2"]), "_revinclude": "HealthcareService:location"},
        base=LOC_BASE,
    )
    assert _included(by_location) == {("HealthcareService", str(world["derm"]))}
    by_coverage = await _search(
        client,
        {"_id": str(world["loc2"]), "_revinclude": "HealthcareService:coverage-area"},
        base=LOC_BASE,
    )
    assert _included(by_coverage) == {("HealthcareService", str(world["cardio"]))}


# ── _sort / paging / totals ──────────────────────────────────────────────────


async def test_sort_by_name_and_id(client, world):
    asc = [r["id"] for r in _matches(await _search(client, {"_sort": "name"}))]
    named = [str(world[k]) for k in ("cardio", "derm", "ortho")]
    assert asc[:3] == named  # Cardiology, Dermatology, Ortho (no name sorts last)
    assert asc[-1] == str(world["bare"])
    desc = [r["id"] for r in _matches(await _search(client, {"_sort": "-name"}))]
    assert desc[0] == str(world["ortho"])
    default = [int(r["id"]) for r in _matches(await _search(client))]
    assert default == sorted(default, reverse=True)
    assert [
        int(r["id"]) for r in _matches(await _search(client, {"_sort": "_id"}))
    ] == sorted(default)


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
    cardio = str(world["cardio"])
    data = await _search(client, {"_id": cardio, "_summary": "true"})
    resource = _matches(data)[0]
    assert (
        "name" in resource
        and "specialty" in resource
        and "availableTime" not in resource
    )
    assert any(t.get("code") == "SUBSETTED" for t in resource["meta"]["tag"])
    el = _matches(await _search(client, {"_id": cardio, "_elements": "name"}))[0]
    assert el["name"] == "Cardiology Clinic" and "specialty" not in el


# ── lenient / strict handling, rejected input ────────────────────────────────


async def test_unknown_parameter_ignored_with_outcome_or_400_when_strict(client, world):
    bundle = await _search(client, {"bogus": "x", "name": "Cardio"})
    assert _ids(bundle) == {world["cardio"]}
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
        {"active:contains": "x"},
        {"specialty:exact": "x"},
        {"organization:above": "1"},
        {"_lastUpdated": "notadate"},
        {"_count": "abc"},
        {"_query": "x"},
        {"program.name": "x"},  # token parameters can't be chained
        {"endpoint.name": "x"},  # Endpoint isn't a resource here
    ):
        assert (await client.get(BASE + "/", params=params)).status_code == 400, params


# ── Bundle shape / POST _search ──────────────────────────────────────────────


async def test_bundle_shape(client, world):
    bundle = await _search(client, {"name": "Cardio"})
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/healthcare-services/{world['cardio']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "HealthcareService"


async def test_xml_only_accept_is_406_on_search(client):
    assert (
        await client.get(BASE + "/", headers={"Accept": "application/fhir+xml"})
    ).status_code == 406


async def test_post_search_form_encoded_and_combined_with_query_string(client, world):
    form = {"Content-Type": "application/x-www-form-urlencoded"}
    resp = await client.post(
        BASE + "/_search", content="name=Cardio&active=true", headers=form
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["cardio"]}
    resp = await client.post(
        BASE + "/_search?active=true", content="name=Cardio", headers=form
    )
    assert _ids(resp.json()) == {world["cardio"]}
    resp = await client.post(
        BASE + "/_search?active=false", content="name=Cardio", headers=form
    )
    assert _ids(resp.json()) == set()
