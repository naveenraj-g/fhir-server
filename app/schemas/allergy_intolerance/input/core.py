from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.allergy_intolerance.enums import (
    AllergyIntoleranceCategory,
    AllergyIntoleranceCriticality,
    AllergyIntoleranceSeverity,
    AllergyIntoleranceType,
)
from app.schemas.allergy_intolerance.input.codeable_concept import (
    AllergyIntoleranceCodeableConceptInput,
)
from app.schemas.allergy_intolerance.input.identifier import (
    AllergyIntoleranceIdentifierInput,
)
from app.schemas.allergy_intolerance.input.note import (
    AllergyIntoleranceNoteInput,
)
from app.schemas.allergy_intolerance.input.reaction import (
    AllergyIntoleranceReactionInput,
)

_CREATE_EXAMPLE = {
    "clinical_status": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical",
                "code": "active",
                "display": "Active",
            }
        ],
        "text": "Active",
    },
    "verification_status": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification",
                "code": "confirmed",
                "display": "Confirmed",
            }
        ],
        "text": "Confirmed",
    },
    "type": "allergy",
    "category": ["food"],
    "criticality": "high",
    "code": {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "227493005",
                "display": "Cashew nut allergy",
            }
        ],
        "text": "Cashew nut allergy",
    },
    "patient": "Patient/10001",
    "patient_display": "Jane Doe",
    "encounter": "Encounter/20001",
    "encounter_display": "Annual Physical",
    "onset_date_time": "2023-01-15T09:30:00Z",
    "recorded_date": "2023-01-15T10:00:00Z",
    "recorder": "Practitioner/30001",
    "recorder_display": "Dr. Alice Smith",
    "asserter": "Patient/10001",
    "asserter_display": "Jane Doe",
    "last_occurrence": "2023-06-01T12:00:00Z",
    "note": [
        {
            "text": "Patient experienced severe urticaria after cashew ingestion.",
            "time": "2023-01-15T10:05:00Z",
            "author_string": "Dr. Alice Smith",
        }
    ],
    "reaction": [
        {
            "substance": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "227493005",
                        "display": "Cashew nut",
                    }
                ],
                "text": "Cashew nut",
            },
            "manifestation": [
                {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "64305001",
                            "display": "Urticaria",
                        }
                    ],
                    "text": "Urticaria",
                }
            ],
            "description": "Severe hives on face and neck",
            "onset": "2023-01-15T09:40:00Z",
            "severity": "severe",
            "exposure_route": {
                "coding": [
                    {
                        "system": "http://snomed.info/sct",
                        "code": "26643006",
                        "display": "Oral route",
                    }
                ],
                "text": "Oral route",
            },
            "note": [
                {
                    "text": "Resolved after administration of intramuscular epinephrine.",
                    "time": "2023-01-15T10:15:00Z",
                }
            ],
        }
    ],
    "identifier": [
        {
            "use": "official",
            "system": "http://example.org/allergy-ids",
            "value": "ALG-12345",
        }
    ],
    "extension": [],
}


class AllergyIntoleranceCreateSchema(BaseModel):
    """Payload for POST /api/fhir/v1/allergy-intolerances.

    Tenant scoping (org_id) and created_by come from the verified JWT (actor.org_id / actor.sub).
    """

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": _CREATE_EXAMPLE},
    )

    clinical_status: AllergyIntoleranceCodeableConceptInput | None = Field(
        None, description="active | recurrence | relapse | inactive | remission | resolved."
    )
    verification_status: AllergyIntoleranceCodeableConceptInput | None = Field(
        None, description="unconfirmed | presumed | confirmed | refuted | entered-in-error."
    )
    type: AllergyIntoleranceType | None = Field(
        None, description="allergy | intolerance - Underlying mechanism."
    )
    category: list[AllergyIntoleranceCategory] | None = Field(
        None, description="food | medication | environment | biologic."
    )
    criticality: AllergyIntoleranceCriticality | None = Field(
        None, description="low | high | unable-to-assess."
    )
    code: AllergyIntoleranceCodeableConceptInput | None = Field(
        None, description="Code that identifies the allergy or intolerance."
    )

    # Reference(Patient) - 1..1
    patient: str = Field(
        ..., description="Who the sensitivity is for. Reference(Patient)"
    )
    patient_display: str | None = Field(
        None, description="Display text for patient."
    )

    # Reference(Encounter) - 0..1
    encounter: str | None = Field(
        None, description="Encounter when allergy or intolerance was asserted. Reference(Encounter)"
    )
    encounter_display: str | None = Field(
        None, description="Display text for encounter."
    )

    # Choice onset[x]
    onset_date_time: datetime | None = Field(
        None, description="When allergy or intolerance was identified (dateTime)."
    )
    onset_age: dict[str, Any] | None = Field(
        None, description="When allergy or intolerance was identified (Age/Quantity)."
    )
    onset_period_start: datetime | None = Field(
        None, description="When allergy or intolerance was identified (Period start)."
    )
    onset_period_end: datetime | None = Field(
        None, description="When allergy or intolerance was identified (Period end)."
    )
    onset_range: dict[str, Any] | None = Field(
        None, description="When allergy or intolerance was identified (Range)."
    )
    onset_string: str | None = Field(
        None, description="When allergy or intolerance was identified (string)."
    )

    recorded_date: datetime | None = Field(
        None, description="Date first version of the resource was recorded."
    )

    # Reference(recorder) - 0..1
    recorder: str | None = Field(
        None, description="Who recorded the sensitivity. Reference(Practitioner|PractitionerRole|Patient|RelatedPerson)"
    )
    recorder_display: str | None = Field(
        None, description="Display text for recorder."
    )

    # Reference(asserter) - 0..1
    asserter: str | None = Field(
        None, description="Source of the information about the allergy. Reference(Patient|RelatedPerson|Practitioner|PractitionerRole)"
    )
    asserter_display: str | None = Field(
        None, description="Display text for asserter."
    )

    last_occurrence: datetime | None = Field(
        None, description="Date(/time) of last known occurrence of a reaction."
    )
    note: list[AllergyIntoleranceNoteInput] | None = Field(
        None, description="Additional text not captured in other fields."
    )
    reaction: list[AllergyIntoleranceReactionInput] | None = Field(
        None, description="Adverse Reaction Events linked to issue."
    )
    identifier: list[AllergyIntoleranceIdentifierInput] | None = Field(
        None, description="External ids for this item."
    )
    extension: list[dict[str, Any]] | None = Field(
        None, description="Additional content defined by implementations."
    )


