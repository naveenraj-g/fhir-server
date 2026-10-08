from .core import _CoreMixin

__all__ = ["FhirProfileService"]


class FhirProfileService(_CoreMixin):
    """Cache-aside reads of fhir_profile, in front of FhirProfileRepository
    — see core.py for the real docstring. __init__(self, repository,
    cache_backend) lives on _CoreMixin. Only one mixin here since
    fhir_profile has a single flat set of operations, no sub-resources —
    same shape as Organization's own service package."""
