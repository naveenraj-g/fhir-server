from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirReferenceInput,
)

# GoalLifecycleStatus (the required binding of Goal.lifecycleStatus).
LifecycleStatus = Literal[
    "proposed",
    "planned",
    "accepted",
    "active",
    "on-hold",
    "completed",
    "cancelled",
    "entered-in-error",
    "rejected",
]

_EXAMPLE = {
    "resourceType": "Goal",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/goal-id",
            "value": "G-1",
        }
    ],
    "lifecycleStatus": "active",
    "achievementStatus": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/goal-achievement",
                "code": "in-progress",
            }
        ]
    },
    "category": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/goal-category",
                    "code": "dietary",
                }
            ]
        }
    ],
    "priority": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/goal-priority",
                "code": "high-priority",
            }
        ]
    },
    "description": {"text": "Reduce HbA1c below 7%"},
    "subject": {"reference": "Patient/10001"},
    "startDate": "2026-01-15",
    "target": [
        {
            "measure": {
                "coding": [
                    {
                        "system": "http://loinc.org",
                        "code": "4548-4",
                        "display": "Hemoglobin A1c",
                    }
                ]
            },
            "detailQuantity": {"value": 7, "comparator": "<", "unit": "%"},
            "dueDate": "2026-12-31",
        }
    ],
    "statusDate": "2026-01-15",
    "expressedBy": {"reference": "Patient/10001"},
    "note": [{"text": "Agreed with the patient."}],
}


class GoalTargetInput(FhirInputModel):
    """Goal.target - the target outcome for the goal."""

    measure: FhirCodeableConceptInput | None = Field(
        None,
        description="The parameter whose value is being tracked (required by R4 when `detail[x]` is present - rule gol-1, enforced by the `java_validator` backend).",
    )
    detailQuantity: dict | None = Field(None, description="detail[x]: a Quantity.")
    detailRange: dict | None = Field(None, description="detail[x]: a Range.")
    detailCodeableConcept: FhirCodeableConceptInput | None = Field(
        None, description="detail[x]: a CodeableConcept."
    )
    detailString: str | None = Field(None, description="detail[x]: a string.")
    detailBoolean: bool | None = Field(None, description="detail[x]: a boolean.")
    detailInteger: int | None = Field(None, description="detail[x]: an integer.")
    detailRatio: dict | None = Field(None, description="detail[x]: a Ratio.")
    dueDate: str | None = Field(
        None,
        description="due[x]: reach goal on this date (a FHIR date). Searched by `target-date`.",
    )
    dueDuration: dict | None = Field(
        None, description="due[x]: reach goal within this Duration (not searchable)."
    )


class _GoalFields(FhirInputModel):
    """Every writable Goal element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/goal.html). Create and patch accept exactly the same fields.
    R4 requires `lifecycleStatus`, `description` and `subject` (the native validator checks
    `description` and `subject`; the rest of the minimums and rule gol-1 are only enforced by the `java_validator`
    backend).

    The validated body is stored whole (GoalModel.content), so any valid R4 element is kept -
    including ones this model does not declare. Server-managed elements are ignored if sent:
    `id` (assigned from the goal_id sequence) and `meta` (audit/tenant data, stamped on at read
    time). org_id and created_by/updated_by come from the verified JWT (actor.org_id /
    actor.sub), never the body. There is no user_id."""

    resourceType: Literal["Goal"] | None = Field(
        None, description="Optional; if supplied it must be 'Goal'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries - validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="External ids for this goal. Searched by `identifier`."
    )
    lifecycleStatus: LifecycleStatus | None = Field(
        None,
        description="proposed | planned | accepted | active | on-hold | completed | cancelled | entered-in-error | rejected (required by R4). Searched by `lifecycle-status`.",
    )
    achievementStatus: FhirCodeableConceptInput | None = Field(
        None,
        description="in-progress | improving | worsening | no-change | achieved | sustaining | not-achieved | no-progress | not-attainable. Searched by `achievement-status`.",
    )
    category: list[FhirCodeableConceptInput] | None = Field(
        None,
        description="E.g. Treatment, dietary, behavioral, etc. Searched by `category`.",
    )
    priority: FhirCodeableConceptInput | None = Field(
        None, description="high-priority | medium-priority | low-priority."
    )
    description: FhirCodeableConceptInput | None = Field(
        None, description="Code or text describing the goal (required by R4)."
    )
    subject: FhirReferenceInput | None = Field(
        None,
        description="Who this goal is intended for - Reference(Patient | Group | Organization) (required by R4). A relative reference to a rebuilt resource must exist in the caller's org (422 otherwise). Searched by `subject` / `patient`.",
    )
    startDate: str | None = Field(
        None,
        description="start[x]: when goal pursuit begins (a FHIR date). Searched by `start-date`.",
    )
    startCodeableConcept: FhirCodeableConceptInput | None = Field(
        None, description="start[x]: reference point for the goal, as a concept."
    )
    target: list[GoalTargetInput] | None = Field(
        None, description="Target outcome for the goal."
    )
    statusDate: str | None = Field(
        None, description="When the goal status took effect (a FHIR date)."
    )
    statusReason: str | None = Field(None, description="Reason for the current status.")
    expressedBy: FhirReferenceInput | None = Field(
        None,
        description="Who is responsible for creating the goal - Reference(Patient | Practitioner | PractitionerRole | RelatedPerson).",
    )
    addresses: list[FhirReferenceInput] | None = Field(
        None,
        description="Issues addressed by this goal - Reference(Condition | Observation | MedicationStatement | NutritionOrder | ServiceRequest | RiskAssessment).",
    )
    note: list[dict] | None = Field(
        None, description="Comments about the goal (Annotation)."
    )
    outcomeCode: list[FhirCodeableConceptInput] | None = Field(
        None, description="What result was achieved regarding the goal."
    )
    outcomeReference: list[FhirReferenceInput] | None = Field(
        None,
        description="Observation that resulted from goal - Reference(Observation).",
    )


class GoalCreateSchema(_GoalFields):
    """POST body - a FHIR R4 Goal resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class GoalPatchSchema(_GoalFields):
    """PATCH body - a partial FHIR R4 Goal (merge-patch semantics on top-level elements). Only
    supplied elements are written; omitted ones are left untouched. A supplied element replaces
    the stored value wholesale - a list (even `[]`) replaces every existing entry, an object
    replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "lifecycleStatus": "completed",
                "achievementStatus": {"text": "achieved"},
            }
        }
    }
