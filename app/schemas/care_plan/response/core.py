from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRQuantity,
    FHIRReference,
)
from app.schemas.datatypes.annotation import FHIRAnnotation
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRCarePlanActivityDetail(BaseModel):
    kind: str | None = Field(None, description="Kind of resource the activity is.")
    instantiatesCanonical: list[str] | None = Field(
        None, description="Instantiates FHIR protocol or definition."
    )
    instantiatesUri: list[str] | None = Field(
        None, description="Instantiates external protocol or definition."
    )
    code: FHIRCodeableConcept | None = Field(
        None, description="Detail type of activity."
    )
    reasonCode: list[FHIRCodeableConcept] | None = Field(
        None, description="Why activity should be done or why activity was prohibited."
    )
    reasonReference: list[FHIRReference] | None = Field(
        None, description="Why activity is needed."
    )
    goal: list[FHIRReference] | None = Field(
        None, description="Goals this activity relates to."
    )
    status: str | None = Field(None, description="Current state of the activity.")
    statusReason: FHIRCodeableConcept | None = Field(
        None, description="Reason for current status."
    )
    doNotPerform: bool | None = Field(
        None, description="If true, activity is prohibiting action."
    )
    scheduledTiming: dict | None = Field(
        None, description="When activity is to occur (Timing)."
    )
    scheduledPeriod: FHIRPeriod | None = Field(
        None, description="When activity is to occur (Period)."
    )
    scheduledString: str | None = Field(
        None, description="When activity is to occur (string)."
    )
    location: FHIRReference | None = Field(None, description="Where it should happen.")
    performer: list[FHIRReference] | None = Field(
        None, description="Who will be responsible?"
    )
    productCodeableConcept: FHIRCodeableConcept | None = Field(
        None, description="What is to be administered/supplied (CodeableConcept)."
    )
    productReference: FHIRReference | None = Field(
        None, description="What is to be administered/supplied (Reference)."
    )
    dailyAmount: FHIRQuantity | None = Field(None, description="How to consume/day?")
    quantity: FHIRQuantity | None = Field(
        None, description="How much to administer/supply/consume."
    )
    description: str | None = Field(
        None, description="Extra info describing activity to perform."
    )


class FHIRCarePlanActivity(BaseModel):
    outcomeCodeableConcept: list[FHIRCodeableConcept] | None = Field(
        None, description="Results of the activity."
    )
    outcomeReference: list[FHIRReference] | None = Field(
        None, description="Appointment, Encounter, Procedure, etc."
    )
    progress: list[FHIRAnnotation] | None = Field(
        None, description="Comments about the activity status/progress."
    )
    reference: FHIRReference | None = Field(
        None, description="Activity details defined in specific resource."
    )
    detail: FHIRCarePlanActivityDetail | None = Field(
        None, description="In-line definition of activity."
    )


class FHIRCarePlanSchema(BaseModel):
    resourceType: str = Field("CarePlan", description="Always 'CarePlan'.")
    id: str = Field(..., description="Public care_plan_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="External Ids for this plan."
    )
    instantiatesCanonical: list[str] | None = Field(
        None, description="Instantiates FHIR protocol or definition."
    )
    instantiatesUri: list[str] | None = Field(
        None, description="Instantiates external protocol or definition."
    )
    basedOn: list[FHIRReference] | None = Field(None, description="Fulfills CarePlan.")
    replaces: list[FHIRReference] | None = Field(
        None, description="CarePlan replaced by this CarePlan."
    )
    partOf: list[FHIRReference] | None = Field(
        None, description="Part of referenced CarePlan."
    )
    status: str | None = Field(
        None,
        description="draft | active | on-hold | revoked | completed | entered-in-error | unknown.",
    )
    intent: str | None = Field(None, description="proposal | plan | order | option.")
    category: list[FHIRCodeableConcept] | None = Field(
        None, description="Type of plan."
    )
    title: str | None = Field(
        None, description="Human-friendly name for the care plan."
    )
    description: str | None = Field(None, description="Summary of nature of plan.")
    subject: FHIRReference | None = Field(None, description="Who the care plan is for.")
    encounter: FHIRReference | None = Field(
        None, description="The Encounter during which this CarePlan was created."
    )
    period: FHIRPeriod | None = Field(None, description="Time period plan covers.")
    created: str | None = Field(None, description="Date record was first recorded.")
    author: FHIRReference | None = Field(
        None, description="Who is the designated responsible party."
    )
    contributor: list[FHIRReference] | None = Field(
        None, description="Who provided the content of the care plan."
    )
    careTeam: list[FHIRReference] | None = Field(
        None, description="Who's involved in plan?"
    )
    addresses: list[FHIRReference] | None = Field(
        None, description="Health issues this plan addresses."
    )
    supportingInfo: list[FHIRReference] | None = Field(
        None, description="Information considered as part of plan."
    )
    goal: list[FHIRReference] | None = Field(
        None, description="Desired outcome of plan."
    )
    activity: list[FHIRCarePlanActivity] | None = Field(
        None, description="Action to occur as part of plan."
    )
    note: list[FHIRAnnotation] | None = Field(
        None, description="Comments about the plan."
    )


class FHIRCarePlanBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRCarePlanSchema | dict = Field(
        ...,
        description="A CarePlan (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Patient / Group / Encounter / CareTeam / Condition / Practitioner / PractitionerRole / RelatedPerson / Organization / HealthcareService / Appointment / MedicationRequest / ServiceRequest / CarePlan (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRCarePlanBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRCarePlanBundleEntry] | None = None
