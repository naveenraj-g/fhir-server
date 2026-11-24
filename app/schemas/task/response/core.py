from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRPeriod,
    FHIRReference,
)
from app.schemas.datatypes.annotation import FHIRAnnotation
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRTaskRestriction(BaseModel):
    repetitions: int | None = Field(None, description="How many times to repeat.")
    period: FHIRPeriod | None = Field(None, description="When fulfillment is sought.")
    recipient: list[FHIRReference] | None = Field(
        None, description="For whom is fulfillment sought."
    )


class FHIRTaskSchema(BaseModel):
    resourceType: str = Field("Task", description="Always 'Task'.")
    id: str = Field(..., description="Public task_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="Task Instance Identifier."
    )
    instantiatesCanonical: str | None = Field(
        None, description="Formal definition of task (canonical)."
    )
    instantiatesUri: str | None = Field(
        None, description="Formal definition of task (URI)."
    )
    basedOn: list[FHIRReference] | None = Field(
        None, description="Request fulfilled by this task."
    )
    groupIdentifier: FHIRIdentifier | None = Field(
        None, description="Requisition or grouper id."
    )
    partOf: list[FHIRReference] | None = Field(None, description="Composite task.")
    status: str | None = Field(
        None,
        description="draft | requested | received | accepted | rejected | ready | cancelled | in-progress | on-hold | failed | completed | entered-in-error.",
    )
    statusReason: FHIRCodeableConcept | None = Field(
        None, description="Reason for current status."
    )
    businessStatus: FHIRCodeableConcept | None = Field(
        None, description="E.g. 'Specimen collected', 'IV prepped'."
    )
    intent: str | None = Field(
        None,
        description="unknown | proposal | plan | order | original-order | reflex-order | filler-order | instance-order | option.",
    )
    priority: str | None = Field(None, description="routine | urgent | asap | stat.")
    code: FHIRCodeableConcept | None = Field(None, description="Task Type.")
    description: str | None = Field(
        None, description="Human-readable explanation of task."
    )
    focus: FHIRReference | None = Field(None, description="What task is acting on.")
    for_: FHIRReference | None = Field(
        None, alias="for", description="Beneficiary of the Task."
    )
    encounter: FHIRReference | None = Field(
        None, description="Healthcare event during which this task originated."
    )
    executionPeriod: FHIRPeriod | None = Field(
        None, description="Start and end time of execution."
    )
    authoredOn: str | None = Field(None, description="Task Creation Date.")
    lastModified: str | None = Field(None, description="Task Last Modified Date.")
    requester: FHIRReference | None = Field(
        None, description="Who is asking for task to be done."
    )
    performerType: list[FHIRCodeableConcept] | None = Field(
        None, description="Requested performer."
    )
    owner: FHIRReference | None = Field(None, description="Responsible individual.")
    location: FHIRReference | None = Field(None, description="Where task occurs.")
    reasonCode: FHIRCodeableConcept | None = Field(
        None, description="Why task is needed."
    )
    reasonReference: FHIRReference | None = Field(
        None, description="Why task is needed."
    )
    insurance: list[FHIRReference] | None = Field(
        None, description="Associated insurance coverage."
    )
    note: list[FHIRAnnotation] | None = Field(
        None, description="Comments made about the task."
    )
    relevantHistory: list[FHIRReference] | None = Field(
        None, description="Key events in history of the Task."
    )
    restriction: FHIRTaskRestriction | None = Field(
        None, description="Constraints on fulfillment tasks."
    )
    input: list[dict] | None = Field(
        None, description="Information used to perform task (type + value[x])."
    )
    output: list[dict] | None = Field(
        None, description="Information produced as part of task (type + value[x])."
    )

    model_config = {"populate_by_name": True}


class FHIRTaskBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRTaskSchema | dict = Field(
        ...,
        description="A Task (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included resource (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRTaskBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRTaskBundleEntry] | None = None
