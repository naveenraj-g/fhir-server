from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRQuantity,
    FHIRReference,
)
from app.schemas.medication_dispense.response.codeable_concept import (
    PlainMedicationDispenseCodeableConcept,
)
from app.schemas.medication_dispense.response.dosage import (
    FHIRMedicationDispenseDosage,
    PlainMedicationDispenseDosage,
)
from app.schemas.medication_dispense.response.identifier import (
    PlainMedicationDispenseIdentifier,
)
from app.schemas.medication_dispense.response.note import (
    FHIRAnnotation,
    PlainMedicationDispenseNote,
)
from app.schemas.medication_dispense.response.performer import (
    FHIRMedicationDispensePerformer,
    PlainMedicationDispensePerformer,
)
from app.schemas.medication_dispense.response.quantity import (
    PlainMedicationDispenseQuantity,
)
from app.schemas.medication_dispense.response.reference import (
    PlainMedicationDispenseReference,
)
from app.schemas.medication_dispense.response.substitution import (
    FHIRMedicationDispenseSubstitution,
    PlainMedicationDispenseSubstitution,
)


class FHIRMedicationDispenseSchema(BaseModel):
    """FHIR R4 MedicationDispense resource schema."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["MedicationDispense"] = "MedicationDispense"
    id: str = Field(..., description="Logical id of this artifact.")
    meta: FHIRMeta | None = Field(None, description="Metadata about the resource.")
    extension: list[dict] | None = Field(None, description="Additional content defined by implementations.")
    identifier: list[FHIRIdentifier] | None = Field(None, description="External identifier.")
    partOf: list[FHIRReference] | None = Field(None, description="Event that dispense is part of.")
    status: str = Field(..., description="preparation | in-progress | cancelled | on-hold | completed | entered-in-error | stopped | declined | unknown.")
    statusReasonCodeableConcept: FHIRCodeableConcept | None = Field(None, description="Why a dispense was not performed.")
    statusReasonReference: FHIRReference | None = Field(None, description="Why a dispense was not performed.")
    category: FHIRCodeableConcept | None = Field(None, description="Type of medication dispense.")
    medicationCodeableConcept: FHIRCodeableConcept | None = Field(None, description="What medication was supplied.")
    medicationReference: FHIRReference | None = Field(None, description="What medication was supplied.")
    subject: FHIRReference | None = Field(None, description="Who the dispense is for.")
    context: FHIRReference | None = Field(None, description="Encounter / Episode associated with event.")
    supportingInformation: list[FHIRReference] | None = Field(None, description="Information that supports the dispense.")
    performer: list[FHIRMedicationDispensePerformer] | None = Field(None, description="Who performed event.")
    location: FHIRReference | None = Field(None, description="Where the dispense occurred.")
    authorizingPrescription: list[FHIRReference] | None = Field(None, description="Medication order that authorizes the dispense.")
    type: FHIRCodeableConcept | None = Field(None, description="Trial fill, partial fill, emergency fill, etc.")
    quantity: FHIRQuantity | None = Field(None, description="Amount dispensed.")
    daysSupply: FHIRQuantity | None = Field(None, description="Amount of medication expressed as a timing amount.")
    whenPrepared: str | None = Field(None, description="When product was packaged and reviewed.")
    whenHandedOver: str | None = Field(None, description="When product was given out.")
    destination: FHIRReference | None = Field(None, description="Where the medication was sent.")
    receiver: list[FHIRReference] | None = Field(None, description="Who collected the medication.")
    note: list[FHIRAnnotation] | None = Field(None, description="Information about the dispense.")
    dosageInstruction: list[FHIRMedicationDispenseDosage] | None = Field(None, description="How the medication is to be used by the patient.")
    substitution: FHIRMedicationDispenseSubstitution | None = Field(None, description="Deals with substitution of one medicine for another.")
    detectedIssue: list[FHIRReference] | None = Field(None, description="Clinical issue with action.")
    eventHistory: list[FHIRReference] | None = Field(None, description="A list of relevant histories for the dispense.")


class PlainMedicationDispenseResponse(BaseModel):
    """Plain (snake_case) MedicationDispense response schema."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID (public medication_dispense_id).")
    extension: list[dict] | None = None
    identifier: list[PlainMedicationDispenseIdentifier] | None = None
    part_of: list[PlainMedicationDispenseReference] | None = None
    status: str
    status_reason_codeable_concept: PlainMedicationDispenseCodeableConcept | None = None
    status_reason_reference: PlainMedicationDispenseReference | None = None
    category: PlainMedicationDispenseCodeableConcept | None = None
    medication_codeable_concept: PlainMedicationDispenseCodeableConcept | None = None
    medication_reference: PlainMedicationDispenseReference | None = None
    subject: PlainMedicationDispenseReference | None = None
    context: PlainMedicationDispenseReference | None = None
    supporting_information: list[PlainMedicationDispenseReference] | None = None
    performer: list[PlainMedicationDispensePerformer] | None = None
    location: PlainMedicationDispenseReference | None = None
    authorizing_prescription: list[PlainMedicationDispenseReference] | None = None
    type: PlainMedicationDispenseCodeableConcept | None = None
    quantity: PlainMedicationDispenseQuantity | None = None
    days_supply: PlainMedicationDispenseQuantity | None = None
    when_prepared: datetime | None = None
    when_handed_over: datetime | None = None
    destination: PlainMedicationDispenseReference | None = None
    receiver: list[PlainMedicationDispenseReference] | None = None
    note: list[PlainMedicationDispenseNote] | None = None
    dosage_instruction: list[PlainMedicationDispenseDosage] | None = None
    substitution: PlainMedicationDispenseSubstitution | None = None
    detected_issue: list[PlainMedicationDispenseReference] | None = None
    event_history: list[PlainMedicationDispenseReference] | None = None


class PaginatedMedicationDispenseResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    limit: int
    offset: int
    data: list[PlainMedicationDispenseResponse]


class FHIRMedicationDispenseBundleEntry(BaseModel):
    model_config = ConfigDict(extra="allow")

    fullUrl: str | None = None
    resource: FHIRMedicationDispenseSchema


class FHIRMedicationDispenseBundle(BaseModel):
    model_config = ConfigDict(extra="allow")

    resourceType: Literal["Bundle"] = "Bundle"
    type: Literal["searchset"] = "searchset"
    total: int
    entry: list[FHIRMedicationDispenseBundleEntry] = []
