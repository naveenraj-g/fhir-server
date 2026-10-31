from pydantic import BaseModel, ConfigDict, Field

from .codeable_concept import SpecimenCodeableConceptInput
from .identifier import SpecimenIdentifierInput
from .reference import SpecimenAdditiveReferenceInput


class SpecimenContainerInput(BaseModel):
    """Specimen.container (0..* BackboneElement)."""

    model_config = ConfigDict(extra="forbid")

    identifier: list[SpecimenIdentifierInput] | None = Field(
        None, description="Id for container."
    )
    description: str | None = Field(
        None, description="Textual description of the container."
    )
    type: SpecimenCodeableConceptInput | None = Field(
        None, description="Kind of container directly associated with specimen."
    )
    capacity_value: float | None = Field(
        None, description="Container volume or size value (SimpleQuantity.value)."
    )
    capacity_unit: str | None = Field(
        None, description="Container volume unit."
    )
    capacity_system: str | None = Field(
        None, description="System that defines container volume unit."
    )
    capacity_code: str | None = Field(
        None, description="Coded form of container volume unit."
    )
    specimen_quantity_value: float | None = Field(
        None, description="Quantity of specimen within container value."
    )
    specimen_quantity_unit: str | None = Field(
        None, description="Quantity of specimen unit."
    )
    specimen_quantity_system: str | None = Field(
        None, description="System for specimen quantity unit."
    )
    specimen_quantity_code: str | None = Field(
        None, description="Coded form of specimen quantity unit."
    )
    additive_codeable_concept: SpecimenCodeableConceptInput | None = Field(
        None, description="Additive associated with container as CodeableConcept."
    )
    additive_reference: SpecimenAdditiveReferenceInput | None = Field(
        None, description="Additive associated with container as Reference(Substance)."
    )
