from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRReference,
    PlainCodingRow,
)

from .identifier import PlainObservationDefinitionIdentifier
from .qualified_interval import (
    FHIRQualifiedInterval,
    PlainObservationDefinitionQualifiedInterval,
)


class FHIRObservationDefinitionQuantitativeDetails(BaseModel):
    """ObservationDefinition.quantitativeDetails FHIR representation."""

    model_config = ConfigDict(extra="allow")

    customaryUnit: FHIRCodeableConcept | None = Field(
        None, description="Customary unit used to report quantitative results."
    )
    unit: FHIRCodeableConcept | None = Field(
        None, description="SI unit used to report quantitative results."
    )
    conversionFactor: float | None = Field(
        None, description="Factor for converting value expressed with SI unit to customary unit."
    )
    decimalPrecision: int | None = Field(
        None, description="Number of digits after decimal separator."
    )


class PlainObservationDefinitionQuantitativeDetails(BaseModel):
    """Plain quantitative details representation."""

    model_config = ConfigDict(extra="allow")

    customary_unit_text: str | None = Field(None, description="Customary unit text.")
    customary_unit_codings: list[PlainCodingRow] | None = Field(None, description="Customary unit codings.")
    unit_text: str | None = Field(None, description="Unit text.")
    unit_codings: list[PlainCodingRow] | None = Field(None, description="Unit codings.")
    conversion_factor: float | None = Field(None, description="Conversion factor.")
    decimal_precision: int | None = Field(None, description="Decimal precision.")


class PlainObservationDefinitionCategory(BaseModel):
    """Plain category representation."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal DB ID.")
    text: str | None = Field(None, description="Category text.")
    codings: list[PlainCodingRow] | None = Field(None, description="Category codings.")


class PlainObservationDefinitionCode(BaseModel):
    """Plain code representation."""

    model_config = ConfigDict(extra="allow")

    text: str | None = Field(None, description="Code text.")
    codings: list[PlainCodingRow] | None = Field(None, description="Code codings.")


class PlainObservationDefinitionMethod(BaseModel):
    """Plain method representation."""

    model_config = ConfigDict(extra="allow")

    text: str | None = Field(None, description="Method text.")
    codings: list[PlainCodingRow] | None = Field(None, description="Method codings.")


class FHIRObservationDefinitionSchema(BaseModel):
    """FHIR R4 ObservationDefinition resource schema."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["ObservationDefinition"] = "ObservationDefinition"
    id: str = Field(..., description="Logical ID of this artifact.")
    meta: FHIRMeta | None = Field(None, description="Metadata about the resource.")
    category: list[FHIRCodeableConcept] | None = Field(
        None, description="A code that classifies the general type of observation."
    )
    code: FHIRCodeableConcept = Field(
        ..., description="Describes what will be observed (name/code)."
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Unique identifier for this artifact."
    )
    permittedDataType: list[str] | None = Field(
        None, description="Data types allowed for the value element."
    )
    multipleResultsAllowed: bool | None = Field(
        None, description="Multiple results allowed."
    )
    method: FHIRCodeableConcept | None = Field(
        None, description="Method or technique used."
    )
    preferredReportName: str | None = Field(
        None, description="Preferred report name."
    )
    quantitativeDetails: FHIRObservationDefinitionQuantitativeDetails | None = Field(
        None, description="Characteristics for quantitative results."
    )
    qualifiedInterval: list[FHIRQualifiedInterval] | None = Field(
        None, description="Ranges of results qualified by context."
    )
    validCodedValueSet: FHIRReference | None = Field(
        None, description="Valid coded results ValueSet reference."
    )
    normalCodedValueSet: FHIRReference | None = Field(
        None, description="Normal coded results ValueSet reference."
    )
    abnormalCodedValueSet: FHIRReference | None = Field(
        None, description="Abnormal coded results ValueSet reference."
    )
    criticalCodedValueSet: FHIRReference | None = Field(
        None, description="Critical coded results ValueSet reference."
    )
    extension: list[dict] | None = Field(None, description="FHIR extension list.")


class PlainObservationDefinitionResponse(BaseModel):
    """Plain (snake_case) ObservationDefinition response schema."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Public observation_definition_id identifier.")
    tenant_id: str = Field(..., description="Tenant organization ID.")
    code: PlainObservationDefinitionCode | None = Field(None, description="Observation code.")
    category: list[PlainObservationDefinitionCategory] | None = Field(None, description="Categories.")
    identifier: list[PlainObservationDefinitionIdentifier] | None = Field(None, description="Identifiers.")
    permitted_data_type: list[str] | None = Field(None, description="Permitted data types.")
    multiple_results_allowed: bool | None = Field(None, description="Multiple results allowed.")
    method: PlainObservationDefinitionMethod | None = Field(None, description="Observation method.")
    preferred_report_name: str | None = Field(None, description="Preferred report name.")
    quantitative_details: PlainObservationDefinitionQuantitativeDetails | None = Field(
        None, description="Quantitative details."
    )
    qualified_interval: list[PlainObservationDefinitionQualifiedInterval] | None = Field(
        None, description="Qualified intervals."
    )
    valid_coded_value_set: str | None = Field(None, description="Valid coded ValueSet reference.")
    valid_coded_value_set_display: str | None = Field(None, description="Valid coded ValueSet display.")
    normal_coded_value_set: str | None = Field(None, description="Normal coded ValueSet reference.")
    normal_coded_value_set_display: str | None = Field(None, description="Normal coded ValueSet display.")
    abnormal_coded_value_set: str | None = Field(None, description="Abnormal coded ValueSet reference.")
    abnormal_coded_value_set_display: str | None = Field(None, description="Abnormal coded ValueSet display.")
    critical_coded_value_set: str | None = Field(None, description="Critical coded ValueSet reference.")
    critical_coded_value_set_display: str | None = Field(None, description="Critical coded ValueSet display.")
    extension: list[dict] | None = Field(None, description="Extension list.")
    created_by: str = Field(..., description="Creator user ID.")
    updated_by: str | None = Field(None, description="Last updater user ID.")
    created_at: datetime = Field(..., description="Creation timestamp.")
    updated_at: datetime = Field(..., description="Last update timestamp.")


class PaginatedObservationDefinitionResponse(BaseModel):
    """Paginated plain ObservationDefinition list response."""

    model_config = ConfigDict(extra="allow")

    data: list[PlainObservationDefinitionResponse] = Field(..., description="List of observation definitions.")
    total: int | None = Field(None, description="Total matching records.")
    limit: int = Field(..., description="Page size.")
    offset: int = Field(..., description="Page offset.")


class FHIRObservationDefinitionBundleEntry(BaseModel):
    """Single entry in an ObservationDefinition FHIR Bundle."""

    model_config = ConfigDict(extra="allow")

    fullUrl: str | None = Field(None, description="Full URL for resource.")
    resource: FHIRObservationDefinitionSchema = Field(..., description="ObservationDefinition resource.")


class FHIRObservationDefinitionBundle(BaseModel):
    """FHIR R4 Bundle for ObservationDefinition resources."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["Bundle"] = "Bundle"
    type: Literal["searchset"] = "searchset"
    total: int | None = Field(None, description="Total matching records.")
    entry: list[FHIRObservationDefinitionBundleEntry] = Field(
        default_factory=list, description="Bundle entries."
    )
