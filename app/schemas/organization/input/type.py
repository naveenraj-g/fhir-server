from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import CodingInput


class OrganizationTypeInput(BaseModel):
    """Organization.type — the kind(s) of organization that this is (CodeableConcept).
    `text` is the CodeableConcept's own field (sibling of coding[], not part
    of it); `coding` is the real 0..* list — see app.schemas.datatypes.CodingInput."""

    model_config = ConfigDict(extra="forbid")
    coding: list[CodingInput] | None = Field(
        None,
        description="Coding(s) for this organization type — may include both an org-defined custom code and a standard-terminology crosswalk.",
    )
    text: str | None = Field(
        None,
        description="A human language representation of the organization type, as seen/selected/entered by the user.",
    )
