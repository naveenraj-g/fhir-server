from app.repository.medication_administration.core import _CoreMixin
from app.repository.medication_administration.full import _FullMixin


class MedicationAdministrationRepository(_CoreMixin, _FullMixin):
    def __init__(self, session_factory):
        self.session_factory = session_factory


__all__ = ["MedicationAdministrationRepository"]
