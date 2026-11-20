"""FHIR R4 search over Patient (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/patient.html#search).

One block per search parameter — `birthdate` and `death-date` are dates held as
the range they cover (so a partial date like `1990` works), `deceased` is the
R4 "marked deceased" boolean, `general-practitioner` and `link` are references
with several target types, `organization` a single reference — then chaining,
`_include` / `_revinclude` in both directions, the result parameters,
combination rules, lenient vs strict handling, the Bundle shape and POST
_search.
"""

import pytest

from tests.integration.patient.support import (
    API,
    BASE,
    LANG,
    MRN,
    create_organization,
    create_patient,
    create_practitioner,
    create_practitioner_role,
)

KEYS = ("a", "b", "c", "bare")
ALL = set(KEYS)


def _ids(bundle: dict) -> set[int]:
    return {int(e["resource"]["id"]) for e in bundle.get("entry") or [] if e["search"]["mode"] == "match"}


@pytest.fixture
async def world(client):
    """A practitioner, a role and two organizations, and four patients with
    distinct, searchable values. Returns {key: public id}."""
    w = {}
    w["prac"] = await create_practitioner(client, "Careful", "Adam")
    w["role"] = await create_practitioner_role(client)
    w["org1"] = await create_organization(client, "North Hospital")
    w["org2"] = await create_organization(client, "South Clinic")

    w["bare"] = await create_patient(client, {"name": [{"family": "Zed"}]})
    rp = await client.post(
        API + "/related-persons/",
        json={"patient": {"reference": f"Patient/{w['bare']}"}, "name": [{"family": "Relative"}]},
    )
    assert rp.status_code == 201, rp.text
    w["rp"] = int(rp.json()["id"])
    w["c"] = await create_patient(
        client,
        {
            "active": True,
            "gender": "other",
            "birthDate": "1990",
            "name": [{"family": "Dupont", "given": ["Marie"]}],
            "address": [{"city": "Paris", "country": "FR", "postalCode": "75001"}],
            "communication": [{"language": {"text": "Francais"}}],
            "generalPractitioner": [{"reference": f"PractitionerRole/{w['role']}"}],
            "link": [{"other": {"reference": f"RelatedPerson/{w['rp']}"}, "type": "replaced-by"}],
        },
    )
    w["b"] = await create_patient(
        client,
        {
            "active": False,
            "gender": "female",
            "birthDate": "1990-05",
            "deceasedDateTime": "2020-03-01T10:00:00Z",
            "identifier": [{"system": MRN, "value": "MRN-B"}],
            "name": [{"use": "official", "family": "Windsor", "given": ["Aïsha"], "suffix": ["Jr"]}],
            "telecom": [{"system": "phone", "value": "555-9999", "use": "work"}],
            "address": [{"use": "work", "line": ["9 Elm Road"], "city": "Cambridge", "state": "MA", "postalCode": "02139", "country": "US"}],
            "communication": [{"language": {"coding": [{"system": LANG, "code": "fr"}]}}],
            "generalPractitioner": [{"reference": f"Organization/{w['org2']}"}],
            "managingOrganization": {"reference": f"Organization/{w['org2']}"},
        },
    )
    w["a"] = await create_patient(
        client,
        {
            "active": True,
            "gender": "male",
            "birthDate": "1974-12-25",
            "deceasedBoolean": False,
            "identifier": [
                {
                    "system": MRN,
                    "value": "MRN-A",
                    "type": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR"}], "text": "Medical record"},
                }
            ],
            "name": [{"use": "official", "family": "Chalmers", "given": ["Peter", "James"], "prefix": ["Mr"]}],
            "telecom": [{"system": "phone", "value": "555-1234", "use": "home"}, {"system": "email", "value": "peter@example.org"}],
            "address": [
                {"use": "home", "line": ["534 Erewhon St"], "city": "Boston", "state": "MA", "postalCode": "02110", "country": "US"}
            ],
            "communication": [{"language": {"coding": [{"system": LANG, "code": "en"}]}, "preferred": True}],
            "generalPractitioner": [{"reference": f"Practitioner/{w['prac']}"}],
            "managingOrganization": {"reference": f"Organization/{w['org1']}"},
            "link": [{"other": {"reference": f"Patient/{w['bare']}"}, "type": "seealso"}],
        },
    )
    return w


