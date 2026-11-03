from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRQuantity,
    FHIRReference,
    PlainCodingRow,
)


class PlainMeasureReportGroupStratifierStratumComponent(BaseModel):
    """Plain representation of MeasureReport stratum component."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    code_text: str | None = None
    code_codings: list[PlainCodingRow] | None = None
    value_text: str | None = None
    value_codings: list[PlainCodingRow] | None = None


class PlainMeasureReportGroupStratifierStratumPopulation(BaseModel):
    """Plain representation of MeasureReport stratum population."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    code_text: str | None = None
    code_codings: list[PlainCodingRow] | None = None
    count: int | None = None
    subject_results: str | None = None
    subject_results_display: str | None = None


class PlainMeasureReportGroupStratifierStratum(BaseModel):
    """Plain representation of MeasureReport stratum."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    value_text: str | None = None
    value_codings: list[PlainCodingRow] | None = None
    component: list[PlainMeasureReportGroupStratifierStratumComponent] | None = None
    population: list[PlainMeasureReportGroupStratifierStratumPopulation] | None = None
    measure_score_value: float | None = None
    measure_score_comparator: str | None = None
    measure_score_unit: str | None = None
    measure_score_system: str | None = None
    measure_score_code: str | None = None


class PlainMeasureReportGroupStratifierCode(BaseModel):
    """Plain representation of MeasureReport stratifier code."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    text: str | None = None
    codings: list[PlainCodingRow] | None = None


class PlainMeasureReportGroupStratifier(BaseModel):
    """Plain representation of MeasureReport stratifier."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    code: list[PlainMeasureReportGroupStratifierCode] | None = None
    stratum: list[PlainMeasureReportGroupStratifierStratum] | None = None


class PlainMeasureReportGroupPopulation(BaseModel):
    """Plain representation of MeasureReport group population."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    code_text: str | None = None
    code_codings: list[PlainCodingRow] | None = None
    count: int | None = None
    subject_results: str | None = None
    subject_results_display: str | None = None


class PlainMeasureReportGroup(BaseModel):
    """Plain representation of MeasureReport group."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal row ID.")
    code_text: str | None = None
    code_codings: list[PlainCodingRow] | None = None
    population: list[PlainMeasureReportGroupPopulation] | None = None
    measure_score_value: float | None = None
    measure_score_comparator: str | None = None
    measure_score_unit: str | None = None
    measure_score_system: str | None = None
    measure_score_code: str | None = None
    stratifier: list[PlainMeasureReportGroupStratifier] | None = None


# FHIR representations
class FHIRMeasureReportGroupPopulation(BaseModel):
    """FHIR R4 MeasureReport.group.population."""

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    code: FHIRCodeableConcept | None = None
    count: int | None = None
    subjectResults: FHIRReference | None = None


class FHIRMeasureReportGroupStratifierStratumComponent(BaseModel):
    """FHIR R4 MeasureReport.group.stratifier.stratum.component."""

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    code: FHIRCodeableConcept | None = None
    value: FHIRCodeableConcept | None = None


class FHIRMeasureReportGroupStratifierStratumPopulation(BaseModel):
    """FHIR R4 MeasureReport.group.stratifier.stratum.population."""

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    code: FHIRCodeableConcept | None = None
    count: int | None = None
    subjectResults: FHIRReference | None = None


class FHIRMeasureReportGroupStratifierStratum(BaseModel):
    """FHIR R4 MeasureReport.group.stratifier.stratum."""

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    value: FHIRCodeableConcept | None = None
    component: list[FHIRMeasureReportGroupStratifierStratumComponent] | None = None
    population: list[FHIRMeasureReportGroupStratifierStratumPopulation] | None = None
    measureScore: FHIRQuantity | None = None


class FHIRMeasureReportGroupStratifier(BaseModel):
    """FHIR R4 MeasureReport.group.stratifier."""

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    code: list[FHIRCodeableConcept] | None = None
    stratum: list[FHIRMeasureReportGroupStratifierStratum] | None = None


class FHIRMeasureReportGroup(BaseModel):
    """FHIR R4 MeasureReport.group."""

    model_config = ConfigDict(extra="allow")

    id: str | None = None
    code: FHIRCodeableConcept | None = None
    population: list[FHIRMeasureReportGroupPopulation] | None = None
    measureScore: FHIRQuantity | None = None
    stratifier: list[FHIRMeasureReportGroupStratifier] | None = None
