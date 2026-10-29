from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput


class ServiceRequestCodeableConceptInput(BaseModel):
    """Shared shape for every plain CodeableConcept field/list-item on
    ServiceRequest (category[], orderDetail[], locationCode[],
    reasonCode[], bodySite[], code, performerType, and the
    asNeededCodeableConcept variant) — all the same {coding[], text}
    shape, reused rather than redeclared per field."""

    model_config = ConfigDict(extra="forbid")
    coding: list[CodingInput] | None = Field(None, description="Coding(s) for this concept.")
    text: str | None = Field(None, description="A human language representation of the concept.")
