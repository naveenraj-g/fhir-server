from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    PlainIdentifier,
)
from app.schemas.specimen_definition.response.codeable_concept import (
    PlainSpecimenDefinitionChildConcept,
    PlainSpecimenDefinitionCodeableConcept,
)
from app.schemas.specimen_definition.response.type_tested import (
    FHIRSpecimenDefinitionTypeTested,
    PlainSpecimenDefinitionTypeTested,
)


class FHIRSpecimenDefinitionSchema(BaseModel):
    """FHIR R4 SpecimenDefinition resource schema."""

    model_config = ConfigDict(extra="allow")

    resourceType: Literal["SpecimenDefinition"] = "SpecimenDefinition"
    id: str = Field(..., description="Logical id of this artifact.")
    meta: FHIRMeta | None = Field(None, description="Metadata about the resource.")
    extension: list[dict[str, Any]] | None = Field(
        None, description="Additional content defined by implementations."
    )
    identifier: FHIRIdentifier | None = Field(
        None, description="Business identifier of a kind of specimen."
    )
    typeCollected: FHIRCodeableConcept | None = Field(
        None, description="Kind of specimen to collect."
    )
    patientPreparation: list[FHIRCodeableConcept] | None = Field(
        None, description="Patient preparation before collection."
    )
    timeAspect: str | None = Field(
        None, description="Time aspect for collection (e.g. 24 hour)."
    )
    collection: list[FHIRCodeableConcept] | None = Field(
        None, description="Specimen collection procedure."
    )
    typeTested: list[FHIRSpecimenDefinitionTypeTested] | None = Field(
        None, description="Specimen in container tested."
    )


class PlainSpecimenDefinitionResponse(BaseModel):
    """Plain snake_case SpecimenDefinition response schema."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Sequence-based public identifier.")
    identifier: PlainIdentifier | None = Field(
        None, description="Business identifier."
    )
    type_collected: PlainSpecimenDefinitionCodeableConcept | None = Field(
        None, description="Kind of specimen to collect."
    )
    patient_preparation: list[PlainSpecimenDefinitionChildConcept] | None = Field(
        None, description="Patient preparation before collection."
    )
    time_aspect: str | None = Field(
        None, description="Time aspect for collection."
    )
    collection: list[PlainSpecimenDefinitionChildConcept] | None = Field(
        None, description="Specimen collection procedure."
    )
    type_tested: list[PlainSpecimenDefinitionTypeTested] | None = Field(
        None, description="Specimen in container tested."
    )
    created_at: datetime | None = Field(
        None, description="Timestamp of creation."
    )
    updated_at: datetime | None = Field(
        None, description="Timestamp of last update."
    )
    created_by: str = Field(
        ..., description="Subject that created the record."
    )
    updated_by: str | None = Field(
        None, description="Subject that last updated the record."
    )


class PaginatedSpecimenDefinitionResponse(BaseModel):
    """Paginated plain snake_case SpecimenDefinition response."""

    model_config = ConfigDict(extra="forbid")

    total: int = Field(..., description="Total number of matching records.")
    limit: int = Field(..., description="Page size limit.")
    offset: int = Field(..., description="Page offset.")
    data: list[PlainSpecimenDefinitionResponse] = Field(
        ..., description="List of matching SpecimenDefinition records."
    )


class FHIRSpecimenDefinitionBundleEntry(BaseModel):
    """Entry in a FHIR SpecimenDefinition searchset Bundle."""

    model_config = ConfigDict(extra="forbid")

    fullUrl: str = Field(..., description="Full URL for the resource.")
    resource: FHIRSpecimenDefinitionSchema = Field(
        ..., description="SpecimenDefinition resource."
    )


class FHIRSpecimenDefinitionBundle(BaseModel):
    """FHIR R4 searchset Bundle for SpecimenDefinition."""

    model_config = ConfigDict(extra="forbid")

    resourceType: Literal["Bundle"] = "Bundle"
    type: Literal["searchset"] = "searchset"
    total: int = Field(..., description="Total number of matches.")
    entry: list[FHIRSpecimenDefinitionBundleEntry] = Field(
        default_factory=list, description="Matched resources."
    )
