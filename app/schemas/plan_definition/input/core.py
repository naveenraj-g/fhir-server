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

# publication-status (the required binding of PlanDefinition.status).
StatusCode = Literal["draft", "active", "retired", "unknown"]
_EXAMPLE = {
    "resourceType": "PlanDefinition",
    "url": "https://fhir-server.dev/fhir/PlanDefinition/discharge-pathway",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/plan-definition-id",
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
    "type": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/plan-definition-type",
                "code": "order-set",
            }
        ]
    },
    "action": [
        {
            "title": "Book a visit",
            "definitionCanonical": "http://example.org/fhir/ActivityDefinition/follow-up-visit",
        }
    ],
}


class _PlanDefinitionFields(FhirInputModel):
    """Every writable PlanDefinition element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/plandefinition.html). Create and patch accept exactly the
    same fields. R4 requires `status`; the native validator cannot see a missing primitive
    `status`, which only the `java_validator` backend rejects.

    The validated body is stored whole (PlanDefinitionModel.content), so any valid R4 element
    is kept - including ones this model does not declare. Server-managed elements are ignored if
    sent: `id` (assigned from the plan_definition_id sequence) and `meta` (audit/tenant data,
    stamped on at read time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["PlanDefinition"] | None = Field(
        None, description="Optional; if supplied it must be 'PlanDefinition'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries - validated by the profile pipeline, not here.",
    )
    url: str | None = Field(
        None,
        description="Canonical identifier for this plan definition. Searched by `url`.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="Additional identifier. Searched by `identifier`."
    )
    version: str | None = Field(
        None,
        description="Business version of the plan definition. Searched by `version`.",
    )
    name: str | None = Field(
        None,
        description="Name for this plan definition (computer friendly). Searched by `name`.",
    )
    title: str | None = Field(
        None,
        description="Name for this plan definition (human friendly). Searched by `title`.",
    )
    subtitle: str | None = Field(None, description="Subordinate title.")
    type: FhirCodeableConceptInput | None = Field(
        None,
        description="order-set | clinical-protocol | eca-rule | workflow-definition. Searched by `type`.",
    )
    status: StatusCode | None = Field(
        None,
        description="draft | active | retired | unknown (required by R4). Searched by `status`.",
    )
    experimental: bool | None = Field(
        None, description="For testing purposes, not real usage."
    )
    subjectCodeableConcept: FhirCodeableConceptInput | None = Field(
        None,
        description="subject[x]: type of individual the plan definition is intended for.",
    )
    subjectReference: FhirReferenceInput | None = Field(
        None,
        description="subject[x]: Reference(Group) the plan definition is intended for.",
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
        None, description="Why this plan definition is defined."
    )
    usage: str | None = Field(
        None, description="Describes the clinical usage of the plan definition."
    )
    copyright: str | None = Field(
        None, description="Use and/or publishing restrictions."
    )
    approvalDate: str | None = Field(
        None, description="When the plan definition was approved by the publisher."
    )
    lastReviewDate: str | None = Field(
        None, description="When the plan definition was last reviewed."
    )
    effectivePeriod: FhirPeriodInput | None = Field(
        None,
        description="When the plan definition is expected to be used. Searched by `effective`.",
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
        description="Logic used by the plan definition (canonical(Library)). Searched by `depends-on`.",
    )
    goal: list[dict] | None = Field(
        None, description="What the plan is trying to accomplish (PlanDefinition.goal)."
    )
    action: list[dict] | None = Field(
        None,
        description="Action defined by the plan (PlanDefinition.action, a recursive tree). The `definitionCanonical` of every action, at any depth, is searched by `definition`.",
    )


class PlanDefinitionCreateSchema(_PlanDefinitionFields):
    """POST body - a FHIR R4 PlanDefinition resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class PlanDefinitionPatchSchema(_PlanDefinitionFields):
    """PATCH body - a partial FHIR R4 PlanDefinition (merge-patch semantics on top-level
    elements). Only supplied elements are written; omitted ones are left untouched. A supplied
    element replaces the stored value wholesale - a list (even `[]`) replaces every existing
    entry, an object replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {"status": "retired", "version": "1.1"},
        }
    }
