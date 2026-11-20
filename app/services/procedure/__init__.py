from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["ProcedureService"]


@trace_methods
class ProcedureService(_CoreMixin):
    """All Procedure business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
