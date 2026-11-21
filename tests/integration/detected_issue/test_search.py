"""FHIR R4 search over DetectedIssue (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/detectedissue.html#search).

One block per search parameter — `code` and `identifier` are tokens, `identified` a date range
over a dateTime *or* a Period, `patient` a single-target reference, `author` a multi-target one
and `implicated` a Reference(Any) — then chaining, `_include`/`_revinclude`, result parameters,
combination rules, lenient vs strict handling and POST _search. There is deliberately no
`status` or `severity` search: R4 defines none for this resource.
"""

import pytest

from tests.integration.detected_issue.support import (
    ACT_CODE,
    API,
    BASE,
    ISSUE_IDS,
    V2_0203,
    allergy_body,
    category,
    condition_body,
    create_allergy_intolerance,
    create_condition,
    create_impression,
    create_issue,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    impression_body,
    issue_body,
)

KEYS = ("a", "b", "c", "d", "e")
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
    """Two patients, a practitioner, a practitioner role, a condition, an allergy and a clinical
    impression, plus five issues with distinct, searchable values. Returns {key: id}."""
    w = {}
    w["p1"] = await create_patient(
        client, {"active": True, "name": [{"family": "Windsor", "given": ["Anna"]}]}
    )
    w["p2"] = await create_patient(
        client, {"active": True, "name": [{"family": "Fairfax", "given": ["Ben"]}]}
    )
    w["pr"] = await create_practitioner(client)  # family "Careful"
    w["role"] = await create_practitioner_role(client)
    w["cond"] = await create_condition(client, condition_body(w["p1"]))
    w["allergy"] = await create_allergy_intolerance(client, allergy_body(w["p1"]))
    w["imp"] = await create_impression(client, impression_body(w["p1"]))
    w["a"] = await create_issue(
        client,
        issue_body(
            w["p1"],
            "final",
            identifier=[
                {
                    "system": ISSUE_IDS,
                    "value": "DI-A",
                    "type": {
                        "coding": [{"system": V2_0203, "code": "FILL"}],
                        "text": "Issue id",
                    },
                }
            ],
            code=category("DUPTHPY", "Duplicate therapy alert"),
            identifiedDateTime="2023-01-15T09:30:00Z",
            author={"reference": f"Practitioner/{w['pr']}"},
            implicated=[
                {"reference": f"Condition/{w['cond']}"},
                {"reference": "MedicationRequest/90001"},
            ],
        ),
    )
    w["b"] = await create_issue(
        client,
        issue_body(
            w["p2"],
            "preliminary",
            identifier=[{"system": ISSUE_IDS, "value": "DI-B"}],
            code={"text": "Drug interaction"},
            identifiedPeriod={"start": "2024-01-01", "end": "2024-03-01"},
            author={"reference": f"PractitionerRole/{w['role']}"},
            implicated=[
                {"reference": f"AllergyIntolerance/{w['allergy']}"},
                {"reference": f"ClinicalImpression/{w['imp']}"},
            ],
        ),
    )
    w["c"] = await create_issue(
        client,
        issue_body(
            w["p1"],
            "amended",
            code=category("DRG"),
            identifiedPeriod={"start": "2022-06-01"},
            author={"reference": "Device/5"},
            implicated=[{"reference": f"Patient/{w['p2']}"}],
        ),
    )
    w["d"] = await create_issue(
        client, {"status": "cancelled", "identifiedDateTime": "2019"}
    )
    w["e"] = await create_issue(
        client,
        {
            "status": "final",
            "patient": {
                "identifier": {"system": "urn:pts", "value": "P-9"},
                "display": "External",
            },
            "identifiedDateTime": "2024-03-15T00:00:00Z",
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


async def test_there_is_no_status_or_severity_search(client, world):
    """R4 defines no `status` / `severity` search parameter for DetectedIssue: unknown parameters."""
    for name, value in (("status", "final"), ("severity", "high")):
        lenient = await client.get(BASE + "/", params={name: value})
        assert lenient.status_code == 200
        assert any(e["search"]["mode"] == "outcome" for e in lenient.json()["entry"])
        strict = await client.get(
            BASE + "/", params={name: value}, headers={"Prefer": "handling=strict"}
        )
        assert strict.status_code == 400


# ── identified ───────────────────────────────────────────────────────────────


async def test_identified_reads_a_datetime_and_a_period(client, world):
    assert await _keys(client, world, identified="2023-01-15") == {"a"}
    assert await _keys(client, world, identified="2023") == {"a"}
    assert await _keys(client, world, identified="2024") == {
        "b",
        "e",
    }  # b's period and e's instant lie inside 2024
    assert await _keys(client, world, identified="ge2024-01-01") == {
        "b",
        "c",
        "e",
    }  # c's open-ended period reaches it
    assert await _keys(client, world, identified="lt2023-01-01") == {"c", "d"}
    assert await _keys(client, world, identified="sa2023-02-01") == {"b", "e"}
    assert await _keys(client, world, identified="eb2020-01-01") == {"d"}
    assert await _keys(client, world, **{"identified:missing": "true"}) == set()
    assert await _keys(client, world, **{"identified:missing": "false"}) == ALL


# ── identifier ───────────────────────────────────────────────────────────────


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="DI-A") == {"a"}
    assert await _keys(client, world, identifier=f"{ISSUE_IDS}|DI-B") == {"b"}
    assert await _keys(client, world, identifier="DI-A,DI-B") == {"a", "b"}
    assert await _keys(client, world, identifier="urn:wrong|DI-A") == set()
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|FILL|DI-A"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|FILL|DI-B"})
        == set()
    )
    assert await _keys(client, world, **{"identifier:text": "issue"}) == {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


# ── code ─────────────────────────────────────────────────────────────────────


async def test_code(client, world):
    assert await _keys(client, world, code="DUPTHPY") == {"a"}
    assert await _keys(client, world, code=f"{ACT_CODE}|DUPTHPY") == {"a"}
    assert await _keys(client, world, code="http://wrong|DUPTHPY") == set()
    assert await _keys(client, world, code="DUPTHPY,DRG") == {"a", "c"}
    assert await _keys(client, world, **{"code:text": "drug"}) == {
        "b"
    }  # a text-only concept is found
    assert await _keys(client, world, **{"code:text": "duplicate"}) == {
        "a"
    }  # Coding.display
    assert await _keys(client, world, **{"code:missing": "true"}) == {"d", "e"}


# ── patient ──────────────────────────────────────────────────────────────────


async def test_patient(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {
        "a",
        "c",
    }  # one target: a bare id works
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"b"}
    assert await _keys(client, world, patient=f"{world['p1']},{world['p2']}") == {
        "a",
        "b",
        "c",
    }
    assert await _keys(client, world, patient="999999") == set()
    assert await _keys(client, world, **{"patient:Patient": str(world["p1"])}) == {
        "a",
        "c",
    }
    assert await _keys(client, world, **{"patient:identifier": "urn:pts|P-9"}) == {"e"}
    assert await _keys(client, world, **{"patient:missing": "true"}) == {"d"}
    assert await _keys(client, world, **{"patient:missing": "false"}) == {
        "a",
        "b",
        "c",
        "e",
    }


# ── author ───────────────────────────────────────────────────────────────────


async def test_author_is_multi_target(client, world):
    assert (
        await _status(client, author=str(world["pr"])) == 400
    )  # a bare id is ambiguous
    assert await _keys(client, world, author=f"Practitioner/{world['pr']}") == {"a"}
    assert await _keys(client, world, **{"author:Practitioner": str(world["pr"])}) == {
        "a"
    }
    assert await _keys(client, world, author=f"PractitionerRole/{world['role']}") == {
        "b"
    }
    assert await _keys(client, world, author="Device/5") == {
        "c"
    }  # a Device is searchable by reference
    assert (
        await _keys(client, world, author=f"Practitioner/{world['role']}") == set()
    )  # the type is part of the match
    assert await _keys(client, world, **{"author:missing": "true"}) == {"d", "e"}


# ── implicated ───────────────────────────────────────────────────────────────


async def test_implicated_is_reference_any(client, world):
    assert (
        await _status(client, implicated=str(world["cond"])) == 400
    )  # a bare id is ambiguous
    assert await _keys(client, world, implicated=f"Condition/{world['cond']}") == {"a"}
    assert await _keys(client, world, implicated="MedicationRequest/90001") == {
        "a"
    }  # not a resource here: by reference
    assert await _keys(
        client, world, implicated=f"AllergyIntolerance/{world['allergy']}"
    ) == {"b"}
    assert await _keys(
        client, world, implicated=f"ClinicalImpression/{world['imp']}"
    ) == {"b"}
    assert await _keys(client, world, implicated=f"Patient/{world['p2']}") == {"c"}
    assert await _keys(
        client, world, **{"implicated:Condition": str(world["cond"])}
    ) == {"a"}
    assert (
        await _keys(client, world, implicated=f"Condition/{world['allergy']}") == set()
    )  # the type is part of the match
    assert await _keys(client, world, **{"implicated:missing": "true"}) == {"d", "e"}
    assert await _keys(client, world, **{"implicated:missing": "false"}) == {
        "a",
        "b",
        "c",
    }


# ── chaining ─────────────────────────────────────────────────────────────────


async def test_chains(client, world):
    assert await _keys(client, world, **{"patient.family": "Windsor"}) == {"a", "c"}
    assert await _keys(client, world, **{"author:Practitioner.family": "Careful"}) == {
        "a"
    }
    assert await _keys(
        client, world, **{"implicated:Condition.patient": str(world["p1"])}
    ) == {"a"}
    assert await _keys(
        client, world, **{"implicated:AllergyIntolerance.patient": str(world["p1"])}
    ) == {"b"}
    assert await _keys(
        client, world, **{"implicated:ClinicalImpression.patient": str(world["p1"])}
    ) == {"b"}
    assert await _keys(client, world, **{"implicated:Patient.family": "Fairfax"}) == {
        "c"
    }


async def test_bad_chains_are_400(client, world):
    assert await _status(client, **{"patient.nonsense": "x"}) == 400
    assert (
        await _status(client, **{"author.family": "x"}) == 400
    )  # an untyped multi-target cannot be chained
    assert (
        await _status(client, **{"author:Device.model": "x"}) == 400
    )  # Device is not searchable here
    assert (
        await _status(client, **{"implicated:MedicationRequest.status": "x"}) == 400
    )  # not built yet
    assert (
        await _status(client, **{"code.x": "y"}) == 400
    )  # a token cannot be chained through
    assert await _status(client, **{"identified.x": "y"}) == 400


# ── _sort / _count / _offset / _total ────────────────────────────────────────


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "author",
        "code",
        "identified",
        "identifier",
        "implicated",
        "patient",
        "_id",
    ):
        assert (await _search(client, _sort=key))["total"] == 5, key
    assert await _status(client, _sort="status") == 400


