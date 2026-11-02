from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRQuantity,
    FHIRRange,
    FHIRReference,
)
from app.schemas.specimen_definition.response.codeable_concept import (
    PlainSpecimenDefinitionChildConcept,
    PlainSpecimenDefinitionCodeableConcept,
)


class FHIRSpecimenDefinitionAdditive(BaseModel):
    """SpecimenDefinition.typeTested.container.additive FHIR element."""

    model_config = ConfigDict(extra="forbid")

    additiveCodeableConcept: FHIRCodeableConcept | None = Field(
        None, description="Additive associated with container as concept."
    )
    additiveReference: FHIRReference | None = Field(
        None, description="Additive associated with container as reference."
    )


class FHIRSpecimenDefinitionContainer(BaseModel):
    """SpecimenDefinition.typeTested.container FHIR element."""

    model_config = ConfigDict(extra="forbid")

    material: FHIRCodeableConcept | None = Field(
        None, description="The material of the container."
    )
    type: FHIRCodeableConcept | None = Field(
        None, description="Kind of container directly associated with specimen."
    )
    cap: FHIRCodeableConcept | None = Field(
        None, description="Color of the cap of the container."
    )
    description: str | None = Field(
        None, description="Description of the container."
    )
    capacity: FHIRQuantity | None = Field(
        None, description="Container volume or size."
    )
    minimumVolumeQuantity: FHIRQuantity | None = Field(
        None, description="Minimum volume required as Quantity."
    )
    minimumVolumeString: str | None = Field(
        None, description="Minimum volume required as string description."
    )
    additive: list[FHIRSpecimenDefinitionAdditive] | None = Field(
        None, description="Additive associated with container."
    )
    preparation: str | None = Field(
        None, description="Special preparation of container."
    )


class FHIRSpecimenDefinitionHandling(BaseModel):
    """SpecimenDefinition.typeTested.handling FHIR element."""

    model_config = ConfigDict(extra="forbid")

    temperatureQualifier: FHIRCodeableConcept | None = Field(
        None, description="Temperature qualifier."
    )
    temperatureRange: FHIRRange | None = Field(
        None, description="Temperature range."
    )
    maxDuration: FHIRQuantity | None = Field(
        None, description="Maximum preservation time."
    )
    instruction: str | None = Field(
        None, description="Preservation instruction."
    )


class FHIRSpecimenDefinitionTypeTested(BaseModel):
    """SpecimenDefinition.typeTested FHIR element."""

    model_config = ConfigDict(extra="forbid")

    isDerived: bool | None = Field(
        None, description="Primary or secondary specimen."
    )
    type: FHIRCodeableConcept | None = Field(
        None, description="Type of intended specimen."
    )
    preference: str = Field(
        ..., description="preferred | alternate."
    )
    container: FHIRSpecimenDefinitionContainer | None = Field(
        None, description="The specimen's container."
    )
    requirement: str | None = Field(
        None, description="Specimen requirements."
    )
    retentionTime: FHIRQuantity | None = Field(
        None, description="Retention time."
    )
    rejectionCriterion: list[FHIRCodeableConcept] | None = Field(
        None, description="Rejection criteria."
    )
    handling: list[FHIRSpecimenDefinitionHandling] | None = Field(
        None, description="Specimen handling before testing."
    )


