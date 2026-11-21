"""FHIR R4 search over RelatedPerson (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/relatedperson.html#search).

One block per search parameter — `active`/`gender`/`address-use`/`relationship`
are tokens, the name and address parameters are strings (starts-with by default,
case- and accent-insensitive), `birthdate` is a date held as the range it covers,
`telecom`/`phone`/`email` are tokens on a ContactPoint, `patient` is a single
target reference — then chaining, `_include`/`_revinclude` in both directions,
result parameters, combination rules, lenient vs strict handling and POST _search.
"""

import pytest

from tests.integration.related_person.support import (
    API,
    BASE,
    RP_IDS,
    ROLE,
    appointment_body,
    create_appointment,
    create_patient,
    create_related_person,
    participant,
    related_person_body,
)

KEYS = ("a", "b", "c", "d")
ALL = set(KEYS)


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


@pytest.fixture
async def world(client):
    """Two patients and four related persons with distinct, searchable values.
    Returns {key: id}."""
    w = {}
    w["p1"] = await create_patient(
        client, {"active": True, "name": [{"family": "Windsor", "given": ["Anna"]}]}
    )
    w["p2"] = await create_patient(
        client, {"active": True, "name": [{"family": "Fairfax", "given": ["Ben"]}]}
    )
    w["a"] = await create_related_person(
        client,
        related_person_body(
            w["p1"],
            identifier=[
                {"system": RP_IDS, "value": "RP-A", "type": {"text": "Contact id"}}
            ],
            active=True,
            relationship=[
                {
                    "coding": [{"system": ROLE, "code": "MTH", "display": "mother"}],
                    "text": "Mother",
                }
            ],
            name=[{"family": "Windsor", "given": ["Mary", "Ann"], "prefix": ["Mrs"]}],
            telecom=[
                {"system": "phone", "value": "555-9988", "use": "mobile"},
                {"system": "email", "value": "mary@example.org"},
            ],
            gender="female",
            birthDate="1965-04-12",
            address=[
                {
                    "use": "home",
                    "line": ["1 Main St"],
                    "city": "Boston",
                    "state": "MA",
                    "postalCode": "02110",
                    "country": "US",
                }
            ],
        ),
    )
    w["b"] = await create_related_person(
        client,
        related_person_body(
            w["p2"],
            identifier=[{"system": RP_IDS, "value": "RP-B"}],
            active=False,
            relationship=[
                {"text": "Guardian"},
                {"coding": [{"system": ROLE, "code": "GUARD"}]},
            ],
            name=[{"family": "Fairfax", "given": ["Robert"], "text": "Bob Fairfax"}],
            telecom=[{"system": "phone", "value": "555-1111", "use": "work"}],
            gender="male",
            birthDate="1990-05",
            address=[
                {
                    "use": "work",
                    "line": ["9 Lake Rd"],
                    "city": "Chicago",
                    "state": "IL",
                    "postalCode": "60601",
                    "country": "US",
                }
            ],
        ),
    )
    w["c"] = await create_related_person(
        client,
        related_person_body(
            None,
            relationship=[{"coding": [{"system": ROLE, "code": "WIFE"}]}],
            name=[{"family": "Müller", "given": ["Zoë"]}],
            gender="other",
            birthDate="2000",
            telecom=[{"system": "email", "value": "zoe@example.org"}],
        ),
    )
    w["d"] = await create_related_person(
        client,
        {
            "patient": {"identifier": {"system": "urn:pts", "value": "P-9"}},
            "gender": "unknown",
        },
    )
    return w


