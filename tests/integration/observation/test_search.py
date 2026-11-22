"""FHIR R4 search over Observation (https://www.hl7.org/fhir/R4/search.html,
https://www.hl7.org/fhir/R4/observation.html#search).

One block per search parameter family — `status`, `date`, `identifier`; the CodeableConcept tokens
(`category`, `code`, `method`, `data-absent-reason`, `value-concept` and their `component-*` /
`combo-*` forms); the value searches (`value-quantity`, `value-string`, `value-date`); the
references (`patient`, `subject`, `encounter`, `device`, `specimen`, `performer`, `based-on`,
`part-of`, `focus`, `has-member`, `derived-from`) — then the **composite** searches
(`code-value-quantity`, `component-code-value-concept`, ... — a code and a value of the *same*
element), chaining, `_include`/`_revinclude`, result parameters, lenient vs strict handling and
POST _search.
"""

import pytest

from tests.integration.observation.support import (
    API,
    BASE,
    CATEGORY,
    LOINC,
    OBSERVATION_IDS,
    SCT,
    UCUM,
    V2_0203,
    concept,
    create_encounter,
    create_immunization,
    create_observation,
    create_patient,
    create_practitioner,
    create_practitioner_role,
    create_procedure,
    encounter_body,
    immunization_body,
    loinc,
    observation_body,
    procedure_body,
    quantity,
)

