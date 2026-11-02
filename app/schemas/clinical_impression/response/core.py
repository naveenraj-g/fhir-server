from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
)
from app.schemas.clinical_impression.response.codeable_concept import (
    PlainClinicalImpressionCodeableConcept,
)
from app.schemas.clinical_impression.response.finding import (
    PlainClinicalImpressionFinding,
)
from app.schemas.clinical_impression.response.identifier import (
    PlainClinicalImpressionIdentifier,
)
from app.schemas.clinical_impression.response.investigation import (
    PlainClinicalImpressionInvestigation,
)
from app.schemas.clinical_impression.response.note import (
    PlainClinicalImpressionNote,
)
from app.schemas.clinical_impression.response.reference import (
    PlainClinicalImpressionReference,
)


class FHIRAnnotation(BaseModel):
    """FHIR R4 Annotation datatype."""

    model_config = ConfigDict(extra="forbid")

    authorString: str | None = Field(None, description="Individual responsible for the annotation.")
    authorReference: FHIRReference | None = Field(None, description="Individual responsible for the annotation.")
    time: str | None = Field(None, description="When the annotation was made.")
    text: str = Field(..., description="The annotation — text content (as markdown).")


class FHIRClinicalImpressionInvestigation(BaseModel):
    """ClinicalImpression.investigation FHIR element."""

    model_config = ConfigDict(extra="forbid")

    code: FHIRCodeableConcept = Field(..., description="A name/code for the set of investigations conducted.")
    item: list[FHIRReference] | None = Field(None, description="Record of a specific investigation performed.")


class FHIRClinicalImpressionFinding(BaseModel):
    """ClinicalImpression.finding FHIR element."""

    model_config = ConfigDict(extra="forbid")

    itemCodeableConcept: FHIRCodeableConcept | None = Field(None, description="What was found (codeable concept).")
    itemReference: FHIRReference | None = Field(None, description="What was found (reference).")
    basis: str | None = Field(None, description="Which investigations support finding.")


