from sqlalchemy import BigInteger, Column, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base

# The four R4 targets of DiagnosticReport.performer and .resultsInterpreter.
PERFORMER_TYPES = ("Practitioner", "PractitionerRole", "Organization", "CareTeam")

# Which search parameter a row feeds, and the DiagnosticReport element it is read from.
PERFORMER_PARAMS = {
    "performer": "performer",
    "results-interpreter": "resultsInterpreter",
}


class DiagnosticReportPerformer(Base):
    """Search index for `performer` (DiagnosticReport.performer, 0..*) and
    `results-interpreter` (DiagnosticReport.resultsInterpreter, 0..*), which have the
    same shape: one row per Reference that has a `reference` or an `identifier`.
    `param` says which parameter the row belongs to (see PERFORMER_PARAMS).
    Derived from DiagnosticReportModel.content — never read to build a response.

    `reference_type` records which type a relative `Type/<id>` names — a plain
    string, not a Postgres enum, because the target can be one of four types (a
    search by bare id is ambiguous: `performer=Type/id` or `:Type=id`).

      performer / results-interpreter
                   -> reference_type/reference_id or reference_reference
      <param>:identifier
                   -> reference_identifier_system/_value"""

    __tablename__ = "diagnostic_report_performer"
    __table_args__ = (
        Index(
            "ix_diagnostic_report_performer_param_type_id",
            "param",
            "reference_type",
            "reference_id",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    diagnostic_report_pk = Column(
        BigInteger, ForeignKey("diagnostic_report.id"), nullable=False, index=True
    )
    param = Column(String, nullable=False)
    reference_reference = Column(String, nullable=True)
    reference_type = Column(String, nullable=True)
    reference_id = Column(BigInteger, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)

    diagnostic_report = relationship(
        "DiagnosticReportModel", back_populates="performers"
    )
