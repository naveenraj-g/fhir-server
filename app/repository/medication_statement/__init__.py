from app.repository.base import BaseRepository

from .core import _CoreMixin
from .full import _FullMixin


class MedicationStatementRepository(BaseRepository, _CoreMixin, _FullMixin):
    """Data-access layer for FHIR R4 MedicationStatement."""


__all__ = ["MedicationStatementRepository"]
