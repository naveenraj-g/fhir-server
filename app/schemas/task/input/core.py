from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

# TaskStatus / TaskIntent / RequestPriority (the required bindings of Task.status, .intent and
# .priority).
StatusCode = Literal[
    "draft",
    "requested",
    "received",
    "accepted",
    "rejected",
    "ready",
    "cancelled",
    "in-progress",
    "on-hold",
    "failed",
    "completed",
    "entered-in-error",
]
IntentCode = Literal[
    "unknown",
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
    "resourceType": "Task",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/task-id",
            "value": "T-1",
        }
    ],
    "status": "requested",
    "intent": "order",
    "priority": "routine",
    "code": {
        "coding": [
            {"system": "http://hl7.org/fhir/CodeSystem/task-code", "code": "fulfill"}
        ]
    },
    "description": "Collect a blood sample",
    "focus": {"reference": "ServiceRequest/80001"},
    "for": {"reference": "Patient/10001"},
    "encounter": {"reference": "Encounter/20001"},
    "authoredOn": "2026-01-15T09:00:00Z",
    "requester": {"reference": "Practitioner/30001"},
    "owner": {"reference": "Practitioner/30001"},
    "restriction": {"repetitions": 1, "period": {"end": "2026-02-15T00:00:00Z"}},
    "input": [
        {"type": {"text": "sample type"}, "valueString": "venous blood"},
    ],
}


class TaskRestrictionInput(FhirInputModel):
    """Task.restriction - constraints on fulfillment tasks."""

    repetitions: int | None = Field(
        None, description="How many times to repeat (a positiveInt)."
    )
    period: FhirPeriodInput | None = Field(
        None, description="When fulfillment is sought."
    )
    recipient: list[FhirReferenceInput] | None = Field(
        None,
        description="For whom is fulfillment sought - Reference(Patient | Practitioner | PractitionerRole | RelatedPerson | Group | Organization).",
    )


class TaskInputInput(FhirInputModel):
    """Task.input - information used to perform the task. `value[x]` is an open choice of fifty
    types (valueString, valueBoolean, valueQuantity, valueReference, ...), sent and kept as is."""

    type: FhirCodeableConceptInput | None = Field(
        None, description="Label for the input (required by R4)."
    )


class TaskOutputInput(FhirInputModel):
    """Task.output - information produced as part of the task. `value[x]` is an open choice of
    fifty types, sent and kept as is."""

    type: FhirCodeableConceptInput | None = Field(
        None, description="Label for the output (required by R4)."
    )


