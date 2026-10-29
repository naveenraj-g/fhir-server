from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
    PlainCodingRow,
)
from app.schemas.questionnaire.response import FHIRQuantity, FHIRRange
from app.schemas.service_request.response.core import FHIRAnnotation, FHIRRatio

from .codeable_concept import PlainObservationCode, PlainObservationCodeableConcept
from .component import PlainObservationComponent
from .identifier import PlainObservationIdentifier
from .note import PlainObservationNote
from .reference import (
    PlainObservationBasedOn,
    PlainObservationDerivedFrom,
    PlainObservationDevice,
    PlainObservationEncounter,
    PlainObservationFocus,
    PlainObservationHasMember,
    PlainObservationPartOf,
    PlainObservationPerformer,
    PlainObservationSpecimen,
    PlainObservationSubject,
)
from .reference_range import PlainObservationReferenceRange

# ── FHIR (camelCase) ────────────────────────────────────────────────────────


class FHIRSampledData(BaseModel):
    """FHIR R4 SampledData — https://www.hl7.org/fhir/R4/datatypes.html#SampledData
    This codebase's first use, via Observation.valueSampledData /
    component.valueSampledData."""

    origin: FHIRQuantity | None = None
    period: float | None = None
    factor: float | None = None
    lowerLimit: float | None = None
    upperLimit: float | None = None
    dimensions: int | None = None
    data: str | None = None


class FHIRObservationReferenceRange(BaseModel):
    """Observation.referenceRange (0..*) — reused identically for
    Observation.component.referenceRange."""

    low: FHIRQuantity | None = None
    high: FHIRQuantity | None = None
    type: FHIRCodeableConcept | None = None
    appliesTo: list[FHIRCodeableConcept] | None = None
    age: FHIRRange | None = None
    text: str | None = None


class FHIRObservationComponent(BaseModel):
    """Observation.component (0..*). `value[x]` reuses the identical
    11-variant choice shape as the root resource's own `value[x]`."""

    code: FHIRCodeableConcept
    valueQuantity: FHIRQuantity | None = None
    valueCodeableConcept: FHIRCodeableConcept | None = None
    valueString: str | None = None
    valueBoolean: bool | None = None
    valueInteger: int | None = None
    valueRange: FHIRRange | None = None
    valueRatio: FHIRRatio | None = None
    valueSampledData: FHIRSampledData | None = None
    valueTime: str | None = None
    valueDateTime: str | None = None
    valuePeriod: FHIRPeriod | None = None
    dataAbsentReason: FHIRCodeableConcept | None = None
    interpretation: list[FHIRCodeableConcept] | None = None
    referenceRange: list[FHIRObservationReferenceRange] | None = None


class FHIRObservationSchema(BaseModel):
    resourceType: str = Field("Observation", description="Always 'Observation'.")
    id: str = Field(..., description="Public observation_id as a string.")
    meta: FHIRMeta | None = Field(None, description="Infrastructure-maintained resource metadata. Response-only.")
    extension: list[dict] | None = Field(None, description="Resource-level FHIR extensions.")
    identifier: list[FHIRIdentifier] | None = Field(None, description="Business identifier for the observation.")
    basedOn: list[FHIRReference] | None = Field(None, description="Plan, proposal, or order fulfilled by this event.")
    partOf: list[FHIRReference] | None = Field(None, description="Larger event this observation is a component or step of.")
    status: str = Field(..., description="registered | preliminary | final | amended | corrected | cancelled | entered-in-error | unknown.")
    category: list[FHIRCodeableConcept] | None = Field(None, description="General type classification of the observation.")
    code: FHIRCodeableConcept = Field(..., description="What was observed (the observation 'name').")
    subject: FHIRReference | None = Field(None, description="Patient, Group, Device, or Location the observation is about.")
    focus: list[FHIRReference] | None = Field(None, description="Actual focus when not the subject of record.")
    encounter: FHIRReference | None = Field(None, description="Healthcare event during which the observation was made.")
    effectiveDateTime: str | None = Field(None, description="effective[x]: dateTime.")
    effectivePeriod: FHIRPeriod | None = Field(None, description="effective[x]: Period.")
    effectiveTiming: dict | None = Field(None, description="effective[x]: Timing, as a raw dict.")
    effectiveInstant: str | None = Field(None, description="effective[x]: instant.")
    issued: str | None = Field(None, description="When this version was made available to providers.")
    performer: list[FHIRReference] | None = Field(None, description="Who was responsible for asserting the value.")
    valueQuantity: FHIRQuantity | None = Field(None, description="value[x]: Quantity.")
    valueCodeableConcept: FHIRCodeableConcept | None = Field(None, description="value[x]: CodeableConcept.")
    valueString: str | None = Field(None, description="value[x]: string.")
    valueBoolean: bool | None = Field(None, description="value[x]: boolean.")
    valueInteger: int | None = Field(None, description="value[x]: integer.")
    valueRange: FHIRRange | None = Field(None, description="value[x]: Range.")
    valueRatio: FHIRRatio | None = Field(None, description="value[x]: Ratio.")
    valueSampledData: FHIRSampledData | None = Field(None, description="value[x]: SampledData.")
    valueTime: str | None = Field(None, description="value[x]: time.")
    valueDateTime: str | None = Field(None, description="value[x]: dateTime.")
    valuePeriod: FHIRPeriod | None = Field(None, description="value[x]: Period.")
    dataAbsentReason: FHIRCodeableConcept | None = Field(None, description="Why the value is missing.")
    interpretation: list[FHIRCodeableConcept] | None = Field(None, description="Categorical assessment, e.g. high, low, normal.")
    note: list[FHIRAnnotation] | None = Field(None, description="Comments about the observation or results.")
    bodySite: FHIRCodeableConcept | None = Field(None, description="Body site where the observation was made.")
    method: FHIRCodeableConcept | None = Field(None, description="Mechanism used to perform the observation.")
    specimen: FHIRReference | None = Field(None, description="Specimen used for the observation.")
    device: FHIRReference | None = Field(None, description="Device that generated the observation data.")
    referenceRange: list[FHIRObservationReferenceRange] | None = Field(None, description="Guidance for interpreting the value.")
    hasMember: list[FHIRReference] | None = Field(None, description="Member resources in a group observation.")
    derivedFrom: list[FHIRReference] | None = Field(None, description="Measurements this observation value is derived from.")
    component: list[FHIRObservationComponent] | None = Field(None, description="Component observations sharing the same attributes.")


