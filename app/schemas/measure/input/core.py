import datetime as dt
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import MeasureStatus
from app.schemas.measure.input.codeable_concept import MeasureCodeableConceptInput
from app.schemas.measure.input.contact import MeasureContactInput
from app.schemas.measure.input.group import MeasureGroupInput
from app.schemas.measure.input.identifier import MeasureIdentifierInput
from app.schemas.measure.input.related_artifact import MeasureRelatedArtifactInput
from app.schemas.measure.input.supplemental_data import MeasureSupplementalDataInput
from app.schemas.measure.input.use_context import MeasureUseContextInput


class MeasureCreateSchema(BaseModel):
    """Payload to create a new Measure resource."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "url": "http://example.org/fhir/Measure/exclusive-breastfeeding-measure",
                "version": "1.0.0",
                "name": "ExclusiveBreastfeedingMeasure",
                "title": "Exclusive Breastfeeding Measure",
                "status": "draft",
                "experimental": True,
                "description": "Exclusive breastfeeding measure for newborns during birth stay.",
                "group": [
                    {
                        "description": "Initial Population, Denominator, Numerator",
                        "population": [
                            {
                                "code": {
                                    "coding": [
                                        {
                                            "system": "http://terminology.hl7.org/CodeSystem/measure-population",
                                            "code": "initial-population",
                                            "display": "Initial Population",
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
        },
    )

    extension: list[dict[str, Any]] | None = Field(
        None, description="May be used to represent additional information."
    )
    url: str | None = Field(None, description="Canonical identifier for this measure, represented as a URI.")
    identifier: list[MeasureIdentifierInput] | None = Field(
        None, description="Additional identifier for the measure."
    )
    version: str | None = Field(None, description="Business version of the measure.")
    name: str | None = Field(None, description="Name for this measure (computer friendly).")
    title: str | None = Field(None, description="Name for this measure (human friendly).")
    subtitle: str | None = Field(None, description="Subordinate title of the measure.")
    status: MeasureStatus = Field(..., description="draft | active | retired | unknown.")
    experimental: bool | None = Field(None, description="For testing purposes, not real usage.")

    # subject[x] (CodeableConcept | Reference(Group))
    subject_codeable_concept: MeasureCodeableConceptInput | None = Field(
        None, description="E.g. Patient, Practitioner, RelatedPerson, Location."
    )
    subject_reference: str | None = Field(
        None, description="Reference to Group definition (e.g. 'Group/101')."
    )
    subject_reference_display: str | None = Field(
        None, description="Text alternative for the subject reference."
    )

    date: dt.datetime | None = Field(None, description="Date last changed.")
    publisher: str | None = Field(None, description="Name of the publisher (organization or individual).")
    contact: list[MeasureContactInput] | None = Field(
        None, description="Contact details for the publisher."
    )
    description: str | None = Field(None, description="Natural language description of the measure.")
    use_context: list[MeasureUseContextInput] | None = Field(
        None, description="The context that the content is intended to support."
    )
    jurisdiction: list[MeasureCodeableConceptInput] | None = Field(
        None, description="Intended jurisdiction for measure (e.g. country)."
    )
    purpose: str | None = Field(None, description="Why this measure is defined.")
    usage: str | None = Field(None, description="Describes the clinical usage of the measure.")
    copyright: str | None = Field(None, description="Use and/or publishing restrictions.")
    approval_date: dt.date | None = Field(None, description="When the measure was approved by publisher.")
    last_review_date: dt.date | None = Field(None, description="When the measure was last reviewed.")
    effective_period_start: dt.datetime | None = Field(
        None, description="When the measure is expected to be used (start)."
    )
    effective_period_end: dt.datetime | None = Field(
        None, description="When the measure is expected to be used (end)."
    )
    topic: list[MeasureCodeableConceptInput] | None = Field(
        None, description="The category of the measure, such as ACC, AHA, etc."
    )
    author: list[MeasureContactInput] | None = Field(
        None, description="Who authored the content."
    )
    editor: list[MeasureContactInput] | None = Field(
        None, description="Who edited the content."
    )
    reviewer: list[MeasureContactInput] | None = Field(
        None, description="Who reviewed the content."
    )
    endorser: list[MeasureContactInput] | None = Field(
        None, description="Who endorsed the content."
    )
    related_artifact: list[MeasureRelatedArtifactInput] | None = Field(
        None, description="Additional documentation, citations, etc."
    )
    library: list[str] | None = Field(
        None, description="Logic used by the measure (canonical references)."
    )
    disclaimer: str | None = Field(None, description="Disclaimer for use of the measure.")
    scoring: MeasureCodeableConceptInput | None = Field(
        None, description="proportion | ratio | continuous-variable | cohort."
    )
    composite_scoring: MeasureCodeableConceptInput | None = Field(
        None, description="opportunity | all-or-nothing | linear | weighted."
    )
    type: list[MeasureCodeableConceptInput] | None = Field(
        None, description="process | outcome | structure | process | composite."
    )
    risk_adjustment: str | None = Field(None, description="How risk adjustment is applied for this measure.")
    rate_aggregation: str | None = Field(None, description="How rate aggregation is performed for this measure.")
    rationale: str | None = Field(None, description="Detailed description of rationale for measure.")
    clinical_recommendation_statement: str | None = Field(
        None, description="Summary of clinical guidelines or recommendations."
    )
    improvement_notation: MeasureCodeableConceptInput | None = Field(
        None, description="Increased score indicates improvement / Decreased score indicates improvement."
    )
    definition: list[str] | None = Field(
        None, description="Defined terms used in the measure documentation."
    )
    guidance: str | None = Field(None, description="Additional guidance for implementers.")
    group: list[MeasureGroupInput] | None = Field(
        None, description="What groups are in the measure."
    )
    supplemental_data: list[MeasureSupplementalDataInput] | None = Field(
        None, description="What other data should be reported with the measure."
    )


class MeasurePatchSchema(BaseModel):
    """Payload to patch an existing Measure resource. All fields optional."""

    model_config = ConfigDict(extra="forbid")

    extension: list[dict[str, Any]] | None = None
    url: str | None = None
    identifier: list[MeasureIdentifierInput] | None = None
    version: str | None = None
    name: str | None = None
    title: str | None = None
    subtitle: str | None = None
    status: MeasureStatus | None = None
    experimental: bool | None = None

    subject_codeable_concept: MeasureCodeableConceptInput | None = None
    subject_reference: str | None = None
    subject_reference_display: str | None = None

    date: dt.datetime | None = None
    publisher: str | None = None
    contact: list[MeasureContactInput] | None = None
    description: str | None = None
    use_context: list[MeasureUseContextInput] | None = None
    jurisdiction: list[MeasureCodeableConceptInput] | None = None
    purpose: str | None = None
    usage: str | None = None
    copyright: str | None = None
    approval_date: dt.date | None = None
    last_review_date: dt.date | None = None
    effective_period_start: dt.datetime | None = None
    effective_period_end: dt.datetime | None = None
    topic: list[MeasureCodeableConceptInput] | None = None
    author: list[MeasureContactInput] | None = None
    editor: list[MeasureContactInput] | None = None
    reviewer: list[MeasureContactInput] | None = None
    endorser: list[MeasureContactInput] | None = None
    related_artifact: list[MeasureRelatedArtifactInput] | None = None
    library: list[str] | None = None
    disclaimer: str | None = None
    scoring: MeasureCodeableConceptInput | None = None
    composite_scoring: MeasureCodeableConceptInput | None = None
    type: list[MeasureCodeableConceptInput] | None = None
    risk_adjustment: str | None = None
    rate_aggregation: str | None = None
    rationale: str | None = None
    clinical_recommendation_statement: str | None = None
    improvement_notation: MeasureCodeableConceptInput | None = None
    definition: list[str] | None = None
    guidance: str | None = None
    group: list[MeasureGroupInput] | None = None
    supplemental_data: list[MeasureSupplementalDataInput] | None = None
