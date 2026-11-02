from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import PlainCodingRow


class PlainDetectedIssueCodeableConcept(BaseModel):
    """Plain snake_case response representation for CodeableConcept."""

    model_config = ConfigDict(extra="forbid")

    text: str | None = Field(None, description="Plain text representation of the concept.")
    coding: list[PlainCodingRow] | None = Field(
        None, description="Code defined by a terminology system."
    )
