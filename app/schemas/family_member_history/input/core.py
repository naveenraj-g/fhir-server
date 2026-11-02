from datetime import date as py_date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import (
    FamilyMemberHistoryQuantityComparator,
    FamilyMemberHistoryStatus,
    IdentifierUse,
)
from app.schemas.family_member_history.input.codeable_concept import (
    FamilyMemberHistoryCodeableConceptInput,
)
from app.schemas.family_member_history.input.condition import (
    FamilyMemberHistoryConditionInput,
)
from app.schemas.family_member_history.input.identifier import (
    FamilyMemberHistoryIdentifierInput,
)
from app.schemas.family_member_history.input.note import (
    FamilyMemberHistoryNoteInput,
)
from app.schemas.family_member_history.input.reason_code import (
    FamilyMemberHistoryReasonCodeInput,
)
from app.schemas.family_member_history.input.reason_reference import (
    FamilyMemberHistoryReasonReferenceInput,
)

_CREATE_EXAMPLE = {
    "status": "completed",
    "patient": "Patient/10001",
    "patient_display": "Jane Doe",
    "date": "2026-01-15T10:00:00Z",
    "name": "John Doe",
    "relationship": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/v3-RoleCode",
                "code": "FTH",
                "display": "father",
            }
        ],
        "text": "Father",
    },
    "sex": {
        "coding": [
            {
                "system": "http://hl7.org/fhir/administrative-gender",
                "code": "male",
                "display": "Male",
            }
        ],
        "text": "Male",
    },
    "born_date": "1950-05-12",
    "age_age_value": 75.0,
    "age_age_unit": "a",
    "age_age_system": "http://unitsofmeasure.org",
    "age_age_code": "a",
    "estimated_age": False,
    "deceased_boolean": False,
    "reason_code": [
        {
            "coding": [
                {
                    "system": "http://snomed.info/sct",
                    "code": "44054006",
                    "display": "Type 2 diabetes mellitus",
                }
            ],
            "text": "Family history of Type 2 Diabetes",
        }
    ],
    "note": [
        {
            "text": "Father was diagnosed with diabetes in his early 50s.",
            "time": "2026-01-15T10:05:00Z",
            "author_string": "Dr. Alice Smith",
        }
    ],
    "condition": [
        {
            "code": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "44054006",
                        "display": "Type 2 diabetes mellitus",
                    }
                ],
                "text": "Type 2 Diabetes",
            },
            "outcome": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-outcome",
                        "code": "alive",
                        "display": "Alive",
                    }
                ],
                "text": "Alive and well managed",
            },
            "contributed_to_death": False,
            "onset_age_value": 52.0,
            "onset_age_unit": "a",
            "onset_age_system": "http://unitsofmeasure.org",
            "onset_age_code": "a",
            "note": [
                {
                    "text": "Managed with oral metformin and lifestyle interventions.",
                    "time": "2026-01-15T10:06:00Z",
                }
            ],
        }
    ],
}


