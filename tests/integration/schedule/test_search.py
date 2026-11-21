"""FHIR R4 search over Schedule (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/schedule.html#search).

One block per search parameter — `actor` is the engine's first reference
parameter with several target types, and `date` a Period search over
`planningHorizon` — then chaining through a typed actor, `_include` (one per
actor type) and `_revinclude` from every actor resource, the result
parameters, combination rules, lenient vs strict handling, the Bundle shape
and POST _search.
"""

import pytest

from tests.integration.schedule.support import (
    BASE,
    CAT,
    SCHED_IDS,
    SCT,
    TYPE,
    create_healthcare_service,
    create_location,
    create_practitioner,
    create_practitioner_role,
    create_schedule,
)

API = "/api/fhir/v1"
KEYS = ("clinic", "surgery", "cover", "bare")
ALL = set(KEYS)


@pytest.fixture
async def world(client):
    """Practitioner, role, service and location actors, and four schedules
    with distinct, searchable values. Returns {key: public id}."""
    w = {}
    w["prac"] = await create_practitioner(client, "Careful", "Adam")
    w["role"] = await create_practitioner_role(client)
    w["svc"] = await create_healthcare_service(client, "Cardiology Clinic")
    w["loc"] = await create_location(client, "North Wing", "Boston")

    w["clinic"] = await create_schedule(
        client,
        {
            "active": True,
            "planningHorizon": {
                "start": "2026-01-01T00:00:00Z",
                "end": "2026-06-30T23:59:59Z",
            },
            "identifier": [
                {
                    "system": SCHED_IDS,
                    "value": "S-1",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "SCH",
                            }
                        ],
                        "text": "Schedule number",
                    },
                }
            ],
            "serviceCategory": [
                {
                    "coding": [
                        {"system": CAT, "code": "17", "display": "General Practice"}
                    ],
                    "text": "General",
                }
            ],
            "serviceType": [
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
            "actor": [
                {"reference": f"Practitioner/{w['prac']}"},
                {"reference": f"Location/{w['loc']}"},
            ],
        },
    )
    w["surgery"] = await create_schedule(
        client,
        {
            "active": False,
            "planningHorizon": {
                "start": "2026-07-01T00:00:00Z",
                "end": "2026-12-31T23:59:59Z",
            },
            "identifier": [{"system": SCHED_IDS, "value": "S-2"}],
            "serviceCategory": [{"coding": [{"system": CAT, "code": "3"}]}],
            "serviceType": [{"coding": [{"system": TYPE, "code": "124"}]}],
            "specialty": [
                {
                    "coding": [
                        {"system": SCT, "code": "394801008", "display": "Orthopaedics"}
                    ]
                }
            ],
            "actor": [
                {"reference": f"PractitionerRole/{w['role']}"},
                {"reference": f"HealthcareService/{w['svc']}"},
            ],
        },
    )
    w["cover"] = await create_schedule(
        client,
        {
            "planningHorizon": {"start": "2026-03-01T00:00:00Z"},  # still going
            "serviceCategory": [{"text": "Locum cover"}],
            "actor": [
                {"reference": "Patient/77"},
                {"reference": "https://other.example.org/fhir/Device/5"},
                {"identifier": {"system": "urn:device", "value": "D-9"}},
            ],
        },
    )
    w["bare"] = await create_schedule(
        client, {"comment": "no index", "actor": [{"display": "Nobody"}]}
    )
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
    by_id = {w[k]: k for k in KEYS}
    return {by_id[i] for i in _ids(await _search(client, params))}


# ── _id / _lastUpdated / active ──────────────────────────────────────────────


async def test_id(client, world):
    assert await _found(client, world, _id=str(world["surgery"])) == {"surgery"}
    assert await _found(client, world, _id="999999") == set()
    assert await _found(client, world, _id=f"{world['surgery']},{world['bare']}") == {
        "surgery",
        "bare",
    }
    assert await _found(client, world, **{"_id:not": str(world["surgery"])}) == ALL - {
        "surgery"
    }


