"""Response schemas for MedicationKnowledge (generated; see scripts/generate_fhir_resources.py)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import FHIRBundle
from app.schemas.common.examples import bundle_example, served_example
from app.schemas.common.searchset import FHIRBundleEntrySearch, FHIRBundleLink
from app.schemas.fhir_datatypes import Meta
from app.schemas.fhir_resources.medication_knowledge import MedicationKnowledge
from app.schemas.medication_knowledge.input.core import _CREATE_EXAMPLE

_EXAMPLE = served_example("MedicationKnowledge", "600000", _CREATE_EXAMPLE)


class FHIRMedicationKnowledgeSchema(MedicationKnowledge):
    "A FHIR R4 MedicationKnowledge as served: the stored document with `id` and `meta` stamped on."

    model_config = ConfigDict(json_schema_extra={"example": _EXAMPLE})

    resourceType: str = Field(
        "MedicationKnowledge", description="Always 'MedicationKnowledge'."
    )
    id: str = Field(..., description="Public medication_knowledge_id as a string.")
    meta: Meta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only.",
    )


class FHIRMedicationKnowledgeBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRMedicationKnowledgeSchema | dict = Field(
        ...,
        description="A MedicationKnowledge (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included resource (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRMedicationKnowledgeBundle(FHIRBundle):
    model_config = ConfigDict(
        json_schema_extra={"example": bundle_example("/medication-knowledge", _EXAMPLE)}
    )

    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRMedicationKnowledgeBundleEntry] | None = None
