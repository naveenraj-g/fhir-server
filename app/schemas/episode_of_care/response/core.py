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


class FHIREpisodeOfCareStatusHistory(BaseModel):
    status: str | None = Field(
        None,
        description="planned | waitlist | active | onhold | finished | cancelled | entered-in-error.",
    )
    period: FHIRPeriod | None = Field(
        None, description="Duration the EpisodeOfCare was in the specified status."
    )


class FHIREpisodeOfCareDiagnosis(BaseModel):
    condition: FHIRReference | None = Field(
        None, description="Conditions/problems/diagnoses this episode of care is for."
    )
    role: FHIRCodeableConcept | None = Field(
        None, description="Role that this diagnosis has within the episode of care."
    )
    rank: int | None = Field(None, description="Ranking of the diagnosis.")


class FHIREpisodeOfCareSchema(BaseModel):
    resourceType: str = Field("EpisodeOfCare", description="Always 'EpisodeOfCare'.")
    id: str = Field(..., description="Public episode_of_care_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Business Identifier(s) relevant for this EpisodeOfCare."
    )
    status: str | None = Field(
        None,
        description="planned | waitlist | active | onhold | finished | cancelled | entered-in-error.",
    )
    statusHistory: list[FHIREpisodeOfCareStatusHistory] | None = Field(
        None, description="Past list of status codes."
    )
    type: list[FHIRCodeableConcept] | None = Field(
        None, description="Type/class - e.g. specialist referral, disease management."
    )
    diagnosis: list[FHIREpisodeOfCareDiagnosis] | None = Field(
        None, description="The list of diagnosis relevant to this episode of care."
    )
    patient: FHIRReference | None = Field(
        None, description="The patient who is the focus of this episode of care."
    )
    managingOrganization: FHIRReference | None = Field(
        None, description="Organization that assumes care."
    )
    period: FHIRPeriod | None = Field(
        None, description="Interval during responsibility is assumed."
    )
    referralRequest: list[FHIRReference] | None = Field(
        None, description="Originating Referral Request(s)."
    )
    careManager: FHIRReference | None = Field(
        None, description="Care manager/care coordinator for the patient."
    )
    team: list[FHIRReference] | None = Field(
        None, description="Other practitioners facilitating this episode of care."
    )
    account: list[FHIRReference] | None = Field(
        None,
        description="The set of accounts that may be used for billing for this EpisodeOfCare.",
    )


class FHIREpisodeOfCareBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIREpisodeOfCareSchema | dict = Field(
        ...,
        description="An EpisodeOfCare (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Patient / Organization / Practitioner / Condition / ServiceRequest / Encounter (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIREpisodeOfCareBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIREpisodeOfCareBundleEntry] | None = None
