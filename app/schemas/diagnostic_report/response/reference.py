from pydantic import BaseModel, ConfigDict


class _PlainReferenceRow(BaseModel):
    """List-item Reference rows — real 0..* child-table rows, so each
    carries its own `id`."""

    model_config = ConfigDict(extra="allow")
    id: int
    reference: str | None = None
    reference_type: str | None = None
    reference_id: int | None = None
    reference_display: str | None = None


class PlainDiagnosticReportBasedOn(_PlainReferenceRow):
    pass


class PlainDiagnosticReportPerformer(_PlainReferenceRow):
    pass


class PlainDiagnosticReportResultsInterpreter(_PlainReferenceRow):
    pass


class PlainDiagnosticReportSpecimen(_PlainReferenceRow):
    pass


class PlainDiagnosticReportResult(_PlainReferenceRow):
    pass


class PlainDiagnosticReportImagingStudy(_PlainReferenceRow):
    pass


class _PlainSingleReferenceRow(BaseModel):
    """Single 0..1 Reference fields — flattened directly onto the owning
    row, so no `id` here."""

    model_config = ConfigDict(extra="allow")
    reference: str | None = None
    reference_type: str | None = None
    reference_id: int | None = None
    reference_display: str | None = None


class PlainDiagnosticReportSubject(_PlainSingleReferenceRow):
    pass


class PlainDiagnosticReportEncounter(_PlainSingleReferenceRow):
    pass
