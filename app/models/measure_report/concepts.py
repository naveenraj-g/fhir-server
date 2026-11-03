from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.enums import IdentifierUse
from app.models.shared import FhirCodingMixin, TenantAuditMixin


class MeasureReportImprovementNotationCoding(FhirCodingMixin, TenantAuditMixin, Base):
    """MeasureReport.improvementNotation.coding child table."""

    __tablename__ = "measure_report_improvement_notation_coding"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_report_pk = Column(
        BigInteger, ForeignKey("measure_report.id", ondelete="CASCADE"), nullable=False, index=True
    )

    measure_report = relationship(
        "MeasureReportModel", back_populates="improvement_notation_coding"
    )


class MeasureReportEvaluatedResource(TenantAuditMixin, Base):
    """MeasureReport.evaluatedResource (0..* Reference(Resource)) child table."""

    __tablename__ = "measure_report_evaluated_resource"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    measure_report_pk = Column(
        BigInteger, ForeignKey("measure_report.id", ondelete="CASCADE"), nullable=False, index=True
    )

    evaluated_resource_reference = Column(String, nullable=True)
    evaluated_resource_type = Column(String, nullable=True)
    evaluated_resource_id = Column(BigInteger, nullable=True, index=True)
    evaluated_resource_display = Column(String, nullable=True)

    # fallback identifier (11 columns)
    evaluated_resource_identifier_use = Column(
        Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True
    )
    evaluated_resource_identifier_type_system = Column(String, nullable=True)
    evaluated_resource_identifier_type_version = Column(String, nullable=True)
    evaluated_resource_identifier_type_code = Column(String, nullable=True)
    evaluated_resource_identifier_type_display = Column(String, nullable=True)
    evaluated_resource_identifier_type_user_selected = Column(Boolean, nullable=True)
    evaluated_resource_identifier_type_text = Column(String, nullable=True)
    evaluated_resource_identifier_system = Column(String, nullable=True)
    evaluated_resource_identifier_value = Column(String, nullable=True)
    evaluated_resource_identifier_period_start = Column(
        DateTime(timezone=True), nullable=True
    )
    evaluated_resource_identifier_period_end = Column(
        DateTime(timezone=True), nullable=True
    )

    measure_report = relationship(
        "MeasureReportModel", back_populates="evaluated_resources"
    )
