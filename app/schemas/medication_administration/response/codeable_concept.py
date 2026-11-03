from pydantic import BaseModel, ConfigDict

from app.schemas.datatypes import PlainCodingRow


class PlainMedicationAdministrationCodeableConcept(BaseModel):
    model_config = ConfigDict(extra="allow")

    text: str | None = None
    coding: list[PlainCodingRow] | None = None
