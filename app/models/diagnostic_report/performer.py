from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.diagnostic_report.enums import DiagnosticReportActorReferenceType
from app.models.enums import IdentifierUse
from app.models.shared import TenantAuditMixin


class DiagnosticReportPerformer(TenantAuditMixin, Base):
    """performer[] — of the four allowed types, only Practitioner/
    PractitionerRole/Organization are modeled resources — the existence
    check is only ever attempted for that subset (see
    app.repository.diagnostic_report._shared._MODELED_PERFORMER_TYPES)."""

    __tablename__ = "diagnostic_report_performer"
    __table_args__ = (
        UniqueConstraint(
            "diagnostic_report_pk", "reference_type", "reference_id",
            name="uq_diagnostic_report_performer_reference",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    diagnostic_report_pk = Column(BigInteger, ForeignKey("diagnostic_report.id"), nullable=False, index=True)

    reference_reference = Column(String, nullable=True)
    reference_type = Column(
        Enum(DiagnosticReportActorReferenceType, name="diagnostic_report_actor_reference_type"), nullable=True
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

    diagnostic_report = relationship("DiagnosticReportModel", back_populates="performers")
