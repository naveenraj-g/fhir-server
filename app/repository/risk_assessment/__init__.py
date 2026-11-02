from app.repository.base import BaseRepository
from app.repository.risk_assessment.core import _CoreMixin
from app.repository.risk_assessment.full import _FullMixin


class RiskAssessmentRepository(BaseRepository, _CoreMixin, _FullMixin):
    """Repository managing RiskAssessment persistence and queries."""


__all__ = ["RiskAssessmentRepository"]

