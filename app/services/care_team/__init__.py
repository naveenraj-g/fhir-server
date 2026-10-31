from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["CareTeamService"]


@trace_methods
class CareTeamService(_CoreMixin):
    """Orchestrates CareTeam CRUD operations and data transformations."""
