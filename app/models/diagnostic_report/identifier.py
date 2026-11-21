from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base


class DiagnosticReportIdentifier(Base):
    """Search index for the `identifier` token parameter (0..*). Derived
    from DiagnosticReportModel.content — never read to build a response.

    One row per DiagnosticReport.identifier *per Identifier.type.coding*
    (one row with no type when the identifier has no coded type), so that
    `identifier:of-type=type-system|type-code|value` can match type and
    value on the same row. A plain `identifier=` search is an EXISTS, so
    the repetition never duplicates results.

      identifier            -> system, value
      identifier:of-type    -> type_system, type_code, value
      identifier:text       -> type_text_norm / type_display_norm

    No UniqueConstraint on (system, value): FHIR R4 doesn't require
    identifier uniqueness — that's a profile decision, not a base rule."""

    __tablename__ = "diagnostic_report_identifier"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    # Named diagnostic_report_pk (not diagnostic_report_id) so it can't be
    # confused with DiagnosticReportModel.diagnostic_report_id, the public id.
    diagnostic_report_pk = Column(
        BigInteger, ForeignKey("diagnostic_report.id"), nullable=False, index=True
    )
    system = Column(String, nullable=True)
    value = Column(String, nullable=True, index=True)
    type_system = Column(String, nullable=True)
    type_code = Column(String, nullable=True)
    type_text_norm = Column(String, nullable=True)
    type_display_norm = Column(String, nullable=True)

    diagnostic_report = relationship(
        "DiagnosticReportModel", back_populates="identifiers"
    )
