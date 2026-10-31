from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
    FHIRReference,
)
from app.schemas.service_request.response.core import FHIRAnnotation

from .codeable_concept import PlainSpecimenCodeableConcept, PlainSpecimenCondition
from .collection import FHIRSpecimenCollection, PlainSpecimenCollection
from .container import FHIRSpecimenContainer, PlainSpecimenContainer
from .identifier import PlainSpecimenIdentifier
from .note import PlainSpecimenNote
from .processing import FHIRSpecimenProcessing, PlainSpecimenProcessing
from .reference import PlainSpecimenReference


class FHIRSpecimenSchema(BaseModel):
    """FHIR R4 Specimen resource representation."""

    resourceType: str = Field("Specimen", description="Always 'Specimen'.")
    id: str = Field(..., description="Public specimen_id as a string.")
    meta: FHIRMeta | None = Field(
        None, description="Infrastructure-maintained resource metadata. Response-only."
    )
    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions."
    )
    identifier: list[FHIRIdentifier] | None = Field(
        None, description="External identifiers for this specimen."
    )
    accessionIdentifier: FHIRIdentifier | None = Field(
        None, description="Identifier assigned by the lab when the specimen was received."
    )
    status: str | None = Field(
        None, description="available | unavailable | unsatisfactory | entered-in-error."
    )
    type: FHIRCodeableConcept | None = Field(
        None, description="Kind for specimen."
    )
    subject: FHIRReference | None = Field(
        None, description="Where the specimen came from (Patient | Group | Device | Substance | Location)."
    )
    receivedTime: str | None = Field(
        None, description="The time when specimen was received for processing."
    )
    parent: list[FHIRReference] | None = Field(
        None, description="Specimen from which this specimen originated."
    )
    request: list[FHIRReference] | None = Field(
        None, description="Why the specimen was collected (ServiceRequest)."
    )
    collection: FHIRSpecimenCollection | None = Field(
        None, description="Collection details."
    )
    processing: list[FHIRSpecimenProcessing] | None = Field(
        None, description="Processing and manipulation details."
    )
    container: list[FHIRSpecimenContainer] | None = Field(
        None, description="Direct container of specimen."
    )
    condition: list[FHIRCodeableConcept] | None = Field(
        None, description="State of the specimen (e.g. frozen, cooled)."
    )
    note: list[FHIRAnnotation] | None = Field(
        None, description="Comments."
    )


class FHIRSpecimenBundleEntry(BaseModel):
    fullUrl: str | None = None
    resource: FHIRSpecimenSchema | None = None


class FHIRSpecimenBundle(FHIRBundle):
    entry: list[FHIRSpecimenBundleEntry] | None = None


class PlainSpecimenResponse(BaseModel):
    """Plain snake_case response representation of Specimen."""

    model_config = ConfigDict(extra="allow")

    id: int = Field(..., description="Public sequence specimen_id as an integer.")
    identifier: list[PlainSpecimenIdentifier] | None = Field(
        None, description="External identifiers for this specimen."
    )
    accession_identifier: PlainSpecimenIdentifier | None = Field(
        None, description="Identifier assigned by the lab when the specimen was received."
    )
    status: str | None = Field(
        None, description="available | unavailable | unsatisfactory | entered-in-error."
    )
    type: PlainSpecimenCodeableConcept | None = Field(
        None, description="Kind for specimen."
    )
    subject: PlainSpecimenReference | None = Field(
        None, description="Where the specimen came from."
    )
    received_time: datetime | None = Field(
        None, description="The time when specimen was received for processing."
    )
    parent: list[PlainSpecimenReference] | None = Field(
        None, description="Specimen from which this specimen originated."
    )
    request: list[PlainSpecimenReference] | None = Field(
        None, description="Why the specimen was collected."
    )
    collection: PlainSpecimenCollection | None = Field(
        None, description="Collection details."
    )
    processing: list[PlainSpecimenProcessing] | None = Field(
        None, description="Processing and manipulation details."
    )
    container: list[PlainSpecimenContainer] | None = Field(
        None, description="Direct container of specimen."
    )
    condition: list[PlainSpecimenCondition] | None = Field(
        None, description="State of the specimen."
    )
    note: list[PlainSpecimenNote] | None = Field(
        None, description="Comments."
    )
    extension: list[dict] | None = Field(
        None, description="Resource-level FHIR extensions."
    )
    created_at: datetime | None = Field(None, description="Timestamp created.")
    updated_at: datetime | None = Field(None, description="Timestamp updated.")


class PaginatedSpecimenResponse(BaseModel):
    """Paginated plain snake_case response for Specimens."""

    total: int = Field(..., description="Total count matching filter.")
    limit: int = Field(..., description="Page size.")
    offset: int = Field(..., description="Page offset.")
    data: list[PlainSpecimenResponse] = Field(..., description="List of Specimens.")
