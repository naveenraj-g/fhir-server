from app.repository.measure_report.core import _CoreMixin
from app.repository.measure_report.full import _FullMixin


class MeasureReportRepository(_CoreMixin, _FullMixin):
    """Data-access repository for the FHIR MeasureReport resource."""

    def __init__(self, session_factory):
        self.session_factory = session_factory


__all__ = ["MeasureReportRepository"]
