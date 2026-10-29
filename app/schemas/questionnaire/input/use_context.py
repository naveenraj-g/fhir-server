from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput
from app.schemas.enums import QuestionnaireQuantityComparator


class QuestionnaireUseContextInput(BaseModel):
    """Questionnaire.useContext (0..* UsageContext) —
    https://www.hl7.org/fhir/R4/metadatatypes.html#UsageContext

    `code` (1..1 Coding) is flattened directly on this schema (bare
    system/version/code/display/user_selected — not a list, since
    UsageContext.code is a single Coding, not a CodeableConcept).
    `value[x]` (1..1, choice of CodeableConcept|Quantity|Range|Reference)
    gets one field group per variant; the service picks whichever is
    populated. Reference fields are plain `str` (the raw 'Type/id' string,
    same convention as every other Reference input field in this codebase —
    see SlotCreateSchema.schedule) rather than a typed enum.
    """

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
    value_quantity_comparator: QuestionnaireQuantityComparator | None = Field(
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
        description="value[x]: Reference(PlanDefinition|ResearchStudy|InsurancePlan|HealthcareService|Group|Location|Organization), as a FHIR reference string.",
    )
    value_reference_display: str | None = Field(
        None, description="value[x]: Reference — plain text display."
    )