KEYS = ("a", "b", "c", "d", "e", "f")
ALL = set(KEYS)
DAR = "http://terminology.hl7.org/CodeSystem/data-absent-reason"
DAR_UNKNOWN = concept(DAR, "unknown")


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
    """Two patients, a practitioner, a practitioner role, an encounter, a procedure and an
    immunization, plus six observations with distinct, searchable values. Returns {key: id}.

      a  blood-pressure panel of p1: components systolic 142 and diastolic 91 mmHg
      b  body weight of p2: 70 kg, effective over a period
      c  smoking status of p1: a coded value (former smoker)
      d  lab report with a Group subject: a string value, a component with no value, groups a and b
      e  body height with a logical subject: no value, data absent
      f  illness onset of p2: a dateTime value, components with coded values
    """
    w = {}
    w["p1"] = await create_patient(
        client, {"active": True, "name": [{"family": "Windsor", "given": ["Anna"]}]}
    )
    w["p2"] = await create_patient(
        client, {"active": True, "name": [{"family": "Fairfax", "given": ["Ben"]}]}
    )
    w["pr"] = await create_practitioner(client)  # family "Careful"
    w["role"] = await create_practitioner_role(client)
    w["enc"] = await create_encounter(client, encounter_body())
    w["proc"] = await create_procedure(client, procedure_body(w["p1"]))
    w["imm"] = await create_immunization(client, immunization_body(w["p1"]))
    w["a"] = await create_observation(
        client,
        observation_body(
            w["p1"],
            "final",
            identifier=[
                {
                    "system": OBSERVATION_IDS,
                    "value": "OBS-A",
                    "type": {
                        "coding": [{"system": V2_0203, "code": "FILL"}],
                        "text": "Obs id",
                    },
                }
            ],
            category=[concept(CATEGORY, "vital-signs", "Vital Signs")],
            code=loinc("85354-9", "Blood pressure panel"),
            effectiveDateTime="2023-01-15T09:30:00Z",
            encounter={"reference": f"Encounter/{w['enc']}"},
            performer=[{"reference": f"Practitioner/{w['pr']}"}],
            method=concept(SCT, "37931006", "Auscultation"),
            partOf=[{"reference": f"Procedure/{w['proc']}"}],
            device={"reference": "Device/5"},
            specimen={"reference": "Specimen/310001"},
            component=[
                {
                    "code": loinc("8480-6", "Systolic blood pressure"),
                    "valueQuantity": quantity(142),
                },
                {
                    "code": loinc("8462-4", "Diastolic blood pressure"),
                    "valueQuantity": quantity(91),
                },
            ],
        ),
    )
    w["b"] = await create_observation(
        client,
        observation_body(
            w["p2"],
            "preliminary",
            identifier=[{"system": OBSERVATION_IDS, "value": "OBS-B"}],
            category=[concept(CATEGORY, "vital-signs")],
            code=loinc("29463-7", "Body weight"),
            effectivePeriod={"start": "2024-01-01", "end": "2024-03-01"},
            performer=[{"reference": f"PractitionerRole/{w['role']}"}],
            valueQuantity={"value": 70, "unit": "kg", "system": UCUM, "code": "kg"},
            derivedFrom=[{"reference": f"Observation/{w['a']}"}],
        ),
    )
    w["c"] = await create_observation(
        client,
        observation_body(
            w["p1"],
            "amended",
            category=[concept(CATEGORY, "social-history")],
            code=loinc("72166-2", "Tobacco smoking status"),
            effectiveDateTime="2022-06-01T00:00:00Z",
            valueCodeableConcept={
                "coding": [{"system": SCT, "code": "8517006", "display": "Ex-smoker"}],
                "text": "Former smoker",
            },
            focus=[{"reference": "Condition/120001"}],
            basedOn=[{"reference": "ServiceRequest/80001"}],
        ),
    )
    w["d"] = await create_observation(
        client,
        {
            "status": "cancelled",
            "code": loinc("11502-2", "Laboratory report"),
            "subject": {"reference": "Group/430001"},
            "effectiveInstant": "2019-05-05T10:00:00Z",
            "valueString": "Positive for influenza",
            "partOf": [{"reference": f"Immunization/{w['imm']}"}],
            "hasMember": [
                {"reference": f"Observation/{w['a']}"},
                {"reference": f"Observation/{w['b']}"},
            ],
            "component": [
                {"code": loinc("5778-6", "Colour"), "dataAbsentReason": DAR_UNKNOWN}
            ],
        },
    )
    w["e"] = await create_observation(
        client,
        {
            "status": "final",
            "code": loinc("8302-2", "Body height"),
            "subject": {
                "identifier": {"system": "urn:pts", "value": "P-9"},
                "display": "External",
            },
            "dataAbsentReason": DAR_UNKNOWN,
        },
    )
    w["f"] = await create_observation(
        client,
        observation_body(
            w["p2"],
            "final",
            code=loinc("11368-8", "Date of illness onset"),
            effectiveDateTime="2024-02-10T08:00:00Z",
            valueDateTime="2024-02-10",
            component=[
                {
                    "code": loinc("8480-6"),
                    "valueCodeableConcept": concept(SCT, "75540009", "High"),
                },
                {
                    "code": loinc("8462-4"),
                    "valueCodeableConcept": concept(SCT, "17621005", "Normal"),
                },
            ],
        ),
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


# ── _id / _lastUpdated / status / date / identifier ──────────────────────────


async def test_id(client, world):
    assert await _keys(client, world, _id=str(world["a"])) == {"a"}
    assert await _keys(client, world, _id="999999") == set()
    assert await _keys(client, world, **{"_id:not": str(world["a"])}) == ALL - {"a"}


async def test_last_updated(client, world):
    assert await _keys(client, world, _lastUpdated="ge2020-01-01") == ALL
    assert await _keys(client, world, _lastUpdated="lt2020-01-01") == set()


async def test_status(client, world):
    assert await _keys(client, world, status="final") == {"a", "e", "f"}
    assert await _keys(client, world, status="preliminary") == {"b"}
    assert await _keys(client, world, status="amended") == {"c"}
    assert await _keys(client, world, status="cancelled") == {"d"}
    assert (
        await _keys(client, world, status="entered-in-error") == set()
    )  # the real FHIR code
    assert await _keys(client, world, status="final,amended") == {"a", "c", "e", "f"}
    assert await _keys(
        client, world, status="http://hl7.org/fhir/observation-status|final"
    ) == {"a", "e", "f"}
    assert await _keys(client, world, status="http://wrong|final") == set()
    assert await _keys(client, world, status="no-such-code") == set()
    assert await _keys(client, world, **{"status:not": "final"}) == {"b", "c", "d"}
    assert await _keys(client, world, **{"status:missing": "true"}) == set()


async def test_date_reads_a_datetime_an_instant_and_a_period(client, world):
    assert await _keys(client, world, date="2023-01-15") == {"a"}
    assert await _keys(client, world, date="2023") == {"a"}
    assert await _keys(client, world, date="2024") == {
        "b",
        "f",
    }  # b's period and f's instant lie inside 2024
    assert await _keys(client, world, date="2019-05-05") == {"d"}  # an effectiveInstant
    assert await _keys(client, world, date="ge2024-01-01") == {"b", "f"}
    assert await _keys(client, world, date="lt2023-01-01") == {"c", "d"}
    assert await _keys(client, world, date="sa2023-02-01") == {"b", "f"}
    assert await _keys(client, world, date="eb2020-01-01") == {"d"}
    assert await _keys(client, world, **{"date:missing": "true"}) == {"e"}
    assert await _keys(client, world, **{"date:missing": "false"}) == ALL - {"e"}


async def test_identifier(client, world):
    assert await _keys(client, world, identifier="OBS-A") == {"a"}
    assert await _keys(client, world, identifier=f"{OBSERVATION_IDS}|OBS-B") == {"b"}
    assert await _keys(client, world, identifier="OBS-A,OBS-B") == {"a", "b"}
    assert await _keys(client, world, identifier="urn:wrong|OBS-A") == set()
    assert await _keys(
        client, world, **{"identifier:of-type": f"{V2_0203}|FILL|OBS-A"}
    ) == {"a"}
    assert (
        await _keys(client, world, **{"identifier:of-type": f"{V2_0203}|FILL|OBS-B"})
        == set()
    )
    assert await _keys(client, world, **{"identifier:text": "obs id"}) == {"a"}
    assert await _keys(client, world, **{"identifier:missing": "true"}) == {
        "c",
        "d",
        "e",
        "f",
    }


# ── tokens: category / code / method / data-absent-reason / value-concept ────


async def test_category(client, world):
    assert await _keys(client, world, category="vital-signs") == {"a", "b"}
    assert await _keys(client, world, category=f"{CATEGORY}|social-history") == {"c"}
    assert await _keys(client, world, category="http://wrong|vital-signs") == set()
    assert await _keys(client, world, **{"category:text": "vital"}) == {
        "a"
    }  # Coding.display
    assert await _keys(client, world, **{"category:missing": "true"}) == {"d", "e", "f"}


async def test_code(client, world):
    assert await _keys(client, world, code="85354-9") == {"a"}
    assert await _keys(client, world, code=f"{LOINC}|29463-7") == {"b"}
    assert await _keys(client, world, code="http://wrong|29463-7") == set()
    assert await _keys(client, world, code="85354-9,29463-7") == {"a", "b"}
    assert await _keys(client, world, **{"code:text": "blood pressure"}) == {"a"}
    assert await _keys(client, world, **{"code:text": "laboratory"}) == {"d"}
    assert await _keys(client, world, **{"code:missing": "true"}) == set()


async def test_method_and_data_absent_reason(client, world):
    assert await _keys(client, world, method=f"{SCT}|37931006") == {"a"}
    assert await _keys(client, world, **{"method:text": "ausc"}) == {"a"}
    assert await _keys(client, world, **{"method:missing": "true"}) == ALL - {"a"}
    assert await _keys(client, world, **{"data-absent-reason": "unknown"}) == {
        "e"
    }  # not the component-level one
    assert await _keys(client, world, **{"data-absent-reason:missing": "false"}) == {
        "e"
    }


async def test_value_concept(client, world):
    assert await _keys(client, world, **{"value-concept": "8517006"}) == {"c"}
    assert await _keys(client, world, **{"value-concept": f"{SCT}|8517006"}) == {"c"}
    assert await _keys(client, world, **{"value-concept:text": "former"}) == {
        "c"
    }  # CodeableConcept.text
    assert await _keys(client, world, **{"value-concept:text": "ex-smoker"}) == {
        "c"
    }  # Coding.display
    assert (
        await _keys(client, world, **{"value-concept": "75540009"}) == set()
    )  # a component value, not the Observation's


async def test_component_tokens(client, world):
    assert await _keys(client, world, **{"component-code": "8480-6"}) == {"a", "f"}
    assert await _keys(client, world, **{"component-code": f"{LOINC}|8462-4"}) == {
        "a",
        "f",
    }
    assert (
        await _keys(client, world, **{"component-code": "85354-9"}) == set()
    )  # the Observation's own code
    assert await _keys(client, world, **{"component-code:missing": "true"}) == {
        "b",
        "c",
        "e",
    }
    assert await _keys(
        client, world, **{"component-data-absent-reason": "unknown"}
    ) == {"d"}
    assert await _keys(client, world, **{"component-value-concept": "75540009"}) == {
        "f"
    }
    assert await _keys(client, world, **{"component-value-concept": "8517006"}) == set()


async def test_combo_tokens_are_the_union(client, world):
    assert await _keys(client, world, **{"combo-code": "85354-9"}) == {
        "a"
    }  # the Observation's code
    assert await _keys(client, world, **{"combo-code": "8480-6"}) == {
        "a",
        "f",
    }  # a component's code
    assert await _keys(client, world, **{"combo-code": "85354-9,8480-6"}) == {"a", "f"}
    assert await _keys(client, world, **{"combo-data-absent-reason": "unknown"}) == {
        "d",
        "e",
    }
    assert await _keys(client, world, **{"combo-value-concept": "8517006"}) == {"c"}
    assert await _keys(
        client, world, **{"combo-value-concept": "75540009,8517006"}
    ) == {"c", "f"}
    assert await _keys(client, world, **{"combo-value-concept:text": "high"}) == {"f"}


# ── values: quantity / string / date ─────────────────────────────────────────


async def test_value_quantity(client, world):
    assert await _keys(client, world, **{"value-quantity": "70"}) == {"b"}
    assert await _keys(client, world, **{"value-quantity": "gt50"}) == {"b"}
    assert await _keys(client, world, **{"value-quantity": "lt70"}) == set()
    assert await _keys(client, world, **{"value-quantity": f"70|{UCUM}|kg"}) == {"b"}
    assert await _keys(client, world, **{"value-quantity": "70||kg"}) == {"b"}
    assert await _keys(client, world, **{"value-quantity": "70||g"}) == set()
    assert (
        await _keys(client, world, **{"value-quantity": "142"}) == set()
    )  # a component value, not the Observation's
    assert await _keys(client, world, **{"value-quantity:missing": "true"}) == ALL - {
        "b"
    }


async def test_component_value_quantity(client, world):
    assert await _keys(client, world, **{"component-value-quantity": "gt140"}) == {"a"}
    assert await _keys(client, world, **{"component-value-quantity": "91"}) == {"a"}
    assert await _keys(
        client, world, **{"component-value-quantity": f"142|{UCUM}|mm[Hg]"}
    ) == {"a"}
    assert await _keys(client, world, **{"component-value-quantity": "70"}) == set()
    assert await _keys(
        client, world, **{"component-value-quantity:missing": "true"}
    ) == ALL - {"a"}


async def test_combo_value_quantity_is_the_union(client, world):
    assert await _keys(client, world, **{"combo-value-quantity": "70"}) == {"b"}
    assert await _keys(client, world, **{"combo-value-quantity": "91"}) == {"a"}
    assert await _keys(client, world, **{"combo-value-quantity": "gt60"}) == {"a", "b"}


async def test_quantity_rejects_bad_values(client, world):
    assert await _status(client, **{"value-quantity": "abc"}) == 400
    assert await _status(client, **{"value-quantity:contains": "1"}) == 400


async def test_value_string(client, world):
    assert await _keys(client, world, **{"value-string": "positive"}) == {
        "d"
    }  # starts-with, case-insensitive
    assert await _keys(client, world, **{"value-string:contains": "influenza"}) == {"d"}
    assert await _keys(client, world, **{"value-string": "influenza"}) == set()
    assert await _keys(client, world, **{"value-string": "former"}) == {
        "c"
    }  # also reads CodeableConcept.text
    assert await _keys(client, world, **{"value-string:missing": "true"}) == {
        "a",
        "b",
        "e",
        "f",
    }
    assert (
        await _status(client, **{"value-string:exact": "x"}) == 400
    )  # only the normalized form is stored


async def test_value_date(client, world):
    assert await _keys(client, world, **{"value-date": "2024-02-10"}) == {"f"}
    assert await _keys(client, world, **{"value-date": "ge2024-01-01"}) == {"f"}
    assert await _keys(client, world, **{"value-date": "lt2024-01-01"}) == set()
    assert await _keys(client, world, **{"value-date:missing": "true"}) == ALL - {"f"}


# ── composites: a code and a value of the same element ───────────────────────


async def test_code_value_quantity(client, world):
    assert await _keys(client, world, **{"code-value-quantity": "29463-7$70"}) == {"b"}
    assert await _keys(
        client, world, **{"code-value-quantity": f"{LOINC}|29463-7$gt50|{UCUM}|kg"}
    ) == {"b"}
    assert (
        await _keys(client, world, **{"code-value-quantity": "29463-7$lt50"}) == set()
    )
    assert (
        await _keys(client, world, **{"code-value-quantity": "85354-9$70"}) == set()
    )  # b's value, a's code
    assert (
        await _keys(client, world, **{"code-value-quantity": "8480-6$gt100"}) == set()
    )  # a component's code is not `code`
    assert await _keys(
        client, world, **{"code-value-quantity": "29463-7$70,29463-7$80"}
    ) == {"b"}  # OR


async def test_code_value_concept_string_and_date(client, world):
    assert await _keys(client, world, **{"code-value-concept": "72166-2$8517006"}) == {
        "c"
    }
    assert await _keys(
        client, world, **{"code-value-concept": f"{LOINC}|72166-2${SCT}|8517006"}
    ) == {"c"}
    assert (
        await _keys(client, world, **{"code-value-concept": "72166-2$75540009"})
        == set()
    )
    assert await _keys(client, world, **{"code-value-string": "11502-2$positive"}) == {
        "d"
    }
    assert (
        await _keys(client, world, **{"code-value-string": "11502-2$negative"}) == set()
    )
    assert await _keys(client, world, **{"code-value-string": "72166-2$former"}) == {
        "c"
    }
    assert await _keys(client, world, **{"code-value-date": "11368-8$2024-02-10"}) == {
        "f"
    }
    assert await _keys(
        client, world, **{"code-value-date": "11368-8$ge2024-01-01"}
    ) == {"f"}
    assert (
        await _keys(client, world, **{"code-value-date": "11368-8$lt2024-01-01"})
        == set()
    )
    assert (
        await _keys(client, world, **{"code-value-date": "29463-7$ge2024-01-01"})
        == set()
    )


async def test_component_composites_pair_a_code_with_its_own_value(client, world):
    assert await _keys(
        client, world, **{"component-code-value-quantity": "8480-6$gt140"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"component-code-value-quantity": "8462-4$91"}
    ) == {"a"}
    # the systolic code with the diastolic value (or the reverse) must NOT match
    assert (
        await _keys(client, world, **{"component-code-value-quantity": "8462-4$gt140"})
        == set()
    )
    assert (
        await _keys(client, world, **{"component-code-value-quantity": "8480-6$lt100"})
        == set()
    )
    assert await _keys(
        client, world, **{"component-code-value-quantity": "8480-6$142,8462-4$91"}
    ) == {"a"}
    assert await _keys(
        client, world, **{"component-code-value-concept": "8480-6$75540009"}
    ) == {"f"}
    assert await _keys(
        client, world, **{"component-code-value-concept": "8462-4$17621005"}
    ) == {"f"}
    assert (
        await _keys(
            client, world, **{"component-code-value-concept": "8480-6$17621005"}
        )
        == set()
    )
    assert await _keys(
        client,
        world,
        **{"component-code-value-concept": f"{LOINC}|8480-6${SCT}|75540009"},
    ) == {"f"}


async def test_combo_composites_read_the_observation_and_its_components(client, world):
    assert await _keys(
        client, world, **{"combo-code-value-quantity": "8480-6$142"}
    ) == {"a"}  # a component
    assert await _keys(
        client, world, **{"combo-code-value-quantity": "29463-7$70"}
    ) == {"b"}  # the Observation
    assert (
        await _keys(client, world, **{"combo-code-value-quantity": "8480-6$70"})
        == set()
    )
    assert (
        await _keys(client, world, **{"combo-code-value-quantity": "8462-4$gt140"})
        == set()
    )
    assert await _keys(
        client, world, **{"combo-code-value-concept": "8480-6$75540009"}
    ) == {"f"}
    assert await _keys(
        client, world, **{"combo-code-value-concept": "72166-2$8517006"}
    ) == {"c"}
    assert (
        await _keys(client, world, **{"combo-code-value-concept": "72166-2$75540009"})
        == set()
    )


async def test_composite_syntax_errors_are_400(client, world):
    assert await _status(client, **{"code-value-quantity": "29463-7"}) == 400  # no `$`
    assert (
        await _status(client, **{"code-value-quantity": "29463-7$70$80"}) == 400
    )  # three parts
    assert (
        await _status(client, **{"code-value-quantity": "29463-7$"}) == 400
    )  # an empty part
    assert (
        await _status(client, **{"code-value-quantity": "29463-7$abc"}) == 400
    )  # not a quantity
    assert (
        await _status(client, **{"component-code-value-quantity:missing": "true"})
        == 400
    )  # no modifiers
    assert (
        await _status(client, **{"code-value-quantity.x": "1$2"}) == 400
    )  # a composite cannot be chained
    assert await _status(client, _sort="code-value-quantity") == 400  # nor sorted


# ── patient / subject / encounter / device / specimen ────────────────────────


async def test_patient(client, world):
    assert await _keys(client, world, patient=str(world["p1"])) == {
        "a",
        "c",
    }  # one target: a bare id works
    assert await _keys(client, world, patient=f"Patient/{world['p2']}") == {"b", "f"}
    assert await _keys(client, world, patient=f"{world['p1']},{world['p2']}") == {
        "a",
        "b",
        "c",
        "f",
    }
    assert await _keys(client, world, patient="999999") == set()
    assert await _keys(client, world, **{"patient:Patient": str(world["p1"])}) == {
        "a",
        "c",
    }
    # a Group or a logical subject is not a Patient, so it counts as missing `patient`
    assert await _keys(client, world, **{"patient:missing": "true"}) == {"d", "e"}
    assert await _keys(client, world, **{"patient:missing": "false"}) == {
        "a",
        "b",
        "c",
        "f",
    }


async def test_subject_is_multi_target(client, world):
    assert (
        await _status(client, subject=str(world["p1"])) == 400
    )  # a bare id is ambiguous
    assert await _keys(client, world, subject=f"Patient/{world['p1']}") == {"a", "c"}
    assert await _keys(client, world, **{"subject:Patient": str(world["p2"])}) == {
        "b",
        "f",
    }
    assert await _keys(client, world, subject="Group/430001") == {
        "d"
    }  # the type is part of the match
    assert await _keys(client, world, subject=f"Group/{world['p1']}") == set()
    assert await _keys(client, world, **{"subject:identifier": "urn:pts|P-9"}) == {"e"}
    assert await _keys(client, world, **{"subject:missing": "true"}) == set()


async def test_encounter_device_and_specimen(client, world):
    assert await _keys(client, world, encounter=str(world["enc"])) == {"a"}
    assert await _keys(client, world, encounter=f"Encounter/{world['enc']}") == {"a"}
    assert await _keys(client, world, **{"encounter:missing": "true"}) == ALL - {"a"}
    assert (
        await _status(client, device="5") == 400
    )  # Device | DeviceMetric: a bare id is ambiguous
    assert await _keys(client, world, device="Device/5") == {"a"}
    assert await _keys(client, world, **{"device:Device": "5"}) == {"a"}
    assert await _keys(client, world, device="DeviceMetric/5") == set()
    assert await _keys(client, world, specimen="310001") == {
        "a"
    }  # one target: a bare id works
    assert await _keys(client, world, **{"specimen:missing": "true"}) == ALL - {"a"}


# ── performer / based-on / part-of / focus / has-member / derived-from ───────


async def test_performer_is_multi_target(client, world):
    assert (
        await _status(client, performer=str(world["pr"])) == 400
    )  # a bare id is ambiguous
    assert await _keys(client, world, performer=f"Practitioner/{world['pr']}") == {"a"}
    assert await _keys(
        client, world, **{"performer:Practitioner": str(world["pr"])}
    ) == {"a"}
    assert await _keys(
        client, world, performer=f"PractitionerRole/{world['role']}"
    ) == {"b"}
    assert (
        await _keys(client, world, performer=f"Practitioner/{world['role']}") == set()
    )  # the type is part of the match
    assert await _keys(client, world, **{"performer:missing": "true"}) == {
        "c",
        "d",
        "e",
        "f",
    }


async def test_reference_table_parameters(client, world):
    assert await _keys(client, world, **{"based-on": "ServiceRequest/80001"}) == {"c"}
    assert await _status(client, **{"based-on": "80001"}) == 400
    assert await _keys(client, world, **{"part-of": f"Procedure/{world['proc']}"}) == {
        "a"
    }
    assert await _keys(
        client, world, **{"part-of": f"Immunization/{world['imm']}"}
    ) == {"d"}
    assert await _keys(client, world, focus="Condition/120001") == {
        "c"
    }  # Reference(Any)
    assert await _keys(client, world, **{"focus:Condition": "120001"}) == {"c"}
    assert await _keys(
        client, world, **{"has-member": f"Observation/{world['a']}"}
    ) == {"d"}
    assert await _keys(
        client, world, **{"has-member": f"Observation/{world['b']}"}
    ) == {"d"}
    assert await _keys(
        client, world, **{"derived-from": f"Observation/{world['a']}"}
    ) == {"b"}
    assert await _keys(client, world, **{"derived-from:missing": "true"}) == ALL - {"b"}
    assert await _keys(client, world, **{"has-member:missing": "false"}) == {"d"}


# ── chaining ─────────────────────────────────────────────────────────────────


async def test_chains(client, world):
    assert await _keys(client, world, **{"patient.family": "Windsor"}) == {"a", "c"}
    assert await _keys(client, world, **{"subject:Patient.name": "Ben"}) == {"b", "f"}
    assert await _keys(
        client, world, **{"performer:Practitioner.family": "Careful"}
    ) == {"a"}
    assert await _keys(client, world, **{"encounter.status": "in-progress"}) == {"a"}
    assert await _keys(client, world, **{"has-member:Observation.code": "85354-9"}) == {
        "d"
    }
    assert await _keys(
        client, world, **{"derived-from:Observation.patient": str(world["p1"])}
    ) == {"b"}
    assert await _keys(
        client, world, **{"part-of:Procedure.patient": str(world["p1"])}
    ) == {"a"}
    assert await _keys(
        client, world, **{"part-of:Immunization.patient": str(world["p1"])}
    ) == {"d"}


async def test_bad_chains_are_400(client, world):
    assert await _status(client, **{"patient.nonsense": "x"}) == 400
    assert (
        await _status(client, **{"subject.family": "x"}) == 400
    )  # an untyped multi-target cannot be chained
    assert (
        await _status(client, **{"subject:Group.name": "x"}) == 400
    )  # Group is not searchable here
    assert (
        await _status(client, **{"device:Device.model": "x"}) == 400
    )  # likewise Device
    assert (
        await _status(client, **{"based-on:DeviceRequest.status": "x"}) == 400
    )  # not built yet
    assert (
        await _status(client, **{"code.x": "y"}) == 400
    )  # a token cannot be chained through
    assert await _status(client, **{"value-quantity.x": "y"}) == 400


# ── _sort / _count / _offset / _total ────────────────────────────────────────


async def test_sort_by_every_declared_param(client, world):
    for key in (
        "based-on",
        "category",
        "code",
        "combo-code",
        "combo-data-absent-reason",
        "combo-value-concept",
        "combo-value-quantity",
        "component-code",
        "component-data-absent-reason",
        "component-value-concept",
        "component-value-quantity",
        "data-absent-reason",
        "date",
        "derived-from",
        "device",
        "encounter",
        "focus",
        "has-member",
        "identifier",
        "method",
        "part-of",
        "patient",
        "performer",
        "specimen",
        "status",
        "subject",
        "value-concept",
        "value-date",
        "value-quantity",
        "value-string",
        "_id",
    ):
        assert (await _search(client, _sort=key))["total"] == 6, key


async def test_sort_by_date_and_value(client, world):
    async def ids(**params):
        return [
            int(e["resource"]["id"]) for e in (await _search(client, **params))["entry"]
        ]

    assert await ids(**{"date:missing": "false", "_sort": "date"}) == [
        world["d"],
        world["c"],
        world["a"],
        world["b"],
        world["f"],
    ]
    assert await ids(**{"date:missing": "false", "_sort": "-date"}) == [
        world["f"],
        world["b"],
        world["a"],
        world["c"],
        world["d"],
    ]
    assert await ids(
        **{
            "component-value-quantity:missing": "false",
            "_sort": "-component-value-quantity",
        }
    ) == [world["a"]]


async def test_default_sort_is_newest_first(client, world):
    got = [int(e["resource"]["id"]) for e in (await _search(client))["entry"]]
    assert got == sorted(got, reverse=True)


async def test_paging_and_total(client, world):
    page = await _search(client, _count=2, _sort="_id")
    assert page["total"] == 6 and len(page["entry"]) == 2
    assert any(link["relation"] == "next" for link in page["link"])
    nxt = await _search(client, _count=2, _offset=2, _sort="_id")
    assert not (
        {e["resource"]["id"] for e in page["entry"]}
        & {e["resource"]["id"] for e in nxt["entry"]}
    )
    assert "entry" not in await _search(client, _count=0)
    assert "total" not in await _search(client, _total="none")


async def test_summary_count_and_elements(client, world):
    assert (await _search(client, _summary="count"))["total"] == 6
    resource = (await _search(client, _elements="status", _id=str(world["a"])))[
        "entry"
    ][0]["resource"]
    assert resource["status"] == "final"
    assert "component" not in resource and "method" not in resource


# ── _include / _revinclude ───────────────────────────────────────────────────


async def test_include_subject_encounter_and_performer(client, world):
    ids = f"{world['a']},{world['b']},{world['d']},{world['e']}"
    for param in ("patient", "subject"):
        bundle = await _search(client, _id=ids, _include=f"Observation:{param}")
        assert _of_type(bundle, "Patient", "include") == {
            str(world["p1"]),
            str(world["p2"]),
        }  # a Group adds nothing
    bundle = await _search(client, _id=ids, _include="Observation:encounter")
    assert _of_type(bundle, "Encounter", "include") == {str(world["enc"])}
    bundle = await _search(client, _id=ids, _include="Observation:performer")
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "PractitionerRole", "include") == {str(world["role"])}
    bundle = await _search(
        client, _id=ids, _include="Observation:performer:Practitioner"
    )
    assert _of_type(bundle, "Practitioner", "include") == {str(world["pr"])}
    assert _of_type(bundle, "PractitionerRole", "include") == set()


