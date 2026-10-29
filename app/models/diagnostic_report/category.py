from sqlalchemy import BigInteger, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.shared import FhirCodingMixin, TenantAuditMixin

# ---------------------------------------------------------------------------
# category (0..*) CodeableConcept child table
# ---------------------------------------------------------------------------


class DiagnosticReportCategory(TenantAuditMixin, Base):
    """One entry of DiagnosticReport.category (0..* CodeableConcept)."""

    __tablename__ = "diagnostic_report_category"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    diagnostic_report_pk = Column(BigInteger, ForeignKey("diagnostic_report.id"), nullable=False, index=True)
    text = Column(String, nullable=True)

    diagnostic_report = relationship("DiagnosticReportModel", back_populates="categories")
    codings = relationship("DiagnosticReportCategoryCoding", back_populates="category", cascade="all, delete-orphan")


class DiagnosticReportCategoryCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """One entry of DiagnosticReport.category.coding (0..*)."""

    __tablename__ = "diagnostic_report_category_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    diagnostic_report_category_id = Column(
        BigInteger, ForeignKey("diagnostic_report_category.id"), nullable=False, index=True
    )

    category = relationship("DiagnosticReportCategory", back_populates="codings")
