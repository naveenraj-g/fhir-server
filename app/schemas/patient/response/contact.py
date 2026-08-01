from pydantic import BaseModel, Field

from app.schemas.common.fhir import (
    FHIRAddress,
    FHIRCodeableConcept,
    FHIRContactPoint,
    FHIRHumanName,
    FHIRPeriod,
    FHIRReference,
)


class FHIRPatientContact(BaseModel):
    """FHIR R4 Patient.contact BackboneElement — a contact party (guardian,
    partner, friend, etc.) for the patient."""

    relationship: list[FHIRCodeableConcept] | None = Field(
        None, description="The kind(s) of relationship this contact has to the patient."
    )
    name: FHIRHumanName | None = Field(
        None, description="A name associated with the contact person."
    )
    telecom: list[FHIRContactPoint] | None = Field(
        None,
        description="Contact detail(s) (phone, email, etc.) for the contact person.",
    )
    address: FHIRAddress | None = Field(
        None, description="Address for the contact person."
    )
    gender: str | None = Field(None, description="male|female|other|unknown")
    organization: FHIRReference | None = Field(
        None,
        description=(
            "Organization on behalf of which the contact is acting or for which the "
            "contact is associated. Per pat-1, required if none of name, telecom, "
            "or address is given."
        ),
    )
    period: FHIRPeriod | None = Field(
        None,
        description="The period during which this contact is valid to be contacted regarding the patient.",
    )


