from pydantic import BaseModel, Field

from app.schemas.common.fhir import FHIRCodeableConcept


class FHIRCommunication(BaseModel):
    language: FHIRCodeableConcept | None = Field(
        None, description="Language as CodeableConcept (BCP-47)."
    )


class PlainPractitionerCommunication(BaseModel):
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
        None,
        description="A representation of the meaning of the language code, following the rules of the system.",
    )
    language_text: str | None = Field(
        None,
        description="A human language representation of the language, as seen/selected/entered by the user.",
    )
    language_user_selected: bool | None = Field(
        None,
        description="Whether this language coding was chosen directly by the user.",
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


class PractitionerCommunicationsListResponse(BaseModel):
    data: list[PlainPractitionerCommunication]
    total: int = Field(..., description="Total count of communication entries.")


class FHIRPractitionerCommunicationListItem(FHIRCommunication):
    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPractitionerCommunicationsListResponse(BaseModel):
    data: list[FHIRPractitionerCommunicationListItem]
    total: int = Field(..., description="Total count of communication entries.")
