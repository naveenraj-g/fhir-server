from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["PractitionerRoleService"]


@trace_methods
class PractitionerRoleService(_CoreMixin):
    """All PractitionerRole business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
