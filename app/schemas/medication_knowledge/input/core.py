from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirInputModel,
    FhirReferenceInput,
)

# MedicationKnowledge Status Codes (the required binding of MedicationKnowledge.status).
StatusCode = Literal["active", "inactive", "entered-in-error"]

_EXAMPLE = {
    "resourceType": "MedicationKnowledge",
    "code": {
        "coding": [
            {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "1049502",
                "display": "12 HR Oxycodone Hydrochloride 10 MG Extended Release Oral Tablet",
            }
        ]
    },
    "status": "active",
    "manufacturer": {"reference": "Organization/190001"},
    "doseForm": {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "385057009",
                "display": "Film-coated tablet",
            }
        ]
    },
    "amount": {"value": 30, "unit": "tablet"},
    "synonym": ["Oxycodone ER 10 mg"],
    "ingredient": [
        {
            "itemCodeableConcept": {
                "coding": [
                    {
                        "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                        "code": "7804",
                        "display": "Oxycodone",
                    }
                ]
            },
            "isActive": True,
            "strength": {
                "numerator": {"value": 10, "unit": "mg"},
                "denominator": {"value": 1, "unit": "tablet"},
            },
        }
    ],
    "medicineClassification": [
        {
            "type": {"text": "therapeutic"},
            "classification": [
                {"coding": [{"system": "http://www.whocc.no/atc", "code": "N02AA05"}]}
            ],
        }
    ],
    "monitoringProgram": [{"name": "Opioid-Safety"}],
    "cost": [
        {
            "type": {"text": "wholesale"},
            "source": "Wholesaler-A",
            "cost": {"value": 12.5, "currency": "USD"},
        }
    ],
}


class MedicationKnowledgeRelatedInput(FhirInputModel):
    """MedicationKnowledge.relatedMedicationKnowledge - associated or related knowledge."""

    type: FhirCodeableConceptInput | None = Field(
        None, description="Category of medicationKnowledge (required by R4)."
    )
    reference: list[FhirReferenceInput] | None = Field(
        None,
        description="Associated documentation about the associated medication knowledge - Reference(MedicationKnowledge), 1..* in R4. A relative reference must exist in the caller's org (422 otherwise).",
    )


class MedicationKnowledgeMonographInput(FhirInputModel):
    """MedicationKnowledge.monograph - associated documentation about the medication."""

    type: FhirCodeableConceptInput | None = Field(
        None,
        description="The category of medication document. Searched by `monograph-type`.",
    )
    source: FhirReferenceInput | None = Field(
        None,
        description="Associated documentation about the medication - Reference(DocumentReference | Media). Searched by `monograph`. A relative DocumentReference must exist in the caller's org (422 otherwise).",
    )


class MedicationKnowledgeIngredientInput(FhirInputModel):
    """MedicationKnowledge.ingredient - active or inactive ingredient."""

    itemCodeableConcept: FhirCodeableConceptInput | None = Field(
        None,
        description="Medication(s) or substance(s) contained in the medication (a CodeableConcept). One of the item[x] choices (required by R4); searched by `ingredient-code`.",
    )
    itemReference: FhirReferenceInput | None = Field(
        None,
        description="Medication(s) or substance(s) contained in the medication - Reference(Substance). One of the item[x] choices (required by R4); searched by `ingredient`.",
    )
    isActive: bool | None = Field(None, description="Active ingredient indicator.")
    strength: dict | None = Field(
        None, description="Quantity of ingredient present (a Ratio)."
    )


class MedicationKnowledgeCostInput(FhirInputModel):
    """MedicationKnowledge.cost - the pricing of the drug."""

    type: FhirCodeableConceptInput | None = Field(
        None, description="The category of the cost information (required by R4)."
    )
    source: str | None = Field(
        None,
        description="The source or owner for the price information. Searched by `source-cost`.",
    )
    cost: dict | None = Field(
        None, description="The price of the medication (a Money; required by R4)."
    )


class MedicationKnowledgeMonitoringProgramInput(FhirInputModel):
    """MedicationKnowledge.monitoringProgram - program under which a medication is reviewed."""

    type: FhirCodeableConceptInput | None = Field(
        None,
        description="Type of program under which the medication is monitored. Searched by `monitoring-program-type`.",
    )
    name: str | None = Field(
        None,
        description="Name of the reviewing program. Searched by `monitoring-program-name`.",
    )


class MedicationKnowledgeMedicineClassificationInput(FhirInputModel):
    """MedicationKnowledge.medicineClassification - categorization of the medication."""

    type: FhirCodeableConceptInput | None = Field(
        None,
        description="The type of category for the medication (for example, therapeutic classification, therapeutic sub-classification; required by R4). Searched by `classification-type`.",
    )
    classification: list[FhirCodeableConceptInput] | None = Field(
        None,
        description="Specific category assigned to the medication. Searched by `classification`.",
    )


