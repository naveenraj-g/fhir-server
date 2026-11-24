"""FHIR R4 search over MedicationKnowledge (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/medicationknowledge.html#search).

One block per search parameter - `status` a code, the CodeableConcept tokens (`code`,
`doseform`, `ingredient-code`, `classification`, `classification-type`, `monograph-type`,
`monitoring-program-type`), the two tokens over a plain string (`monitoring-program-name`,
`source-cost`), the single-target `manufacturer` and `ingredient` references and the
multi-target `monograph` reference - then chaining, `_include`/`_revinclude`, result
parameters, combination rules, lenient vs strict handling and POST _search.
"""

import pytest

from tests.integration.medication_knowledge.support import (
    API,
    ATC,
    BASE,
    CLASS_TYPES,
    RXNORM,
    SCT,
    concept,
    create_document,
    create_medication_knowledge,
    create_organization,
    document_body,
)

KEYS = ("a", "b", "c", "d", "e")
ALL = set(KEYS)
PROGRAMS = "http://example.org/program-types"


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
    """Two organizations, two documents and five entries with distinct, searchable values.
    Returns {key: id}.

      a  active tablet from org1; two ingredients (one coded, one a Substance); a classified
         (therapeutic / ATC N02AA05), monitored (Opioid-Safety), priced (Wholesaler-A) entry
         with a coded monograph pointing at doc1
      b  inactive capsule from org2; a Substance ingredient; a different classification; a
         monograph that is a Media (not a resource here)
      c  entered-in-error, coded only by text; a text-only monograph pointing at doc2
      d  a Substance ingredient and a logical manufacturer
      e  nothing coded
    """
    w = {}
    w["o1"] = await create_organization(client, name="Pharma One")
    w["o2"] = await create_organization(client, name="Pharma Two")
    w["doc1"] = await create_document(client, document_body())
    w["doc2"] = await create_document(client, document_body(status="superseded"))
    w["a"] = await create_medication_knowledge(
        client,
        {
            "status": "active",
            "code": concept(RXNORM, "1049502", "Oxycodone 10 MG ER tablet"),
            "doseForm": concept(SCT, "385057009", "Film-coated tablet"),
            "manufacturer": {"reference": f"Organization/{w['o1']}"},
            "ingredient": [
                {"itemCodeableConcept": concept(RXNORM, "7804", "Oxycodone")},
                {"itemReference": {"reference": "Substance/12345"}},
            ],
            "medicineClassification": [
                {
                    "type": concept(CLASS_TYPES, "therapeutic", "Therapeutic"),
                    "classification": [
                        concept(ATC, "N02AA05", "Oxycodone"),
                        concept(ATC, "N02A"),
                    ],
                }
            ],
            "monograph": [
                {
                    "type": concept(SCT, "374273001", "Drug monograph"),
                    "source": {"reference": f"DocumentReference/{w['doc1']}"},
                }
            ],
            "monitoringProgram": [
                {
                    "type": concept(PROGRAMS, "safety", "Safety"),
                    "name": "Opioid-Safety",
                }
            ],
            "cost": [
                {
                    "type": {"text": "wholesale"},
                    "source": "Wholesaler-A",
                    "cost": {"value": 12.5, "currency": "USD"},
                }
            ],
        },
    )
    w["b"] = await create_medication_knowledge(
        client,
        {
            "status": "inactive",
            "code": concept(RXNORM, "197696", "Ibuprofen"),
            "doseForm": concept(SCT, "385049006", "Capsule"),
            "manufacturer": {"reference": f"Organization/{w['o2']}"},
            "ingredient": [{"itemReference": {"reference": "Substance/67890"}}],
            "medicineClassification": [
                {
                    "type": concept(CLASS_TYPES, "pharmacological"),
                    "classification": [concept(ATC, "M01AE01", "Ibuprofen")],
                }
            ],
            "monograph": [{"source": {"reference": "Media/9"}}],
            "monitoringProgram": [{"name": "Other-Program"}],
            "cost": [
                {
                    "type": {"text": "retail"},
                    "source": "Wholesaler-B",
                    "cost": {"value": 3, "currency": "USD"},
                }
            ],
        },
    )
    w["c"] = await create_medication_knowledge(
        client,
        {
            "status": "entered-in-error",
            "code": {"text": "Compounded cream"},
            "monograph": [
                {
                    "type": {"text": "Patient leaflet"},
                    "source": {"reference": f"DocumentReference/{w['doc2']}"},
                }
            ],
        },
    )
    w["d"] = await create_medication_knowledge(
        client,
        {
            "manufacturer": {
                "identifier": {"system": "urn:mfr", "value": "M-9"},
                "display": "External",
            },
            "ingredient": [{"itemReference": {"reference": "Substance/12345"}}],
        },
    )
    w["e"] = await create_medication_knowledge(client, {})
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
    assert await _keys(client, world, status="inactive") == {"b"}
    assert await _keys(client, world, status="entered-in-error") == {
        "c"
    }  # the real FHIR code
    assert await _keys(client, world, status="active,inactive") == {"a", "b"}
    assert await _keys(
        client,
        world,
        status="http://hl7.org/fhir/CodeSystem/medicationknowledge-status|active",
    ) == {"a"}
    assert await _keys(client, world, status="http://wrong|active") == set()
    assert await _keys(client, world, status="no-such-code") == set()
    assert await _keys(client, world, **{"status:missing": "true"}) == {"d", "e"}
    assert await _keys(client, world, **{"status:missing": "false"}) == {"a", "b", "c"}


