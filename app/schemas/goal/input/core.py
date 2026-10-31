from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.goal.enums import GoalLifecycleStatus
from app.schemas.datatypes import CodingInput

from .category import GoalCategoryInput
from .identifier import GoalIdentifierInput
from .note import GoalNoteInput
from .reference import GoalReferenceInput
from .target import GoalTargetInput

_EXAMPLE = {
    "lifecycle_status": "active",
    "achievement_status_coding": [
        {
            "system": "http://terminology.hl7.org/CodeSystem/goal-achievement",
            "code": "in-progress",
            "display": "In Progress",
        }
    ],
    "achievement_status_text": "In Progress",
    "category": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/goal-category",
                    "code": "dietary",
                    "display": "Dietary",
                }
            ],
            "text": "Dietary",
        }
    ],
    "priority_coding": [
        {
            "system": "http://terminology.hl7.org/CodeSystem/goal-priority",
            "code": "high-priority",
            "display": "High Priority",
        }
    ],
    "priority_text": "High Priority",
    "description_coding": [
        {
            "system": "http://snomed.info/sct",
            "code": "281036007",
            "display": "Follow-up dietary regime",
        }
    ],
    "description_text": "Follow-up dietary regime",
    "subject": "Patient/10001",
    "subject_display": "Jane Doe",
    "start_date": "2026-01-01",
    "target": [
        {
            "measure_text": "Weight",
            "detail_quantity_value": 70,
            "detail_quantity_unit": "kg",
            "detail_quantity_system": "http://unitsofmeasure.org",
            "detail_quantity_code": "kg",
            "due_date": "2026-06-01",
        }
    ],
    "status_date": "2026-01-01",
    "status_reason": "Patient willing to adhere to diet",
    "expressed_by": "Practitioner/30001",
    "expressed_by_display": "Dr. Smith",
}


