from typing import Literal

from pydantic import Field

from app.schemas.fhir_input import (
    FhirCodeableConceptInput,
    FhirCodingInput,
    FhirIdentifierInput,
    FhirInputModel,
    FhirPeriodInput,
    FhirReferenceInput,
)

EncounterStatusCode = Literal[
    "planned",
    "arrived",
    "triaged",
    "in-progress",
    "onleave",
    "finished",
    "cancelled",
    "entered-in-error",
    "unknown",
]
LocationStatusCode = Literal["planned", "active", "reserved", "completed"]
DurationComparatorCode = Literal["<", "<=", ">=", ">"]

_EXAMPLE = {
    "resourceType": "Encounter",
    "identifier": [
        {
            "system": "https://fhir-server.dev/fhir/identifier-system/encounter-id",
            "value": "E-1001",
        }
    ],
    "status": "in-progress",
    "class": {
        "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
        "code": "AMB",
        "display": "ambulatory",
    },
    "type": [
        {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "270427003",
                    "display": "Patient-initiated encounter",
                }
            ]
        }
    ],
    "priority": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/v3-ActPriority",
                "code": "R",
            }
        ]
    },
    "subject": {"reference": "Patient/10001"},
    "participant": [
        {
            "type": [
                {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v3-ParticipationType",
                            "code": "ATND",
                        }
                    ]
                }
            ],
            "individual": {"reference": "Practitioner/30001"},
        }
    ],
    "appointment": [{"reference": "Appointment/40001"}],
    "period": {"start": "2026-06-01T09:00:00Z"},
    "length": {
        "value": 1,
        "unit": "d",
        "system": "http://unitsofmeasure.org",
        "code": "d",
    },
    "reasonCode": [{"text": "Annual check-up"}],
    "location": [{"location": {"reference": "Location/230001"}, "status": "active"}],
    "serviceProvider": {"reference": "Organization/190001"},
}


class EncounterStatusHistoryInput(FhirInputModel):
    """Encounter.statusHistory — a past status and when it applied (R4: both required)."""

    status: EncounterStatusCode | None = Field(
        None,
        description="planned | arrived | triaged | in-progress | onleave | finished | cancelled | entered-in-error | unknown.",
    )
    period: FhirPeriodInput | None = Field(
        None, description="The time that the episode was in the specified status."
    )


class EncounterClassHistoryInput(FhirInputModel):
    """Encounter.classHistory — a past class and when it applied (R4: both required)."""

    class_: FhirCodingInput | None = Field(
        None,
        alias="class",
        description="inpatient | outpatient | ambulatory | emergency +.",
    )
    period: FhirPeriodInput | None = Field(
        None, description="The time that the episode was in the specified class."
    )


class EncounterParticipantInput(FhirInputModel):
    """Encounter.participant — a person involved in the encounter."""

    type: list[FhirCodeableConceptInput] | None = Field(
        None, description="Role of participant in encounter."
    )
    period: FhirPeriodInput | None = Field(
        None,
        description="Period of time during the encounter that the participant participated.",
    )
    individual: FhirReferenceInput | None = Field(
        None,
        description="Persons involved in the encounter other than the patient — Reference(Practitioner | PractitionerRole | RelatedPerson). A relative Practitioner/PractitionerRole reference must exist in the caller's org (422 otherwise).",
    )


class EncounterDiagnosisInput(FhirInputModel):
    """Encounter.diagnosis — a diagnosis or procedure relevant to the encounter."""

    condition: FhirReferenceInput | None = Field(
        None,
        description="The diagnosis or procedure relevant to the encounter — Reference(Condition | Procedure) (required by R4).",
    )
    use: FhirCodeableConceptInput | None = Field(
        None,
        description="Role that this diagnosis has within the encounter (e.g. admission, billing, discharge).",
    )
    rank: int | None = Field(
        None, ge=1, description="Ranking of the diagnosis (for each role type)."
    )


