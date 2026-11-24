from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirAttachmentInput,
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirReferenceInput,
)

# EventStatus / RequestPriority (the required bindings of Communication.status and .priority).
StatusCode = Literal[
    "preparation",
    "in-progress",
    "not-done",
    "on-hold",
    "stopped",
    "completed",
    "entered-in-error",
    "unknown",
]
PriorityCode = Literal["routine", "urgent", "asap", "stat"]

_EXAMPLE = {
    "resourceType": "Communication",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/communication-id",
            "value": "CM-1",
        }
    ],
    "basedOn": [{"reference": "CommunicationRequest/470001"}],
    "status": "completed",
    "category": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/communication-category",
                    "code": "notification",
                }
            ]
        }
    ],
    "priority": "routine",
    "medium": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationMode",
                    "code": "WRITTEN",
                }
            ]
        }
    ],
    "subject": {"reference": "Patient/10001"},
    "encounter": {"reference": "Encounter/20001"},
    "sent": "2026-01-15T09:00:00Z",
    "received": "2026-01-15T09:05:00Z",
    "recipient": [{"reference": "Patient/10001"}],
    "sender": {"reference": "Practitioner/30001"},
    "payload": [{"contentString": "Your results are ready."}],
}


class CommunicationPayloadInput(FhirInputModel):
    """Communication.payload - the message content. `content[x]` is a choice of `contentString`,
    `contentAttachment` or `contentReference` (Reference(Any)), required by R4 (only the
    `java_validator` backend enforces it)."""

    contentString: str | None = Field(
        None, description="content[x]: the message as a string."
    )
    contentAttachment: FhirAttachmentInput | None = Field(
        None, description="content[x]: the message as an Attachment."
    )
    contentReference: FhirReferenceInput | None = Field(
        None,
        description="content[x]: the message as a Reference(Any). A relative reference to a rebuilt resource must exist in the caller's org (422 otherwise).",
    )


class _CommunicationFields(FhirInputModel):
    """Every writable Communication element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/communication.html). Create and patch accept exactly the same
    fields. R4 requires `status`; the native validator cannot see a missing primitive `status`,
    which only the `java_validator` backend rejects.

    The validated body is stored whole (CommunicationModel.content), so any valid R4 element is
    kept - including ones this model does not declare. Server-managed elements are ignored if
    sent: `id` (assigned from the communication_id sequence) and `meta` (audit/tenant data,
    stamped on at read time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["Communication"] | None = Field(
        None, description="Optional; if supplied it must be 'Communication'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries - validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="Unique identifier. Searched by `identifier`."
    )
    instantiatesCanonical: list[str] | None = Field(
        None,
        description="Instantiates FHIR protocol or definition (canonical URLs). Searched by `instantiates-canonical`.",
    )
    instantiatesUri: list[str] | None = Field(
        None,
        description="Instantiates external protocol or definition (URIs). Searched by `instantiates-uri`.",
    )
    basedOn: list[FhirReferenceInput] | None = Field(
        None,
        description="Request fulfilled by this communication - Reference(Any). A relative reference to a rebuilt resource must exist in the caller's org (422 otherwise). Searched by `based-on`.",
    )
    partOf: list[FhirReferenceInput] | None = Field(
        None, description="Part of this action - Reference(Any). Searched by `part-of`."
    )
    inResponseTo: list[FhirReferenceInput] | None = Field(
        None, description="Reply to - Reference(Communication)."
    )
    status: StatusCode | None = Field(
        None,
        description="preparation | in-progress | not-done | on-hold | stopped | completed | entered-in-error | unknown (required by R4). Searched by `status`.",
    )
    statusReason: FhirCodeableConceptInput | None = Field(
        None, description="Reason for current status."
    )
    category: list[FhirCodeableConceptInput] | None = Field(
        None, description="Message category. Searched by `category`."
    )
    priority: PriorityCode | None = Field(
        None, description="routine | urgent | asap | stat."
    )
    medium: list[FhirCodeableConceptInput] | None = Field(
        None, description="A channel of communication. Searched by `medium`."
    )
    subject: FhirReferenceInput | None = Field(
        None,
        description="Focus of message - Reference(Patient | Group). Searched by `subject` / `patient`.",
    )
    topic: FhirCodeableConceptInput | None = Field(
        None, description="Description of the purpose/content."
    )
    about: list[FhirReferenceInput] | None = Field(
        None,
        description="Resources that pertain to this communication - Reference(Any).",
    )
    encounter: FhirReferenceInput | None = Field(
        None,
        description="Encounter created as part of - Reference(Encounter). Searched by `encounter`.",
    )
    sent: str | None = Field(
        None, description="When sent (a FHIR dateTime). Searched by `sent`."
    )
    received: str | None = Field(
        None, description="When received (a FHIR dateTime). Searched by `received`."
    )
    recipient: list[FhirReferenceInput] | None = Field(
        None,
        description="Message recipient - Reference(Device | Organization | Patient | Practitioner | PractitionerRole | RelatedPerson | Group | CareTeam | HealthcareService). Searched by `recipient`.",
    )
    sender: FhirReferenceInput | None = Field(
        None,
        description="Message sender - Reference(Device | Organization | Patient | Practitioner | PractitionerRole | RelatedPerson | HealthcareService). Searched by `sender`.",
    )
    reasonCode: list[FhirCodeableConceptInput] | None = Field(
        None, description="Indication for message."
    )
    reasonReference: list[FhirReferenceInput] | None = Field(
        None,
        description="Why was communication done? - Reference(Condition | Observation | DiagnosticReport | DocumentReference).",
    )
    payload: list[CommunicationPayloadInput] | None = Field(
        None, description="Message payload."
    )
    note: list[dict] | None = Field(
        None, description="Comments made about the communication (Annotation)."
    )


class CommunicationCreateSchema(_CommunicationFields):
    """POST body - a FHIR R4 Communication resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class CommunicationPatchSchema(_CommunicationFields):
    """PATCH body - a partial FHIR R4 Communication (merge-patch semantics on top-level
    elements). Only supplied elements are written; omitted ones are left untouched. A supplied
    element replaces the stored value wholesale - a list (even `[]`) replaces every existing
    entry, an object replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "completed",
                "received": "2026-01-15T09:05:00Z",
            }
        }
    }
