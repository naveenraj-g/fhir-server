from app.repository.base import BaseRepository
from app.repository.measure.core import _CoreMixin
from app.repository.measure.full import _FullMixin


class MeasureRepository(BaseRepository, _CoreMixin, _FullMixin):
    """Repository managing Measure persistence and queries."""


__all__ = ["MeasureRepository"]
