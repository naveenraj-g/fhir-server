from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRConsentPolicy(BaseModel):
    authority: str | None = Field(None, description="Enforcement source for policy.")
    uri: str | None = Field(
        None, description="Specific policy covered by this consent."
    )


class FHIRConsentVerification(BaseModel):
    verified: bool | None = Field(None, description="Has been verified.")
    verifiedWith: FHIRReference | None = Field(None, description="Person who verified.")
    verificationDate: str | None = Field(None, description="When consent verified.")


class FHIRConsentProvisionActor(BaseModel):
    role: FHIRCodeableConcept | None = Field(
        None, description="How the actor is involved."
    )
    reference: FHIRReference | None = Field(None, description="Resource for the actor.")


class FHIRConsentProvisionData(BaseModel):
    meaning: str | None = Field(
        None, description="instance | related | dependents | authoredby."
    )
    reference: FHIRReference | None = Field(
        None, description="The actual data reference."
    )


class FHIRConsentProvision(BaseModel):
    type: str | None = Field(None, description="deny | permit.")
    period: FHIRPeriod | None = Field(None, description="Timeframe for this rule.")
    actor: list[FHIRConsentProvisionActor] | None = Field(
        None, description="Who|what controlled by this rule."
    )
    action: list[FHIRCodeableConcept] | None = Field(
        None, description="Actions controlled by this rule."
    )
    securityLabel: list[dict] | None = Field(
        None, description="Security Labels that define affected resources (Codings)."
    )
    purpose: list[dict] | None = Field(
        None, description="Context of activities covered by this rule (Codings)."
    )
    class_: list[dict] | None = Field(
        None, alias="class", description="e.g. Resource Type, Profile, CDA, etc."
    )
    code: list[FHIRCodeableConcept] | None = Field(
        None, description="e.g. LOINC or SNOMED CT code, etc. in the content."
    )
    dataPeriod: FHIRPeriod | None = Field(
        None, description="Timeframe for data controlled by this rule."
    )
    data: list[FHIRConsentProvisionData] | None = Field(
        None, description="Data controlled by this rule."
    )
    provision: list[dict] | None = Field(None, description="Nested Exception Rules.")

    model_config = {"populate_by_name": True}


class FHIRConsentSchema(BaseModel):
    resourceType: str = Field("Consent", description="Always 'Consent'.")
    id: str = Field(..., description="Public consent_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Identifier for this record."
    )
    status: str | None = Field(
        None,
        description="draft | proposed | active | rejected | inactive | entered-in-error.",
    )
    scope: FHIRCodeableConcept | None = Field(
        None, description="Which of the four areas this resource covers."
    )
    category: list[FHIRCodeableConcept] | None = Field(
        None, description="Classification of the consent statement."
    )
    patient: FHIRReference | None = Field(
        None, description="Who the consent applies to."
    )
    dateTime: str | None = Field(
        None, description="When this Consent was created or indexed."
    )
    performer: list[FHIRReference] | None = Field(
        None, description="Who is agreeing to the policy and rules."
    )
    organization: list[FHIRReference] | None = Field(
        None, description="Custodian of the consent."
    )
    sourceAttachment: dict | None = Field(
        None, description="source[x]: the source of the consent, as an Attachment."
    )
    sourceReference: FHIRReference | None = Field(
        None, description="source[x]: the source of the consent, as a Reference."
    )
    policy: list[FHIRConsentPolicy] | None = Field(
        None, description="Policies covered by this consent."
    )
    policyRule: FHIRCodeableConcept | None = Field(
        None, description="Regulation that this consents to."
    )
    verification: list[FHIRConsentVerification] | None = Field(
        None, description="Consent Verified by patient or family."
    )
    provision: FHIRConsentProvision | None = Field(
        None, description="Constraints to the base Consent.policyRule."
    )


class FHIRConsentBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRConsentSchema | dict = Field(
        ...,
        description="A Consent (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included resource (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRConsentBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRConsentBundleEntry] | None = None