class GoalCreateSchema(BaseModel):
    """Request body for POST /api/fhir/v1/goals.

    Goal is an org-scoped clinical entity and has no user_id.
    lifecycle_status, description, and subject are required per FHIR R4.
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": _EXAMPLE},
    )

    identifier: list[GoalIdentifierInput] | None = Field(
        None, description="External Ids for this goal."
    )
    lifecycle_status: GoalLifecycleStatus = Field(
        ...,
        description="proposed | planned | accepted | active | on-hold | completed | cancelled | entered-in-error | rejected.",
    )
    achievement_status_coding: list[CodingInput] | None = Field(
        None, description="in-progress | improving | worsening | no-change | achieved | sustaining | not-achieved | no-progress | not-attainable."
    )
    achievement_status_text: str | None = Field(
        None, description="Plain text representation of achievement status."
    )
    category: list[GoalCategoryInput] | None = Field(
        None, description="E.g. Treatment, dietary, behavioral, etc."
    )
    priority_coding: list[CodingInput] | None = Field(
        None, description="high-priority | moderate-priority | low-priority."
    )
    priority_text: str | None = Field(
        None, description="Plain text representation of priority."
    )
    description_coding: list[CodingInput] | None = Field(
        None, description="Code describing the goal."
    )
    description_text: str | None = Field(
        None, description="Plain text describing the goal."
    )
    subject: str = Field(
        ...,
        description="Who this goal is intended for (Patient | Group | Organization).",
    )
    subject_display: str | None = Field(
        None, description="Plain text narrative for subject reference."
    )
    start_date: date | None = Field(
        None, description="When goal pursuit begins (as date)."
    )
    start_codeable_concept_coding: list[CodingInput] | None = Field(
        None, description="When goal pursuit begins (as CodeableConcept coding)."
    )
    start_codeable_concept_text: str | None = Field(
        None, description="When goal pursuit begins (as CodeableConcept text)."
    )
    target: list[GoalTargetInput] | None = Field(
        None, description="Target outcome for the goal."
    )
    status_date: date | None = Field(
        None, description="When goal status took effect."
    )
    status_reason: str | None = Field(
        None, description="Reason for current status (string per FHIR R4)."
    )
    expressed_by: str | None = Field(
        None,
        description="Who's responsible for creating Goal (Patient | Practitioner | PractitionerRole | RelatedPerson).",
    )
    expressed_by_display: str | None = Field(
        None, description="Plain text narrative for expressedBy reference."
    )
    addresses: list[GoalReferenceInput | str] | None = Field(
        None,
        description="Issues addressed by this goal (Condition | Observation | MedicationStatement | NutritionOrder | ServiceRequest | RiskAssessment).",
    )
    note: list[GoalNoteInput | str] | None = Field(
        None, description="Comments about the goal."
    )
    outcome_code: list[GoalCategoryInput] | None = Field(
        None, description="What result was achieved regarding the goal."
    )
    outcome_reference: list[GoalReferenceInput | str] | None = Field(
        None, description="Observation that resulted from goal (Reference(Observation))."
    )
    extension: list[dict] | None = Field(
        None, description="May be used to represent additional information that is not part of the basic definition."
    )

    @model_validator(mode="after")
    def validate_description_present(self) -> "GoalCreateSchema":
        if not self.description_text and not self.description_coding:
            raise ValueError(
                "Goal.description is required (at least description_text or description_coding must be provided)"
            )
        return self


class GoalPatchSchema(BaseModel):
    """Request body for PATCH /api/fhir/v1/goals/{goal_id}.

    All fields are optional. Excludes immutable fields (id, goal_id, org_id, created_at, created_by).
    """

    model_config = ConfigDict(extra="forbid")

    identifier: list[GoalIdentifierInput] | None = Field(
        None, description="External Ids for this goal."
    )
    lifecycle_status: GoalLifecycleStatus | None = Field(
        None,
        description="proposed | planned | accepted | active | on-hold | completed | cancelled | entered-in-error | rejected.",
    )
    achievement_status_coding: list[CodingInput] | None = Field(
        None, description="in-progress | improving | worsening | no-change | achieved | sustaining | not-achieved | no-progress | not-attainable."
    )
    achievement_status_text: str | None = Field(
        None, description="Plain text representation of achievement status."
    )
    category: list[GoalCategoryInput] | None = Field(
        None, description="E.g. Treatment, dietary, behavioral, etc."
    )
    priority_coding: list[CodingInput] | None = Field(
        None, description="high-priority | moderate-priority | low-priority."
    )
    priority_text: str | None = Field(
        None, description="Plain text representation of priority."
    )
    description_coding: list[CodingInput] | None = Field(
        None, description="Code describing the goal."
    )
    description_text: str | None = Field(
        None, description="Plain text describing the goal."
    )
    subject: str | None = Field(
        None,
        description="Who this goal is intended for (Patient | Group | Organization).",
    )
    subject_display: str | None = Field(
        None, description="Plain text narrative for subject reference."
    )
    start_date: date | None = Field(
        None, description="When goal pursuit begins (as date)."
    )
    start_codeable_concept_coding: list[CodingInput] | None = Field(
        None, description="When goal pursuit begins (as CodeableConcept coding)."
    )
    start_codeable_concept_text: str | None = Field(
        None, description="When goal pursuit begins (as CodeableConcept text)."
    )
    target: list[GoalTargetInput] | None = Field(
        None, description="Target outcome for the goal."
    )
    status_date: date | None = Field(
        None, description="When goal status took effect."
    )
    status_reason: str | None = Field(
        None, description="Reason for current status (string per FHIR R4)."
    )
    expressed_by: str | None = Field(
        None,
        description="Who's responsible for creating Goal (Patient | Practitioner | PractitionerRole | RelatedPerson).",
    )
    expressed_by_display: str | None = Field(
        None, description="Plain text narrative for expressedBy reference."
    )
    addresses: list[GoalReferenceInput | str] | None = Field(
        None,
        description="Issues addressed by this goal (Condition | Observation | MedicationStatement | NutritionOrder | ServiceRequest | RiskAssessment).",
    )
    note: list[GoalNoteInput | str] | None = Field(
        None, description="Comments about the goal."
    )
    outcome_code: list[GoalCategoryInput] | None = Field(
        None, description="What result was achieved regarding the goal."
    )
    outcome_reference: list[GoalReferenceInput | str] | None = Field(
        None, description="Observation that resulted from goal (Reference(Observation))."
    )
    extension: list[dict] | None = Field(
        None, description="May be used to represent additional information that is not part of the basic definition."
    )