class PlainContactRelationship(BaseModel):
    """Plain-JSON CodeableConcept — the kind of relationship a Patient.contact has to the patient."""

    id: int = Field(..., description="Internal row ID.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded tenant/account ID this row is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    coding_system: str | None = Field(
        None, description="Coding system that defines this relationship code."
    )
    coding_version: str | None = Field(
        None, description="Version of the coding system."
    )
    coding_code: str | None = Field(
        None,
        description="Code for the nature of the relationship (e.g. C, N, MTH, FTH).",
    )
    coding_display: str | None = Field(
        None, description="Human-readable display for the relationship code."
    )
    text: str | None = Field(
        None, description="Plain-text rendering of the relationship CodeableConcept."
    )
    coding_user_selected: bool | None = Field(
        None, description="Whether this coding was chosen directly by the user."
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


class PlainContactTelecom(BaseModel):
    """Plain-JSON ContactPoint — a contact detail for the patient's contact person."""

    id: int = Field(..., description="Internal row ID.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded tenant/account ID this row is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    system: str | None = Field(None, description="phone|fax|email|pager|url|sms|other")
    value: str | None = Field(
        None, description="Contact point details (phone number, email address, etc.)."
    )
    use: str | None = Field(None, description="home|work|temp|old|mobile")
    rank: int | None = Field(
        None, description="Preferred order of use — 1 indicates the most preferred."
    )
    period_start: str | None = Field(
        None, description="ISO 8601 datetime this contact point became valid."
    )
    period_end: str | None = Field(
        None, description="ISO 8601 datetime this contact point stopped being valid."
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


class PlainPatientContact(BaseModel):
    """Plain-JSON Patient.contact BackboneElement — a contact party (guardian,
    next-of-kin, emergency contact) for the patient."""

    id: int = Field(..., description="Internal row ID — use for PATCH/DELETE calls.")
    org_id: str | None = Field(
        None,
        description="Gateway-forwarded tenant/account ID this row is scoped to (multi-tenancy) — not a FHIR concept.",
    )
    relationship: list[PlainContactRelationship] | None = Field(
        None, description="The kind(s) of relationship this contact has to the patient."
    )
    name_use: str | None = Field(
        None, description="usual|official|temp|nickname|anonymous|old|maiden"
    )
    name_text: str | None = Field(
        None, description="Full name of the contact person as a display string."
    )
    name_family: str | None = Field(
        None, description="Family name of the contact person."
    )
    name_given: list[str] | None = Field(
        None, description="Given names of the contact person, in order."
    )
    name_prefix: list[str] | None = Field(
        None, description="Name prefixes for the contact person."
    )
    name_suffix: list[str] | None = Field(
        None, description="Name suffixes for the contact person."
    )
    name_period_start: str | None = Field(
        None, description="ISO 8601 datetime the contact person's name became valid."
    )
    name_period_end: str | None = Field(
        None,
        description="ISO 8601 datetime the contact person's name stopped being valid.",
    )
    telecom: list[PlainContactTelecom] | None = Field(
        None, description="Contact detail(s) for the contact person."
    )
    address_use: str | None = Field(None, description="home|work|temp|old|billing")
    address_type: str | None = Field(None, description="postal|physical|both")
    address_text: str | None = Field(
        None, description="Full address of the contact person as a display string."
    )
    address_line: list[str] | None = Field(
        None, description="Street address lines for the contact person."
    )
    address_city: str | None = Field(
        None, description="City for the contact person's address."
    )
    address_district: str | None = Field(
        None, description="County/district for the contact person's address."
    )
    address_state: str | None = Field(
        None, description="State for the contact person's address."
    )
    address_postal_code: str | None = Field(
        None, description="Postal code for the contact person's address."
    )
    address_country: str | None = Field(
        None, description="Country for the contact person's address."
    )
    address_period_start: str | None = Field(
        None, description="ISO 8601 datetime the contact person's address became valid."
    )
    address_period_end: str | None = Field(
        None,
        description="ISO 8601 datetime the contact person's address stopped being valid.",
    )
    gender: str | None = Field(None, description="male|female|other|unknown")
    organization_type: str | None = Field(
        None, description="Reference type for the associated organization."
    )
    organization_id: int | None = Field(
        None, description="Public id of the associated Organization."
    )
    organization_display: str | None = Field(
        None, description="Display text for the associated organization."
    )
    organization_identifier_use: str | None = Field(
        None,
        description="Fallback identifier (used when the associated organization "
        "isn't a resource in this system) — usual|official|temp|secondary|old.",
    )
    organization_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — coding system for its type."
    )
    organization_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type coding system."
    )
    organization_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — code for its type (e.g. MR, SS)."
    )
    organization_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    organization_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — plain-text rendering of its type."
    )
    organization_identifier_type_user_selected: bool | None = Field(
        None,
        description="Fallback identifier — whether its type coding was user-selected.",
    )
    organization_identifier_system: str | None = Field(
        None, description="Fallback identifier — URI namespace."
    )
    organization_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    organization_identifier_period_start: str | None = Field(
        None, description="Fallback identifier — ISO 8601 datetime it became valid."
    )
    organization_identifier_period_end: str | None = Field(
        None,
        description="Fallback identifier — ISO 8601 datetime it stopped being valid.",
    )
    period_start: str | None = Field(
        None,
        description="ISO 8601 datetime this contact became valid to be contacted regarding the patient.",
    )
    period_end: str | None = Field(
        None,
        description="ISO 8601 datetime this contact stopped being valid to be contacted regarding the patient.",
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


class PatientContactsListResponse(BaseModel):
    """Plain-JSON list envelope for GET /{patient_id}/contacts."""

    data: list[PlainPatientContact] = Field(
        ..., description="Contact entries for the patient."
    )
    total: int = Field(..., description="Total count of contact entries.")


class FHIRPatientContactListItem(FHIRPatientContact):
    """FHIRPatientContact plus the internal row id, for the GET /{patient_id}/contacts list item."""

    id: int = Field(..., description="Internal row ID — use for DELETE calls.")


class FHIRPatientContactsListResponse(BaseModel):
    """FHIR-camelCase list envelope for GET /{patient_id}/contacts."""

    data: list[FHIRPatientContactListItem] = Field(
        ..., description="Contact entries for the patient."
    )
    total: int = Field(..., description="Total count of contact entries.")
