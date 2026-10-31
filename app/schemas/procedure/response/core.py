from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRRange,
    FHIRReference,
)
from app.schemas.procedure.response.codeable_concept import (
    PlainProcedureConcept,
    PlainProcedureSingleConcept,
)
from app.schemas.procedure.response.focal_device import (
    FHIRProcedureFocalDevice,
    PlainProcedureFocalDevice,
)
from app.schemas.procedure.response.identifier import PlainProcedureIdentifier
from app.schemas.procedure.response.note import PlainProcedureNote
from app.schemas.procedure.response.performer import (
    FHIRProcedurePerformer,
    PlainProcedurePerformer,
)


class FHIRProcedureSchema(BaseModel):
    """FHIR R4 Procedure resource schema."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["Procedure"] = "Procedure"
    id: str
    meta: FHIRMeta | None = None
    identifier: list[FHIRIdentifier] | None = None
    instantiatesCanonical: list[str] | None = None
    instantiatesUri: list[str] | None = None
    basedOn: list[FHIRReference] | None = None
    partOf: list[FHIRReference] | None = None
    status: str
    statusReason: FHIRCodeableConcept | None = None
    category: FHIRCodeableConcept | None = None
    code: FHIRCodeableConcept | None = None
    subject: FHIRReference
    encounter: FHIRReference | None = None
    performedDateTime: str | None = None
    performedPeriod: FHIRPeriod | None = None
    performedString: str | None = None
    performedAge: dict[str, Any] | None = None
    performedRange: FHIRRange | None = None
    recorder: FHIRReference | None = None
    asserter: FHIRReference | None = None
    performer: list[FHIRProcedurePerformer] | None = None
    location: FHIRReference | None = None
    reasonCode: list[FHIRCodeableConcept] | None = None
    reasonReference: list[FHIRReference] | None = None
    bodySite: list[FHIRCodeableConcept] | None = None
    outcome: FHIRCodeableConcept | None = None
    report: list[FHIRReference] | None = None
    complication: list[FHIRCodeableConcept] | None = None
    complicationDetail: list[FHIRReference] | None = None
    followUp: list[FHIRCodeableConcept] | None = None
    note: list[dict[str, Any]] | None = None
    focalDevice: list[FHIRProcedureFocalDevice] | None = None
    usedReference: list[FHIRReference] | None = None
    usedCode: list[FHIRCodeableConcept] | None = None
    extension: list[dict[str, Any]] | None = None


class PlainProcedureResponse(BaseModel):
    """Simplified snake_case Procedure response."""

    model_config = ConfigDict(extra="allow")

    id: int
    instantiates_canonical: list[str] | None = None
    instantiates_uri: list[str] | None = None
    based_on: list[str] | None = None
    part_of: list[str] | None = None
    status: str
    status_reason: PlainProcedureSingleConcept | None = None
    category: PlainProcedureSingleConcept | None = None
    code: PlainProcedureSingleConcept | None = None
    subject: str
    subject_display: str | None = None
    encounter: str | None = None
    encounter_display: str | None = None
    performed_date_time: datetime | None = None
    performed_period_start: datetime | None = None
    performed_period_end: datetime | None = None
    performed_string: str | None = None
    performed_age: dict[str, Any] | None = None
    performed_range: dict[str, Any] | None = None
    recorder: str | None = None
    recorder_display: str | None = None
    asserter: str | None = None
    asserter_display: str | None = None
    performer: list[PlainProcedurePerformer] | None = None
    location: str | None = None
    location_display: str | None = None
    reason_code: list[PlainProcedureConcept] | None = None
    reason_reference: list[str] | None = None
    body_site: list[PlainProcedureConcept] | None = None
    outcome: PlainProcedureSingleConcept | None = None
    report: list[str] | None = None
    complication: list[PlainProcedureConcept] | None = None
    complication_detail: list[str] | None = None
    follow_up: list[PlainProcedureConcept] | None = None
    note: list[PlainProcedureNote] | None = None
    focal_device: list[PlainProcedureFocalDevice] | None = None
    used_reference: list[str] | None = None
    used_code: list[PlainProcedureConcept] | None = None
    identifier: list[PlainProcedureIdentifier] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class PaginatedProcedureResponse(BaseModel):
    """Paginated list response for Procedure resources."""

    model_config = ConfigDict(extra="forbid")

    total: int | None = Field(None, description="Total number of matching resources.")
    limit: int = Field(..., description="Page size.")
    offset: int = Field(..., description="Page offset.")
    data: list[PlainProcedureResponse] = Field(..., description="List of Procedure resources.")


class FHIRProcedureBundleEntry(BaseModel):
    """Entry in a FHIR Procedure Bundle."""

    model_config = ConfigDict(extra="forbid")

    fullUrl: str | None = None
    resource: FHIRProcedureSchema


class FHIRProcedureBundle(BaseModel):
    """FHIR Bundle containing Procedure resources."""

    model_config = ConfigDict(extra="forbid")

    resourceType: Literal["Bundle"] = "Bundle"
    type: str = "searchset"
    total: int | None = None
    entry: list[FHIRProcedureBundleEntry] = []
