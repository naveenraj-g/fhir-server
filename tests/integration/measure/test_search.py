"""FHIR R4 search over Measure (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/measure.html#search).

One block per search parameter - strings (`name`, `title`, `description`, `publisher`), the uri
`url`, dates (`date`, `effective`), tokens (`status`, `version`, `identifier`, `jurisdiction`,
`topic`, `context-type`, `context`), the quantity `context-quantity`, the two composites, and the
five relatedArtifact reference parameters (`composed-of`, `depends-on`, `derived-from`,
`predecessor`, `successor`, which read canonical URLs) - then chaining, `_include` /
`_revinclude`, result parameters, combination rules, lenient vs strict handling and POST _search.
"""

import pytest

from tests.integration.measure.support import (
    MEASURE_IDS,
    BASE,
    SCT,
    UCUM,
    URL,
    USAGE_CONTEXT_TYPE,
    V2_0203,
    measure_body,
    create_measure,
)

KEYS = ("a", "b", "c")
ALL = set(KEYS)
B_URL = "https://fhir-server.dev/fhir/Measure/gad-7"
LIB = "http://example.org/fhir/Library"
TOPIC = "http://terminology.hl7.org/CodeSystem/definition-topic"


def _ids(bundle: dict) -> set[int]:
    return {
        int(e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e["search"]["mode"] == "match"
    }


def _of_type(bundle: dict, rtype: str, mode: str) -> set[str]:
    return {
        e["resource"]["id"]
        for e in bundle.get("entry") or []
        if e["resource"]["resourceType"] == rtype and e["search"]["mode"] == mode
    }


def _context(code: str, **value) -> dict:
    return {"code": {"system": USAGE_CONTEXT_TYPE, "code": code}, **value}


@pytest.fixture
async def world(client) -> dict:
    """Three measures that differ on every searchable element.

    a - active, PHQ9, 2026, US, topic treatment; a focus context (SCT 35489007) and an age Range
        12-17; predecessor `c` (relative), composed-of Library/x|1.0, depends-on Library/dep and
        library Library/lib1.
    b - draft, GAD7, 2025, CA, topic assessment; a focus context (SCT 197480006) and an age
        Quantity 40; an open-ended effective period; derived-from an absolute base URL, successor
        `a` (relative).
    c - retired, nothing else (no url, name, version, dates, topics, contexts or artifacts).
    """
    c = await create_measure(client, measure_body(status="retired"))
    a_body = measure_body(
        status="active",
        url=URL,
        identifier=[
            {
                "system": MEASURE_IDS,
                "value": "AD-1",
                "type": {
                    "coding": [
                        {"system": V2_0203, "code": "ACSN", "display": "Accession ID"}
                    ],
                    "text": "Form number",
                },
            }
        ],
        version="1.0",
        name="PHQ9",
        title="Patient Health Activity",
        date="2026-01-15T10:00:00Z",
        publisher="Example Health",
        description="A nine-question depression screen",
        useContext=[
            _context(
                "focus",
                valueCodeableConcept={
                    "coding": [
                        {"system": SCT, "code": "35489007", "display": "Depression"}
                    ],
                    "text": "Mood disorder",
                },
            ),
            _context(
                "age",
                valueRange={
                    "low": {"value": 12, "system": UCUM, "code": "a"},
                    "high": {"value": 17, "system": UCUM, "code": "a"},
                },
            ),
        ],
        jurisdiction=[{"coding": [{"system": "urn:iso:std:iso:3166", "code": "US"}]}],
        topic=[{"coding": [{"system": TOPIC, "code": "treatment"}]}],
        effectivePeriod={"start": "2026-01-01", "end": "2026-12-31"},
        relatedArtifact=[
            {"type": "predecessor", "resource": f"Measure/{c}"},
            {"type": "composed-of", "resource": f"{LIB}/x|1.0"},
            {"type": "depends-on", "resource": f"{LIB}/dep"},
            {"type": "documentation", "resource": f"{LIB}/doc"},
        ],
        library=[f"{LIB}/lib1"],
    )
    a = await create_measure(client, a_body)
    b_body = measure_body(
        status="draft",
        url=B_URL,
        identifier=[{"system": "urn:other", "value": "GAD-7"}],
        version="2.0",
        name="GAD7",
        title="Generalized Anxiety Disorder",
        date="2025-06-01",
        publisher="Other Org",
        description="A seven-question anxiety screen",
        useContext=[
            _context(
                "focus",
                valueCodeableConcept={
                    "coding": [
                        {"system": SCT, "code": "197480006", "display": "Anxiety"}
                    ]
                },
            ),
            _context(
                "age",
                valueQuantity={
                    "value": 40,
                    "unit": "years",
                    "system": UCUM,
                    "code": "a",
                },
            ),
        ],
        jurisdiction=[{"coding": [{"system": "urn:iso:std:iso:3166", "code": "CA"}]}],
        topic=[{"coding": [{"system": TOPIC, "code": "assessment"}]}],
        effectivePeriod={"start": "2025-01-01"},
        relatedArtifact=[
            {
                "type": "derived-from",
                "resource": "http://example.org/fhir/Measure/base",
            },
            {"type": "successor", "resource": f"Measure/{a}"},
        ],
    )
    b = await create_measure(client, b_body)
    return {"a": a, "b": b, "c": c}


async def _search(client, **params) -> dict:
    resp = await client.get(BASE + "/", params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _keys(client, world, **params) -> set[str]:
    by_id = {world[k]: k for k in KEYS}
    return {by_id[i] for i in _ids(await _search(client, **params))}


async def _status(client, **params) -> int:
    return (await client.get(BASE + "/", params=params)).status_code


# -- _id / _lastUpdated ---------------------------------------------------------------------


async def test_id(client, world):
    assert await _keys(client, world, _id=str(world["a"])) == {"a"}
    assert await _keys(client, world, _id=f"{world['a']},{world['c']}") == {"a", "c"}
    assert await _keys(client, world, _id="999999") == set()
    assert await _keys(client, world, **{"_id:not": str(world["a"])}) == {"b", "c"}


async def test_last_updated(client, world):
    assert await _keys(client, world, _lastUpdated="ge2000-01-01") == ALL
    assert await _keys(client, world, _lastUpdated="lt2000-01-01") == set()


# -- strings: name / title / description / publisher ----------------------------------------


async def test_name_is_starts_with_and_case_insensitive(client, world):
    assert await _keys(client, world, name="phq") == {"a"}
    assert await _keys(client, world, name="GAD") == {"b"}
    assert await _keys(client, world, name="9") == set()  # not a prefix of PHQ9
    assert await _keys(client, world, **{"name:contains": "q9"}) == {"a"}
    assert await _keys(client, world, **{"name:exact": "PHQ9"}) == {"a"}
    assert await _keys(client, world, **{"name:exact": "phq9"}) == set()


async def test_title(client, world):
    assert await _keys(client, world, title="patient health") == {"a"}
    assert await _keys(client, world, **{"title:contains": "disorder"}) == {"b"}
    assert await _keys(
        client, world, **{"title:exact": "Generalized Anxiety Disorder"}
    ) == {"b"}


async def test_description(client, world):
    assert await _keys(client, world, description="a nine") == {"a"}
    assert await _keys(client, world, **{"description:contains": "screen"}) == {
        "a",
        "b",
    }


async def test_publisher(client, world):
    assert await _keys(client, world, publisher="example") == {"a"}
    assert await _keys(client, world, publisher="other") == {"b"}


async def test_string_missing(client, world):
    assert await _keys(client, world, **{"name:missing": "true"}) == {"c"}
    assert await _keys(client, world, **{"name:missing": "false"}) == {"a", "b"}
    assert await _keys(client, world, **{"publisher:missing": "true"}) == {"c"}


# -- uris: url / definition -----------------------------------------------------------------


async def test_url_is_exact_and_case_sensitive(client, world):
    assert await _keys(client, world, url=URL) == {"a"}
    assert await _keys(client, world, url=URL.upper()) == set()
    assert await _keys(client, world, url=f"{URL},{B_URL}") == {"a", "b"}


async def test_url_below_and_above(client, world):
    assert await _keys(
        client,
        world,
        **{"url:below": "https://fhir-server.dev/fhir/Measure"},
    ) == {"a", "b"}
    assert await _keys(client, world, **{"url:above": f"{URL}/extra"}) == {"a"}
    assert await _keys(client, world, **{"url:below": f"{URL}/extra"}) == set()


async def test_url_missing(client, world):
    assert await _keys(client, world, **{"url:missing": "true"}) == {"c"}


# -- dates: date / effective ----------------------------------------------------------------


async def test_date_prefixes_and_partial_precision(client, world):
    assert await _keys(client, world, date="2026") == {"a"}
    assert await _keys(client, world, date="2026-01") == {"a"}
    assert await _keys(client, world, date="2025") == {"b"}
    assert await _keys(client, world, date="ge2026-01-01") == {"a"}
    assert await _keys(client, world, date="lt2026-01-01") == {"b"}
    assert await _keys(client, world, date="gt2025-12-31") == {"a"}
    assert await _keys(client, world, date="2026-02") == set()
    assert await _keys(client, world, **{"date:missing": "true"}) == {"c"}


async def test_effective_is_a_period_search(client, world):
    # a covers 2026; b starts 2025 and never ends; c has none.
    assert await _keys(client, world, effective="ge2026-06-01") == {"a", "b"}
    assert await _keys(client, world, effective="lt2025-06-01") == {"b"}
    assert await _keys(client, world, effective="gt2027-01-01") == {"b"}
    assert await _keys(client, world, effective="sa2024-12-31") == {"a", "b"}
    assert await _keys(client, world, effective="eb2027-01-01") == {"a"}  # b never ends
    assert await _keys(client, world, **{"effective:missing": "true"}) == {"c"}


# -- tokens ---------------------------------------------------------------------------------


async def test_status(client, world):
    assert await _keys(client, world, status="active") == {"a"}
    assert await _keys(client, world, status="active,draft") == {"a", "b"}
    assert await _keys(
        client, world, status="http://hl7.org/fhir/publication-status|retired"
    ) == {"c"}
    assert await _keys(client, world, status="http://wrong|active") == set()
    assert await _keys(client, world, status="|active") == set()
    assert await _keys(client, world, status="nonsense") == set()
    assert await _keys(client, world, **{"status:not": "active"}) == {"b", "c"}


async def test_version_is_a_token_over_a_string(client, world):
    assert await _keys(client, world, version="1.0") == {"a"}
    assert await _keys(client, world, version="2.0,1.0") == {"a", "b"}
    assert await _keys(client, world, version="1") == set()  # exact, not a prefix
    assert (
        await _keys(client, world, version="http://x|1.0") == set()
    )  # a string has no system
    assert await _keys(client, world, **{"version:missing": "true"}) == {"c"}


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="AD-1") == {"a"}
    assert await _keys(client, world, identifier=f"{MEASURE_IDS}|AD-1") == {"a"}
    assert await _keys(client, world, identifier="urn:other|") == {"b"}
    assert await _keys(client, world, identifier="|AD-1") == set()
    assert await _keys(client, world, **{"identifier:text": "form number"}) == {"a"}
    assert await _keys(client, world, **{"identifier:text": "accession"}) == {"a"}
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|ACSN|AD-1"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|ACSN|GAD-7"})
        == set()
    )
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {"c"}


