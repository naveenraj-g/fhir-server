import datetime as dt
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
    PlainCodingRow,
)
from app.schemas.measure_report.response.group import (
    FHIRMeasureReportGroup,
    PlainMeasureReportGroup,
)
from app.schemas.measure_report.response.identifier import PlainMeasureReportIdentifier


class PlainMeasureReportEvaluatedResource(BaseModel):
    """Plain representation of evaluatedResource."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    reference: str | None = None
    display: str | None = None


class FHIRMeasureReportSchema(BaseModel):
    """FHIR R4 MeasureReport resource schema."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["MeasureReport"] = "MeasureReport"
    id: str | None = None
    meta: FHIRMeta | None = None
    extension: list[dict[str, Any]] | None = None
    identifier: list[FHIRIdentifier] | None = None
    status: str = Field(..., description="complete | pending | error.")
    type: str = Field(
        ..., description="individual | subject-list | summary | data-collection."
    )
    measure: str = Field(..., description="What measure was calculated.")
    subject: FHIRReference | None = None
    date: str | None = None
    reporter: FHIRReference | None = None
    period: FHIRPeriod | None = None
    improvementNotation: FHIRCodeableConcept | None = None
    group: list[FHIRMeasureReportGroup] | None = None
    evaluatedResource: list[FHIRReference] | None = None


class PlainMeasureReportResponse(BaseModel):
    """Plain JSON representation of MeasureReport."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Public sequence measure_report_id.")
    status: str
    type: str
    measure: str
    subject: str | None = None
    subject_display: str | None = None
    date: dt.datetime | None = None
    reporter: str | None = None
    reporter_display: str | None = None
    period_start: dt.datetime | None = None
    period_end: dt.datetime | None = None
    improvement_notation_text: str | None = None
    improvement_notation_coding: list[PlainCodingRow] | None = None

    tenant_id: str
    created_by: str
    updated_by: str | None = None
    created_at: dt.datetime | None = None
    updated_at: dt.datetime | None = None

    identifier: list[PlainMeasureReportIdentifier] | None = None
    evaluated_resource: list[PlainMeasureReportEvaluatedResource] | None = None
    group: list[PlainMeasureReportGroup] | None = None


class PaginatedMeasureReportResponse(BaseModel):
    """Paginated plain response for MeasureReport."""

    model_config = ConfigDict(extra="allow")

    total: int
    limit: int
    offset: int
    data: list[PlainMeasureReportResponse]


class FHIRMeasureReportBundleEntry(BaseModel):
    """Entry in a FHIR MeasureReport Bundle."""

    model_config = ConfigDict(extra="allow")

    fullUrl: str | None = None
    resource: FHIRMeasureReportSchema


class FHIRMeasureReportBundle(BaseModel):
    """FHIR searchset Bundle for MeasureReport."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["Bundle"] = "Bundle"
    type: Literal["searchset"] = "searchset"
    total: int
    entry: list[FHIRMeasureReportBundleEntry] = []
