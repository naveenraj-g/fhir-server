"""Shared helpers and payloads for medication_knowledge integration tests.

Request bodies are genuine FHIR R4 MedicationKnowledge JSON (camelCase, nested datatypes), and
every response is FHIR R4 too."""

from tests.integration.practitioner_role.support import create_organization

BASE = "/api/fhir/v1/medication-knowledge"
API = "/api/fhir/v1"

RXNORM = "http://www.nlm.nih.gov/research/umls/rxnorm"
SCT = "http://snomed.info/sct"
ATC = "http://www.whocc.no/atc"
CLASS_TYPES = "http://terminology.hl7.org/CodeSystem/medicationknowledge-classification"


def concept(system: str, code: str, display: str | None = None) -> dict:
    return {
        "coding": [
            {
                "system": system,
                "code": code,
                **({"display": display} if display else {}),
            }
        ]
    }


def medication_knowledge_body(**extra) -> dict:
    """A valid minimal MedicationKnowledge (every R4 element is optional)."""
    return dict(extra)


def full_body(
    organization_id: int,
    medication_id: int,
    document_id: int,
    related_id: int | None = None,
) -> dict:
    """Every R4 element, including the ones no search parameter reads (they must round-trip)."""
    return medication_knowledge_body(
        resourceType="MedicationKnowledge",
        code=concept(RXNORM, "1049502", "Oxycodone 10 MG ER tablet"),
        status="active",
        manufacturer={"reference": f"Organization/{organization_id}"},
        doseForm=concept(SCT, "385057009", "Film-coated tablet"),
        amount={"value": 30, "unit": "tablet"},
        synonym=["Oxycodone ER 10 mg", "OxyContin 10 mg"],
        relatedMedicationKnowledge=(
            [
                {
                    "type": {"text": "similar"},
                    "reference": [{"reference": f"MedicationKnowledge/{related_id}"}],
                }
            ]
            if related_id
            else []
        ),
        associatedMedication=[{"reference": f"Medication/{medication_id}"}],
        productType=[{"text": "brand"}],
        monograph=[
            {
                "type": concept(SCT, "374273001", "Drug monograph"),
                "source": {"reference": f"DocumentReference/{document_id}"},
            },
            {"source": {"reference": "Media/1"}},
        ],
        ingredient=[
            {
                "itemCodeableConcept": concept(RXNORM, "7804", "Oxycodone"),
                "isActive": True,
                "strength": {
                    "numerator": {"value": 10, "unit": "mg"},
                    "denominator": {"value": 1, "unit": "tablet"},
                },
            },
            {"itemReference": {"reference": "Substance/77"}, "isActive": False},
        ],
        preparationInstruction="Swallow whole.",
        intendedRoute=[concept(SCT, "26643006", "Oral route")],
        cost=[
            {
                "type": {"text": "wholesale"},
                "source": "Wholesaler-A",
                "cost": {"value": 12.5, "currency": "USD"},
            }
        ],
        monitoringProgram=[
            {"type": {"text": "safety"}, "name": "Opioid-Safety"},
        ],
        administrationGuidelines=[
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
                    }
                ],
            }
        ],
        medicineClassification=[
            {
                "type": concept(CLASS_TYPES, "therapeutic"),
                "classification": [concept(ATC, "N02AA05", "Oxycodone")],
            }
        ],
        packaging={"type": {"text": "blister"}, "quantity": {"value": 30}},
        drugCharacteristic=[
            {"type": {"text": "imprint"}, "valueString": "OC 10"},
        ],
        regulatory=[
            {
                "regulatoryAuthority": {"reference": f"Organization/{organization_id}"},
                "substitution": [{"type": {"text": "generic"}, "allowed": True}],
                "schedule": [{"schedule": {"text": "CII"}}],
                "maxDispense": {
                    "quantity": {"value": 60},
                    "period": {"value": 30, "unit": "d"},
                },
            }
        ],
        kinetics=[
            {
                "areaUnderCurve": [{"value": 100, "unit": "mg.h/L"}],
                "lethalDose50": [{"value": 5, "unit": "mg/kg"}],
                "halfLifePeriod": {"value": 4, "unit": "h"},
            }
        ],
    )


async def create_medication_knowledge(client, body: dict) -> int:
    """Create a medication knowledge entry and return its public id (int)."""
    resp = await client.post(BASE + "/", json=body)
    assert resp.status_code == 201, resp.text
    return int(resp.json()["id"])


# Helpers for the resources a MedicationKnowledge can point at.
from tests.integration.detected_issue.support import (
    create_issue,
    issue_body,
)
from tests.integration.document_reference.support import (
    create_document,
    document_body,
)
from tests.integration.medication.support import (
    create_medication,
    medication_body,
)
