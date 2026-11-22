from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["CarePlanService"]


@trace_methods
class CarePlanService(_CoreMixin):
    """All CarePlan business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
