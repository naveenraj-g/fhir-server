from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import PlainCodingRow


class _PlainCodeableConceptFields(BaseModel):
    model_config = ConfigDict(extra="allow")
    codings: list[PlainCodingRow] | None = Field(None, description="Coding(s) for this concept.")
    text: str | None = Field(None, description="A human language representation of the concept.")


class PlainObservationCodeableConcept(_PlainCodeableConceptFields):
    """List-item CodeableConcept (category[]/interpretation[]/
    referenceRange.appliesTo[]) — a real child-table row, so it carries
    its own `id`."""

    id: int = Field(..., description="Internal row ID.")


class PlainObservationCode(_PlainCodeableConceptFields):
    """Singular CodeableConcept fields (code/valueCodeableConcept/
    dataAbsentReason/bodySite/method/referenceRange.type) — flattened
    directly onto the owning row, so no `id` here."""
