from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRReference,
)
from app.schemas.questionnaire.response import FHIRQuantity

from .codeable_concept import PlainServiceRequestCode, PlainServiceRequestCodeableConcept
from .identifier import PlainServiceRequestIdentifier, PlainServiceRequestRequisition
from .note import PlainServiceRequestNote
from .reference import (
    PlainServiceRequestBasedOn,
    PlainServiceRequestEncounter,
    PlainServiceRequestInsurance,
    PlainServiceRequestLocationReference,
    PlainServiceRequestPerformer,
    PlainServiceRequestReasonReference,
    PlainServiceRequestRelevantHistory,
    PlainServiceRequestReplaces,
    PlainServiceRequestRequester,
    PlainServiceRequestSpecimen,
    PlainServiceRequestSubject,
    PlainServiceRequestSupportingInfo,
)

# ── FHIR (camelCase) ────────────────────────────────────────────────────────


class FHIRRatio(BaseModel):
    """FHIR R4 Ratio — this codebase's first use. Used only by
    ServiceRequest.quantityRatio's numerator/denominator."""

    numerator: FHIRQuantity | None = None
    denominator: FHIRQuantity | None = None


class FHIRAnnotation(BaseModel):
    """FHIR R4 Annotation — this codebase's first use, via
    ServiceRequest.note. `authorReference`/`authorString` are the two
    `author[x]` variants."""

    authorReference: FHIRReference | None = None
    authorString: str | None = None
    time: str | None = None
    text: str = Field(..., description="The annotation text (markdown).")


class FHIRServiceRequestSchema(BaseModel):
    resourceType: str = Field("ServiceRequest", description="Always 'ServiceRequest'.")
    id: str = Field(..., description="Public service_request_id as a string.")
    meta: FHIRMeta | None = Field(None, description="Infrastructure-maintained resource metadata. Response-only.")
    extension: list[dict] | None = Field(None, description="Resource-level FHIR extensions.")
    identifier: list[FHIRIdentifier] | None = Field(None, description="Business identifiers for this request.")
    instantiatesCanonical: list[str] | None = Field(None, description="Canonical references instantiated.")
    instantiatesUri: list[str] | None = Field(None, description="External protocol/definition URIs instantiated.")
    basedOn: list[FHIRReference] | None = Field(None, description="Plan/proposal/order fulfilled by this request.")
    replaces: list[FHIRReference] | None = Field(None, description="The request this one supersedes.")
    requisition: FHIRIdentifier | None = Field(None, description="A shared identifier common to all service requests in a requisition.")
    status: str = Field(..., description="draft | active | on-hold | revoked | completed | entered-in-error | unknown.")
    intent: str = Field(..., description="proposal | plan | directive | order | original-order | reflex-order | filler-order | instance-order | option.")
    category: list[FHIRCodeableConcept] | None = Field(None, description="Classification of the service.")
    priority: str | None = Field(None, description="routine | urgent | asap | stat.")
    doNotPerform: bool | None = Field(None, description="True if the service/procedure should NOT be performed.")
    code: FHIRCodeableConcept | None = Field(None, description="What is being requested/ordered.")
    orderDetail: list[FHIRCodeableConcept] | None = Field(None, description="Additional order details.")
    quantityQuantity: FHIRQuantity | None = Field(None, description="quantity[x]: Quantity.")
    quantityRatio: FHIRRatio | None = Field(None, description="quantity[x]: Ratio.")
    quantityRange: dict | None = Field(None, description="quantity[x]: Range.")
    subject: FHIRReference = Field(..., description="Individual/entity the service is for.")
    encounter: FHIRReference | None = Field(None, description="Encounter this request was created during.")
    occurrenceDateTime: str | None = Field(None, description="occurrence[x]: dateTime.")
    occurrencePeriod: dict | None = Field(None, description="occurrence[x]: Period.")
    occurrenceTiming: dict | None = Field(None, description="occurrence[x]: Timing (raw, verbatim).")
    asNeededBoolean: bool | None = Field(None, description="asNeeded[x]: boolean.")
    asNeededCodeableConcept: FHIRCodeableConcept | None = Field(None, description="asNeeded[x]: CodeableConcept.")
    authoredOn: str | None = Field(None, description="Date/time the request was authored.")
    requester: FHIRReference | None = Field(None, description="Who/what is requesting the service.")
    performerType: FHIRCodeableConcept | None = Field(None, description="Desired kind of performer.")
    performer: list[FHIRReference] | None = Field(None, description="Desired performer(s).")
    locationCode: list[FHIRCodeableConcept] | None = Field(None, description="Requested location, coded.")
    locationReference: list[FHIRReference] | None = Field(None, description="Requested location, resolved.")
    reasonCode: list[FHIRCodeableConcept] | None = Field(None, description="Explanation/justification, coded.")
    reasonReference: list[FHIRReference] | None = Field(None, description="Explanation/justification, resolved.")
    insurance: list[FHIRReference] | None = Field(None, description="Associated insurance coverage.")
    supportingInfo: list[FHIRReference] | None = Field(None, description="Additional clinical information.")
    specimen: list[FHIRReference] | None = Field(None, description="Procedure samples.")
    bodySite: list[FHIRCodeableConcept] | None = Field(None, description="Coded body site(s).")
    note: list[FHIRAnnotation] | None = Field(None, description="Comments.")
    patientInstruction: str | None = Field(None, description="Patient/consumer-oriented instructions.")
    relevantHistory: list[FHIRReference] | None = Field(None, description="Key events in the history of the request.")


