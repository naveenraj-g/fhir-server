from app.repository.base import BaseRepository
from app.repository.allergy_intolerance.core import _CoreMixin
from app.repository.allergy_intolerance.full import _FullMixin


class AllergyIntoleranceRepository(_CoreMixin, _FullMixin, BaseRepository):
    """Repository for AllergyIntolerance FHIR resource."""

    pass


__all__ = ["AllergyIntoleranceRepository"]
