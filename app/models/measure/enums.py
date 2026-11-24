from enum import Enum


class MeasureStatus(str, Enum):
    """Measure.status (PublicationStatus, required) - stored by value.
    https://www.hl7.org/fhir/R4/valueset-publication-status.html"""

    draft = "draft"
    active = "active"
    retired = "retired"
    unknown = "unknown"
