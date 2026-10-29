from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import ContactPointInput


class QuestionnaireContactInput(BaseModel):
    """Questionnaire.contact (0..* ContactDetail) — just `{name, telecom[]}`,
    unlike Organization.contact's BackboneElement (purpose/name/telecom/
    address)."""

    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(
        None, description="Name of an individual to contact."
    )
    telecom: list[ContactPointInput] | None = Field(
        None, description="Contact details for individual or organization."
    )
