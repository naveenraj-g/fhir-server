from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

# RequestStatus, RequestIntent and RequestPriority (the required bindings).
StatusCode = Literal[
    "draft",
    "active",
    "on-hold",
    "revoked",
    "completed",
    "entered-in-error",
    "unknown",
]
IntentCode = Literal[
    "proposal",
    "plan",
    "directive",
    "order",
    "original-order",
    "reflex-order",
    "filler-order",
    "instance-order",
    "option",
]
PriorityCode = Literal["routine", "urgent", "asap", "stat"]

_EXAMPLE = {
    "resourceType": "ServiceRequest",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/service-request-id",
            "value": "SR-1001",
        }
    ],
    "status": "active",
    "intent": "order",
    "priority": "routine",
    "category": [
        {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "108252007",
                    "display": "Laboratory procedure",
                }
            ]
        }
    ],
    "code": {
        "coding": [
            {
                "system": "http://loinc.org",
                "code": "58410-2",
                "display": "CBC panel - Blood by Automated count",
            }
        ]
    },
    "subject": {"reference": "Patient/10001"},
    "encounter": {"reference": "Encounter/20001"},
    "occurrenceDateTime": "2023-01-16T09:00:00Z",
    "authoredOn": "2023-01-15T09:30:00Z",
    "requester": {"reference": "Practitioner/30001"},
    "performer": [{"reference": "Organization/190001"}],
    "reasonCode": [
        {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "271737000",
                    "display": "Anemia",
                }
            ]
        }
    ],
    "note": [{"text": "Fasting not required."}],
}


class ServiceRequestQuantityInput(FhirInputModel):
    """Quantity — a measured amount with an optional comparator."""

    value: float | int | None = Field(
        None, description="Numerical value (with implicit precision)."
    )
    comparator: Literal["<", "<=", ">=", ">"] | None = Field(
        None, description="How the value should be understood: < | <= | >= | >."
    )
    unit: str | None = Field(None, description="Unit representation.")
    system: str | None = Field(
        None,
        description="System that defines coded unit form (usually http://unitsofmeasure.org).",
    )
    code: str | None = Field(None, description="Coded form of the unit.")


class ServiceRequestRatioInput(FhirInputModel):
    """Ratio — a relationship of two Quantity values."""

    numerator: ServiceRequestQuantityInput | None = Field(
        None, description="Numerator value."
    )
    denominator: ServiceRequestQuantityInput | None = Field(
        None, description="Denominator value."
    )


class ServiceRequestRangeInput(FhirInputModel):
    """Range — a set of values bounded by low and high."""

    low: ServiceRequestQuantityInput | None = Field(None, description="Low limit.")
    high: ServiceRequestQuantityInput | None = Field(None, description="High limit.")


