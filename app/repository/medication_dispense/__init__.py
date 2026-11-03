from app.repository.medication_dispense.core import _CoreMixin
from app.repository.medication_dispense.full import _FullMixin


class MedicationDispenseRepository(_CoreMixin, _FullMixin):
    def __init__(self, session_factory):
        self.session_factory = session_factory


__all__ = ["MedicationDispenseRepository"]
