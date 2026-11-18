from pydantic import BaseModel, Field


class PractitionerUserLinkResponse(BaseModel):
    """Who a practitioner record is linked to. Not a FHIR resource: the
    link is server-side state, kept out of the Practitioner document."""

    practitioner_id: int = Field(..., description="Public practitioner id.")
    user_id: str | None = Field(
        None, description="Linked IAM user id, or null when the record is not linked."
    )
