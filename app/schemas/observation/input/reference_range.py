from pydantic import BaseModel, ConfigDict, Field

from .codeable_concept import ObservationCodeableConceptInput


class ObservationReferenceRangeAppliesToInput(ObservationCodeableConceptInput):
    """referenceRange.appliesTo[] — plain {coding[], text} CodeableConcept,
    same shape as ObservationCodeableConceptInput; kept as its own name
    for clarity at the call site."""


class ObservationReferenceRangeInput(BaseModel):
    """Observation.referenceRange (0..*) — reused identically for
    Observation.component.referenceRange too (same shape, different
    parent table at the DB layer — see
    app.models.observation.component.ObservationComponentReferenceRange).
    `low`/`high` (SimpleQuantity) and `age.low`/`age.high` (SimpleQuantity)
    are flattened; `type` (0..1 CodeableConcept) is flattened with `_text`
    on this same model; `appliesTo` is a real 0..* list."""

    model_config = ConfigDict(extra="forbid")

    low_value: float | None = Field(None, description="low (SimpleQuantity) — numeric value.")
    low_unit: str | None = Field(None, description="low — unit.")
    low_system: str | None = Field(None, description="low — unit system.")
    low_code: str | None = Field(None, description="low — coded unit form.")
    high_value: float | None = Field(None, description="high (SimpleQuantity) — numeric value.")
    high_unit: str | None = Field(None, description="high — unit.")
    high_system: str | None = Field(None, description="high — unit system.")
    high_code: str | None = Field(None, description="high — coded unit form.")
    type: ObservationCodeableConceptInput | None = Field(None, description="Range qualifier, e.g. normal, therapeutic.")
    applies_to: list[ObservationReferenceRangeAppliesToInput] | None = Field(None, description="Target population for this range.")
    age_low_value: float | None = Field(None, description="age.low (SimpleQuantity) — numeric value.")
    age_low_unit: str | None = Field(None, description="age.low — unit.")
    age_low_system: str | None = Field(None, description="age.low — unit system.")
    age_low_code: str | None = Field(None, description="age.low — coded unit form.")
    age_high_value: float | None = Field(None, description="age.high (SimpleQuantity) — numeric value.")
    age_high_unit: str | None = Field(None, description="age.high — unit.")
    age_high_system: str | None = Field(None, description="age.high — unit system.")
    age_high_code: str | None = Field(None, description="age.high — coded unit form.")
    text: str | None = Field(None, description="Text-based range, e.g. 'Negative'.")
