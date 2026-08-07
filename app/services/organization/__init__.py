from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["OrganizationService"]


@trace_methods
class OrganizationService(_CoreMixin):
    """All Organization business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
