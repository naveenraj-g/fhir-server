from app.repository.medication.core import _CoreMixin
from app.repository.medication.full import _FullMixin


class MedicationRepository(_CoreMixin, _FullMixin):
    def __init__(self, session_factory):
        self.session_factory = session_factory


__all__ = ["MedicationRepository"]