class EncounterHospitalizationInput(FhirInputModel):
    """Encounter.hospitalization — details about the admission to a healthcare service."""

    preAdmissionIdentifier: FhirIdentifierInput | None = Field(
        None, description="Pre-admission identifier."
    )
    origin: FhirReferenceInput | None = Field(
        None,
        description="The location/organization from which the patient came before admission — Reference(Location | Organization).",
    )
    admitSource: FhirCodeableConceptInput | None = Field(
        None,
        description="From where patient was admitted (physician referral, transfer).",
    )
    reAdmission: FhirCodeableConceptInput | None = Field(
        None,
        description="The type of hospital re-admission that has occurred (if any).",
    )
    dietPreference: list[FhirCodeableConceptInput] | None = Field(
        None, description="Diet preferences reported by the patient."
    )
    specialCourtesy: list[FhirCodeableConceptInput] | None = Field(
        None, description="Special courtesies (VIP, board member)."
    )
    specialArrangement: list[FhirCodeableConceptInput] | None = Field(
        None, description="Wheelchair, translator, stretcher, etc."
    )
    destination: FhirReferenceInput | None = Field(
        None,
        description="Location/organization to which the patient is discharged — Reference(Location | Organization).",
    )
    dischargeDisposition: FhirCodeableConceptInput | None = Field(
        None, description="Category or kind of location after discharge."
    )


class EncounterLocationInput(FhirInputModel):
    """Encounter.location — a location the patient has been at during the encounter."""

    location: FhirReferenceInput | None = Field(
        None,
        description="Location the encounter takes place — Reference(Location) (required by R4). A relative reference must exist in the caller's org (422 otherwise).",
    )
    status: LocationStatusCode | None = Field(
        None, description="planned | active | reserved | completed."
    )
    physicalType: FhirCodeableConceptInput | None = Field(
        None,
        description="The physical type of the location (usually the level in the location hierarchy - bed, room, ward, virtual etc.).",
    )
    period: FhirPeriodInput | None = Field(
        None,
        description="Time period during which the patient was present at the location.",
    )


class EncounterDurationInput(FhirInputModel):
    """Encounter.length — a Duration (a Quantity with a time unit)."""

    value: float | int | None = Field(
        None, description="Numerical value (with implicit precision)."
    )
    comparator: DurationComparatorCode | None = Field(
        None, description="< | <= | >= | > - how to understand the value."
    )
    unit: str | None = Field(None, description="Unit representation.")
    system: str | None = Field(
        None,
        description="System that defines coded unit form (usually http://unitsofmeasure.org).",
    )
    code: str | None = Field(
        None, description="Coded form of the unit (UCUM: s, min, h, d, wk, mo, a)."
    )