async def _search(client, **params) -> dict:
    resp = await client.get(BASE + "/", params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _keys(client, world, **params) -> set[str]:
    by_id = {world[k]: k for k in KEYS}
    return {by_id[i] for i in _ids(await _search(client, **params))}


# ── _id / _lastUpdated ───────────────────────────────────────────────────────


async def test_id(client, world):
    assert await _keys(client, world, _id=str(world["a"])) == {"a"}
    assert await _keys(client, world, _id=f"{world['a']},{world['b']}") == {"a", "b"}
    assert await _keys(client, world, **{"_id:not": str(world["a"])}) == ALL - {"a"}


async def test_last_updated(client, world):
    assert await _keys(client, world, _lastUpdated="ge2000-01-01") == ALL
    assert await _keys(client, world, _lastUpdated="lt2000-01-01") == set()


# ── active / gender / deceased ───────────────────────────────────────────────


async def test_active(client, world):
    assert await _keys(client, world, active="true") == {"a", "c"}
    assert await _keys(client, world, active="false") == {"b"}
    assert await _keys(client, world, **{"active:not": "true"}) == {"b", "bare"}
    assert (await client.get(BASE + "/", params={"active": "maybe"})).status_code == 400


async def test_gender(client, world):
    assert await _keys(client, world, gender="male") == {"a"}
    assert await _keys(client, world, gender="female,other") == {"b", "c"}
    assert await _keys(client, world, gender="http://hl7.org/fhir/administrative-gender|male") == {"a"}
    assert await _keys(client, world, gender="http://wrong.example.org|male") == set()
    assert await _keys(client, world, gender="robot") == set()
    assert await _keys(client, world, **{"gender:not": "male"}) == ALL - {"a"}
    assert await _keys(client, world, **{"gender:missing": "true"}) == {"bare"}


async def test_deceased_is_the_r4_marked_deceased_boolean(client, world):
    # b has a death date; a has deceasedBoolean=false; c and bare have neither.
    assert await _keys(client, world, deceased="true") == {"b"}
    assert await _keys(client, world, deceased="false") == ALL - {"b"}
    assert await _keys(client, world, **{"deceased:missing": "true"}) == {"c", "bare"}
    assert (await client.get(BASE + "/", params={"deceased": "x"})).status_code == 400


# ── birthdate / death-date ───────────────────────────────────────────────────


async def test_birthdate_eq_matches_the_range_it_covers(client, world):
    assert await _keys(client, world, birthdate="1974-12-25") == {"a"}
    assert await _keys(client, world, birthdate="1974") == {"a"}
    assert await _keys(client, world, birthdate="1990") == {"b", "c"}  # May 1990 and "1990" both lie inside 1990
    assert await _keys(client, world, birthdate="1990-05") == {"b"}  # "1990" is wider than the search range
    assert await _keys(client, world, birthdate="1991") == set()


async def test_birthdate_prefixes(client, world):
    assert await _keys(client, world, birthdate="lt1980-01-01") == {"a"}
    assert await _keys(client, world, birthdate="gt2000-01-01") == set()
    assert await _keys(client, world, birthdate="ge1990-01-01") == {"b", "c"}
    assert await _keys(client, world, birthdate="le1974-12-25") == {"a"}
    assert await _keys(client, world, birthdate="ne1974-12-25") == {"b", "c"}


async def test_birthdate_range_and_or(client, world):
    assert await _keys(client, world, birthdate=["ge1970-01-01", "lt1980-01-01"]) == {"a"}
    assert await _keys(client, world, birthdate="1974-12-25,1990-05") == {"a", "b"}


async def test_birthdate_missing_and_bad_value(client, world):
    assert await _keys(client, world, **{"birthdate:missing": "true"}) == {"bare"}
    assert await _keys(client, world, **{"birthdate:missing": "false"}) == {"a", "b", "c"}
    assert (await client.get(BASE + "/", params={"birthdate": "last-tuesday"})).status_code == 400


async def test_death_date(client, world):
    assert await _keys(client, world, **{"death-date": "2020-03-01"}) == {"b"}
    assert await _keys(client, world, **{"death-date": "ge2020-01-01"}) == {"b"}
    assert await _keys(client, world, **{"death-date": "lt2020-01-01"}) == set()
    assert await _keys(client, world, **{"death-date:missing": "true"}) == {"a", "c", "bare"}


# ── names ────────────────────────────────────────────────────────────────────


async def test_family_is_case_and_accent_insensitive_starts_with(client, world):
    assert await _keys(client, world, family="chal") == {"a"}
    assert await _keys(client, world, family="CHALMERS") == {"a"}
    assert await _keys(client, world, family="halmers") == set()  # starts-with, not contains
    assert await _keys(client, world, **{"family:contains": "halmers"}) == {"a"}
    assert await _keys(client, world, **{"family:exact": "Chalmers"}) == {"a"}
    assert await _keys(client, world, **{"family:exact": "chalmers"}) == set()
    assert await _keys(client, world, family="Windsor,Dupont") == {"b", "c"}


async def test_given_matches_each_given_name_on_its_own(client, world):
    assert await _keys(client, world, given="Peter") == {"a"}
    assert await _keys(client, world, given="james") == {"a"}
    assert await _keys(client, world, given="Aisha") == {"b"}  # accent-insensitive
    assert await _keys(client, world, given="PeterJames") == set()


async def test_name_matches_any_part_of_a_human_name(client, world):
    assert await _keys(client, world, name="Chal") == {"a"}  # family
    assert await _keys(client, world, name="Marie") == {"c"}  # given
    assert await _keys(client, world, name="Mr") == {"a"}  # prefix
    assert await _keys(client, world, name="Jr") == {"b"}  # suffix


async def test_name_and_family_missing(client, world):
    assert await _keys(client, world, **{"family:missing": "true"}) == set()
    assert await _keys(client, world, **{"given:missing": "true"}) == {"bare"}
    assert await _keys(client, world, **{"name:missing": "false"}) == ALL


async def test_phonetic(client, world):
    assert await _keys(client, world, phonetic="Chalmurs") == {"a"}
    assert await _keys(client, world, phonetic="Windsur") == {"b"}
    assert await _keys(client, world, phonetic="Zzzz") == set()


# ── identifier ───────────────────────────────────────────────────────────────


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="MRN-A") == {"a"}
    assert await _keys(client, world, identifier=f"{MRN}|MRN-B") == {"b"}
    assert await _keys(client, world, identifier="urn:other|MRN-A") == set()
    assert await _keys(client, world, identifier=f"{MRN}|") == {"a", "b"}


