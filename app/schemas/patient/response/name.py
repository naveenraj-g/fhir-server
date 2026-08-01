from pydantic import BaseModel, Field

from app.schemas.common.fhir import FHIRHumanName


class PlainPatientName(BaseModel):
    """Plain-JSON HumanName — a name associated with the patient."""

    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded tenant/account ID this row is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    use: str | None = Field(
        None, description="usual|official|temp|nickname|anonymous|old|maiden"
    )
    text: str | None = Field(None, description="Full name as a display string.")
    family: str | None = Field(None, description="Family (last) name.")
    given: list[str] | None = Field(
        None, description="Given (first/middle) names, in order."
    )
    prefix: list[str] | None = Field(
        None, description="Name prefixes (Mr., Dr., etc.)."
    )
    suffix: list[str] | None = Field(None, description="Name suffixes (Jr., MD, etc.).")
    period_start: str | None = Field(
        None, description="ISO 8601 datetime this name became valid."
    )
    period_end: str | None = Field(
        None, description="ISO 8601 datetime this name stopped being valid."
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


class PatientNamesListResponse(BaseModel):
    """Plain-JSON list envelope for GET /{patient_id}/names."""

    data: list[PlainPatientName] = Field(
        ..., description="HumanName entries for the patient."
    )
    total: int = Field(..., description="Total count of name entries.")


class FHIRPatientNameListItem(FHIRHumanName):
    """FHIRHumanName plus the internal row id, for the GET /{patient_id}/names list item."""

    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPatientNamesListResponse(BaseModel):
    """FHIR-camelCase list envelope for GET /{patient_id}/names."""

    data: list[FHIRPatientNameListItem] = Field(
        ..., description="HumanName entries for the patient."
    )
    total: int = Field(..., description="Total count of name entries.")
