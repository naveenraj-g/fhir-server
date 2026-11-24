from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

# publication-status (the required binding of ActivityDefinition.status).
StatusCode = Literal["draft", "active", "retired", "unknown"]
# RequestResourceType (the required binding of ActivityDefinition.kind).
KindCode = Literal[
    "Appointment",
    "AppointmentResponse",
    "CarePlan",
    "Claim",
    "CommunicationRequest",
    "Contract",
    "DeviceRequest",
    "EnrollmentRequest",
    "ImmunizationRecommendation",
    "MedicationRequest",
    "NutritionOrder",
    "ServiceRequest",
    "SupplyRequest",
    "Task",
    "VisionPrescription",
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
    "resourceType": "ActivityDefinition",
    "url": "https://fhir-server.dev/fhir/ActivityDefinition/follow-up-visit",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/activity-definition-id",
            "value": "AD-1",
        }
    ],
    "version": "1.0",
    "name": "FollowUpVisit",
    "title": "Follow-up visit",
    "status": "active",
    "date": "2026-01-15",
    "publisher": "Example Health",
    "description": "Book a follow-up visit.",
    "useContext": [
        {
            "code": {
                "system": "http://terminology.hl7.org/CodeSystem/usage-context-type",
                "code": "focus",
            },
            "valueCodeableConcept": {
                "coding": [{"system": "http://snomed.info/sct", "code": "35489007"}]
            },
        }
    ],
    "jurisdiction": [{"coding": [{"system": "urn:iso:std:iso:3166", "code": "US"}]}],
    "topic": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/definition-topic",
                    "code": "treatment",
                }
            ]
        }
    ],
    "kind": "ServiceRequest",
    "intent": "order",
    "priority": "routine",
}


