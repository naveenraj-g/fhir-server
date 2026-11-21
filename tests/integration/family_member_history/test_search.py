"""FHIR R4 search over FamilyMemberHistory (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/familymemberhistory.html#search).

One block per search parameter — `status` is a token on a plain code, `code`, `relationship`
and `sex` tokens on CodeableConcepts, `identifier` a token on an Identifier, `date` a dateTime
range, `patient` a single-target reference, `instantiates-canonical` a canonical-URL search and
`instantiates-uri` a uri search — then chaining, `_include`/`_revinclude`, result parameters,
combination rules, lenient vs strict handling and POST _search.
"""

import pytest

from tests.integration.family_member_history.support import (
    API,
    BASE,
    GENDER,
    HISTORY_IDS,
    ROLE_CODE,
    SCT,
    STATUS_SYSTEM,
    V2_0203,
    create_history,
    create_patient,
    disease,
    history_body,
    relationship,
    sex,
)

KEYS = ("a", "b", "c", "d", "e")
ALL = set(KEYS)
CANONICAL = "http://example.org/fhir/PlanDefinition/fh"


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
    """Two patients, plus five histories with distinct, searchable values. Returns {key: id}."""
    w = {}
    w["p1"] = await create_patient(
        client, {"active": True, "name": [{"family": "Windsor", "given": ["Anna"]}]}
    )
    w["p2"] = await create_patient(
        client, {"active": True, "name": [{"family": "Fairfax", "given": ["Ben"]}]}
    )
    w["a"] = await create_history(
        client,
        history_body(
            w["p1"],
            "completed",
            identifier=[
                {
                    "system": HISTORY_IDS,
                    "value": "FMH-A",
                    "type": {
                        "coding": [{"system": V2_0203, "code": "FILL"}],
                        "text": "History id",
                    },
                }
            ],
            date="2023-01-15T09:30:00Z",
            relationship=relationship("MTH", "mother"),
            sex=sex("female"),
            condition=[
                {"code": disease("44054006", "Type 2 diabetes")},
                {"code": disease("38341003", "Hypertension")},
            ],
            instantiatesCanonical=[f"{CANONICAL}|1.0", "Questionnaire/5"],
            instantiatesUri=["http://example.org/protocols/fh/1"],
        ),
    )
    w["b"] = await create_history(
        client,
        history_body(
            w["p2"],
            "partial",
            identifier=[{"system": HISTORY_IDS, "value": "FMH-B"}],
            date="2024-02",
            relationship=relationship("FTH", "father"),
            sex=sex("male"),
            condition=[{"code": {"text": "Asthma"}}],
        ),
    )
    w["c"] = await create_history(
        client,
        history_body(
            w["p1"],
            "health-unknown",
            date="2022-06-10T00:00:00Z",
            relationship={"text": "Aunt"},
            sex=sex("unknown"),
            instantiatesUri=["http://example.org/protocols/other"],
        ),
    )
    w["d"] = await create_history(
        client,
        history_body(
            w["p2"],
            "entered-in-error",
            date="2019",
            relationship=relationship("SIB", "sibling"),
            sex=sex("female"),
            condition=[{"code": disease("195967001")}],
        ),
    )
    w["e"] = await create_history(
        client,
        {
            "status": "completed",
            "patient": {
                "identifier": {"system": "urn:pts", "value": "P-9"},
                "display": "External",
            },
            "relationship": relationship("MTH"),
            "date": "2024-03-01T00:00:00Z",
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


async def _other(client, path: str, **params) -> dict:
    resp = await client.get(f"{API}/{path}/", params=params)
    assert resp.status_code == 200, resp.text
    return resp.json()


# ── _id / _lastUpdated ───────────────────────────────────────────────────────


async def test_id(client, world):
    assert await _keys(client, world, _id=str(world["a"])) == {"a"}
    assert await _keys(client, world, _id="999999") == set()
    assert await _keys(client, world, **{"_id:not": str(world["a"])}) == ALL - {"a"}


async def test_last_updated(client, world):
    assert await _keys(client, world, _lastUpdated="ge2020-01-01") == ALL
    assert await _keys(client, world, _lastUpdated="lt2020-01-01") == set()


# ── status ───────────────────────────────────────────────────────────────────


async def test_status(client, world):
    assert await _keys(client, world, status="completed") == {"a", "e"}
    assert await _keys(client, world, status="partial,health-unknown") == {"b", "c"}
    assert await _keys(client, world, status="entered-in-error") == {
        "d"
    }  # the real FHIR code
    assert await _keys(client, world, status="health-unknown") == {"c"}
    assert await _keys(client, world, status=f"{STATUS_SYSTEM}|partial") == {"b"}
    assert await _keys(client, world, status="http://wrong|completed") == set()
    assert (
        await _keys(client, world, status="|completed") == set()
    )  # a code with no system is not this one
    assert await _keys(client, world, status="nonsense") == set()
    assert await _keys(client, world, **{"status:not": "completed"}) == {"b", "c", "d"}
    assert (
        await _status(client, **{"status:text": "completed"}) == 400
    )  # a plain code has no :text


# ── date ─────────────────────────────────────────────────────────────────────


async def test_date(client, world):
    assert await _keys(client, world, date="2023-01-15") == {"a"}
    assert await _keys(client, world, date="2023") == {"a"}
    assert await _keys(client, world, date="2024") == {
        "b",
        "e",
    }  # 2024-02 and 2024-03-01 lie inside 2024
    assert await _keys(client, world, date="ge2024-01-01") == {"b", "e"}
    assert await _keys(client, world, date="lt2023-01-01") == {"c", "d"}
    assert await _keys(client, world, date="lt2020-01-01,ge2024-03-01") == {"d", "e"}
    assert await _keys(client, world, date="sa2023-02-01") == {"b", "e"}
    assert await _keys(client, world, date="eb2020-01-01") == {"d"}
    assert await _keys(client, world, **{"date:missing": "true"}) == set()
    assert await _keys(client, world, **{"date:missing": "false"}) == ALL


# ── identifier ───────────────────────────────────────────────────────────────


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="FMH-A") == {"a"}
    assert await _keys(client, world, identifier=f"{HISTORY_IDS}|FMH-B") == {"b"}
    assert await _keys(client, world, identifier="FMH-A,FMH-B") == {"a", "b"}
    assert await _keys(client, world, identifier="urn:wrong|FMH-A") == set()
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|FILL|FMH-A"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|FILL|FMH-B"})
        == set()
    )
    assert await _keys(client, world, **{"identifier:text": "history"}) == {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


# ── code / relationship / sex ────────────────────────────────────────────────


async def test_code_reads_every_condition(client, world):
    assert await _keys(client, world, code="44054006") == {"a"}
    assert await _keys(client, world, code="38341003") == {
        "a"
    }  # the second condition of `a`
    assert await _keys(client, world, code=f"{SCT}|195967001") == {"d"}
    assert await _keys(client, world, code="44054006,195967001") == {"a", "d"}
    assert await _keys(client, world, code="http://wrong|44054006") == set()
    assert await _keys(client, world, **{"code:text": "asthma"}) == {
        "b"
    }  # a text-only concept is found
    assert await _keys(client, world, **{"code:text": "hypertension"}) == {
        "a"
    }  # Coding.display
    assert await _keys(client, world, **{"code:missing": "true"}) == {"c", "e"}


async def test_relationship(client, world):
    assert await _keys(client, world, relationship="MTH") == {"a", "e"}
    assert await _keys(client, world, relationship=f"{ROLE_CODE}|FTH") == {"b"}
    assert await _keys(client, world, relationship=f"{ROLE_CODE}|") == {
        "a",
        "b",
        "d",
        "e",
    }
    assert await _keys(client, world, relationship="FTH,SIB") == {"b", "d"}
    assert await _keys(client, world, **{"relationship:text": "aunt"}) == {"c"}
    assert await _keys(client, world, **{"relationship:text": "mother"}) == {"a"}
    assert await _keys(client, world, **{"relationship:not": "MTH"}) == {"b", "c", "d"}
    assert await _keys(client, world, **{"relationship:missing": "true"}) == set()


async def test_sex(client, world):
    assert await _keys(client, world, sex="female") == {"a", "d"}
    assert await _keys(client, world, sex=f"{GENDER}|male") == {"b"}
    assert await _keys(client, world, sex="unknown") == {"c"}
    assert await _keys(client, world, sex="male,unknown") == {"b", "c"}
    assert await _keys(client, world, sex="http://wrong|female") == set()
    assert await _keys(client, world, **{"sex:missing": "true"}) == {"e"}


# ── patient ──────────────────────────────────────────────────────────────────


async def test_patient(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {
        "a",
        "c",
    }  # one target: a bare id works
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"b", "d"}
    assert await _keys(client, world, patient=f"{world['p1']},{world['p2']}") == {
        "a",
        "b",
        "c",
        "d",
    }
    assert await _keys(client, world, patient="999999") == set()
    assert await _keys(client, world, **{"patient:Patient": str(world["p1"])}) == {
        "a",
        "c",
    }
    assert await _keys(client, world, **{"patient:identifier": "urn:pts|P-9"}) == {"e"}
    assert await _keys(client, world, **{"patient:missing": "false"}) == ALL


# ── instantiates-canonical / instantiates-uri ────────────────────────────────


async def test_instantiates_canonical(client, world):
    assert await _keys(
        client, world, **{"instantiates-canonical": f"{CANONICAL}|1.0"}
    ) == {"a"}
    assert await _keys(client, world, **{"instantiates-canonical": CANONICAL}) == {
        "a"
    }  # the unversioned URL finds versions
    assert (
        await _keys(client, world, **{"instantiates-canonical": f"{CANONICAL}|2.0"})
        == set()
    )
    assert await _keys(
        client, world, **{"instantiates-canonical": "Questionnaire/5"}
    ) == {"a"}
    assert (
        await _keys(
            client,
            world,
            **{
                "instantiates-canonical": "http://example.org/fhir/PlanDefinition/other"
            },
        )
        == set()
    )
    assert await _keys(client, world, **{"instantiates-canonical:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }
    assert await _keys(
        client, world, **{"instantiates-canonical:missing": "false"}
    ) == {"a"}
    assert (
        await _status(client, **{"instantiates-canonical": "5"}) == 400
    )  # a bare id is ambiguous


async def test_instantiates_uri(client, world):
    assert await _keys(
        client, world, **{"instantiates-uri": "http://example.org/protocols/fh/1"}
    ) == {"a"}
    assert (
        await _keys(
            client, world, **{"instantiates-uri": "HTTP://EXAMPLE.ORG/PROTOCOLS/FH/1"}
        )
        == set()
    )  # case-sensitive
    assert await _keys(
        client, world, **{"instantiates-uri:below": "http://example.org/protocols/fh"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"instantiates-uri:below": "http://example.org/protocols"}
    ) == {"a", "c"}
    assert await _keys(
        client,
        world,
        **{"instantiates-uri:above": "http://example.org/protocols/fh/1/extra"},
    ) == {"a"}
    assert await _keys(client, world, **{"instantiates-uri:missing": "true"}) == {
        "b",
        "d",
        "e",
    }


# ── chaining ─────────────────────────────────────────────────────────────────


async def test_chains(client, world):
    assert await _keys(client, world, **{"patient.family": "Windsor"}) == {"a", "c"}
    assert await _keys(client, world, **{"patient.name": "Ben"}) == {"b", "d"}


async def test_bad_chains_are_400(client, world):
    assert await _status(client, **{"patient.nonsense": "x"}) == 400
    assert (
        await _status(client, **{"code.x": "y"}) == 400
    )  # a token cannot be chained through
    assert await _status(client, **{"relationship.x": "y"}) == 400
    assert await _status(client, **{"instantiates-uri.x": "y"}) == 400
    assert (
        await _status(client, **{"instantiates-canonical.name": "y"}) == 400
    )  # no target is a resource here


# ── _sort / _count / _offset / _total ────────────────────────────────────────


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "code",
        "date",
        "identifier",
        "instantiates-canonical",
        "instantiates-uri",
        "patient",
        "relationship",
        "sex",
        "status",
        "_id",
    ):
        assert (await _search(client, _sort=key))["total"] == 5, key
    assert await _status(client, _sort="name") == 400


async def test_sort_by_date(client, world):
    async def ids(**params):
        return [
            int(e["resource"]["id"]) for e in (await _search(client, **params))["entry"]
        ]

    assert await ids(_sort="date") == [
        world["d"],
        world["c"],
        world["a"],
        world["b"],
        world["e"],
    ]
    assert await ids(_sort="-date") == [
        world["e"],
        world["b"],
        world["a"],
        world["c"],
        world["d"],
    ]


async def test_default_sort_is_newest_first(client, world):
    got = [int(e["resource"]["id"]) for e in (await _search(client))["entry"]]
    assert got == sorted(got, reverse=True)


async def test_paging_and_total(client, world):
    page = await _search(client, _count=2, _sort="_id")
    assert page["total"] == 5 and len(page["entry"]) == 2
    assert any(link["relation"] == "next" for link in page["link"])
    nxt = await _search(client, _count=2, _offset=2, _sort="_id")
    assert not (
        {e["resource"]["id"] for e in page["entry"]}
        & {e["resource"]["id"] for e in nxt["entry"]}
    )
    assert "entry" not in await _search(client, _count=0)
    assert "total" not in await _search(client, _total="none")


async def test_summary_count_and_elements(client, world):
    assert (await _search(client, _summary="count"))["total"] == 5
    resource = (await _search(client, _elements="status", _id=str(world["a"])))[
        "entry"
    ][0]["resource"]
    assert resource["status"] == "completed"
    assert "condition" not in resource and "date" not in resource


# ── _include / _revinclude ───────────────────────────────────────────────────


async def test_include_patient(client, world):
    ids = f"{world['a']},{world['b']},{world['e']}"
    bundle = await _search(client, _id=ids, _include="FamilyMemberHistory:patient")
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }  # a logical patient adds nothing


async def test_revinclude_histories_on_the_patients_they_describe(client, world):
    bundle = await _other(
        client,
        "patients",
        _id=str(world["p1"]),
        _revinclude="FamilyMemberHistory:patient",
    )
    assert _of_type(bundle, "FamilyMemberHistory", "include") == {
        str(world["a"]),
        str(world["c"]),
    }
    bundle = await _other(
        client,
        "patients",
        _id=str(world["p2"]),
        _revinclude="FamilyMemberHistory:patient",
    )
    assert _of_type(bundle, "FamilyMemberHistory", "include") == {
        str(world["b"]),
        str(world["d"]),
    }


async def test_revinclude_is_tenant_scoped(client, other_client):
    from app.auth.dependencies import get_current_user
    from app.main import app
    from tests.conftest import make_test_user
    from tests.integration.family_member_history.conftest import HISTORY_PERMS

    def as_user(**kw):
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=HISTORY_PERMS, **kw
        )

    as_user()
    mine = await create_patient(client)
    await create_history(client, history_body(mine))
    as_user(sub="u-other", org_id="org-other")
    try:
        # The other org cannot see the patient, so nothing reaches its histories.
        bundle = await _other(
            other_client,
            "patients",
            _id=str(mine),
            _revinclude="FamilyMemberHistory:patient",
        )
        assert bundle["total"] == 0 and "entry" not in bundle
        theirs = await create_patient(other_client)
        bundle = await _other(
            other_client,
            "patients",
            _id=str(theirs),
            _revinclude="FamilyMemberHistory:patient",
        )
        assert _of_type(bundle, "FamilyMemberHistory", "include") == set()
    finally:
        as_user()


# ── combination rules / lenient vs strict ────────────────────────────────────


async def test_params_are_anded(client, world):
    assert await _keys(client, world, status="completed", relationship="MTH") == {
        "a",
        "e",
    }
    assert await _keys(client, world, status="partial", relationship="MTH") == set()
    assert await _keys(client, world, patient=str(world["p1"]), sex="female") == {"a"}
    assert await _keys(client, world, relationship="MTH", date="ge2024") == {"e"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"status:above": "x"}) == 400
    assert await _status(client, **{"patient:text": "x"}) == 400
    assert await _status(client, **{"date:exact": "2020"}) == 400
    assert await _status(client, **{"identifier:below": "x"}) == 400


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
        BASE + "/_search", data={"status": "partial", "patient": str(world["p2"])}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, status="partial")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/family-member-histories/{world['b']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "FamilyMemberHistory"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
