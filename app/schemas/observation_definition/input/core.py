from pydantic import BaseModel, ConfigDict, Field

from app.models.observation_definition.enums import (
    ObservationDefinitionPermittedDataType,
)

from .codeable_concept import ObservationDefinitionCodeableConceptInput
from .identifier import ObservationDefinitionIdentifierInput
from .qualified_interval import ObservationDefinitionQualifiedIntervalInput
from .quantitative_details import ObservationDefinitionQuantitativeDetailsInput


class ObservationDefinitionCreateSchema(BaseModel):
    """ObservationDefinition creation schema. Accepts full nested payload."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "code": {
                    "coding": [
                        {
                            "system": "http://loinc.org",
                            "code": "15074-8",
                            "display": "Glucose [Moles/volume] in Blood",
                        }
                    ],
                    "text": "Glucose in Blood",
                },
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                "code": "laboratory",
                                "display": "Laboratory",
                            }
                        ],
                        "text": "Laboratory",
                    }
                ],
                "permitted_data_type": ["Quantity"],
                "multiple_results_allowed": False,
                "preferred_report_name": "Blood Glucose",
                "quantitative_details": {
                    "unit": {
                        "coding": [
                            {
                                "system": "http://unitsofmeasure.org",
                                "code": "mmol/L",
                                "display": "mmol/L",
                            }
                        ],
                        "text": "mmol/L",
                    },
                    "decimal_precision": 1,
                },
                "qualified_interval": [
                    {
                        "category": "reference",
                        "range_low_value": 3.9,
                        "range_low_unit": "mmol/L",
                        "range_high_value": 5.6,
                        "range_high_unit": "mmol/L",
                        "gender": "unknown",
                    }
                ],
            }
        },
    )

    category: list[ObservationDefinitionCodeableConceptInput] | None = Field(
        None, description="General type of observation."
    )
    code: ObservationDefinitionCodeableConceptInput = Field(
        ..., description="Describes what will be observed (name/code)."
    )
    identifier: list[ObservationDefinitionIdentifierInput] | None = Field(
        None, description="Unique identifier for this artifact."
    )
    permitted_data_type: list[ObservationDefinitionPermittedDataType] | None = Field(
        None, description="Data types allowed for value element."
    )
    multiple_results_allowed: bool | None = Field(
        None, description="Multiple results allowed."
    )
    method: ObservationDefinitionCodeableConceptInput | None = Field(
        None, description="Method or technique used."
    )
    preferred_report_name: str | None = Field(
        None, description="Preferred report name."
    )
    quantitative_details: ObservationDefinitionQuantitativeDetailsInput | None = Field(
        None, description="Characteristics for quantitative results."
    )
    qualified_interval: list[ObservationDefinitionQualifiedIntervalInput] | None = Field(
        None, description="Ranges of results qualified by context."
    )
    valid_coded_value_set: str | None = Field(
        None, description="Valid coded results ValueSet reference (e.g. ValueSet/1)."
    )
    valid_coded_value_set_display: str | None = Field(
        None, description="Display name for valid coded results ValueSet."
    )
    normal_coded_value_set: str | None = Field(
        None, description="Normal coded results ValueSet reference."
    )
    normal_coded_value_set_display: str | None = Field(
        None, description="Display name for normal coded results ValueSet."
    )
    abnormal_coded_value_set: str | None = Field(
        None, description="Abnormal coded results ValueSet reference."
    )
    abnormal_coded_value_set_display: str | None = Field(
        None, description="Display name for abnormal coded results ValueSet."
    )
    critical_coded_value_set: str | None = Field(
        None, description="Critical coded results ValueSet reference."
    )
    critical_coded_value_set_display: str | None = Field(
        None, description="Display name for critical coded results ValueSet."
    )
    extension: list[dict] | None = Field(
        None, description="FHIR extension list."
    )


class ObservationDefinitionPatchSchema(BaseModel):
    """ObservationDefinition patch schema — all fields optional."""

    model_config = ConfigDict(extra="forbid")

    category: list[ObservationDefinitionCodeableConceptInput] | None = Field(
        None, description="General type of observation."
    )
    code: ObservationDefinitionCodeableConceptInput | None = Field(
        None, description="Describes what will be observed (name/code)."
    )
    identifier: list[ObservationDefinitionIdentifierInput] | None = Field(
        None, description="Unique identifier for this artifact."
    )
    permitted_data_type: list[ObservationDefinitionPermittedDataType] | None = Field(
        None, description="Data types allowed for value element."
    )
    multiple_results_allowed: bool | None = Field(
        None, description="Multiple results allowed."
    )
    method: ObservationDefinitionCodeableConceptInput | None = Field(
        None, description="Method or technique used."
    )
    preferred_report_name: str | None = Field(
        None, description="Preferred report name."
    )
    quantitative_details: ObservationDefinitionQuantitativeDetailsInput | None = Field(
        None, description="Characteristics for quantitative results."
    )
    qualified_interval: list[ObservationDefinitionQualifiedIntervalInput] | None = Field(
        None, description="Ranges of results qualified by context."
    )
    valid_coded_value_set: str | None = Field(
        None, description="Valid coded results ValueSet reference."
    )
    valid_coded_value_set_display: str | None = Field(
        None, description="Display name for valid coded results ValueSet."
    )
    normal_coded_value_set: str | None = Field(
        None, description="Normal coded results ValueSet reference."
    )
    normal_coded_value_set_display: str | None = Field(
        None, description="Display name for normal coded results ValueSet."
    )
    abnormal_coded_value_set: str | None = Field(
        None, description="Abnormal coded results ValueSet reference."
    )
    abnormal_coded_value_set_display: str | None = Field(
        None, description="Display name for abnormal coded results ValueSet."
    )
    critical_coded_value_set: str | None = Field(
        None, description="Critical coded results ValueSet reference."
    )
    critical_coded_value_set_display: str | None = Field(
        None, description="Display name for critical coded results ValueSet."
    )
    extension: list[dict] | None = Field(
        None, description="FHIR extension list."
    )
