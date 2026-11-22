from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

# RequestStatus (the required binding of CarePlan.status).
StatusCode = Literal[
    "draft", "active", "on-hold", "revoked", "completed", "entered-in-error", "unknown"
]
# CarePlanIntent (the required binding of CarePlan.intent).
IntentCode = Literal["proposal", "plan", "order", "option"]
# CarePlanActivityKind and CarePlanActivityStatus (required bindings of activity.detail).
ActivityKind = Literal[
    "Appointment",
    "CommunicationRequest",
    "DeviceRequest",
    "MedicationRequest",
    "NutritionOrder",
    "Task",
    "ServiceRequest",
    "VisionPrescription",
]
ActivityStatus = Literal[
    "not-started",
    "scheduled",
    "in-progress",
    "on-hold",
    "completed",
    "cancelled",
    "stopped",
    "unknown",
    "entered-in-error",
]

_EXAMPLE = {
    "resourceType": "CarePlan",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/care-plan-id",
            "value": "CP-1001",
        }
    ],
    "status": "active",
    "intent": "plan",
    "category": [
        {
            "coding": [
                {
                    "system": "http://hl7.org/fhir/us/core/CodeSystem/careplan-category",
                    "code": "assess-plan",
                }
            ]
        }
    ],
    "title": "Diabetes management plan",
    "subject": {"reference": "Patient/10001"},
    "period": {"start": "2026-01-01"},
    "author": {"reference": "Practitioner/30001"},
    "careTeam": [{"reference": "CareTeam/390001"}],
    "addresses": [{"reference": "Condition/120001"}],
    "activity": [
        {
            "detail": {
                "kind": "ServiceRequest",
                "code": {
                    "coding": [
                        {"system": "http://snomed.info/sct", "code": "386053000"}
                    ]
                },
                "status": "scheduled",
                "scheduledPeriod": {"start": "2026-02-01", "end": "2026-02-28"},
                "performer": [{"reference": "Practitioner/30001"}],
            }
        }
    ],
    "note": [{"text": "Review monthly."}],
}


class CarePlanQuantityInput(FhirInputModel):
    """Quantity (SimpleQuantity) - a measured amount."""

    value: float | int | None = Field(None, description="Numerical value.")
    comparator: Literal["<", "<=", ">=", ">"] | None = Field(
        None, description="How the value should be understood."
    )
    unit: str | None = Field(None, description="Unit representation.")
    system: str | None = Field(None, description="System that defines coded unit form.")
    code: str | None = Field(None, description="Coded form of the unit.")


class CarePlanAnnotationInput(FhirInputModel):
    """Annotation - a note with an author (a Reference or plain text) and a time."""

    authorReference: FhirReferenceInput | None = Field(
        None,
        description="Individual responsible for the annotation - Reference(Practitioner | Patient | RelatedPerson | Organization). A relative reference must exist in the caller's org (422 otherwise).",
    )
    authorString: str | None = Field(
        None, description="Individual responsible for the annotation, as plain text."
    )
    time: str | None = Field(
        None, description="When the annotation was made (a FHIR dateTime)."
    )
    text: str | None = Field(
        None, description="The annotation text, as markdown (required by R4)."
    )