class PlainSpecimenDefinitionAdditive(BaseModel):
    """Plain response shape for SpecimenDefinition container additive."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal DB ID.")
    additive_codeable_concept: PlainSpecimenDefinitionCodeableConcept | None = Field(
        None, description="Additive associated with container as concept."
    )
    additive_reference: str | None = Field(
        None, description="Additive reference URL/string."
    )
    additive_reference_display: str | None = Field(
        None, description="Display name for additive reference."
    )
    additive_reference_type: str | None = Field(
        None, description="Target resource type for additive reference."
    )
    additive_reference_id: int | None = Field(
        None, description="Target public ID for additive reference."
    )


class PlainSpecimenDefinitionContainer(BaseModel):
    """Plain response shape for SpecimenDefinition container."""

    model_config = ConfigDict(extra="allow")

    material: PlainSpecimenDefinitionCodeableConcept | None = Field(
        None, description="The material of the container."
    )
    type: PlainSpecimenDefinitionCodeableConcept | None = Field(
        None, description="Kind of container directly associated with specimen."
    )
    cap: PlainSpecimenDefinitionCodeableConcept | None = Field(
        None, description="Color of the cap of the container."
    )
    description: str | None = Field(
        None, description="Description of the container."
    )
    capacity_value: float | None = Field(
        None, description="Container volume value."
    )
    capacity_unit: str | None = Field(None, description="Container capacity unit.")
    capacity_system: str | None = Field(None, description="Container capacity system.")
    capacity_code: str | None = Field(None, description="Container capacity code.")

    minimum_volume_string: str | None = Field(
        None, description="Minimum volume required as string description."
    )
    minimum_volume_quantity_value: float | None = Field(
        None, description="Minimum volume required as numeric Quantity."
    )
    minimum_volume_quantity_comparator: str | None = Field(
        None, description="Minimum volume comparator."
    )
    minimum_volume_quantity_unit: str | None = Field(None, description="Minimum volume unit.")
    minimum_volume_quantity_system: str | None = Field(None, description="Minimum volume system.")
    minimum_volume_quantity_code: str | None = Field(None, description="Minimum volume code.")

    additive: list[PlainSpecimenDefinitionAdditive] | None = Field(
        None, description="Additive associated with container."
    )
    preparation: str | None = Field(
        None, description="Special preparation of container."
    )


class PlainSpecimenDefinitionHandling(BaseModel):
    """Plain response shape for SpecimenDefinition handling."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal DB ID.")
    temperature_qualifier: PlainSpecimenDefinitionCodeableConcept | None = Field(
        None, description="Temperature qualifier."
    )
    temperature_range_low_value: float | None = Field(
        None, description="Low limit of temperature range."
    )
    temperature_range_low_unit: str | None = Field(None, description="Low limit unit.")
    temperature_range_low_system: str | None = Field(None, description="Low limit system.")
    temperature_range_low_code: str | None = Field(None, description="Low limit code.")
    temperature_range_high_value: float | None = Field(
        None, description="High limit of temperature range."
    )
    temperature_range_high_unit: str | None = Field(None, description="High limit unit.")
    temperature_range_high_system: str | None = Field(None, description="High limit system.")
    temperature_range_high_code: str | None = Field(None, description="High limit code.")

    max_duration_value: float | None = Field(
        None, description="Maximum preservation time value."
    )
    max_duration_comparator: str | None = Field(
        None, description="Maximum duration comparator."
    )
    max_duration_unit: str | None = Field(None, description="Maximum duration unit.")
    max_duration_system: str | None = Field(None, description="Maximum duration system.")
    max_duration_code: str | None = Field(None, description="Maximum duration code.")

    instruction: str | None = Field(
        None, description="Preservation instruction."
    )


class PlainSpecimenDefinitionTypeTested(BaseModel):
    """Plain response shape for SpecimenDefinition typeTested."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal DB ID.")
    is_derived: bool | None = Field(
        None, description="Primary or secondary specimen."
    )
    type: PlainSpecimenDefinitionCodeableConcept | None = Field(
        None, description="Type of intended specimen."
    )
    preference: str = Field(
        ..., description="preferred | alternate."
    )
    container: PlainSpecimenDefinitionContainer | None = Field(
        None, description="The specimen's container."
    )
    requirement: str | None = Field(
        None, description="Specimen requirements."
    )
    retention_time_value: float | None = Field(
        None, description="Retention time duration value."
    )
    retention_time_comparator: str | None = Field(
        None, description="Retention time duration comparator."
    )
    retention_time_unit: str | None = Field(None, description="Retention time unit.")
    retention_time_system: str | None = Field(None, description="Retention time system.")
    retention_time_code: str | None = Field(None, description="Retention time code.")

    rejection_criterion: list[PlainSpecimenDefinitionChildConcept] | None = Field(
        None, description="Rejection criteria."
    )
    handling: list[PlainSpecimenDefinitionHandling] | None = Field(
        None, description="Specimen handling before testing."
    )
