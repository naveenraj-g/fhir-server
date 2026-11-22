from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

# medicationrequest-status, medicationrequest-intent and request-priority (the required bindings).
StatusCode = Literal[
    "active",
    "on-hold",
    "cancelled",
    "completed",
    "entered-in-error",
    "stopped",
    "draft",
    "unknown",
]
IntentCode = Literal[
    "proposal",
    "plan",
    "order",
    "original-order",
    "reflex-order",
    "filler-order",
    "instance-order",
    "option",
]
PriorityCode = Literal["routine", "urgent", "asap", "stat"]

_EXAMPLE = {
    "resourceType": "MedicationRequest",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/prescription-id",
            "value": "RX-1001",
        }
    ],
    "status": "active",
    "intent": "order",
    "category": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/medicationrequest-category",
                    "code": "outpatient",
                    "display": "Outpatient",
                }
            ]
        }
    ],
    "priority": "routine",
    "medicationCodeableConcept": {
        "coding": [
            {
                "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                "code": "1049502",
                "display": "12 HR Oxycodone Hydrochloride 10 MG Extended Release Oral Tablet",
            }
        ]
    },
    "subject": {"reference": "Patient/10001"},
    "encounter": {"reference": "Encounter/20001"},
    "authoredOn": "2023-01-15T09:30:00Z",
    "requester": {"reference": "Practitioner/30001"},
    "reasonCode": [
        {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "22253000",
                    "display": "Pain",
                }
            ]
        }
    ],
    "note": [{"text": "Take with food."}],
    "dosageInstruction": [
        {
            "sequence": 1,
            "text": "1 tablet every 12 hours",
            "timing": {"repeat": {"frequency": 1, "period": 12, "periodUnit": "h"}},
            "route": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "26643006",
                        "display": "Oral route",
                    }
                ]
            },
            "doseAndRate": [{"doseQuantity": {"value": 1, "unit": "tablet"}}],
        }
    ],
    "dispenseRequest": {
        "validityPeriod": {"start": "2023-01-15", "end": "2023-07-15"},
        "numberOfRepeatsAllowed": 1,
        "quantity": {"value": 60, "unit": "tablet"},
        "expectedSupplyDuration": {
            "value": 30,
            "unit": "days",
            "system": "http://unitsofmeasure.org",
            "code": "d",
        },
    },
    "substitution": {"allowedBoolean": True},
}


class MedicationRequestQuantityInput(FhirInputModel):
    """Quantity - a measured amount with an optional comparator."""

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


class MedicationRequestAnnotationInput(FhirInputModel):
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


class MedicationRequestInitialFillInput(FhirInputModel):
    """MedicationRequest.dispenseRequest.initialFill - first fill details (a quantity or a
    duration is required by R4)."""

    quantity: MedicationRequestQuantityInput | None = Field(
        None, description="First fill quantity."
    )
    duration: MedicationRequestQuantityInput | None = Field(
        None, description="First fill duration (a Duration)."
    )


class MedicationRequestDispenseRequestInput(FhirInputModel):
    """MedicationRequest.dispenseRequest - medication supply authorization."""

    initialFill: MedicationRequestInitialFillInput | None = Field(
        None, description="First fill details."
    )
    dispenseInterval: MedicationRequestQuantityInput | None = Field(
        None, description="Minimum period of time between dispenses (a Duration)."
    )
    validityPeriod: FhirPeriodInput | None = Field(
        None, description="Time period supply is authorized for."
    )
    numberOfRepeatsAllowed: int | None = Field(
        None, ge=0, description="Number of refills authorized."
    )
    quantity: MedicationRequestQuantityInput | None = Field(
        None, description="Amount of medication to supply per dispense."
    )
    expectedSupplyDuration: MedicationRequestQuantityInput | None = Field(
        None, description="Number of days supply per dispense (a Duration)."
    )
    performer: FhirReferenceInput | None = Field(
        None,
        description="Intended dispenser - Reference(Organization). A relative reference must exist in the caller's org (422 otherwise). Searched by `intended-dispenser`.",
    )