async def _search(client, **params) -> dict:
    resp = await client.get(BASE + "/", params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _keys(client, world, **params) -> set[str]:
    ids = _ids(await _search(client, **params))
    by_id = {world[k]: k for k in KEYS}
    return {by_id[i] for i in ids}


async def _status(client, **params) -> int:
    return (await client.get(BASE + "/", params=params)).status_code


# ── _id / _lastUpdated ───────────────────────────────────────────────────────


async def test_id(client, world):
    assert await _keys(client, world, _id=str(world["a"])) == {"a"}
    assert await _keys(client, world, _id="999999") == set()
    assert await _keys(client, world, **{"_id:not": str(world["a"])}) == ALL - {"a"}


async def test_last_updated(client, world):
    assert await _keys(client, world, _lastUpdated="ge2020-01-01") == ALL
    assert await _keys(client, world, _lastUpdated="lt2020-01-01") == set()


# ── active / gender ──────────────────────────────────────────────────────────


async def test_active(client, world):
    assert await _keys(client, world, active="true") == {"a"}
    assert await _keys(client, world, active="false") == {"b"}
    assert await _keys(client, world, **{"active:not": "true"}) == {
        "b",
        "c",
        "d",
    }  # includes "not recorded"
    assert await _keys(client, world, **{"active:missing": "true"}) == {"c", "d"}
    assert await _status(client, active="maybe") == 400


async def test_gender(client, world):
    assert await _keys(client, world, gender="female") == {"a"}
    assert await _keys(client, world, gender="male,other") == {"b", "c"}
    assert await _keys(
        client, world, gender="http://hl7.org/fhir/administrative-gender|unknown"
    ) == {"d"}
    assert await _keys(client, world, gender="http://wrong|female") == set()
    assert await _keys(client, world, gender="robot") == set()
    assert await _keys(client, world, **{"gender:not": "female"}) == {"b", "c", "d"}
    assert await _keys(client, world, **{"gender:missing": "true"}) == set()


# ── birthdate (a date held as the range it covers) ───────────────────────────


async def test_birthdate(client, world):
    assert await _keys(client, world, birthdate="1965-04-12") == {"a"}
    assert await _keys(client, world, birthdate="1965") == {
        "a"
    }  # the year contains the day
    assert await _keys(client, world, birthdate="1990-05") == {"b"}
    assert await _keys(client, world, birthdate="2000") == {"c"}
    assert (
        await _keys(client, world, birthdate="1990-05-15") == set()
    )  # a day inside the month does not equal it


async def test_birthdate_prefixes_and_missing(client, world):
    assert await _keys(client, world, birthdate="ge1990") == {"b", "c"}
    assert await _keys(client, world, birthdate="lt1970") == {"a"}
    assert await _keys(client, world, birthdate=["ge1960", "lt2000"]) == {"a", "b"}
    assert await _keys(client, world, **{"birthdate:missing": "true"}) == {"d"}
    assert await _status(client, birthdate="banana") == 400


# ── name / phonetic ──────────────────────────────────────────────────────────


async def test_name_matches_any_string_part_and_starts_with(client, world):
    assert await _keys(client, world, name="Wind") == {"a"}  # family, starts-with
    assert await _keys(client, world, name="mary") == {"a"}  # given, case-insensitive
    assert await _keys(client, world, name="Mrs") == {"a"}  # prefix
    assert await _keys(client, world, name="Bob") == {"b"}  # text
    assert await _keys(client, world, name="Rob") == {"b"}
    assert await _keys(client, world, name="Fair,Wind") == {"a", "b"}
    assert await _keys(client, world, name="indsor") == set()  # not a prefix


async def test_name_modifiers_and_accents(client, world):
    assert await _keys(client, world, **{"name:contains": "indso"}) == {"a"}
    assert await _keys(client, world, **{"name:exact": "Windsor"}) == {"a"}
    assert await _keys(client, world, **{"name:exact": "windsor"}) == set()
    assert await _keys(client, world, name="muller") == {"c"}  # accent-insensitive
    assert await _keys(client, world, name="zoe") == {"c"}
    assert await _keys(client, world, **{"name:missing": "true"}) == {"d"}


async def test_phonetic(client, world):
    assert await _keys(client, world, phonetic="Windsur") == {"a"}
    assert await _keys(client, world, phonetic="Fairfacks") == {"b"}
    assert await _keys(client, world, phonetic="Qwxz") == set()


# ── address ──────────────────────────────────────────────────────────────────


async def test_address_any_part(client, world):
    assert await _keys(client, world, address="1 Main") == {"a"}  # line, starts-with
    assert await _keys(client, world, address="Chic") == {"b"}  # city
    assert await _keys(client, world, address="US") == {"a", "b"}  # country
    assert await _keys(client, world, address="60601") == {"b"}  # postal code


async def test_address_parts(client, world):
    assert await _keys(client, world, **{"address-city": "bos"}) == {"a"}
    assert await _keys(client, world, **{"address-state": "IL"}) == {"b"}
    assert await _keys(client, world, **{"address-country": "us"}) == {"a", "b"}
    assert await _keys(client, world, **{"address-postalcode": "021"}) == {"a"}
    assert await _keys(client, world, **{"address-city:exact": "boston"}) == set()
    assert await _keys(client, world, **{"address-city:missing": "true"}) == {"c", "d"}


async def test_address_use(client, world):
    assert await _keys(client, world, **{"address-use": "home"}) == {"a"}
    assert await _keys(client, world, **{"address-use": "work"}) == {"b"}
    assert await _keys(
        client, world, **{"address-use": "http://hl7.org/fhir/address-use|home"}
    ) == {"a"}
    assert await _keys(client, world, **{"address-use": "http://wrong|home"}) == set()
    assert await _keys(client, world, **{"address-use": "nonsense"}) == set()
    assert await _keys(client, world, **{"address-use:not": "home"}) == {"b", "c", "d"}


# ── telecom / phone / email ──────────────────────────────────────────────────


async def test_telecom_phone_email(client, world):
    assert await _keys(client, world, telecom="555-9988") == {"a"}
    assert await _keys(client, world, telecom="mobile|555-9988") == {"a"}  # `use|value`
    assert await _keys(client, world, telecom="work|555-9988") == set()
    assert await _keys(client, world, phone="555-1111") == {"b"}
    assert (
        await _keys(client, world, phone="mary@example.org") == set()
    )  # an email is not a phone
    assert await _keys(client, world, email="mary@example.org") == {"a"}
    assert await _keys(client, world, email="zoe@example.org,mary@example.org") == {
        "a",
        "c",
    }
    assert await _keys(client, world, **{"phone:missing": "true"}) == {"c", "d"}
    assert await _keys(client, world, **{"email:missing": "true"}) == {"b", "d"}
    assert await _keys(client, world, **{"telecom:not": "555-9988"}) == {"b", "c", "d"}


# ── identifier / relationship ────────────────────────────────────────────────


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="RP-A") == {"a"}
    assert await _keys(client, world, identifier=f"{RP_IDS}|RP-B") == {"b"}
    assert await _keys(client, world, identifier="RP-A,RP-B") == {"a", "b"}
    assert await _keys(client, world, identifier="urn:other|RP-A") == set()


