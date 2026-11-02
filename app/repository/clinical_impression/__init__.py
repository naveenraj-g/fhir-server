from app.repository.base import BaseRepository
from app.repository.clinical_impression.core import _CoreMixin
from app.repository.clinical_impression.full import _FullMixin


class ClinicalImpressionRepository(BaseRepository, _CoreMixin, _FullMixin):
    """Repository managing ClinicalImpression persistence and queries."""


__all__ = ["ClinicalImpressionRepository"]
