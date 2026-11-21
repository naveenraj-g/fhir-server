"""FHIR R4 search over Practitioner (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/practitioner.html#search).

One block per search parameter, then the result parameters (`_sort`,
`_count`/`_offset`/`_total`, `_summary`/`_elements`), combination rules
(OR / AND / escaping), lenient vs strict handling, the Bundle's
links/fullUrl/search.mode and POST _search.
"""

import pytest

from app.core.config import settings
from tests.integration.practitioner.support import BASE, create_practitioner

NPI = "http://hl7.org/fhir/sid/us-npi"


@pytest.fixture
async def people(client):
    """Four practitioners with distinct, searchable values. Returns {key: id}."""
    ids = {}
    ids["adam"] = await create_practitioner(
        client,
        {
            "active": True,
            "gender": "male",
            "identifier": [
                {
                    "system": NPI,
                    "value": "1111",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "NPI",
                            }
                        ],
                        "text": "National Provider",
                    },
                }
            ],
            "name": [
                {"family": "Careful", "given": ["Adam", "Quincy"], "prefix": ["Dr"]}
            ],
            "telecom": [
                {"system": "phone", "value": "555-0001", "use": "work"},
                {"system": "email", "value": "adam@example.org"},
            ],
            "address": [
                {
                    "use": "work",
                    "line": ["534 Erewhon St"],
                    "city": "Boston",
                    "state": "MA",
                    "postalCode": "02110",
                    "country": "US",
                }
            ],
            "communication": [{"coding": [{"code": "en", "display": "English"}]}],
        },
    )
    ids["beth"] = await create_practitioner(
        client,
        {
            "active": False,
            "gender": "female",
            "identifier": [{"system": NPI, "value": "2222"}],
            "name": [
                {"family": "Zimmermann", "given": ["Beth"], "suffix": ["PhD"]},
                {"family": "Alt", "given": ["Bette"]},
            ],
            "telecom": [{"system": "phone", "value": "555-0002", "use": "home"}],
            "address": [
                {
                    "use": "home",
                    "city": "Austin",
                    "state": "TX",
                    "postalCode": "73301",
                    "country": "US",
                }
            ],
            "communication": [{"coding": [{"code": "es", "display": "Spanish"}]}],
        },
    )
    ids["cara"] = await create_practitioner(
        client,
        {
            "gender": "other",
            "name": [
                {
                    "text": "Cara Müller-Lüdenscheid",
                    "family": "Müller",
                    "given": ["Cara"],
                }
            ],
            "address": [{"city": "München", "country": "DE"}],
        },
    )
    ids["dan"] = await create_practitioner(
        client, {"name": [{"family": "Dunn", "given": ["Dan"]}]}
    )
    return ids


async def _search(client, params=None, headers=None) -> dict:
    resp = await client.get(BASE + "/", params=params or {}, headers=headers or {})
    assert resp.status_code == 200, resp.text
    return resp.json()


def _ids(bundle: dict) -> set[int]:
    return {
        int(e["resource"]["id"])
        for e in bundle.get("entry") or []
        if e.get("search", {}).get("mode") == "match"
    }


async def _found(client, people, **params) -> set[str]:
    by_id = {v: k for k, v in people.items()}
    return {by_id[i] for i in _ids(await _search(client, params))}


# ── _id / _lastUpdated ───────────────────────────────────────────────────────


async def test_id(client, people):
    assert await _found(client, people, _id=str(people["beth"])) == {"beth"}
    assert await _found(client, people, _id="999999") == set()
    assert await _found(
        client, people, **{"_id": f"{people['beth']},{people['dan']}"}
    ) == {"beth", "dan"}
    assert await _found(client, people, **{"_id:not": str(people["beth"])}) == {
        "adam",
        "cara",
        "dan",
    }


async def test_last_updated(client, people):
    assert await _found(client, people, _lastUpdated="ge2000-01-01") == set(people)
    assert await _found(client, people, _lastUpdated="lt2000-01-01") == set()


# ── active / gender ──────────────────────────────────────────────────────────


async def test_active(client, people):
    assert await _found(client, people, active="true") == {"adam"}
    assert await _found(client, people, active="false") == {"beth"}
    # :not includes the records where active isn't recorded at all.
    assert await _found(client, people, **{"active:not": "true"}) == {
        "beth",
        "cara",
        "dan",
    }
    assert (await client.get(BASE + "/", params={"active": "maybe"})).status_code == 400


