from app.core.logging import trace_methods

from .core import _CoreMixin

__all__ = ["AppointmentService"]


@trace_methods
class AppointmentService(_CoreMixin):
    """All Appointment business logic. __init__ (repository=...) is
    inherited from _CoreMixin."""
