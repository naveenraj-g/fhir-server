from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import ImmunizationStatus
from app.schemas.immunization.input.codeable_concept import (
    ImmunizationCodeableConceptInput,
)
from app.schemas.immunization.input.education import ImmunizationEducationInput
from app.schemas.immunization.input.identifier import (
    ImmunizationIdentifierInput,
)
from app.schemas.immunization.input.note import ImmunizationNoteInput
from app.schemas.immunization.input.performer import ImmunizationPerformerInput
from app.schemas.immunization.input.protocol_applied import (
    ImmunizationProtocolAppliedInput,
)
from app.schemas.immunization.input.quantity import SimpleQuantityInput
from app.schemas.immunization.input.reaction import ImmunizationReactionInput
from app.schemas.immunization.input.reference import (
    ImmunizationEncounterInput,
    ImmunizationLocationInput,
    ImmunizationManufacturerInput,
    ImmunizationPatientInput,
    ImmunizationReasonReferenceInput,
)

_CREATE_EXAMPLE: dict[str, Any] = {
    "status": "completed",
    "vaccine_code": {
        "coding": [
            {
                "system": "http://hl7.org/fhir/sid/cvx",
                "code": "197",
                "display": "influenza, high-dose, quadrivalent",
            }
        ],
        "text": "Fluzone High-Dose Quadrivalent",
    },
    "patient": {
        "reference": "Patient/10001",
        "reference_display": "Jane Doe",
    },
    "occurrence_date_time": "2026-01-15T09:30:00Z",
    "recorded": "2026-01-15T09:35:00Z",
    "primary_source": True,
    "lot_number": "AA78910",
    "expiration_date": "2026-12-31",
    "dose_quantity": {
        "value": 0.5,
        "unit": "mL",
        "system": "http://unitsofmeasure.org",
        "code": "mL",
    },
    "performer": [
        {
            "function": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v2-0443",
                        "code": "AP",
                        "display": "Administering Provider",
                    }
                ],
                "text": "Administering Provider",
            },
            "actor": {
                "reference": "Practitioner/30001",
                "reference_display": "Dr. Sarah Smith",
            },
        }
    ],
    "note": [
        {
            "text": "Patient tolerated immunization well, no adverse reactions noted.",
        }
    ],
}


class ImmunizationCreateSchema(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": _CREATE_EXAMPLE},
    )

    status: ImmunizationStatus = Field(
        ...,
        description="completed | entered-in-error | not-done.",
    )
    status_reason: ImmunizationCodeableConceptInput | None = Field(
        None, description="Reason not done."
    )
    vaccine_code: ImmunizationCodeableConceptInput = Field(
        ..., description="Vaccine product administered."
    )
    patient: ImmunizationPatientInput = Field(
        ..., description="Who was immunized (Reference(Patient))."
    )
    encounter: ImmunizationEncounterInput | None = Field(
        None, description="Encounter the immunization was part of (Reference(Encounter))."
    )
    occurrence_date_time: datetime | None = Field(
        None, description="Vaccine administration date/time."
    )
    occurrence_string: str | None = Field(
        None, description="Vaccine administration date text."
    )
    recorded: datetime | None = Field(
        None, description="When the immunization was first captured in the record."
    )
    primary_source: bool | None = Field(
        None, description="Indicates context the data was recorded in."
    )
    report_origin: ImmunizationCodeableConceptInput | None = Field(
        None, description="Indicates the source of a secondarily reported record."
    )
    location: ImmunizationLocationInput | None = Field(
        None, description="Where immunization occurred (Reference(Location))."
    )
    manufacturer: ImmunizationManufacturerInput | None = Field(
        None, description="Vaccine manufacturer (Reference(Organization))."
    )
    lot_number: str | None = Field(
        None, description="Vaccine lot number."
    )
    expiration_date: date | None = Field(
        None, description="Vaccine expiration date."
    )
    site: ImmunizationCodeableConceptInput | None = Field(
        None, description="Body site where vaccine was administered."
    )
    route: ImmunizationCodeableConceptInput | None = Field(
        None, description="How vaccine entered body."
    )
    dose_quantity: SimpleQuantityInput | None = Field(
        None, description="Amount of vaccine administered."
    )
    is_subpotent: bool | None = Field(
        None, description="Dose potency."
    )
    funding_source: ImmunizationCodeableConceptInput | None = Field(
        None, description="Funding source for the vaccine."
    )

    identifier: list[ImmunizationIdentifierInput] | None = Field(
        None, description="Business identifier."
    )
    performer: list[ImmunizationPerformerInput] | None = Field(
        None, description="Who performed event."
    )
    note: list[ImmunizationNoteInput] | None = Field(
        None, description="Additional notes."
    )
    reason_code: list[ImmunizationCodeableConceptInput] | None = Field(
        None, description="Why immunization occurred."
    )
    reason_reference: list[ImmunizationReasonReferenceInput] | None = Field(
        None, description="Why immunization occurred (Reference(Condition|Observation|DiagnosticReport))."
    )
    subpotent_reason: list[ImmunizationCodeableConceptInput] | None = Field(
        None, description="Reason for being subpotent."
    )
    education: list[ImmunizationEducationInput] | None = Field(
        None, description="Educational material presented to person receiving vaccine."
    )
    program_eligibility: list[ImmunizationCodeableConceptInput] | None = Field(
        None, description="Patient eligibility for a specific program."
    )
    reaction: list[ImmunizationReactionInput] | None = Field(
        None, description="Details of a reaction that follows immunization."
    )
    protocol_applied: list[ImmunizationProtocolAppliedInput] | None = Field(
        None, description="Protocol followed by the provider."
    )


class ImmunizationPatchSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ImmunizationStatus | None = Field(
        None, description="completed | entered-in-error | not-done."
    )
    status_reason: ImmunizationCodeableConceptInput | None = Field(
        None, description="Reason not done."
    )
    vaccine_code: ImmunizationCodeableConceptInput | None = Field(
        None, description="Vaccine product administered."
    )
    patient: ImmunizationPatientInput | None = Field(
        None, description="Who was immunized (Reference(Patient))."
    )
    encounter: ImmunizationEncounterInput | None = Field(
        None, description="Encounter the immunization was part of (Reference(Encounter))."
    )
    occurrence_date_time: datetime | None = Field(
        None, description="Vaccine administration date/time."
    )
    occurrence_string: str | None = Field(
        None, description="Vaccine administration date text."
    )
    recorded: datetime | None = Field(
        None, description="When the immunization was first captured in the record."
    )
    primary_source: bool | None = Field(
        None, description="Indicates context the data was recorded in."
    )
    report_origin: ImmunizationCodeableConceptInput | None = Field(
        None, description="Indicates the source of a secondarily reported record."
    )
    location: ImmunizationLocationInput | None = Field(
        None, description="Where immunization occurred (Reference(Location))."
    )
    manufacturer: ImmunizationManufacturerInput | None = Field(
        None, description="Vaccine manufacturer (Reference(Organization))."
    )
    lot_number: str | None = Field(
        None, description="Vaccine lot number."
    )
    expiration_date: date | None = Field(
        None, description="Vaccine expiration date."
    )
    site: ImmunizationCodeableConceptInput | None = Field(
        None, description="Body site where vaccine was administered."
    )
    route: ImmunizationCodeableConceptInput | None = Field(
        None, description="How vaccine entered body."
    )
    dose_quantity: SimpleQuantityInput | None = Field(
        None, description="Amount of vaccine administered."
    )
    is_subpotent: bool | None = Field(
        None, description="Dose potency."
    )
    funding_source: ImmunizationCodeableConceptInput | None = Field(
        None, description="Funding source for the vaccine."
    )

    identifier: list[ImmunizationIdentifierInput] | None = Field(
        None, description="Business identifier."
    )
    performer: list[ImmunizationPerformerInput] | None = Field(
        None, description="Who performed event."
    )
    note: list[ImmunizationNoteInput] | None = Field(
        None, description="Additional notes."
    )
    reason_code: list[ImmunizationCodeableConceptInput] | None = Field(
        None, description="Why immunization occurred."
    )
    reason_reference: list[ImmunizationReasonReferenceInput] | None = Field(
        None, description="Why immunization occurred (Reference(Condition|Observation|DiagnosticReport))."
    )
    subpotent_reason: list[ImmunizationCodeableConceptInput] | None = Field(
        None, description="Reason for being subpotent."
    )
    education: list[ImmunizationEducationInput] | None = Field(
        None, description="Educational material presented to person receiving vaccine."
    )
    program_eligibility: list[ImmunizationCodeableConceptInput] | None = Field(
        None, description="Patient eligibility for a specific program."
    )
    reaction: list[ImmunizationReactionInput] | None = Field(
        None, description="Details of a reaction that follows immunization."
    )
    protocol_applied: list[ImmunizationProtocolAppliedInput] | None = Field(
        None, description="Protocol followed by the provider."
    )
