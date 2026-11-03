from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
)
from app.schemas.medication_administration.response.codeable_concept import (
    PlainMedicationAdministrationCodeableConcept,
)
from app.schemas.medication_administration.response.dosage import (
    FHIRMedicationAdministrationDosage,
    PlainMedicationAdministrationDosage,
)
from app.schemas.medication_administration.response.identifier import (
    PlainMedicationAdministrationIdentifier,
)
from app.schemas.medication_administration.response.note import (
    FHIRAnnotation,
    PlainMedicationAdministrationNote,
)
from app.schemas.medication_administration.response.performer import (
    FHIRMedicationAdministrationPerformer,
    PlainMedicationAdministrationPerformer,
)
from app.schemas.medication_administration.response.reference import (
    PlainMedicationAdministrationReference,
)


class FHIRMedicationAdministrationSchema(BaseModel):
    """FHIR R4 MedicationAdministration resource schema."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["MedicationAdministration"] = "MedicationAdministration"
    id: str = Field(..., description="Logical id of this artifact.")
    meta: FHIRMeta | None = Field(None, description="Metadata about the resource.")
    extension: list[dict] | None = Field(None, description="Additional content defined by implementations.")
    identifier: list[FHIRIdentifier] | None = Field(None, description="External identifier.")
    instantiates: list[str] | None = Field(None, description="Instantiates protocol or definition.")
    partOf: list[FHIRReference] | None = Field(None, description="Part of referenced event.")
    status: str = Field(..., description="in-progress | not-done | on-hold | completed | entered-in-error | stopped | unknown.")
    statusReason: list[FHIRCodeableConcept] | None = Field(None, description="Reason administration not performed.")
    category: FHIRCodeableConcept | None = Field(None, description="Type of medication administration.")
    medicationCodeableConcept: FHIRCodeableConcept | None = Field(None, description="What was administered.")
    medicationReference: FHIRReference | None = Field(None, description="What was administered.")
    subject: FHIRReference = Field(..., description="Who received administration.")
    context: FHIRReference | None = Field(None, description="Encounter / Episode associated with administration.")
    supportingInformation: list[FHIRReference] | None = Field(None, description="Additional information supporting administration.")
    effectiveDateTime: str | None = Field(None, description="Start and end time of administration.")
    effectivePeriod: FHIRPeriod | None = Field(None, description="Start and end time of administration.")
    performer: list[FHIRMedicationAdministrationPerformer] | None = Field(None, description="Who or what performed the medication administration.")
    reasonCode: list[FHIRCodeableConcept] | None = Field(None, description="Reason administration performed.")
    reasonReference: list[FHIRReference] | None = Field(None, description="Condition or observation that supports why the medication was administered.")
    request: FHIRReference | None = Field(None, description="Request that this administration is performed for.")
    device: list[FHIRReference] | None = Field(None, description="Device used to administer.")
    note: list[FHIRAnnotation] | None = Field(None, description="Information about the administration.")
    dosage: FHIRMedicationAdministrationDosage | None = Field(None, description="Details of how medication was taken.")
    eventHistory: list[FHIRReference] | None = Field(None, description="A list of relevant histories for the administration.")


class PlainMedicationAdministrationResponse(BaseModel):
    """Plain (snake_case) MedicationAdministration response schema."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID (public medication_administration_id).")
    extension: list[dict] | None = None
    instantiates: list[str] | None = None
    part_of: list[PlainMedicationAdministrationReference] | None = None
    status: str
    status_reason: list[PlainMedicationAdministrationCodeableConcept] | None = None
    category: PlainMedicationAdministrationCodeableConcept | None = None
    medication_codeable_concept: PlainMedicationAdministrationCodeableConcept | None = None
    medication_reference: PlainMedicationAdministrationReference | None = None
    subject: PlainMedicationAdministrationReference
    context: PlainMedicationAdministrationReference | None = None
    supporting_information: list[PlainMedicationAdministrationReference] | None = None
    effective_date_time: datetime | None = None
    effective_period_start: datetime | None = None
    effective_period_end: datetime | None = None
    performer: list[PlainMedicationAdministrationPerformer] | None = None
    reason_code: list[PlainMedicationAdministrationCodeableConcept] | None = None
    reason_reference: list[PlainMedicationAdministrationReference] | None = None
    request: PlainMedicationAdministrationReference | None = None
    device: list[PlainMedicationAdministrationReference] | None = None
    note: list[PlainMedicationAdministrationNote] | None = None
    dosage: PlainMedicationAdministrationDosage | None = None
    event_history: list[PlainMedicationAdministrationReference] | None = None
    identifier: list[PlainMedicationAdministrationIdentifier] | None = None


class PaginatedMedicationAdministrationResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    total: int
    limit: int
    offset: int
    data: list[PlainMedicationAdministrationResponse]


class FHIRMedicationAdministrationBundleEntry(BaseModel):
    model_config = ConfigDict(extra="allow")

    fullUrl: str | None = None
    resource: FHIRMedicationAdministrationSchema


class FHIRMedicationAdministrationBundle(BaseModel):
    model_config = ConfigDict(extra="allow")

    resourceType: Literal["Bundle"] = "Bundle"
    type: Literal["searchset"] = "searchset"
    total: int
    entry: list[FHIRMedicationAdministrationBundleEntry] = []