# -- the CodeableConcept tokens --------------------------------------------------------------


async def test_code(client, world):
    assert await _keys(client, world, code="1049502") == {"a"}
    assert await _keys(client, world, code=f"{RXNORM}|197696") == {"b"}
    assert await _keys(client, world, code="http://wrong|197696") == set()
    assert await _keys(client, world, code="1049502,197696") == {"a", "b"}
    assert await _keys(client, world, **{"code:text": "compounded"}) == {
        "c"
    }  # a text-only concept is found
    assert await _keys(client, world, **{"code:text": "ibuprofen"}) == {
        "b"
    }  # Coding.display
    assert await _keys(client, world, **{"code:missing": "true"}) == {"d", "e"}


async def test_doseform(client, world):
    assert await _keys(client, world, doseform="385057009") == {"a"}
    assert await _keys(client, world, doseform=f"{SCT}|385049006") == {"b"}
    assert await _keys(client, world, **{"doseform:text": "capsule"}) == {"b"}
    assert await _keys(client, world, **{"doseform:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


async def test_ingredient_code_reads_every_ingredient(client, world):
    assert await _keys(client, world, **{"ingredient-code": "7804"}) == {"a"}
    assert await _keys(client, world, **{"ingredient-code": f"{RXNORM}|7804"}) == {"a"}
    assert await _keys(client, world, **{"ingredient-code:text": "oxy"}) == {"a"}
    # an ingredient that is a reference carries no code
    assert await _keys(client, world, **{"ingredient-code:missing": "true"}) == {
        "b",
        "c",
        "d",
        "e",
    }


async def test_classification_reads_every_entry(client, world):
    assert await _keys(client, world, classification="N02AA05") == {"a"}
    assert await _keys(client, world, classification="N02A") == {
        "a"
    }  # the second classification of the same entry
    assert await _keys(client, world, classification=f"{ATC}|M01AE01") == {"b"}
    assert await _keys(client, world, classification="http://wrong|N02AA05") == set()
    assert await _keys(client, world, **{"classification:text": "ibuprofen"}) == {"b"}
    assert await _keys(client, world, **{"classification:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


async def test_classification_type(client, world):
    assert await _keys(client, world, **{"classification-type": "therapeutic"}) == {"a"}
    assert await _keys(
        client, world, **{"classification-type": f"{CLASS_TYPES}|pharmacological"}
    ) == {"b"}
    assert await _keys(client, world, **{"classification-type:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


async def test_monograph_type(client, world):
    assert await _keys(client, world, **{"monograph-type": "374273001"}) == {"a"}
    assert await _keys(client, world, **{"monograph-type": f"{SCT}|374273001"}) == {"a"}
    assert await _keys(client, world, **{"monograph-type:text": "patient leaflet"}) == {
        "c"
    }
    assert await _keys(client, world, **{"monograph-type:missing": "true"}) == {
        "b",
        "d",
        "e",
    }


async def test_monitoring_program_type(client, world):
    assert await _keys(client, world, **{"monitoring-program-type": "safety"}) == {"a"}
    assert await _keys(
        client, world, **{"monitoring-program-type": f"{PROGRAMS}|safety"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"monitoring-program-type": "http://wrong|safety"})
        == set()
    )
    assert await _keys(
        client, world, **{"monitoring-program-type:missing": "true"}
    ) == {
        "b",
        "c",
        "d",
        "e",
    }


# -- the two tokens over a plain string ------------------------------------------------------


async def test_monitoring_program_name(client, world):
    assert await _keys(
        client, world, **{"monitoring-program-name": "Opioid-Safety"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"monitoring-program-name": "Opioid-Safety,Other-Program"}
    ) == {"a", "b"}
    assert (
        await _keys(client, world, **{"monitoring-program-name": "opioid-safety"})
        == set()
    )  # an exact, case-sensitive code
    assert (
        await _keys(client, world, **{"monitoring-program-name": "urn:x|Opioid-Safety"})
        == set()
    )  # a string has no system
    assert await _keys(
        client, world, **{"monitoring-program-name:not": "Opioid-Safety"}
    ) == {"b", "c", "d", "e"}
    assert await _keys(
        client, world, **{"monitoring-program-name:missing": "true"}
    ) == {
        "c",
        "d",
        "e",
    }


async def test_source_cost(client, world):
    assert await _keys(client, world, **{"source-cost": "Wholesaler-A"}) == {"a"}
    assert await _keys(
        client, world, **{"source-cost": "Wholesaler-A,Wholesaler-B"}
    ) == {
        "a",
        "b",
    }
    assert await _keys(client, world, **{"source-cost": "wholesaler-a"}) == set()
    assert await _keys(client, world, **{"source-cost": "urn:x|Wholesaler-A"}) == set()
    assert await _keys(client, world, **{"source-cost:missing": "true"}) == {
        "c",
        "d",
        "e",
    }


# -- manufacturer / ingredient / monograph ---------------------------------------------------


async def test_manufacturer(client, world):
    assert await _keys(client, world, manufacturer=str(world["o1"])) == {
        "a"
    }  # one target: a bare id works
    assert await _keys(client, world, manufacturer=f"Organization/{world['o2']}") == {
        "b"
    }
    assert await _keys(client, world, manufacturer=f"{world['o1']},{world['o2']}") == {
        "a",
        "b",
    }
    assert await _keys(client, world, manufacturer="999999") == set()
    assert await _keys(client, world, **{"manufacturer:identifier": "urn:mfr|M-9"}) == {
        "d"
    }
    assert await _keys(client, world, **{"manufacturer:missing": "true"}) == {"c", "e"}


async def test_ingredient_has_one_target(client, world):
    """`ingredient` is Reference(Substance): one target, so a bare id works."""
    assert await _keys(client, world, ingredient="12345") == {"a", "d"}
    assert await _keys(client, world, ingredient="Substance/67890") == {"b"}
    assert await _keys(client, world, **{"ingredient:Substance": "12345"}) == {"a", "d"}
    assert await _keys(client, world, ingredient="Medication/12345") == set()
    assert await _keys(client, world, **{"ingredient:missing": "true"}) == {"c", "e"}


async def test_monograph_is_multi_target(client, world):
    assert (
        await _status(client, monograph=str(world["doc1"])) == 400
    )  # a bare id is ambiguous
    assert await _keys(
        client, world, monograph=f"DocumentReference/{world['doc1']}"
    ) == {"a"}
    assert await _keys(
        client, world, **{"monograph:DocumentReference": str(world["doc2"])}
    ) == {"c"}
    assert await _keys(client, world, monograph="Media/9") == {
        "b"
    }  # Media is not a resource here, but is indexed
    assert (
        await _keys(client, world, monograph=f"Media/{world['doc1']}") == set()
    )  # the type is part of the match
    assert await _keys(client, world, **{"monograph:missing": "true"}) == {"d", "e"}


# -- chaining --------------------------------------------------------------------------------


async def test_chains(client, world):
    assert await _keys(client, world, **{"manufacturer.name": "Pharma One"}) == {"a"}
    assert await _keys(client, world, **{"manufacturer.name": "Pharma"}) == {"a", "b"}
    assert await _keys(
        client, world, **{"monograph:DocumentReference.status": "current"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"monograph:DocumentReference.status": "superseded"}
    ) == {"c"}


async def test_bad_chains_are_400(client, world):
    assert await _status(client, **{"manufacturer.nonsense": "x"}) == 400
    assert (
        await _status(client, **{"monograph.status": "x"}) == 400
    )  # an untyped multi-target cannot be chained
    assert (
        await _status(client, **{"monograph:Media.status": "x"}) == 400
    )  # Media is not a resource here
    assert (
        await _status(client, **{"monograph:Patient.name": "x"}) == 400
    )  # not a target of monograph
    assert (
        await _status(client, **{"ingredient.name": "x"}) == 400
    )  # Substance is not a resource here
    assert await _status(client, **{"code.x": "y"}) == 400  # a token cannot be chained


# -- _sort / _count / _offset / _total -------------------------------------------------------


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "classification",
        "classification-type",
        "code",
        "doseform",
        "ingredient",
        "ingredient-code",
        "manufacturer",
        "monitoring-program-name",
        "monitoring-program-type",
        "monograph",
        "monograph-type",
        "source-cost",
        "status",
        "_id",
    ):
        assert (await _search(client, _sort=key))["total"] == 5, key


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
    assert "cost" not in resource and "ingredient" not in resource


async def test_summary_true_keeps_only_summary_elements(client, world):
    resource = (await _search(client, _summary="true", _id=str(world["a"])))["entry"][
        0
    ]["resource"]
    assert resource["status"] == "active" and "code" in resource
    assert "cost" not in resource and "monograph" not in resource


# -- _include / _revinclude ------------------------------------------------------------------


async def test_include_manufacturer_and_monograph(client, world):
    ids = ",".join(str(world[k]) for k in KEYS)
    bundle = await _search(client, _id=ids, _include="MedicationKnowledge:manufacturer")
    assert _of_type(bundle, "Organization", "include") == {
        str(world["o1"]),
        str(world["o2"]),
    }
    bundle = await _search(client, _id=ids, _include="MedicationKnowledge:monograph")
    assert _of_type(bundle, "DocumentReference", "include") == {
        str(world["doc1"]),
        str(world["doc2"]),
    }  # the Media monograph adds nothing


async def test_include_ingredient_is_unsupported_as_substance_is_not_a_resource(
    client, world
):
    """No target of `ingredient` (Substance) is a resource here, so there is nothing to include."""
    assert (
        await _status(
            client, _id=str(world["a"]), _include="MedicationKnowledge:ingredient"
        )
        == 400
    )


async def test_revinclude_on_the_organizations_and_documents(client, world):
    bundle = await _other(
        client,
        "organizations",
        _id=str(world["o1"]),
        _revinclude="MedicationKnowledge:manufacturer",
    )
    assert _of_type(bundle, "MedicationKnowledge", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "organizations",
        _id=f"{world['o1']},{world['o2']}",
        _revinclude="MedicationKnowledge:manufacturer",
    )
    assert _of_type(bundle, "MedicationKnowledge", "include") == {
        str(world["a"]),
        str(world["b"]),
    }
    bundle = await _other(
        client,
        "document-references",
        _id=str(world["doc2"]),
        _revinclude="MedicationKnowledge:monograph",
    )
    assert _of_type(bundle, "MedicationKnowledge", "include") == {str(world["c"])}


# -- combination rules / lenient vs strict ---------------------------------------------------


async def test_params_are_anded(client, world):
    assert await _keys(client, world, status="active", doseform="385057009") == {"a"}
    assert await _keys(client, world, status="inactive", doseform="385057009") == set()
    assert await _keys(
        client, world, code="1049502", **{"source-cost": "Wholesaler-A"}
    ) == {"a"}


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"manufacturer:text": "x"}) == 400
    assert await _status(client, **{"source-cost:text": "x"}) == 400
    assert await _status(client, **{"identifier": "x"}) == 200  # unknown, ignored
    assert await _status(client, **{"status:text": "x"}) == 400


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
        BASE + "/_search", data={"doseform": "385049006", "status": "inactive"}
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["b"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, **{"source-cost": "Wholesaler-B"})
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/medication-knowledge/{world['b']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "MedicationKnowledge"


async def test_empty_result(client, world):
    bundle = await _search(client, **{"source-cost": "nope"})
    assert bundle["total"] == 0 and "entry" not in bundle
