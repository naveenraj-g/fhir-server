from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.consent.response.codeable_concept import (
    PlainConsentCodeableConcept,
)
from app.schemas.consent.response.identifier import PlainConsentIdentifier
from app.schemas.consent.response.policy import (
    FHIRConsentPolicy,
    PlainConsentPolicy,
    PlainConsentReference,
)
from app.schemas.consent.response.provision import (
    FHIRConsentProvision,
    PlainConsentProvision,
)
from app.schemas.consent.response.verification import (
    FHIRConsentVerification,
    PlainConsentVerification,
)
from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRReference,
)


class FHIRConsentSchema(BaseModel):
    """FHIR R4 Consent resource schema."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["Consent"] = "Consent"
    id: str
    meta: FHIRMeta | None = None
    identifier: list[FHIRIdentifier] | None = None
    status: str
    scope: FHIRCodeableConcept
    category: list[FHIRCodeableConcept]
    patient: FHIRReference | None = None
    dateTime: str | None = None
    performer: list[FHIRReference] | None = None
    organization: list[FHIRReference] | None = None
    sourceAttachment: dict[str, Any] | None = None
    sourceReference: FHIRReference | None = None
    policy: list[FHIRConsentPolicy] | None = None
    policyRule: FHIRCodeableConcept | None = None
    verification: list[FHIRConsentVerification] | None = None
    provision: FHIRConsentProvision | None = None
    extension: list[dict[str, Any]] | None = None


class PlainConsentResponse(BaseModel):
    """Plain snake_case response schema for Consent."""

    model_config = ConfigDict(extra="ignore")

    id: int = Field(..., description="Public sequence Consent ID.")
    status: str = Field(
        ...,
        description="draft | proposed | active | rejected | inactive | entered-in-error.",
    )
    scope: PlainConsentCodeableConcept = Field(
        ..., description="Which problem code this consent applies to."
    )
    category: list[PlainConsentCodeableConcept] = Field(
        ..., description="Classification of the consent statement."
    )
    patient: str | None = Field(None, description="Who the consent applies to.")
    patient_display: str | None = Field(
        None, description="Plain text display for patient reference."
    )
    date_time: datetime | None = Field(
        None, description="When this Consent was created or indexed."
    )
    performer: list[PlainConsentReference] | None = Field(
        None, description="Who is agreeing to the policy and rules."
    )
    organization: list[PlainConsentReference] | None = Field(
        None, description="Custodian of the consent."
    )
    source_attachment: dict[str, Any] | None = Field(
        None, description="Source attachment as FHIR Attachment dict."
    )
    source_reference: str | None = Field(
        None, description="Source reference string."
    )
    source_reference_display: str | None = Field(
        None, description="Display name for source reference."
    )
    policy: list[PlainConsentPolicy] | None = Field(
        None, description="Policies that this consent's rule conforms to."
    )
    policy_rule: PlainConsentCodeableConcept | None = Field(
        None, description="Regulation that this consent conforms to."
    )
    verification: list[PlainConsentVerification] | None = Field(
        None, description="Consent verification by patient or guardian."
    )
    provision: PlainConsentProvision | None = Field(
        None, description="Constraints to the base Consent.provision rule."
    )
    identifier: list[PlainConsentIdentifier] | None = Field(
        None, description="External identifiers."
    )
    extension: list[dict[str, Any]] | None = Field(
        None, description="Extensions."
    )


class PaginatedConsentResponse(BaseModel):
    """Paginated response for plain Consent listing."""

    model_config = ConfigDict(extra="ignore")

    total: int
    limit: int
    offset: int
    data: list[PlainConsentResponse]


class FHIRConsentBundleEntry(BaseModel):
    """Single entry in FHIR Consent searchset bundle."""

    model_config = ConfigDict(extra="allow")

    fullUrl: str | None = None
    resource: FHIRConsentSchema


class FHIRConsentBundle(BaseModel):
    """FHIR searchset Bundle for Consent resources."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["Bundle"] = "Bundle"
    type: Literal["searchset"] = "searchset"
    total: int
    entry: list[FHIRConsentBundleEntry] = []
