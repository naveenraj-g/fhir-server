from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["CareTeamService"]


@trace_methods
class CareTeamService(_CoreMixin):
    """All CareTeam business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
