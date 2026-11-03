from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.immunization_evaluation.enums import ImmunizationEvaluationStatus
from app.schemas.immunization_evaluation.input.codeable_concept import (
    ImmunizationEvaluationCodeableConceptInput,
)
from app.schemas.immunization_evaluation.input.identifier import (
    ImmunizationEvaluationIdentifierInput,
)
from app.schemas.immunization_evaluation.input.reference import (
    ImmunizationEvaluationAuthorityInput,
    ImmunizationEvaluationImmunizationEventInput,
    ImmunizationEvaluationPatientInput,
)

_CREATE_EXAMPLE: dict[str, Any] = {
    "status": "completed",
    "patient": {
        "reference": "Patient/10001",
        "reference_display": "Jane Doe",
    },
    "date": "2026-02-01T10:00:00Z",
    "authority": {
        "reference": "Organization/190001",
        "reference_display": "CDC",
    },
    "target_disease": {
        "coding": [
            {
                "system": "http://snomed.info/sct",
                "code": "14189004",
                "display": "Measles",
            }
        ],
        "text": "Measles",
    },
    "immunization_event": {
        "reference": "Immunization/330001",
        "reference_display": "MMR vaccine dose 1",
    },
    "dose_status": {
        "coding": [
            {
                "system": "http://terminology.hl7.org/CodeSystem/immunization-evaluation-dose-status",
                "code": "valid",
                "display": "Valid",
            }
        ],
        "text": "Valid",
    },
    "series": "2-dose MMR",
    "dose_number_positive_int": 1,
    "series_doses_positive_int": 2,
}


class ImmunizationEvaluationCreateSchema(BaseModel):
    """Payload to create a new ImmunizationEvaluation resource."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": _CREATE_EXAMPLE},
    )

    status: ImmunizationEvaluationStatus = Field(
        ..., description="completed | entered-in-error."
    )
    patient: ImmunizationEvaluationPatientInput = Field(
        ..., description="Who this evaluation is for (Reference(Patient))."
    )
    date: datetime | None = Field(
        None, description="Date evaluation was performed."
    )
    authority: ImmunizationEvaluationAuthorityInput | None = Field(
        None, description="Who is responsible for protocol (Reference(Organization))."
    )
    target_disease: ImmunizationEvaluationCodeableConceptInput = Field(
        ..., description="Evaluation target disease."
    )
    immunization_event: ImmunizationEvaluationImmunizationEventInput = Field(
        ..., description="Immunization event being evaluated (Reference(Immunization))."
    )
    dose_status: ImmunizationEvaluationCodeableConceptInput = Field(
        ..., description="Valid | notvalid status."
    )
    dose_status_reason: list[ImmunizationEvaluationCodeableConceptInput] | None = Field(
        None, description="Reason for dose status."
    )
    description: str | None = Field(
        None, description="Evaluation notes or outcome description."
    )
    series: str | None = Field(
        None, description="Name of vaccine series."
    )
    dose_number_positive_int: int | None = Field(
        None, description="Dose number within series (positive int)."
    )
    dose_number_string: str | None = Field(
        None, description="Dose number within series (string)."
    )
    series_doses_positive_int: int | None = Field(
        None, description="Recommended number of doses for series (positive int)."
    )
    series_doses_string: str | None = Field(
        None, description="Recommended number of doses for series (string)."
    )
    identifier: list[ImmunizationEvaluationIdentifierInput] | None = Field(
        None, description="Business identifier."
    )
    extension: list[dict[str, Any]] | None = Field(
        None, description="May be used to represent additional information that is not part of the basic definition."
    )

    @model_validator(mode="after")
    def _validate_choices(self) -> "ImmunizationEvaluationCreateSchema":
        if self.dose_number_positive_int is not None and self.dose_number_string is not None:
            raise ValueError("Only one of dose_number_positive_int or dose_number_string can be set")
        if self.series_doses_positive_int is not None and self.series_doses_string is not None:
            raise ValueError("Only one of series_doses_positive_int or series_doses_string can be set")
        return self


class ImmunizationEvaluationPatchSchema(BaseModel):
    """Payload to partially update an ImmunizationEvaluation resource."""

    model_config = ConfigDict(extra="forbid")

    status: ImmunizationEvaluationStatus | None = Field(
        None, description="completed | entered-in-error."
    )
    patient: ImmunizationEvaluationPatientInput | None = Field(
        None, description="Who this evaluation is for (Reference(Patient))."
    )
    date: datetime | None = Field(
        None, description="Date evaluation was performed."
    )
    authority: ImmunizationEvaluationAuthorityInput | None = Field(
        None, description="Who is responsible for protocol (Reference(Organization))."
    )
    target_disease: ImmunizationEvaluationCodeableConceptInput | None = Field(
        None, description="Evaluation target disease."
    )
    immunization_event: ImmunizationEvaluationImmunizationEventInput | None = Field(
        None, description="Immunization event being evaluated (Reference(Immunization))."
    )
    dose_status: ImmunizationEvaluationCodeableConceptInput | None = Field(
        None, description="Valid | notvalid status."
    )
    dose_status_reason: list[ImmunizationEvaluationCodeableConceptInput] | None = Field(
        None, description="Reason for dose status."
    )
    description: str | None = Field(
        None, description="Evaluation notes or outcome description."
    )
    series: str | None = Field(
        None, description="Name of vaccine series."
    )
    dose_number_positive_int: int | None = Field(
        None, description="Dose number within series (positive int)."
    )
    dose_number_string: str | None = Field(
        None, description="Dose number within series (string)."
    )
    series_doses_positive_int: int | None = Field(
        None, description="Recommended number of doses for series (positive int)."
    )
    series_doses_string: str | None = Field(
        None, description="Recommended number of doses for series (string)."
    )
    identifier: list[ImmunizationEvaluationIdentifierInput] | None = Field(
        None, description="Business identifier."
    )
    extension: list[dict[str, Any]] | None = Field(
        None, description="May be used to represent additional information that is not part of the basic definition."
    )

    @model_validator(mode="after")
    def _validate_choices(self) -> "ImmunizationEvaluationPatchSchema":
        if self.dose_number_positive_int is not None and self.dose_number_string is not None:
            raise ValueError("Only one of dose_number_positive_int or dose_number_string can be set")
        if self.series_doses_positive_int is not None and self.series_doses_string is not None:
            raise ValueError("Only one of series_doses_positive_int or series_doses_string can be set")
        return self
