from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput


class LocationTypeInput(BaseModel):
    """Location.type — the function performed at the location (CodeableConcept).
    `text` is the CodeableConcept's own field (sibling of coding[], not part
    of it); `coding` is the real 0..* list — see app.schemas.datatypes.CodingInput.
    Mirrors app.schemas.organization.input.type.OrganizationTypeInput."""

    model_config = ConfigDict(extra="forbid")
    coding: list[CodingInput] | None = Field(
        None,
        description="Coding(s) for this location type — may include both a custom code and a standard-terminology crosswalk.",
    )
    text: str | None = Field(
        None,
        description="A human language representation of the location type, as seen/selected/entered by the user.",
    )
