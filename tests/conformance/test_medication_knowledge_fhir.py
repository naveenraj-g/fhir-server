"""FHIR R4 conformance for `to_fhir_medication_knowledge()`, checked against google-fhir-r4.

See tests/conformance/support.py for why this exists and what it does not cover.

MedicationKnowledge is stored content-based (like Medication, Patient, Encounter and the other
rebuilt resources): the resource lives whole in MedicationKnowledgeModel.content, and
to_fhir_medication_knowledge() only stamps `id` and `meta` onto it. So what can go wrong on the
read side is that stamping (e.g. a malformed meta extension) or a stored document the server
returns that isn't valid R4 - each case below is a `content` document as the write path would
store it, run through the real read mapper.
"""

import datetime as dt

import pytest

from app.fhir.mappers.medication_knowledge import to_fhir_medication_knowledge
from app.models.medication_knowledge import MedicationKnowledgeModel

from .support import assert_valid, fhir_json_text

pb2 = pytest.importorskip(
    "google.fhir.r4.proto.core.resources.medication_knowledge_pb2",
    reason="google-fhir-r4 is a dev-only dependency",
)

D = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
RXNORM = "http://www.nlm.nih.gov/research/umls/rxnorm"
SCT = "http://snomed.info/sct"
ATC = "http://www.whocc.no/atc"
CODE = {"coding": [{"system": RXNORM, "code": "1049502", "display": "Oxycodone"}]}
RATIO = {
    "numerator": {"value": 10, "unit": "mg"},
    "denominator": {"value": 1, "unit": "tablet"},
}


def _mk(content: dict, **overrides) -> MedicationKnowledgeModel:
    fields = {
        "medication_knowledge_id": 600001,
        "tenant_id": "org-test",
        "created_by": "u-test",
        "created_at": D,
        "content": content,
    }
    fields.update(overrides)
    return MedicationKnowledgeModel(**fields)


