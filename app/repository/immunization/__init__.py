from app.repository.base import BaseRepository

from .core import _CoreMixin
from .full import _FullMixin


class ImmunizationRepository(BaseRepository, _CoreMixin, _FullMixin):
    """Data-access layer for FHIR R4 Immunization."""


__all__ = ["ImmunizationRepository"]
