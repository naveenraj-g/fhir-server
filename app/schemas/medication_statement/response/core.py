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
from app.schemas.medication_request.response.core import FHIRDosage
from app.schemas.medication_statement.response.codeable_concept import (
    PlainMedicationStatementCodeableConcept,
)
from app.schemas.medication_statement.response.dosage import (
    PlainMedicationStatementDosage,
)
from app.schemas.medication_statement.response.identifier import (
    PlainMedicationStatementIdentifier,
)
from app.schemas.medication_statement.response.note import (
    PlainMedicationStatementNote,
)
from app.schemas.medication_statement.response.reason_code import (
    PlainMedicationStatementReasonCode,
)
from app.schemas.medication_statement.response.reference import (
    PlainMedicationStatementBasedOn,
    PlainMedicationStatementContext,
    PlainMedicationStatementDerivedFrom,
    PlainMedicationStatementInformationSource,
    PlainMedicationStatementMedicationReference,
    PlainMedicationStatementPartOf,
    PlainMedicationStatementReasonReference,
    PlainMedicationStatementSubject,
)
from app.schemas.medication_statement.response.status_reason import (
    PlainMedicationStatementStatusReason,
)
from app.schemas.service_request.response.core import FHIRAnnotation


class FHIRMedicationStatementSchema(BaseModel):
    """FHIR R4 MedicationStatement resource schema."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["MedicationStatement"] = "MedicationStatement"
    id: str = Field(..., description="Logical id of this artifact.")
    meta: FHIRMeta | None = Field(None, description="Metadata about the resource.")
    extension: list[dict] | None = Field(None, description="Additional content defined by implementations.")
    identifier: list[FHIRIdentifier] | None = Field(None, description="External identifier.")
    basedOn: list[FHIRReference] | None = Field(None, description="Fulfils plan, proposal or order.")
    partOf: list[FHIRReference] | None = Field(None, description="Part of referenced event.")
    status: str = Field(..., description="active | completed | entered-in-error | intended | stopped | on-hold | unknown | not-taken.")
    statusReason: list[FHIRCodeableConcept] | None = Field(None, description="Reason for current status.")
    category: FHIRCodeableConcept | None = Field(None, description="Type of medication statement.")
    medicationCodeableConcept: FHIRCodeableConcept | None = Field(None, description="What medication was taken.")
    medicationReference: FHIRReference | None = Field(None, description="What medication was taken.")
    subject: FHIRReference = Field(..., description="Who is/was taking the medication.")
    context: FHIRReference | None = Field(None, description="Encounter / Episode associated with MedicationStatement.")
    effectiveDateTime: str | None = Field(None, description="The date/time or interval when the medication is/was/will be taken.")
    effectivePeriod: FHIRPeriod | None = Field(None, description="The date/time or interval when the medication is/was/will be taken.")
    dateAsserted: str | None = Field(None, description="When the statement was asserted/recorded.")
    informationSource: FHIRReference | None = Field(None, description="Person or organization that provided information about the medication.")
    derivedFrom: list[FHIRReference] | None = Field(None, description="Additional supporting information.")
    reasonCode: list[FHIRCodeableConcept] | None = Field(None, description="Reason for medication administration.")
    reasonReference: list[FHIRReference] | None = Field(None, description="Condition or observation that supports why the medication is being/was taken.")
    note: list[FHIRAnnotation] | None = Field(None, description="Further information about the statement.")
    dosage: list[FHIRDosage] | None = Field(None, description="Details of how medication is/was taken or should be taken.")


class PlainMedicationStatementResponse(BaseModel):
    """Plain (snake_case) MedicationStatement response schema."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID (public medication_statement_id).")
    extension: list[dict] | None = None
    identifier: list[PlainMedicationStatementIdentifier] | None = None
    based_on: list[PlainMedicationStatementBasedOn] | None = None
    part_of: list[PlainMedicationStatementPartOf] | None = None
    status: str
    status_reason: list[PlainMedicationStatementStatusReason] | None = None
    category: PlainMedicationStatementCodeableConcept | None = None
    medication_codeable_concept: PlainMedicationStatementCodeableConcept | None = None
    medication_reference: PlainMedicationStatementMedicationReference | None = None
    subject: PlainMedicationStatementSubject
    context: PlainMedicationStatementContext | None = None
    effective_date_time: datetime | None = None
    effective_period_start: datetime | None = None
    effective_period_end: datetime | None = None
    date_asserted: datetime | None = None
    information_source: PlainMedicationStatementInformationSource | None = None
    derived_from: list[PlainMedicationStatementDerivedFrom] | None = None
    reason_code: list[PlainMedicationStatementReasonCode] | None = None
    reason_reference: list[PlainMedicationStatementReasonReference] | None = None
    note: list[PlainMedicationStatementNote] | None = None
    dosage: list[PlainMedicationStatementDosage] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PaginatedMedicationStatementResponse(BaseModel):
    """Paginated plain (snake_case) response envelope."""

    model_config = ConfigDict(extra="allow")

    total: int
    limit: int
    offset: int
    data: list[PlainMedicationStatementResponse]


class FHIRMedicationStatementBundleEntry(BaseModel):
    model_config = ConfigDict(extra="allow")
    resource: FHIRMedicationStatementSchema


class FHIRMedicationStatementBundle(BaseModel):
    """FHIR R4 Bundle searchset response envelope."""

    model_config = ConfigDict(extra="allow")

    resourceType: str = "Bundle"
    type: str = "searchset"
    total: int
    link: list[dict] | None = None
    entry: list[FHIRMedicationStatementBundleEntry] | None = None