async def test_identifier_text_not_and_missing(client, world):
    assert await _keys(client, world, **{"identifier:text": "contact"}) == {"a"}
    assert await _keys(client, world, **{"identifier:not": "RP-A"}) == ALL - {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {"c", "d"}


async def test_relationship(client, world):
    assert await _keys(client, world, relationship="MTH") == {"a"}
    assert await _keys(client, world, relationship=f"{ROLE}|GUARD") == {"b"}
    assert await _keys(client, world, relationship=f"{ROLE}|") == {"a", "b", "c"}
    assert await _keys(client, world, relationship="MTH,WIFE") == {"a", "c"}
    assert await _keys(client, world, relationship="http://wrong|MTH") == set()


async def test_relationship_text_not_and_missing(client, world):
    assert await _keys(client, world, **{"relationship:text": "moth"}) == {"a"}
    assert await _keys(client, world, **{"relationship:text": "guard"}) == {
        "b"
    }  # a text-only concept is found too
    assert await _keys(client, world, **{"relationship:not": "MTH"}) == {"b", "c", "d"}
    assert await _keys(client, world, **{"relationship:missing": "true"}) == {"d"}


# ── patient ──────────────────────────────────────────────────────────────────


async def test_patient(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {
        "a"
    }  # a bare id works: one target
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"b"}
    assert await _keys(client, world, patient=f"{world['p1']},{world['p2']}") == {
        "a",
        "b",
    }
    assert await _keys(client, world, **{"patient:Patient": str(world["p1"])}) == {"a"}
    assert await _keys(client, world, patient="999999") == set()


async def test_patient_absolute_identifier_and_missing(client, world):
    assert await _keys(
        client, world, patient="https://other.example.org/fhir/Patient/1"
    ) == {"c"}
    assert await _keys(client, world, **{"patient:identifier": "urn:pts|P-9"}) == {"d"}
    assert await _keys(client, world, **{"patient:missing": "true"}) == set()
    assert await _keys(client, world, **{"patient:missing": "false"}) == ALL


async def test_patient_chain(client, world):
    assert await _keys(client, world, **{"patient.family": "Windsor"}) == {"a"}
    assert await _keys(client, world, **{"patient.name": "Ben"}) == {"b"}
    assert await _keys(client, world, **{"patient.family": "Nobody"}) == set()


async def test_bad_chains_are_400(client, world):
    assert await _status(client, **{"patient.nonsense": "x"}) == 400
    assert (
        await _status(client, **{"name.family": "x"}) == 400
    )  # a string cannot be chained through
    assert await _status(client, **{"gender.x": "y"}) == 400


# ── _sort / _count / _offset / _total ────────────────────────────────────────


async def test_sort_by_other_params(client, world):
    for key in (
        "active",
        "gender",
        "birthdate",
        "name",
        "identifier",
        "patient",
        "relationship",
        "address-city",
        "address-state",
        "address-country",
        "address-postalcode",
        "_id",
    ):
        assert (await _search(client, _sort=key))["total"] == 4, key
    assert await _status(client, _sort="photo") == 400


async def test_sort_by_birthdate_and_name(client, world):
    async def ids(**params):
        return [
            int(e["resource"]["id"]) for e in (await _search(client, **params))["entry"]
        ]

    assert await ids(**{"birthdate:missing": "false", "_sort": "birthdate"}) == [
        world["a"],
        world["b"],
        world["c"],
    ]
    assert await ids(**{"birthdate:missing": "false", "_sort": "-birthdate"}) == [
        world["c"],
        world["b"],
        world["a"],
    ]
    assert await ids(**{"name:missing": "false", "_sort": "name"}) == [
        world["b"],
        world["c"],
        world["a"],
    ]  # Fairfax, Müller, Windsor


async def test_default_sort_is_newest_first(client, world):
    got = [int(e["resource"]["id"]) for e in (await _search(client))["entry"]]
    assert got == sorted(got, reverse=True)


async def test_paging_and_total(client, world):
    page = await _search(client, _count=2, _sort="_id")
    assert page["total"] == 4 and len(page["entry"]) == 2
    assert any(link["relation"] == "next" for link in page["link"])
    nxt = await _search(client, _count=2, _offset=2, _sort="_id")
    assert not (
        {e["resource"]["id"] for e in page["entry"]}
        & {e["resource"]["id"] for e in nxt["entry"]}
    )
    assert "entry" not in await _search(client, _count=0)
    assert "total" not in await _search(client, _total="none")


async def test_summary_count_and_elements(client, world):
    assert (await _search(client, _summary="count"))["total"] == 4
    resource = (await _search(client, _elements="gender", _id=str(world["a"])))[
        "entry"
    ][0]["resource"]
    assert resource["gender"] == "female"
    assert "name" not in resource and "telecom" not in resource


# ── _include / _revinclude ───────────────────────────────────────────────────


async def test_include_patient(client, world):
    bundle = await _search(
        client, _id=str(world["a"]), _include="RelatedPerson:patient"
    )
    assert _of_type(bundle, "Patient", "include") == {str(world["p1"])}


async def test_include_patient_is_deduplicated_and_skips_non_resources(client, world):
    bundle = await _search(
        client,
        _id=f"{world['a']},{world['c']},{world['d']}",
        _include="RelatedPerson:patient",
    )
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"])
    }  # c and d point elsewhere
    bundle = await _search(
        client, patient=str(world["p1"]), _include="RelatedPerson:patient"
    )
    assert (
        sum(1 for e in bundle["entry"] if e["resource"]["resourceType"] == "Patient")
        == 1
    )