class _EncounterFields(FhirInputModel):
    """Every writable Encounter element, in genuine FHIR R4 shape
    (https://www.hl7.org/fhir/R4/encounter.html). Create and patch accept
    exactly the same fields. R4 requires `status` and `class`; that is enforced
    by base R4 validation of the stored document (the `java_validator` backend
    — the native structural check has no cardinality minimums), not by this
    model. A PATCH may omit them: it is merged onto the current resource before
    validating.

    The validated body is stored whole (EncounterModel.content), so any valid R4
    element is kept — including ones this model does not declare.
    Server-managed elements are ignored if sent: `id` (assigned from the
    encounter_id sequence) and `meta` (audit/tenant data, stamped on at read
    time). org_id and created_by/updated_by come from the verified JWT
    (actor.org_id / actor.sub), never the body. There is no user_id."""

    resourceType: Literal["Encounter"] | None = Field(
        None, description="Optional; if supplied it must be 'Encounter'."
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries — validated by the profile pipeline, not here.",
    )
    identifier: list[FhirIdentifierInput] | None = Field(
        None, description="Identifier(s) by which this encounter is known."
    )
    status: EncounterStatusCode | None = Field(
        None,
        description="planned | arrived | triaged | in-progress | onleave | finished | cancelled | entered-in-error | unknown (required by R4).",
    )
    statusHistory: list[EncounterStatusHistoryInput] | None = Field(
        None, description="List of past encounter statuses."
    )
    class_: FhirCodingInput | None = Field(
        None,
        alias="class",
        description="Classification of patient encounter — a Coding, e.g. AMB (ambulatory), IMP (inpatient), EMER (emergency) from http://terminology.hl7.org/CodeSystem/v3-ActCode (required by R4).",
    )
    classHistory: list[EncounterClassHistoryInput] | None = Field(
        None, description="List of past encounter classes."
    )
    type: list[FhirCodeableConceptInput] | None = Field(
        None, description="Specific type of encounter."
    )
    serviceType: FhirCodeableConceptInput | None = Field(
        None, description="Specific type of service."
    )
    priority: FhirCodeableConceptInput | None = Field(
        None, description="Indicates the urgency of the encounter."
    )
    subject: FhirReferenceInput | None = Field(
        None,
        description="The patient or group present at the encounter — Reference(Patient | Group). A relative Patient reference must exist in the caller's org (422 otherwise).",
    )
    episodeOfCare: list[FhirReferenceInput] | None = Field(
        None,
        description="Episode(s) of care that this encounter should be recorded against — Reference(EpisodeOfCare).",
    )
    basedOn: list[FhirReferenceInput] | None = Field(
        None,
        description="The ServiceRequest that initiated this encounter — Reference(ServiceRequest).",
    )
    participant: list[EncounterParticipantInput] | None = Field(
        None, description="List of participants involved in the encounter."
    )
    appointment: list[FhirReferenceInput] | None = Field(
        None,
        description="The appointment that scheduled this encounter — Reference(Appointment). A relative reference must exist in the caller's org (422 otherwise).",
    )
    period: FhirPeriodInput | None = Field(
        None, description="The start and end time of the encounter."
    )
    length: EncounterDurationInput | None = Field(
        None, description="Quantity of time the encounter lasted (less time absent)."
    )
    reasonCode: list[FhirCodeableConceptInput] | None = Field(
        None, description="Coded reason the encounter takes place."
    )
    reasonReference: list[FhirReferenceInput] | None = Field(
        None,
        description="Reason the encounter takes place (reference) — Reference(Condition | Procedure | Observation | ImmunizationRecommendation).",
    )
    diagnosis: list[EncounterDiagnosisInput] | None = Field(
        None, description="The list of diagnosis relevant to this encounter."
    )
    account: list[FhirReferenceInput] | None = Field(
        None,
        description="The set of accounts that may be used for billing for this Encounter — Reference(Account).",
    )
    hospitalization: EncounterHospitalizationInput | None = Field(
        None, description="Details about the admission to a healthcare service."
    )
    location: list[EncounterLocationInput] | None = Field(
        None, description="List of locations where the patient has been."
    )
    serviceProvider: FhirReferenceInput | None = Field(
        None,
        description="The organization (facility) responsible for this encounter — Reference(Organization). A relative reference must exist in the caller's org (422 otherwise).",
    )
    partOf: FhirReferenceInput | None = Field(
        None,
        description="Another Encounter this encounter is part of — Reference(Encounter). A relative reference must exist in the caller's org (422 otherwise).",
    )


class EncounterCreateSchema(_EncounterFields):
    """POST body — a FHIR R4 Encounter resource."""

    model_config = {"json_schema_extra": {"example": _EXAMPLE}}


class EncounterPatchSchema(_EncounterFields):
    """PATCH body — a partial FHIR R4 Encounter (merge-patch semantics on
    top-level elements). Only supplied elements are written; omitted ones are
    left untouched. A supplied element replaces the stored value wholesale — a
    list (even `[]`) replaces every existing entry, an object such as
    `hospitalization` replaces the whole value, and `null` clears it."""

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "finished",
                "period": {
                    "start": "2026-06-01T09:00:00Z",
                    "end": "2026-06-01T09:40:00Z",
                },
            }
        }
    }
