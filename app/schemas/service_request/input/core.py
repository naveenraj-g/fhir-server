from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import (
    ServiceRequestIntent,
    ServiceRequestPriority,
    ServiceRequestQuantityComparator,
    ServiceRequestStatus,
)

from .codeable_concept import ServiceRequestCodeableConceptInput
from .identifier import ServiceRequestIdentifierInput
from .note import ServiceRequestNoteInput
from .reference import (
    ServiceRequestBasedOnInput,
    ServiceRequestEncounterInput,
    ServiceRequestInsuranceInput,
    ServiceRequestLocationReferenceInput,
    ServiceRequestPerformerInput,
    ServiceRequestReasonReferenceInput,
    ServiceRequestRelevantHistoryInput,
    ServiceRequestReplacesInput,
    ServiceRequestRequesterInput,
    ServiceRequestSpecimenInput,
    ServiceRequestSubjectInput,
    ServiceRequestSupportingInfoInput,
)

_EXAMPLE = {
    "status": "active",
    "intent": "order",
    "subject": {"reference": "Patient/10001"},
    "code": {"text": "Chest X-ray"},
    "authored_on": "2026-01-15T10:30:00Z",
}


class ServiceRequestCreateSchema(BaseModel):
    """Creates a ServiceRequest and any combination of its sub-resource
    lists atomically in one request — same set-once-then-patch shape as
    every other resource in this codebase.

    JWT/RBAC auth-rollout pattern — same as every other resource now:
    `org_id`/`created_by` come from the verified JWT (`actor.org_id`/
    `actor.sub`), not the request body — an org-less token is rejected
    outright (403). `user_id` is unaffected — still a plain, optional,
    gateway-forwarded field.

    `quantity[x]`/`occurrence[x]`/`asNeeded[x]` choice-type fields are
    all flattened directly onto this schema with a field-group-per-
    variant shape (e.g. `quantity_quantity_*` vs `quantity_ratio_*` vs
    `quantity_range_*`) — the service layer picks whichever group is
    actually populated; supplying more than one variant group is not
    rejected at the schema layer (same tolerance as every other
    choice-type field in this codebase)."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": _EXAMPLE})


    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions, as raw [{url, valueType, value}, ...] entries."
    )

    identifier: list[ServiceRequestIdentifierInput] | None = Field(None, description="Business identifiers for this request.")
    instantiates_canonical: list[str] | None = Field(None, description="Canonical references to instantiated ActivityDefinition/PlanDefinition.")
    instantiates_uri: list[str] | None = Field(None, description="External protocol/definition URIs instantiated.")
    based_on: list[ServiceRequestBasedOnInput] | None = Field(None, description="Plan/proposal/order fulfilled by this request.")
    replaces: list[ServiceRequestReplacesInput] | None = Field(None, description="The request this one supersedes.")
    requisition: ServiceRequestIdentifierInput | None = Field(None, description="A shared identifier common to all service requests in a requisition.")

    status: ServiceRequestStatus = Field(..., description="draft | active | on-hold | revoked | completed | entered-in-error | unknown.")
    intent: ServiceRequestIntent = Field(..., description="proposal | plan | directive | order | original-order | reflex-order | filler-order | instance-order | option.")
    category: list[ServiceRequestCodeableConceptInput] | None = Field(None, description="Classification of the service.")
    priority: ServiceRequestPriority | None = Field(None, description="routine | urgent | asap | stat.")
    do_not_perform: bool | None = Field(None, description="True if the service/procedure should NOT be performed.")
    code: ServiceRequestCodeableConceptInput | None = Field(None, description="What is being requested/ordered.")
    order_detail: list[ServiceRequestCodeableConceptInput] | None = Field(
        None, description="Additional order details — SHALL only be present if `code` is present."
    )

    # quantity[x] — choice of Quantity | Ratio | Range
    quantity_quantity_value: float | None = Field(None, description="quantity[x]: Quantity — numeric value.")
    quantity_quantity_comparator: ServiceRequestQuantityComparator | None = Field(None, description="quantity[x]: Quantity — < | <= | >= | >.")
    quantity_quantity_unit: str | None = Field(None, description="quantity[x]: Quantity — unit representation.")
    quantity_quantity_system: str | None = Field(None, description="quantity[x]: Quantity — unit system.")
    quantity_quantity_code: str | None = Field(None, description="quantity[x]: Quantity — coded unit form.")
    quantity_ratio_numerator_value: float | None = Field(None, description="quantity[x]: Ratio.numerator — numeric value.")
    quantity_ratio_numerator_comparator: ServiceRequestQuantityComparator | None = Field(None, description="quantity[x]: Ratio.numerator — comparator.")
    quantity_ratio_numerator_unit: str | None = Field(None, description="quantity[x]: Ratio.numerator — unit.")
    quantity_ratio_numerator_system: str | None = Field(None, description="quantity[x]: Ratio.numerator — unit system.")
    quantity_ratio_numerator_code: str | None = Field(None, description="quantity[x]: Ratio.numerator — coded unit form.")
    quantity_ratio_denominator_value: float | None = Field(None, description="quantity[x]: Ratio.denominator — numeric value.")
    quantity_ratio_denominator_comparator: ServiceRequestQuantityComparator | None = Field(None, description="quantity[x]: Ratio.denominator — comparator.")
    quantity_ratio_denominator_unit: str | None = Field(None, description="quantity[x]: Ratio.denominator — unit.")
    quantity_ratio_denominator_system: str | None = Field(None, description="quantity[x]: Ratio.denominator — unit system.")
    quantity_ratio_denominator_code: str | None = Field(None, description="quantity[x]: Ratio.denominator — coded unit form.")
    quantity_range_low_value: float | None = Field(None, description="quantity[x]: Range.low — numeric value.")
    quantity_range_low_unit: str | None = Field(None, description="quantity[x]: Range.low — unit.")
    quantity_range_low_system: str | None = Field(None, description="quantity[x]: Range.low — unit system.")
    quantity_range_low_code: str | None = Field(None, description="quantity[x]: Range.low — coded unit form.")
    quantity_range_high_value: float | None = Field(None, description="quantity[x]: Range.high — numeric value.")
    quantity_range_high_unit: str | None = Field(None, description="quantity[x]: Range.high — unit.")
    quantity_range_high_system: str | None = Field(None, description="quantity[x]: Range.high — unit system.")
    quantity_range_high_code: str | None = Field(None, description="quantity[x]: Range.high — coded unit form.")

    subject: ServiceRequestSubjectInput = Field(..., description="Individual/entity the service is for (1..1, required).")
    encounter: ServiceRequestEncounterInput | None = Field(None, description="Encounter this request was created during.")

    # occurrence[x] — choice of dateTime | Period | Timing
    occurrence_date_time: datetime | None = Field(None, description="occurrence[x]: dateTime.")
    occurrence_period_start: datetime | None = Field(None, description="occurrence[x]: Period — start.")
    occurrence_period_end: datetime | None = Field(None, description="occurrence[x]: Period — end.")
    occurrence_timing: dict | None = Field(
        None,
        description="occurrence[x]: Timing, as a raw FHIR Timing BackboneElement dict — stored and round-tripped verbatim rather than flattened (see ServiceRequestModel's docstring for why).",
    )

    # asNeeded[x] — choice of boolean | CodeableConcept
    as_needed_boolean: bool | None = Field(None, description="asNeeded[x]: boolean.")
    as_needed_codeable_concept: ServiceRequestCodeableConceptInput | None = Field(None, description="asNeeded[x]: CodeableConcept.")

    authored_on: datetime | None = Field(None, description="Date/time the request was authored.")
    requester: ServiceRequestRequesterInput | None = Field(None, description="Who/what is requesting the service.")
    performer_type: ServiceRequestCodeableConceptInput | None = Field(None, description="Desired kind of performer for the service.")
    performer: list[ServiceRequestPerformerInput] | None = Field(None, description="Desired performer(s).")
    location_code: list[ServiceRequestCodeableConceptInput] | None = Field(None, description="Requested location, coded.")
    location_reference: list[ServiceRequestLocationReferenceInput] | None = Field(None, description="Requested location, resolved.")
    reason_code: list[ServiceRequestCodeableConceptInput] | None = Field(None, description="Explanation/justification for the request, coded.")
    reason_reference: list[ServiceRequestReasonReferenceInput] | None = Field(None, description="Explanation/justification for the request, resolved.")
    insurance: list[ServiceRequestInsuranceInput] | None = Field(None, description="Associated insurance coverage.")
    supporting_info: list[ServiceRequestSupportingInfoInput] | None = Field(None, description="Additional clinical information.")
    specimen: list[ServiceRequestSpecimenInput] | None = Field(None, description="Procedure Samples.")
    body_site: list[ServiceRequestCodeableConceptInput] | None = Field(None, description="Coded body site(s).")
    note: list[ServiceRequestNoteInput] | None = Field(None, description="Comments.")
    patient_instruction: str | None = Field(None, description="Patient/consumer-oriented instructions.")
    relevant_history: list[ServiceRequestRelevantHistoryInput] | None = Field(None, description="Key events in the history of the request.")


class ServiceRequestPatchSchema(BaseModel):
    """Partial update — only supplied fields are written. Every supplied
    sub-resource list (even `[]`) replaces the corresponding rows
    wholesale; omitted lists are left untouched. `org_id`/`created_by`/
    `updated_by` all come from the verified JWT now — none are
    request-body fields."""

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": {"status": "completed"}})

    extension: list[dict] | None = Field(None, description="Replaces the full list if supplied.")
    identifier: list[ServiceRequestIdentifierInput] | None = Field(None, description="Replaces the full list if supplied.")
    instantiates_canonical: list[str] | None = Field(None, description="Replaces the full list if supplied.")
    instantiates_uri: list[str] | None = Field(None, description="Replaces the full list if supplied.")
    based_on: list[ServiceRequestBasedOnInput] | None = Field(None, description="Replaces the full list if supplied.")
    replaces: list[ServiceRequestReplacesInput] | None = Field(None, description="Replaces the full list if supplied.")
    requisition: ServiceRequestIdentifierInput | None = Field(None, description="Set to null to clear.")

    status: ServiceRequestStatus | None = Field(None, description="draft | active | on-hold | revoked | completed | entered-in-error | unknown.")
    intent: ServiceRequestIntent | None = Field(None, description="proposal | plan | directive | order | original-order | reflex-order | filler-order | instance-order | option.")
    category: list[ServiceRequestCodeableConceptInput] | None = Field(None, description="Replaces the full list if supplied.")
    priority: ServiceRequestPriority | None = Field(None, description="routine | urgent | asap | stat.")
    do_not_perform: bool | None = Field(None, description="True if the service/procedure should NOT be performed.")
    code: ServiceRequestCodeableConceptInput | None = Field(None, description="Set to null to clear.")
    order_detail: list[ServiceRequestCodeableConceptInput] | None = Field(None, description="Replaces the full list if supplied.")

    quantity_quantity_value: float | None = Field(None, description="quantity[x]: Quantity — numeric value.")
    quantity_quantity_comparator: ServiceRequestQuantityComparator | None = Field(None, description="quantity[x]: Quantity — comparator.")
    quantity_quantity_unit: str | None = Field(None, description="quantity[x]: Quantity — unit.")
    quantity_quantity_system: str | None = Field(None, description="quantity[x]: Quantity — unit system.")
    quantity_quantity_code: str | None = Field(None, description="quantity[x]: Quantity — coded unit form.")
    quantity_ratio_numerator_value: float | None = Field(None, description="quantity[x]: Ratio.numerator — numeric value.")
    quantity_ratio_numerator_comparator: ServiceRequestQuantityComparator | None = Field(None, description="quantity[x]: Ratio.numerator — comparator.")
    quantity_ratio_numerator_unit: str | None = Field(None, description="quantity[x]: Ratio.numerator — unit.")
    quantity_ratio_numerator_system: str | None = Field(None, description="quantity[x]: Ratio.numerator — unit system.")
    quantity_ratio_numerator_code: str | None = Field(None, description="quantity[x]: Ratio.numerator — coded unit form.")
    quantity_ratio_denominator_value: float | None = Field(None, description="quantity[x]: Ratio.denominator — numeric value.")
    quantity_ratio_denominator_comparator: ServiceRequestQuantityComparator | None = Field(None, description="quantity[x]: Ratio.denominator — comparator.")
    quantity_ratio_denominator_unit: str | None = Field(None, description="quantity[x]: Ratio.denominator — unit.")
    quantity_ratio_denominator_system: str | None = Field(None, description="quantity[x]: Ratio.denominator — unit system.")
    quantity_ratio_denominator_code: str | None = Field(None, description="quantity[x]: Ratio.denominator — coded unit form.")
    quantity_range_low_value: float | None = Field(None, description="quantity[x]: Range.low — numeric value.")
    quantity_range_low_unit: str | None = Field(None, description="quantity[x]: Range.low — unit.")
    quantity_range_low_system: str | None = Field(None, description="quantity[x]: Range.low — unit system.")
    quantity_range_low_code: str | None = Field(None, description="quantity[x]: Range.low — coded unit form.")
    quantity_range_high_value: float | None = Field(None, description="quantity[x]: Range.high — numeric value.")
    quantity_range_high_unit: str | None = Field(None, description="quantity[x]: Range.high — unit.")
    quantity_range_high_system: str | None = Field(None, description="quantity[x]: Range.high — unit system.")
    quantity_range_high_code: str | None = Field(None, description="quantity[x]: Range.high — coded unit form.")

    subject: ServiceRequestSubjectInput | None = Field(None, description="Set to null to clear (not recommended — subject is 1..1 in FHIR).")
    encounter: ServiceRequestEncounterInput | None = Field(None, description="Set to null to clear.")

    occurrence_date_time: datetime | None = Field(None, description="occurrence[x]: dateTime.")
    occurrence_period_start: datetime | None = Field(None, description="occurrence[x]: Period — start.")
    occurrence_period_end: datetime | None = Field(None, description="occurrence[x]: Period — end.")
    occurrence_timing: dict | None = Field(None, description="occurrence[x]: Timing, raw dict.")

    as_needed_boolean: bool | None = Field(None, description="asNeeded[x]: boolean.")
    as_needed_codeable_concept: ServiceRequestCodeableConceptInput | None = Field(None, description="asNeeded[x]: CodeableConcept.")

    authored_on: datetime | None = Field(None, description="Date/time the request was authored.")
    requester: ServiceRequestRequesterInput | None = Field(None, description="Set to null to clear.")
    performer_type: ServiceRequestCodeableConceptInput | None = Field(None, description="Set to null to clear.")
    performer: list[ServiceRequestPerformerInput] | None = Field(None, description="Replaces the full list if supplied.")
    location_code: list[ServiceRequestCodeableConceptInput] | None = Field(None, description="Replaces the full list if supplied.")
    location_reference: list[ServiceRequestLocationReferenceInput] | None = Field(None, description="Replaces the full list if supplied.")
    reason_code: list[ServiceRequestCodeableConceptInput] | None = Field(None, description="Replaces the full list if supplied.")
    reason_reference: list[ServiceRequestReasonReferenceInput] | None = Field(None, description="Replaces the full list if supplied.")
    insurance: list[ServiceRequestInsuranceInput] | None = Field(None, description="Replaces the full list if supplied.")
    supporting_info: list[ServiceRequestSupportingInfoInput] | None = Field(None, description="Replaces the full list if supplied.")
    specimen: list[ServiceRequestSpecimenInput] | None = Field(None, description="Replaces the full list if supplied.")
    body_site: list[ServiceRequestCodeableConceptInput] | None = Field(None, description="Replaces the full list if supplied.")
    note: list[ServiceRequestNoteInput] | None = Field(None, description="Replaces the full list if supplied.")
    patient_instruction: str | None = Field(None, description="Patient/consumer-oriented instructions.")
    relevant_history: list[ServiceRequestRelevantHistoryInput] | None = Field(None, description="Replaces the full list if supplied.")
