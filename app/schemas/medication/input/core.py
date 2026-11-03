from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import IdentifierUse, MedicationStatus
from app.schemas.medication.input.batch import MedicationBatchInput
from app.schemas.medication.input.codeable_concept import (
    MedicationCodeableConceptInput,
)
from app.schemas.medication.input.identifier import (
    MedicationIdentifierInput,
)
from app.schemas.medication.input.ingredient import (
    MedicationIngredientInput,
)
from app.schemas.medication.input.quantity import (
    MedicationRatioInput,
)

_CREATE_EXAMPLE: dict[str, Any] = {
    "status": "active",
    "code": {
        "text": "Amoxicillin 500mg capsule",
        "coding": [
            {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "308182",
                "display": "Amoxicillin 500 MG Oral Capsule",
            }
        ],
    },
    "form": {
        "text": "Oral Capsule",
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "385055001",
                "display": "Oral Capsule",
            }
        ],
    },
    "amount": {
        "numerator": {
            "value": 500.0,
            "unit": "mg",
            "system": "http://unitsofmeasure.org",
            "code": "mg",
        },
        "denominator": {
            "value": 1.0,
            "unit": "TAB",
            "system": "http://terminology.hl7.org/CodeSystem/v3-orderableDrugForm",
            "code": "TAB",
        },
    },
}


class MedicationCreateSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": _CREATE_EXAMPLE},
    )

    identifier: list[MedicationIdentifierInput] | None = Field(
        None, description="Business identifier for this medication."
    )
    code: MedicationCodeableConceptInput | None = Field(
        None, description="Codes that identify this medication."
    )
    status: MedicationStatus | None = Field(
        None, description="active | inactive | entered-in-error."
    )

    # manufacturer Reference(Organization) with identifier fallback (15 columns)
    manufacturer: str | None = Field(
        None,
        description="Manufacturer of the item. Reference(Organization), e.g. 'Organization/190001'.",
    )
    manufacturer_display: str | None = Field(
        None, description="Display text for manufacturer reference."
    )
    manufacturer_identifier_use: IdentifierUse | None = Field(
        None, description="Fallback identifier — purpose."
    )
    manufacturer_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — type system."
    )
    manufacturer_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — type version."
    )
    manufacturer_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — type code."
    )
    manufacturer_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — type display."
    )
    manufacturer_identifier_type_user_selected: bool | None = Field(
        None, description="Fallback identifier — type user selected."
    )
    manufacturer_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — type text."
    )
    manufacturer_identifier_system: str | None = Field(
        None, description="Fallback identifier — system."
    )
    manufacturer_identifier_value: str | None = Field(
        None, description="Fallback identifier — value."
    )
    manufacturer_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — period start."
    )
    manufacturer_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — period end."
    )

    form: MedicationCodeableConceptInput | None = Field(
        None, description="powder | tablets | capsule +"
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
    extension: list[dict] | None = Field(
        None, description="Additional content defined by implementations."
    )


class MedicationPatchSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    identifier: list[MedicationIdentifierInput] | None = Field(None, description="Business identifier for this medication.")
    code: MedicationCodeableConceptInput | None = Field(None, description="Codes that identify this medication.")
    status: MedicationStatus | None = Field(None, description="active | inactive | entered-in-error.")

    manufacturer: str | None = Field(None, description="Manufacturer of the item. Reference(Organization).")
    manufacturer_display: str | None = Field(None, description="Display text for manufacturer reference.")
    manufacturer_identifier_use: IdentifierUse | None = Field(None, description="Fallback identifier — purpose.")
    manufacturer_identifier_type_system: str | None = Field(None, description="Fallback identifier — type system.")
    manufacturer_identifier_type_version: str | None = Field(None, description="Fallback identifier — type version.")
    manufacturer_identifier_type_code: str | None = Field(None, description="Fallback identifier — type code.")
    manufacturer_identifier_type_display: str | None = Field(None, description="Fallback identifier — type display.")
    manufacturer_identifier_type_user_selected: bool | None = Field(None, description="Fallback identifier — type user selected.")
    manufacturer_identifier_type_text: str | None = Field(None, description="Fallback identifier — type text.")
    manufacturer_identifier_system: str | None = Field(None, description="Fallback identifier — system.")
    manufacturer_identifier_value: str | None = Field(None, description="Fallback identifier — value.")
    manufacturer_identifier_period_start: datetime | None = Field(None, description="Fallback identifier — period start.")
    manufacturer_identifier_period_end: datetime | None = Field(None, description="Fallback identifier — period end.")

    form: MedicationCodeableConceptInput | None = Field(None, description="powder | tablets | capsule +")
    amount: MedicationRatioInput | None = Field(None, description="Amount of drug in package.")
    ingredient: list[MedicationIngredientInput] | None = Field(None, description="Active or inactive ingredient.")
    batch: MedicationBatchInput | None = Field(None, description="Details about packaged medications.")
    extension: list[dict] | None = Field(None, description="Additional content defined by implementations.")