class FHIRObservationBundleEntry(BaseModel):
    resource: FHIRObservationSchema


class FHIRObservationBundle(FHIRBundle):
    entry: list[FHIRObservationBundleEntry] | None = None


# ── Plain (snake_case) ───────────────────────────────────────────────────────


class PlainObservationResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Public observation_id.")
    extension: list[dict] | None = Field(None, description="Resource-level FHIR extensions.")
    identifier: list[PlainObservationIdentifier] | None = Field(None, description="Business identifier for the observation.")
    based_on: list[PlainObservationBasedOn] | None = Field(None, description="Plan, proposal, or order fulfilled by this event.")
    part_of: list[PlainObservationPartOf] | None = Field(None, description="Larger event this observation is a component or step of.")
    status: str | None = Field(None, description="registered | preliminary | final | amended | corrected | cancelled | entered-in-error | unknown.")
    category: list[PlainObservationCodeableConcept] | None = Field(None, description="General type classification of the observation.")
    code_codings: list[PlainCodingRow] | None = Field(None, description="Coding(s) for what was observed.")
    code_text: str | None = Field(None, description="Text for what was observed.")
    subject: PlainObservationSubject | None = Field(None, description="Patient, Group, Device, or Location the observation is about.")
    focus: list[PlainObservationFocus] | None = Field(None, description="Actual focus when not the subject of record.")
    encounter: PlainObservationEncounter | None = Field(None, description="Healthcare event during which the observation was made.")
    effective_date_time: str | None = Field(None, description="effective[x]: dateTime.")
    effective_period_start: str | None = Field(None, description="effective[x]: Period — start.")
    effective_period_end: str | None = Field(None, description="effective[x]: Period — end.")
    effective_timing: dict | None = Field(None, description="effective[x]: Timing, as a raw dict.")
    effective_instant: str | None = Field(None, description="effective[x]: instant.")
    issued: str | None = Field(None, description="When this version was made available to providers.")
    performer: list[PlainObservationPerformer] | None = Field(None, description="Who was responsible for asserting the value.")
    value_quantity_value: float | None = Field(None, description="value[x]: Quantity — numeric value.")
    value_quantity_comparator: str | None = Field(None, description="value[x]: Quantity — comparator.")
    value_quantity_unit: str | None = Field(None, description="value[x]: Quantity — unit.")
    value_quantity_system: str | None = Field(None, description="value[x]: Quantity — unit system.")
    value_quantity_code: str | None = Field(None, description="value[x]: Quantity — coded unit form.")
    value_codeable_concept: PlainObservationCode | None = Field(None, description="value[x]: CodeableConcept.")
    value_string: str | None = Field(None, description="value[x]: string.")
    value_boolean: bool | None = Field(None, description="value[x]: boolean.")
    value_integer: int | None = Field(None, description="value[x]: integer.")
    value_range_low_value: float | None = Field(None, description="value[x]: Range.low — numeric value.")
    value_range_low_unit: str | None = Field(None, description="value[x]: Range.low — unit.")
    value_range_low_system: str | None = Field(None, description="value[x]: Range.low — unit system.")
    value_range_low_code: str | None = Field(None, description="value[x]: Range.low — coded unit form.")
    value_range_high_value: float | None = Field(None, description="value[x]: Range.high — numeric value.")
    value_range_high_unit: str | None = Field(None, description="value[x]: Range.high — unit.")
    value_range_high_system: str | None = Field(None, description="value[x]: Range.high — unit system.")
    value_range_high_code: str | None = Field(None, description="value[x]: Range.high — coded unit form.")
    value_ratio_numerator_value: float | None = Field(None, description="value[x]: Ratio.numerator — numeric value.")
    value_ratio_numerator_comparator: str | None = Field(None, description="value[x]: Ratio.numerator — comparator.")
    value_ratio_numerator_unit: str | None = Field(None, description="value[x]: Ratio.numerator — unit.")
    value_ratio_numerator_system: str | None = Field(None, description="value[x]: Ratio.numerator — unit system.")
    value_ratio_numerator_code: str | None = Field(None, description="value[x]: Ratio.numerator — coded unit form.")
    value_ratio_denominator_value: float | None = Field(None, description="value[x]: Ratio.denominator — numeric value.")
    value_ratio_denominator_comparator: str | None = Field(None, description="value[x]: Ratio.denominator — comparator.")
    value_ratio_denominator_unit: str | None = Field(None, description="value[x]: Ratio.denominator — unit.")
    value_ratio_denominator_system: str | None = Field(None, description="value[x]: Ratio.denominator — unit system.")
    value_ratio_denominator_code: str | None = Field(None, description="value[x]: Ratio.denominator — coded unit form.")
    value_sampled_data_origin_value: float | None = Field(None, description="value[x]: SampledData.origin — numeric value.")
    value_sampled_data_origin_unit: str | None = Field(None, description="value[x]: SampledData.origin — unit.")
    value_sampled_data_origin_system: str | None = Field(None, description="value[x]: SampledData.origin — unit system.")
    value_sampled_data_origin_code: str | None = Field(None, description="value[x]: SampledData.origin — coded unit form.")
    value_sampled_data_period: float | None = Field(None, description="value[x]: SampledData.period.")
    value_sampled_data_factor: float | None = Field(None, description="value[x]: SampledData.factor.")
    value_sampled_data_lower_limit: float | None = Field(None, description="value[x]: SampledData.lowerLimit.")
    value_sampled_data_upper_limit: float | None = Field(None, description="value[x]: SampledData.upperLimit.")
    value_sampled_data_dimensions: int | None = Field(None, description="value[x]: SampledData.dimensions.")
    value_sampled_data_data: str | None = Field(None, description="value[x]: SampledData.data.")
    value_time: str | None = Field(None, description="value[x]: time.")
    value_date_time: str | None = Field(None, description="value[x]: dateTime.")
    value_period_start: str | None = Field(None, description="value[x]: Period — start.")
    value_period_end: str | None = Field(None, description="value[x]: Period — end.")
    data_absent_reason: PlainObservationCode | None = Field(None, description="Why the value is missing.")
    interpretation: list[PlainObservationCodeableConcept] | None = Field(None, description="Categorical assessment, e.g. high, low, normal.")
    note: list[PlainObservationNote] | None = Field(None, description="Comments about the observation or results.")
    body_site: PlainObservationCode | None = Field(None, description="Body site where the observation was made.")
    method: PlainObservationCode | None = Field(None, description="Mechanism used to perform the observation.")
    specimen: PlainObservationSpecimen | None = Field(None, description="Specimen used for the observation.")
    device: PlainObservationDevice | None = Field(None, description="Device that generated the observation data.")
    reference_range: list[PlainObservationReferenceRange] | None = Field(None, description="Guidance for interpreting the value.")
    has_member: list[PlainObservationHasMember] | None = Field(None, description="Member resources in a group observation.")
    derived_from: list[PlainObservationDerivedFrom] | None = Field(None, description="Measurements this observation value is derived from.")
    component: list[PlainObservationComponent] | None = Field(None, description="Component observations sharing the same attributes.")
    user_id: str | None = Field(None, description="Gateway-forwarded end-user ID — not a FHIR concept.")
    org_id: str | None = Field(None, description="Gateway-forwarded tenant/account ID — not a FHIR concept. Internally this column is named tenant_id.")
    created_at: str | None = Field(None, description="When this row was created.")
    updated_at: str | None = Field(None, description="When this row was last updated.")
    created_by: str | None = Field(None, description="Acting user who created this record.")
    updated_by: str | None = Field(None, description="Acting user who last updated this record.")


class PaginatedObservationResponse(BaseModel):
    total: int | None = Field(None, description="Total matching rows (null when total_mode=none).")
    limit: int = Field(..., description="Page size used for this response.")
    offset: int = Field(..., description="Number of rows skipped before this page.")
    data: list[PlainObservationResponse]
