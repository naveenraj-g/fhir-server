from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRReference,
)
from app.schemas.questionnaire.response import FHIRQuantity

from .codeable_concept import PlainSpecimenCodeableConcept
from .identifier import PlainSpecimenIdentifier
from .reference import PlainSpecimenReference


class FHIRSpecimenContainer(BaseModel):
    """FHIR representation of Specimen.container."""

    identifier: list[FHIRIdentifier] | None = Field(None, description="Id for container.")
    description: str | None = Field(None, description="Textual description of the container.")
    type: FHIRCodeableConcept | None = Field(None, description="Kind of container.")
    capacity: FHIRQuantity | None = Field(None, description="Container volume or size.")
    specimenQuantity: FHIRQuantity | None = Field(None, description="Quantity of specimen within container.")
    additiveCodeableConcept: FHIRCodeableConcept | None = Field(
        None, description="Additive associated with container as concept."
    )
    additiveReference: FHIRReference | None = Field(
        None, description="Additive associated with container as reference."
    )


class PlainSpecimenContainer(BaseModel):
    """Plain response representation of Specimen.container."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Internal DB ID.")
    identifier: list[PlainSpecimenIdentifier] | None = Field(None, description="Container identifiers.")
    description: str | None = Field(None, description="Textual description of the container.")
    type: PlainSpecimenCodeableConcept | None = Field(None, description="Kind of container.")
    capacity_value: float | None = Field(None, description="Container volume value.")
    capacity_unit: str | None = Field(None, description="Container volume unit.")
    capacity_system: str | None = Field(None, description="System for container volume unit.")
    capacity_code: str | None = Field(None, description="Coded form of container volume unit.")
    specimen_quantity_value: float | None = Field(None, description="Specimen quantity value.")
    specimen_quantity_unit: str | None = Field(None, description="Specimen quantity unit.")
    specimen_quantity_system: str | None = Field(None, description="System for specimen quantity unit.")
    specimen_quantity_code: str | None = Field(None, description="Coded form of specimen quantity unit.")
    additive_codeable_concept: PlainSpecimenCodeableConcept | None = Field(
        None, description="Additive concept."
    )
    additive_reference: PlainSpecimenReference | None = Field(
        None, description="Additive reference."
    )
