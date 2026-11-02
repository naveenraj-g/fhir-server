from pydantic import BaseModel, ConfigDict


class PlainMedicationStatementCode(BaseModel):
    model_config = ConfigDict(extra="allow")

    system: str | None = None
    version: str | None = None
    code: str | None = None
    display: str | None = None
    user_selected: bool | None = None


class PlainMedicationStatementCodeableConcept(BaseModel):
    model_config = ConfigDict(extra="allow")

    text: str | None = None
    coding: list[PlainMedicationStatementCode] | None = None
