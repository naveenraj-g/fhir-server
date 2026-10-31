from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import ConditionQuantityComparator

from .codeable_concept import ConditionCodeableConceptInput
from .evidence import ConditionEvidenceInput
from .identifier import ConditionIdentifierInput
from .note import ConditionNoteInput
from .reference import (
    ConditionAsserterInput,
    ConditionEncounterInput,
    ConditionRecorderInput,
    ConditionSubjectInput,
)
from .stage import ConditionStageInput

_EXAMPLE = {
    "clinical_status": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                "code": "active",
                "display": "Active",
            }
        ]
    },
    "verification_status": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                "code": "confirmed",
                "display": "Confirmed",
            }
        ]
    },
    "category": [
        {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                    "code": "problem-list-item",
                    "display": "Problem List Item",
                }
            ]
        }
    ],
    "severity": {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "24484000",
                "display": "Severe",
            }
        ]
    },
    "code": {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "38341003",
                "display": "Hypertension",
            }
        ],
        "text": "Essential hypertension",
    },
    "subject": {"reference": "Patient/10001", "reference_display": "Jane Doe"},
    "onset_date_time": "2023-01-15T09:30:00Z",
    "recorded_date": "2023-01-15T10:00:00Z",
}


class ConditionCreateSchema(BaseModel):
    """Creates a Condition and any combination of its sub-resource lists atomically.

    `tenant_id`/`created_by` come from the verified JWT (`actor.org_id`/`actor.sub`) —
    neither is a request body field.
    """

    model_config = ConfigDict(extra="forbid", json_schema_extra={"example": _EXAMPLE})

    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions."
    )
    identifier: list[ConditionIdentifierInput] | None = Field(
        None, description="External ids for this condition."
    )
    clinical_status: ConditionCodeableConceptInput | None = Field(
        None, description="active | recurrence | relapse | inactive | remission | resolved."
    )
    verification_status: ConditionCodeableConceptInput | None = Field(
        None, description="unconfirmed | provisional | differential | confirmed | refuted | entered-in-error."
    )
    category: list[ConditionCodeableConceptInput] | None = Field(
        None, description="problem-list-item | encounter-diagnosis."
    )
    severity: ConditionCodeableConceptInput | None = Field(
        None, description="Subjective severity of condition."
    )
    code: ConditionCodeableConceptInput | None = Field(
        None, description="Identification of the condition, problem or diagnosis."
    )
    body_site: list[ConditionCodeableConceptInput] | None = Field(
        None, description="Anatomical location, if relevant."
    )
    subject: ConditionSubjectInput = Field(
        ..., description="Who has the condition (1..1 Reference(Patient | Group))."
    )
    encounter: ConditionEncounterInput | None = Field(
        None, description="Encounter created as part of."
    )

    # onset[x] (0..1 choice: dateTime | Age | Period | Range | string)
    onset_date_time: datetime | None = Field(
        None, description="onset[x]: dateTime."
    )
    onset_age_value: float | None = Field(
        None, description="onset[x]: Age (Quantity) — numeric value."
    )
    onset_age_comparator: ConditionQuantityComparator | None = Field(
        None, description="onset[x]: Age (Quantity) — comparator."
    )
    onset_age_unit: str | None = Field(
        None, description="onset[x]: Age (Quantity) — unit."
    )
    onset_age_system: str | None = Field(
        None, description="onset[x]: Age (Quantity) — unit system."
    )
    onset_age_code: str | None = Field(
        None, description="onset[x]: Age (Quantity) — coded unit form."
    )
    onset_period_start: datetime | None = Field(
        None, description="onset[x]: Period — start."
    )
    onset_period_end: datetime | None = Field(
        None, description="onset[x]: Period — end."
    )
    onset_range_low_value: float | None = Field(
        None, description="onset[x]: Range.low — numeric value."
    )
    onset_range_low_unit: str | None = Field(
        None, description="onset[x]: Range.low — unit."
    )
    onset_range_low_system: str | None = Field(
        None, description="onset[x]: Range.low — unit system."
    )
    onset_range_low_code: str | None = Field(
        None, description="onset[x]: Range.low — coded unit form."
    )
    onset_range_high_value: float | None = Field(
        None, description="onset[x]: Range.high — numeric value."
    )
    onset_range_high_unit: str | None = Field(
        None, description="onset[x]: Range.high — unit."
    )
    onset_range_high_system: str | None = Field(
        None, description="onset[x]: Range.high — unit system."
    )
    onset_range_high_code: str | None = Field(
        None, description="onset[x]: Range.high — coded unit form."
    )
    onset_string: str | None = Field(
        None, description="onset[x]: string."
    )

    # abatement[x] (0..1 choice: dateTime | Age | Period | Range | string)
    abatement_date_time: datetime | None = Field(
        None, description="abatement[x]: dateTime."
    )
    abatement_age_value: float | None = Field(
        None, description="abatement[x]: Age (Quantity) — numeric value."
    )
    abatement_age_comparator: ConditionQuantityComparator | None = Field(
        None, description="abatement[x]: Age (Quantity) — comparator."
    )
    abatement_age_unit: str | None = Field(
        None, description="abatement[x]: Age (Quantity) — unit."
    )
    abatement_age_system: str | None = Field(
        None, description="abatement[x]: Age (Quantity) — unit system."
    )
    abatement_age_code: str | None = Field(
        None, description="abatement[x]: Age (Quantity) — coded unit form."
    )
    abatement_period_start: datetime | None = Field(
        None, description="abatement[x]: Period — start."
    )
    abatement_period_end: datetime | None = Field(
        None, description="abatement[x]: Period — end."
    )
    abatement_range_low_value: float | None = Field(
        None, description="abatement[x]: Range.low — numeric value."
    )
    abatement_range_low_unit: str | None = Field(
        None, description="abatement[x]: Range.low — unit."
    )
    abatement_range_low_system: str | None = Field(
        None, description="abatement[x]: Range.low — unit system."
    )
    abatement_range_low_code: str | None = Field(
        None, description="abatement[x]: Range.low — coded unit form."
    )
    abatement_range_high_value: float | None = Field(
        None, description="abatement[x]: Range.high — numeric value."
    )
    abatement_range_high_unit: str | None = Field(
        None, description="abatement[x]: Range.high — unit."
    )
    abatement_range_high_system: str | None = Field(
        None, description="abatement[x]: Range.high — unit system."
    )
    abatement_range_high_code: str | None = Field(
        None, description="abatement[x]: Range.high — coded unit form."
    )
    abatement_string: str | None = Field(
        None, description="abatement[x]: string."
    )

    recorded_date: datetime | None = Field(
        None, description="Date record was first recorded."
    )
    recorder: ConditionRecorderInput | None = Field(
        None, description="Who recorded the condition."
    )
    asserter: ConditionAsserterInput | None = Field(
        None, description="Person who asserts this condition."
    )
    stage: list[ConditionStageInput] | None = Field(
        None, description="Stage/grade, usually assessed formally."
    )
    evidence: list[ConditionEvidenceInput] | None = Field(
        None, description="Supporting evidence."
    )
    note: list[ConditionNoteInput] | None = Field(
        None, description="Additional information about the condition."
    )


