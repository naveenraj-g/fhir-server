from pydantic import BaseModel, ConfigDict, Field


class PatientUserLinkResponse(BaseModel):
    """Who a patient record is linked to. Not a FHIR resource: the link is
    server-side state, kept out of the Patient document."""

    model_config = ConfigDict(
        json_schema_extra={"example": {"patient_id": 10000, "user_id": "user-abc123"}}
    )

    patient_id: int = Field(..., description="Public patient id.")
    user_id: str | None = Field(
        None, description="Linked IAM user id, or null when the record is not linked."
    )
