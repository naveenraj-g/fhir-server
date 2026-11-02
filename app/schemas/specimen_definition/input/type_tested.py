from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.enums import (
    IdentifierUse,
    SpecimenDefinitionPreference,
    SpecimenDefinitionQuantityComparator,
)
from app.schemas.specimen_definition.input.codeable_concept import (
    SpecimenDefinitionCodeableConceptInput,
)


class SpecimenDefinitionAdditiveReferenceInput(BaseModel):
    """Additive reference to Substance."""

    model_config = ConfigDict(extra="forbid")

    reference: str | None = Field(
        None, description="Literal reference, Relative, internal or absolute URL."
    )
    display: str | None = Field(
        None, description="Text alternative for the resource."
    )
    identifier_use: IdentifierUse | None = Field(None)
    identifier_type_system: str | None = Field(None)
    identifier_type_version: str | None = Field(None)
    identifier_type_code: str | None = Field(None)
    identifier_type_display: str | None = Field(None)
    identifier_type_text: str | None = Field(None)
    identifier_type_user_selected: bool | None = Field(None)
    identifier_system: str | None = Field(None)
    identifier_value: str | None = Field(None)
    identifier_period_start: datetime | None = Field(None)
    identifier_period_end: datetime | None = Field(None)


class SpecimenDefinitionAdditiveInput(BaseModel):
    """SpecimenDefinition.typeTested.container.additive (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    additive_codeable_concept: SpecimenDefinitionCodeableConceptInput | None = Field(
        None, description="Additive associated with container as CodeableConcept."
    )
    additive_reference: SpecimenDefinitionAdditiveReferenceInput | None = Field(
        None, description="Additive associated with container as Reference(Substance)."
    )


class SpecimenDefinitionContainerInput(BaseModel):
    """SpecimenDefinition.typeTested.container (0..1 BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    material: SpecimenDefinitionCodeableConceptInput | None = Field(
        None, description="The material of the container."
    )
    type: SpecimenDefinitionCodeableConceptInput | None = Field(
        None, description="Kind of container directly associated with specimen."
    )
    cap: SpecimenDefinitionCodeableConceptInput | None = Field(
        None, description="Color of the cap of the container."
    )
    description: str | None = Field(
        None, description="Description of the container."
    )
    capacity_value: float | None = Field(
        None, description="Container volume or size (SimpleQuantity.value)."
    )
    capacity_unit: str | None = Field(None, description="Container capacity unit.")
    capacity_system: str | None = Field(None, description="Container capacity unit system.")
    capacity_code: str | None = Field(None, description="Container capacity unit code.")

    minimum_volume_string: str | None = Field(
        None, description="Minimum volume required as string description."
    )
    minimum_volume_quantity_value: float | None = Field(
        None, description="Minimum volume required as numeric Quantity."
    )
    minimum_volume_quantity_comparator: SpecimenDefinitionQuantityComparator | None = Field(
        None, description="Minimum volume comparator (< | <= | >= | >)."
    )
    minimum_volume_quantity_unit: str | None = Field(None, description="Minimum volume unit.")
    minimum_volume_quantity_system: str | None = Field(None, description="Minimum volume system.")
    minimum_volume_quantity_code: str | None = Field(None, description="Minimum volume code.")

    additive: list[SpecimenDefinitionAdditiveInput] | None = Field(
        None, description="Additive associated with container."
    )
    preparation: str | None = Field(
        None, description="Special preparation of container."
    )


class SpecimenDefinitionHandlingInput(BaseModel):
    """SpecimenDefinition.typeTested.handling (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    temperature_qualifier: SpecimenDefinitionCodeableConceptInput | None = Field(
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
        None, description="Maximum preservation time (Duration.value)."
    )
    max_duration_comparator: SpecimenDefinitionQuantityComparator | None = Field(
        None, description="Maximum duration comparator (< | <= | >= | >)."
    )
    max_duration_unit: str | None = Field(None, description="Maximum duration unit.")
    max_duration_system: str | None = Field(None, description="Maximum duration system.")
    max_duration_code: str | None = Field(None, description="Maximum duration code.")

    instruction: str | None = Field(
        None, description="Preservation instruction."
    )


class SpecimenDefinitionTypeTestedInput(BaseModel):
    """SpecimenDefinition.typeTested (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    is_derived: bool | None = Field(
        None, description="Primary or secondary specimen."
    )
    type: SpecimenDefinitionCodeableConceptInput | None = Field(
        None, description="Type of intended specimen."
    )
    preference: SpecimenDefinitionPreference = Field(
        ..., description="preferred | alternate."
    )
    container: SpecimenDefinitionContainerInput | None = Field(
        None, description="The specimen's container."
    )
    requirement: str | None = Field(
        None, description="Specimen requirements."
    )
    retention_time_value: float | None = Field(
        None, description="Retention time duration value."
    )
    retention_time_comparator: SpecimenDefinitionQuantityComparator | None = Field(
        None, description="Retention time duration comparator."
    )
    retention_time_unit: str | None = Field(None, description="Retention time unit.")
    retention_time_system: str | None = Field(None, description="Retention time system.")
    retention_time_code: str | None = Field(None, description="Retention time code.")

    rejection_criterion: list[SpecimenDefinitionCodeableConceptInput] | None = Field(
        None, description="Rejection criteria."
    )
    handling: list[SpecimenDefinitionHandlingInput] | None = Field(
        None, description="Specimen handling before testing."
    )
