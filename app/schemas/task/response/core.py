from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    AuditFields,
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
    PlainCodingRow,
)

from .identifier import PlainTaskIdentifier
from .io import (
    FHIRTaskInput,
    FHIRTaskOutput,
    PlainTaskInput,
    PlainTaskOutput,
)
from .note import FHIRTaskAnnotation, PlainTaskNote
from .performer_type import PlainTaskPerformerType
from .reference import PlainTaskReference
from .restriction import FHIRTaskRestriction, PlainTaskRestriction


# ── FHIR JSON ─────────────────────────────────────────────────────────────────


class FHIRTaskSchema(BaseModel):
    """FHIR R4 Task resource schema."""

    model_config = ConfigDict(populate_by_name=True)

    resourceType: Literal["Task"] = "Task"
    id: str = Field(..., description="Logical ID of this artifact.")
    meta: FHIRMeta | None = Field(None, description="Metadata about the resource.")
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Task Instance Identifier."
    )
    instantiatesCanonical: str | None = Field(
        None, description="Formal definition of task (canonical(ActivityDefinition))."
    )
    instantiatesUri: str | None = Field(
        None, description="Formal definition of task (uri)."
    )
    basedOn: list[FHIRReference] | None = Field(
        None, description="Request fulfilled by this task."
    )
    groupIdentifier: FHIRIdentifier | None = Field(
        None, description="Requisition or Form identifier."
    )
    partOf: list[FHIRReference] | None = Field(
        None, description="Composite task."
    )
    status: str = Field(
        ...,
        description="draft | requested | received | accepted | rejected | ready | cancelled | in-progress | on-hold | failed | completed | entered-in-error.",
    )
    statusReason: FHIRCodeableConcept | None = Field(
        None, description="Reason for current status."
    )
    businessStatus: FHIRCodeableConcept | None = Field(
        None, description="E.g. 'Waiting on review', 'Deferred'."
    )
    intent: str = Field(
        ...,
        description="unknown | proposal | plan | order | original-order | reflex-order | filler-order | instance-order | option.",
    )
    priority: str | None = Field(
        None, description="routine | urgent | asap | stat."
    )
    code: FHIRCodeableConcept | None = Field(
        None, description="Task Type."
    )
    description: str | None = Field(
        None, description="Human-readable explanation of task."
    )
    focus: FHIRReference | None = Field(
        None, description="What task is acting on."
    )
    for_: FHIRReference | None = Field(
        None,
        alias="for",
        description="Beneficiary of the task.",
    )
    encounter: FHIRReference | None = Field(
        None, description="Healthcare event during which task was created."
    )
    executionPeriod: FHIRPeriod | None = Field(
        None, description="Start and end time of execution."
    )
    authoredOn: str | None = Field(
        None, description="Task Creation Date."
    )
    lastModified: str | None = Field(
        None, description="Task Last Modified Date."
    )
    requester: FHIRReference | None = Field(
        None, description="Who is asking for task to be done."
    )
    performerType: list[FHIRCodeableConcept] | None = Field(
        None, description="Requested performer normal role."
    )
    owner: FHIRReference | None = Field(
        None, description="Responsible individual."
    )
    location: FHIRReference | None = Field(
        None, description="Where task occurs."
    )
    reasonCode: FHIRCodeableConcept | None = Field(
        None, description="Why task is needed."
    )
    reasonReference: FHIRReference | None = Field(
        None, description="Why task is needed (Reference)."
    )
    insurance: list[FHIRReference] | None = Field(
        None, description="Associated insurance coverage."
    )
    note: list[FHIRTaskAnnotation] | None = Field(
        None, description="Comments made about the task."
    )
    relevantHistory: list[FHIRReference] | None = Field(
        None, description="Key events in history of the task."
    )
    restriction: FHIRTaskRestriction | None = Field(
        None, description="Constraints on task execution."
    )
    input: list[FHIRTaskInput] | None = Field(
        None, description="Information used to perform task."
    )
    output: list[FHIRTaskOutput] | None = Field(
        None, description="Information produced as part of task."
    )
    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions."
    )


class FHIRTaskBundleEntry(BaseModel):
    resource: FHIRTaskSchema


class FHIRTaskBundle(FHIRBundle):
    entry: list[FHIRTaskBundleEntry] | None = None


# ── Plain (snake_case) ─────────────────────────────────────────────────────────


class PlainTaskResponse(AuditFields):
    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Public task_id.")
    status: str = Field(..., description="Current status of the task.")
    intent: str = Field(..., description="Intent of the task.")
    priority: str | None = Field(None, description="Priority.")
    description: str | None = Field(None, description="Description.")
    instantiates_canonical: str | None = None
    instantiates_uri: str | None = None
    authored_on: str | None = None
    last_modified: str | None = None
    code_text: str | None = None
    code_codings: list[PlainCodingRow] | None = None
    status_reason_text: str | None = None
    status_reason_codings: list[PlainCodingRow] | None = None
    business_status_text: str | None = None
    business_status_codings: list[PlainCodingRow] | None = None
    reason_code_text: str | None = None
    reason_code_codings: list[PlainCodingRow] | None = None
    focus_reference: str | None = None
    focus_type: str | None = None
    focus_id: int | None = None
    focus_display: str | None = None
    for_reference: str | None = None
    for_type: str | None = None
    for_id: int | None = None
    for_display: str | None = None
    encounter_reference: str | None = None
    encounter_type: str | None = None
    encounter_id: int | None = None
    encounter_display: str | None = None
    execution_period_start: str | None = None
    execution_period_end: str | None = None
    requester_reference: str | None = None
    requester_type: str | None = None
    requester_id: int | None = None
    requester_display: str | None = None
    owner_reference: str | None = None
    owner_type: str | None = None
    owner_id: int | None = None
    owner_display: str | None = None
    location_reference: str | None = None
    location_type: str | None = None
    location_id: int | None = None
    location_display: str | None = None
    reason_reference_reference: str | None = None
    reason_reference_type: str | None = None
    reason_reference_id: int | None = None
    reason_reference_display: str | None = None
    group_identifier_use: str | None = None
    group_identifier_system: str | None = None
    group_identifier_value: str | None = None
    group_identifier_period_start: str | None = None
    group_identifier_period_end: str | None = None
    group_identifier_assigner_reference: str | None = None
    group_identifier_assigner_type: str | None = None
    group_identifier_assigner_id: int | None = None
    group_identifier_assigner_display: str | None = None
    restriction_repetitions: int | None = None
    restriction_period_start: str | None = None
    restriction_period_end: str | None = None
    extension: list[dict] | None = None
    identifiers: list[PlainTaskIdentifier] | None = None
    performer_types: list[PlainTaskPerformerType] | None = None
    based_on_list: list[PlainTaskReference] | None = None
    part_of_list: list[PlainTaskReference] | None = None
    insurance_list: list[PlainTaskReference] | None = None
    relevant_history_list: list[PlainTaskReference] | None = None
    restriction_recipients: list[PlainTaskReference] | None = None
    notes: list[PlainTaskNote] | None = None
    inputs: list[PlainTaskInput] | None = None
    outputs: list[PlainTaskOutput] | None = None


class PaginatedTaskResponse(BaseModel):
    total: int = Field(..., description="Total matching records.")
    limit: int = Field(..., description="Maximum results returned.")
    offset: int = Field(..., description="Offset applied.")
    data: list[PlainTaskResponse] = Field(
        ..., description="Page of task records."
    )