class _TaskFields(FhirInputModel):
    """Every writable Task element, in genuine FHIR R4 shape (https://www.hl7.org/fhir/R4/task.html).
    Create and patch accept exactly the same fields. R4 requires `status` and `intent` (a missing
    one is only rejected by the `java_validator` backend, along with each `input` / `output`'s
    `type` and `value[x]` and rule inv-1: `lastModified` not before `authoredOn`).

    The validated body is stored whole (TaskModel.content), so any valid R4 element is kept -
    including ones this model does not declare (every `input.value[x]` / `output.value[x]`).
    Server-managed elements are ignored if sent: `id` (assigned from the task_id sequence) and
    `meta` (audit/tenant data, stamped on at read time). org_id and created_by/updated_by come from
    the verified JWT (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["Task"] | None = Field(
        None, description="Optional; if supplied it must be 'Task'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries - validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="Task Instance Identifier. Searched by `identifier`."
    )
    instantiatesCanonical: str | None = Field(
        None,
        description="Formal definition of task (a canonical URL, ActivityDefinition).",
    )
    instantiatesUri: str | None = Field(
        None, description="Formal definition of task (a URI)."
    )
    basedOn: list[FhirReferenceInput] | None = Field(
        None,
        description="Request fulfilled by this task - Reference(Any). A relative reference to a rebuilt resource must exist in the caller's org (422 otherwise). Searched by `based-on`.",
    )
    groupIdentifier: FhirIdentifierInput | None = Field(
        None, description="Requisition or grouper id. Searched by `group-identifier`."
    )
    partOf: list[FhirReferenceInput] | None = Field(
        None,
        description="Composite task - Reference(Task). A relative reference must exist in the caller's org (422 otherwise). Searched by `part-of`.",
    )
    status: StatusCode | None = Field(
        None,
        description="draft | requested | received | accepted | rejected | ready | cancelled | in-progress | on-hold | failed | completed | entered-in-error (required by R4). Searched by `status`.",
    )
    statusReason: FhirCodeableConceptInput | None = Field(
        None, description="Reason for current status."
    )
    businessStatus: FhirCodeableConceptInput | None = Field(
        None,
        description="E.g. 'Specimen collected', 'IV prepped'. Searched by `business-status`.",
    )
    intent: IntentCode | None = Field(
        None,
        description="unknown | proposal | plan | order | original-order | reflex-order | filler-order | instance-order | option (required by R4). Searched by `intent`.",
    )
    priority: PriorityCode | None = Field(
        None, description="routine | urgent | asap | stat. Searched by `priority`."
    )
    code: FhirCodeableConceptInput | None = Field(
        None, description="Task Type. Searched by `code`."
    )
    description: str | None = Field(
        None, description="Human-readable explanation of task."
    )
    focus: FhirReferenceInput | None = Field(
        None,
        description="What task is acting on - Reference(Any). Searched by `focus`.",
    )
    for_: FhirReferenceInput | None = Field(
        None,
        alias="for",
        description="Beneficiary of the Task - Reference(Any). Searched by `subject` (and `patient` when it names a Patient).",
    )
    encounter: FhirReferenceInput | None = Field(
        None,
        description="Healthcare event during which this task originated - Reference(Encounter).",
    )
    executionPeriod: FhirPeriodInput | None = Field(
        None, description="Start and end time of execution. Searched by `period`."
    )
    authoredOn: str | None = Field(
        None,
        description="Task Creation Date (a FHIR dateTime). Searched by `authored-on`.",
    )
    lastModified: str | None = Field(
        None,
        description="Task Last Modified Date (a FHIR dateTime). Searched by `modified`.",
    )
    requester: FhirReferenceInput | None = Field(
        None,
        description="Who is asking for task to be done - Reference(Device | Organization | Patient | Practitioner | PractitionerRole | RelatedPerson).",
    )
    performerType: list[FhirCodeableConceptInput] | None = Field(
        None,
        description="Requested performer (e.g. Requester, Performer, Scheduler). Searched by `performer`.",
    )
    owner: FhirReferenceInput | None = Field(
        None,
        description="Responsible individual - Reference(Practitioner | PractitionerRole | Organization | CareTeam | HealthcareService | Patient | Device | RelatedPerson).",
    )
    location: FhirReferenceInput | None = Field(
        None, description="Where task occurs - Reference(Location)."
    )
    reasonCode: FhirCodeableConceptInput | None = Field(
        None, description="Why task is needed."
    )
    reasonReference: FhirReferenceInput | None = Field(
        None, description="Why task is needed - Reference(Any)."
    )
    insurance: list[FhirReferenceInput] | None = Field(
        None,
        description="Associated insurance coverage - Reference(Coverage | ClaimResponse).",
    )
    note: list[dict] | None = Field(None, description="Comments made about the task.")
    relevantHistory: list[FhirReferenceInput] | None = Field(
        None, description="Key events in history of the Task - Reference(Provenance)."
    )
    restriction: TaskRestrictionInput | None = Field(
        None, description="Constraints on fulfillment tasks."
    )
    input: list[TaskInputInput] | None = Field(
        None, description="Information used to perform task."
    )
    output: list[TaskOutputInput] | None = Field(
        None, description="Information produced as part of task."
    )


class TaskCreateSchema(_TaskFields):
    """POST body - a FHIR R4 Task resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class TaskPatchSchema(_TaskFields):
    """PATCH body - a partial FHIR R4 Task (merge-patch semantics on top-level elements). Only
    supplied elements are written; omitted ones are left untouched. A supplied element replaces
    the stored value wholesale - a list (even `[]`) replaces every existing entry, an object
    replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "completed",
                "businessStatus": {"text": "Specimen collected"},
            }
        }
    }
