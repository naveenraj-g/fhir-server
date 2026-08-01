from pydantic import BaseModel, Field

from app.schemas.common.fhir import FHIRCodeableConcept


class FHIRPatientCommunication(BaseModel):
    """FHIR R4 Patient.communication BackboneElement — a language the patient can
    use for healthcare-related communication."""

    language: FHIRCodeableConcept = Field(
        ...,
        description="The language which can be used to communicate with the patient about their health.",
    )
    preferred: bool | None = Field(
        None,
        description="Indicates whether this language is preferred for communicating with the patient.",
    )


class PlainPatientCommunication(BaseModel):
    """Plain-JSON Patient.communication BackboneElement — a language the patient
    can use for healthcare-related communication."""

    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded tenant/account ID this row is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    language_system: str | None = Field(
        None, description="URI of the language code system."
    )
    language_version: str | None = Field(
        None, description="Version of the language code system."
    )
    language_code: str | None = Field(
        None, description="ISO-639-1 language code (e.g. en, fr, de)."
    )
    language_display: str | None = Field(
        None, description="Human-readable name of the language."
    )
    language_text: str | None = Field(
        None, description="Plain-text rendering of the language concept."
    )
    language_user_selected: bool | None = Field(
        None, description="Whether this coding was chosen directly by the user."
    )
    preferred: bool | None = Field(
        None, description="True if this is the patient's preferred language."
    )
    created_at: str | None = Field(
        None, description="ISO 8601 datetime when this row was created."
    )
    updated_at: str | None = Field(
        None, description="ISO 8601 datetime when this row was last updated."
    )
    created_by: str | None = Field(
        None, description="Acting-user value recorded as the creator of this row."
    )
    updated_by: str | None = Field(
        None, description="Acting-user value recorded as the last updater of this row."
    )


class PatientCommunicationsListResponse(BaseModel):
    """Plain-JSON list envelope for GET /{patient_id}/communications."""

    data: list[PlainPatientCommunication] = Field(
        ..., description="Communication-language entries for the patient."
    )
    total: int = Field(..., description="Total count of communication entries.")


class FHIRPatientCommunicationListItem(FHIRPatientCommunication):
    """FHIRPatientCommunication plus the internal row id, for the GET /{patient_id}/communications list item."""

    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPatientCommunicationsListResponse(BaseModel):
    """FHIR-camelCase list envelope for GET /{patient_id}/communications."""

    data: list[FHIRPatientCommunicationListItem] = Field(
        ..., description="Communication-language entries for the patient."
    )
    total: int = Field(..., description="Total count of communication entries.")
