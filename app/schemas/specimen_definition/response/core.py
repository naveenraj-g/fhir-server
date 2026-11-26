"""Response schemas for SpecimenDefinition (generated; see scripts/generate_fhir_resources.py)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import FHIRBundle
from app.schemas.common.examples import bundle_example, served_example
from app.schemas.common.searchset import FHIRBundleEntrySearch, FHIRBundleLink
from app.schemas.fhir_datatypes import Meta
from app.schemas.fhir_resources.specimen_definition import SpecimenDefinition
from app.schemas.specimen_definition.input.core import _CREATE_EXAMPLE

_EXAMPLE = served_example("SpecimenDefinition", "550000", _CREATE_EXAMPLE)


class FHIRSpecimenDefinitionSchema(SpecimenDefinition):
    "A FHIR R4 SpecimenDefinition as served: the stored document with `id` and `meta` stamped on."

    model_config = ConfigDict(json_schema_extra={"example": _EXAMPLE})

    resourceType: str = Field(
        "SpecimenDefinition", description="Always 'SpecimenDefinition'."
    )
    id: str = Field(..., description="Public specimen_definition_id as a string.")
    meta: Meta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only.",
    )


class FHIRSpecimenDefinitionBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRSpecimenDefinitionSchema | dict = Field(
        ...,
        description="A SpecimenDefinition (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included resource (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRSpecimenDefinitionBundle(FHIRBundle):
    model_config = ConfigDict(
        json_schema_extra={"example": bundle_example("/specimen-definitions", _EXAMPLE)}
    )

    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRSpecimenDefinitionBundleEntry] | None = None
