from fastapi import APIRouter

from . import (
    capabilities,
    code_systems,
    codesystem_operations,
    concept_maps,
    conceptmap_operations,
    concepts,
    org_concepts,
    validation,
    value_sets,
    valueset_operations,
)

# No prefix/tags here — app/main.py sets prefix="/api/v1/terminology",
# tags=["Terminology"], and dependencies=[Depends(get_current_user)] at
# include_router() time, since terminology is mounted unconditionally
# (not covered by routes.enabled, see CLAUDE.md's "Enabling/Disabling
# Resources"), unlike the routes.enabled-gated FHIR resources whose own
# packages set prefix/tags themselves.
router = APIRouter()

for _module in (
    code_systems,
    value_sets,
    concepts,
    validation,
    concept_maps,
    org_concepts,
    codesystem_operations,
    valueset_operations,
    conceptmap_operations,
    capabilities,
):
    router.include_router(_module.router)
