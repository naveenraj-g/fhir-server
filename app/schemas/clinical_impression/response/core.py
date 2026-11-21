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


class FHIRClinicalImpressionAnnotation(BaseModel):
    authorReference: FHIRReference | None = Field(None, description="Individual responsible for the annotation.")
    authorString: str | None = Field(None, description="Individual responsible for the annotation, as plain text.")
    time: str | None = Field(None, description="When the annotation was made.")
    text: str | None = Field(None, description="The annotation text.")


class FHIRClinicalImpressionInvestigation(BaseModel):
    code: FHIRCodeableConcept | None = Field(None, description="A name/code for the set.")
    item: list[FHIRReference] | None = Field(None, description="Record of a specific investigation.")


class FHIRClinicalImpressionFinding(BaseModel):
    itemCodeableConcept: FHIRCodeableConcept | None = Field(None, description="What was found.")
    itemReference: FHIRReference | None = Field(None, description="What was found.")
    basis: str | None = Field(None, description="Which investigations support the finding.")


class FHIRClinicalImpressionSchema(BaseModel):
    resourceType: str = Field("ClinicalImpression", description="Always 'ClinicalImpression'.")
    id: str = Field(..., description="Public clinical_impression_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries."
    )
    identifier: list[FHIRIdentifier] | None = Field(None, description="Business identifier.")
    status: str | None = Field(None, description="in-progress | completed | entered-in-error.")
    statusReason: FHIRCodeableConcept | None = Field(None, description="Reason for current status.")
    code: FHIRCodeableConcept | None = Field(None, description="Kind of assessment performed.")
    description: str | None = Field(None, description="Why/how the assessment was performed.")
    subject: FHIRReference | None = Field(None, description="Patient or group assessed.")
    encounter: FHIRReference | None = Field(None, description="Encounter created as part of.")
    effectiveDateTime: str | None = Field(None, description="Time of assessment (dateTime).")
    effectivePeriod: FHIRPeriod | None = Field(None, description="Time of assessment (Period).")
    date: str | None = Field(None, description="When the assessment was documented.")
    assessor: FHIRReference | None = Field(None, description="The clinician performing the assessment.")
    previous: FHIRReference | None = Field(None, description="Reference to last assessment.")
    problem: list[FHIRReference] | None = Field(None, description="Relevant impressions of patient state.")
    investigation: list[FHIRClinicalImpressionInvestigation] | None = Field(None, description="One or more sets of investigations.")
    protocol: list[str] | None = Field(None, description="Clinical Protocol followed.")
    summary: str | None = Field(None, description="Summary of the assessment.")
    finding: list[FHIRClinicalImpressionFinding] | None = Field(None, description="Possible or likely findings and diagnoses.")
    prognosisCodeableConcept: list[FHIRCodeableConcept] | None = Field(None, description="Estimate of likely outcome.")
    prognosisReference: list[FHIRReference] | None = Field(None, description="RiskAssessment expressing likely outcome.")
    supportingInfo: list[FHIRReference] | None = Field(None, description="Information supporting the clinical impression.")
    note: list[FHIRClinicalImpressionAnnotation] | None = Field(None, description="Comments made about the ClinicalImpression.")


class FHIRClinicalImpressionBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRClinicalImpressionSchema | dict = Field(
        ...,
        description="A ClinicalImpression (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Patient / Encounter / Condition / Practitioner / PractitionerRole / RiskAssessment (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRClinicalImpressionBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRClinicalImpressionBundleEntry] | None = None
