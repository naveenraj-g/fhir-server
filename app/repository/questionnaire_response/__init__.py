from app.core.logging import trace_methods
from app.repository.base import BaseRepository

from .core import _CoreMixin
from .full import _FullMixin

__all__ = ["QuestionnaireResponseRepository"]


@trace_methods
class QuestionnaireResponseRepository(_CoreMixin, _FullMixin, BaseRepository):
    """All QuestionnaireResponse DB I/O. session_factory/__init__ and the
    generic paginated-list execution (`_execute_paginated`) are inherited
    from BaseRepository — see that class."""
