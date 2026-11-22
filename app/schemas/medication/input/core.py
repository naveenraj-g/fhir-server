from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirReferenceInput,
)

# MedicationStatusCodes (the required binding of Medication.status).
StatusCode = Literal["active", "inactive", "entered-in-error"]

_EXAMPLE = {
    "resourceType": "Medication",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/medication-id",
            "value": "MED-1001",
        }
    ],
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
    "form": {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "385057009",
                "display": "Film-coated tablet",
            }
        ]
    },
    "amount": {
        "numerator": {"value": 30, "unit": "tablet"},
        "denominator": {"value": 1, "unit": "package"},
    },
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
    "batch": {"lotNumber": "LOT-2026-1", "expirationDate": "2027-06-30"},
}


class MedicationQuantityInput(FhirInputModel):
    """Quantity - a measured amount with an optional comparator."""

    value: float | int | None = Field(
        None, description="Numerical value (with implicit precision)."
    )
    comparator: Literal["<", "<=", ">=", ">"] | None = Field(
        None, description="How the value should be understood: < | <= | >= | >."
    )
    unit: str | None = Field(None, description="Unit representation.")
    system: str | None = Field(
        None,
        description="System that defines coded unit form (usually http://unitsofmeasure.org).",
    )
    code: str | None = Field(None, description="Coded form of the unit.")


class MedicationRatioInput(FhirInputModel):
    """Ratio - a relationship of two Quantity values."""

    numerator: MedicationQuantityInput | None = Field(
        None, description="Numerator value."
    )
    denominator: MedicationQuantityInput | None = Field(
        None, description="Denominator value."
    )


class MedicationIngredientInput(FhirInputModel):
    """Medication.ingredient - active or inactive ingredient."""

    itemCodeableConcept: FhirCodeableConceptInput | None = Field(
        None,
        description="The actual ingredient (a CodeableConcept). One of the item[x] choices (required by R4); searched by `ingredient-code`.",
    )
    itemReference: FhirReferenceInput | None = Field(
        None,
        description="The actual ingredient - Reference(Substance | Medication). One of the item[x] choices (required by R4); searched by `ingredient`. A relative Medication must exist in the caller's org (422 otherwise); a Substance is stored as sent.",
    )
    isActive: bool | None = Field(None, description="Active ingredient indicator.")
    strength: MedicationRatioInput | None = Field(
        None, description="Quantity of ingredient present."
    )


class MedicationBatchInput(FhirInputModel):
    """Medication.batch - details about packaged medications."""

    lotNumber: str | None = Field(
        None, description="Identifier assigned to batch. Searched by `lot-number`."
    )
    expirationDate: str | None = Field(
        None,
        description="When batch will expire (a FHIR dateTime). Searched by `expiration-date`.",
    )


class _MedicationFields(FhirInputModel):
    """Every writable Medication element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/medication.html). Create and patch accept exactly the same
    fields. R4 requires nothing beyond the types (every Medication element is optional; an
    ingredient needs its `item[x]`), so any well-formed document is valid.

    The validated body is stored whole (MedicationModel.content), so any valid R4 element is
    kept - including ones this model does not declare. Server-managed elements are ignored if
    sent: `id` (assigned from the medication_id sequence) and `meta` (audit/tenant data,
    stamped on at read time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["Medication"] | None = Field(
        None, description="Optional; if supplied it must be 'Medication'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries - validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="Business identifier for this medication."
    )
    code: FhirCodeableConceptInput | None = Field(
        None, description="Codes that identify this medication. Searched by `code`."
    )
    status: StatusCode | None = Field(
        None, description="active | inactive | entered-in-error."
    )
    manufacturer: FhirReferenceInput | None = Field(
        None,
        description="Manufacturer of the item - Reference(Organization). A relative reference must exist in the caller's org (422 otherwise).",
    )
    form: FhirCodeableConceptInput | None = Field(
        None, description="powder | tablets | capsule ... Searched by `form`."
    )
    amount: MedicationRatioInput | None = Field(
        None, description="Amount of drug in package."
    )
    ingredient: list[MedicationIngredientInput] | None = Field(
        None, description="Active or inactive ingredient."
    )
    batch: MedicationBatchInput | None = Field(
        None, description="Details about packaged medications."
    )


class MedicationCreateSchema(_MedicationFields):
    """POST body - a FHIR R4 Medication resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class MedicationPatchSchema(_MedicationFields):
    """PATCH body - a partial FHIR R4 Medication (merge-patch semantics on top-level
    elements). Only supplied elements are written; omitted ones are left untouched. A supplied
    element replaces the stored value wholesale - a list (even `[]`) replaces every existing
    entry, an object such as `batch` replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "inactive",
                "batch": {"lotNumber": "LOT-2026-2", "expirationDate": "2027-12-31"},
            }
        }
    }