async def test_jurisdiction(client, world):
    assert await _keys(client, world, jurisdiction="urn:iso:std:iso:3166|US") == {"a"}
    assert await _keys(client, world, jurisdiction="CA") == {"b"}
    assert await _keys(client, world, jurisdiction="urn:iso:std:iso:3166|") == {
        "a",
        "b",
    }
    assert await _keys(client, world, **{"jurisdiction:missing": "true"}) == {"c"}


# -- topic ----------------------------------------------------------------------------------


async def test_topic(client, world):
    assert await _keys(client, world, topic=f"{TOPIC}|treatment") == {"a"}
    assert await _keys(client, world, topic="assessment") == {"b"}
    assert await _keys(client, world, topic=f"{TOPIC}|") == {"a", "b"}
    assert await _keys(client, world, **{"topic:missing": "true"}) == {"c"}


# -- relatedArtifact reference parameters (canonical URLs) ----------------------------------


async def test_composed_of_matches_a_versioned_canonical_by_url_too(client, world):
    assert await _keys(client, world, **{"composed-of": f"{LIB}/x|1.0"}) == {"a"}
    assert await _keys(client, world, **{"composed-of": f"{LIB}/x"}) == {
        "a"
    }  # unversioned
    assert await _keys(client, world, **{"composed-of": f"{LIB}/x|2.0"}) == set()
    assert await _keys(client, world, **{"composed-of:missing": "true"}) == {"b", "c"}