class MedicationRequestSubstitutionInput(FhirInputModel):
    """MedicationRequest.substitution - any restrictions on medication substitution."""

    allowedBoolean: bool | None = Field(
        None,
        description="Whether substitution is allowed or not (a boolean). One of the allowed[x] choices (required by R4).",
    )
    allowedCodeableConcept: FhirCodeableConceptInput | None = Field(
        None,
        description="What type of substitution is allowed (a CodeableConcept). One of the allowed[x] choices.",
    )
    reason: FhirCodeableConceptInput | None = Field(
        None, description="Why should (not) substitution be made."
    )


class _MedicationRequestFields(FhirInputModel):
    """Every writable MedicationRequest element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/medicationrequest.html). Create and patch accept exactly the
    same fields. R4 requires `status`, `intent`, `medication[x]` and `subject`, but those
    minimums are enforced by the base-R4 validator (`java_validator` backend), not by this
    model - so a PATCH can send any subset.

    The validated body is stored whole (MedicationRequestModel.content), so any valid R4
    element is kept - including ones this model does not declare. Server-managed elements are
    ignored if sent: `id` (assigned from the medication_request_id sequence) and `meta`
    (audit/tenant data, stamped on at read time). org_id and created_by/updated_by come from
    the verified JWT (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["MedicationRequest"] | None = Field(
        None, description="Optional; if supplied it must be 'MedicationRequest'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries - validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="External ids for this request."
    )
    status: StatusCode | None = Field(
        None,
        description="active | on-hold | cancelled | completed | entered-in-error | stopped | draft | unknown (required by R4).",
    )
    statusReason: FhirCodeableConceptInput | None = Field(
        None, description="Reason for current status."
    )
    intent: IntentCode | None = Field(
        None,
        description="proposal | plan | order | original-order | reflex-order | filler-order | instance-order | option (required by R4).",
    )
    category: list[FhirCodeableConceptInput] | None = Field(
        None, description="Type of medication usage."
    )
    priority: PriorityCode | None = Field(
        None, description="routine | urgent | asap | stat."
    )
    doNotPerform: bool | None = Field(
        None, description="True if request is prohibiting action."
    )
    reportedBoolean: bool | None = Field(
        None,
        description="Reported rather than primary record (a boolean). One of the reported[x] choices.",
    )
    reportedReference: FhirReferenceInput | None = Field(
        None,
        description="Reported rather than primary record - Reference(Patient | Practitioner | PractitionerRole | RelatedPerson | Organization). One of the reported[x] choices.",
    )
    medicationCodeableConcept: FhirCodeableConceptInput | None = Field(
        None,
        description="Medication to be taken (a CodeableConcept). One of the medication[x] choices (required by R4); searched by `code`.",
    )
    medicationReference: FhirReferenceInput | None = Field(
        None,
        description="Medication to be taken - Reference(Medication). One of the medication[x] choices (required by R4); searched by `medication`. A relative reference must exist in the caller's org (422 otherwise).",
    )
    subject: FhirReferenceInput | None = Field(
        None,
        description="Who or group medication request is for - Reference(Patient | Group). A relative Patient must exist in the caller's org (422 otherwise).",
    )
    encounter: FhirReferenceInput | None = Field(
        None,
        description="Encounter created as part of encounter/admission/stay - Reference(Encounter). A relative reference must exist in the caller's org (422 otherwise).",
    )
    supportingInformation: list[FhirReferenceInput] | None = Field(
        None,
        description="Information to support ordering of the medication - Reference(Any). A relative reference to a rebuilt resource must exist in the caller's org (422 otherwise).",
    )
    authoredOn: str | None = Field(
        None,
        description="When request was initially authored (a FHIR dateTime). Searched by `authoredon`.",
    )
    requester: FhirReferenceInput | None = Field(
        None,
        description="Who/What requested the Request - Reference(Practitioner | PractitionerRole | Organization | Patient | RelatedPerson | Device). A relative reference of a rebuilt type must exist in the caller's org (422 otherwise).",
    )
    performer: FhirReferenceInput | None = Field(
        None,
        description="Intended performer of administration - Reference(Practitioner | PractitionerRole | Organization | Patient | Device | RelatedPerson | CareTeam). Searched by `intended-performer`. A relative reference of a rebuilt type must exist in the caller's org (422 otherwise).",
    )
    performerType: FhirCodeableConceptInput | None = Field(
        None,
        description="Desired kind of performer of the medication administration. Searched by `intended-performertype`.",
    )
    recorder: FhirReferenceInput | None = Field(
        None,
        description="Person who entered the request - Reference(Practitioner | PractitionerRole).",
    )
    reasonCode: list[FhirCodeableConceptInput] | None = Field(
        None,
        description="Reason or indication for ordering or not ordering the medication.",
    )
    reasonReference: list[FhirReferenceInput] | None = Field(
        None,
        description="Condition or observation that supports why the prescription is being written - Reference(Condition | Observation). A relative reference must exist in the caller's org (422 otherwise).",
    )
    instantiatesCanonical: list[str] | None = Field(
        None, description="Instantiates FHIR protocol or definition (canonical URLs)."
    )
    instantiatesUri: list[str] | None = Field(
        None, description="Instantiates external protocol or definition."
    )
    basedOn: list[FhirReferenceInput] | None = Field(
        None,
        description="What request fulfills - Reference(CarePlan | MedicationRequest | ServiceRequest | ImmunizationRecommendation). A relative MedicationRequest, ServiceRequest or ImmunizationRecommendation must exist in the caller's org (422 otherwise).",
    )
    groupIdentifier: FhirIdentifierInput | None = Field(
        None, description="Composite request this is part of."
    )
    courseOfTherapyType: FhirCodeableConceptInput | None = Field(
        None, description="Overall pattern of medication administration."
    )
    insurance: list[FhirReferenceInput] | None = Field(
        None,
        description="Associated insurance coverage - Reference(Coverage | ClaimResponse). Stored as sent.",
    )
    note: list[MedicationRequestAnnotationInput] | None = Field(
        None, description="Information about the prescription."
    )
    dosageInstruction: list[dict] | None = Field(
        None,
        description="How the medication should be taken - a list of FHIR R4 Dosage elements (sequence, text, additionalInstruction, patientInstruction, timing, asNeeded[x], site, route, method, doseAndRate, maxDosePerPeriod, maxDosePerAdministration, maxDosePerLifetime), validated as R4 JSON. `timing.event` dateTimes are searched by `date`.",
    )
    dispenseRequest: MedicationRequestDispenseRequestInput | None = Field(
        None, description="Medication supply authorization."
    )
    substitution: MedicationRequestSubstitutionInput | None = Field(
        None, description="Any restrictions on medication substitution."
    )
    priorPrescription: FhirReferenceInput | None = Field(
        None,
        description="An order/prescription that is being replaced - Reference(MedicationRequest). A relative reference must exist in the caller's org (422 otherwise).",
    )
    detectedIssue: list[FhirReferenceInput] | None = Field(
        None,
        description="Clinical Issue with action - Reference(DetectedIssue). A relative reference must exist in the caller's org (422 otherwise).",
    )
    eventHistory: list[FhirReferenceInput] | None = Field(
        None,
        description="A list of events of interest in the lifecycle - Reference(Provenance). Stored as sent.",
    )


class MedicationRequestCreateSchema(_MedicationRequestFields):
    """POST body - a FHIR R4 MedicationRequest resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class MedicationRequestPatchSchema(_MedicationRequestFields):
    """PATCH body - a partial FHIR R4 MedicationRequest (merge-patch semantics on top-level
    elements). Only supplied elements are written; omitted ones are left untouched. A supplied
    element replaces the stored value wholesale - a list (even `[]`) replaces every existing
    entry, an object such as `dispenseRequest` replaces the whole value, and `null` clears
    it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "completed",
                "priority": "urgent",
                "note": [{"text": "Dispensed."}],
            }
        }
    }