CASES = {
    "empty": _mk({}),
    "updated_by_and_updated_at": _mk({}, updated_by="u-other", updated_at=D),
    "code": _mk({"code": CODE}),
    "code_text_only": _mk({"code": {"text": "Compounded cream"}}),
    **{
        f"status_{s}": _mk({"status": s})
        for s in ("active", "inactive", "entered-in-error")
    },
    "manufacturer": _mk({"manufacturer": {"reference": "Organization/190001"}}),
    "manufacturer_with_display": _mk(
        {"manufacturer": {"reference": "Organization/190001", "display": "ACME"}}
    ),
    "manufacturer_logical": _mk(
        {"manufacturer": {"identifier": {"system": "urn:mfr", "value": "M-9"}}}
    ),
    "manufacturer_absolute_url": _mk(
        {"manufacturer": {"reference": "https://other.example.org/fhir/Organization/7"}}
    ),
    "dose_form": _mk({"doseForm": {"coding": [{"system": SCT, "code": "385057009"}]}}),
    "amount": _mk({"amount": {"value": 30, "unit": "tablet"}}),
    "synonym": _mk({"synonym": ["Oxycodone ER 10 mg", "OxyContin 10 mg"]}),
    "related": _mk(
        {
            "relatedMedicationKnowledge": [
                {
                    "type": {"text": "similar"},
                    "reference": [
                        {"reference": "MedicationKnowledge/600002"},
                        {"reference": "MedicationKnowledge/600003"},
                    ],
                }
            ]
        }
    ),
    "associated_medication": _mk(
        {"associatedMedication": [{"reference": "Medication/250001"}]}
    ),
    "product_type": _mk(
        {"productType": [{"text": "brand"}, {"coding": [CODE["coding"][0]]}]}
    ),
    "monograph": _mk(
        {
            "monograph": [
                {
                    "type": {"coding": [{"system": SCT, "code": "374273001"}]},
                    "source": {"reference": "DocumentReference/320001"},
                },
                {"source": {"reference": "Media/9"}},
            ]
        }
    ),
    "ingredient_codeable_concept": _mk({"ingredient": [{"itemCodeableConcept": CODE}]}),
    "ingredient_reference_substance": _mk(
        {"ingredient": [{"itemReference": {"reference": "Substance/1"}}]}
    ),
    "ingredient_full": _mk(
        {
            "ingredient": [
                {"itemCodeableConcept": CODE, "isActive": True, "strength": RATIO},
                {
                    "itemReference": {"reference": "Substance/2"},
                    "isActive": False,
                    "strength": RATIO,
                },
            ]
        }
    ),
    "preparation_instruction": _mk({"preparationInstruction": "Swallow **whole**."}),
    "intended_route": _mk(
        {"intendedRoute": [{"coding": [{"system": SCT, "code": "26643006"}]}]}
    ),
    "cost": _mk(
        {
            "cost": [
                {
                    "type": {"text": "wholesale"},
                    "source": "Wholesaler-A",
                    "cost": {"value": 12.5, "currency": "USD"},
                }
            ]
        }
    ),
    "monitoring_program": _mk(
        {"monitoringProgram": [{"type": {"text": "safety"}, "name": "Opioid-Safety"}]}
    ),
    "administration_guidelines": _mk(
        {
            "administrationGuidelines": [
                {
                    "dosage": [
                        {
                            "type": {"text": "adult"},
                            "dosage": [{"text": "1 tablet every 12 hours"}],
                        }
                    ],
                    "indicationCodeableConcept": {"text": "pain"},
                    "patientCharacteristics": [
                        {
                            "characteristicCodeableConcept": {"text": "adult"},
                            "value": ["18+"],
                        },
                        {
                            "characteristicQuantity": {"value": 60, "unit": "kg"},
                            "value": ["60"],
                        },
                    ],
                }
            ]
        }
    ),
    "administration_guideline_indication_reference": _mk(
        {
            "administrationGuidelines": [
                {"indicationReference": {"reference": "ObservationDefinition/400001"}}
            ]
        }
    ),
    "medicine_classification": _mk(
        {
            "medicineClassification": [
                {
                    "type": {"text": "therapeutic"},
                    "classification": [
                        {"coding": [{"system": ATC, "code": "N02AA05"}]},
                        {"text": "Opioid"},
                    ],
                }
            ]
        }
    ),
    "packaging": _mk(
        {"packaging": {"type": {"text": "blister"}, "quantity": {"value": 30}}}
    ),
    "drug_characteristic_string": _mk(
        {"drugCharacteristic": [{"type": {"text": "imprint"}, "valueString": "OC 10"}]}
    ),
    "drug_characteristic_concept": _mk(
        {"drugCharacteristic": [{"valueCodeableConcept": {"text": "white"}}]}
    ),
    "drug_characteristic_quantity": _mk(
        {"drugCharacteristic": [{"valueQuantity": {"value": 8, "unit": "mm"}}]}
    ),
    "drug_characteristic_base64": _mk(
        {"drugCharacteristic": [{"valueBase64Binary": "aGVsbG8="}]}
    ),
    "contraindication": _mk(
        {"contraindication": [{"reference": "DetectedIssue/540001"}]}
    ),
    "regulatory": _mk(
        {
            "regulatory": [
                {
                    "regulatoryAuthority": {"reference": "Organization/190001"},
                    "substitution": [{"type": {"text": "generic"}, "allowed": True}],
                    "schedule": [{"schedule": {"text": "CII"}}],
                    "maxDispense": {
                        "quantity": {"value": 60},
                        "period": {"value": 30, "unit": "d"},
                    },
                }
            ]
        }
    ),
    "kinetics": _mk(
        {
            "kinetics": [
                {
                    "areaUnderCurve": [{"value": 100, "unit": "mg.h/L"}],
                    "lethalDose50": [{"value": 5, "unit": "mg/kg"}],
                    "halfLifePeriod": {"value": 4, "unit": "h"},
                }
            ]
        }
    ),
    "extension": _mk(
        {
            "extension": [
                {
                    "url": "https://fhir-server.dev/fhir/StructureDefinition/x",
                    "valueString": "y",
                }
            ]
        }
    ),
    "full": _mk(
        {
            "code": CODE,
            "status": "active",
            "manufacturer": {"reference": "Organization/190001"},
            "doseForm": {"text": "tablet"},
            "amount": {"value": 30, "unit": "tablet"},
            "synonym": ["Syn"],
            "ingredient": [
                {"itemCodeableConcept": CODE, "isActive": True, "strength": RATIO}
            ],
            "medicineClassification": [
                {"type": {"text": "therapeutic"}, "classification": [{"text": "x"}]}
            ],
            "cost": [
                {
                    "type": {"text": "w"},
                    "source": "S",
                    "cost": {"value": 1, "currency": "USD"},
                }
            ],
            "monitoringProgram": [{"name": "P"}],
        }
    ),
}