async def test_gender(client, people):
    assert await _found(client, people, gender="male") == {"adam"}
    assert await _found(
        client, people, gender="http://hl7.org/fhir/administrative-gender|female"
    ) == {"beth"}
    assert await _found(client, people, **{"gender": "male,other"}) == {"adam", "cara"}
    assert await _found(client, people, **{"gender:not": "male"}) == {
        "beth",
        "cara",
        "dan",
    }
    assert await _found(client, people, gender="robot") == set()
    assert await _found(client, people, gender="urn:other|male") == set()
    assert await _found(client, people, **{"gender:missing": "true"}) == {"dan"}


# ── names ────────────────────────────────────────────────────────────────────


async def test_family_is_case_and_accent_insensitive_starts_with(client, people):
    assert await _found(client, people, family="care") == {"adam"}
    assert await _found(client, people, family="CAREFUL") == {"adam"}
    assert await _found(client, people, family="muller") == {"cara"}  # ü -> u
    assert await _found(client, people, family="areful") == set()  # not a prefix


async def test_family_modifiers(client, people):
    assert await _found(client, people, **{"family:contains": "areful"}) == {"adam"}
    assert await _found(client, people, **{"family:exact": "Careful"}) == {"adam"}
    assert await _found(client, people, **{"family:exact": "careful"}) == set()
    assert await _found(client, people, **{"family:missing": "true"}) == set()


async def test_family_matches_any_of_several_names(client, people):
    assert await _found(client, people, family="Alt") == {"beth"}
    assert await _found(client, people, family="Zimm") == {"beth"}


async def test_given_matches_each_given_name_on_its_own(client, people):
    assert await _found(client, people, given="Quin") == {"adam"}
    assert await _found(client, people, given="adam") == {"adam"}
    assert await _found(client, people, **{"given:exact": "Bette"}) == {"beth"}


async def test_name_matches_any_string_field_of_the_humanname(client, people):
    assert await _found(client, people, name="Careful") == {"adam"}
    assert await _found(client, people, name="Quincy") == {"adam"}  # given
    assert await _found(client, people, name="Dr") == {"adam"}  # prefix
    assert await _found(client, people, name="PhD") == {"beth"}  # suffix
    assert await _found(client, people, name="Cara Mül") == {"cara"}  # text
    assert await _found(client, people, **{"name:contains": "ller"}) == {"cara"}
    assert await _found(client, people, **{"name:contains": "mann"}) == {"beth"}


async def test_phonetic(client, people):
    assert await _found(client, people, phonetic="Carefull") == {"adam"}  # Soundex C614
    assert (
        await _found(client, people, phonetic="Karefull") == set()
    )  # first letter must match
    assert await _found(client, people, phonetic="Dunne") == {"dan"}
    assert await _found(client, people, phonetic="Qxyz") == set()
    assert await _found(client, people, phonetic="") == set(
        people
    )  # R4: a parameter with no value is ignored


# ── identifier ───────────────────────────────────────────────────────────────


async def test_identifier(client, people):
    assert await _found(client, people, identifier="1111") == {"adam"}
    assert await _found(client, people, identifier=f"{NPI}|2222") == {"beth"}
    assert await _found(client, people, identifier=f"{NPI}|") == {"adam", "beth"}
    assert await _found(client, people, identifier="|1111") == set()  # has a system
    assert await _found(client, people, **{"identifier:not": f"{NPI}|1111"}) == {
        "beth",
        "cara",
        "dan",
    }
    assert await _found(client, people, **{"identifier:missing": "true"}) == {
        "cara",
        "dan",
    }


async def test_identifier_of_type_and_text(client, people):
    v2 = "http://terminology.hl7.org/CodeSystem/v2-0203"
    assert await _found(client, people, **{"identifier:of-type": f"{v2}|NPI|1111"}) == {
        "adam"
    }
    assert (
        await _found(client, people, **{"identifier:of-type": f"{v2}|NPI|2222"})
        == set()
    )
    assert await _found(client, people, **{"identifier:text": "National"}) == {"adam"}


# ── telecom / phone / email ──────────────────────────────────────────────────