async def _other(client, path, **params) -> dict:
    resp = await client.get(f"{API}/{path}/", params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_revinclude_related_person_on_patients(client, world):
    bundle = await _other(
        client, "patients", _id=str(world["p2"]), _revinclude="RelatedPerson:patient"
    )
    assert _of_type(bundle, "RelatedPerson", "include") == {str(world["b"])}
    bundle = await _other(
        client,
        "patients",
        _id=f"{world['p1']},{world['p2']}",
        _revinclude="RelatedPerson:patient",
    )
    assert _of_type(bundle, "RelatedPerson", "include") == {
        str(world["a"]),
        str(world["b"]),
    }


async def test_revinclude_what_points_at_a_related_person(client, world):
    rp = world["a"]
    ref = f"RelatedPerson/{rp}"
    appointment = await create_appointment(
        client, appointment_body(world["p1"], participant=[participant(ref)])
    )
    ar = (
        await client.post(
            f"{API}/appointment-responses/",
            json={
                "appointment": {"reference": f"Appointment/{appointment}"},
                "participantStatus": "accepted",
                "actor": {"reference": ref},
            },
        )
    ).json()["id"]
    enc = (
        await client.post(
            f"{API}/encounters/",
            json={
                "status": "finished",
                "class": {"code": "AMB"},
                "participant": [{"individual": {"reference": ref}}],
            },
        )
    ).json()["id"]
    patient = (
        await client.post(
            f"{API}/patients/",
            json={"link": [{"other": {"reference": ref}, "type": "seealso"}]},
        )
    ).json()["id"]

    def go(**params):
        return _search(client, _id=str(rp), **params)

    assert _of_type(
        await go(_revinclude="Appointment:actor"), "Appointment", "include"
    ) == {str(appointment)}
    assert _of_type(
        await go(_revinclude="AppointmentResponse:actor"),
        "AppointmentResponse",
        "include",
    ) == {ar}
    assert _of_type(
        await go(_revinclude="Encounter:participant"), "Encounter", "include"
    ) == {enc}
    assert _of_type(await go(_revinclude="Patient:link"), "Patient", "include") == {
        patient
    }


async def test_revinclude_is_tenant_scoped(client, other_client):
    from app.auth.dependencies import get_current_user
    from app.main import app
    from tests.conftest import make_test_user
    from tests.integration.related_person.conftest import RELATED_PERSON_PERMS

    def as_user(**kw):
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=RELATED_PERSON_PERMS, **kw
        )

    as_user()
    mine = await create_patient(client)
    await create_related_person(client, related_person_body(mine))
    as_user(sub="u-other", org_id="org-other")
    try:
        # The other org cannot see the patient, so nothing reaches its related persons.
        bundle = await _other(
            other_client, "patients", _id=str(mine), _revinclude="RelatedPerson:patient"
        )
        assert bundle["total"] == 0 and "entry" not in bundle
        theirs = await create_patient(other_client)
        bundle = await _other(
            other_client,
            "patients",
            _id=str(theirs),
            _revinclude="RelatedPerson:patient",
        )
        assert _of_type(bundle, "RelatedPerson", "include") == set()
    finally:
        as_user()


