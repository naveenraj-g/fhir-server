from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import IdentifierUse
from app.models.task.enums import (
    TaskIntent,
    TaskPriority,
    TaskStatus,
)
from app.schemas.datatypes import CodingInput

from .identifier import TaskIdentifierInput
from .io import TaskInputInput, TaskOutputInput
from .note import TaskNoteInput
from .performer_type import TaskPerformerTypeInput
from .reference import TaskReferenceInput
from .restriction import TaskRestrictionInput

_EXAMPLE = {
    "status": "requested",
    "intent": "order",
    "priority": "routine",
    "code_coding": [
        {
            "system": "http://hl7.org/fhir/CodeSystem/task-code",
            "code": "approve",
            "display": "Activate/approve the focal resource",
        }
    ],
    "code_text": "Approve medication request",
    "description": "Please review and approve the medication order.",
    "for": "Patient/10001",
    "for_display": "Jane Doe",
    "encounter": "Encounter/20001",
    "encounter_display": "Outpatient consultation",
    "authored_on": "2026-01-01T12:00:00Z",
    "last_modified": "2026-01-01T12:00:00Z",
    "requester": "Practitioner/30001",
    "requester_display": "Dr. Alice Smith",
    "owner": "Practitioner/30002",
    "owner_display": "Dr. Bob Jones",
    "execution_period_start": "2026-01-01T12:00:00Z",
    "execution_period_end": "2026-01-02T12:00:00Z",
}


class TaskCreateSchema(BaseModel):
    """Request body for POST /api/fhir/v1/tasks.

    Task is an org-scoped entity and has no user_id.
    status and intent are required (1..1) per FHIR R4.
    """

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={"example": _EXAMPLE},
    )

    identifier: list[TaskIdentifierInput] | None = Field(
        None, description="Task Instance Identifier."
    )
    instantiates_canonical: str | None = Field(
        None, description="Formal definition of task (canonical(ActivityDefinition))."
    )
    instantiates_uri: str | None = Field(
        None, description="Formal definition of task (uri)."
    )
    based_on: list[TaskReferenceInput | str] | None = Field(
        None, description="Request fulfilled by this task (Reference(Any))."
    )
    group_identifier_use: IdentifierUse | None = Field(
        None, description="Group identifier use."
    )
    group_identifier_system: str | None = Field(
        None, description="Group identifier system."
    )
    group_identifier_value: str | None = Field(
        None, description="Group identifier value."
    )
    group_identifier_period_start: datetime | None = Field(
        None, description="Group identifier validity start."
    )
    group_identifier_period_end: datetime | None = Field(
        None, description="Group identifier validity end."
    )
    group_identifier_assigner: str | None = Field(
        None, description="Group identifier assigner reference."
    )
    group_identifier_assigner_display: str | None = Field(
        None, description="Group identifier assigner display."
    )
    part_of: list[TaskReferenceInput | str] | None = Field(
        None, description="Composite task (Reference(Task))."
    )
    status: TaskStatus = Field(
        ...,
        description="draft | requested | received | accepted | rejected | ready | cancelled | in-progress | on-hold | failed | completed | entered-in-error.",
    )
    status_reason_coding: list[CodingInput] | None = Field(
        None, description="Reason for current status codings."
    )
    status_reason_text: str | None = Field(
        None, description="Reason for current status text."
    )
    business_status_coding: list[CodingInput] | None = Field(
        None, description="E.g. 'Waiting on review', 'Deferred' codings."
    )
    business_status_text: str | None = Field(
        None, description="E.g. 'Waiting on review', 'Deferred' text."
    )
    intent: TaskIntent = Field(
        ...,
        description="unknown | proposal | plan | order | original-order | reflex-order | filler-order | instance-order | option.",
    )
    priority: TaskPriority | None = Field(
        None, description="routine | urgent | asap | stat."
    )
    code_coding: list[CodingInput] | None = Field(
        None, description="Task Type codings."
    )
    code_text: str | None = Field(
        None, description="Task Type text description."
    )
    description: str | None = Field(
        None, description="Human-readable explanation of task."
    )
    focus: str | None = Field(
        None, description="What task is acting on (Reference(Any))."
    )
    focus_display: str | None = Field(
        None, description="Narrative for focus reference."
    )
    for_: str | None = Field(
        None,
        alias="for",
        description="Beneficiary of the task (Reference(Any)).",
    )
    for_display: str | None = Field(
        None, description="Narrative for beneficiary reference."
    )
    encounter: str | None = Field(
        None, description="Healthcare event during which task was created (Reference(Encounter))."
    )
    encounter_display: str | None = Field(
        None, description="Narrative for encounter reference."
    )
    execution_period_start: datetime | None = Field(
        None, description="Start of execution period."
    )
    execution_period_end: datetime | None = Field(
        None, description="End of execution period."
    )
    authored_on: datetime | None = Field(
        None, description="Task Creation Date."
    )
    last_modified: datetime | None = Field(
        None, description="Task Last Modified Date."
    )
    requester: str | None = Field(
        None,
        description="Who is asking for task to be done (Reference(Device|Organization|Patient|Practitioner|PractitionerRole|RelatedPerson)).",
    )
    requester_display: str | None = Field(
        None, description="Narrative for requester reference."
    )
    performer_type: list[TaskPerformerTypeInput] | None = Field(
        None, description="Requested performer normal role."
    )
    owner: str | None = Field(
        None,
        description="Responsible individual (Reference(Practitioner|PractitionerRole|Organization|CareTeam|HealthcareService|Patient|Device|RelatedPerson)).",
    )
    owner_display: str | None = Field(
        None, description="Narrative for owner reference."
    )
    location: str | None = Field(
        None, description="Where task occurs (Reference(Location))."
    )
    location_display: str | None = Field(
        None, description="Narrative for location reference."
    )
    reason_code_coding: list[CodingInput] | None = Field(
        None, description="Why task is needed codings."
    )
    reason_code_text: str | None = Field(
        None, description="Why task is needed text."
    )
    reason_reference: str | None = Field(
        None, description="Why task is needed reference (Reference(Any))."
    )
    reason_reference_display: str | None = Field(
        None, description="Narrative for reason reference."
    )
    insurance: list[TaskReferenceInput | str] | None = Field(
        None, description="Associated insurance coverage (Reference(Coverage|ClaimResponse))."
    )
    note: list[TaskNoteInput] | None = Field(
        None, description="Comments made about the task."
    )
    relevant_history: list[TaskReferenceInput | str] | None = Field(
        None, description="Key events in history of the task (Reference(Provenance))."
    )
    restriction: TaskRestrictionInput | None = Field(
        None, description="Constraints on task execution."
    )
    input: list[TaskInputInput] | None = Field(
        None, description="Information used to perform task."
    )
    output: list[TaskOutputInput] | None = Field(
        None, description="Information produced as part of task."
    )


