from app.repository.base import BaseRepository
from app.repository.immunization_evaluation.core import _CoreMixin
from app.repository.immunization_evaluation.full import _FullMixin


class ImmunizationEvaluationRepository(BaseRepository, _CoreMixin, _FullMixin):
    """Repository managing ImmunizationEvaluation persistence and queries."""


__all__ = ["ImmunizationEvaluationRepository"]
