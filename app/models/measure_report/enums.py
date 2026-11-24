from enum import Enum


class MeasureReportStatus(str, Enum):
    """MeasureReport.status (MeasureReportStatus, required) - stored by value.
    https://www.hl7.org/fhir/R4/valueset-measure-report-status.html"""

    complete = "complete"
    pending = "pending"
    error = "error"
