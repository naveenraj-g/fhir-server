"""FHIR R4 search over Consent (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/consent.html#search).

One block per search parameter - `status`, the CodeableConcept and Coding tokens (`scope`,
`category`, `action`, `purpose`, `security-label`), `identifier`, the dates (`date` a dateTime,
`period` the provision's Period), the single-target `patient` and `organization`, the
multi-target `consentor`, `actor` and `source-reference` and the Reference(Any) `data` - then
chaining, `_include`/`_revinclude`, result parameters, combination rules, lenient vs strict
handling and POST _search. The parameters read the top-level `provision` only.
"""

import pytest

from tests.integration.consent.support import (
    ACTION,
    API,
    BASE,
    CONFIDENTIALITY,
    CONSENT_IDS,
    LOINC,
    PURPOSE,
    ROLE,
    SCOPE,
    V2_0203,
    concept,
    consent_body,
    create_consent,
    create_document,
    create_observation,
    create_organization,
    create_patient,
    create_practitioner,
    create_related_person,
    document_body,
    observation_body,
    related_person_body,
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


def _actor(reference: str) -> dict:
    return {"role": concept(ROLE, "IRCP"), "reference": {"reference": reference}}


@pytest.fixture
async def world(client):
    """Two patients, a related person, an organization, a practitioner, a document and an
    observation, and five consents with distinct, searchable values. Returns {key: id}.

      a  active, patient-privacy, for p1; categories 59284-0 and 59284-1; dated 2026-01-15; p1
         and the related person agree; the organization is the custodian; sourced from the
         document; permit 2026-01-15..2027-01-14 for the practitioner and the organization,
         actions access and disclose, purpose TREAT, label R, data the observation; id C-A
      b  draft, research, for p2; dated 2026-06; the practitioner agrees; sourced from `a`; a deny
         that starts 2026-06-01 and never ends
      c  inactive, adr; no patient, no date; the organization is the custodian; a source
         attachment instead of a reference
      d  rejected, treatment; patient is an absolute URL; id C-D; a provision whose only content
         is a nested provision (the practitioner as actor) - which is not indexed
      e  proposed, patient-privacy; nothing else
    """
    w = {}
    w["p1"] = await create_patient(client)
    w["p2"] = await create_patient(client)
    w["rp"] = await create_related_person(client, related_person_body(w["p1"]))
    w["org"] = await create_organization(client, name="Consent Org")
    w["pr"] = await create_practitioner(client)
    w["doc"] = await create_document(client, document_body())
    w["obs"] = await create_observation(client, observation_body(w["p1"]))
    w["a"] = await create_consent(
        client,
        consent_body(
            w["p1"],
            status="active",
            identifier=[
                {
                    "system": CONSENT_IDS,
                    "value": "C-A",
                    "type": {
                        "coding": [{"system": V2_0203, "code": "FILL"}],
                        "text": "Consent id",
                    },
                }
            ],
            category=[
                concept(LOINC, "59284-0", "Consent Document"),
                concept(LOINC, "59284-1"),
            ],
            dateTime="2026-01-15T09:00:00Z",
            performer=[
                {"reference": f"Patient/{w['p1']}"},
                {"reference": f"RelatedPerson/{w['rp']}"},
            ],
            organization=[{"reference": f"Organization/{w['org']}"}],
            sourceReference={"reference": f"DocumentReference/{w['doc']}"},
            provision={
                "type": "permit",
                "period": {"start": "2026-01-15", "end": "2027-01-14"},
                "actor": [
                    _actor(f"Practitioner/{w['pr']}"),
                    _actor(f"Organization/{w['org']}"),
                ],
                "action": [
                    concept(ACTION, "access", "Access"),
                    concept(ACTION, "disclose"),
                ],
                "purpose": [
                    {"system": PURPOSE, "code": "TREAT", "display": "Treatment"}
                ],
                "securityLabel": [{"system": CONFIDENTIALITY, "code": "R"}],
                "data": [
                    {
                        "meaning": "instance",
                        "reference": {"reference": f"Observation/{w['obs']}"},
                    }
                ],
            },
        ),
    )
    w["b"] = await create_consent(
        client,
        consent_body(
            w["p2"],
            status="draft",
            scope=concept(SCOPE, "research"),
            dateTime="2026-06",
            performer=[{"reference": f"Practitioner/{w['pr']}"}],
            sourceReference={"reference": f"Consent/{w['a']}"},
            provision={"type": "deny", "period": {"start": "2026-06-01"}},
        ),
    )
    w["c"] = await create_consent(
        client,
        consent_body(
            status="inactive",
            scope=concept(SCOPE, "adr"),
            organization=[{"reference": f"Organization/{w['org']}"}],
            sourceAttachment={"contentType": "application/pdf", "title": "signed"},
        ),
    )
    d_body = consent_body(
        status="rejected",
        scope=concept(SCOPE, "treatment"),
        identifier=[{"system": CONSENT_IDS, "value": "C-D"}],
        provision={"provision": [{"actor": [_actor(f"Practitioner/{w['pr']}")]}]},
    )
    d_body["patient"] = {"reference": "https://other.example.org/fhir/Patient/9"}
    w["d"] = await create_consent(client, d_body)
    w["e"] = await create_consent(client, consent_body(status="proposed"))
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


# -- _id / _lastUpdated / status -------------------------------------------------------------


async def test_id(client, world):
    assert await _keys(client, world, _id=str(world["a"])) == {"a"}
    assert await _keys(client, world, _id="999999") == set()
    assert await _keys(client, world, **{"_id:not": str(world["a"])}) == ALL - {"a"}


async def test_last_updated(client, world):
    assert await _keys(client, world, _lastUpdated="ge2020-01-01") == ALL
    assert await _keys(client, world, _lastUpdated="lt2020-01-01") == set()


async def test_status(client, world):
    assert await _keys(client, world, status="active") == {"a"}
    assert await _keys(client, world, status="draft,rejected") == {"b", "d"}
    assert await _keys(
        client, world, status="http://hl7.org/fhir/consent-state-codes|inactive"
    ) == {"c"}
    assert await _keys(client, world, status="http://wrong|active") == set()
    assert await _keys(client, world, status="no-such-code") == set()
    assert await _keys(client, world, **{"status:not": "active"}) == ALL - {"a"}
    assert await _keys(client, world, **{"status:missing": "true"}) == set()


# -- the tokens: scope / category / action / purpose / security-label -------------------------


async def test_scope(client, world):
    assert await _keys(client, world, scope="patient-privacy") == {"a", "e"}
    assert await _keys(client, world, scope=f"{SCOPE}|research") == {"b"}
    assert await _keys(client, world, scope="http://wrong|research") == set()
    assert await _keys(client, world, **{"scope:not": "patient-privacy"}) == {
        "b",
        "c",
        "d",
    }


async def test_category_reads_every_entry(client, world):
    assert await _keys(client, world, category="59284-0") == ALL
    assert await _keys(client, world, category="59284-1") == {"a"}
    assert await _keys(client, world, **{"category:text": "consent document"}) == {"a"}


async def test_action_reads_every_action_of_the_top_level_provision(client, world):
    assert await _keys(client, world, action="access") == {"a"}
    assert await _keys(client, world, action="disclose") == {"a"}
    assert await _keys(client, world, action=f"{ACTION}|access") == {"a"}
    assert await _keys(client, world, **{"action:text": "access"}) == {"a"}
    assert await _keys(client, world, **{"action:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }


async def test_purpose_and_security_label_are_codings(client, world):
    assert await _keys(client, world, purpose="TREAT") == {"a"}
    assert await _keys(client, world, purpose=f"{PURPOSE}|TREAT") == {"a"}
    assert await _keys(client, world, purpose="http://wrong|TREAT") == set()
    assert await _keys(client, world, **{"purpose:text": "treatment"}) == {"a"}
    assert await _keys(client, world, **{"security-label": "R"}) == {"a"}
    assert await _keys(client, world, **{"security-label": f"{CONFIDENTIALITY}|R"}) == {
        "a"
    }
    assert await _keys(client, world, **{"security-label:missing": "true"}) == ALL - {
        "a"
    }


# -- identifier / date / period ---------------------------------------------------------------


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="C-A") == {"a"}
    assert await _keys(client, world, identifier=f"{CONSENT_IDS}|C-D") == {"d"}
    assert await _keys(client, world, identifier="C-A,C-D") == {"a", "d"}
    assert await _keys(client, world, identifier="urn:wrong|C-A") == set()
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|FILL|C-A"}
    ) == {"a"}
    assert await _keys(client, world, **{"identifier:text": "consent id"}) == {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {
        "b",
        "c",
        "e",
    }


async def test_date(client, world):
    assert await _keys(client, world, date="2026-01-15") == {"a"}
    assert await _keys(client, world, date="2026-06") == {"b"}  # a partial date
    assert await _keys(client, world, date="ge2026-01-01") == {"a", "b"}
    assert await _keys(client, world, date="lt2026-02-01") == {"a"}
    assert await _keys(client, world, **{"date:missing": "true"}) == {"c", "d", "e"}


async def test_period_is_a_range_search_over_the_top_level_provision(client, world):
    assert await _keys(client, world, period="ge2026-03-01") == {
        "a",
        "b",
    }  # overlaps above
    assert await _keys(client, world, period="le2026-03-01") == {"a"}  # overlaps below
    assert await _keys(client, world, period="ge2030-01-01") == {"b"}  # open ended
    assert await _keys(client, world, period="sa2026-02-01") == {"b"}  # starts after
    assert await _keys(client, world, period="eb2026-01-01") == set()
    assert await _keys(client, world, **{"period:missing": "true"}) == {"c", "d", "e"}


# -- patient / organization / consentor / source-reference ------------------------------------


async def test_patient_has_one_target_so_a_bare_id_works(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {"a"}
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"b"}
    assert await _keys(client, world, **{"patient:missing": "true"}) == {
        "c",
        "e",
    }  # not d: a URL


async def test_organization_has_one_target_so_a_bare_id_works(client, world):
    assert await _keys(client, world, organization=str(world["org"])) == {"a", "c"}
    assert await _keys(client, world, **{"organization:missing": "true"}) == {
        "b",
        "d",
        "e",
    }


async def test_consentor_is_multi_target(client, world):
    assert await _status(client, consentor=str(world["p1"])) == 400
    assert await _keys(client, world, consentor=f"Patient/{world['p1']}") == {"a"}
    assert await _keys(client, world, consentor=f"RelatedPerson/{world['rp']}") == {"a"}
    assert await _keys(
        client, world, **{"consentor:Practitioner": str(world["pr"])}
    ) == {"b"}
    assert await _keys(client, world, consentor=f"Patient/{world['pr']}") == set()
    assert await _keys(client, world, **{"consentor:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


async def test_source_reference_is_multi_target(client, world):
    assert await _status(client, **{"source-reference": str(world["doc"])}) == 400
    assert await _keys(
        client, world, **{"source-reference": f"DocumentReference/{world['doc']}"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"source-reference": f"Consent/{world['a']}"}
    ) == {"b"}
    assert await _keys(
        client, world, **{"source-reference:Consent": str(world["a"])}
    ) == {"b"}
    # a source attachment is not a reference, so it counts as missing
    assert await _keys(client, world, **{"source-reference:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


# -- actor / data (the top-level provision only) ----------------------------------------------


async def test_actor_is_multi_target_and_reads_every_actor(client, world):
    assert await _status(client, actor=str(world["pr"])) == 400
    assert await _keys(client, world, actor=f"Practitioner/{world['pr']}") == {"a"}
    assert await _keys(client, world, actor=f"Organization/{world['org']}") == {"a"}
    assert await _keys(client, world, **{"actor:Organization": str(world["org"])}) == {
        "a"
    }
    # `d` names the practitioner only in a nested provision: R4's expression does not reach it
    assert await _keys(client, world, **{"actor:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }


async def test_data_is_reference_any(client, world):
    assert await _status(client, data=str(world["obs"])) == 400
    assert await _keys(client, world, data=f"Observation/{world['obs']}") == {"a"}
    assert await _keys(client, world, **{"data:Observation": str(world["obs"])}) == {
        "a"
    }
    assert await _keys(client, world, data=f"Patient/{world['obs']}") == set()
    assert await _keys(client, world, **{"data:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }


# -- chaining --------------------------------------------------------------------------------


async def test_chains(client, world):
    assert await _keys(client, world, **{"patient.active": "true"}) == {"a", "b"}
    assert await _keys(client, world, **{"organization.name": "Consent Org"}) == {
        "a",
        "c",
    }
    assert await _keys(client, world, **{"consentor:Practitioner.active": "true"}) <= {
        "b"
    }
    assert await _keys(client, world, **{"actor:Organization.name": "Consent Org"}) == {
        "a"
    }
    assert await _keys(client, world, **{"data:Observation.status": "final"}) == {"a"}
    assert await _keys(
        client, world, **{"source-reference:DocumentReference.status": "current"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"source-reference:Consent.status": "active"}
    ) == {"b"}


async def test_bad_chains_are_400(client, world):
    assert await _status(client, **{"patient.nonsense": "x"}) == 400
    assert await _status(client, **{"actor.name": "x"}) == 400  # untyped multi-target
    assert (
        await _status(client, **{"data.status": "x"}) == 400
    )  # untyped Reference(Any)
    assert (
        await _status(client, **{"actor:Device.name": "x"}) == 400
    )  # not a resource here
    assert (
        await _status(client, **{"source-reference:Contract.status": "x"}) == 400
    )  # not a resource here
    assert await _status(client, **{"scope.x": "y"}) == 400  # a token cannot be chained


# -- _sort / _count / _offset / _total -------------------------------------------------------


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "action",
        "actor",
        "category",
        "consentor",
        "data",
        "date",
        "identifier",
        "organization",
        "patient",
        "period",
        "purpose",
        "scope",
        "security-label",
        "source-reference",
        "status",
        "_id",
    ):
        assert (await _search(client, _sort=key))["total"] == 5, key


async def test_sort_by_date(client, world):
    async def ids(**params):
        return [
            int(e["resource"]["id"]) for e in (await _search(client, **params))["entry"]
        ]

    assert await ids(**{"date:missing": "false", "_sort": "date"}) == [
        world["a"],
        world["b"],
    ]
    assert await ids(**{"date:missing": "false", "_sort": "-date"}) == [
        world["b"],
        world["a"],
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
    assert resource["status"] == "active"
    assert "provision" not in resource and "policy" not in resource
    assert "category" in resource  # a mandatory element (min 1) is always kept


# -- _include / _revinclude ------------------------------------------------------------------


async def test_include_patient_organization_consentor_and_source(client, world):
    ids = ",".join(str(world[k]) for k in KEYS)
    bundle = await _search(client, _id=ids, _include="Consent:patient")
    assert _of_type(bundle, "Patient", "include") == {
        str(world["p1"]),
        str(world["p2"]),
    }
    bundle = await _search(client, _id=ids, _include="Consent:organization")
    assert _of_type(bundle, "Organization", "include") == {str(world["org"])}
    bundle = await _search(client, _id=ids, _include="Consent:consentor")
    assert _of_type(bundle, "Patient", "include") == {str(world["p1"])}
    assert _of_type(bundle, "RelatedPerson", "include") == {str(world["rp"])}
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    bundle = await _search(client, _id=ids, _include="Consent:source-reference")
    assert _of_type(bundle, "DocumentReference", "include") == {str(world["doc"])}
    # `a` is a match itself here, so it is not repeated as an include; searched alone, `b` brings it in
    bundle = await _search(
        client, _id=str(world["b"]), _include="Consent:source-reference"
    )
    assert _of_type(bundle, "Consent", "include") == {str(world["a"])}


async def test_include_actor_and_data(client, world):
    ids = ",".join(str(world[k]) for k in KEYS)
    bundle = await _search(client, _id=ids, _include="Consent:actor")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "Organization", "include") == {str(world["org"])}
    bundle = await _search(client, _id=ids, _include="Consent:data")
    assert _of_type(bundle, "Observation", "include") == {str(world["obs"])}
    bundle = await _search(client, _id=ids, _include="Consent:actor:Organization")
    assert _of_type(bundle, "Practitioner", "include") == set()


async def test_revinclude_on_the_resources_a_consent_points_at(client, world):
    bundle = await _other(
        client, "patients", _id=str(world["p1"]), _revinclude="Consent:patient"
    )
    assert _of_type(bundle, "Consent", "include") == {str(world["a"])}
    bundle = await _other(
        client, "patients", _id=str(world["p1"]), _revinclude="Consent:consentor"
    )
    assert _of_type(bundle, "Consent", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "organizations",
        _id=str(world["org"]),
        _revinclude="Consent:organization",
    )
    assert _of_type(bundle, "Consent", "include") == {str(world["a"]), str(world["c"])}
    bundle = await _other(
        client, "organizations", _id=str(world["org"]), _revinclude="Consent:actor"
    )
    assert _of_type(bundle, "Consent", "include") == {str(world["a"])}
    bundle = await _other(
        client, "practitioners", _id=str(world["pr"]), _revinclude="Consent:consentor"
    )
    assert _of_type(bundle, "Consent", "include") == {str(world["b"])}
    bundle = await _other(
        client, "practitioners", _id=str(world["pr"]), _revinclude="Consent:actor"
    )
    assert _of_type(bundle, "Consent", "include") == {str(world["a"])}
    bundle = await _other(
        client, "related-persons", _id=str(world["rp"]), _revinclude="Consent:consentor"
    )
    assert _of_type(bundle, "Consent", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "document-references",
        _id=str(world["doc"]),
        _revinclude="Consent:source-reference",
    )
    assert _of_type(bundle, "Consent", "include") == {str(world["a"])}
    bundle = await _search(
        client, _id=str(world["a"]), _revinclude="Consent:source-reference"
    )
    assert _of_type(bundle, "Consent", "include") == {str(world["b"])}


# -- combination rules / lenient vs strict ---------------------------------------------------


async def test_params_are_anded(client, world):
    assert await _keys(client, world, status="active", scope="patient-privacy") == {"a"}
    assert await _keys(client, world, status="draft", scope="patient-privacy") == set()
    assert await _keys(
        client, world, patient=str(world["p1"]), action="access", date="ge2026-01-01"
    ) == {"a"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"patient:text": "x"}) == 400
    assert await _status(client, **{"date:exact": "2020"}) == 400
    assert await _status(client, **{"identifier:below": "x"}) == 400
    assert await _status(client, **{"status:text": "x"}) == 400
    assert await _status(client, date="banana") == 400
    assert await _status(client, period="banana") == 400


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


# -- POST _search / Bundle shape -------------------------------------------------------------


async def test_post_search_form_encoded(client, world):
    resp = await client.post(
        BASE + "/_search", data={"status": "draft", "scope": "research"}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, identifier="C-D")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/consents/{world['d']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "Consent"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
