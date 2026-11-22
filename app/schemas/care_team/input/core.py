from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirContactPointInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

# CareTeamStatus (the required binding of CareTeam.status).
StatusCode = Literal["proposed", "active", "suspended", "inactive", "entered-in-error"]

_EXAMPLE = {
    "resourceType": "CareTeam",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/care-team-id",
            "value": "CT-1001",
        }
    ],
    "status": "active",
    "category": [
        {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "LA27976-2",
                    "display": "Encounter-focused care team",
                }
            ]
        }
    ],
    "name": "Cardiology care team",
    "subject": {"reference": "Patient/10001"},
    "period": {"start": "2026-01-01"},
    "participant": [
        {
            "role": [
                {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "17561000",
                            "display": "Cardiologist",
                        }
                    ]
                }
            ],
            "member": {"reference": "Practitioner/30001"},
        }
    ],
    "managingOrganization": [{"reference": "Organization/190001"}],
    "telecom": [{"system": "phone", "value": "+1-555-0100"}],
    "note": [{"text": "Weekly review."}],
}


class CareTeamAnnotationInput(FhirInputModel):
    """Annotation - a note with an author (a Reference or plain text) and a time."""

    authorReference: FhirReferenceInput | None = Field(
        None,
        description="Individual responsible for the annotation - Reference(Practitioner | Patient | RelatedPerson | Organization). A relative reference must exist in the caller's org (422 otherwise).",
    )
    authorString: str | None = Field(
        None, description="Individual responsible for the annotation, as plain text."
    )
    time: str | None = Field(
        None, description="When the annotation was made (a FHIR dateTime)."
    )
    text: str | None = Field(
        None, description="The annotation text, as markdown (required by R4)."
    )


class CareTeamParticipantInput(FhirInputModel):
    """CareTeam.participant - members of the team."""

    role: list[FhirCodeableConceptInput] | None = Field(
        None, description="Type of involvement."
    )
    member: FhirReferenceInput | None = Field(
        None,
        description="Who is involved - Reference(Practitioner | PractitionerRole | RelatedPerson | Patient | Organization | CareTeam). A relative reference must exist in the caller's org (422 otherwise). Searched by `participant`.",
    )
    onBehalfOf: FhirReferenceInput | None = Field(
        None,
        description="Organization of the practitioner - Reference(Organization). R4 rule ctm-1: only when `member` is a Practitioner. A relative reference must exist in the caller's org (422 otherwise).",
    )
    period: FhirPeriodInput | None = Field(
        None, description="Time period of the participant."
    )


class _CareTeamFields(FhirInputModel):
    """Every writable CareTeam element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/careteam.html). Create and patch accept exactly the same
    fields. R4 requires nothing beyond the types (every CareTeam element is optional), so any
    well-formed document is valid.

    The validated body is stored whole (CareTeamModel.content), so any valid R4 element is kept -
    including ones this model does not declare. Server-managed elements are ignored if sent:
    `id` (assigned from the care_team_id sequence) and `meta` (audit/tenant data, stamped on at
    read time). org_id and created_by/updated_by come from the verified JWT (actor.org_id /
    actor.sub), never the body. There is no user_id."""

    resourceType: Literal["CareTeam"] | None = Field(
        None, description="Optional; if supplied it must be 'CareTeam'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries - validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="External Ids for this team. Searched by `identifier`."
    )
    status: StatusCode | None = Field(
        None,
        description="proposed | active | suspended | inactive | entered-in-error. Searched by `status`.",
    )
    category: list[FhirCodeableConceptInput] | None = Field(
        None, description="Type of team. Searched by `category`."
    )
    name: str | None = Field(
        None, description="Name of the team, such as crisis assessment team."
    )
    subject: FhirReferenceInput | None = Field(
        None,
        description="Who care team is for - Reference(Patient | Group). A relative reference must exist in the caller's org (422 otherwise). Searched by `subject` / `patient`.",
    )
    encounter: FhirReferenceInput | None = Field(
        None,
        description="Encounter created as part of - Reference(Encounter). A relative reference must exist in the caller's org (422 otherwise). Searched by `encounter`.",
    )
    period: FhirPeriodInput | None = Field(
        None, description="Time period team covers. Searched by `date`."
    )
    participant: list[CareTeamParticipantInput] | None = Field(
        None, description="Members of the team."
    )
    reasonCode: list[FhirCodeableConceptInput] | None = Field(
        None, description="Why the care team exists."
    )
    reasonReference: list[FhirReferenceInput] | None = Field(
        None,
        description="Why the care team exists - Reference(Condition). A relative reference must exist in the caller's org (422 otherwise).",
    )
    managingOrganization: list[FhirReferenceInput] | None = Field(
        None,
        description="Organization responsible for the care team - Reference(Organization). A relative reference must exist in the caller's org (422 otherwise).",
    )
    telecom: list[FhirContactPointInput] | None = Field(
        None,
        description="A contact detail for the care team (that applies to all members).",
    )
    note: list[CareTeamAnnotationInput] | None = Field(
        None, description="Comments made about the CareTeam."
    )


class CareTeamCreateSchema(_CareTeamFields):
    """POST body - a FHIR R4 CareTeam resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class CareTeamPatchSchema(_CareTeamFields):
    """PATCH body - a partial FHIR R4 CareTeam (merge-patch semantics on top-level elements).
    Only supplied elements are written; omitted ones are left untouched. A supplied element
    replaces the stored value wholesale - a list (even `[]`) replaces every existing entry, an
    object such as `period` replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "inactive",
                "period": {"start": "2026-01-01", "end": "2026-06-30"},
            }
        }
    }
