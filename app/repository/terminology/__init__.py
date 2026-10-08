from app.repository.base import BaseRepository

from .audit_log import _AuditLogMixin
from .code_systems import _CodeSystemsMixin
from .concept_maps import _ConceptMapsMixin
from .concepts import _ConceptsMixin
from .display_overrides import _DisplayOverridesMixin
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
    _DisplayOverridesMixin,
    _AuditLogMixin,
    BaseRepository,
):
    """All terminology DB I/O. session_factory/__init__ inherited from
    BaseRepository — same convention the reworked FHIR resources use, see
    that class. Split into one mixin per domain (code systems, value sets,
    concepts, validation, concept maps, org concepts, display overrides,
    audit log) — same grouping as app/routers/terminology/'s own
    sub-modules, so a reader sees the same file names across
    router/service/repository for the same concept. No single "core"
    mixin the way Patient/Organization have one — terminology has no
    single primary resource row, just this flat set of domains."""