async def test_include_has_member_derived_from_and_part_of(client, world):
    bundle = await _search(
        client, _id=str(world["d"]), _include="Observation:has-member"
    )
    assert _of_type(bundle, "Observation", "include") == {
        str(world["a"]),
        str(world["b"]),
    }
    bundle = await _search(
        client, _id=str(world["b"]), _include="Observation:derived-from"
    )
    assert _of_type(bundle, "Observation", "include") == {str(world["a"])}
    ids = f"{world['a']},{world['d']}"
    bundle = await _search(client, _id=ids, _include="Observation:part-of")
    assert _of_type(bundle, "Procedure", "include") == {str(world["proc"])}
    assert _of_type(bundle, "Immunization", "include") == {str(world["imm"])}
    bundle = await _search(client, _id=str(world["c"]), _include="Observation:focus")
    assert (
        _of_type(bundle, "Condition", "include") == set()
    )  # Condition/120001 does not exist here: nothing to add


async def test_revinclude_observations_on_the_resources_they_point_at(client, world):
    for param in ("patient", "subject"):
        bundle = await _other(
            client, "patients", _id=str(world["p1"]), _revinclude=f"Observation:{param}"
        )
        assert _of_type(bundle, "Observation", "include") == {
            str(world["a"]),
            str(world["c"]),
        }
    bundle = await _other(
        client, "encounters", _id=str(world["enc"]), _revinclude="Observation:encounter"
    )
    assert _of_type(bundle, "Observation", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "practitioners",
        _id=str(world["pr"]),
        _revinclude="Observation:performer",
    )
    assert _of_type(bundle, "Observation", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "practitioner-roles",
        _id=str(world["role"]),
        _revinclude="Observation:performer",
    )
    assert _of_type(bundle, "Observation", "include") == {str(world["b"])}
    bundle = await _other(
        client, "procedures", _id=str(world["proc"]), _revinclude="Observation:part-of"
    )
    assert _of_type(bundle, "Observation", "include") == {str(world["a"])}
    bundle = await _other(
        client,
        "immunizations",
        _id=str(world["imm"]),
        _revinclude="Observation:part-of",
    )
    assert _of_type(bundle, "Observation", "include") == {str(world["d"])}