async def test_telecom_phone_email(client, people):
    assert await _found(client, people, telecom="555-0001") == {"adam"}
    assert await _found(client, people, phone="555-0002") == {"beth"}
    assert await _found(client, people, email="adam@example.org") == {"adam"}
    # phone/email only look at ContactPoints of their own system.
    assert await _found(client, people, email="555-0001") == set()
    assert await _found(client, people, phone="adam@example.org") == set()
    # `use|value`: the system part of a ContactPoint token is its use.
    assert await _found(client, people, telecom="work|555-0001") == {"adam"}
    assert await _found(client, people, telecom="home|555-0001") == set()
    assert await _found(client, people, **{"phone:missing": "true"}) == {"cara", "dan"}
    assert await _found(client, people, **{"phone:not": "555-0001"}) == {
        "beth",
        "cara",
        "dan",
    }


# ── address ──────────────────────────────────────────────────────────────────


async def test_address_matches_any_part(client, people):
    assert await _found(client, people, address="534 Erewhon") == {
        "adam"
    }  # line (starts-with)
    assert (
        await _found(client, people, address="Erewhon") == set()
    )  # not a prefix of the line
    assert await _found(client, people, **{"address:contains": "Erewhon"}) == {"adam"}
    assert await _found(client, people, address="Austin") == {"beth"}  # city
    assert await _found(client, people, address="TX") == {"beth"}  # state
    assert await _found(client, people, address="02110") == {"adam"}  # postal code
    assert await _found(client, people, address="muenchen") == set()
    assert await _found(client, people, address="munchen") == {
        "cara"
    }  # accent-insensitive


async def test_address_parts(client, people):
    assert await _found(client, people, **{"address-city": "bos"}) == {"adam"}
    assert await _found(client, people, **{"address-state": "tx"}) == {"beth"}
    assert await _found(client, people, **{"address-postalcode": "73301"}) == {"beth"}
    assert await _found(client, people, **{"address-country": "us"}) == {"adam", "beth"}
    assert await _found(client, people, **{"address-country:exact": "us"}) == set()
    assert await _found(client, people, **{"address-use": "home"}) == {"beth"}
    assert await _found(client, people, **{"address-use:not": "home"}) == {
        "adam",
        "cara",
        "dan",
    }
    assert await _found(client, people, **{"address-city:missing": "true"}) == {"dan"}


# ── communication ────────────────────────────────────────────────────────────


async def test_communication(client, people):
    assert await _found(client, people, communication="en") == {"adam"}
    assert await _found(client, people, communication="en,es") == {"adam", "beth"}
    assert await _found(client, people, **{"communication:text": "Span"}) == {"beth"}
    assert await _found(client, people, **{"communication:missing": "true"}) == {
        "cara",
        "dan",
    }


# ── combination rules ────────────────────────────────────────────────────────


async def test_comma_is_or_and_repeat_is_and(client, people):
    assert await _found(client, people, family="Careful,Dunn") == {"adam", "dan"}
    resp = await client.get(BASE + "/", params=[("given", "Adam"), ("given", "Quincy")])
    assert _ids(resp.json()) == {people["adam"]}  # both given names -> AND
    resp = await client.get(BASE + "/", params=[("given", "Adam"), ("given", "Beth")])
    assert _ids(resp.json()) == set()


async def test_different_parameters_and_together(client, people):
    assert await _found(
        client, people, gender="male", **{"address-city": "Boston"}
    ) == {"adam"}
    assert (
        await _found(client, people, gender="female", **{"address-city": "Boston"})
        == set()
    )


async def test_escaped_comma_is_literal(client, people):
    assert await _found(client, people, family="Careful\\,Dunn") == set()


# ── _sort / paging / totals ──────────────────────────────────────────────────


async def test_sort_by_family(client, people):
    asc = await _search(client, {"_sort": "family"})
    order = [int(e["resource"]["id"]) for e in asc["entry"]]
    assert order == [
        people[k] for k in ("beth", "adam", "dan", "cara")
    ]  # Alt, Careful, Dunn, Müller
    desc = await _search(client, {"_sort": "-family"})
    ids_desc = [int(e["resource"]["id"]) for e in desc["entry"]]
    assert ids_desc[:1] == [people["beth"]]  # Zimmermann is the largest family name


async def test_sort_by_id_default_is_newest_first(client, people):
    default = [int(e["resource"]["id"]) for e in (await _search(client))["entry"]]
    assert default == sorted(people.values(), reverse=True)
    asc = [
        int(e["resource"]["id"])
        for e in (await _search(client, {"_sort": "_id"}))["entry"]
    ]
    assert asc == sorted(people.values())


