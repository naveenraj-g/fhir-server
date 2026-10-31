from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["ProcedureService"]


@trace_methods
class ProcedureService(_CoreMixin):
    """Orchestrates Procedure CRUD operations and data transformations."""
