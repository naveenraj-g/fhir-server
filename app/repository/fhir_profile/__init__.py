from app.repository.base import BaseRepository

from .core import _CoreMixin

__all__ = ["FhirProfileRepository"]


class FhirProfileRepository(_CoreMixin, BaseRepository):
    """All DB I/O for fhir_profile. session_factory/__init__ inherited from
    BaseRepository — same convention the reworked FHIR resources
    (Organization, Patient, ...) use, see that class. Only one mixin here
    (core.py) since fhir_profile has a single flat set of operations, no
    sub-resources — same shape as Organization's own repository package."""
