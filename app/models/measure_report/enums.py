from enum import Enum


class MeasureReportStatus(str, Enum):
    """MeasureReport.status: complete | pending | error."""

    complete = "complete"
    pending = "pending"
    error = "error"


class MeasureReportType(str, Enum):
    """MeasureReport.type: individual | subject-list | summary | data-collection."""

    individual = "individual"
    subject_list = "subject-list"
    summary = "summary"
    data_collection = "data-collection"


class MeasureReportSubjectReferenceType(str, Enum):
    """MeasureReport.subject allowed reference targets in R4."""

    Patient = "Patient"
    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Location = "Location"
    Device = "Device"
    RelatedPerson = "RelatedPerson"
    Group = "Group"


class MeasureReportReporterReferenceType(str, Enum):
    """MeasureReport.reporter allowed reference targets in R4."""

    Practitioner = "Practitioner"
    PractitionerRole = "PractitionerRole"
    Organization = "Organization"
    Location = "Location"


class MeasureReportSubjectResultsReferenceType(str, Enum):
    """MeasureReport population subjectResults allowed reference target in R4."""

    List = "List"


class MeasureReportQuantityComparator(str, Enum):
    """Quantity comparator: < | <= | >= | >."""

    lt = "<"
    le = "<="
    ge = ">="
    gt = ">"
