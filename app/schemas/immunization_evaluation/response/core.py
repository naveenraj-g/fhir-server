"""Response schemas for ImmunizationEvaluation (generated; see scripts/generate_fhir_resources.py)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import FHIRBundle
from app.schemas.common.examples import bundle_example, served_example
from app.schemas.common.searchset import FHIRBundleEntrySearch, FHIRBundleLink
from app.schemas.fhir_datatypes import Meta
from app.schemas.fhir_resources.immunization_evaluation import ImmunizationEvaluation
from app.schemas.immunization_evaluation.input.core import _CREATE_EXAMPLE

_EXAMPLE = served_example("ImmunizationEvaluation", "610000", _CREATE_EXAMPLE)


class FHIRImmunizationEvaluationSchema(ImmunizationEvaluation):
    "A FHIR R4 ImmunizationEvaluation as served: the stored document with `id` and `meta` stamped on."

    model_config = ConfigDict(json_schema_extra={"example": _EXAMPLE})

    resourceType: str = Field(
        "ImmunizationEvaluation", description="Always 'ImmunizationEvaluation'."
    )
    id: str = Field(..., description="Public immunization_evaluation_id as a string.")
    meta: Meta | None = Field(
        None,
        description="Infrastructure-maintained resource metadata - lastUpdated, plus this server's org_id/created_by/updated_by/created_at as extensions (FHIR R4's Meta has no native field for those). Response-only.",
    )


class FHIRImmunizationEvaluationBundleEntry(BaseModel):
    fullUrl: str | None = Field(
        None, description="Absolute URL of the resource (absent on an outcome entry)."
    )
    resource: FHIRImmunizationEvaluationSchema | dict = Field(
        ...,
        description="A ImmunizationEvaluation (match; possibly subsetted by _summary/_elements and then tagged SUBSETTED), an included resource (from _include or _revinclude), or an OperationOutcome (outcome).",
    )
    search: FHIRBundleEntrySearch


class FHIRImmunizationEvaluationBundle(FHIRBundle):
    model_config = ConfigDict(
        json_schema_extra={
            "example": bundle_example("/immunization-evaluations", _EXAMPLE)
        }
    )

    total: int | None = Field(
        None,
        description="Number of matches across all pages (not counting included resources). Omitted with _total=none.",
    )
    link: list[FHIRBundleLink] = Field(
        ..., description="Paging links: self, first, previous, next, last."
    )
    entry: list[FHIRImmunizationEvaluationBundleEntry] | None = None
