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
    group_identifier_assigner_identifier_use: IdentifierUse | None = Field(
        None, description="Group identifier assigner identifier use."
    )
    group_identifier_assigner_identifier_type_system: str | None = Field(
        None, description="Group identifier assigner identifier type system."
    )
    group_identifier_assigner_identifier_type_version: str | None = Field(
        None, description="Group identifier assigner identifier type version."
    )
    group_identifier_assigner_identifier_type_code: str | None = Field(
        None, description="Group identifier assigner identifier type code."
    )
    group_identifier_assigner_identifier_type_display: str | None = Field(
        None, description="Group identifier assigner identifier type display."
    )
    group_identifier_assigner_identifier_type_user_selected: bool | None = Field(
        None, description="Group identifier assigner identifier type user selected."
    )
    group_identifier_assigner_identifier_type_text: str | None = Field(
        None, description="Group identifier assigner identifier type text."
    )
    group_identifier_assigner_identifier_system: str | None = Field(
        None, description="Group identifier assigner identifier system."
    )
    group_identifier_assigner_identifier_value: str | None = Field(
        None, description="Group identifier assigner identifier value."
    )
    group_identifier_assigner_identifier_period_start: datetime | None = Field(
        None, description="Group identifier assigner identifier period start."
    )
    group_identifier_assigner_identifier_period_end: datetime | None = Field(
        None, description="Group identifier assigner identifier period end."
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
    focus_identifier_use: IdentifierUse | None = Field(
        None, description="Focus identifier use."
    )
    focus_identifier_type_system: str | None = Field(
        None, description="Focus identifier type system."
    )
    focus_identifier_type_version: str | None = Field(
        None, description="Focus identifier type version."
    )
    focus_identifier_type_code: str | None = Field(
        None, description="Focus identifier type code."
    )
    focus_identifier_type_display: str | None = Field(
        None, description="Focus identifier type display."
    )
    focus_identifier_type_user_selected: bool | None = Field(
        None, description="Focus identifier type user selected."
    )
    focus_identifier_type_text: str | None = Field(
        None, description="Focus identifier type text."
    )
    focus_identifier_system: str | None = Field(
        None, description="Focus identifier system."
    )
    focus_identifier_value: str | None = Field(
        None, description="Focus identifier value."
    )
    focus_identifier_period_start: datetime | None = Field(
        None, description="Focus identifier period start."
    )
    focus_identifier_period_end: datetime | None = Field(
        None, description="Focus identifier period end."
    )
    for_: str | None = Field(
        None,
        alias="for",
        description="Beneficiary of the task (Reference(Any)).",
    )
    for_display: str | None = Field(
        None, description="Narrative for beneficiary reference."
    )
    for_identifier_use: IdentifierUse | None = Field(
        None, description="Beneficiary identifier use."
    )
    for_identifier_type_system: str | None = Field(
        None, description="Beneficiary identifier type system."
    )
    for_identifier_type_version: str | None = Field(
        None, description="Beneficiary identifier type version."
    )
    for_identifier_type_code: str | None = Field(
        None, description="Beneficiary identifier type code."
    )
    for_identifier_type_display: str | None = Field(
        None, description="Beneficiary identifier type display."
    )
    for_identifier_type_user_selected: bool | None = Field(
        None, description="Beneficiary identifier type user selected."
    )
    for_identifier_type_text: str | None = Field(
        None, description="Beneficiary identifier type text."
    )
    for_identifier_system: str | None = Field(
        None, description="Beneficiary identifier system."
    )
    for_identifier_value: str | None = Field(
        None, description="Beneficiary identifier value."
    )
    for_identifier_period_start: datetime | None = Field(
        None, description="Beneficiary identifier period start."
    )
    for_identifier_period_end: datetime | None = Field(
        None, description="Beneficiary identifier period end."
    )
    encounter: str | None = Field(
        None, description="Healthcare event during which task was created (Reference(Encounter))."
    )
    encounter_display: str | None = Field(
        None, description="Narrative for encounter reference."
    )
    encounter_identifier_use: IdentifierUse | None = Field(
        None, description="Encounter identifier use."
    )
    encounter_identifier_type_system: str | None = Field(
        None, description="Encounter identifier type system."
    )
    encounter_identifier_type_version: str | None = Field(
        None, description="Encounter identifier type version."
    )
    encounter_identifier_type_code: str | None = Field(
        None, description="Encounter identifier type code."
    )
    encounter_identifier_type_display: str | None = Field(
        None, description="Encounter identifier type display."
    )
    encounter_identifier_type_user_selected: bool | None = Field(
        None, description="Encounter identifier type user selected."
    )
    encounter_identifier_type_text: str | None = Field(
        None, description="Encounter identifier type text."
    )
    encounter_identifier_system: str | None = Field(
        None, description="Encounter identifier system."
    )
    encounter_identifier_value: str | None = Field(
        None, description="Encounter identifier value."
    )
    encounter_identifier_period_start: datetime | None = Field(
        None, description="Encounter identifier period start."
    )
    encounter_identifier_period_end: datetime | None = Field(
        None, description="Encounter identifier period end."
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
    requester_identifier_use: IdentifierUse | None = Field(
        None, description="Requester identifier use."
    )
    requester_identifier_type_system: str | None = Field(
        None, description="Requester identifier type system."
    )
    requester_identifier_type_version: str | None = Field(
        None, description="Requester identifier type version."
    )
    requester_identifier_type_code: str | None = Field(
        None, description="Requester identifier type code."
    )
    requester_identifier_type_display: str | None = Field(
        None, description="Requester identifier type display."
    )
    requester_identifier_type_user_selected: bool | None = Field(
        None, description="Requester identifier type user selected."
    )
    requester_identifier_type_text: str | None = Field(
        None, description="Requester identifier type text."
    )
    requester_identifier_system: str | None = Field(
        None, description="Requester identifier system."
    )
    requester_identifier_value: str | None = Field(
        None, description="Requester identifier value."
    )
    requester_identifier_period_start: datetime | None = Field(
        None, description="Requester identifier period start."
    )
    requester_identifier_period_end: datetime | None = Field(
        None, description="Requester identifier period end."
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
    owner_identifier_use: IdentifierUse | None = Field(
        None, description="Owner identifier use."
    )
    owner_identifier_type_system: str | None = Field(
        None, description="Owner identifier type system."
    )
    owner_identifier_type_version: str | None = Field(
        None, description="Owner identifier type version."
    )
    owner_identifier_type_code: str | None = Field(
        None, description="Owner identifier type code."
    )
    owner_identifier_type_display: str | None = Field(
        None, description="Owner identifier type display."
    )
    owner_identifier_type_user_selected: bool | None = Field(
        None, description="Owner identifier type user selected."
    )
    owner_identifier_type_text: str | None = Field(
        None, description="Owner identifier type text."
    )
    owner_identifier_system: str | None = Field(
        None, description="Owner identifier system."
    )
    owner_identifier_value: str | None = Field(
        None, description="Owner identifier value."
    )
    owner_identifier_period_start: datetime | None = Field(
        None, description="Owner identifier period start."
    )
    owner_identifier_period_end: datetime | None = Field(
        None, description="Owner identifier period end."
    )
    location: str | None = Field(
        None, description="Where task occurs (Reference(Location))."
    )
    location_display: str | None = Field(
        None, description="Narrative for location reference."
    )
    location_identifier_use: IdentifierUse | None = Field(
        None, description="Location identifier use."
    )
    location_identifier_type_system: str | None = Field(
        None, description="Location identifier type system."
    )
    location_identifier_type_version: str | None = Field(
        None, description="Location identifier type version."
    )
    location_identifier_type_code: str | None = Field(
        None, description="Location identifier type code."
    )
    location_identifier_type_display: str | None = Field(
        None, description="Location identifier type display."
    )
    location_identifier_type_user_selected: bool | None = Field(
        None, description="Location identifier type user selected."
    )
    location_identifier_type_text: str | None = Field(
        None, description="Location identifier type text."
    )
    location_identifier_system: str | None = Field(
        None, description="Location identifier system."
    )
    location_identifier_value: str | None = Field(
        None, description="Location identifier value."
    )
    location_identifier_period_start: datetime | None = Field(
        None, description="Location identifier period start."
    )
    location_identifier_period_end: datetime | None = Field(
        None, description="Location identifier period end."
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
    reason_reference_identifier_use: IdentifierUse | None = Field(
        None, description="Reason reference identifier use."
    )
    reason_reference_identifier_type_system: str | None = Field(
        None, description="Reason reference identifier type system."
    )
    reason_reference_identifier_type_version: str | None = Field(
        None, description="Reason reference identifier type version."
    )
    reason_reference_identifier_type_code: str | None = Field(
        None, description="Reason reference identifier type code."
    )
    reason_reference_identifier_type_display: str | None = Field(
        None, description="Reason reference identifier type display."
    )
    reason_reference_identifier_type_user_selected: bool | None = Field(
        None, description="Reason reference identifier type user selected."
    )
    reason_reference_identifier_type_text: str | None = Field(
        None, description="Reason reference identifier type text."
    )
    reason_reference_identifier_system: str | None = Field(
        None, description="Reason reference identifier system."
    )
    reason_reference_identifier_value: str | None = Field(
        None, description="Reason reference identifier value."
    )
    reason_reference_identifier_period_start: datetime | None = Field(
        None, description="Reason reference identifier period start."
    )
    reason_reference_identifier_period_end: datetime | None = Field(
        None, description="Reason reference identifier period end."
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
    group_identifier_assigner_identifier_use: IdentifierUse | None = None
    group_identifier_assigner_identifier_type_system: str | None = None
    group_identifier_assigner_identifier_type_version: str | None = None
    group_identifier_assigner_identifier_type_code: str | None = None
    group_identifier_assigner_identifier_type_display: str | None = None
    group_identifier_assigner_identifier_type_user_selected: bool | None = None
    group_identifier_assigner_identifier_type_text: str | None = None
    group_identifier_assigner_identifier_system: str | None = None
    group_identifier_assigner_identifier_value: str | None = None
    group_identifier_assigner_identifier_period_start: datetime | None = None
    group_identifier_assigner_identifier_period_end: datetime | None = None
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
    focus_identifier_use: IdentifierUse | None = None
    focus_identifier_type_system: str | None = None
    focus_identifier_type_version: str | None = None
    focus_identifier_type_code: str | None = None
    focus_identifier_type_display: str | None = None
    focus_identifier_type_user_selected: bool | None = None
    focus_identifier_type_text: str | None = None
    focus_identifier_system: str | None = None
    focus_identifier_value: str | None = None
    focus_identifier_period_start: datetime | None = None
    focus_identifier_period_end: datetime | None = None
    for_: str | None = Field(None, alias="for")
    for_display: str | None = None
    for_identifier_use: IdentifierUse | None = None
    for_identifier_type_system: str | None = None
    for_identifier_type_version: str | None = None
    for_identifier_type_code: str | None = None
    for_identifier_type_display: str | None = None
    for_identifier_type_user_selected: bool | None = None
    for_identifier_type_text: str | None = None
    for_identifier_system: str | None = None
    for_identifier_value: str | None = None
    for_identifier_period_start: datetime | None = None
    for_identifier_period_end: datetime | None = None
    encounter: str | None = None
    encounter_display: str | None = None
    encounter_identifier_use: IdentifierUse | None = None
    encounter_identifier_type_system: str | None = None
    encounter_identifier_type_version: str | None = None
    encounter_identifier_type_code: str | None = None
    encounter_identifier_type_display: str | None = None
    encounter_identifier_type_user_selected: bool | None = None
    encounter_identifier_type_text: str | None = None
    encounter_identifier_system: str | None = None
    encounter_identifier_value: str | None = None
    encounter_identifier_period_start: datetime | None = None
    encounter_identifier_period_end: datetime | None = None
    execution_period_start: datetime | None = None
    execution_period_end: datetime | None = None
    authored_on: datetime | None = None
    last_modified: datetime | None = None
    requester: str | None = None
    requester_display: str | None = None
    requester_identifier_use: IdentifierUse | None = None
    requester_identifier_type_system: str | None = None
    requester_identifier_type_version: str | None = None
    requester_identifier_type_code: str | None = None
    requester_identifier_type_display: str | None = None
    requester_identifier_type_user_selected: bool | None = None
    requester_identifier_type_text: str | None = None
    requester_identifier_system: str | None = None
    requester_identifier_value: str | None = None
    requester_identifier_period_start: datetime | None = None
    requester_identifier_period_end: datetime | None = None
    performer_type: list[TaskPerformerTypeInput] | None = None
    owner: str | None = None
    owner_display: str | None = None
    owner_identifier_use: IdentifierUse | None = None
    owner_identifier_type_system: str | None = None
    owner_identifier_type_version: str | None = None
    owner_identifier_type_code: str | None = None
    owner_identifier_type_display: str | None = None
    owner_identifier_type_user_selected: bool | None = None
    owner_identifier_type_text: str | None = None
    owner_identifier_system: str | None = None
    owner_identifier_value: str | None = None
    owner_identifier_period_start: datetime | None = None
    owner_identifier_period_end: datetime | None = None
    location: str | None = None
    location_display: str | None = None
    location_identifier_use: IdentifierUse | None = None
    location_identifier_type_system: str | None = None
    location_identifier_type_version: str | None = None
    location_identifier_type_code: str | None = None
    location_identifier_type_display: str | None = None
    location_identifier_type_user_selected: bool | None = None
    location_identifier_type_text: str | None = None
    location_identifier_system: str | None = None
    location_identifier_value: str | None = None
    location_identifier_period_start: datetime | None = None
    location_identifier_period_end: datetime | None = None
    reason_code_coding: list[CodingInput] | None = None
    reason_code_text: str | None = None
    reason_reference: str | None = None
    reason_reference_display: str | None = None
    reason_reference_identifier_use: IdentifierUse | None = None
    reason_reference_identifier_type_system: str | None = None
    reason_reference_identifier_type_version: str | None = None
    reason_reference_identifier_type_code: str | None = None
    reason_reference_identifier_type_display: str | None = None
    reason_reference_identifier_type_user_selected: bool | None = None
    reason_reference_identifier_type_text: str | None = None
    reason_reference_identifier_system: str | None = None
    reason_reference_identifier_value: str | None = None
    reason_reference_identifier_period_start: datetime | None = None
    reason_reference_identifier_period_end: datetime | None = None
    insurance: list[TaskReferenceInput | str] | None = None
    note: list[TaskNoteInput] | None = None
    relevant_history: list[TaskReferenceInput | str] | None = None
    restriction: TaskRestrictionInput | None = None
    input: list[TaskInputInput] | None = None
    output: list[TaskOutputInput] | None = None
