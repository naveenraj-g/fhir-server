from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRQuantity,
    FHIRRange,
    FHIRReference,
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRObservationRatio(BaseModel):
    numerator: FHIRQuantity | None = Field(None, description="Numerator value.")
    denominator: FHIRQuantity | None = Field(None, description="Denominator value.")


class FHIRObservationAnnotation(BaseModel):
    authorReference: FHIRReference | None = Field(None, description="Individual responsible for the annotation.")
    authorString: str | None = Field(None, description="Individual responsible for the annotation, as plain text.")
    time: str | None = Field(None, description="When the annotation was made.")
    text: str | None = Field(None, description="The annotation text.")


class FHIRObservationReferenceRange(BaseModel):
    low: FHIRQuantity | None = Field(None, description="Low Range, if relevant.")
    high: FHIRQuantity | None = Field(None, description="High Range, if relevant.")
    type: FHIRCodeableConcept | None = Field(None, description="Reference range qualifier.")
    appliesTo: list[FHIRCodeableConcept] | None = Field(None, description="Reference range population.")
    age: FHIRRange | None = Field(None, description="Applicable age range, if relevant.")
    text: str | None = Field(None, description="Text based reference range in an observation.")


class FHIRObservationComponent(BaseModel):
    code: FHIRCodeableConcept | None = Field(None, description="Type of component observation (code / type).")
    valueQuantity: FHIRQuantity | None = Field(None, description="Actual component result (Quantity).")
    valueCodeableConcept: FHIRCodeableConcept | None = Field(None, description="Actual component result (CodeableConcept).")
    valueString: str | None = Field(None, description="Actual component result (string).")
    valueBoolean: bool | None = Field(None, description="Actual component result (boolean).")
    valueInteger: int | None = Field(None, description="Actual component result (integer).")
    valueRange: FHIRRange | None = Field(None, description="Actual component result (Range).")
    valueRatio: FHIRObservationRatio | None = Field(None, description="Actual component result (Ratio).")
    valueSampledData: dict | None = Field(None, description="Actual component result (SampledData).")
    valueTime: str | None = Field(None, description="Actual component result (time).")
    valueDateTime: str | None = Field(None, description="Actual component result (dateTime).")
    valuePeriod: FHIRPeriod | None = Field(None, description="Actual component result (Period).")
    dataAbsentReason: FHIRCodeableConcept | None = Field(None, description="Why the component result is missing.")
    interpretation: list[FHIRCodeableConcept] | None = Field(None, description="High, low, normal, etc.")
    referenceRange: list[FHIRObservationReferenceRange] | None = Field(None, description="Provides guide for interpretation of component result.")


class FHIRObservationSchema(BaseModel):
    resourceType: str = Field("Observation", description="Always 'Observation'.")
    id: str = Field(..., description="Public observation_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries."
    )
    identifier: list[FHIRIdentifier] | None = Field(None, description="Business Identifier for observation.")
    basedOn: list[FHIRReference] | None = Field(None, description="Fulfills plan, proposal or order.")
    partOf: list[FHIRReference] | None = Field(None, description="Part of referenced event.")
    status: str | None = Field(None, description="registered | preliminary | final | amended | corrected | cancelled | entered-in-error | unknown.")
    category: list[FHIRCodeableConcept] | None = Field(None, description="Classification of type of observation.")
    code: FHIRCodeableConcept | None = Field(None, description="Type of observation (code / type).")
    subject: FHIRReference | None = Field(None, description="Who and/or what the observation is about.")
    focus: list[FHIRReference] | None = Field(None, description="What the observation is about, when it is not about the subject of record.")
    encounter: FHIRReference | None = Field(None, description="Healthcare event during which this observation is made.")
    effectiveDateTime: str | None = Field(None, description="Clinically relevant time (dateTime).")
    effectivePeriod: FHIRPeriod | None = Field(None, description="Clinically relevant time (Period).")
    effectiveTiming: dict | None = Field(None, description="Clinically relevant time (Timing).")
    effectiveInstant: str | None = Field(None, description="Clinically relevant time (instant).")
    issued: str | None = Field(None, description="Date/Time this version was made available.")
    performer: list[FHIRReference] | None = Field(None, description="Who is responsible for the observation.")
    valueQuantity: FHIRQuantity | None = Field(None, description="Actual result (Quantity).")
    valueCodeableConcept: FHIRCodeableConcept | None = Field(None, description="Actual result (CodeableConcept).")
    valueString: str | None = Field(None, description="Actual result (string).")
    valueBoolean: bool | None = Field(None, description="Actual result (boolean).")
    valueInteger: int | None = Field(None, description="Actual result (integer).")
    valueRange: FHIRRange | None = Field(None, description="Actual result (Range).")
    valueRatio: FHIRObservationRatio | None = Field(None, description="Actual result (Ratio).")
    valueSampledData: dict | None = Field(None, description="Actual result (SampledData).")
    valueTime: str | None = Field(None, description="Actual result (time).")
    valueDateTime: str | None = Field(None, description="Actual result (dateTime).")
    valuePeriod: FHIRPeriod | None = Field(None, description="Actual result (Period).")
    dataAbsentReason: FHIRCodeableConcept | None = Field(None, description="Why the result is missing.")
    interpretation: list[FHIRCodeableConcept] | None = Field(None, description="High, low, normal, etc.")
    note: list[FHIRObservationAnnotation] | None = Field(None, description="Comments about the observation.")
    bodySite: FHIRCodeableConcept | None = Field(None, description="Observed body part.")
    method: FHIRCodeableConcept | None = Field(None, description="How it was done.")
    specimen: FHIRReference | None = Field(None, description="Specimen used for this observation.")
    device: FHIRReference | None = Field(None, description="(Measurement) Device.")
    referenceRange: list[FHIRObservationReferenceRange] | None = Field(None, description="Provides guide for interpretation.")
    hasMember: list[FHIRReference] | None = Field(None, description="Related resource that belongs to the Observation group.")
    derivedFrom: list[FHIRReference] | None = Field(None, description="Related measurements the observation is made from.")
    component: list[FHIRObservationComponent] | None = Field(None, description="Component results.")


class FHIRObservationBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRObservationSchema | dict = Field(
        ...,
        description="An Observation (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Patient / Encounter / Practitioner / PractitionerRole / Observation / ... (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRObservationBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRObservationBundleEntry] | None = None
