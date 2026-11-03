from pydantic import BaseModel, ConfigDict

from app.schemas.datatypes import PlainCodingRow


class PlainMedicationCodeableConcept(BaseModel):
    model_config = ConfigDict(extra="allow")

    coding: list[PlainCodingRow] | None = None
    text: str | None = None