class TaskPatchSchema(BaseModel):
    """Request body for PATCH /api/fhir/v1/tasks/{id}. All fields optional."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    identifier: list[TaskIdentifierInput] | None = None
    instantiates_canonical: str | None = None
    instantiates_uri: str | None = None
    based_on: list[TaskReferenceInput | str] | None = None
    group_identifier_use: IdentifierUse | None = None
    group_identifier_system: str | None = None
    group_identifier_value: str | None = None
    group_identifier_period_start: datetime | None = None
    group_identifier_period_end: datetime | None = None
    group_identifier_assigner: str | None = None
    group_identifier_assigner_display: str | None = None
    part_of: list[TaskReferenceInput | str] | None = None
    status: TaskStatus | None = None
    status_reason_coding: list[CodingInput] | None = None
    status_reason_text: str | None = None
    business_status_coding: list[CodingInput] | None = None
    business_status_text: str | None = None
    intent: TaskIntent | None = None
    priority: TaskPriority | None = None
    code_coding: list[CodingInput] | None = None
    code_text: str | None = None
    description: str | None = None
    focus: str | None = None
    focus_display: str | None = None
    for_: str | None = Field(None, alias="for")
    for_display: str | None = None
    encounter: str | None = None
    encounter_display: str | None = None
    execution_period_start: datetime | None = None
    execution_period_end: datetime | None = None
    authored_on: datetime | None = None
    last_modified: datetime | None = None
    requester: str | None = None
    requester_display: str | None = None
    performer_type: list[TaskPerformerTypeInput] | None = None
    owner: str | None = None
    owner_display: str | None = None
    location: str | None = None
    location_display: str | None = None
    reason_code_coding: list[CodingInput] | None = None
    reason_code_text: str | None = None
    reason_reference: str | None = None
    reason_reference_display: str | None = None
    insurance: list[TaskReferenceInput | str] | None = None
    note: list[TaskNoteInput] | None = None
    relevant_history: list[TaskReferenceInput | str] | None = None
    restriction: TaskRestrictionInput | None = None
    input: list[TaskInputInput] | None = None
    output: list[TaskOutputInput] | None = None