class FHIRClinicalImpressionSchema(BaseModel):
    """FHIR R4 ClinicalImpression resource schema."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["ClinicalImpression"] = "ClinicalImpression"
    id: str = Field(..., description="Logical id of this artifact.")
    meta: FHIRMeta | None = Field(None, description="Metadata about the resource.")
    extension: list[dict[str, Any]] | None = Field(
        None, description="Additional content defined by implementations."
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Business identifier for impression."
    )
    status: str = Field(
        ...,
        description="in-progress | completed | entered-in-error",
    )
    statusReason: FHIRCodeableConcept | None = Field(
        None, description="Reason for current status."
    )
    code: FHIRCodeableConcept | None = Field(
        None, description="Kind of impression performed."
    )
    description: str | None = Field(
        None, description="Why/how the assessment was performed."
    )
    subject: FHIRReference = Field(
        ..., description="Patient or group impression is about."
    )
    encounter: FHIRReference | None = Field(
        None, description="Encounter created as part of."
    )
    effectiveDateTime: str | None = Field(
        None, description="Time of assessment (dateTime)."
    )
    effectivePeriod: FHIRPeriod | None = Field(
        None, description="Time of assessment (Period)."
    )
    date: str | None = Field(
        None, description="When the assessment was documented."
    )
    assessor: FHIRReference | None = Field(
        None, description="The clinician performing the assessment."
    )
    previous: FHIRReference | None = Field(
        None, description="Reference to last assessment."
    )
    problem: list[FHIRReference] | None = Field(
        None, description="Relevant impressions of patient state."
    )
    investigation: list[FHIRClinicalImpressionInvestigation] | None = Field(
        None, description="One or more sets of investigations."
    )
    protocol: list[str] | None = Field(
        None, description="Clinical Protocol followed (URI)."
    )
    summary: str | None = Field(
        None, description="Summary of the assessment."
    )
    finding: list[FHIRClinicalImpressionFinding] | None = Field(
        None, description="Possible or likely findings and diagnoses."
    )
    prognosisCodeableConcept: list[FHIRCodeableConcept] | None = Field(
        None, description="Estimate of likely outcome (CodeableConcept)."
    )
    prognosisReference: list[FHIRReference] | None = Field(
        None, description="RiskAssessment expressing likely outcome."
    )
    supportingInfo: list[FHIRReference] | None = Field(
        None, description="Information supporting the clinical impression."
    )
    note: list[FHIRAnnotation] | None = Field(
        None, description="Comments made about the ClinicalImpression."
    )


class PlainClinicalImpressionResponse(BaseModel):
    """Plain snake_case ClinicalImpression response schema."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Public sequence identifier.")
    status: str = Field(..., description="Clinical impression status.")
    status_reason: PlainClinicalImpressionCodeableConcept | None = Field(
        None, description="Reason for current status."
    )
    code: PlainClinicalImpressionCodeableConcept | None = Field(
        None, description="Kind of impression performed."
    )
    description: str | None = Field(
        None, description="Why/how the assessment was performed."
    )
    subject: PlainClinicalImpressionReference = Field(
        ..., description="Patient or group impression is about."
    )
    encounter: PlainClinicalImpressionReference | None = Field(
        None, description="Encounter created as part of."
    )
    effective_date_time: datetime | None = Field(
        None, description="Time of assessment."
    )
    effective_period_start: datetime | None = Field(
        None, description="Time of assessment period start."
    )
    effective_period_end: datetime | None = Field(
        None, description="Time of assessment period end."
    )
    date: datetime | None = Field(
        None, description="When the assessment was documented."
    )
    assessor: PlainClinicalImpressionReference | None = Field(
        None, description="The clinician performing the assessment."
    )
    previous: PlainClinicalImpressionReference | None = Field(
        None, description="Reference to last assessment."
    )
    problem: list[PlainClinicalImpressionReference] | None = Field(
        None, description="Relevant impressions of patient state."
    )
    investigation: list[PlainClinicalImpressionInvestigation] | None = Field(
        None, description="One or more sets of investigations."
    )
    protocol: list[str] | None = Field(
        None, description="Clinical Protocol followed (URI)."
    )
    summary: str | None = Field(
        None, description="Summary of the assessment."
    )
    finding: list[PlainClinicalImpressionFinding] | None = Field(
        None, description="Possible or likely findings and diagnoses."
    )
    prognosis_codeable_concept: list[PlainClinicalImpressionCodeableConcept] | None = Field(
        None, description="Estimate of likely outcome (CodeableConcept)."
    )
    prognosis_reference: list[PlainClinicalImpressionReference] | None = Field(
        None, description="RiskAssessment expressing likely outcome."
    )
    supporting_info: list[PlainClinicalImpressionReference] | None = Field(
        None, description="Information supporting the clinical impression."
    )
    note: list[PlainClinicalImpressionNote] | None = Field(
        None, description="Comments made about the ClinicalImpression."
    )
    identifier: list[PlainClinicalImpressionIdentifier] | None = Field(
        None, description="Business identifier for impression."
    )
    extension: list[dict[str, Any]] | None = Field(
        None, description="Additional content defined by implementations."
    )


class PaginatedClinicalImpressionResponse(BaseModel):
    """Paginated response for Plain ClinicalImpression search results."""

    model_config = ConfigDict(extra="forbid")

    total: int = Field(..., description="Total matching items.")
    limit: int = Field(..., description="Items per page.")
    offset: int = Field(..., description="Offset of page.")
    data: list[PlainClinicalImpressionResponse] = Field(..., description="Page of clinical impressions.")


class FHIRClinicalImpressionBundleEntry(BaseModel):
    """Entry element within a ClinicalImpression FHIR Bundle."""

    model_config = ConfigDict(extra="forbid")

    fullUrl: str = Field(..., description="Full URL for resource in bundle.")
    resource: FHIRClinicalImpressionSchema = Field(..., description="The clinical impression resource.")


class FHIRClinicalImpressionBundle(BaseModel):
    """FHIR R4 Bundle containing ClinicalImpression resources."""

    model_config = ConfigDict(extra="forbid")

    resourceType: Literal["Bundle"] = "Bundle"
    type: str = Field("searchset", description="Bundle type.")
    total: int = Field(..., description="Total matching resources.")
    entry: list[FHIRClinicalImpressionBundleEntry] = Field(
        default_factory=list, description="Entries in bundle."
    )
