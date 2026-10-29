from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import ObservationQuantityComparator, ObservationStatus

from .codeable_concept import ObservationCodeableConceptInput
from .component import ObservationComponentInput
from .identifier import ObservationIdentifierInput
from .note import ObservationNoteInput
from .reference import (
    ObservationBasedOnInput,
    ObservationDerivedFromInput,
    ObservationDeviceInput,
    ObservationEncounterInput,
    ObservationFocusInput,
    ObservationHasMemberInput,
    ObservationPartOfInput,
    ObservationPerformerInput,
    ObservationSpecimenInput,
    ObservationSubjectInput,
)
from .reference_range import ObservationReferenceRangeInput

_EXAMPLE = {
    "user_id": "user-001",
    "status": "final",
    "code": {"coding": [{"system": "http://loinc.org", "code": "15074-8", "display": "Glucose [Moles/volume] in Blood"}]},
    "subject": {"reference": "Patient/10001"},
    "value_quantity_value": 6.3,
    "value_quantity_unit": "mmol/l",
    "value_quantity_system": "http://unitsofmeasure.org",
    "value_quantity_code": "mmol/L",
}


class ObservationCreateSchema(BaseModel):
    """Creates an Observation and any combination of its sub-resource
    lists atomically in one request. JWT/RBAC auth-rollout pattern —
    same as every other resource now: `org_id`/`created_by` come from
    the verified JWT (`actor.org_id`/`actor.sub`), not the request body
    — an org-less token is rejected outright (403). `user_id` is
    unaffected — still a plain, optional, gateway-forwarded field.

    `value[x]` (11 choice variants) is fully flattened, field-for-field
    identical to Observation.component's own `value[x]` (see
    ObservationComponentInput) — the service layer picks whichever
    group is actually populated when building the FHIR output."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": _EXAMPLE})

    user_id: str | None = Field(None, description="Gateway-forwarded ID of the end-user this record is scoped to.")

    extension: list[dict] | None = Field(None, description="Resource-level FHIR extensions.")

    identifier: list[ObservationIdentifierInput] | None = Field(None, description="Business identifier for the observation.")
    based_on: list[ObservationBasedOnInput] | None = Field(None, description="Plan, proposal, or order fulfilled by this event.")
    part_of: list[ObservationPartOfInput] | None = Field(None, description="Larger event this observation is a component or step of.")
    status: ObservationStatus = Field(..., description="registered | preliminary | final | amended | corrected | cancelled | entered-in-error | unknown.")
    category: list[ObservationCodeableConceptInput] | None = Field(None, description="General type classification of the observation.")
    code: ObservationCodeableConceptInput = Field(..., description="What was observed (the observation 'name').")
    subject: ObservationSubjectInput | None = Field(None, description="Patient, Group, Device, or Location the observation is about.")
    focus: list[ObservationFocusInput] | None = Field(None, description="Actual focus when not the subject of record.")
    encounter: ObservationEncounterInput | None = Field(None, description="Healthcare event during which the observation was made.")

    # effective[x]
    effective_date_time: datetime | None = Field(None, description="effective[x]: dateTime.")
    effective_period_start: datetime | None = Field(None, description="effective[x]: Period — start.")
    effective_period_end: datetime | None = Field(None, description="effective[x]: Period — end.")
    effective_timing: dict | None = Field(None, description="effective[x]: Timing, as a raw FHIR Timing dict.")
    effective_instant: datetime | None = Field(None, description="effective[x]: instant.")

    issued: datetime | None = Field(None, description="When this version was made available to providers.")
    performer: list[ObservationPerformerInput] | None = Field(None, description="Who was responsible for asserting the value.")

    # value[x] (0..1 choice: 11 variants)
    value_quantity_value: float | None = Field(None, description="value[x]: Quantity — numeric value.")
    value_quantity_comparator: ObservationQuantityComparator | None = Field(None, description="value[x]: Quantity — comparator.")
    value_quantity_unit: str | None = Field(None, description="value[x]: Quantity — unit.")
    value_quantity_system: str | None = Field(None, description="value[x]: Quantity — unit system.")
    value_quantity_code: str | None = Field(None, description="value[x]: Quantity — coded unit form.")
    value_codeable_concept: ObservationCodeableConceptInput | None = Field(None, description="value[x]: CodeableConcept.")
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
    value_ratio_numerator_comparator: ObservationQuantityComparator | None = Field(None, description="value[x]: Ratio.numerator — comparator.")
    value_ratio_numerator_unit: str | None = Field(None, description="value[x]: Ratio.numerator — unit.")
    value_ratio_numerator_system: str | None = Field(None, description="value[x]: Ratio.numerator — unit system.")
    value_ratio_numerator_code: str | None = Field(None, description="value[x]: Ratio.numerator — coded unit form.")
    value_ratio_denominator_value: float | None = Field(None, description="value[x]: Ratio.denominator — numeric value.")
    value_ratio_denominator_comparator: ObservationQuantityComparator | None = Field(None, description="value[x]: Ratio.denominator — comparator.")
    value_ratio_denominator_unit: str | None = Field(None, description="value[x]: Ratio.denominator — unit.")
    value_ratio_denominator_system: str | None = Field(None, description="value[x]: Ratio.denominator — unit system.")
    value_ratio_denominator_code: str | None = Field(None, description="value[x]: Ratio.denominator — coded unit form.")
    value_sampled_data_origin_value: float | None = Field(None, description="value[x]: SampledData.origin — numeric value.")
    value_sampled_data_origin_unit: str | None = Field(None, description="value[x]: SampledData.origin — unit.")
    value_sampled_data_origin_system: str | None = Field(None, description="value[x]: SampledData.origin — unit system.")
    value_sampled_data_origin_code: str | None = Field(None, description="value[x]: SampledData.origin — coded unit form.")
    value_sampled_data_period: float | None = Field(None, description="value[x]: SampledData.period — ms between samples.")
    value_sampled_data_factor: float | None = Field(None, description="value[x]: SampledData.factor — correction factor.")
    value_sampled_data_lower_limit: float | None = Field(None, description="value[x]: SampledData.lowerLimit.")
    value_sampled_data_upper_limit: float | None = Field(None, description="value[x]: SampledData.upperLimit.")
    value_sampled_data_dimensions: int | None = Field(None, description="value[x]: SampledData.dimensions — sample points per time point.")
    value_sampled_data_data: str | None = Field(None, description="value[x]: SampledData.data — space-separated values.")
    value_time: time | None = Field(None, description="value[x]: time.")
    value_date_time: datetime | None = Field(None, description="value[x]: dateTime.")
    value_period_start: datetime | None = Field(None, description="value[x]: Period — start.")
    value_period_end: datetime | None = Field(None, description="value[x]: Period — end.")

    data_absent_reason: ObservationCodeableConceptInput | None = Field(None, description="Why the value is missing.")
    interpretation: list[ObservationCodeableConceptInput] | None = Field(None, description="Categorical assessment, e.g. high, low, normal.")
    note: list[ObservationNoteInput] | None = Field(None, description="Comments about the observation or results.")
    body_site: ObservationCodeableConceptInput | None = Field(None, description="Body site where the observation was made.")
    method: ObservationCodeableConceptInput | None = Field(None, description="Mechanism used to perform the observation.")
    specimen: ObservationSpecimenInput | None = Field(None, description="Specimen used for the observation.")
    device: ObservationDeviceInput | None = Field(None, description="Device that generated the observation data.")
    reference_range: list[ObservationReferenceRangeInput] | None = Field(None, description="Guidance for interpreting the value.")
    has_member: list[ObservationHasMemberInput] | None = Field(None, description="Member resources in a group observation.")
    derived_from: list[ObservationDerivedFromInput] | None = Field(None, description="Measurements this observation value is derived from.")
    component: list[ObservationComponentInput] | None = Field(None, description="Component observations sharing the same attributes.")


class ObservationPatchSchema(BaseModel):
    """Partial update — only supplied fields are written. Every supplied
    sub-resource list (even `[]`) replaces the corresponding rows
    wholesale; omitted lists are left untouched. `org_id`/`created_by`/
    `updated_by` all come from the verified JWT now — none are
    request-body fields."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"status": "amended"}})

    extension: list[dict] | None = Field(None, description="Replaces the full list if supplied.")
    identifier: list[ObservationIdentifierInput] | None = Field(None, description="Replaces the full list if supplied.")
    based_on: list[ObservationBasedOnInput] | None = Field(None, description="Replaces the full list if supplied.")
    part_of: list[ObservationPartOfInput] | None = Field(None, description="Replaces the full list if supplied.")
    status: ObservationStatus | None = Field(None, description="registered | preliminary | final | amended | corrected | cancelled | entered-in-error | unknown.")
    category: list[ObservationCodeableConceptInput] | None = Field(None, description="Replaces the full list if supplied.")
    code: ObservationCodeableConceptInput | None = Field(None, description="Set to null to clear (not recommended — code is 1..1 in FHIR).")
    subject: ObservationSubjectInput | None = Field(None, description="Set to null to clear.")
    focus: list[ObservationFocusInput] | None = Field(None, description="Replaces the full list if supplied.")
    encounter: ObservationEncounterInput | None = Field(None, description="Set to null to clear.")

    effective_date_time: datetime | None = Field(None, description="effective[x]: dateTime.")
    effective_period_start: datetime | None = Field(None, description="effective[x]: Period — start.")
    effective_period_end: datetime | None = Field(None, description="effective[x]: Period — end.")
    effective_timing: dict | None = Field(None, description="effective[x]: Timing, as a raw FHIR Timing dict.")
    effective_instant: datetime | None = Field(None, description="effective[x]: instant.")

    issued: datetime | None = Field(None, description="When this version was made available to providers.")
    performer: list[ObservationPerformerInput] | None = Field(None, description="Replaces the full list if supplied.")

    value_quantity_value: float | None = Field(None, description="value[x]: Quantity — numeric value.")
    value_quantity_comparator: ObservationQuantityComparator | None = Field(None, description="value[x]: Quantity — comparator.")
    value_quantity_unit: str | None = Field(None, description="value[x]: Quantity — unit.")
    value_quantity_system: str | None = Field(None, description="value[x]: Quantity — unit system.")
    value_quantity_code: str | None = Field(None, description="value[x]: Quantity — coded unit form.")
    value_codeable_concept: ObservationCodeableConceptInput | None = Field(None, description="value[x]: CodeableConcept.")
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
    value_ratio_numerator_comparator: ObservationQuantityComparator | None = Field(None, description="value[x]: Ratio.numerator — comparator.")
    value_ratio_numerator_unit: str | None = Field(None, description="value[x]: Ratio.numerator — unit.")
    value_ratio_numerator_system: str | None = Field(None, description="value[x]: Ratio.numerator — unit system.")
    value_ratio_numerator_code: str | None = Field(None, description="value[x]: Ratio.numerator — coded unit form.")
    value_ratio_denominator_value: float | None = Field(None, description="value[x]: Ratio.denominator — numeric value.")
    value_ratio_denominator_comparator: ObservationQuantityComparator | None = Field(None, description="value[x]: Ratio.denominator — comparator.")
    value_ratio_denominator_unit: str | None = Field(None, description="value[x]: Ratio.denominator — unit.")
    value_ratio_denominator_system: str | None = Field(None, description="value[x]: Ratio.denominator — unit system.")
    value_ratio_denominator_code: str | None = Field(None, description="value[x]: Ratio.denominator — coded unit form.")
    value_sampled_data_origin_value: float | None = Field(None, description="value[x]: SampledData.origin — numeric value.")
    value_sampled_data_origin_unit: str | None = Field(None, description="value[x]: SampledData.origin — unit.")
    value_sampled_data_origin_system: str | None = Field(None, description="value[x]: SampledData.origin — unit system.")
    value_sampled_data_origin_code: str | None = Field(None, description="value[x]: SampledData.origin — coded unit form.")
    value_sampled_data_period: float | None = Field(None, description="value[x]: SampledData.period — ms between samples.")
    value_sampled_data_factor: float | None = Field(None, description="value[x]: SampledData.factor — correction factor.")
    value_sampled_data_lower_limit: float | None = Field(None, description="value[x]: SampledData.lowerLimit.")
    value_sampled_data_upper_limit: float | None = Field(None, description="value[x]: SampledData.upperLimit.")
    value_sampled_data_dimensions: int | None = Field(None, description="value[x]: SampledData.dimensions — sample points per time point.")
    value_sampled_data_data: str | None = Field(None, description="value[x]: SampledData.data — space-separated values.")
    value_time: time | None = Field(None, description="value[x]: time.")
    value_date_time: datetime | None = Field(None, description="value[x]: dateTime.")
    value_period_start: datetime | None = Field(None, description="value[x]: Period — start.")
    value_period_end: datetime | None = Field(None, description="value[x]: Period — end.")

    data_absent_reason: ObservationCodeableConceptInput | None = Field(None, description="Set to null to clear.")
    interpretation: list[ObservationCodeableConceptInput] | None = Field(None, description="Replaces the full list if supplied.")
    note: list[ObservationNoteInput] | None = Field(None, description="Replaces the full list if supplied.")
    body_site: ObservationCodeableConceptInput | None = Field(None, description="Set to null to clear.")
    method: ObservationCodeableConceptInput | None = Field(None, description="Set to null to clear.")
    specimen: ObservationSpecimenInput | None = Field(None, description="Set to null to clear.")
    device: ObservationDeviceInput | None = Field(None, description="Set to null to clear.")
    reference_range: list[ObservationReferenceRangeInput] | None = Field(None, description="Replaces the full list if supplied.")
    has_member: list[ObservationHasMemberInput] | None = Field(None, description="Replaces the full list if supplied.")
    derived_from: list[ObservationDerivedFromInput] | None = Field(None, description="Replaces the full list if supplied.")
    component: list[ObservationComponentInput] | None = Field(None, description="Replaces the full list if supplied.")
