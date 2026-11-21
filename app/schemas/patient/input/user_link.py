from pydantic import BaseModel, ConfigDict, Field


class PatientUserLinkInput(BaseModel):
    """Body of `PUT /patients/{id}/user`: the IAM user (the JWT `sub`) this
    patient record belongs to."""

    model_config = ConfigDict(
        extra="forbid", json_schema_extra={"example": {"user_id": "user-abc123"}}
    )

    user_id: str = Field(
        ...,
        min_length=1,
        description="IAM user id (the JWT `sub`) to link to this patient.",
    )