class _ActivityDefinitionFields(FhirInputModel):
    """Every writable ActivityDefinition element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/activitydefinition.html). Create and patch accept exactly the
    same fields. R4 requires `status`; the native validator cannot see a missing primitive
    `status`, which only the `java_validator` backend rejects.

    The validated body is stored whole (ActivityDefinitionModel.content), so any valid R4 element
    is kept - including ones this model does not declare. Server-managed elements are ignored if
    sent: `id` (assigned from the activity_definition_id sequence) and `meta` (audit/tenant data,
    stamped on at read time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["ActivityDefinition"] | None = Field(
        None, description="Optional; if supplied it must be 'ActivityDefinition'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries - validated by the profile pipeline, not here.",
    )
    url: str | None = Field(
        None,
        description="Canonical identifier for this activity definition. Searched by `url`.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="Additional identifier. Searched by `identifier`."
    )
    version: str | None = Field(
        None,
        description="Business version of the activity definition. Searched by `version`.",
    )
    name: str | None = Field(
        None,
        description="Name for this activity definition (computer friendly). Searched by `name`.",
    )
    title: str | None = Field(
        None,
        description="Name for this activity definition (human friendly). Searched by `title`.",
    )
    subtitle: str | None = Field(None, description="Subordinate title.")
    status: StatusCode | None = Field(
        None,
        description="draft | active | retired | unknown (required by R4). Searched by `status`.",
    )
    experimental: bool | None = Field(
        None, description="For testing purposes, not real usage."
    )
    subjectCodeableConcept: FhirCodeableConceptInput | None = Field(
        None,
        description="subject[x]: type of individual the activity definition is intended for.",
    )
    subjectReference: FhirReferenceInput | None = Field(
        None,
        description="subject[x]: Reference(Group) the activity definition is intended for.",
    )
    date: str | None = Field(
        None, description="Date last changed (a FHIR dateTime). Searched by `date`."
    )
    publisher: str | None = Field(
        None, description="Name of the publisher. Searched by `publisher`."
    )
    contact: list[dict] | None = Field(
        None, description="Contact details for the publisher (ContactDetail)."
    )
    description: str | None = Field(
        None, description="Natural language description. Searched by `description`."
    )
    useContext: list[dict] | None = Field(
        None,
        description="The context that the content is intended to support (UsageContext). Searched by `context`, `context-type`, `context-quantity` and the two composites.",
    )
    jurisdiction: list[FhirCodeableConceptInput] | None = Field(
        None, description="Intended jurisdiction. Searched by `jurisdiction`."
    )
    purpose: str | None = Field(
        None, description="Why this activity definition is defined."
    )
    usage: str | None = Field(
        None, description="Describes the clinical usage of the activity definition."
    )
    copyright: str | None = Field(
        None, description="Use and/or publishing restrictions."
    )
    approvalDate: str | None = Field(
        None, description="When the activity definition was approved by the publisher."
    )
    lastReviewDate: str | None = Field(
        None, description="When the activity definition was last reviewed."
    )
    effectivePeriod: FhirPeriodInput | None = Field(
        None,
        description="When the activity definition is expected to be used. Searched by `effective`.",
    )
    topic: list[FhirCodeableConceptInput] | None = Field(
        None,
        description="E.g. Education, Treatment, Assessment, etc. Searched by `topic`.",
    )
    author: list[dict] | None = Field(
        None, description="Who authored the content (ContactDetail)."
    )
    editor: list[dict] | None = Field(
        None, description="Who edited the content (ContactDetail)."
    )
    reviewer: list[dict] | None = Field(
        None, description="Who reviewed the content (ContactDetail)."
    )
    endorser: list[dict] | None = Field(
        None, description="Who endorsed the content (ContactDetail)."
    )
    relatedArtifact: list[dict] | None = Field(
        None,
        description="Additional documentation, citations, etc. (RelatedArtifact). The `resource` of a `composed-of` / `depends-on` / `derived-from` / `predecessor` / `successor` entry is searched by the parameter of that name.",
    )
    library: list[str] | None = Field(
        None,
        description="Logic used by the activity definition (canonical(Library)). Searched by `depends-on`.",
    )
    kind: KindCode | None = Field(None, description="Kind of resource.")
    profile: str | None = Field(
        None, description="What profile the resource needs to conform to."
    )
    code: FhirCodeableConceptInput | None = Field(
        None, description="Detail type of activity."
    )
    intent: IntentCode | None = Field(
        None,
        description="proposal | plan | directive | order | original-order | reflex-order | filler-order | instance-order | option.",
    )
    priority: PriorityCode | None = Field(
        None, description="routine | urgent | asap | stat."
    )
    doNotPerform: bool | None = Field(
        None, description="True if the activity should not be performed."
    )
    timingTiming: dict | None = Field(
        None, description="timing[x]: when activity is to occur (Timing)."
    )
    timingDateTime: str | None = Field(
        None, description="timing[x]: when activity is to occur (dateTime)."
    )
    timingAge: dict | None = Field(
        None, description="timing[x]: when activity is to occur (Age)."
    )
    timingPeriod: FhirPeriodInput | None = Field(
        None, description="timing[x]: when activity is to occur (Period)."
    )
    timingRange: dict | None = Field(
        None, description="timing[x]: when activity is to occur (Range)."
    )
    timingDuration: dict | None = Field(
        None, description="timing[x]: when activity is to occur (Duration)."
    )
    location: FhirReferenceInput | None = Field(
        None, description="Where it should happen - Reference(Location)."
    )
    participant: list[dict] | None = Field(
        None, description="Who should participate in the action."
    )
    productReference: FhirReferenceInput | None = Field(
        None,
        description="product[x]: what's administered/supplied - Reference(Medication | Substance).",
    )
    productCodeableConcept: FhirCodeableConceptInput | None = Field(
        None, description="product[x]: what's administered/supplied."
    )
    quantity: dict | None = Field(
        None, description="How much is administered/consumed/supplied (SimpleQuantity)."
    )
    dosage: list[dict] | None = Field(
        None, description="Detailed dosage instructions (Dosage)."
    )
    bodySite: list[FhirCodeableConceptInput] | None = Field(
        None, description="What part of body to perform on."
    )
    specimenRequirement: list[FhirReferenceInput] | None = Field(
        None,
        description="What specimens are required to perform this action - Reference(SpecimenDefinition).",
    )
    observationRequirement: list[FhirReferenceInput] | None = Field(
        None,
        description="What observations are required to perform this action - Reference(ObservationDefinition).",
    )
    observationResultRequirement: list[FhirReferenceInput] | None = Field(
        None,
        description="What observations must be produced by this action - Reference(ObservationDefinition).",
    )
    transform: str | None = Field(
        None, description="Transform to apply the template (canonical(StructureMap))."
    )
    dynamicValue: list[dict] | None = Field(
        None, description="Dynamic aspects of the definition."
    )


class ActivityDefinitionCreateSchema(_ActivityDefinitionFields):
    """POST body - a FHIR R4 ActivityDefinition resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class ActivityDefinitionPatchSchema(_ActivityDefinitionFields):
    """PATCH body - a partial FHIR R4 ActivityDefinition (merge-patch semantics on top-level
    elements). Only supplied elements are written; omitted ones are left untouched. A supplied
    element replaces the stored value wholesale - a list (even `[]`) replaces every existing
    entry, an object replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {"status": "retired", "version": "1.1"},
        }
    }
