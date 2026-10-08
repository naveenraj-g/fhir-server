from app.models.terminology.terminology import (
    TerminologyCodeSystem,
    TerminologyConcept,
    TerminologyDisplayOverride,
    TerminologyValueSet,
)
from app.schemas.terminology import (
    CodeSystemResponse,
    ConceptResponse,
    DisplayOverrideResponse,
    OrgConceptResponse,
    ValueSetResponse,
)


def _cs_response(cs: TerminologyCodeSystem) -> CodeSystemResponse:
    return CodeSystemResponse(
        id=cs.id,
        canonical_url=cs.canonical_url,
        name=cs.name,
        title=cs.title,
        version=cs.version,
        publisher=cs.publisher,
        content_mode=cs.content_mode,
        active=cs.active,
    )


def _vs_response(vs: TerminologyValueSet) -> ValueSetResponse:
    return ValueSetResponse(
        id=vs.id,
        canonical_url=vs.canonical_url,
        name=vs.name,
        title=vs.title,
        description=vs.description,
        version=vs.version,
        binding_strength=vs.binding_strength,
        active=vs.active,
    )


def _concept_response(
    concept: TerminologyConcept, cs: TerminologyCodeSystem
) -> ConceptResponse:
    return ConceptResponse(
        id=concept.id,
        code=concept.code,
        display=concept.display,
        definition=concept.definition,
        active=concept.active,
        system=cs.canonical_url,
        system_name=cs.name,
    )


def _org_concept_response(
    concept: TerminologyConcept, cs: TerminologyCodeSystem
) -> OrgConceptResponse:
    return OrgConceptResponse(
        id=concept.id,
        code=concept.code,
        display=concept.display,
        definition=concept.definition,
        active=concept.active,
        system=cs.canonical_url,
        system_name=cs.name,
        user_id=concept.user_id,
        org_id=concept.org_id,
        created_at=concept.created_at,
    )


def _display_override_response(
    override: TerminologyDisplayOverride,
    concept: TerminologyConcept,
    cs: TerminologyCodeSystem,
) -> DisplayOverrideResponse:
    return DisplayOverrideResponse(
        id=override.id,
        code=concept.code,
        system=cs.canonical_url,
        system_name=cs.name,
        display=override.display,
        definition=override.definition,
        org_id=override.org_id,
        user_id=override.user_id,
        created_at=override.created_at,
    )
