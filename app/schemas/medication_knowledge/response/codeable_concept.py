from pydantic import BaseModel, ConfigDict

from app.schemas.datatypes.coding_input import CodingInput


class MedicationKnowledgeCodeableConceptResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: int | None = None
    coding: list[CodingInput] | None = None
    text: str | None = None