async def test_depends_on_reads_related_artifacts_and_library(client, world):
    assert await _keys(client, world, **{"depends-on": f"{LIB}/dep"}) == {"a"}
    assert await _keys(client, world, **{"depends-on": f"{LIB}/lib1"}) == {
        "a"
    }  # `library`
    assert (
        await _keys(client, world, **{"depends-on": f"{LIB}/doc"}) == set()
    )  # documentation
    assert await _keys(client, world, **{"depends-on:missing": "true"}) == {"b", "c"}


async def test_derived_from_predecessor_and_successor(client, world):
    base = "http://example.org/fhir/Measure/base"
    assert await _keys(client, world, **{"derived-from": base}) == {"b"}
    assert await _keys(client, world, predecessor=f"Measure/{world['c']}") == {"a"}
    assert await _keys(client, world, successor=f"Measure/{world['a']}") == {"b"}
    assert await _keys(client, world, **{"successor:Measure": str(world["a"])}) == {"b"}
    assert await _keys(client, world, predecessor=f"Library/{world['c']}") == set()
    assert await _keys(client, world, **{"predecessor:missing": "true"}) == {"b", "c"}


async def test_reference_by_bare_id_is_ambiguous(client, world):
    for name in (
        "composed-of",
        "depends-on",
        "derived-from",
        "predecessor",
        "successor",
    ):
        assert await _status(client, **{name: str(world["a"])}) == 400, name


