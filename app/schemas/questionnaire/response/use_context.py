from pydantic import BaseModel, Field

from app.schemas.datatypes import AuditFields, FHIRCodeableConcept, FHIRCoding, FHIRReference, PlainCodingRow

from .fhir_quantity import FHIRQuantity, FHIRRange


class FHIRQuestionnaireUseContext(BaseModel):
    """FHIR R4 UsageContext — https://www.hl7.org/fhir/R4/metadatatypes.html#UsageContext.
    `value[x]` rendered as separate camelCase keys — see fhir_item.py's
    module docstring for why."""

    code: FHIRCoding
    valueCodeableConcept: FHIRCodeableConcept | None = None
    valueQuantity: FHIRQuantity | None = None
    valueRange: FHIRRange | None = None
    valueReference: FHIRReference | None = None


class PlainQuestionnaireUseContext(AuditFields):
    id: int = Field(..., description="Internal row ID.")

    code_system: str | None = Field(None, description="UsageContext.code — code system.")
    code_version: str | None = Field(None, description="UsageContext.code — code system version.")
    code_code: str | None = Field(None, description="UsageContext.code — the code itself.")
    code_display: str | None = Field(None, description="UsageContext.code — display text.")
    code_user_selected: bool | None = Field(None, description="UsageContext.code — whether chosen directly by a user.")

    value_codeable_concept_codings: list[PlainCodingRow] | None = Field(
        None, description="value[x]: CodeableConcept — coding(s)."
    )
    value_codeable_concept_text: str | None = Field(None, description="value[x]: CodeableConcept — human language text.")

    value_quantity_value: float | None = Field(None, description="value[x]: Quantity — numeric value.")
    value_quantity_comparator: str | None = Field(None, description="value[x]: Quantity — < | <= | >= | >.")
    value_quantity_unit: str | None = Field(None, description="value[x]: Quantity — unit representation.")
    value_quantity_system: str | None = Field(None, description="value[x]: Quantity — unit system.")
    value_quantity_code: str | None = Field(None, description="value[x]: Quantity — coded unit form.")

    value_range_low_value: float | None = Field(None, description="value[x]: Range — low bound value.")
    value_range_low_unit: str | None = Field(None, description="value[x]: Range — low bound unit.")
    value_range_low_system: str | None = Field(None, description="value[x]: Range — low bound unit system.")
    value_range_low_code: str | None = Field(None, description="value[x]: Range — low bound coded unit.")
    value_range_high_value: float | None = Field(None, description="value[x]: Range — high bound value.")
    value_range_high_unit: str | None = Field(None, description="value[x]: Range — high bound unit.")
    value_range_high_system: str | None = Field(None, description="value[x]: Range — high bound unit system.")
    value_range_high_code: str | None = Field(None, description="value[x]: Range — high bound coded unit.")

    value_reference: str | None = Field(
        None, description="Resolved FHIR reference, e.g. 'Location/230001'."
    )
    value_reference_type: str | None = Field(None, description="Resolved reference target type.")
    value_reference_id: int | None = Field(None, description="Internal ID of the resolved target, if any.")
    value_reference_display: str | None = Field(None, description="value[x]: Reference — plain text display.")