class _MedicationKnowledgeFields(FhirInputModel):
    """Every writable MedicationKnowledge element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/medicationknowledge.html). Create and patch accept exactly the
    same fields. R4 requires nothing at the top level (every MedicationKnowledge element is
    optional; the nested minimums are only enforced by the `java_validator` backend), so any
    well-formed document is valid.

    The validated body is stored whole (MedicationKnowledgeModel.content), so any valid R4
    element is kept - including ones this model does not declare (`packaging`,
    `drugCharacteristic`, `regulatory`, `kinetics`, `administrationGuidelines`, ...).
    Server-managed elements are ignored if sent: `id` (assigned from the
    medication_knowledge_id sequence) and `meta` (audit/tenant data, stamped on at read time).
    org_id and created_by/updated_by come from the verified JWT (actor.org_id / actor.sub),
    never the body. There is no user_id."""

    resourceType: Literal["MedicationKnowledge"] | None = Field(
        None, description="Optional; if supplied it must be 'MedicationKnowledge'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries - validated by the profile pipeline, not here.",
    )
    code: FhirCodeableConceptInput | None = Field(
        None, description="Code that identifies this medication. Searched by `code`."
    )
    status: StatusCode | None = Field(
        None, description="active | inactive | entered-in-error. Searched by `status`."
    )
    manufacturer: FhirReferenceInput | None = Field(
        None,
        description="Manufacturer of the item - Reference(Organization). A relative reference must exist in the caller's org (422 otherwise).",
    )
    doseForm: FhirCodeableConceptInput | None = Field(
        None, description="powder | tablets | capsule ... Searched by `doseform`."
    )
    amount: dict | None = Field(
        None, description="Amount of drug in package (a SimpleQuantity)."
    )
    synonym: list[str] | None = Field(
        None, description="Additional names for a medication."
    )
    relatedMedicationKnowledge: list[MedicationKnowledgeRelatedInput] | None = Field(
        None, description="Associated or related medication information."
    )
    associatedMedication: list[FhirReferenceInput] | None = Field(
        None,
        description="A medication resource that is associated with this medication - Reference(Medication). A relative reference must exist in the caller's org (422 otherwise).",
    )
    productType: list[FhirCodeableConceptInput] | None = Field(
        None, description="Category of the medication or product."
    )
    monograph: list[MedicationKnowledgeMonographInput] | None = Field(
        None, description="Associated documentation about the medication."
    )
    ingredient: list[MedicationKnowledgeIngredientInput] | None = Field(
        None, description="Active or inactive ingredient."
    )
    preparationInstruction: str | None = Field(
        None, description="The instructions for preparing the medication (markdown)."
    )
    intendedRoute: list[FhirCodeableConceptInput] | None = Field(
        None, description="The intended or approved route of administration."
    )
    cost: list[MedicationKnowledgeCostInput] | None = Field(
        None, description="The pricing of the drug."
    )
    monitoringProgram: list[MedicationKnowledgeMonitoringProgramInput] | None = Field(
        None, description="Program under which a medication is reviewed."
    )
    administrationGuidelines: list[dict] | None = Field(
        None,
        description="Guidelines for the administration of the medication (dosage, indication, patientCharacteristics).",
    )
    medicineClassification: (
        list[MedicationKnowledgeMedicineClassificationInput] | None
    ) = Field(
        None,
        description="Categorization of the medication within a formulary or classification system.",
    )
    packaging: dict | None = Field(
        None, description="Details about packaged medications (type, quantity)."
    )
    drugCharacteristic: list[dict] | None = Field(
        None, description="Specifies descriptive properties of the medicine."
    )
    contraindication: list[FhirReferenceInput] | None = Field(
        None,
        description="Potential clinical issue with or between medication(s) - Reference(DetectedIssue). A relative reference must exist in the caller's org (422 otherwise).",
    )
    regulatory: list[dict] | None = Field(
        None, description="Regulatory information about a medication."
    )
    kinetics: list[dict] | None = Field(
        None,
        description="The time course of drug absorption, distribution, metabolism and excretion.",
    )


class MedicationKnowledgeCreateSchema(_MedicationKnowledgeFields):
    """POST body - a FHIR R4 MedicationKnowledge resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class MedicationKnowledgePatchSchema(_MedicationKnowledgeFields):
    """PATCH body - a partial FHIR R4 MedicationKnowledge (merge-patch semantics on top-level
    elements). Only supplied elements are written; omitted ones are left untouched. A supplied
    element replaces the stored value wholesale - a list (even `[]`) replaces every existing
    entry, an object such as `packaging` replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "inactive",
                "synonym": ["Oxycodone ER 10 mg", "OxyContin 10 mg"],
            }
        }
    }
