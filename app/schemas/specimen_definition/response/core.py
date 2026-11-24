from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.datatypes import (
    FHIRBundle,
    FHIRCodeableConcept,
    FHIRIdentifier,
    FHIRMeta,
)
from app.schemas.datatypes.searchset import FHIRBundleEntrySearch, FHIRBundleLink


class FHIRSpecimenDefinitionSchema(BaseModel):
    resourceType: str = Field(
        "SpecimenDefinition", description="Always 'SpecimenDefinition'."
    )
    id: str = Field(..., description="Public specimen_definition_id as a string.")
    meta: FHIRMeta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only: not accepted on create/patch, since this is server-derived audit/tenant data.",
    )
    extension: list[dict] | None = Field(
        None,
        description="Resource-level FHIR extensions, as raw [{url, value[x]}, ...] entries.",
    )
    identifier: FHIRIdentifier | None = Field(
        None, description="Business identifier of a kind of specimen."
    )
    typeCollected: FHIRCodeableConcept | None = Field(
        None, description="Kind of material to collect."
    )
    patientPreparation: list[FHIRCodeableConcept] | None = Field(
        None, description="Patient preparation for collection."
    )
    timeAspect: str | None = Field(None, description="Time aspect for collection.")
    collection: list[FHIRCodeableConcept] | None = Field(
        None, description="Specimen collection procedure."
    )
    typeTested: list[dict] | None = Field(
        None, description="Specimen in container intended for testing by lab."
    )


class FHIRSpecimenDefinitionBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRSpecimenDefinitionSchema | dict = Field(
        ...,
        description="A SpecimenDefinition (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED) or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRSpecimenDefinitionBundle(FHIRBundle):
    total: int | None = Field(
        None,
        description="Number of matches across all pages. Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRSpecimenDefinitionBundleEntry] | None = None