# ── combination rules / lenient vs strict ────────────────────────────────────


async def test_params_are_anded(client, world):
    assert await _keys(client, world, gender="female", active="true") == {"a"}
    assert await _keys(client, world, gender="female", active="false") == set()
    assert await _keys(
        client, world, patient=str(world["p2"]), relationship="GUARD"
    ) == {"b"}
    assert await _keys(client, world, **{"address-city": "Boston"}, name="Windsor") == {
        "a"
    }


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"gender:above": "x"}) == 400
    assert await _status(client, **{"name:text": "x"}) == 400
    assert await _status(client, **{"phone:contains": "x"}) == 400


async def test_unknown_param_lenient_vs_strict(client, world):
    lenient = await client.get(BASE + "/", params={"nonsense": "1"})
    assert lenient.status_code == 200
    assert any(e["search"]["mode"] == "outcome" for e in lenient.json()["entry"])
    strict = await client.get(
        BASE + "/", params={"nonsense": "1"}, headers={"Prefer": "handling=strict"}
    )
    assert strict.status_code == 400


async def test_query_param_refused(client, world):
    assert await _status(client, _query="x") == 400


# ── POST _search / Bundle shape ──────────────────────────────────────────────


async def test_post_search_form_encoded(client, world):
    resp = await client.post(
        BASE + "/_search", data={"gender": "male", "patient": str(world["p2"])}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, gender="male")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/related-persons/{world['b']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "RelatedPerson"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