class ConditionPatchSchema(BaseModel):
    """All fields optional. Fields not passed are left unchanged."""

    model_config = ConfigDict(extra="forbid")

    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions."
    )
    identifier: list[ConditionIdentifierInput] | None = Field(
        None, description="External ids for this condition."
    )
    clinical_status: ConditionCodeableConceptInput | None = Field(
        None, description="active | recurrence | relapse | inactive | remission | resolved."
    )
    verification_status: ConditionCodeableConceptInput | None = Field(
        None, description="unconfirmed | provisional | differential | confirmed | refuted | entered-in-error."
    )
    category: list[ConditionCodeableConceptInput] | None = Field(
        None, description="problem-list-item | encounter-diagnosis."
    )
    severity: ConditionCodeableConceptInput | None = Field(
        None, description="Subjective severity of condition."
    )
    code: ConditionCodeableConceptInput | None = Field(
        None, description="Identification of the condition, problem or diagnosis."
    )
    body_site: list[ConditionCodeableConceptInput] | None = Field(
        None, description="Anatomical location, if relevant."
    )
    subject: ConditionSubjectInput | None = Field(
        None, description="Who has the condition (Reference(Patient | Group))."
    )
    encounter: ConditionEncounterInput | None = Field(
        None, description="Encounter created as part of."
    )

    onset_date_time: datetime | None = None
    onset_age_value: float | None = None
    onset_age_comparator: ConditionQuantityComparator | None = None
    onset_age_unit: str | None = None
    onset_age_system: str | None = None
    onset_age_code: str | None = None
    onset_period_start: datetime | None = None
    onset_period_end: datetime | None = None
    onset_range_low_value: float | None = None
    onset_range_low_unit: str | None = None
    onset_range_low_system: str | None = None
    onset_range_low_code: str | None = None
    onset_range_high_value: float | None = None
    onset_range_high_unit: str | None = None
    onset_range_high_system: str | None = None
    onset_range_high_code: str | None = None
    onset_string: str | None = None

    abatement_date_time: datetime | None = None
    abatement_age_value: float | None = None
    abatement_age_comparator: ConditionQuantityComparator | None = None
    abatement_age_unit: str | None = None
    abatement_age_system: str | None = None
    abatement_age_code: str | None = None
    abatement_period_start: datetime | None = None
    abatement_period_end: datetime | None = None
    abatement_range_low_value: float | None = None
    abatement_range_low_unit: str | None = None
    abatement_range_low_system: str | None = None
    abatement_range_low_code: str | None = None
    abatement_range_high_value: float | None = None
    abatement_range_high_unit: str | None = None
    abatement_range_high_system: str | None = None
    abatement_range_high_code: str | None = None
    abatement_string: str | None = None

    recorded_date: datetime | None = None
    recorder: ConditionRecorderInput | None = None
    asserter: ConditionAsserterInput | None = None
    stage: list[ConditionStageInput] | None = None
    evidence: list[ConditionEvidenceInput] | None = None
    note: list[ConditionNoteInput] | None = None