async def test_revinclude_has_member_and_derived_from_on_itself(client, world):
    bundle = await _search(
        client, _id=str(world["a"]), _revinclude="Observation:has-member"
    )
    assert _of_type(bundle, "Observation", "include") == {str(world["d"])}
    bundle = await _search(
        client, _id=str(world["a"]), _revinclude="Observation:derived-from"
    )
    assert _of_type(bundle, "Observation", "include") == {str(world["b"])}


async def test_revinclude_is_tenant_scoped(client, other_client):
    from app.auth.dependencies import get_current_user
    from app.main import app
    from tests.conftest import make_test_user
    from tests.integration.observation.conftest import OBSERVATION_PERMS

    def as_user(**kw):
        app.dependency_overrides[get_current_user] = make_test_user(
            permissions=OBSERVATION_PERMS, **kw
        )

    as_user()
    mine = await create_patient(client)
    await create_observation(client, observation_body(mine))
    as_user(sub="u-other", org_id="org-other")
    try:
        # The other org cannot see the patient, so nothing reaches its observations.
        bundle = await _other(
            other_client, "patients", _id=str(mine), _revinclude="Observation:patient"
        )
        assert bundle["total"] == 0 and "entry" not in bundle
        theirs = await create_patient(other_client)
        bundle = await _other(
            other_client, "patients", _id=str(theirs), _revinclude="Observation:patient"
        )
        assert _of_type(bundle, "Observation", "include") == set()
    finally:
        as_user()


