import datetime as dt

from pydantic import BaseModel, ConfigDict, Field

from app.models.activity_definition.enums import (
    ActivityDefinitionIntent,
    ActivityDefinitionKind,
    ActivityDefinitionPriority,
    ActivityDefinitionQuantityComparator,
    ActivityDefinitionStatus,
)
from app.schemas.activity_definition.input.codeable_concept import (
    ActivityDefinitionCodeableConceptInput,
)
from app.schemas.activity_definition.input.contact import ActivityDefinitionContactInput
from app.schemas.activity_definition.input.dosage import ActivityDefinitionDosageInput
from app.schemas.activity_definition.input.dynamic_value import (
    ActivityDefinitionDynamicValueInput,
)
from app.schemas.activity_definition.input.identifier import (
    ActivityDefinitionIdentifierInput,
)
from app.schemas.activity_definition.input.participant import (
    ActivityDefinitionParticipantInput,
)
from app.schemas.activity_definition.input.related_artifact import (
    ActivityDefinitionRelatedArtifactInput,
)
from app.schemas.activity_definition.input.use_context import (
    ActivityDefinitionUseContextInput,
)


class ActivityDefinitionCreateSchema(BaseModel):
    """Request body for creating an ActivityDefinition resource."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "status": "draft",
                "name": "BloodGlucoseMonitoringActivity",
                "title": "Blood Glucose Monitoring Activity",
                "kind": "ServiceRequest",
                "code": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "35335000",
                            "display": "Blood glucose measurement",
                        }
                    ],
                    "text": "Blood glucose measurement",
                },
                "intent": "order",
                "priority": "routine",
                "do_not_perform": False,
            }
        },
    )

    url: str | None = Field(None, description="Canonical identifier for this activity definition.")
    identifier: list[ActivityDefinitionIdentifierInput] | None = Field(
        None, description="Additional identifier for the activity definition."
    )
    version: str | None = Field(None, description="Business version of the activity definition.")
    name: str | None = Field(None, description="Name for this activity definition (computer friendly).")
    title: str | None = Field(None, description="Name for this activity definition (human friendly).")
    subtitle: str | None = Field(None, description="Sub-title of the activity definition.")
    status: ActivityDefinitionStatus = Field(
        ...,
        description="draft | active | retired | unknown (PublicationStatus).",
    )
    experimental: bool | None = Field(None, description="For testing purposes, not real usage.")
    date: dt.datetime | None = Field(None, description="Date last changed.")
    publisher: str | None = Field(None, description="Name of the publisher/organization.")
    contact: list[ActivityDefinitionContactInput] | None = Field(
        None, description="Contact details for the publisher."
    )
    description: str | None = Field(None, description="Natural language description of the activity definition.")
    use_context: list[ActivityDefinitionUseContextInput] | None = Field(
        None, description="The context that the content is intended to support."
    )
    jurisdiction: list[ActivityDefinitionCodeableConceptInput] | None = Field(
        None, description="Intended jurisdiction for activity definition."
    )
    purpose: str | None = Field(None, description="Why this activity definition is defined.")
    usage: str | None = Field(None, description="Describes how the definition is intended to be used.")
    copyright: str | None = Field(None, description="Use and/or publishing rights.")
    approval_date: dt.date | None = Field(None, description="When the activity definition was approved by publisher.")
    last_review_date: dt.date | None = Field(None, description="When the activity definition was last reviewed.")
    effective_period_start: dt.datetime | None = Field(None, description="When the activity definition is expected to be used (start).")
    effective_period_end: dt.datetime | None = Field(None, description="When the activity definition is expected to be used (end).")
    topic: list[ActivityDefinitionCodeableConceptInput] | None = Field(
        None, description="E.g. treatment, education, assessment, etc."
    )
    author: list[ActivityDefinitionContactInput] | None = Field(None, description="Who authored the content.")
    editor: list[ActivityDefinitionContactInput] | None = Field(None, description="Who edited the content.")
    reviewer: list[ActivityDefinitionContactInput] | None = Field(None, description="Who reviewed the content.")
    endorser: list[ActivityDefinitionContactInput] | None = Field(None, description="Who endorsed the content.")
    related_artifact: list[ActivityDefinitionRelatedArtifactInput] | None = Field(
        None, description="Additional documentation, citations, etc."
    )
    library: list[str] | None = Field(None, description="Logic framework used by the activity definition.")
    kind: ActivityDefinitionKind | None = Field(
        None, description="Kind of activity (ServiceRequest, MedicationRequest, etc.)."
    )
    profile: str | None = Field(None, description="What profile the resulting resource conforms to.")
    code: ActivityDefinitionCodeableConceptInput | None = Field(
        None, description="Detail type of activity."
    )
    intent: ActivityDefinitionIntent | None = Field(
        None, description="proposal | plan | directive | order | original-order | reflex-order | filler-order | instance-order | option."
    )
    priority: ActivityDefinitionPriority | None = Field(
        None, description="routine | urgent | asap | stat."
    )
    do_not_perform: bool | None = Field(None, description="True if the activity should not be performed.")

    # timing[x]
    timing_timing: dict | None = Field(None, description="When activity is to occur (Timing).")
    timing_date_time: dt.datetime | None = Field(None, description="When activity is to occur (dateTime).")
    timing_age_value: float | None = Field(None, description="When activity is to occur (Age value).")
    timing_age_unit: str | None = Field(None, description="When activity is to occur (Age unit).")
    timing_age_system: str | None = Field(None, description="When activity is to occur (Age system).")
    timing_age_code: str | None = Field(None, description="When activity is to occur (Age code).")
    timing_period_start: dt.datetime | None = Field(None, description="When activity is to occur (Period start).")
    timing_period_end: dt.datetime | None = Field(None, description="When activity is to occur (Period end).")
    timing_range_low_value: float | None = Field(None, description="When activity is to occur (Range low value).")
    timing_range_low_unit: str | None = Field(None, description="When activity is to occur (Range low unit).")
    timing_range_high_value: float | None = Field(None, description="When activity is to occur (Range high value).")
    timing_range_high_unit: str | None = Field(None, description="When activity is to occur (Range high unit).")
    timing_duration_value: float | None = Field(None, description="When activity is to occur (Duration value).")
    timing_duration_unit: str | None = Field(None, description="When activity is to occur (Duration unit).")
    timing_duration_system: str | None = Field(None, description="When activity is to occur (Duration system).")
    timing_duration_code: str | None = Field(None, description="When activity is to occur (Duration code).")

    location: str | None = Field(None, description="Where it should happen (Location/123).")
    location_display: str | None = Field(None, description="Location display text.")
    participant: list[ActivityDefinitionParticipantInput] | None = Field(
        None, description="Who should participate in the action."
    )
    product_codeable_concept: ActivityDefinitionCodeableConceptInput | None = Field(
        None, description="What product is used (CodeableConcept)."
    )
    product_reference: str | None = Field(None, description="What product is used (Medication/123 | Substance/123).")
    product_display: str | None = Field(None, description="Product display text.")
    quantity_value: float | None = Field(None, description="How much is required/consumed (value).")
    quantity_comparator: ActivityDefinitionQuantityComparator | None = Field(None, description="Quantity comparator.")
    quantity_unit: str | None = Field(None, description="Quantity unit.")
    quantity_system: str | None = Field(None, description="Quantity unit system.")
    quantity_code: str | None = Field(None, description="Quantity coded form.")
    dosage: list[ActivityDefinitionDosageInput] | None = Field(
        None, description="Detailed dosage instructions."
    )
    body_site: list[ActivityDefinitionCodeableConceptInput] | None = Field(
        None, description="What part of body to perform on."
    )
    specimen_requirement: list[str] | None = Field(
        None, description="What specimens are required (SpecimenDefinition/123)."
    )
    observation_requirement: list[str] | None = Field(
        None, description="What observation results are required (ObservationDefinition/123)."
    )
    observation_result_requirement: list[str] | None = Field(
        None, description="What observation results are produced (ObservationDefinition/123)."
    )
    transform: str | None = Field(None, description="Transform to advance the activity.")
    dynamic_value: list[ActivityDefinitionDynamicValueInput] | None = Field(
        None, description="Dynamic aspects of the definition."
    )

    # subject[x]
    subject_codeable_concept: ActivityDefinitionCodeableConceptInput | None = Field(
        None, description="Type of subject for the activity (CodeableConcept)."
    )
    subject_reference: str | None = Field(None, description="Type of subject for the activity (Group/123).")
    subject_display: str | None = Field(None, description="Subject display text.")

    extension: list[dict] | None = Field(None, description="Additional content defined by implementations.")


class ActivityDefinitionPatchSchema(BaseModel):
    """Request body for updating an ActivityDefinition resource."""

    model_config = ConfigDict(extra="forbid")

    url: str | None = Field(None, description="Canonical identifier for this activity definition.")
    identifier: list[ActivityDefinitionIdentifierInput] | None = Field(
        None, description="Additional identifier for the activity definition."
    )
    version: str | None = Field(None, description="Business version of the activity definition.")
    name: str | None = Field(None, description="Name for this activity definition (computer friendly).")
    title: str | None = Field(None, description="Name for this activity definition (human friendly).")
    subtitle: str | None = Field(None, description="Sub-title of the activity definition.")
    status: ActivityDefinitionStatus | None = Field(
        None, description="draft | active | retired | unknown (PublicationStatus)."
    )
    experimental: bool | None = Field(None, description="For testing purposes, not real usage.")
    date: dt.datetime | None = Field(None, description="Date last changed.")
    publisher: str | None = Field(None, description="Name of the publisher/organization.")
    contact: list[ActivityDefinitionContactInput] | None = Field(
        None, description="Contact details for the publisher."
    )
    description: str | None = Field(None, description="Natural language description of the activity definition.")
    use_context: list[ActivityDefinitionUseContextInput] | None = Field(
        None, description="The context that the content is intended to support."
    )
    jurisdiction: list[ActivityDefinitionCodeableConceptInput] | None = Field(
        None, description="Intended jurisdiction for activity definition."
    )
    purpose: str | None = Field(None, description="Why this activity definition is defined.")
    usage: str | None = Field(None, description="Describes how the definition is intended to be used.")
    copyright: str | None = Field(None, description="Use and/or publishing rights.")
    approval_date: dt.date | None = Field(None, description="When the activity definition was approved by publisher.")
    last_review_date: dt.date | None = Field(None, description="When the activity definition was last reviewed.")
    effective_period_start: dt.datetime | None = Field(None, description="When the activity definition is expected to be used (start).")
    effective_period_end: dt.datetime | None = Field(None, description="When the activity definition is expected to be used (end).")
    topic: list[ActivityDefinitionCodeableConceptInput] | None = Field(
        None, description="E.g. treatment, education, assessment, etc."
    )
    author: list[ActivityDefinitionContactInput] | None = Field(None, description="Who authored the content.")
    editor: list[ActivityDefinitionContactInput] | None = Field(None, description="Who edited the content.")
    reviewer: list[ActivityDefinitionContactInput] | None = Field(None, description="Who reviewed the content.")
    endorser: list[ActivityDefinitionContactInput] | None = Field(None, description="Who endorsed the content.")
    related_artifact: list[ActivityDefinitionRelatedArtifactInput] | None = Field(
        None, description="Additional documentation, citations, etc."
    )
    library: list[str] | None = Field(None, description="Logic framework used by the activity definition.")
    kind: ActivityDefinitionKind | None = Field(
        None, description="Kind of activity (ServiceRequest, MedicationRequest, etc.)."
    )
    profile: str | None = Field(None, description="What profile the resulting resource conforms to.")
    code: ActivityDefinitionCodeableConceptInput | None = Field(
        None, description="Detail type of activity."
    )
    intent: ActivityDefinitionIntent | None = Field(
        None, description="proposal | plan | directive | order | original-order | reflex-order | filler-order | instance-order | option."
    )
    priority: ActivityDefinitionPriority | None = Field(
        None, description="routine | urgent | asap | stat."
    )
    do_not_perform: bool | None = Field(None, description="True if the activity should not be performed.")

    # timing[x]
    timing_timing: dict | None = Field(None, description="When activity is to occur (Timing).")
    timing_date_time: dt.datetime | None = Field(None, description="When activity is to occur (dateTime).")
    timing_age_value: float | None = Field(None, description="When activity is to occur (Age value).")
    timing_age_unit: str | None = Field(None, description="When activity is to occur (Age unit).")
    timing_age_system: str | None = Field(None, description="When activity is to occur (Age system).")
    timing_age_code: str | None = Field(None, description="When activity is to occur (Age code).")
    timing_period_start: dt.datetime | None = Field(None, description="When activity is to occur (Period start).")
    timing_period_end: dt.datetime | None = Field(None, description="When activity is to occur (Period end).")
    timing_range_low_value: float | None = Field(None, description="When activity is to occur (Range low value).")
    timing_range_low_unit: str | None = Field(None, description="When activity is to occur (Range low unit).")
    timing_range_high_value: float | None = Field(None, description="When activity is to occur (Range high value).")
    timing_range_high_unit: str | None = Field(None, description="When activity is to occur (Range high unit).")
    timing_duration_value: float | None = Field(None, description="When activity is to occur (Duration value).")
    timing_duration_unit: str | None = Field(None, description="When activity is to occur (Duration unit).")
    timing_duration_system: str | None = Field(None, description="When activity is to occur (Duration system).")
    timing_duration_code: str | None = Field(None, description="When activity is to occur (Duration code).")

    location: str | None = Field(None, description="Where it should happen (Location/123).")
    location_display: str | None = Field(None, description="Location display text.")
    participant: list[ActivityDefinitionParticipantInput] | None = Field(
        None, description="Who should participate in the action."
    )
    product_codeable_concept: ActivityDefinitionCodeableConceptInput | None = Field(
        None, description="What product is used (CodeableConcept)."
    )
    product_reference: str | None = Field(None, description="What product is used (Medication/123 | Substance/123).")
    product_display: str | None = Field(None, description="Product display text.")
    quantity_value: float | None = Field(None, description="How much is required/consumed (value).")
    quantity_comparator: ActivityDefinitionQuantityComparator | None = Field(None, description="Quantity comparator.")
    quantity_unit: str | None = Field(None, description="Quantity unit.")
    quantity_system: str | None = Field(None, description="Quantity unit system.")
    quantity_code: str | None = Field(None, description="Quantity coded form.")
    dosage: list[ActivityDefinitionDosageInput] | None = Field(
        None, description="Detailed dosage instructions."
    )
    body_site: list[ActivityDefinitionCodeableConceptInput] | None = Field(
        None, description="What part of body to perform on."
    )
    specimen_requirement: list[str] | None = Field(
        None, description="What specimens are required (SpecimenDefinition/123)."
    )
    observation_requirement: list[str] | None = Field(
        None, description="What observation results are required (ObservationDefinition/123)."
    )
    observation_result_requirement: list[str] | None = Field(
        None, description="What observation results are produced (ObservationDefinition/123)."
    )
    transform: str | None = Field(None, description="Transform to advance the activity.")
    dynamic_value: list[ActivityDefinitionDynamicValueInput] | None = Field(
        None, description="Dynamic aspects of the definition."
    )

    # subject[x]
    subject_codeable_concept: ActivityDefinitionCodeableConceptInput | None = Field(
        None, description="Type of subject for the activity (CodeableConcept)."
    )
    subject_reference: str | None = Field(None, description="Type of subject for the activity (Group/123).")
    subject_display: str | None = Field(None, description="Subject display text.")

    extension: list[dict] | None = Field(None, description="Additional content defined by implementations.")