class AllergyIntolerancePatchSchema(BaseModel):
    """Payload for PATCH /api/fhir/v1/allergy-intolerances/{id}.

    All fields optional. Immutable fields (id, allergy_intolerance_id, created_at, tenant_id, created_by) excluded.
    """

    model_config = ConfigDict(extra="forbid")

    clinical_status: AllergyIntoleranceCodeableConceptInput | None = Field(
        None, description="active | recurrence | relapse | inactive | remission | resolved."
    )
    verification_status: AllergyIntoleranceCodeableConceptInput | None = Field(
        None, description="unconfirmed | presumed | confirmed | refuted | entered-in-error."
    )
    type: AllergyIntoleranceType | None = Field(
        None, description="allergy | intolerance - Underlying mechanism."
    )
    category: list[AllergyIntoleranceCategory] | None = Field(
        None, description="food | medication | environment | biologic."
    )
    criticality: AllergyIntoleranceCriticality | None = Field(
        None, description="low | high | unable-to-assess."
    )
    code: AllergyIntoleranceCodeableConceptInput | None = Field(
        None, description="Code that identifies the allergy or intolerance."
    )
    patient: str | None = Field(
        None, description="Who the sensitivity is for. Reference(Patient)"
    )
    patient_display: str | None = Field(
        None, description="Display text for patient."
    )
    encounter: str | None = Field(
        None, description="Encounter when allergy was asserted. Reference(Encounter)"
    )
    encounter_display: str | None = Field(
        None, description="Display text for encounter."
    )
    onset_date_time: datetime | None = Field(
        None, description="When allergy or intolerance was identified (dateTime)."
    )
    onset_age: dict[str, Any] | None = Field(
        None, description="When allergy or intolerance was identified (Age/Quantity)."
    )
    onset_period_start: datetime | None = Field(
        None, description="When allergy or intolerance was identified (Period start)."
    )
    onset_period_end: datetime | None = Field(
        None, description="When allergy or intolerance was identified (Period end)."
    )
    onset_range: dict[str, Any] | None = Field(
        None, description="When allergy or intolerance was identified (Range)."
    )
    onset_string: str | None = Field(
        None, description="When allergy or intolerance was identified (string)."
    )
    recorded_date: datetime | None = Field(
        None, description="Date first version of the resource was recorded."
    )
    recorder: str | None = Field(
        None, description="Who recorded the sensitivity. Reference(Practitioner|PractitionerRole|Patient|RelatedPerson)"
    )
    recorder_display: str | None = Field(
        None, description="Display text for recorder."
    )
    asserter: str | None = Field(
        None, description="Source of the information about the allergy. Reference(Patient|RelatedPerson|Practitioner|PractitionerRole)"
    )
    asserter_display: str | None = Field(
        None, description="Display text for asserter."
    )
    last_occurrence: datetime | None = Field(
        None, description="Date(/time) of last known occurrence of a reaction."
    )
    note: list[AllergyIntoleranceNoteInput] | None = Field(
        None, description="Additional text not captured in other fields."
    )
    reaction: list[AllergyIntoleranceReactionInput] | None = Field(
        None, description="Adverse Reaction Events linked to issue."
    )
    identifier: list[AllergyIntoleranceIdentifierInput] | None = Field(
        None, description="External ids for this item."
    )
    extension: list[dict[str, Any]] | None = Field(
        None, description="Additional content defined by implementations."
    )
