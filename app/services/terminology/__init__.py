from .audit_log import _AuditLogMixin
from .code_systems import _CodeSystemsMixin
from .concept_maps import _ConceptMapsMixin
from .concepts import _ConceptsMixin
from .core import _CoreMixin
from .display_overrides import _DisplayOverridesMixin
from .org_concepts import _OrgConceptsMixin
from .validation import _ValidationMixin
from .value_sets import _ValueSetsMixin

__all__ = ["TerminologyService"]


class TerminologyService(
    _CoreMixin,
    _CodeSystemsMixin,
    _ValueSetsMixin,
    _ConceptsMixin,
    _ValidationMixin,
    _ConceptMapsMixin,
    _OrgConceptsMixin,
    _DisplayOverridesMixin,
    _AuditLogMixin,
):
    """Thin orchestration layer between the router and TerminologyRepository
    — every method maps repository rows onto a Pydantic response schema,
    no other business logic. __init__(self, repository) lives on
    _CoreMixin. Split into one mixin per domain, same grouping as
    app/repository/terminology/ and app/routers/terminology/ — a reader
    sees the same file names across all three layers for the same
    concept. Response-building helpers shared across mixins (_cs_response,
    _vs_response, _concept_response, _org_concept_response,
    _display_override_response) live in _shared.py."""