async def test_chain_through_a_relative_canonical(client, world):
    assert await _keys(client, world, **{"predecessor:Measure.status": "retired"}) == {
        "a"
    }
    assert await _keys(client, world, **{"successor:Measure.name": "PHQ9"}) == {"b"}


async def test_bad_chains_are_400(client, world):
    assert (
        await _status(client, **{"predecessor.status": "x"}) == 400
    )  # untyped Reference(Any)
    assert await _status(client, **{"predecessor:Measure.nonsense": "x"}) == 400
    assert await _status(client, **{"status.x": "y"}) == 400


async def test_include_and_revinclude(client, world):
    bundle = await _search(client, _id=str(world["a"]), _include="Measure:predecessor")
    assert _of_type(bundle, "Measure", "include") == {str(world["c"])}
    bundle = await _search(client, _id=str(world["b"]), _include="Measure:successor")
    assert _of_type(bundle, "Measure", "include") == {str(world["a"])}
    bundle = await _search(
        client, _id=str(world["c"]), _revinclude="Measure:predecessor"
    )
    assert _of_type(bundle, "Measure", "include") == {str(world["a"])}
    bundle = await _search(client, _id=str(world["a"]), _revinclude="Measure:successor")
    assert _of_type(bundle, "Measure", "include") == {str(world["b"])}