async def test_last_updated(client, world):
    assert await _found(client, world, _lastUpdated="ge2000-01-01") == ALL
    assert await _found(client, world, _lastUpdated="lt2000-01-01") == set()


async def test_active(client, world):
    assert await _found(client, world, active="true") == {"clinic"}
    assert await _found(client, world, active="false") == {"surgery"}
    assert await _found(client, world, **{"active:not": "true"}) == ALL - {"clinic"}
    assert await _found(client, world, **{"active:missing": "true"}) == {
        "cover",
        "bare",
    }
    assert (await client.get(BASE + "/", params={"active": "maybe"})).status_code == 400


# ── date (the planningHorizon Period) ────────────────────────────────────────
# clinic: Jan-Jun 2026   surgery: Jul-Dec 2026   cover: from Mar 2026, still going   bare: none


async def test_date_default_is_eq_containment(client, world):
    assert await _found(client, world, date="2026") == {"clinic", "surgery"}
    assert await _found(client, world, date="eq2026") == {"clinic", "surgery"}
    assert (
        await _found(client, world, date="2026-03") == set()
    )  # nothing sits wholly inside March
    assert await _found(client, world, date="2027") == set()


async def test_date_overlap_and_ordering_prefixes(client, world):
    assert await _found(client, world, date="gt2026-06-30") == {"surgery", "cover"}
    assert await _found(client, world, date="gt2027-01-01") == {
        "cover"
    }  # only the open-ended one reaches past
    assert await _found(client, world, date="lt2026-02-01") == {"clinic"}
    assert await _found(client, world, date="le2026-03-15") == {"clinic", "cover"}
    assert await _found(client, world, date="sa2026-06-30T23:59:59Z") == {"surgery"}
    assert await _found(client, world, date="eb2026-07-01") == {"clinic"}
    assert await _found(client, world, date="ne2026") == {"cover"}
    assert "bare" not in await _found(
        client, world, date="ne2026"
    )  # no period -> no value -> no match


async def test_date_missing_and_malformed(client, world):
    assert await _found(client, world, **{"date:missing": "true"}) == {"bare"}
    assert await _found(client, world, **{"date:missing": "false"}) == ALL - {"bare"}
    assert (
        await client.get(BASE + "/", params={"date": "last-tuesday"})
    ).status_code == 400
    assert (
        await client.get(BASE + "/", params={"date:exact": "2026"})
    ).status_code == 400


# ── identifier ───────────────────────────────────────────────────────────────


async def test_identifier(client, world):
    assert await _found(client, world, identifier="S-1") == {"clinic"}
    assert await _found(client, world, identifier=f"{SCHED_IDS}|S-2") == {"surgery"}
    assert await _found(client, world, identifier=f"{SCHED_IDS}|") == {
        "clinic",
        "surgery",
    }
    assert await _found(client, world, identifier="|S-1") == set()
    assert await _found(
        client, world, **{"identifier:not": f"{SCHED_IDS}|S-1"}
    ) == ALL - {"clinic"}
    assert await _found(client, world, **{"identifier:missing": "true"}) == {
        "cover",
        "bare",
    }


async def test_identifier_of_type_and_text(client, world):
    v2 = "http://terminology.hl7.org/CodeSystem/v2-0203"
    assert await _found(client, world, **{"identifier:of-type": f"{v2}|SCH|S-1"}) == {
        "clinic"
    }
    assert (
        await _found(client, world, **{"identifier:of-type": f"{v2}|SCH|S-2"}) == set()
    )
    assert await _found(client, world, **{"identifier:text": "Schedule num"}) == {
        "clinic"
    }


# ── the three CodeableConcept token parameters ───────────────────────────────


