from pydantic import BaseModel, ConfigDict, Field


class PractitionerUserLinkInput(BaseModel):
    """Body of `PUT /practitioners/{id}/user`: the IAM user (the JWT `sub`)
    who acts as this practitioner."""

    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"example": {"user_id": "user-abc123"}}
    )

    user_id: str = Field(
        ..., min_length=1, description="IAM user id (the JWT `sub`) to link to this practitioner."
    )