class CarePlanActivityDetailInput(FhirInputModel):
    """CarePlan.activity.detail - in-line definition of activity."""

    kind: ActivityKind | None = Field(
        None, description="Kind of resource the activity is."
    )
    instantiatesCanonical: list[str] | None = Field(
        None, description="Instantiates FHIR protocol or definition (canonical URLs)."
    )
    instantiatesUri: list[str] | None = Field(
        None, description="Instantiates external protocol or definition (URIs)."
    )
    code: FhirCodeableConceptInput | None = Field(
        None, description="Detail type of activity. Searched by `activity-code`."
    )
    reasonCode: list[FhirCodeableConceptInput] | None = Field(
        None, description="Why activity should be done or why activity was prohibited."
    )
    reasonReference: list[FhirReferenceInput] | None = Field(
        None,
        description="Why activity is needed - Reference(Condition | Observation | DiagnosticReport | DocumentReference). A relative Condition / Observation / DiagnosticReport must exist in the caller's org (422 otherwise).",
    )
    goal: list[FhirReferenceInput] | None = Field(
        None,
        description="Goals this activity relates to - Reference(Goal). Stored as sent.",
    )
    status: ActivityStatus | None = Field(
        None,
        description="not-started | scheduled | in-progress | on-hold | completed | cancelled | stopped | unknown | entered-in-error (required by R4).",
    )
    statusReason: FhirCodeableConceptInput | None = Field(
        None, description="Reason for current status."
    )
    doNotPerform: bool | None = Field(
        None, description="If true, activity is prohibiting action."
    )
    scheduledTiming: dict | None = Field(
        None,
        description="When activity is to occur (a Timing, as raw FHIR JSON). One of the scheduled[x] choices; searched by `activity-date`.",
    )
    scheduledPeriod: FhirPeriodInput | None = Field(
        None,
        description="When activity is to occur (a Period). One of the scheduled[x] choices; searched by `activity-date`.",
    )
    scheduledString: str | None = Field(
        None,
        description="When activity is to occur (a string). One of the scheduled[x] choices; not a date, so not searchable.",
    )
    location: FhirReferenceInput | None = Field(
        None,
        description="Where it should happen - Reference(Location). A relative reference must exist in the caller's org (422 otherwise).",
    )
    performer: list[FhirReferenceInput] | None = Field(
        None,
        description="Who will be responsible? - Reference(Practitioner | PractitionerRole | Organization | RelatedPerson | Patient | CareTeam | HealthcareService | Device). A relative reference of a type built here must exist in the caller's org (422 otherwise). Searched by `performer`.",
    )
    productCodeableConcept: FhirCodeableConceptInput | None = Field(
        None,
        description="What is to be administered/supplied (a CodeableConcept). One of the product[x] choices.",
    )
    productReference: FhirReferenceInput | None = Field(
        None,
        description="What is to be administered/supplied - Reference(Medication | Substance). One of the product[x] choices. A relative Medication must exist in the caller's org (422 otherwise).",
    )
    dailyAmount: CarePlanQuantityInput | None = Field(
        None, description="How to consume/day?"
    )
    quantity: CarePlanQuantityInput | None = Field(
        None, description="How much to administer/supply/consume."
    )
    description: str | None = Field(
        None, description="Extra info describing activity to perform."
    )


class CarePlanActivityInput(FhirInputModel):
    """CarePlan.activity - action to occur as part of plan. R4 rule cpl-3: `reference` or `detail`, not both."""

    outcomeCodeableConcept: list[FhirCodeableConceptInput] | None = Field(
        None, description="Results of the activity."
    )
    outcomeReference: list[FhirReferenceInput] | None = Field(
        None,
        description="Appointment, Encounter, Procedure, etc. - Reference(Any). A relative reference of a type built here must exist in the caller's org (422 otherwise).",
    )
    progress: list[CarePlanAnnotationInput] | None = Field(
        None, description="Comments about the activity status/progress."
    )
    reference: FhirReferenceInput | None = Field(
        None,
        description="Activity details defined in specific resource - Reference(Appointment | CommunicationRequest | DeviceRequest | MedicationRequest | NutritionOrder | Task | ServiceRequest | VisionPrescription | RequestGroup). A relative Appointment / MedicationRequest / ServiceRequest must exist in the caller's org (422 otherwise). Searched by `activity-reference`.",
    )
    detail: CarePlanActivityDetailInput | None = Field(
        None, description="In-line definition of activity."
    )


