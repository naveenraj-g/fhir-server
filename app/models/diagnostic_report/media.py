from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import relationship

from app.core.database import FHIRBase as Base
from app.models.diagnostic_report.enums import DiagnosticReportMediaLinkReferenceType
from app.models.enums import IdentifierUse
from app.models.shared import TenantAuditMixin


class DiagnosticReportMedia(TenantAuditMixin, Base):
    """DiagnosticReport.media (0..* BackboneElement) — `comment` (0..1
    string) + `link` (1..1 Reference(Media)). `link`'s flattened
    reference columns stay nullable at the DB level like every other
    reference field in this codebase — the 1..1 cardinality is enforced
    by the Base R4 validator (app.fhir.validation), not a DB
    CheckConstraint (see CLAUDE.md's "DB CheckConstraints are otherwise
    avoided" rule). Media is not a modeled resource in this system
    today, so the existence check is never attempted for `link`."""

    __tablename__ = "diagnostic_report_media"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    diagnostic_report_pk = Column(BigInteger, ForeignKey("diagnostic_report.id"), nullable=False, index=True)

    comment = Column(String, nullable=True)

    link_reference = Column(String, nullable=True)
    link_type = Column(
        Enum(DiagnosticReportMediaLinkReferenceType, name="diagnostic_report_media_link_reference_type"),
        nullable=True,
    )
    link_id = Column(BigInteger, nullable=True, index=True)
    link_display = Column(String, nullable=True)

    link_identifier_use = Column(Enum(IdentifierUse, name="identifier_use", create_type=False), nullable=True)
    link_identifier_type_system = Column(String, nullable=True)
    link_identifier_type_version = Column(String, nullable=True)
    link_identifier_type_code = Column(String, nullable=True)
    link_identifier_type_display = Column(String, nullable=True)
    link_identifier_type_text = Column(String, nullable=True)
    link_identifier_type_user_selected = Column(Boolean, nullable=True)
    link_identifier_system = Column(String, nullable=True)
    link_identifier_value = Column(String, nullable=True)
    link_identifier_period_start = Column(DateTime(timezone=True), nullable=True)
    link_identifier_period_end = Column(DateTime(timezone=True), nullable=True)

    diagnostic_report = relationship("DiagnosticReportModel", back_populates="media")