async def test_sort_by_identified(client, world):
    async def ids(**params):
        return [
            int(e["resource"]["id"]) for e in (await _search(client, **params))["entry"]
        ]

    assert await ids(_sort="identified") == [
        world["d"],
        world["c"],
        world["a"],
        world["b"],
        world["e"],
    ]
    assert await ids(_sort="-identified") == [
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
    assert resource["status"] == "final"
    assert "implicated" not in resource and "detail" not in resource


# ── _include / _revinclude ───────────────────────────────────────────────────


async def test_include_patient_and_author(client, world):
    ids = f"{world['a']},{world['b']},{world['c']},{world['e']}"
    bundle = await _search(client, _id=ids, _include="DetectedIssue:patient")
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }  # a logical patient adds nothing
    bundle = await _search(client, _id=ids, _include="DetectedIssue:author")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "PractitionerRole", "include") == {
        str(world["role"])
    }  # a Device adds nothing
    bundle = await _search(
        client, _id=ids, _include="DetectedIssue:author:Practitioner"
    )
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "PractitionerRole", "include") == set()


async def test_include_implicated(client, world):
    ids = f"{world['a']},{world['b']},{world['c']}"
    bundle = await _search(client, _id=ids, _include="DetectedIssue:implicated")
    assert _of_type(bundle, "Condition", "include") == {
        str(world["cond"])
    }  # a MedicationRequest adds nothing
    assert _of_type(bundle, "AllergyIntolerance", "include") == {str(world["allergy"])}
    assert _of_type(bundle, "ClinicalImpression", "include") == {str(world["imp"])}
    assert _of_type(bundle, "Patient", "include") == {str(world["p2"])}
    bundle = await _search(
        client, _id=ids, _include="DetectedIssue:implicated:Condition"
    )
    assert _of_type(bundle, "Condition", "include") == {str(world["cond"])}
    assert _of_type(bundle, "AllergyIntolerance", "include") == set()


