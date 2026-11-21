from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRReference,
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRImmunizationRecommendationDateCriterion(BaseModel):
    code: FHIRCodeableConcept | None = Field(None, description="Type of date.")
    value: str | None = Field(None, description="Recommended date.")


class FHIRImmunizationRecommendationRecommendation(BaseModel):
    vaccineCode: list[FHIRCodeableConcept] | None = Field(None, description="Vaccine or vaccine group the recommendation applies to.")
    targetDisease: FHIRCodeableConcept | None = Field(None, description="Disease to be immunized against.")
    contraindicatedVaccineCode: list[FHIRCodeableConcept] | None = Field(None, description="Vaccine which is contraindicated to fulfill the recommendation.")
    forecastStatus: FHIRCodeableConcept | None = Field(None, description="Vaccine recommendation status.")
    forecastReason: list[FHIRCodeableConcept] | None = Field(None, description="Vaccine administration status reason.")
    dateCriterion: list[FHIRImmunizationRecommendationDateCriterion] | None = Field(None, description="Dates governing the proposed immunization.")
    description: str | None = Field(None, description="Protocol details.")
    series: str | None = Field(None, description="Name of the vaccination series.")
    doseNumberPositiveInt: int | None = Field(None, description="Recommended dose number within the series.")
    doseNumberString: str | None = Field(None, description="Recommended dose number within the series (string).")
    seriesDosesPositiveInt: int | None = Field(None, description="Recommended number of doses for immunity.")
    seriesDosesString: str | None = Field(None, description="Recommended number of doses for immunity (string).")
    supportingImmunization: list[FHIRReference] | None = Field(None, description="Past immunizations supporting the recommendation.")
    supportingPatientInformation: list[FHIRReference] | None = Field(None, description="Patient observations supporting the recommendation.")


class FHIRImmunizationRecommendationSchema(BaseModel):
    resourceType: str = Field("ImmunizationRecommendation", description="Always 'ImmunizationRecommendation'.")
    id: str = Field(..., description="Public immunization_recommendation_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata — lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries."
    )
    identifier: list[FHIRIdentifier] | None = Field(None, description="Business identifier.")
    patient: FHIRReference | None = Field(None, description="Who this profile is for.")
    date: str | None = Field(None, description="Date recommendation(s) created.")
    authority: FHIRReference | None = Field(None, description="Who is responsible for the protocol.")
    recommendation: list[FHIRImmunizationRecommendationRecommendation] | None = Field(
        None, description="Vaccine administration recommendations."
    )


class FHIRImmunizationRecommendationBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRImmunizationRecommendationSchema | dict = Field(
        ...,
        description="An ImmunizationRecommendation (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included Patient / Immunization / Condition / ... (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRImmunizationRecommendationBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRImmunizationRecommendationBundleEntry] | None = None
