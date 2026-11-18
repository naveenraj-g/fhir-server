from pydantic import BaseModel, Field


class PatientUserLinkResponse(BaseModel):
    """Who a patient record is linked to. Not a FHIR resource: the link is
    server-side state, kept out of the Patient document."""

    patient_id: int = Field(..., description="Public patient id.")
    user_id: str | None = Field(
        None, description="Linked IAM user id, or null when the record is not linked."
    )
