from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRQuantity,
    FHIRReference,
)
from app.schemas.immunization.response.codeable_concept import (
    PlainImmunizationCodeableConcept,
)
from app.schemas.immunization.response.education import (
    FHIRImmunizationEducation,
    PlainImmunizationEducation,
)
from app.schemas.immunization.response.identifier import (
    PlainImmunizationIdentifier,
)
from app.schemas.immunization.response.note import (
    PlainImmunizationNote,
)
from app.schemas.immunization.response.performer import (
    FHIRImmunizationPerformer,
    PlainImmunizationPerformer,
)
from app.schemas.immunization.response.protocol_applied import (
    FHIRImmunizationProtocolApplied,
    PlainImmunizationProtocolApplied,
)
from app.schemas.immunization.response.quantity import PlainSimpleQuantity
from app.schemas.immunization.response.reaction import (
    FHIRImmunizationReaction,
    PlainImmunizationReaction,
)
from app.schemas.immunization.response.reference import (
    PlainImmunizationReference,
)
from app.schemas.service_request.response.core import FHIRAnnotation


class FHIRImmunizationSchema(BaseModel):
    """FHIR R4 Immunization resource schema."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["Immunization"] = "Immunization"
    id: str = Field(..., description="Logical id of this artifact.")
    meta: FHIRMeta | None = Field(None, description="Metadata about the resource.")
    extension: list[dict] | None = Field(None, description="Additional content defined by implementations.")
    identifier: list[FHIRIdentifier] | None = Field(None, description="Business identifier.")
    status: str = Field(..., description="completed | entered-in-error | not-done.")
    statusReason: FHIRCodeableConcept | None = Field(None, description="Reason not done.")
    vaccineCode: FHIRCodeableConcept = Field(..., description="Vaccine product administered.")
    patient: FHIRReference = Field(..., description="Who was immunized.")
    encounter: FHIRReference | None = Field(None, description="Encounter immunization was part of.")
    occurrenceDateTime: str | None = Field(None, description="Vaccine administration date/time.")
    occurrenceString: str | None = Field(None, description="Vaccine administration date text.")
    recorded: str | None = Field(None, description="When the immunization was first captured in the record.")
    primarySource: bool | None = Field(None, description="Indicates context the data was recorded in.")
    reportOrigin: FHIRCodeableConcept | None = Field(None, description="Indicates the source of a secondarily reported record.")
    location: FHIRReference | None = Field(None, description="Where immunization occurred.")
    manufacturer: FHIRReference | None = Field(None, description="Vaccine manufacturer.")
    lotNumber: str | None = Field(None, description="Vaccine lot number.")
    expirationDate: str | None = Field(None, description="Vaccine expiration date.")
    site: FHIRCodeableConcept | None = Field(None, description="Body site where vaccine was administered.")
    route: FHIRCodeableConcept | None = Field(None, description="How vaccine entered body.")
    doseQuantity: FHIRQuantity | None = Field(None, description="Amount of vaccine administered.")
    performer: list[FHIRImmunizationPerformer] | None = Field(None, description="Who performed event.")
    note: list[FHIRAnnotation] | None = Field(None, description="Additional notes.")
    reasonCode: list[FHIRCodeableConcept] | None = Field(None, description="Why immunization occurred.")
    reasonReference: list[FHIRReference] | None = Field(None, description="Why immunization occurred.")
    isSubpotent: bool | None = Field(None, description="Dose potency.")
    subpotentReason: list[FHIRCodeableConcept] | None = Field(None, description="Reason for being subpotent.")
    education: list[FHIRImmunizationEducation] | None = Field(None, description="Educational material presented to person receiving vaccine.")
    programEligibility: list[FHIRCodeableConcept] | None = Field(None, description="Patient eligibility for a specific program.")
    fundingSource: FHIRCodeableConcept | None = Field(None, description="Funding source for the vaccine.")
    reaction: list[FHIRImmunizationReaction] | None = Field(None, description="Details of a reaction that follows immunization.")
    protocolApplied: list[FHIRImmunizationProtocolApplied] | None = Field(None, description="Protocol followed by the provider.")


class PlainImmunizationResponse(BaseModel):
    """Plain snake_case Immunization response."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Public numeric ID (starts at 330000).")
    status: str = Field(..., description="completed | entered-in-error | not-done.")
    status_reason: PlainImmunizationCodeableConcept | None = Field(None, description="Reason not done.")
    vaccine_code: PlainImmunizationCodeableConcept | None = Field(None, description="Vaccine product administered.")
    patient: PlainImmunizationReference = Field(..., description="Who was immunized.")
    encounter: PlainImmunizationReference | None = Field(None, description="Encounter immunization was part of.")
    occurrence_date_time: datetime | None = Field(None, description="Vaccine administration date/time.")
    occurrence_string: str | None = Field(None, description="Vaccine administration date text.")
    recorded: datetime | None = Field(None, description="When the immunization was first captured in the record.")
    primary_source: bool | None = Field(None, description="Indicates context the data was recorded in.")
    report_origin: PlainImmunizationCodeableConcept | None = Field(None, description="Indicates the source of a secondarily reported record.")
    location: PlainImmunizationReference | None = Field(None, description="Where immunization occurred.")
    manufacturer: PlainImmunizationReference | None = Field(None, description="Vaccine manufacturer.")
    lot_number: str | None = Field(None, description="Vaccine lot number.")
    expiration_date: date | None = Field(None, description="Vaccine expiration date.")
    site: PlainImmunizationCodeableConcept | None = Field(None, description="Body site where vaccine was administered.")
    route: PlainImmunizationCodeableConcept | None = Field(None, description="How vaccine entered body.")
    dose_quantity: PlainSimpleQuantity | None = Field(None, description="Amount of vaccine administered.")
    is_subpotent: bool | None = Field(None, description="Dose potency.")
    funding_source: PlainImmunizationCodeableConcept | None = Field(None, description="Funding source for the vaccine.")

    identifier: list[PlainImmunizationIdentifier] | None = Field(None, description="Business identifier.")
    performer: list[PlainImmunizationPerformer] | None = Field(None, description="Who performed event.")
    note: list[PlainImmunizationNote] | None = Field(None, description="Additional notes.")
    reason_code: list[PlainImmunizationCodeableConcept] | None = Field(None, description="Why immunization occurred.")
    reason_reference: list[PlainImmunizationReference] | None = Field(None, description="Why immunization occurred.")
    subpotent_reason: list[PlainImmunizationCodeableConcept] | None = Field(None, description="Reason for being subpotent.")
    education: list[PlainImmunizationEducation] | None = Field(None, description="Educational material presented to person receiving vaccine.")
    program_eligibility: list[PlainImmunizationCodeableConcept] | None = Field(None, description="Patient eligibility for a specific program.")
    reaction: list[PlainImmunizationReaction] | None = Field(None, description="Details of a reaction that follows immunization.")
    protocol_applied: list[PlainImmunizationProtocolApplied] | None = Field(None, description="Protocol followed by the provider.")

    # Audit fields
    tenant_id: str | None = Field(None, description="Tenant organization ID.")
    created_by: str | None = Field(None, description="User who created the record.")
    updated_by: str | None = Field(None, description="User who last updated the record.")
    created_at: datetime | None = Field(None, description="Record creation timestamp.")
    updated_at: datetime | None = Field(None, description="Record update timestamp.")


class FHIRImmunizationBundleEntry(BaseModel):
    model_config = ConfigDict(extra="allow")

    fullUrl: str = Field(..., description="Full URL of the resource.")
    resource: FHIRImmunizationSchema = Field(..., description="The Immunization resource.")


class FHIRImmunizationBundle(BaseModel):
    model_config = ConfigDict(extra="allow")

    resourceType: Literal["Bundle"] = "Bundle"
    type: str = "searchset"
    total: int = Field(..., description="Total number of matches.")
    entry: list[FHIRImmunizationBundleEntry] = Field(default_factory=list, description="Entry in the bundle.")


class PaginatedImmunizationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int = Field(..., description="Total number of records matching the query.")
    limit: int = Field(..., description="Maximum number of records returned.")
    offset: int = Field(..., description="Offset of the first record returned.")
    data: list[PlainImmunizationResponse] = Field(..., description="List of immunization records.")
