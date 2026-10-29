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
from app.models.diagnostic_report.enums import DiagnosticReportSpecimenReferenceType
from app.models.enums import IdentifierUse
from app.models.shared import TenantAuditMixin


class DiagnosticReportSpecimen(TenantAuditMixin, Base):
    """specimen[] — Reference(Specimen). Specimen is not a modeled
    resource in this system today, so the existence check is never
    attempted for this field.

    No UniqueConstraint on (diagnostic_report_pk, reference_type,
    reference_id): R4 doesn't forbid listing the same reference twice — a
    deployment that wants that as a rule expresses it as a profile-layer
    invariant, not a base constraint."""

    __tablename__ = "diagnostic_report_specimen"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    diagnostic_report_pk = Column(BigInteger, ForeignKey("diagnostic_report.id"), nullable=False, index=True)

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(DiagnosticReportSpecimenReferenceType, name="diagnostic_report_specimen_reference_type"), nullable=True
    )
    reference_id = Column(BigInteger, nullable=True, index=True)
    reference_display = Column(String, nullable=True)

    reference_identifier_use = Column(Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True)
    reference_identifier_type_system = Column(String, nullable=True)
    reference_identifier_type_version = Column(String, nullable=True)
    reference_identifier_type_code = Column(String, nullable=True)
    reference_identifier_type_display = Column(String, nullable=True)
    reference_identifier_type_text = Column(String, nullable=True)
    reference_identifier_type_user_selected = Column(Boolean, nullable=True)
    reference_identifier_system = Column(String, nullable=True)
    reference_identifier_value = Column(String, nullable=True)
    reference_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    reference_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    diagnostic_report = relationship("DiagnosticReportModel", back_populates="specimens")
