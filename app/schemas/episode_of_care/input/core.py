from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

# episode-of-care-status (the required binding of EpisodeOfCare.status and statusHistory.status).
StatusCode = Literal[
    "planned",
    "waitlist",
    "active",
    "onhold",
    "finished",
    "cancelled",
    "entered-in-error",
]

_EXAMPLE = {
    "resourceType": "EpisodeOfCare",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/episode-of-care-id",
            "value": "EOC-1001",
        }
    ],
    "status": "active",
    "statusHistory": [
        {"status": "planned", "period": {"start": "2025-12-01", "end": "2025-12-31"}},
        {"status": "active", "period": {"start": "2026-01-01"}},
    ],
    "type": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/episodeofcare-type",
                    "code": "cacp",
                    "display": "Community-based aged care",
                }
            ]
        }
    ],
    "diagnosis": [
        {
            "condition": {"reference": "Condition/120001"},
            "rank": 1,
        }
    ],
    "patient": {"reference": "Patient/10001"},
    "managingOrganization": {"reference": "Organization/190001"},
    "period": {"start": "2026-01-01"},
    "careManager": {"reference": "Practitioner/30001"},
}


class EpisodeOfCareStatusHistoryInput(FhirInputModel):
    """EpisodeOfCare.statusHistory - past statuses of the episode."""

    status: StatusCode | None = Field(
        None,
        description="planned | waitlist | active | onhold | finished | cancelled | entered-in-error (required by R4).",
    )
    period: FhirPeriodInput | None = Field(
        None,
        description="Duration the EpisodeOfCare was in the specified status (required by R4).",
    )


class EpisodeOfCareDiagnosisInput(FhirInputModel):
    """EpisodeOfCare.diagnosis - the list of diagnosis relevant to this episode of care."""

    condition: FhirReferenceInput | None = Field(
        None,
        description="Conditions/problems/diagnoses this episode of care is for - Reference(Condition), required by R4. A relative reference must exist in the caller's org (422 otherwise). Searched by `condition`.",
    )
    role: FhirCodeableConceptInput | None = Field(
        None, description="Role that this diagnosis has within the episode of care."
    )
    rank: int | None = Field(
        None, description="Ranking of the diagnosis (for each role type)."
    )


class _EpisodeOfCareFields(FhirInputModel):
    """Every writable EpisodeOfCare element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/episodeofcare.html). Create and patch accept exactly the same
    fields. R4 requires `status` and `patient`, but only the java_validator backend enforces
    cardinality minimums.

    The validated body is stored whole (EpisodeOfCareModel.content), so any valid R4 element is
    kept - including ones this model does not declare. Server-managed elements are ignored if
    sent: `id` (assigned from the episode_of_care_id sequence) and `meta` (audit/tenant data,
    stamped on at read time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["EpisodeOfCare"] | None = Field(
        None, description="Optional; if supplied it must be 'EpisodeOfCare'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries - validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None,
        description="Business Identifier(s) relevant for this EpisodeOfCare. Searched by `identifier`.",
    )
    status: StatusCode | None = Field(
        None,
        description="planned | waitlist | active | onhold | finished | cancelled | entered-in-error (required by R4). Searched by `status`.",
    )
    statusHistory: list[EpisodeOfCareStatusHistoryInput] | None = Field(
        None,
        description="Past list of status codes (the current status may be included to cover the start date of the status).",
    )
    type: list[FhirCodeableConceptInput] | None = Field(
        None,
        description="Type/class - e.g. specialist referral, disease management. Searched by `type`.",
    )
    diagnosis: list[EpisodeOfCareDiagnosisInput] | None = Field(
        None,
        description="The list of diagnosis relevant to this episode of care. `diagnosis.condition` is searched by `condition`.",
    )
    patient: FhirReferenceInput | None = Field(
        None,
        description="The patient who is the focus of this episode of care - Reference(Patient), required by R4. A relative reference must exist in the caller's org (422 otherwise). Searched by `patient`.",
    )
    managingOrganization: FhirReferenceInput | None = Field(
        None,
        description="Organization that assumes care - Reference(Organization). A relative reference must exist in the caller's org (422 otherwise). Searched by `organization`.",
    )
    period: FhirPeriodInput | None = Field(
        None,
        description="Interval during responsibility is assumed. Searched by `date`.",
    )
    referralRequest: list[FhirReferenceInput] | None = Field(
        None,
        description="Originating Referral Request(s) - Reference(ServiceRequest). A relative reference must exist in the caller's org (422 otherwise). Searched by `incoming-referral`.",
    )
    careManager: FhirReferenceInput | None = Field(
        None,
        description="Care manager/care coordinator for the patient - Reference(Practitioner | PractitionerRole). A relative reference must exist in the caller's org (422 otherwise). Searched by `care-manager` (a Practitioner).",
    )
    team: list[FhirReferenceInput] | None = Field(
        None,
        description="Other practitioners facilitating this episode of care - Reference(CareTeam). A relative reference must exist in the caller's org (422 otherwise).",
    )
    account: list[FhirReferenceInput] | None = Field(
        None,
        description="The set of accounts that may be used for billing for this EpisodeOfCare - Reference(Account), stored as sent.",
    )


class EpisodeOfCareCreateSchema(_EpisodeOfCareFields):
    """POST body - a FHIR R4 EpisodeOfCare resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class EpisodeOfCarePatchSchema(_EpisodeOfCareFields):
    """PATCH body - a partial FHIR R4 EpisodeOfCare (merge-patch semantics on top-level elements).
    Only supplied elements are written; omitted ones are left untouched. A supplied element
    replaces the stored value wholesale - a list (even `[]`) replaces every existing entry, an
    object such as `period` replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "finished",
                "period": {"start": "2026-01-01", "end": "2026-06-30"},
            }
        }
    }