async def test_unsupported_sort_is_rejected(client, people):
    assert (await client.get(BASE + "/", params={"_sort": "bogus"})).status_code == 400
    assert (await client.get(BASE + "/", params={"_sort": "given"})).status_code == 400


async def test_count_offset_total_and_links(client, people):
    page1 = await _search(client, {"_count": "2", "_sort": "_id"})
    assert page1["total"] == 4
    assert len(page1["entry"]) == 2
    rels = {link["relation"] for link in page1["link"]}
    assert {"self", "first", "next", "last"} <= rels
    page2 = await _search(client, {"_count": "2", "_offset": "2", "_sort": "_id"})
    assert _ids(page1).isdisjoint(_ids(page2))
    assert "next" not in {link["relation"] for link in page2["link"]}
    assert "previous" in {link["relation"] for link in page2["link"]}


async def test_count_is_capped_and_zero_means_count_only(client, people):
    capped = await _search(client, {"_count": str(settings.pagination.max_limit + 500)})
    assert f"_count={settings.pagination.max_limit}" in next(
        link["url"] for link in capped["link"] if link["relation"] == "self"
    )
    only = await _search(client, {"_count": "0"})
    assert only["total"] == 4
    assert "entry" not in only


async def test_total_none_omits_total(client, people):
    assert "total" not in await _search(client, {"_total": "none"})


async def test_summary_and_elements(client, people):
    data = await _search(client, {"_id": str(people["adam"]), "_summary": "true"})
    resource = data["entry"][0]["resource"]
    assert "name" in resource and "communication" not in resource
    assert any(t.get("code") == "SUBSETTED" for t in resource["meta"]["tag"])
    el = (await _search(client, {"_id": str(people["adam"]), "_elements": "gender"}))[
        "entry"
    ][0]["resource"]
    assert el["gender"] == "male" and "name" not in el


# ── lenient / strict handling, rejected input ────────────────────────────────


async def test_unknown_parameter_is_ignored_with_outcome(client, people):
    bundle = await _search(client, {"bogus": "x", "family": "Careful"})
    assert _ids(bundle) == {people["adam"]}
    outcome = [e for e in bundle["entry"] if e["search"]["mode"] == "outcome"]
    assert outcome and outcome[0]["resource"]["resourceType"] == "OperationOutcome"


async def test_unknown_parameter_is_400_when_strict(client, people):
    resp = await client.get(
        BASE + "/", params={"bogus": "x"}, headers={"Prefer": "handling=strict"}
    )
    assert resp.status_code == 400
    assert resp.json()["resourceType"] == "OperationOutcome"


async def test_unsupported_common_parameters_are_ignored_not_errors(client, people):
    for name in ("_tag", "_profile", "_has", "_text", "_filter"):
        resp = await client.get(BASE + "/", params={name: "x"})
        assert resp.status_code == 200, (name, resp.text)


async def test_bad_modifier_and_malformed_value_are_400(client, people):
    for params in (
        {"family:bogus": "x"},
        {"gender:contains": "x"},
        {"_lastUpdated": "notadate"},
        {"_count": "abc"},
        {"_query": "x"},
    ):
        assert (await client.get(BASE + "/", params=params)).status_code == 400, params


async def test_chaining_is_rejected_because_practitioner_has_no_reference_params(
    client, people
):
    assert (
        await client.get(BASE + "/", params={"family.name": "x"})
    ).status_code == 400


# ── Bundle shape ─────────────────────────────────────────────────────────────


async def test_bundle_shape(client, people):
    bundle = await _search(client, {"family": "Careful"})
    assert bundle["resourceType"] == "Bundle"
    assert bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/practitioners/{people['adam']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "Practitioner"


async def test_xml_only_accept_is_406_on_search(client):
    assert (
        await client.get(BASE + "/", headers={"Accept": "application/fhir+xml"})
    ).status_code == 406


# ── POST _search ─────────────────────────────────────────────────────────────


async def test_post_search_form_encoded(client, people):
    resp = await client.post(
        BASE + "/_search",
        content="family=Careful&gender=male",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {people["adam"]}


async def test_post_search_combines_query_string_and_body(client, people):
    resp = await client.post(
        BASE + "/_search?gender=male",
        content="family=Careful",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert _ids(resp.json()) == {people["adam"]}
    resp = await client.post(
        BASE + "/_search?gender=female",
        content="family=Careful",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert _ids(resp.json()) == set()
