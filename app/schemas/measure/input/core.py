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

# publication-status (the required binding of Measure.status).
StatusCode = Literal["draft", "active", "retired", "unknown"]
_EXAMPLE = {
    "resourceType": "Measure",
    "url": "https://fhir-server.dev/fhir/Measure/follow-up-visit",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/measure-id",
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
    "scoring": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/measure-scoring",
                "code": "proportion",
            }
        ]
    },
    "improvementNotation": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/measure-improvement-notation",
                "code": "increase",
            }
        ]
    },
    "group": [
        {
            "description": "Overall",
            "population": [
                {
                    "code": {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/measure-population",
                                "code": "initial-population",
                            }
                        ]
                    },
                    "criteria": {
                        "language": "text/cql",
                        "expression": "Initial Population",
                    },
                }
            ],
        }
    ],
}


class _MeasureFields(FhirInputModel):
    """Every writable Measure element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/measure.html). Create and patch accept exactly the
    same fields. R4 requires `status`; the native validator cannot see a missing primitive
    `status`, which only the `java_validator` backend rejects.

    The validated body is stored whole (MeasureModel.content), so any valid R4 element
    is kept - including ones this model does not declare. Server-managed elements are ignored if
    sent: `id` (assigned from the measure_id sequence) and `meta` (audit/tenant data,
    stamped on at read time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["Measure"] | None = Field(
        None, description="Optional; if supplied it must be 'Measure'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries - validated by the profile pipeline, not here.",
    )
    url: str | None = Field(
        None,
        description="Canonical identifier for this measure. Searched by `url`.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="Additional identifier. Searched by `identifier`."
    )
    version: str | None = Field(
        None,
        description="Business version of the measure. Searched by `version`.",
    )
    name: str | None = Field(
        None,
        description="Name for this measure (computer friendly). Searched by `name`.",
    )
    title: str | None = Field(
        None,
        description="Name for this measure (human friendly). Searched by `title`.",
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
        description="subject[x]: type of individual the measure is intended for.",
    )
    subjectReference: FhirReferenceInput | None = Field(
        None,
        description="subject[x]: Reference(Group) the measure is intended for.",
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
    purpose: str | None = Field(None, description="Why this measure is defined.")
    usage: str | None = Field(
        None, description="Describes the clinical usage of the measure."
    )
    copyright: str | None = Field(
        None, description="Use and/or publishing restrictions."
    )
    approvalDate: str | None = Field(
        None, description="When the measure was approved by the publisher."
    )
    lastReviewDate: str | None = Field(
        None, description="When the measure was last reviewed."
    )
    effectivePeriod: FhirPeriodInput | None = Field(
        None,
        description="When the measure is expected to be used. Searched by `effective`.",
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
        description="Logic used by the measure (canonical(Library)). Searched by `depends-on`.",
    )
    disclaimer: str | None = Field(
        None, description="Disclaimer for use of the measure or its referenced content."
    )
    scoring: FhirCodeableConceptInput | None = Field(
        None, description="proportion | ratio | continuous-variable | cohort."
    )
    compositeScoring: FhirCodeableConceptInput | None = Field(
        None, description="opportunity | all-or-nothing | linear | weighted."
    )
    type: list[FhirCodeableConceptInput] | None = Field(
        None,
        description="process | outcome | structure | patient-reported-outcome | composite.",
    )
    riskAdjustment: str | None = Field(
        None, description="How risk adjustment is applied for this measure."
    )
    rateAggregation: str | None = Field(
        None, description="How is rate aggregation performed for this measure."
    )
    rationale: str | None = Field(
        None, description="Detailed description of why the measure exists."
    )
    clinicalRecommendationStatement: str | None = Field(
        None, description="Summary of clinical guidelines."
    )
    improvementNotation: FhirCodeableConceptInput | None = Field(
        None, description="increase | decrease."
    )
    definition: list[str] | None = Field(
        None, description="Defined terms used in the measure documentation."
    )
    guidance: str | None = Field(
        None, description="Additional guidance for implementers."
    )
    group: list[dict] | None = Field(
        None,
        description="Population criteria group: [{code, description, population[{code, description, criteria}], stratifier[{code, description, criteria, component[]}]}].",
    )
    supplementalData: list[dict] | None = Field(
        None,
        description="What other data should be reported with the measure: [{code, usage, description, criteria}].",
    )


class MeasureCreateSchema(_MeasureFields):
    """POST body - a FHIR R4 Measure resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class MeasurePatchSchema(_MeasureFields):
    """PATCH body - a partial FHIR R4 Measure (merge-patch semantics on top-level
    elements). Only supplied elements are written; omitted ones are left untouched. A supplied
    element replaces the stored value wholesale - a list (even `[]`) replaces every existing
    entry, an object replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {"status": "retired", "version": "1.1"},
        }
    }