async def test_context_type_and_context(client, world):
    focus = f"{USAGE_CONTEXT_TYPE}|focus"
    assert await _keys(client, world, **{"context-type": focus}) == {"a", "b"}
    assert await _keys(client, world, **{"context-type": "age"}) == {"a", "b"}
    assert await _keys(client, world, **{"context-type": "venue"}) == set()
    assert await _keys(client, world, context=f"{SCT}|35489007") == {"a"}
    assert await _keys(client, world, context="197480006") == {"b"}
    assert await _keys(client, world, **{"context:text": "mood"}) == {"a"}
    assert await _keys(client, world, **{"context:text": "anxiety"}) == {
        "b"
    }  # the display
    assert await _keys(client, world, **{"context-type:missing": "true"}) == {"c"}
    assert await _keys(client, world, **{"context:missing": "true"}) == {"c"}


# -- quantity: context-quantity -------------------------------------------------------------


async def test_context_quantity_over_a_quantity_or_a_range(client, world):
    # a: Range 12..17 years; b: Quantity 40 years.
    assert await _keys(client, world, **{"context-quantity": f"gt10|{UCUM}|a"}) == {
        "a",
        "b",
    }
    assert await _keys(client, world, **{"context-quantity": f"gt20|{UCUM}|a"}) == {"b"}
    assert await _keys(client, world, **{"context-quantity": f"lt13|{UCUM}|a"}) == {"a"}
    assert await _keys(client, world, **{"context-quantity": f"40|{UCUM}|a"}) == {"b"}
    assert await _keys(client, world, **{"context-quantity": f"ge17|{UCUM}|a"}) == {
        "a",
        "b",
    }
    assert (
        await _keys(client, world, **{"context-quantity": f"gt100|{UCUM}|a"}) == set()
    )
    assert (
        await _keys(client, world, **{"context-quantity": f"gt10|{UCUM}|mg"}) == set()
    )
    assert await _keys(client, world, **{"context-quantity:missing": "true"}) == {"c"}


# -- composites -----------------------------------------------------------------------------


async def test_context_type_value_pairs_within_one_use_context(client, world):
    assert await _keys(
        client, world, **{"context-type-value": f"focus${SCT}|35489007"}
    ) == {"a"}
    assert await _keys(client, world, **{"context-type-value": "focus$197480006"}) == {
        "b"
    }
    # a's focus context holds SCT 35489007; its age context holds no concept at all, so a code of
    # one useContext never pairs with the value of another.
    assert await _keys(client, world, **{"context-type-value": "age$35489007"}) == set()
    assert await _keys(
        client, world, **{"context-type-value": "focus$35489007,focus$197480006"}
    ) == {"a", "b"}


async def test_context_type_quantity_pairs_within_one_use_context(client, world):
    assert await _keys(
        client, world, **{"context-type-quantity": f"age$gt30|{UCUM}|a"}
    ) == {"b"}
    assert await _keys(
        client, world, **{"context-type-quantity": f"age$lt13|{UCUM}|a"}
    ) == {"a"}
    # The focus context carries a concept, not a quantity.
    assert (
        await _keys(client, world, **{"context-type-quantity": f"focus$gt0|{UCUM}|a"})
        == set()
    )


async def test_composite_malformed_is_400(client, world):
    for name, value in (
        ("context-type-value", "focus"),
        ("context-type-value", "focus$a$b"),
        ("context-type-value", "$x"),
        ("context-type-quantity", "age"),
        ("context-type-quantity", "age$notanumber"),
    ):
        assert await _status(client, **{name: value}) == 400, (name, value)
    assert await _status(client, **{"context-type-value:text": "focus$x"}) == 400


