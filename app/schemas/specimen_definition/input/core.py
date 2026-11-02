from pydantic import BaseModel, ConfigDict, Field

from app.schemas.specimen_definition.input.codeable_concept import (
    SpecimenDefinitionCodeableConceptInput,
)
from app.schemas.specimen_definition.input.identifier import (
    SpecimenDefinitionIdentifierInput,
)
from app.schemas.specimen_definition.input.type_tested import (
    SpecimenDefinitionTypeTestedInput,
)


class SpecimenDefinitionCreateSchema(BaseModel):
    """Payload to create a new SpecimenDefinition resource."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "identifier": {
                    "system": "http://example.org/specimen-definitions",
                    "value": "SERUM-001",
                },
                "type_collected": {
                    "coding": [
                        {
                            "system": "http://snomed.info/sct",
                            "code": "122555007",
                            "display": "Venous blood specimen",
                        }
                    ],
                    "text": "Venous blood",
                },
                "patient_preparation": [
                    {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "726054005",
                                "display": "Fasting",
                            }
                        ],
                        "text": "12 hour fasting prior to collection",
                    }
                ],
                "time_aspect": "morning",
                "collection": [
                    {
                        "coding": [
                            {
                                "system": "http://snomed.info/sct",
                                "code": "28520004",
                                "display": "Venipuncture",
                            }
                        ],
                        "text": "Venipuncture procedure",
                    }
                ],
                "type_tested": [
                    {
                        "is_derived": True,
                        "type": {
                            "coding": [
                                {
                                    "system": "http://snomed.info/sct",
                                    "code": "119364003",
                                    "display": "Serum specimen",
                                }
                            ],
                            "text": "Serum",
                        },
                        "preference": "preferred",
                        "container": {
                            "type": {
                                "coding": [
                                    {
                                        "system": "http://snomed.info/sct",
                                        "code": "706053007",
                                        "display": "General specimen container",
                                    }
                                ],
                                "text": "Red top tube",
                            },
                            "description": "Serum separator tube (SST)",
                            "capacity_value": 5.0,
                            "capacity_unit": "mL",
                            "capacity_system": "http://unitsofmeasure.org",
                            "capacity_code": "mL",
                            "minimum_volume_quantity_value": 1.0,
                            "minimum_volume_quantity_unit": "mL",
                            "minimum_volume_quantity_system": "http://unitsofmeasure.org",
                            "minimum_volume_quantity_code": "mL",
                        },
                        "handling": [
                            {
                                "temperature_qualifier": {
                                    "text": "Refrigerated"
                                },
                                "temperature_range_low_value": 2.0,
                                "temperature_range_low_unit": "degC",
                                "temperature_range_low_system": "http://unitsofmeasure.org",
                                "temperature_range_low_code": "Cel",
                                "temperature_range_high_value": 8.0,
                                "temperature_range_high_unit": "degC",
                                "temperature_range_high_system": "http://unitsofmeasure.org",
                                "temperature_range_high_code": "Cel",
                                "instruction": "Store at 2-8 degC until analysis.",
                            }
                        ],
                    }
                ],
            }
        },
    )

    identifier: SpecimenDefinitionIdentifierInput | None = Field(
        None, description="Business identifier of a kind of specimen."
    )
    type_collected: SpecimenDefinitionCodeableConceptInput | None = Field(
        None, description="Kind of specimen to collect."
    )
    patient_preparation: list[SpecimenDefinitionCodeableConceptInput] | None = Field(
        None, description="Patient preparation before collection."
    )
    time_aspect: str | None = Field(
        None, description="Time aspect for collection (e.g. 24 hour)."
    )
    collection: list[SpecimenDefinitionCodeableConceptInput] | None = Field(
        None, description="Specimen collection procedure."
    )
    type_tested: list[SpecimenDefinitionTypeTestedInput] | None = Field(
        None, description="Specimen in container tested."
    )


class SpecimenDefinitionPatchSchema(BaseModel):
    """Payload to patch an existing SpecimenDefinition resource."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "time_aspect": "fasting, morning",
            }
        },
    )

    identifier: SpecimenDefinitionIdentifierInput | None = Field(
        None, description="Business identifier of a kind of specimen."
    )
    type_collected: SpecimenDefinitionCodeableConceptInput | None = Field(
        None, description="Kind of specimen to collect."
    )
    patient_preparation: list[SpecimenDefinitionCodeableConceptInput] | None = Field(
        None, description="Patient preparation before collection."
    )
    time_aspect: str | None = Field(
        None, description="Time aspect for collection (e.g. 24 hour)."
    )
    collection: list[SpecimenDefinitionCodeableConceptInput] | None = Field(
        None, description="Specimen collection procedure."
    )
    type_tested: list[SpecimenDefinitionTypeTestedInput] | None = Field(
        None, description="Specimen in container tested."
    )
