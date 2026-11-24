from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirAttachmentInput,
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

# RequestStatus / RequestPriority (the required bindings of CommunicationRequest.status and
# .priority).
StatusCode = Literal[
    "draft",
    "active",
    "on-hold",
    "revoked",
    "completed",
    "entered-in-error",
    "unknown",
]
PriorityCode = Literal["routine", "urgent", "asap", "stat"]

_EXAMPLE = {
    "resourceType": "CommunicationRequest",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/communication-request-id",
            "value": "CR-1",
        }
    ],
    "basedOn": [{"reference": "CarePlan/290001"}],
    "groupIdentifier": {"system": "urn:groups", "value": "G-1"},
    "status": "active",
    "category": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/communication-category",
                    "code": "reminder",
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
    "payload": [{"contentString": "Please book your follow-up visit."}],
    "occurrenceDateTime": "2026-02-01T09:00:00Z",
    "authoredOn": "2026-01-15T09:00:00Z",
    "requester": {"reference": "Practitioner/30001"},
    "recipient": [{"reference": "Patient/10001"}],
    "sender": {"reference": "Practitioner/30001"},
}


class CommunicationRequestPayloadInput(FhirInputModel):
    """CommunicationRequest.payload - the message content. `content[x]` is a choice of
    `contentString`, `contentAttachment` or `contentReference` (Reference(Any)), required by R4
    (only the `java_validator` backend enforces it)."""

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


class _CommunicationRequestFields(FhirInputModel):
    """Every writable CommunicationRequest element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/communicationrequest.html). Create and patch accept exactly the
    same fields. R4 requires `status`; the native validator cannot see a missing primitive
    `status`, which only the `java_validator` backend rejects.

    The validated body is stored whole (CommunicationRequestModel.content), so any valid R4
    element is kept - including ones this model does not declare. Server-managed elements are
    ignored if sent: `id` (assigned from the communication_request_id sequence) and `meta`
    (audit/tenant data, stamped on at read time). org_id and created_by/updated_by come from the
    verified JWT (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["CommunicationRequest"] | None = Field(
        None, description="Optional; if supplied it must be 'CommunicationRequest'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries - validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="Unique identifier. Searched by `identifier`."
    )
    basedOn: list[FhirReferenceInput] | None = Field(
        None,
        description="Fulfills plan or proposal - Reference(Any). A relative reference to a rebuilt resource must exist in the caller's org (422 otherwise). Searched by `based-on`.",
    )
    replaces: list[FhirReferenceInput] | None = Field(
        None,
        description="Request(s) replaced by this request - Reference(CommunicationRequest). Searched by `replaces`.",
    )
    groupIdentifier: FhirIdentifierInput | None = Field(
        None,
        description="Composite request this is part of. Searched by `group-identifier`.",
    )
    status: StatusCode | None = Field(
        None,
        description="draft | active | on-hold | revoked | completed | entered-in-error | unknown (required by R4). Searched by `status`.",
    )
    statusReason: FhirCodeableConceptInput | None = Field(
        None, description="Reason for current status."
    )
    category: list[FhirCodeableConceptInput] | None = Field(
        None, description="Message category. Searched by `category`."
    )
    priority: PriorityCode | None = Field(
        None,
        description="routine | urgent | asap | stat. Searched by `priority`.",
    )
    doNotPerform: bool | None = Field(
        None,
        description="True if the request is asking for the communication NOT to occur.",
    )
    medium: list[FhirCodeableConceptInput] | None = Field(
        None, description="A channel of communication. Searched by `medium`."
    )
    subject: FhirReferenceInput | None = Field(
        None,
        description="Focus of message - Reference(Patient | Group). Searched by `subject` / `patient`.",
    )
    about: list[FhirReferenceInput] | None = Field(
        None,
        description="Resources that pertain to this communication - Reference(Any).",
    )
    encounter: FhirReferenceInput | None = Field(
        None,
        description="Encounter created as part of - Reference(Encounter). Searched by `encounter`.",
    )
    payload: list[CommunicationRequestPayloadInput] | None = Field(
        None, description="Message payload."
    )
    occurrenceDateTime: str | None = Field(
        None,
        description="occurrence[x]: when scheduled (a FHIR dateTime). Searched by `occurrence`.",
    )
    occurrencePeriod: FhirPeriodInput | None = Field(
        None, description="occurrence[x]: when scheduled (a Period; not searched)."
    )
    authoredOn: str | None = Field(
        None,
        description="When request transitioned to being actionable (a FHIR dateTime). Searched by `authored`.",
    )
    requester: FhirReferenceInput | None = Field(
        None,
        description="Who/what is requesting service - Reference(Practitioner | PractitionerRole | Organization | Patient | RelatedPerson | Device). Searched by `requester`.",
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
        None, description="Why is communication needed?"
    )
    reasonReference: list[FhirReferenceInput] | None = Field(
        None,
        description="Why is communication needed? - Reference(Condition | Observation | DiagnosticReport | DocumentReference).",
    )
    note: list[dict] | None = Field(
        None, description="Comments made about the request (Annotation)."
    )


class CommunicationRequestCreateSchema(_CommunicationRequestFields):
    """POST body - a FHIR R4 CommunicationRequest resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class CommunicationRequestPatchSchema(_CommunicationRequestFields):
    """PATCH body - a partial FHIR R4 CommunicationRequest (merge-patch semantics on top-level
    elements). Only supplied elements are written; omitted ones are left untouched. A supplied
    element replaces the stored value wholesale - a list (even `[]`) replaces every existing
    entry, an object replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "completed",
                "occurrenceDateTime": "2026-02-02T09:00:00Z",
            }
        }
    }