class ServiceRequestAnnotationInput(FhirInputModel):
    """Annotation — a note with an author (a Reference or plain text) and a time."""

    authorReference: FhirReferenceInput | None = Field(
        None,
        description="Individual responsible for the annotation — Reference(Practitioner | Patient | RelatedPerson | Organization). A relative reference must exist in the caller's org (422 otherwise).",
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


class _ServiceRequestFields(FhirInputModel):
    """Every writable ServiceRequest element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/servicerequest.html). Create and patch accept exactly the
    same fields. R4 requires `status`, `intent` and `subject` (and rule prr-1: `orderDetail`
    only with a `code`), but those minimums are enforced by the base-R4 validator
    (`java_validator` backend), not by this model — so a PATCH can send any subset.

    The validated body is stored whole (ServiceRequestModel.content), so any valid R4 element
    is kept — including ones this model does not declare. Server-managed elements are ignored
    if sent: `id` (assigned from the service_request_id sequence) and `meta` (audit/tenant
    data, stamped on at read time). org_id and created_by/updated_by come from the verified
    JWT (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["ServiceRequest"] | None = Field(
        None, description="Optional; if supplied it must be 'ServiceRequest'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="Identifiers assigned to this order."
    )
    instantiatesCanonical: list[str] | None = Field(
        None,
        description="Instantiates FHIR protocol or definition — canonical URLs of an ActivityDefinition or PlanDefinition (`url` or `url|version`). Searched by `instantiates-canonical`.",
    )
    instantiatesUri: list[str] | None = Field(
        None,
        description="Instantiates external protocol or definition (URIs). Searched by `instantiates-uri`.",
    )
    basedOn: list[FhirReferenceInput] | None = Field(
        None,
        description="What request fulfills — Reference(CarePlan | ServiceRequest | MedicationRequest). A relative ServiceRequest must exist in the caller's org (422 otherwise); CarePlan and MedicationRequest are stored as sent.",
    )
    replaces: list[FhirReferenceInput] | None = Field(
        None,
        description="What request replaces — Reference(ServiceRequest). A relative reference must exist in the caller's org (422 otherwise).",
    )
    requisition: FhirIdentifierInput | None = Field(
        None, description="Composite Request ID. Searched by `requisition`."
    )
    status: StatusCode | None = Field(
        None,
        description="draft | active | on-hold | revoked | completed | entered-in-error | unknown (required by R4).",
    )
    intent: IntentCode | None = Field(
        None,
        description="proposal | plan | directive | order | original-order | reflex-order | filler-order | instance-order | option (required by R4).",
    )
    category: list[FhirCodeableConceptInput] | None = Field(
        None, description="Classification of service."
    )
    priority: PriorityCode | None = Field(
        None, description="routine | urgent | asap | stat."
    )
    doNotPerform: bool | None = Field(
        None, description="True if the service should NOT be performed."
    )
    code: FhirCodeableConceptInput | None = Field(
        None, description="What is being requested/ordered."
    )
    orderDetail: list[FhirCodeableConceptInput] | None = Field(
        None,
        description="Additional order information (only with a `code`, rule prr-1).",
    )
    quantityQuantity: ServiceRequestQuantityInput | None = Field(
        None, description="Service amount (a Quantity). One of the quantity[x] choices."
    )
    quantityRatio: ServiceRequestRatioInput | None = Field(
        None, description="Service amount (a Ratio). One of the quantity[x] choices."
    )
    quantityRange: ServiceRequestRangeInput | None = Field(
        None, description="Service amount (a Range). One of the quantity[x] choices."
    )
    subject: FhirReferenceInput | None = Field(
        None,
        description="Individual or entity the service is ordered for — Reference(Patient | Group | Location | Device). A relative Patient or Location must exist in the caller's org (422 otherwise).",
    )
    encounter: FhirReferenceInput | None = Field(
        None,
        description="Encounter in which the request was created — Reference(Encounter). A relative reference must exist in the caller's org (422 otherwise).",
    )
    occurrenceDateTime: str | None = Field(
        None,
        description="When service should occur (a FHIR dateTime). One of the occurrence[x] choices; searched by `occurrence`.",
    )
    occurrencePeriod: FhirPeriodInput | None = Field(
        None,
        description="When service should occur (a Period). One of the occurrence[x] choices; searched by `occurrence`.",
    )
    occurrenceTiming: dict | None = Field(
        None,
        description="When service should occur (a Timing, as raw FHIR JSON). One of the occurrence[x] choices; searched by `occurrence`.",
    )
    asNeededBoolean: bool | None = Field(
        None,
        description="Preconditions for service (a boolean). One of the asNeeded[x] choices.",
    )
    asNeededCodeableConcept: FhirCodeableConceptInput | None = Field(
        None,
        description="Preconditions for service (a CodeableConcept). One of the asNeeded[x] choices.",
    )
    authoredOn: str | None = Field(
        None,
        description="Date request signed (a FHIR dateTime). Searched by `authored`.",
    )
    requester: FhirReferenceInput | None = Field(
        None,
        description="Who/what is requesting service — Reference(Practitioner | PractitionerRole | Organization | Patient | RelatedPerson | Device). A relative reference of a rebuilt type must exist in the caller's org (422 otherwise).",
    )
    performerType: FhirCodeableConceptInput | None = Field(
        None, description="Performer role. Searched by `performer-type`."
    )
    performer: list[FhirReferenceInput] | None = Field(
        None,
        description="Requested performer — Reference(Practitioner | PractitionerRole | Organization | CareTeam | HealthcareService | Patient | Device | RelatedPerson). A relative reference of a rebuilt type must exist in the caller's org (422 otherwise).",
    )
    locationCode: list[FhirCodeableConceptInput] | None = Field(
        None, description="Requested location (coded)."
    )
    locationReference: list[FhirReferenceInput] | None = Field(
        None,
        description="Requested location — Reference(Location). A relative reference must exist in the caller's org (422 otherwise).",
    )
    reasonCode: list[FhirCodeableConceptInput] | None = Field(
        None, description="Explanation/justification for procedure or service (coded)."
    )
    reasonReference: list[FhirReferenceInput] | None = Field(
        None,
        description="Explanation/justification — Reference(Condition | Observation | DiagnosticReport | DocumentReference). A relative Condition, Observation or DiagnosticReport must exist in the caller's org (422 otherwise).",
    )
    insurance: list[FhirReferenceInput] | None = Field(
        None,
        description="Associated insurance coverage — Reference(Coverage | ClaimResponse). Stored as sent.",
    )
    supportingInfo: list[FhirReferenceInput] | None = Field(
        None,
        description="Additional clinical information — Reference(Any). A relative reference to a rebuilt resource must exist in the caller's org (422 otherwise).",
    )
    specimen: list[FhirReferenceInput] | None = Field(
        None,
        description="Procedure samples — Reference(Specimen). A relative reference must exist in the caller's org (422 otherwise).",
    )
    bodySite: list[FhirCodeableConceptInput] | None = Field(
        None, description="Location on Body."
    )
    note: list[ServiceRequestAnnotationInput] | None = Field(
        None, description="Comments."
    )
    patientInstruction: str | None = Field(
        None, description="Patient or consumer-oriented instructions."
    )
    relevantHistory: list[FhirReferenceInput] | None = Field(
        None, description="Request provenance — Reference(Provenance). Stored as sent."
    )


class ServiceRequestCreateSchema(_ServiceRequestFields):
    """POST body — a FHIR R4 ServiceRequest resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class ServiceRequestPatchSchema(_ServiceRequestFields):
    """PATCH body — a partial FHIR R4 ServiceRequest (merge-patch semantics on top-level
    elements). Only supplied elements are written; omitted ones are left untouched. A supplied
    element replaces the stored value wholesale — a list (even `[]`) replaces every existing
    entry, an object replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "completed",
                "priority": "urgent",
                "note": [{"text": "Results called through."}],
            }
        }
    }
