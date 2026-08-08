from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["LocationService"]


@trace_methods
class LocationService(_CoreMixin):
    """All Location business logic. __init__ (repository=...) is inherited
    from _CoreMixin."""
