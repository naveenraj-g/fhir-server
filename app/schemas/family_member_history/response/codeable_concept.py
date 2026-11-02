from pydantic import BaseModel, ConfigDict

from app.schemas.datatypes import PlainCodingRow


class PlainFamilyMemberHistoryCodeableConcept(BaseModel):
    """Plain CodeableConcept shape for FamilyMemberHistory response."""

    model_config = ConfigDict(extra="ignore")

    coding: list[PlainCodingRow] | None = None
    text: str | None = None
