from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput


class QuestionnaireJurisdictionInput(BaseModel):
    """One entry of Questionnaire.jurisdiction (0..* CodeableConcept) —
    mirrors app.schemas.organization.input.OrganizationTypeInput's shape."""

    model_config = ConfigDict(extra="forbid")
    coding: list[CodingInput] | None = Field(
        None, description="Coding(s) for this jurisdiction."
    )
    text: str | None = Field(
        None, description="A human language representation of the jurisdiction."
    )
