from app.repository.medication_knowledge.core import _CoreMixin
from app.repository.medication_knowledge.full import _FullMixin


class MedicationKnowledgeRepository(_CoreMixin, _FullMixin):
    def __init__(self, session_factory):
        self.session_factory = session_factory


__all__ = ["MedicationKnowledgeRepository"]
