from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import PlainCodingRow


class _PlainCodeableConceptFields(BaseModel):
    model_config = ConfigDict(extra="allow")
    codings: list[PlainCodingRow] | None = Field(None, description="Coding(s) for this concept.")
    text: str | None = Field(None, description="A human language representation of the concept.")


class PlainServiceRequestCodeableConcept(_PlainCodeableConceptFields):
    """List-item CodeableConcept (category[]/orderDetail[]/locationCode[]/
    reasonCode[]/bodySite[]) — a real child-table row, so it carries its
    own `id`."""

    id: int = Field(..., description="Internal row ID.")


class PlainServiceRequestCode(_PlainCodeableConceptFields):
    """Singular CodeableConcept fields (code/performerType/
    asNeededCodeableConcept) — flattened directly onto the main row, so
    no `id` here."""
