from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import MedicationStatementStatus
from app.schemas.medication_statement.input.codeable_concept import (
    MedicationStatementCodeableConceptInput,
)
from app.schemas.medication_statement.input.dosage import MedicationStatementDosageInput
from app.schemas.medication_statement.input.identifier import (
    MedicationStatementIdentifierInput,
)
from app.schemas.medication_statement.input.note import MedicationStatementNoteInput
from app.schemas.medication_statement.input.reason_code import (
    MedicationStatementReasonCodeInput,
)
from app.schemas.medication_statement.input.reference import (
    MedicationStatementBasedOnInput,
    MedicationStatementContextInput,
    MedicationStatementDerivedFromInput,
    MedicationStatementInformationSourceInput,
    MedicationStatementMedicationReferenceInput,
    MedicationStatementPartOfInput,
    MedicationStatementReasonReferenceInput,
    MedicationStatementSubjectInput,
)
from app.schemas.medication_statement.input.status_reason import (
    MedicationStatementStatusReasonInput,
)

_CREATE_EXAMPLE: dict[str, Any] = {
    "status": "active",
    "medication_codeable_concept": {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "372687004",
                "display": "Amoxicillin 500mg capsule",
            }
        ],
        "text": "Amoxicillin 500mg capsule",
    },
    "subject": {
        "reference": "Patient/10001",
        "reference_display": "Jane Doe",
    },
    "effective_date_time": "2026-01-15T10:00:00Z",
    "date_asserted": "2026-01-15T10:00:00Z",
    "information_source": {
        "reference": "Patient/10001",
        "reference_display": "Jane Doe",
    },
    "note": [
        {
            "text": "Patient reports taking medication regularly with meals.",
        }
    ],
    "dosage": [
        {
            "text": "Take 1 capsule by mouth three times daily with food.",
        }
    ],
}


class MedicationStatementCreateSchema(BaseModel):
    """Request schema for creating a new MedicationStatement resource."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": _CREATE_EXAMPLE},
    )

    extension: list[dict] | None = Field(None, description="Resource-level FHIR extensions.")
    identifier: list[MedicationStatementIdentifierInput] | None = Field(
        None, description="External identifier for this record."
    )
    based_on: list[MedicationStatementBasedOnInput] | None = Field(
        None, description="Fulfils plan, proposal or order."
    )
    part_of: list[MedicationStatementPartOfInput] | None = Field(
        None, description="Part of referenced event."
    )
    status: MedicationStatementStatus = Field(
        ...,
        description="active | completed | entered-in-error | intended | stopped | on-hold | unknown | not-taken.",
    )
    status_reason: list[MedicationStatementStatusReasonInput] | None = Field(
        None, description="Reason for current status."
    )
    category: MedicationStatementCodeableConceptInput | None = Field(
        None, description="Type of medication statement."
    )

    # medication[x] (1..1 choice)
    medication_codeable_concept: MedicationStatementCodeableConceptInput | None = Field(
        None, description="What medication was taken — as CodeableConcept."
    )
    medication_reference: MedicationStatementMedicationReferenceInput | None = Field(
        None, description="What medication was taken — as Reference(Medication)."
    )

    # subject (1..1 Reference(Patient|Group))
    subject: MedicationStatementSubjectInput = Field(
        ..., description="Who is/was taking the medication. Reference(Patient|Group)."
    )
    context: MedicationStatementContextInput | None = Field(
        None, description="Encounter / Episode associated with MedicationStatement."
    )
    effective_date_time: datetime | None = Field(
        None, description="The date/time or interval when the medication is/was/will be taken."
    )
    effective_period_start: datetime | None = Field(
        None, description="Effective period start."
    )
    effective_period_end: datetime | None = Field(
        None, description="Effective period end."
    )
    date_asserted: datetime | None = Field(
        None, description="When the statement was asserted/recorded."
    )
    information_source: MedicationStatementInformationSourceInput | None = Field(
        None, description="Person or organization that provided information about the medication."
    )
    derived_from: list[MedicationStatementDerivedFromInput] | None = Field(
        None, description="Additional supporting information."
    )
    reason_code: list[MedicationStatementReasonCodeInput] | None = Field(
        None, description="Reason for medication administration, coded."
    )
    reason_reference: list[MedicationStatementReasonReferenceInput] | None = Field(
        None, description="Condition or observation that supports why the medication is being/was taken."
    )
    note: list[MedicationStatementNoteInput] | None = Field(
        None, description="Further information about the statement."
    )
    dosage: list[MedicationStatementDosageInput] | None = Field(
        None, description="Details of how medication is/was taken or should be taken."
    )


class MedicationStatementPatchSchema(BaseModel):
    """Request schema for patching an existing MedicationStatement resource."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"status": "completed"}},
    )

    extension: list[dict] | None = Field(None, description="Resource-level FHIR extensions.")
    identifier: list[MedicationStatementIdentifierInput] | None = Field(
        None, description="External identifier for this record."
    )
    based_on: list[MedicationStatementBasedOnInput] | None = Field(
        None, description="Fulfils plan, proposal or order."
    )
    part_of: list[MedicationStatementPartOfInput] | None = Field(
        None, description="Part of referenced event."
    )
    status: MedicationStatementStatus | None = Field(
        None,
        description="active | completed | entered-in-error | intended | stopped | on-hold | unknown | not-taken.",
    )
    status_reason: list[MedicationStatementStatusReasonInput] | None = Field(
        None, description="Reason for current status."
    )
    category: MedicationStatementCodeableConceptInput | None = Field(
        None, description="Type of medication statement."
    )
    medication_codeable_concept: MedicationStatementCodeableConceptInput | None = Field(
        None, description="What medication was taken — as CodeableConcept."
    )
    medication_reference: MedicationStatementMedicationReferenceInput | None = Field(
        None, description="What medication was taken — as Reference(Medication)."
    )
    subject: MedicationStatementSubjectInput | None = Field(
        None, description="Who is/was taking the medication. Reference(Patient|Group)."
    )
    context: MedicationStatementContextInput | None = Field(
        None, description="Encounter / Episode associated with MedicationStatement."
    )
    effective_date_time: datetime | None = Field(
        None, description="The date/time or interval when the medication is/was/will be taken."
    )
    effective_period_start: datetime | None = Field(
        None, description="Effective period start."
    )
    effective_period_end: datetime | None = Field(
        None, description="Effective period end."
    )
    date_asserted: datetime | None = Field(
        None, description="When the statement was asserted/recorded."
    )
    information_source: MedicationStatementInformationSourceInput | None = Field(
        None, description="Person or organization that provided information about the medication."
    )
    derived_from: list[MedicationStatementDerivedFromInput] | None = Field(
        None, description="Additional supporting information."
    )
    reason_code: list[MedicationStatementReasonCodeInput] | None = Field(
        None, description="Reason for medication administration, coded."
    )
    reason_reference: list[MedicationStatementReasonReferenceInput] | None = Field(
        None, description="Condition or observation that supports why the medication is being/was taken."
    )
    note: list[MedicationStatementNoteInput] | None = Field(
        None, description="Further information about the statement."
    )
    dosage: list[MedicationStatementDosageInput] | None = Field(
        None, description="Details of how medication is/was taken or should be taken."
    )
