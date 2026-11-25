"""FHIR R4 conformance for `to_fhir_medication()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

Medication is stored Medplum-style (like Patient, Appointment, Encounter, Condition, Procedure,
Specimen, ServiceRequest and the other content-based resources): the resource lives whole in
MedicationModel.content, and to_fhir_medication() only stamps `id` and `meta` onto it. So what
can go wrong on the read side is that stamping (e.g. a malformed meta extension) or a stored
document the server returns that isn't valid R4 - each case below is a `content` document as
the write path would store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.medication import to_fhir_medication
from app.models.medication import MedicationModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.medication_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
RXNORM = "http://www.nlm.nih.gov/research/umls/rxnorm"
SCT = "http://snomed.info/sct"
CODE = {"coding": [{"system": RXNORM, "code": "1049502", "display": "Oxycodone"}]}


def _ratio(num=10, num_unit="mg", den=1, den_unit="tablet"):
    return {
        "numerator": {"value": num, "unit": num_unit},
        "denominator": {"value": den, "unit": den_unit},
    }


def _med(content: dict, **overrides) -> MedicationModel:
    fields = {
        "medication_id": 250001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return MedicationModel(**fields)


CASES = {
    "empty": _med({}),
    "updated_by_and_updated_at": _med({}, updated_by="u-other", updated_at=D),
    "identifier_with_type_and_assigner": _med(
        {
            "identifier": [
                {
                    "use": "official",
                    "type": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                                "code": "FILL",
                            }
                        ]
                    },
                    "system": "https://fhir-server.dev/fhir/identifier-system/medication-id",
                    "value": "MED-1",
                    "period": {"start": "2020-01-01"},
                    "assigner": {"reference": "Organization/190001"},
                }
            ]
        }
    ),
    "code": _med({"code": CODE}),
    "code_text_only": _med({"code": {"text": "Compounded cream"}}),
    **{
        f"status_{s}": _med({"status": s})
        for s in ("active", "inactive", "entered-in-error")
    },
    "manufacturer": _med({"manufacturer": {"reference": "Organization/190001"}}),
    "manufacturer_with_display": _med(
        {"manufacturer": {"reference": "Organization/190001", "display": "ACME"}}
    ),
    "manufacturer_logical": _med(
        {"manufacturer": {"identifier": {"system": "urn:mfr", "value": "M-9"}}}
    ),
    "manufacturer_absolute_url": _med(
        {"manufacturer": {"reference": "https://other.example.org/fhir/Organization/7"}}
    ),
    "form": _med({"form": {"coding": [{"system": SCT, "code": "385057009"}]}}),
    "amount": _med({"amount": _ratio(30, "tablet", 1, "package")}),
    "ingredient_codeable_concept": _med(
        {"ingredient": [{"itemCodeableConcept": CODE}]}
    ),
    "ingredient_reference_substance": _med(
        {"ingredient": [{"itemReference": {"reference": "Substance/1"}}]}
    ),
    "ingredient_reference_medication": _med(
        {"ingredient": [{"itemReference": {"reference": "Medication/250000"}}]}
    ),
    "ingredient_full": _med(
        {
            "ingredient": [
                {"itemCodeableConcept": CODE, "isActive": True, "strength": _ratio()},
                {
                    "itemReference": {"reference": "Substance/2"},
                    "isActive": False,
                    "strength": _ratio(5, "mg", 1, "mL"),
                },
            ]
        }
    ),
    "batch_lot_number": _med({"batch": {"lotNumber": "LOT-1"}}),
    "batch_expiration_date": _med({"batch": {"expirationDate": "2027-06-30"}}),
    "batch_expiration_date_time": _med(
        {"batch": {"expirationDate": "2027-06-30T12:00:00Z"}}
    ),
    "batch_expiration_date_partial": _med({"batch": {"expirationDate": "2027-06"}}),
    "extension": _med(
        {
            "extension": [
                {
                    "url": "https://fhir-server.dev/fhir/StructureDefinition/x",
                    "valueString": "y",
                }
            ]
        }
    ),
    "full": _med(
        {
            "identifier": [{"system": "urn:med", "value": "MED-1"}],
            "code": CODE,
            "status": "active",
            "manufacturer": {"reference": "Organization/190001"},
            "form": {"text": "tablet"},
            "amount": _ratio(30, "tablet", 1, "package"),
            "ingredient": [
                {"itemCodeableConcept": CODE, "isActive": True, "strength": _ratio()}
            ],
            "batch": {"lotNumber": "LOT-1", "expirationDate": "2027-06-30"},
        }
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_medication_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.Medication, to_fhir_medication(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {"status": "active", "batch": {"lotNumber": "LOT-1"}}
    out = to_fhir_medication(_med(content))
    assert out["resourceType"] == "Medication"
    assert out["id"] == "250001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# -- Guarding the oracle ---------------------------------------------------------------------
# If google-fhir-r4 ever stops validating - a version bump, a changed API, a
# silently-swallowed error - every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 - `code`, `manufacturer` or `batch` as a one-item list; the
# integration tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("status with an unknown code", {"status": "robot"}),
        ("status as number", {"status": 1}),
        ("code as string not a CodeableConcept", {"code": "x"}),
        ("form as string not a CodeableConcept", {"form": "x"}),
        ("manufacturer as string not a Reference", {"manufacturer": "Organization/1"}),
        ("identifier as object not a list", {"identifier": {"value": "x"}}),
        ("amount as string", {"amount": "30"}),
        ("amount numerator as string", {"amount": {"numerator": "30"}}),
        ("ingredient as object not a list", {"ingredient": {"isActive": True}}),
        ("ingredient isActive as string", {"ingredient": [{"isActive": "yes"}]}),
        (
            "ingredient itemCodeableConcept as string",
            {"ingredient": [{"itemCodeableConcept": "x"}]},
        ),
        (
            "ingredient itemReference as string",
            {"ingredient": [{"itemReference": "Substance/1"}]},
        ),
        ("ingredient strength as string", {"ingredient": [{"strength": "10mg"}]}),
        ("batch as string", {"batch": "LOT"}),
        ("batch lotNumber as number", {"batch": {"lotNumber": 5}}),
        ("batch expirationDate not a dateTime", {"batch": {"expirationDate": "soon"}}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "Medication", "id": "250001", **broken}
    with pytest.raises(Exception):  # noqa: B017 - the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.Medication, validate=True
        )