# ── combination rules / lenient vs strict ────────────────────────────────────


async def test_params_are_anded(client, world):
    assert await _keys(client, world, category="vital-signs", status="final") == {"a"}
    assert await _keys(client, world, category="vital-signs", status="amended") == set()
    assert await _keys(
        client, world, patient=str(world["p1"]), **{"component-value-quantity": "gt140"}
    ) == {"a"}
    assert await _keys(client, world, code="85354-9", date="ge2023") == {"a"}


async def test_separate_params_can_pair_a_code_and_a_value_of_different_elements(
    client, world
):
    """What a composite exists to prevent: `component-code=8462-4&component-value-quantity=gt140` is
    satisfied by the diastolic code and the systolic value — different components."""
    assert await _keys(
        client,
        world,
        **{"component-code": "8462-4", "component-value-quantity": "gt140"},
    ) == {"a"}
    assert (
        await _keys(client, world, **{"component-code-value-quantity": "8462-4$gt140"})
        == set()
    )


async def test_bad_value_is_400_operation_outcome(client, world):
    resp = await client.get(BASE + "/", params={"_lastUpdated": "banana"})
    assert resp.status_code == 400 and resp.json()["resourceType"] == "OperationOutcome"
    assert await _status(client, **{"patient:text": "x"}) == 400
    assert await _status(client, **{"date:exact": "2020"}) == 400
    assert await _status(client, **{"identifier:below": "x"}) == 400
    assert await _status(client, **{"code:nonsense": "x"}) == 400
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


# ── POST _search / Bundle shape ──────────────────────────────────────────────


async def test_post_search_form_encoded(client, world):
    resp = await client.post(
        BASE + "/_search",
        data={
            "component-code-value-quantity": "8480-6$gt140",
            "patient": str(world["p1"]),
        },
    )
    assert resp.status_code == 200, resp.text
    assert _ids(resp.json()) == {world["a"]}


async def test_bundle_shape(client, world):
    bundle = await _search(client, identifier="OBS-B")
    assert bundle["resourceType"] == "Bundle" and bundle["type"] == "searchset"
    entry = bundle["entry"][0]
    assert entry["fullUrl"].endswith(f"/observations/{world['b']}")
    assert entry["search"]["mode"] == "match"
    assert entry["resource"]["resourceType"] == "Observation"


async def test_empty_result(client, world):
    bundle = await _search(client, identifier="nope")
    assert bundle["total"] == 0 and "entry" not in bundle