class FHIRServiceRequestBundleEntry(BaseModel):
    resource: FHIRServiceRequestSchema


class FHIRServiceRequestBundle(FHIRBundle):
    entry: list[FHIRServiceRequestBundleEntry] | None = None


# ── Plain (snake_case) ───────────────────────────────────────────────────────


class PlainServiceRequestResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    id: int = Field(..., description="Public service_request_id.")
    extension: list[dict] | None = Field(None, description="Resource-level FHIR extensions.")
    identifier: list[PlainServiceRequestIdentifier] | None = Field(None, description="Business identifiers.")
    instantiates_canonical: list[str] | None = Field(None, description="Canonical references instantiated.")
    instantiates_uri: list[str] | None = Field(None, description="External protocol/definition URIs instantiated.")
    based_on: list[PlainServiceRequestBasedOn] | None = Field(None, description="Plan/proposal/order fulfilled.")
    replaces: list[PlainServiceRequestReplaces] | None = Field(None, description="The request this one supersedes.")
    requisition: PlainServiceRequestRequisition | None = Field(None, description="Shared requisition identifier.")
    status: str | None = Field(None, description="draft | active | on-hold | revoked | completed | entered-in-error | unknown.")
    intent: str | None = Field(None, description="proposal | plan | directive | order | original-order | reflex-order | filler-order | instance-order | option.")
    category: list[PlainServiceRequestCodeableConcept] | None = Field(None, description="Classification of the service.")
    priority: str | None = Field(None, description="routine | urgent | asap | stat.")
    do_not_perform: bool | None = Field(None, description="True if the service/procedure should NOT be performed.")
    code: PlainServiceRequestCode | None = Field(None, description="What is being requested/ordered.")
    order_detail: list[PlainServiceRequestCodeableConcept] | None = Field(None, description="Additional order details.")
    quantity_quantity_value: float | None = Field(None, description="quantity[x]: Quantity — numeric value.")
    quantity_quantity_comparator: str | None = Field(None, description="quantity[x]: Quantity — comparator.")
    quantity_quantity_unit: str | None = Field(None, description="quantity[x]: Quantity — unit.")
    quantity_quantity_system: str | None = Field(None, description="quantity[x]: Quantity — unit system.")
    quantity_quantity_code: str | None = Field(None, description="quantity[x]: Quantity — coded unit form.")
    quantity_ratio_numerator_value: float | None = Field(None, description="quantity[x]: Ratio.numerator — value.")
    quantity_ratio_numerator_comparator: str | None = Field(None, description="quantity[x]: Ratio.numerator — comparator.")
    quantity_ratio_numerator_unit: str | None = Field(None, description="quantity[x]: Ratio.numerator — unit.")
    quantity_ratio_numerator_system: str | None = Field(None, description="quantity[x]: Ratio.numerator — unit system.")
    quantity_ratio_numerator_code: str | None = Field(None, description="quantity[x]: Ratio.numerator — coded unit form.")
    quantity_ratio_denominator_value: float | None = Field(None, description="quantity[x]: Ratio.denominator — value.")
    quantity_ratio_denominator_comparator: str | None = Field(None, description="quantity[x]: Ratio.denominator — comparator.")
    quantity_ratio_denominator_unit: str | None = Field(None, description="quantity[x]: Ratio.denominator — unit.")
    quantity_ratio_denominator_system: str | None = Field(None, description="quantity[x]: Ratio.denominator — unit system.")
    quantity_ratio_denominator_code: str | None = Field(None, description="quantity[x]: Ratio.denominator — coded unit form.")
    quantity_range_low_value: float | None = Field(None, description="quantity[x]: Range.low — value.")
    quantity_range_low_unit: str | None = Field(None, description="quantity[x]: Range.low — unit.")
    quantity_range_low_system: str | None = Field(None, description="quantity[x]: Range.low — unit system.")
    quantity_range_low_code: str | None = Field(None, description="quantity[x]: Range.low — coded unit form.")
    quantity_range_high_value: float | None = Field(None, description="quantity[x]: Range.high — value.")
    quantity_range_high_unit: str | None = Field(None, description="quantity[x]: Range.high — unit.")
    quantity_range_high_system: str | None = Field(None, description="quantity[x]: Range.high — unit system.")
    quantity_range_high_code: str | None = Field(None, description="quantity[x]: Range.high — coded unit form.")
    subject: PlainServiceRequestSubject | None = Field(None, description="Individual/entity the service is for.")
    encounter: PlainServiceRequestEncounter | None = Field(None, description="Encounter this request was created during.")
    occurrence_date_time: str | None = Field(None, description="occurrence[x]: dateTime.")
    occurrence_period_start: str | None = Field(None, description="occurrence[x]: Period — start.")
    occurrence_period_end: str | None = Field(None, description="occurrence[x]: Period — end.")
    occurrence_timing: dict | None = Field(None, description="occurrence[x]: Timing, raw dict.")
    as_needed_boolean: bool | None = Field(None, description="asNeeded[x]: boolean.")
    as_needed_codeable_concept: PlainServiceRequestCode | None = Field(None, description="asNeeded[x]: CodeableConcept.")
    authored_on: str | None = Field(None, description="Date/time the request was authored.")
    requester: PlainServiceRequestRequester | None = Field(None, description="Who/what is requesting the service.")
    performer_type: PlainServiceRequestCode | None = Field(None, description="Desired kind of performer.")
    performer: list[PlainServiceRequestPerformer] | None = Field(None, description="Desired performer(s).")
    location_code: list[PlainServiceRequestCodeableConcept] | None = Field(None, description="Requested location, coded.")
    location_reference: list[PlainServiceRequestLocationReference] | None = Field(None, description="Requested location, resolved.")
    reason_code: list[PlainServiceRequestCodeableConcept] | None = Field(None, description="Explanation/justification, coded.")
    reason_reference: list[PlainServiceRequestReasonReference] | None = Field(None, description="Explanation/justification, resolved.")
    insurance: list[PlainServiceRequestInsurance] | None = Field(None, description="Associated insurance coverage.")
    supporting_info: list[PlainServiceRequestSupportingInfo] | None = Field(None, description="Additional clinical information.")
    specimen: list[PlainServiceRequestSpecimen] | None = Field(None, description="Procedure samples.")
    body_site: list[PlainServiceRequestCodeableConcept] | None = Field(None, description="Coded body site(s).")
    note: list[PlainServiceRequestNote] | None = Field(None, description="Comments.")
    patient_instruction: str | None = Field(None, description="Patient/consumer-oriented instructions.")
    relevant_history: list[PlainServiceRequestRelevantHistory] | None = Field(None, description="Key events in the history of the request.")
    user_id: str | None = Field(None, description="Gateway-forwarded end-user ID — not a FHIR concept.")
    org_id: str | None = Field(None, description="Gateway-forwarded tenant/account ID — not a FHIR concept. Internally this column is named tenant_id.")
    created_at: str | None = Field(None, description="When this row was created.")
    updated_at: str | None = Field(None, description="When this row was last updated.")
    created_by: str | None = Field(None, description="Acting user who created this record.")
    updated_by: str | None = Field(None, description="Acting user who last updated this record.")


class PaginatedServiceRequestResponse(BaseModel):
    total: int | None = Field(None, description="Total matching rows (null when total_mode=none).")
    limit: int = Field(..., description="Page size used for this response.")
    offset: int = Field(..., description="Number of rows skipped before this page.")
    data: list[PlainServiceRequestResponse]