async def test_revinclude_issues_on_the_resources_they_point_at(client, world):
    bundle = await _other(
        client, "patients", _id=str(world["p1"]), _revinclude="DetectedIssue:patient"
    )
    assert _of_type(bundle, "DetectedIssue", "include") == {
        str(world["a"]),
        str(world["c"]),
    }
    bundle = await _other(
        client,
        "practitioners",
        _id=str(world["pr"]),
        _revinclude="DetectedIssue:author",
    )
    assert _of_type(bundle, "DetectedIssue", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "practitioner-roles",
        _id=str(world["role"]),
        _revinclude="DetectedIssue:author",
    )
    assert _of_type(bundle, "DetectedIssue", "include") == {str(world["b"])}


async def test_revinclude_is_tenant_scoped(client, other_client):
    from app.auth.dependencies import get_current_user
    from app.main import app
    from tests.conftest import make_test_user
    from tests.integration.detected_issue.conftest import ISSUE_PERMS

    def as_user(**kw):
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=ISSUE_PERMS, **kw
        )

    as_user()
    mine = await create_patient(client)
    await create_issue(client, issue_body(mine))
    as_user(sub="u-other", org_id="org-other")
    try:
        # The other org cannot see the patient, so nothing reaches its issues.
        bundle = await _other(
            other_client, "patients", _id=str(mine), _revinclude="DetectedIssue:patient"
        )
        assert bundle["total"] == 0 and "entry" not in bundle
        theirs = await create_patient(other_client)
        bundle = await _other(
            other_client,
            "patients",
            _id=str(theirs),
            _revinclude="DetectedIssue:patient",
        )
        assert _of_type(bundle, "DetectedIssue", "include") == set()
    finally:
        as_user()


# ── combination rules / lenient vs strict ────────────────────────────────────


async def test_params_are_anded(client, world):
    assert await _keys(client, world, code="DUPTHPY", identified="2023") == {"a"}
    assert await _keys(client, world, code="DRG", identified="2023") == set()
    assert await _keys(
        client, world, patient=str(world["p1"]), identified="ge2024-01-01"
    ) == {"c"}
    assert await _keys(client, world, patient=str(world["p1"]), code="DUPTHPY") == {"a"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"patient:text": "x"}) == 400
    assert await _status(client, **{"identified:exact": "2020"}) == 400
    assert await _status(client, **{"identifier:below": "x"}) == 400
    assert await _status(client, **{"code:nonsense": "x"}) == 400


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
        BASE + "/_search", data={"code": "DRG", "patient": str(world["p1"])}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["c"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, identifier="DI-B")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/detected-issues/{world['b']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "DetectedIssue"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