class _CarePlanFields(FhirInputModel):
    """Every writable CarePlan element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/careplan.html). Create and patch accept exactly the same fields.
    R4 requires `status`, `intent` and `subject` (enforced by base R4 validation on the stored
    document).

    The validated body is stored whole (CarePlanModel.content), so any valid R4 element is kept -
    including ones this model does not declare. Server-managed elements are ignored if sent:
    `id` (assigned from the care_plan_id sequence) and `meta` (audit/tenant data, stamped on at
    read time). org_id and created_by/updated_by come from the verified JWT (actor.org_id /
    actor.sub), never the body. There is no user_id."""

    resourceType: Literal["CarePlan"] | None = Field(
        None, description="Optional; if supplied it must be 'CarePlan'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries - validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="External Ids for this plan. Searched by `identifier`."
    )
    instantiatesCanonical: list[str] | None = Field(
        None,
        description="Instantiates FHIR protocol or definition (canonical URLs). Searched by `instantiates-canonical`.",
    )
    instantiatesUri: list[str] | None = Field(
        None,
        description="Instantiates external protocol or definition (URIs). Searched by `instantiates-uri`.",
    )
    basedOn: list[FhirReferenceInput] | None = Field(
        None,
        description="Fulfills CarePlan - Reference(CarePlan). A relative reference must exist in the caller's org (422 otherwise).",
    )
    replaces: list[FhirReferenceInput] | None = Field(
        None,
        description="CarePlan replaced by this CarePlan - Reference(CarePlan). A relative reference must exist in the caller's org (422 otherwise).",
    )
    partOf: list[FhirReferenceInput] | None = Field(
        None,
        description="Part of referenced CarePlan - Reference(CarePlan). A relative reference must exist in the caller's org (422 otherwise).",
    )
    status: StatusCode | None = Field(
        None,
        description="draft | active | on-hold | revoked | completed | entered-in-error | unknown (required by R4). Searched by `status`.",
    )
    intent: IntentCode | None = Field(
        None,
        description="proposal | plan | order | option (required by R4). Searched by `intent`.",
    )
    category: list[FhirCodeableConceptInput] | None = Field(
        None, description="Type of plan. Searched by `category`."
    )
    title: str | None = Field(
        None, description="Human-friendly name for the care plan."
    )
    description: str | None = Field(None, description="Summary of nature of plan.")
    subject: FhirReferenceInput | None = Field(
        None,
        description="Who the care plan is for - Reference(Patient | Group) (required by R4). A relative reference must exist in the caller's org (422 otherwise). Searched by `subject` / `patient`.",
    )
    encounter: FhirReferenceInput | None = Field(
        None,
        description="The Encounter during which this CarePlan was created - Reference(Encounter). A relative reference must exist in the caller's org (422 otherwise). Searched by `encounter`.",
    )
    period: FhirPeriodInput | None = Field(
        None, description="Time period plan covers. Searched by `date`."
    )
    created: str | None = Field(
        None, description="Date record was first recorded (a FHIR dateTime)."
    )
    author: FhirReferenceInput | None = Field(
        None,
        description="Who is the designated responsible party - Reference(Patient | Practitioner | PractitionerRole | Device | RelatedPerson | Organization | CareTeam). A relative reference of a type built here must exist in the caller's org (422 otherwise).",
    )
    contributor: list[FhirReferenceInput] | None = Field(
        None,
        description="Who provided the content of the care plan - same targets as `author`.",
    )
    careTeam: list[FhirReferenceInput] | None = Field(
        None,
        description="Who's involved in plan? - Reference(CareTeam). A relative reference must exist in the caller's org (422 otherwise). Searched by `care-team`.",
    )
    addresses: list[FhirReferenceInput] | None = Field(
        None,
        description="Health issues this plan addresses - Reference(Condition). A relative reference must exist in the caller's org (422 otherwise). Searched by `condition`.",
    )
    supportingInfo: list[FhirReferenceInput] | None = Field(
        None,
        description="Information considered as part of plan - Reference(Any). A relative reference of a type built here must exist in the caller's org (422 otherwise).",
    )
    goal: list[FhirReferenceInput] | None = Field(
        None,
        description="Desired outcome of plan - Reference(Goal). Stored as sent. Searched by `goal`.",
    )
    activity: list[CarePlanActivityInput] | None = Field(
        None, description="Action to occur as part of plan."
    )
    note: list[CarePlanAnnotationInput] | None = Field(
        None, description="Comments about the plan."
    )


class CarePlanCreateSchema(_CarePlanFields):
    """POST body - a FHIR R4 CarePlan resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class CarePlanPatchSchema(_CarePlanFields):
    """PATCH body - a partial FHIR R4 CarePlan (merge-patch semantics on top-level elements). Only
    supplied elements are written; omitted ones are left untouched. A supplied element replaces the
    stored value wholesale - a list (even `[]`) replaces every existing entry, an object such as
    `period` replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "completed",
                "period": {"start": "2026-01-01", "end": "2026-06-30"},
            }
        }
    }
