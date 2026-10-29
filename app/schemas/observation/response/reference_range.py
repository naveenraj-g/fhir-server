from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import PlainCodingRow


class PlainObservationReferenceRangeAppliesTo(BaseModel):
    """One entry of referenceRange.appliesTo (0..* — a real child-table row)."""

    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Internal row ID.")
    codings: list[PlainCodingRow] | None = Field(None, description="Coding(s) for this concept.")
    text: str | None = Field(None, description="A human language representation of the concept.")


class PlainObservationReferenceRange(BaseModel):
    """Observation.referenceRange (0..* — a real child-table row). Reused
    identically for Observation.component.referenceRange — same shape,
    different parent table at the DB layer."""

    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Internal row ID.")
    low_value: float | None = Field(None, description="low (SimpleQuantity) — numeric value.")
    low_unit: str | None = Field(None, description="low — unit.")
    low_system: str | None = Field(None, description="low — unit system.")
    low_code: str | None = Field(None, description="low — coded unit form.")
    high_value: float | None = Field(None, description="high (SimpleQuantity) — numeric value.")
    high_unit: str | None = Field(None, description="high — unit.")
    high_system: str | None = Field(None, description="high — unit system.")
    high_code: str | None = Field(None, description="high — coded unit form.")
    type_codings: list[PlainCodingRow] | None = Field(None, description="Coding(s) for the range qualifier.")
    type_text: str | None = Field(None, description="Range qualifier, e.g. normal, therapeutic.")
    applies_to: list[PlainObservationReferenceRangeAppliesTo] | None = Field(None, description="Target population for this range.")
    age_low_value: float | None = Field(None, description="age.low (SimpleQuantity) — numeric value.")
    age_low_unit: str | None = Field(None, description="age.low — unit.")
    age_low_system: str | None = Field(None, description="age.low — unit system.")
    age_low_code: str | None = Field(None, description="age.low — coded unit form.")
    age_high_value: float | None = Field(None, description="age.high (SimpleQuantity) — numeric value.")
    age_high_unit: str | None = Field(None, description="age.high — unit.")
    age_high_system: str | None = Field(None, description="age.high — unit system.")
    age_high_code: str | None = Field(None, description="age.high — coded unit form.")
    text: str | None = Field(None, description="Text-based range, e.g. 'Negative'.")
