from pydantic import BaseModel, Field

from app.schemas.common.fhir import FHIRReference


class PlainPatientGeneralPractitioner(BaseModel):
    """Plain-JSON Patient.generalPractitioner — a reference to the patient's
    nominated primary care provider."""

    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded tenant/account ID this row is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    reference_type: str | None = Field(
        None, description="Organization|Practitioner|PractitionerRole"
    )
    reference_id: int | None = Field(
        None,
        description="Public id of the referenced Organization/Practitioner/PractitionerRole.",
    )
    reference_display: str | None = Field(
        None, description="Display text for the referenced resource."
    )
    reference_identifier_use: str | None = Field(
        None,
        description="Fallback identifier (used when the referenced resource isn't "
        "in this system) — usual|official|temp|secondary|old.",
    )
    reference_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — coding system for its type."
    )
    reference_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type coding system."
    )
    reference_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type (e.g. MR, SS)."
    )
    reference_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    reference_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — plain-text rendering of its type."
    )
    reference_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was user-selected.",
    )
    reference_identifier_system: str | None = Field(
        None, description="Fallback identifier — URI namespace."
    )
    reference_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    reference_identifier_period_start: str | None = Field(
        None, description="Fallback identifier — ISO 8601 datetime it became valid."
    )
    reference_identifier_period_end: str | None = Field(
        None,
        description="Fallback identifier — ISO 8601 datetime it stopped being valid.",
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


class PatientGeneralPractitionersListResponse(BaseModel):
    """Plain-JSON list envelope for GET /{patient_id}/general-practitioners."""

    data: list[PlainPatientGeneralPractitioner] = Field(
        ..., description="General-practitioner reference entries for the patient."
    )
    total: int = Field(
        ..., description="Total count of general practitioner references."
    )


class FHIRPatientGeneralPractitionerListItem(FHIRReference):
    """FHIRReference plus the internal row id, for the GET /{patient_id}/general-practitioners list item."""

    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPatientGeneralPractitionersListResponse(BaseModel):
    """FHIR-camelCase list envelope for GET /{patient_id}/general-practitioners."""

    data: list[FHIRPatientGeneralPractitionerListItem] = Field(
        ..., description="General-practitioner reference entries for the patient."
    )
    total: int = Field(
        ..., description="Total count of general practitioner references."
    )
