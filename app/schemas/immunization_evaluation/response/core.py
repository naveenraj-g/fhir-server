from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRReference,
)
from app.schemas.immunization_evaluation.response.codeable_concept import (
    PlainImmunizationEvaluationCodeableConcept,
)
from app.schemas.immunization_evaluation.response.identifier import (
    PlainImmunizationEvaluationIdentifier,
)
from app.schemas.immunization_evaluation.response.reference import (
    PlainImmunizationEvaluationReference,
)
from app.schemas.immunization_evaluation.response.sub_resources import (
    PlainImmunizationEvaluationDoseStatusReason,
)


class FHIRImmunizationEvaluationSchema(BaseModel):
    """FHIR R4 ImmunizationEvaluation resource schema."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["ImmunizationEvaluation"] = "ImmunizationEvaluation"
    id: str = Field(..., description="Logical id of this artifact.")
    meta: FHIRMeta | None = Field(None, description="Metadata about the resource.")
    extension: list[dict[str, Any]] | None = Field(
        None, description="Additional content defined by implementations."
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Business identifier for evaluation."
    )
    status: str = Field(..., description="completed | entered-in-error.")
    patient: FHIRReference = Field(
        ..., description="Who this evaluation is for (Reference(Patient))."
    )
    date: str | None = Field(None, description="Date evaluation was performed.")
    authority: FHIRReference | None = Field(
        None, description="Who is responsible for protocol (Reference(Organization))."
    )
    targetDisease: FHIRCodeableConcept = Field(
        ..., description="Evaluation target disease."
    )
    immunizationEvent: FHIRReference = Field(
        ..., description="Immunization event being evaluated (Reference(Immunization))."
    )
    doseStatus: FHIRCodeableConcept = Field(
        ..., description="Valid | notvalid status."
    )
    doseStatusReason: list[FHIRCodeableConcept] | None = Field(
        None, description="Reason for dose status."
    )
    description: str | None = Field(
        None, description="Evaluation notes or outcome description."
    )
    series: str | None = Field(None, description="Name of vaccine series.")
    doseNumberPositiveInt: int | None = Field(
        None, description="Dose number within series (positive int)."
    )
    doseNumberString: str | None = Field(
        None, description="Dose number within series (string)."
    )
    seriesDosesPositiveInt: int | None = Field(
        None, description="Recommended number of doses for series (positive int)."
    )
    seriesDosesString: str | None = Field(
        None, description="Recommended number of doses for series (string)."
    )


class PlainImmunizationEvaluationResponse(BaseModel):
    """Plain snake_case ImmunizationEvaluation response schema."""

    model_config = ConfigDict(extra="forbid")

    id: int = Field(..., description="Public sequence identifier.")
    status: str = Field(..., description="Evaluation status.")
    patient: PlainImmunizationEvaluationReference = Field(
        ..., description="Who this evaluation is for."
    )
    date: datetime | None = Field(None, description="Date evaluation was performed.")
    authority: PlainImmunizationEvaluationReference | None = Field(
        None, description="Who is responsible for protocol."
    )
    target_disease: PlainImmunizationEvaluationCodeableConcept = Field(
        ..., description="Evaluation target disease."
    )
    immunization_event: PlainImmunizationEvaluationReference = Field(
        ..., description="Immunization event being evaluated."
    )
    dose_status: PlainImmunizationEvaluationCodeableConcept = Field(
        ..., description="Valid | notvalid status."
    )
    dose_status_reason: list[PlainImmunizationEvaluationDoseStatusReason] | None = Field(
        None, description="Reason for dose status."
    )
    description: str | None = Field(
        None, description="Evaluation notes or outcome description."
    )
    series: str | None = Field(None, description="Name of vaccine series.")
    dose_number_positive_int: int | None = Field(
        None, description="Dose number within series (positive int)."
    )
    dose_number_string: str | None = Field(
        None, description="Dose number within series (string)."
    )
    series_doses_positive_int: int | None = Field(
        None, description="Recommended number of doses for series (positive int)."
    )
    series_doses_string: str | None = Field(
        None, description="Recommended number of doses for series (string)."
    )
    identifier: list[PlainImmunizationEvaluationIdentifier] | None = Field(
        None, description="Business identifiers."
    )
    extension: list[dict[str, Any]] | None = Field(
        None, description="FHIR DomainResource extensions."
    )
    created_at: datetime | None = Field(None, description="Record creation timestamp.")
    updated_at: datetime | None = Field(None, description="Record last update timestamp.")
    created_by: str = Field(..., description="Actor who created record.")
    updated_by: str | None = Field(None, description="Actor who last updated record.")


class PaginatedImmunizationEvaluationResponse(BaseModel):
    """Paginated plain snake_case ImmunizationEvaluation response."""

    model_config = ConfigDict(extra="forbid")

    total: int = Field(..., description="Total number of matching records.")
    limit: int = Field(..., description="Page size limit.")
    offset: int = Field(..., description="Page offset.")
    data: list[PlainImmunizationEvaluationResponse] = Field(
        ..., description="List of matching ImmunizationEvaluation records."
    )


class FHIRImmunizationEvaluationBundleEntry(BaseModel):
    """Entry in a FHIR ImmunizationEvaluation searchset Bundle."""

    model_config = ConfigDict(extra="forbid")

    fullUrl: str = Field(..., description="Full URL for the resource.")
    resource: FHIRImmunizationEvaluationSchema = Field(
        ..., description="ImmunizationEvaluation resource."
    )


class FHIRImmunizationEvaluationBundle(BaseModel):
    """FHIR R4 searchset Bundle for ImmunizationEvaluation."""

    model_config = ConfigDict(extra="forbid")

    resourceType: Literal["Bundle"] = "Bundle"
    type: Literal["searchset"] = "searchset"
    total: int = Field(..., description="Total number of matches.")
    entry: list[FHIRImmunizationEvaluationBundleEntry] = Field(
        default_factory=list, description="Matched resources."
    )