# -- _sort / _count / _offset / _total ------------------------------------------------------


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "_id",
        "_lastUpdated",
        "composed-of",
        "context",
        "context-quantity",
        "context-type",
        "date",
        "depends-on",
        "derived-from",
        "description",
        "effective",
        "identifier",
        "jurisdiction",
        "name",
        "predecessor",
        "publisher",
        "status",
        "successor",
        "title",
        "topic",
        "url",
        "version",
    ):
        assert (await _search(client, _sort=key))["total"] == 3, key
        assert (await _search(client, _sort=f"-{key}"))["total"] == 3, key


async def test_sort_by_name_orders_the_resources(client, world):
    got = [
        e["resource"].get("name")
        for e in (await _search(client, _sort="name"))["entry"]
    ]
    assert [n for n in got if n] == ["GAD7", "PHQ9"]
    got = [
        e["resource"].get("name")
        for e in (await _search(client, _sort="-name"))["entry"]
    ]
    assert [n for n in got if n] == ["PHQ9", "GAD7"]


async def test_default_sort_is_newest_first(client, world):
    got = [int(e["resource"]["id"]) for e in (await _search(client))["entry"]]
    assert got == sorted(got, reverse=True)


async def test_paging_and_total(client, world):
    page = await _search(client, _count=2, _sort="_id")
    assert page["total"] == 3 and len(page["entry"]) == 2
    assert any(link["relation"] == "next" for link in page["link"])
    nxt = await _search(client, _count=2, _offset=2, _sort="_id")
    assert len(nxt["entry"]) == 1
    assert "entry" not in await _search(client, _count=0)
    assert "total" not in await _search(client, _total="none")


async def test_summary_count_and_elements(client, world):
    assert (await _search(client, _summary="count"))["total"] == 3
    resource = (await _search(client, _elements="status", _id=str(world["a"])))[
        "entry"
    ][0]["resource"]
    assert resource["status"] == "active"
    assert "relatedArtifact" not in resource and "title" not in resource


# -- combination, errors --------------------------------------------------------------------


async def test_and_or_combination(client, world):
    assert await _keys(client, world, status="active", name="phq") == {"a"}
    assert await _keys(client, world, status="active", name="gad") == set()
    assert await _keys(client, world, name="phq,gad") == {"a", "b"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, date="notadate") == 400
    assert await _status(client, effective="notadate") == 400
    assert await _status(client, **{"status:text": "x"}) == 400
    assert await _status(client, **{"name:below": "x"}) == 400
    assert await _status(client, **{"context-quantity": "abc"}) == 400
    assert await _status(client, **{"identifier:below": "x"}) == 400


async def test_unknown_param_lenient_vs_strict(client, world):
    lenient = await client.get(BASE + "/", params={"nonsense": "1"})
    assert lenient.status_code == 200
    assert any(e["search"]["mode"] == "outcome" for e in lenient.json()["entry"])
    strict = await client.get(
        BASE + "/", params={"nonsense": "1"}, headers={"Prefer": "handling=strict"}
    )
    assert strict.status_code == 400


async def test_elements_without_a_search_parameter_are_unknown(client, world):
    for name in (
        "kind",
        "code",
        "intent",
        "priority",
        "subject-type",
        "definition",
        "library",
    ):
        strict = await client.get(
            BASE + "/", params={name: "x"}, headers={"Prefer": "handling=strict"}
        )
        assert strict.status_code == 400, name


async def test_query_param_refused(client, world):
    assert await _status(client, _query="x") == 400


# -- POST _search / Bundle shape ------------------------------------------------------------


async def test_post_search_form_encoded(client, world):
    resp = await client.post(BASE + "/_search", data={"status": "draft", "name": "gad"})
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, identifier="AD-1")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/measures/{world['a']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "Measure"
    assert entry["resource"]["relatedArtifact"][0]["type"] == "predecessor"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