@pytest.mark.parametrize("case", sorted(CASES), ids=sorted(CASES))
def test_medication_knowledge_mapper_emits_valid_fhir_r4(case):
    assert_valid(pb2.MedicationKnowledge, to_fhir_medication_knowledge(CASES[case]))


def test_mapper_serves_content_unchanged():
    content = {"status": "active", "synonym": ["A", "B"]}
    out = to_fhir_medication_knowledge(_mk(content))
    assert out["resourceType"] == "MedicationKnowledge"
    assert out["id"] == "600001"
    assert {
        k: v for k, v in out.items() if k not in ("resourceType", "id", "meta")
    } == content


# -- Guarding the oracle ---------------------------------------------------------------------
# If google-fhir-r4 ever stops validating - a version bump, a changed API, a
# silently-swallowed error - every test above would keep passing while checking
# nothing. These deliberately-broken payloads prove the check still has teeth.
# (Not covered by the oracle, as noted in CLAUDE.md: a single-element array
# where the spec says 0..1 - `code`, `manufacturer` or `packaging` as a one-item list; the
# integration tests cover what they can.)


@pytest.mark.parametrize(
    "label,broken",
    [
        ("misspelled element", {"typo": "x"}),
        ("status with an unknown code", {"status": "robot"}),
        ("status as number", {"status": 1}),
        ("code as string not a CodeableConcept", {"code": "x"}),
        ("doseForm as string not a CodeableConcept", {"doseForm": "x"}),
        ("manufacturer as string not a Reference", {"manufacturer": "Organization/1"}),
        ("amount as string", {"amount": "30"}),
        ("synonym as string not a list", {"synonym": "x"}),
        ("synonym entry as number", {"synonym": [5]}),
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
        ("monograph as object not a list", {"monograph": {"type": {"text": "x"}}}),
        (
            "monograph source as string",
            {"monograph": [{"source": "DocumentReference/1"}]},
        ),
        ("cost source as number", {"cost": [{"source": 5}]}),
        ("monitoringProgram name as number", {"monitoringProgram": [{"name": 5}]}),
        (
            "medicineClassification classification as string",
            {"medicineClassification": [{"classification": "x"}]},
        ),
        ("preparationInstruction as number", {"preparationInstruction": 5}),
        (
            "regulatory substitution allowed as string",
            {"regulatory": [{"substitution": [{"allowed": "yes"}]}]},
        ),
        ("kinetics halfLifePeriod as string", {"kinetics": [{"halfLifePeriod": "4h"}]}),
    ],
)
def test_validator_rejects_invalid_fhir(label, broken):
    from google.fhir.r4 import json_format

    payload = {"resourceType": "MedicationKnowledge", "id": "600001", **broken}
    with pytest.raises(Exception):  # noqa: B017 - the library raises several types
        json_format.json_fhir_string_to_proto(
            fhir_json_text(payload), pb2.MedicationKnowledge, validate=True
        )
