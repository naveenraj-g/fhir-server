from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# conclusionCode (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class DiagnosticReportConclusionCode(TenantAuditMixin, Base):
    """One entry of DiagnosticReport.conclusionCode (0..* CodeableConcept)."""

    __tablename__ = "diagnostic_report_conclusion_code"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    diagnostic_report_pk = Column(BigInteger, ForeignKey("diagnostic_report.id"), nullable=False, index=True)
    text = Column(String, nullable=True)

    diagnostic_report = relationship("DiagnosticReportModel", back_populates="conclusion_codes")
    codings = relationship(
        "DiagnosticReportConclusionCodeCoding", back_populates="conclusion_code", cascade="all, delete-orphan"
    )


class DiagnosticReportConclusionCodeCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of DiagnosticReport.conclusionCode.coding (0..*)."""

    __tablename__ = "diagnostic_report_conclusion_code_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    diagnostic_report_conclusion_code_id = Column(
        BigInteger, ForeignKey("diagnostic_report_conclusion_code.id"), nullable=False, index=True
    )

    conclusion_code = relationship("DiagnosticReportConclusionCode", back_populates="codings")