async def test_identifier_text_of_type_not_and_missing(client, world):
    assert await _keys(client, world, **{"identifier:text": "Medical"}) == {"a"}
    ofty = "http://terminology.hl7.org/CodeSystem/v2-0203|MR|MRN-A"
    assert await _keys(client, world, **{"identifier:of-type": ofty}) == {"a"}
    assert await _keys(client, world, **{"identifier:not": "MRN-A"}) == ALL - {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {"c", "bare"}


# ── telecom / phone / email ──────────────────────────────────────────────────


async def test_phone_email_and_telecom(client, world):
    assert await _keys(client, world, phone="555-1234") == {"a"}
    assert await _keys(client, world, phone="555-9999") == {"b"}
    assert await _keys(client, world, email="peter@example.org") == {"a"}
    assert await _keys(client, world, email="555-1234") == set()  # a phone value is not an email
    assert await _keys(client, world, telecom="555-1234") == {"a"}
    assert await _keys(client, world, telecom="peter@example.org") == {"a"}
    assert await _keys(client, world, telecom="work|555-9999") == {"b"}  # `use|value`
    assert await _keys(client, world, **{"phone:missing": "true"}) == {"c", "bare"}


# ── address ──────────────────────────────────────────────────────────────────


async def test_address_parts(client, world):
    assert await _keys(client, world, **{"address-city": "Bos"}) == {"a"}
    assert await _keys(client, world, **{"address-state": "ma"}) == {"a", "b"}
    assert await _keys(client, world, **{"address-postalcode": "02110"}) == {"a"}
    assert await _keys(client, world, **{"address-country": "us"}) == {"a", "b"}
    assert await _keys(client, world, **{"address-country": "FR"}) == {"c"}
    assert await _keys(client, world, **{"address-city:exact": "Boston"}) == {"a"}
    assert await _keys(client, world, **{"address-city:missing": "true"}) == {"bare"}


async def test_address_matches_any_string_part(client, world):
    assert await _keys(client, world, address="534 Erewhon") == {"a"}  # line
    assert await _keys(client, world, address="Cambridge") == {"b"}  # city
    assert await _keys(client, world, address="02139") == {"b"}  # postal code
    assert await _keys(client, world, **{"address:contains": "Elm"}) == {"b"}


async def test_address_use_token(client, world):
    assert await _keys(client, world, **{"address-use": "home"}) == {"a"}
    assert await _keys(client, world, **{"address-use": "work"}) == {"b"}
    assert await _keys(client, world, **{"address-use": "http://hl7.org/fhir/address-use|home"}) == {"a"}
    assert await _keys(client, world, **{"address-use": "http://wrong.example.org|home"}) == set()
    assert await _keys(client, world, **{"address-use": "nonsense"}) == set()


# ── language ─────────────────────────────────────────────────────────────────


async def test_language(client, world):
    assert await _keys(client, world, language="en") == {"a"}
    assert await _keys(client, world, language=f"{LANG}|fr") == {"b"}
    assert await _keys(client, world, language="en,fr") == {"a", "b"}
    assert await _keys(client, world, language="other|en") == set()
    assert await _keys(client, world, **{"language:text": "Franc"}) == {"c"}  # text-only language
    assert await _keys(client, world, **{"language:missing": "true"}) == {"bare"}


# ── organization ─────────────────────────────────────────────────────────────


async def test_organization(client, world):
    assert await _keys(client, world, organization=str(world["org1"])) == {"a"}
    assert await _keys(client, world, organization=f"Organization/{world['org2']}") == {"b"}
    assert await _keys(client, world, **{"organization:Organization": str(world["org1"])}) == {"a"}
    assert await _keys(client, world, organization=f"{world['org1']},{world['org2']}") == {"a", "b"}
    assert await _keys(client, world, **{"organization:missing": "true"}) == {"c", "bare"}


async def test_organization_by_absolute_url_and_logical_reference(client, world):
    url = "https://other.example.org/fhir/Organization/9"
    ext = await create_patient(client, {"managingOrganization": {"reference": url}})
    logical = await create_patient(
        client, {"managingOrganization": {"identifier": {"system": "urn:orgs", "value": "ORG-9"}}}
    )
    assert ext in _ids(await _search(client, organization=url))
    assert logical in _ids(await _search(client, **{"organization:identifier": "urn:orgs|ORG-9"}))
    assert logical not in _ids(await _search(client, organization=url))


async def test_organization_chain(client, world):
    assert await _keys(client, world, **{"organization.name": "North"}) == {"a"}
    assert await _keys(client, world, **{"organization.name": "South"}) == {"b"}
    assert await _keys(client, world, **{"organization.name": "Nowhere"}) == set()


# ── general-practitioner (Practitioner | PractitionerRole | Organization) ────


async def test_general_practitioner_needs_a_type(client, world):
    assert await _keys(client, world, **{"general-practitioner": f"Practitioner/{world['prac']}"}) == {"a"}
    assert await _keys(client, world, **{"general-practitioner": f"PractitionerRole/{world['role']}"}) == {"c"}
    assert await _keys(client, world, **{"general-practitioner": f"Organization/{world['org2']}"}) == {"b"}
    assert await _keys(client, world, **{"general-practitioner:Practitioner": str(world["prac"])}) == {"a"}
    # A bare id is ambiguous across three types.
    assert (await client.get(BASE + "/", params={"general-practitioner": str(world["prac"])})).status_code == 400


async def test_general_practitioner_type_is_part_of_the_match(client, world):
    # Organization/<prac id> must not match the patient whose practitioner has that id.
    assert await _keys(client, world, **{"general-practitioner": f"Organization/{world['prac']}"}) == set()
    assert await _keys(client, world, **{"general-practitioner:Organization": str(world["prac"])}) == set()


async def test_general_practitioner_missing_identifier_and_bad_type(client, world):
    logical = await create_patient(client, {"generalPractitioner": [{"identifier": {"system": "urn:gps", "value": "GP-7"}}]})
    assert logical in _ids(await _search(client, **{"general-practitioner:identifier": "urn:gps|GP-7"}))
    assert await _keys(client, world, **{"general-practitioner:missing": "true"}) == {"bare"}
    assert (await client.get(BASE + "/", params={"general-practitioner:Patient": "1"})).status_code == 400


async def test_general_practitioner_chain_through_a_typed_target(client, world):
    assert await _keys(client, world, **{"general-practitioner:Practitioner.family": "Careful"}) == {"a"}
    assert await _keys(client, world, **{"general-practitioner:Organization.name": "South"}) == {"b"}
    assert await _keys(client, world, **{"general-practitioner:Practitioner.family": "Nobody"}) == set()
    # An untyped chain across several targets is ambiguous.
    assert (await client.get(BASE + "/", params={"general-practitioner.family": "Careful"})).status_code == 400


# ── link ─────────────────────────────────────────────────────────────────────


async def test_link(client, world):
    assert await _keys(client, world, link=f"Patient/{world['bare']}") == {"a"}
    assert await _keys(client, world, **{"link:Patient": str(world["bare"])}) == {"a"}
    assert await _keys(client, world, link=f"RelatedPerson/{world['rp']}") == {"c"}
    assert await _keys(client, world, link="RelatedPerson/5") == set()
    assert await _keys(client, world, **{"link:missing": "true"}) == {"b", "bare"}


async def test_link_chain_through_patient(client, world):
    assert await _keys(client, world, **{"link:Patient.family": "Zed"}) == {"a"}
    # ... and through a RelatedPerson, now that it is a resource here.
    assert await _keys(client, world, **{"link:RelatedPerson.name": "Relative"}) == {"c"}
    assert await _keys(client, world, **{"link:RelatedPerson.name": "Nobody"}) == set()
    assert (await client.get(BASE + "/", params={"link:Practitioner.family": "x"})).status_code == 400


# ── _sort / _count / _offset / _total ────────────────────────────────────────


async def test_sort_by_family_and_birthdate(client, world):
    asc = [int(e["resource"]["id"]) for e in (await _search(client, _sort="family"))["entry"]]
    assert asc[:3] == [world["a"], world["c"], world["b"]]  # Chalmers, Dupont, Windsor (Zed last)
    desc = [int(e["resource"]["id"]) for e in (await _search(client, _sort="-birthdate"))["entry"]]
    assert desc.index(world["c"]) < desc.index(world["a"]) or desc.index(world["b"]) < desc.index(world["a"])
    for key in ("gender", "-gender", "deceased", "death-date", "organization", "general-practitioner", "link"):
        assert (await client.get(BASE + "/", params={"_sort": key})).status_code == 200, key
    assert (await client.get(BASE + "/", params={"_sort": "contact"})).status_code == 400


async def test_default_sort_is_newest_first(client, world):
    got = [int(e["resource"]["id"]) for e in (await _search(client))["entry"]]
    assert got == sorted(got, reverse=True)


async def test_paging_and_total(client, world):
    page = await _search(client, _count=2, _sort="family")
    assert page["total"] == 4 and len(page["entry"]) == 2
    assert {link["relation"] for link in page["link"]} >= {"self", "next"}
    nxt = await _search(client, _count=2, _offset=2, _sort="family")
    assert len(nxt["entry"]) == 2
    assert "entry" not in await _search(client, _count=0)
    assert "total" not in await _search(client, _total="none")


# ── _summary / _elements ─────────────────────────────────────────────────────


async def test_summary_count_and_elements(client, world):
    summary = await _search(client, _summary="count")
    assert summary["total"] == 4 and "entry" not in summary
    elems = await _search(client, _elements="gender", _id=str(world["a"]))
    res = elems["entry"][0]["resource"]
    assert res["gender"] == "male" and "contact" not in res and "address" not in res
    assert res["meta"]["tag"][0]["code"] == "SUBSETTED"


async def test_summary_true_keeps_only_summary_elements(client, world):
    res = (await _search(client, _summary="true", _id=str(world["a"])))["entry"][0]["resource"]
    assert "name" in res and "birthDate" in res and "managingOrganization" in res
    assert "communication" not in res and "photo" not in res


# ── _include / _revinclude ───────────────────────────────────────────────────


def _by_type(bundle: dict, mode: str) -> dict[str, set[str]]:
    out: dict[str, set[str]] = {}
    for e in bundle["entry"]:
        if e["search"]["mode"] == mode:
            out.setdefault(e["resource"]["resourceType"], set()).add(e["resource"]["id"])
    return out


async def test_include_organization(client, world):
    bundle = await _search(client, _id=str(world["a"]), _include="Patient:organization")
    assert _by_type(bundle, "include") == {"Organization": {str(world["org1"])}}


async def test_include_general_practitioner_brings_every_modeled_type(client, world):
    bundle = await _search(client, _id=f"{world['a']},{world['b']},{world['c']}", _include="Patient:general-practitioner")
    assert _by_type(bundle, "include") == {
        "Practitioner": {str(world["prac"])},
        "PractitionerRole": {str(world["role"])},
        "Organization": {str(world["org2"])},
    }


async def test_include_general_practitioner_narrowed_to_one_type(client, world):
    bundle = await _search(
        client, _id=f"{world['a']},{world['b']}", _include="Patient:general-practitioner:Practitioner"
    )
    assert _by_type(bundle, "include") == {"Practitioner": {str(world["prac"])}}


async def test_include_link(client, world):
    bundle = await _search(client, _id=str(world["a"]), _include="Patient:link")
    assert _by_type(bundle, "include") == {"Patient": {str(world["bare"])}}
    bundle = await _search(client, _id=str(world["c"]), _include="Patient:link")
    assert _by_type(bundle, "include") == {"RelatedPerson": {str(world["rp"])}}


async def test_revinclude_link(client, world):
    bundle = await _search(client, _id=str(world["bare"]), _revinclude="Patient:link")
    assert _by_type(bundle, "include") == {"Patient": {str(world["a"])}}


async def test_revinclude_from_practitioner_role_and_organization(client, world):
    for path, params, expected in (
        ("practitioners", {"_id": str(world["prac"]), "_revinclude": "Patient:general-practitioner"}, {world["a"]}),
        ("practitioner-roles", {"_id": str(world["role"]), "_revinclude": "Patient:general-practitioner"}, {world["c"]}),
        ("organizations", {"_id": str(world["org2"]), "_revinclude": "Patient:general-practitioner"}, {world["b"]}),
        ("organizations", {"_id": str(world["org1"]), "_revinclude": "Patient:organization"}, {world["a"]}),
    ):
        resp = await client.get(f"{API}/{path}/", params=params)
        assert resp.status_code == 200, (path, resp.text)
        got = {int(i) for i in _by_type(resp.json(), "include").get("Patient", set())}
        assert got == expected, (path, params)


async def test_include_unknown_param_is_ignored_or_400(client, world):
    resp = await client.get(BASE + "/", params={"_include": "Patient:nonsense"})
    assert resp.status_code in (200, 400)


# ── combination rules / lenient vs strict ────────────────────────────────────


async def test_params_are_anded(client, world):
    assert await _keys(client, world, gender="male", family="Chalmers") == {"a"}
    assert await _keys(client, world, gender="male", family="Windsor") == set()
    assert await _keys(client, world, active="true", **{"address-state": "MA"}) == {"a"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert (await client.get(BASE + "/", params={"gender:above": "male"})).status_code == 400


async def test_unknown_param_lenient_vs_strict(client, world):
    lenient = await client.get(BASE + "/", params={"nonsense": "1"})
    assert lenient.status_code == 200
    assert any(e["search"]["mode"] == "outcome" for e in lenient.json()["entry"])
    strict = await client.get(BASE + "/", params={"nonsense": "1"}, headers={"Prefer": "handling=strict"})
    assert strict.status_code == 400


async def test_query_param_refused(client, world):
    assert (await client.get(BASE + "/", params={"_query": "x"})).status_code == 400


# ── POST _search / Bundle shape ──────────────────────────────────────────────


async def test_post_search_form_encoded(client, world):
    resp = await client.post(BASE + "/_search", data={"gender": "female", "birthdate": "1990-05"})
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, gender="male")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/patients/{world['a']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "Patient"


async def test_empty_result(client, world):
    bundle = await _search(client, family="Nobody")
    assert bundle["total"] == 0 and "entry" not in bundle