@pytest.mark.parametrize(
    "param,system,code,expected",
    [
        ("service-category", CAT, "17", {"clinic"}),
        ("service-type", TYPE, "124", {"clinic", "surgery"}),
        ("specialty", SCT, "394579002", {"clinic"}),
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
    assert await _found(client, world, specialty="17") == set()
    assert await _found(client, world, **{"service-category": "394579002"}) == set()
    assert await _found(client, world, **{"service-type": "17"}) == set()


async def test_token_comma_or_text_and_missing(client, world):
    assert await _found(client, world, specialty="394579002,394801008") == {
        "clinic",
        "surgery",
    }
    assert await _found(client, world, **{"service-category:text": "General"}) == {
        "clinic"
    }  # display and concept text
    assert await _found(client, world, **{"service-category:text": "Locum"}) == {
        "cover"
    }  # text-only concept
    assert await _found(client, world, **{"specialty:text": "Ortho"}) == {"surgery"}
    assert await _found(client, world, **{"specialty:missing": "true"}) == {
        "cover",
        "bare",
    }
    assert await _found(client, world, **{"service-type:missing": "true"}) == {
        "cover",
        "bare",
    }


# ── actor (seven possible target types) ──────────────────────────────────────


async def test_actor_needs_a_type(client, world):
    """A bare id is ambiguous across seven types: R4 requires a type."""
    resp = await client.get(BASE + "/", params={"actor": str(world["prac"])})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    # ...which the `:Type` modifier supplies.
    assert await _found(
        client, world, **{"actor:Practitioner": str(world["prac"])}
    ) == {"clinic"}


async def test_actor_reference_forms_for_every_modeled_type(client, world):
    assert await _found(client, world, actor=f"Practitioner/{world['prac']}") == {
        "clinic"
    }
    assert await _found(client, world, actor=f"Location/{world['loc']}") == {"clinic"}
    assert await _found(client, world, actor=f"PractitionerRole/{world['role']}") == {
        "surgery"
    }
    assert await _found(client, world, actor=f"HealthcareService/{world['svc']}") == {
        "surgery"
    }
    assert await _found(client, world, **{"actor:Location": str(world["loc"])}) == {
        "clinic"
    }
    assert await _found(
        client, world, actor=f"Practitioner/{world['prac']},Location/{world['loc']}"
    ) == {"clinic"}
    assert await _found(
        client,
        world,
        actor=f"Practitioner/{world['prac']},HealthcareService/{world['svc']}",
    ) == {"clinic", "surgery"}


async def test_actor_the_type_is_part_of_the_match(client, world):
    """The same number under another type is a different actor."""
    assert await _found(client, world, actor=f"Location/{world['prac']}") == set()
    assert (
        await _found(client, world, **{"actor:Practitioner": str(world["loc"])})
        == set()
    )


async def test_actor_of_types_that_are_not_resources_here_still_search(client, world):
    assert await _found(client, world, actor="Patient/77") == {"cover"}
    assert await _found(client, world, actor="Patient/78") == set()
    assert await _found(client, world, **{"actor:Patient": "77"}) == {"cover"}
    assert (
        await _found(client, world, actor="Device/5") == set()
    )  # only its absolute URL was stored


async def test_actor_absolute_url_matches_raw_string_and_logical_identifier(
    client, world
):
    assert await _found(
        client, world, actor="https://other.example.org/fhir/Device/5"
    ) == {"cover"}
    assert (
        await _found(client, world, actor="https://other.example.org/fhir/Device/6")
        == set()
    )
    assert await _found(client, world, **{"actor:identifier": "urn:device|D-9"}) == {
        "cover"
    }
    assert (
        await _found(client, world, **{"actor:identifier": "urn:device|D-1"}) == set()
    )


async def test_actor_missing_and_rejected_type_modifier(client, world):
    assert await _found(client, world, **{"actor:missing": "true"}) == {
        "bare"
    }  # display-only: nothing to match
    assert await _found(client, world, **{"actor:missing": "false"}) == ALL - {"bare"}
    assert (
        await client.get(BASE + "/", params={"actor:Organization": "1"})
    ).status_code == 400
    assert (
        await client.get(BASE + "/", params={"actor:not": "Patient/77"})
    ).status_code == 400


async def test_actor_chaining_through_a_typed_actor(client, world):
    assert await _found(client, world, **{"actor:Practitioner.family": "Careful"}) == {
        "clinic"
    }
    assert (
        await _found(client, world, **{"actor:Practitioner.family": "Nobody"}) == set()
    )
    assert await _found(client, world, **{"actor:Location.name": "North"}) == {"clinic"}
    assert await _found(client, world, **{"actor:Location.address-city": "Boston"}) == {
        "clinic"
    }
    assert await _found(
        client, world, **{"actor:HealthcareService.name": "Cardiology"}
    ) == {"surgery"}
    assert await _found(client, world, **{"actor:PractitionerRole.active": "true"}) == {
        "surgery"
    }
    # The chain stays inside its type: a Location named like a Practitioner doesn't match.
    assert await _found(client, world, **{"actor:Practitioner.name": "North"}) == set()


async def test_actor_chaining_needs_a_supported_type(client, world):
    for key in ("actor.family", "actor:Patient.family", "actor:Device.manufacturer"):
        resp = await client.get(BASE + "/", params={key: "x"})
        assert resp.status_code == 400, key  # untyped, or not searchable on this server


# ── _include / _revinclude ───────────────────────────────────────────────────


async def test_include_actor_brings_in_every_modeled_actor(client, world):
    bundle = await _search(
        client, {"_id": str(world["clinic"]), "_include": "Schedule:actor"}
    )
    assert _ids(bundle) == {world["clinic"]}
    assert _included(bundle) == {
        ("Practitioner", str(world["prac"])),
        ("Location", str(world["loc"])),
    }
    both = await _search(
        client, {"_id": str(world["surgery"]), "_include": "Schedule:actor"}
    )
    assert _included(both) == {
        ("PractitionerRole", str(world["role"])),
        ("HealthcareService", str(world["svc"])),
    }


async def test_include_actor_narrowed_to_one_type(client, world):
    bundle = await _search(
        client, {"_id": str(world["clinic"]), "_include": "Schedule:actor:Location"}
    )
    assert _included(bundle) == {("Location", str(world["loc"]))}
    bundle = await _search(
        client,
        {"_id": str(world["clinic"]), "_include": "Schedule:actor:HealthcareService"},
    )
    assert _included(bundle) == set()


async def test_include_star_and_dedup(client, world):
    bundle = await _search(client, {"_include": "*"})
    assert _included(bundle) == {
        ("Practitioner", str(world["prac"])),
        ("Location", str(world["loc"])),
        ("PractitionerRole", str(world["role"])),
        ("HealthcareService", str(world["svc"])),
    }  # Patient / Device / logical actors resolve to nothing


async def test_unsupported_include_is_400(client, world):
    for value in (
        "Schedule:bogus",
        "Schedule:actor:Patient",
        "Patient:actor",
        "Schedule",
    ):
        assert (
            await client.get(BASE + "/", params={"_include": value})
        ).status_code == 400, value


async def test_revinclude_schedules_from_every_actor_resource(client, world):
    for path, key, kind in (
        ("practitioners", "prac", "clinic"),
        ("locations", "loc", "clinic"),
        ("practitioner-roles", "role", "surgery"),
        ("healthcare-services", "svc", "surgery"),
    ):
        bundle = await _search(
            client,
            {"_id": str(world[key]), "_revinclude": "Schedule:actor"},
            base=f"{API}/{path}",
        )
        assert _included(bundle) == {("Schedule", str(world[kind]))}, path
        entry = next(e for e in bundle["entry"] if e["search"]["mode"] == "include")
        assert entry["fullUrl"].endswith(f"/schedules/{world[kind]}"), path
    lonely = await create_practitioner(client, "Lonely", "Larry")
    none = await _search(
        client,
        {"_id": str(lonely), "_revinclude": "Schedule:actor"},
        base=f"{API}/practitioners",
    )
    assert _included(none) == set()


async def test_revinclude_matches_the_actor_type_not_just_the_number(client, world):
    """A Schedule whose *Patient* actor has number N must not be pulled in for
    a Location that happens to have id N."""
    loc = world["loc"]
    patient_schedule = await create_schedule(
        client, {"actor": [{"reference": f"Patient/{loc}"}]}
    )
    bundle = await _search(
        client,
        {"_id": str(loc), "_revinclude": "Schedule:actor"},
        base=f"{API}/locations",
    )
    assert _included(bundle) == {
        ("Schedule", str(world["clinic"]))
    }  # only the real Location actor
    assert str(patient_schedule) not in {i for _t, i in _included(bundle)}
    assert patient_schedule in _ids(await _search(client, {"actor": f"Patient/{loc}"}))


# ── _sort / paging / totals ──────────────────────────────────────────────────


async def test_sort(client, world):
    default = [int(r["id"]) for r in _matches(await _search(client))]
    assert default == sorted(default, reverse=True)
    assert [
        int(r["id"]) for r in _matches(await _search(client, {"_sort": "_id"}))
    ] == sorted(default)
    by_date = [int(r["id"]) for r in _matches(await _search(client, {"_sort": "date"}))]
    assert by_date[:3] == [
        world["clinic"],
        world["cover"],
        world["surgery"],
    ]  # Jan, Mar, Jul; no period last
    assert by_date[-1] == world["bare"]
    for name in (
        "active",
        "identifier",
        "actor",
        "service-category",
        "service-type",
        "specialty",
    ):
        assert (
            await client.get(BASE + "/", params={"_sort": name})
        ).status_code == 200, name


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
    # `comment` isn't a Σ element: the bare schedule has one to strip.
    resource = _matches(
        await _search(client, {"_id": str(world["bare"]), "_summary": "true"})
    )[0]
    assert "actor" in resource and "comment" not in resource
    assert any(t.get("code") == "SUBSETTED" for t in resource["meta"]["tag"])
    el = _matches(
        await _search(client, {"_id": str(world["bare"]), "_elements": "comment"})
    )[0]
    assert (
        el["comment"] == "no index" and "actor" in el
    )  # `actor` is mandatory (1..*) so it is kept
    text = _matches(
        await _search(client, {"_id": str(world["bare"]), "_summary": "text"})
    )[0]
    assert "actor" in text and "comment" not in text


# ── lenient / strict handling, rejected input ────────────────────────────────


async def test_unknown_parameter_ignored_with_outcome_or_400_when_strict(client, world):
    bundle = await _search(client, {"bogus": "x", "identifier": "S-1"})
    assert _ids(bundle) == {world["clinic"]}
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
        {"active:contains": "x"},
        {"specialty:exact": "x"},
        {"_lastUpdated": "notadate"},
        {"_count": "abc"},
        {"_query": "x"},
        {"specialty.name": "x"},  # token parameters can't be chained
    ):
        assert (await client.get(BASE + "/", params=params)).status_code == 400, params


# ── Bundle shape / POST _search ──────────────────────────────────────────────


async def test_bundle_shape(client, world):
    bundle = await _search(client, {"identifier": "S-1"})
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/schedules/{world['clinic']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "Schedule"


async def test_xml_only_accept_is_406_on_search(client):
    assert (
        await client.get(BASE + "/", headers={"Accept": "application/fhir+xml"})
    ).status_code == 406


async def test_post_search_form_encoded_and_combined_with_query_string(client, world):
    form = {"Content-Type": "application/x-www-form-urlencoded"}
    resp = await client.post(
        BASE + "/_search", content="specialty=394579002&active=true", headers=form
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["clinic"]}
    resp = await client.post(
        BASE + "/_search?active=true", content="specialty=394579002", headers=form
    )
    assert _ids(resp.json()) == {world["clinic"]}
    resp = await client.post(
        BASE + "/_search?active=false", content="specialty=394579002", headers=form
    )
    assert _ids(resp.json()) == set()
    resp = await client.post(
        BASE + "/_search", content="actor=Patient/77", headers=form
    )
    assert _ids(resp.json()) == {world["cover"]}
