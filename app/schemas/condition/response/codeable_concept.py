from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import PlainCodingRow


class PlainConditionCategory(BaseModel):
    """Plain response shape for Condition.category."""

    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Internal DB ID.")
    text: str | None = Field(None, description="A human language representation of the category.")
    codings: list[PlainCodingRow] | None = Field(None, description="Coding(s) for this category.")


class PlainConditionBodySite(BaseModel):
    """Plain response shape for Condition.bodySite."""

    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Internal DB ID.")
    text: str | None = Field(None, description="A human language representation of the bodySite.")
    codings: list[PlainCodingRow] | None = Field(None, description="Coding(s) for this bodySite.")
