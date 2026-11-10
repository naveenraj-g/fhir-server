from app.repository.base import BaseRepository

from .capabilities import _CapabilitiesMixin
from .closure import _ClosureMixin
from .code_systems import _CodeSystemsMixin
from .codesystem_operations import _CodeSystemOperationsMixin
from .concept_maps import _ConceptMapsMixin
from .conceptmap_operations import _ConceptMapOperationsMixin
from .concepts import _ConceptsMixin
from .hierarchy import _HierarchyMixin
from .org_concepts import _OrgConceptsMixin
from .validation import _ValidationMixin
from .value_sets import _ValueSetsMixin

__all__ = ["TerminologyRepository"]


class TerminologyRepository(
    _CodeSystemsMixin,
    _ValueSetsMixin,
    _ConceptsMixin,
    _ValidationMixin,
    _ConceptMapsMixin,
    _OrgConceptsMixin,
    _HierarchyMixin,
    _ClosureMixin,
    _CodeSystemOperationsMixin,
    _ConceptMapOperationsMixin,
    _CapabilitiesMixin,
    BaseRepository,
):
    """All terminology DB I/O. session_factory/__init__ inherited from
    BaseRepository — same convention the reworked FHIR resources use, see
    that class. Split into one mixin per domain (code systems, value sets,
    concepts, validation, concept maps, org concepts, hierarchy/subsumption,
    closure-table state, plus the CodeSystem/ConceptMap `$`-operation-only
    additions) — same grouping as app/routers/terminology/'s own
    sub-modules, so a reader sees the same file names across
    router/service/repository for the same concept. No single "core" mixin
    the way Patient/Organization have one — terminology has no single
    primary resource row, just this flat set of domains.

    `_CodeSystemOperationsMixin`/`_ConceptMapOperationsMixin` here are
    repository-layer-only additions backing `$lookup`'s designation output
    and `$translate`'s `reverse=true` direction respectively — distinct
    from the identically-named service-layer mixins in
    app/services/terminology/ (same file-naming convention, different
    layer, no relation beyond sharing a name the way `_ValueSetsMixin`
    already does across repository and service).

    Display overrides and a terminology-specific audit log previously
    lived here too — removed deliberately (not just deferred cleanup):
    audit logging is being designed once, app-wide, rather than one
    terminology-only version now and a second real one later; display
    overrides go back on the list once that's settled. See
    docs/terminology-service/08-fhir-r4-standard-compliance-gap-analysis.md
    for why the FHIR-standard rebuild (CodeSystem/ValueSet/ConceptMap as
    real resources, canonical-URL addressing, standard operations) takes
    priority over either."""
