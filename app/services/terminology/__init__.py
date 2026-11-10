from .capabilities import _CapabilitiesMixin
from .code_systems import _CodeSystemsMixin
from .codesystem_operations import _CodeSystemOperationsMixin
from .concept_maps import _ConceptMapsMixin
from .conceptmap_operations import _ConceptMapOperationsMixin
from .concepts import _ConceptsMixin
from .core import _CoreMixin
from .org_concepts import _OrgConceptsMixin
from .validation import _ValidationMixin
from .value_sets import _ValueSetsMixin
from .valueset_operations import _ValueSetOperationsMixin

__all__ = ["TerminologyService"]


class TerminologyService(
    _CoreMixin,
    _CodeSystemsMixin,
    _ValueSetsMixin,
    _ConceptsMixin,
    _ValidationMixin,
    _ConceptMapsMixin,
    _OrgConceptsMixin,
    _CodeSystemOperationsMixin,
    _ValueSetOperationsMixin,
    _ConceptMapOperationsMixin,
    _CapabilitiesMixin,
):
    """Thin orchestration layer between the router and TerminologyRepository
    — every method maps repository rows onto a Pydantic response schema,
    no other business logic. __init__(self, repository) lives on
    _CoreMixin. Split into one mixin per domain, same grouping as
    app/repository/terminology/ and app/routers/terminology/ — a reader
    sees the same file names across all three layers for the same
    concept. Response-building helpers shared across mixins (_cs_response,
    _vs_response, _concept_response, _org_concept_response) live in
    _shared.py.

    `_CodeSystemOperationsMixin`/`_ValueSetOperationsMixin`/
    `_ConceptMapOperationsMixin` back the real FHIR R4 `$`-operations
    (`$lookup`, `$validate-code` ×2, `$subsumes`, `$find-matches`,
    `$expand`, `$translate`, `$closure` — see
    docs/terminology-service/09-fhir-r4-terminology-standard-reference.md)
    — distinct from, and additional to, every other mixin here, which
    backs this app's own pre-existing non-standard endpoints. Each returns
    a plain dict already shaped as the operation's FHIR `Parameters`/
    `ValueSet`/`ConceptMap` response body (see app/fhir/parameters.py),
    not a Pydantic response schema — that module's own docstring explains
    why.

    Display overrides and a terminology-specific audit log previously
    lived here too — removed deliberately, same reasoning as
    TerminologyRepository's own docstring."""
