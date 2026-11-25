"""FHIR R4 conformance for `to_fhir_observation_definition()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

ObservationDefinition is stored whole in `content` (like the other content-based resources): the
resource lives in ObservationDefinitionModel.content, and to_fhir_observation_definition() only
stamps `id` and `meta` onto it. So what can go wrong on the read side is that stamping (e.g. a
malformed meta extension) or a stored document the server returns that isn't valid R4 - each case
below is a `content` document as the write path would store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.observation_definition import to_fhir_observation_definition
from app.models.observation_definition import ObservationDefinitionModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.observation_definition_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
LOINC = "http://loinc.org"
UCUM = "http://unitsofmeasure.org"
CODE = {"coding": [{"system": LOINC, "code": "718-7"}]}


def _c(content: dict, **overrides) -> ObservationDefinitionModel:
    fields = {
        "observation_definition_id": 400001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return ObservationDefinitionModel(**fields)


def _case(**extra) -> ObservationDefinitionModel:
    return _c({"code": CODE, **extra})


CASES = {
    "minimal": _c({"code": CODE}),
    "updated_by_and_updated_at": _c({"code": CODE}, updated_by="u-other", updated_at=D),
    "identifier_with_type_and_assigner": _case(
        identifier=[
            {
                "use": "official",
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "ACSN",
                        }
                    ]
                },
                "system": "https://fhir-server.dev/fhir/identifier-system/observation-definition-id",
                "value": "OD-1",
                "period": {"start": "2020-01-01"},
                "assigner": {"reference": "Organization/190001"},
            }
        ]
    ),
    "category": _case(
        category=[
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                        "code": "laboratory",
                    }
                ]
            },
            {"text": "x"},
        ]
    ),
    **{
        f"permitted_{t}": _case(permittedDataType=[t])
        for t in (
            "Quantity",
            "CodeableConcept",
            "string",
            "boolean",
            "integer",
            "Range",
            "Ratio",
            "SampledData",
            "time",
            "dateTime",
            "Period",
        )
    },
    "several_permitted_types": _case(permittedDataType=["Quantity", "string"]),
    "multiple_results_method_report_name": _case(
        multipleResultsAllowed=True,
        method={"text": "automated count"},
        preferredReportName="Hemoglobin",
    ),
    "quantitative_details": _case(
        quantitativeDetails={
            "customaryUnit": {"coding": [{"system": UCUM, "code": "g/dL"}]},
            "unit": {"coding": [{"system": UCUM, "code": "g/L"}]},
            "conversionFactor": 10.0,
            "decimalPrecision": 1,
        }
    ),
    **{
        f"interval_{c}": _case(
            qualifiedInterval=[
                {"category": c, "range": {"low": {"value": 1, "unit": "g"}}}
            ]
        )
        for c in ("reference", "critical", "absolute")
    },
    "qualified_interval_every_element": _case(
        qualifiedInterval=[
            {
                "category": "reference",
                "range": {
                    "low": {
                        "value": 12,
                        "unit": "g/dL",
                        "system": UCUM,
                        "code": "g/dL",
                    },
                    "high": {
                        "value": 16,
                        "unit": "g/dL",
                        "system": UCUM,
                        "code": "g/dL",
                    },
                },
                "context": {"text": "adult female"},
                "appliesTo": [{"text": "female"}, {"coding": [{"code": "x"}]}],
                "gender": "female",
                "age": {
                    "low": {"value": 18, "unit": "a"},
                    "high": {"value": 65, "unit": "a"},
                },
                "gestationalAge": {"low": {"value": 0, "unit": "wk"}},
                "condition": "not pregnant",
            }
        ]
    ),
    **{
        f"gender_{g}": _case(qualifiedInterval=[{"gender": g}])
        for g in ("male", "female", "other", "unknown")
    },
    "coded_value_sets": _case(
        validCodedValueSet={"reference": "ValueSet/valid"},
        normalCodedValueSet={"reference": "https://example.org/fhir/ValueSet/normal"},
        abnormalCodedValueSet={"reference": "ValueSet/abnormal", "display": "Abnormal"},
        criticalCodedValueSet={"identifier": {"system": "urn:vs", "value": "crit"}},
    ),
    "extension": _case(
        extension=[
            {
                "url": "https://fhir-server.dev/fhir/StructureDefinition/x",
                "valueString": "y",
            }
        ]
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_observation_definition_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.ObservationDefinition, to_fhir_observation_definition(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {
        "code": CODE,
        "preferredReportName": "Hemoglobin",
        "permittedDataType": ["Quantity"],
    }
    out = to_fhir_observation_definition(_c(content))
    assert out["resourceType"] == "ObservationDefinition"
    assert out["id"] == "400001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# -- Guarding the oracle ---------------------------------------------------------------------
# If google-fhir-r4 ever stops validating - a version bump, a changed API, a
# silently-swallowed error - every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 - `code` or `method` as a one-item list; the
# integration tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("category as object not a list", {"category": {"text": "x"}}),
        ("code as string", {"code": "718-7"}),
        ("permittedDataType with an unknown code", {"permittedDataType": ["banana"]}),
        ("permittedDataType as string", {"permittedDataType": "Quantity"}),
        ("multipleResultsAllowed as string", {"multipleResultsAllowed": "maybe"}),
        ("method as string", {"method": "automated"}),
        ("preferredReportName as number", {"preferredReportName": 5}),
        ("quantitativeDetails as string", {"quantitativeDetails": "x"}),
        (
            "decimalPrecision as string",
            {"quantitativeDetails": {"decimalPrecision": "one"}},
        ),
        (
            "conversionFactor as string",
            {"quantitativeDetails": {"conversionFactor": "ten"}},
        ),
        (
            "qualifiedInterval as object",
            {"qualifiedInterval": {"category": "reference"}},
        ),
        ("interval category unknown", {"qualifiedInterval": [{"category": "banana"}]}),
        ("interval gender unknown", {"qualifiedInterval": [{"gender": "robot"}]}),
        ("interval range as string", {"qualifiedInterval": [{"range": "1-2"}]}),
        (
            "interval appliesTo as object",
            {"qualifiedInterval": [{"appliesTo": {"text": "x"}}]},
        ),
        ("interval condition as number", {"qualifiedInterval": [{"condition": 5}]}),
        ("validCodedValueSet as string", {"validCodedValueSet": "ValueSet/1"}),
        (
            "criticalCodedValueSet as list",
            {"criticalCodedValueSet": [{"reference": "ValueSet/1"}]},
        ),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {
        "resourceType": "ObservationDefinition",
        "id": "400001",
        "code": CODE,
        **broken,
    }
    with pytest.raises(Exception):  # noqa: B017 - the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.ObservationDefinition, validate=True
        )