class FamilyMemberHistoryCreateSchema(BaseModel):
    """Request schema for creating a new FamilyMemberHistory resource."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": _CREATE_EXAMPLE},
    )

    identifier: list[FamilyMemberHistoryIdentifierInput] | None = Field(
        None, description="External Ids for this record."
    )
    instantiates_canonical: list[str] | None = Field(
        None, description="Instantiates FHIR protocol or definition."
    )
    instantiates_uri: list[str] | None = Field(
        None, description="Instantiates external protocol or definition."
    )

    status: FamilyMemberHistoryStatus = Field(
        ..., description="partial | completed | entered-in-error | health-unknown."
    )
    data_absent_reason: FamilyMemberHistoryCodeableConceptInput | None = Field(
        None, description="subject-unknown | withheld | unable-to-obtain | deferred."
    )

    # patient (1..1 Reference(Patient))
    patient: str = Field(
        ..., description="Patient history is about. Reference(Patient), e.g. 'Patient/10001'."
    )
    patient_display: str | None = Field(None, description="Display text for patient.")
    patient_identifier_use: IdentifierUse | None = Field(
        None, description="Fallback identifier — its purpose, if known."
    )
    patient_identifier_type_system: str | None = Field(
        None, description="Fallback identifier — code system for its type."
    )
    patient_identifier_type_version: str | None = Field(
        None, description="Fallback identifier — version of the type code system."
    )
    patient_identifier_type_code: str | None = Field(
        None, description="Fallback identifier — a symbol for its type."
    )
    patient_identifier_type_display: str | None = Field(
        None, description="Fallback identifier — display for its type."
    )
    patient_identifier_type_user_selected: bool | None = Field(
        None, description="Fallback identifier — whether this type coding was chosen directly by the user."
    )
    patient_identifier_type_text: str | None = Field(
        None, description="Fallback identifier — human language rendering of its type."
    )
    patient_identifier_system: str | None = Field(
        None, description="Fallback identifier — namespace URL for the value."
    )
    patient_identifier_value: str | None = Field(
        None, description="Fallback identifier — value within the given system."
    )
    patient_identifier_period_start: datetime | None = Field(
        None, description="Fallback identifier — start of validity period."
    )
    patient_identifier_period_end: datetime | None = Field(
        None, description="Fallback identifier — end of validity period."
    )

    date: datetime | None = Field(None, description="When history was recorded or last updated.")
    name: str | None = Field(None, description="The family member will typically have a name.")
    relationship: FamilyMemberHistoryCodeableConceptInput = Field(
        ..., description="Relationship to the subject (e.g. father, mother, sibling)."
    )
    sex: FamilyMemberHistoryCodeableConceptInput | None = Field(
        None, description="male | female | other | unknown."
    )

    # born[x] (0..1 choice: Period | date | string)
    born_period_start: datetime | None = Field(None, description="born[x]: Period — start.")
    born_period_end: datetime | None = Field(None, description="born[x]: Period — end.")
    born_date: py_date | None = Field(None, description="born[x]: date — date of birth.")
    born_string: str | None = Field(None, description="born[x]: string — free-text birth date/period.")

    # age[x] (0..1 choice: Age | Range | string)
    age_age_value: float | None = Field(None, description="age[x]: Age — numeric value.")
    age_age_comparator: FamilyMemberHistoryQuantityComparator | None = Field(
        None, description="age[x]: Age — < | <= | >= | >."
    )
    age_age_unit: str | None = Field(None, description="age[x]: Age — unit string.")
    age_age_system: str | None = Field(None, description="age[x]: Age — system URI.")
    age_age_code: str | None = Field(None, description="age[x]: Age — unit code.")

    age_range_low_value: float | None = Field(None, description="age[x]: Range — low value.")
    age_range_low_unit: str | None = Field(None, description="age[x]: Range — low unit.")
    age_range_low_system: str | None = Field(None, description="age[x]: Range — low system.")
    age_range_low_code: str | None = Field(None, description="age[x]: Range — low code.")
    age_range_high_value: float | None = Field(None, description="age[x]: Range — high value.")
    age_range_high_unit: str | None = Field(None, description="age[x]: Range — high unit.")
    age_range_high_system: str | None = Field(None, description="age[x]: Range — high system.")
    age_range_high_code: str | None = Field(None, description="age[x]: Range — high code.")

    age_string: str | None = Field(None, description="age[x]: string — free-text age.")
    estimated_age: bool | None = Field(None, description="Whether age is estimated.")

    # deceased[x] (0..1 choice: boolean | Age | Range | date | string)
    deceased_boolean: bool | None = Field(None, description="deceased[x]: boolean — whether deceased.")
    deceased_age_value: float | None = Field(None, description="deceased[x]: Age — age at death value.")
    deceased_age_comparator: FamilyMemberHistoryQuantityComparator | None = Field(
        None, description="deceased[x]: Age — comparator."
    )
    deceased_age_unit: str | None = Field(None, description="deceased[x]: Age — unit string.")
    deceased_age_system: str | None = Field(None, description="deceased[x]: Age — system URI.")
    deceased_age_code: str | None = Field(None, description="deceased[x]: Age — unit code.")

    deceased_range_low_value: float | None = Field(None, description="deceased[x]: Range — low value.")
    deceased_range_low_unit: str | None = Field(None, description="deceased[x]: Range — low unit.")
    deceased_range_low_system: str | None = Field(None, description="deceased[x]: Range — low system.")
    deceased_range_low_code: str | None = Field(None, description="deceased[x]: Range — low code.")
    deceased_range_high_value: float | None = Field(None, description="deceased[x]: Range — high value.")
    deceased_range_high_unit: str | None = Field(None, description="deceased[x]: Range — high unit.")
    deceased_range_high_system: str | None = Field(None, description="deceased[x]: Range — high system.")
    deceased_range_high_code: str | None = Field(None, description="deceased[x]: Range — high code.")

    deceased_date: py_date | None = Field(None, description="deceased[x]: date — date of death.")
    deceased_string: str | None = Field(None, description="deceased[x]: string — free-text death date/age.")

    reason_code: list[FamilyMemberHistoryReasonCodeInput] | None = Field(
        None, description="Why was family member history performed? (0..* CodeableConcept)"
    )
    reason_reference: list[FamilyMemberHistoryReasonReferenceInput] | None = Field(
        None, description="Why was family member history performed? (0..* Reference)"
    )
    note: list[FamilyMemberHistoryNoteInput] | None = Field(
        None, description="General note about related person."
    )
    condition: list[FamilyMemberHistoryConditionInput] | None = Field(
        None, description="Condition that the related person had."
    )
    extension: list[dict[str, Any]] | None = Field(
        None, description="May be used to represent additional information that is not part of the basic definition."
    )


class FamilyMemberHistoryPatchSchema(BaseModel):
    """Request schema for partially updating a FamilyMemberHistory resource."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "status": "completed",
                "note": [
                    {
                        "text": "Updated family history with additional details.",
                        "time": "2026-02-01T12:00:00Z",
                    }
                ],
            }
        },
    )

    identifier: list[FamilyMemberHistoryIdentifierInput] | None = None
    instantiates_canonical: list[str] | None = None
    instantiates_uri: list[str] | None = None

    status: FamilyMemberHistoryStatus | None = None
    data_absent_reason: FamilyMemberHistoryCodeableConceptInput | None = None

    patient: str | None = None
    patient_display: str | None = None
    patient_identifier_use: IdentifierUse | None = None
    patient_identifier_type_system: str | None = None
    patient_identifier_type_version: str | None = None
    patient_identifier_type_code: str | None = None
    patient_identifier_type_display: str | None = None
    patient_identifier_type_user_selected: bool | None = None
    patient_identifier_type_text: str | None = None
    patient_identifier_system: str | None = None
    patient_identifier_value: str | None = None
    patient_identifier_period_start: datetime | None = None
    patient_identifier_period_end: datetime | None = None

    date: datetime | None = None
    name: str | None = None
    relationship: FamilyMemberHistoryCodeableConceptInput | None = None
    sex: FamilyMemberHistoryCodeableConceptInput | None = None

    born_period_start: datetime | None = None
    born_period_end: datetime | None = None
    born_date: py_date | None = None
    born_string: str | None = None

    age_age_value: float | None = None
    age_age_comparator: FamilyMemberHistoryQuantityComparator | None = None
    age_age_unit: str | None = None
    age_age_system: str | None = None
    age_age_code: str | None = None

    age_range_low_value: float | None = None
    age_range_low_unit: str | None = None
    age_range_low_system: str | None = None
    age_range_low_code: str | None = None
    age_range_high_value: float | None = None
    age_range_high_unit: str | None = None
    age_range_high_system: str | None = None
    age_range_high_code: str | None = None

    age_string: str | None = None
    estimated_age: bool | None = None

    deceased_boolean: bool | None = None
    deceased_age_value: float | None = None
    deceased_age_comparator: FamilyMemberHistoryQuantityComparator | None = None
    deceased_age_unit: str | None = None
    deceased_age_system: str | None = None
    deceased_age_code: str | None = None

    deceased_range_low_value: float | None = None
    deceased_range_low_unit: str | None = None
    deceased_range_low_system: str | None = None
    deceased_range_low_code: str | None = None
    deceased_range_high_value: float | None = None
    deceased_range_high_unit: str | None = None
    deceased_range_high_system: str | None = None
    deceased_range_high_code: str | None = None

    deceased_date: py_date | None = None
    deceased_string: str | None = None

    reason_code: list[FamilyMemberHistoryReasonCodeInput] | None = None
    reason_reference: list[FamilyMemberHistoryReasonReferenceInput] | None = None
    note: list[FamilyMemberHistoryNoteInput] | None = None
    condition: list[FamilyMemberHistoryConditionInput] | None = None
    extension: list[dict[str, Any]] | None = None
