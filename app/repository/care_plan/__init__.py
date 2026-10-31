from app.core.logging import trace_methods
from app.repository.base import BaseRepository

from .core import _CoreMixin
from .full import _FullMixin

__all__ = ["CarePlanRepository"]


@trace_methods
class CarePlanRepository(_CoreMixin, _FullMixin, BaseRepository):
    """All CarePlan DB I/O."""
