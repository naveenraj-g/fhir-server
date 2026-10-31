from pydantic import BaseModel, ConfigDict, Field

from app.models.plan_definition.enums import PlanDefinitionQuantityComparator
from app.schemas.datatypes import CodingInput


class PlanDefinitionUseContextInput(BaseModel):
    """PlanDefinition.useContext (0..* UsageContext) input schema."""

    model_config = ConfigDict(extra="forbid")

    code_system: str | None = Field(None, description="UsageContext.code — code system.")
    code_version: str | None = Field(None, description="UsageContext.code — code system version.")
    code_code: str | None = Field(None, description="UsageContext.code — the code itself.")
    code_display: str | None = Field(None, description="UsageContext.code — display text.")
    code_user_selected: bool | None = Field(
        None, description="UsageContext.code — whether chosen directly by a user."
    )

    value_codeable_concept_coding: list[CodingInput] | None = Field(
        None, description="value[x]: CodeableConcept — coding(s)."
    )
    value_codeable_concept_text: str | None = Field(
        None, description="value[x]: CodeableConcept — human language text."
    )

    value_quantity_value: float | None = Field(None, description="value[x]: Quantity — numeric value.")
    value_quantity_comparator: PlanDefinitionQuantityComparator | None = Field(
        None, description="value[x]: Quantity — < | <= | >= | >."
    )
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
        None,
        description="value[x]: Reference string, e.g. 'PlanDefinition/123'.",
    )
    value_reference_display: str | None = Field(
        None, description="value[x]: Reference — plain text display."
    )
